import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import ADMIN_IDS, CRYPTOBOT_API_TOKEN, PAYMENT_AMOUNT_USDT
from bot.database import get_user, upsert_user, create_request, set_user_paid, log_security_event
from bot.keyboards import get_main_keyboard, get_amount_keyboard, get_payment_method_keyboard
from bot.security.prompt_injection_guard import PromptInjectionGuard
from bot.security.jailbreak_guard import JailbreakGuard
from bot.security.pii_guard import PIIGuard
from bot.security.toxicity_guard import ToxicityGuard
from bot.security.topical_guard import TopicalGuard
from bot.security.rag_guard import RAGPoisoningGuard
from bot.utils.notifications import send_admin_notification
from bot.services.payment_service import create_cryptobot_payment


user_router = Router()
logger = logging.getLogger(__name__)


class RequestStates(StatesGroup):
    waiting_request_text = State()
    waiting_project = State()


class PaymentStates(StatesGroup):
    waiting_method = State()
    waiting_amount = State()


@user_router.message(Command("start"))
async def cmd_start(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        upsert_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        "👋 Добро пожаловать в агрегатор AI-услуг!\n\n"
        "Я помогу вам оставить заявку на разработку ботов, автоматизацию и AI-решения.\n\n"
        "После описания задачи вы сможете выбрать сумму оплаты.",
        reply_markup=get_main_keyboard(is_admin=is_admin),
        parse_mode=ParseMode.HTML,
    )


@user_router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "1. Нажмите «📝 Оставить заявку»\n"
        "2. Опишите вашу задачу\n"
        "3. Введите сумму для оплаты\n"
        "4. Оплатите доступ через CryptoBot Testnet\n"
        "5. После оплаты оператор свяжется с вами\n\n"
        "Если есть вопросы — пишите @David_Zhe",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@user_router.message(F.text == "📝 Оставить заявку")
async def process_request(message: Message, state: FSMContext):
    await state.set_state(RequestStates.waiting_request_text)
    await message.answer(
        "📝 <b>Опишите вашу задачу</b>\n\n"
        "Например: «Нужен Telegram-бот для автоматизации продаж с интеграцией CRM»\n\n"
        "Отправьте текст заявки следующим сообщением.",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@user_router.message(StateFilter(RequestStates.waiting_request_text))
async def process_request_text(message: Message, state: FSMContext):
    text = message.text or message.caption or ""
    user_id = message.from_user.id

    if (message.text or "").strip() == "ℹ️ Помощь":
        await cmd_help(message)
        return
    if (message.text or "").strip() in ["🔙 Назад", "📝 Оставить заявку", "💳 Проверить оплату", "🛠 Админ-панель", "📋 Новые заявки", "📊 Статистика"]:
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    ok, result = await PromptInjectionGuard.check(text, user_id)
    if not ok:
        from bot.database import log_security_event
        log_security_event(user_id, "prompt_injection", text[:500])
        await state.clear()
        await message.answer("❌ Запрос содержит запрещённые инструкции", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    ok, result = await JailbreakGuard.check(text, user_id)
    if not ok:
        from bot.database import log_security_event
        log_security_event(user_id, "jailbreak", text[:500])
        await state.clear()
        await message.answer("❌ Запрос содержит запрещённые инструкции", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    ok, result = await ToxicityGuard.check(text, user_id)
    if not ok:
        from bot.database import log_security_event
        log_security_event(user_id, "toxicity", text[:500])
        await state.clear()
        await message.answer("❌ Содержит недопустимый контент", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    text, pii_detected = await PIIGuard.redact(text, user_id)
    if pii_detected:
        from bot.database import log_security_event
        log_security_event(user_id, "pii", text[:500])
        await message.answer("⚠️ В вашем сообщении обнаружены персональные данные. Они были скрыты.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        if not text.strip():
            await state.clear()
            return

    ok, result, topic_status = await TopicalGuard.check(text, user_id)
    if not ok:
        from bot.database import log_security_event
        log_security_event(user_id, "forbidden_topic", text[:500])
        request_id = create_request(user_id, text)
        user = get_user(user_id)
        username = f"@{user['username']}" if user and user.get("username") else "нет username"
        await send_admin_notification(
            f"🚫 <b>Запрещённая тема</b>\n"
            f"👤 {message.from_user.full_name} ({username})\n"
            f"🆔 ID: {user_id}\n"
            f"📩 Заявка #{request_id}\n"
            f"📝 {text[:300]}"
        )
        await state.clear()
        await message.answer("❌ Тема запроса не разрешена.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return
    if topic_status == "off_topic":
        from bot.database import log_security_event
        log_security_event(user_id, "off_topic", text[:500])
        request_id = create_request(user_id, text)
        user = get_user(user_id)
        username = f"@{user['username']}" if user and user.get("username") else "нет username"
        await send_admin_notification(
            f"⚠️ <b>Оффтоп</b>\n"
            f"👤 {message.from_user.full_name} ({username})\n"
            f"🆔 ID: {user_id}\n"
            f"📩 Заявка #{request_id}\n"
            f"📝 {text[:300]}"
        )
        await state.clear()
        await message.answer(result, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    rag_ok, rag_msg = await RAGPoisoningGuard.validate_document(text, f"user_{user_id}")
    if not rag_ok:
        from bot.database import log_security_event
        log_security_event(user_id, "rag_poisoning", text[:500])
        await state.clear()
        await message.answer(f"❌ {rag_msg}", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    await state.update_data(request_text=text)
    request_id = create_request(user_id, text)
    user = get_user(user_id)
    username = f"@{user['username']}" if user and user.get("username") else "нет username"
    await send_admin_notification(
        f"📩 <b>Новая заявка #{request_id}</b>\n"
        f"👤 {message.from_user.full_name} ({username})\n"
        f"🆔 ID: {user_id}\n"
        f"📝 {text[:300]}"
    )
    await state.update_data(request_id=request_id)
    await state.set_state(PaymentStates.waiting_method)
    await message.answer(
        "💳 <b>Выберите способ оплаты</b>",
        reply_markup=get_payment_method_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@user_router.message(StateFilter(PaymentStates.waiting_method))
async def process_payment_method(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text == "ℹ️ Помощь":
        await cmd_help(message)
        return
    if text == "🪙 CryptoBot":
        await state.update_data(payment_method="cryptobot")
        await state.set_state(PaymentStates.waiting_amount)
        await message.answer(
            "🪙 <b>CryptoBot</b>\n\nВведите сумму оплаты (USDT). Например: 10 или 25.50",
            reply_markup=get_amount_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return
    if text in ["🔙 Назад", "📝 Оставить заявку"]:
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return
    await message.answer("❌ Выберите способ оплаты из меню.", reply_markup=get_payment_method_keyboard(), parse_mode=ParseMode.HTML)


@user_router.message(StateFilter(PaymentStates.waiting_amount))
async def process_amount(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    user_id = message.from_user.id
    data = await state.get_data()
    request_text = data.get("request_text", "")

    if text == "ℹ️ Помощь":
        await cmd_help(message)
        return
    if text in ["🔙 Назад", "📝 Оставить заявку", "💳 Оплатить"]:
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return

    try:
        amount = float(text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное положительное число. Например: 10 или 25.50", parse_mode=ParseMode.HTML)
        return

    await state.update_data(request_amount=amount)

    result = await create_cryptobot_payment(user_id, amount=amount)
    if result.get("ok"):
        invoice_id = result["payment_id"]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=result["url"])],
        ])
        await message.answer(
            f"🪙 <b>Оплата {amount} USDT через CryptoBot</b>\n\nСчёт создан. Бот автоматически проверит оплату.",
            reply_markup=kb,
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            f"❌ Ошибка создания чека: {result.get('error')}",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.HTML,
        )
    await state.clear()
async def cmd_send_project(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.get("is_paid"):
        await message.answer("⛔ Для отправки проекта требуется оплата.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return
    await state.set_state(RequestStates.waiting_project)
    await message.answer(
        "📤 <b>Отправьте выполненный проект</b>\n\n"
        "Пришлите текст, фото или файл с результатом.",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@user_router.message(StateFilter(RequestStates.waiting_project))
async def process_project(message: Message, state: FSMContext):
    text = message.text or message.caption or ""
    user_id = message.from_user.id
    request_id = (await state.get_data()).get("request_id")
    if not request_id:
        await message.answer("❌ Активная заявка не найдена.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        await state.clear()
        return

    user = get_user(user_id)
    username = f"@{user['username']}" if user and user.get("username") else "нет username"
    await send_admin_notification(
        f"📤 <b>Проект отправлен по заявке #{request_id}</b>\n"
        f"👤 {message.from_user.full_name} ({username})\n"
        f"🆔 ID: {user_id}\n"
        f"📝 {text[:500]}"
    )
    await state.clear()
    await message.answer("✅ Проект отправлен фрилансеру. Оператор свяжется с вами.", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)


@user_router.message(F.text == "💳 Оплатить", StateFilter(None))
async def cmd_payment(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user and user.get("is_paid"):
        await message.answer("✅ Оплата уже подтверждена. Вы можете оставить заявку!", reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)
        return
    await state.set_state(PaymentStates.waiting_method)
    await message.answer(
        "💳 <b>Выберите способ оплаты</b>",
        reply_markup=get_payment_method_keyboard(),
        parse_mode=ParseMode.HTML,
    )
