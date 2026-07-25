from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from bot.config import ADMIN_IDS
from bot.database import get_user, create_request, log_security_event, sqlite3, DATABASE_PATH
from bot.keyboards import get_admin_keyboard
from bot.utils.notifications import send_admin_notification


admin_router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён", parse_mode=ParseMode.HTML)
        return
    await message.answer("🛠 <b>Админ-панель</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)


@admin_router.message(F.text == "📋 Новые заявки")
async def process_new_requests(message: Message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE status = 'new' ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await message.answer("Нет новых заявок", parse_mode=ParseMode.HTML)
        return
    for row in rows:
        user = get_user(row["user_id"])
        name = user["full_name"] if user else f"ID:{row['user_id']}"
        username = f"@{user['username']}" if user and user.get("username") else ""
        amount_info = f"💵 {row['amount']}\n" if row["amount"] else ""
        text = f"📩 <b>Заявка #{row['id']}</b>\n👤 {name} {username}\n{amount_info}📝 {row['request_text']}\n🕐 {row['created_at']}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ В работе", callback_data=f"status_{row['id']}_in_progress"),
                InlineKeyboardButton(text="✅ Завершена", callback_data=f"status_{row['id']}_done"),
            ]
        ])
        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@admin_router.callback_query(F.data.startswith("status_"))
async def process_status_change(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", parse_mode=ParseMode.HTML)
        return
    _, req_id, status = callback.data.split("_")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE requests SET status = ?, operator_id = ? WHERE id = ?", (status, callback.from_user.id, req_id))
    conn.commit()
    conn.close()
    await callback.message.edit_text(callback.message.text + f"\n\nСтатус: {status}", parse_mode=ParseMode.HTML)
    await send_admin_notification(f"🔄 <b>Статус заявки #{req_id}</b> изменён на: {status}\n👤 Оператор: {callback.from_user.id}")
    await callback.answer("Статус обновлён")


@admin_router.message(F.text == "📊 Статистика")
async def process_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'new'")
    new_req = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_paid = 1")
    paid = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM security_events")
    sec_events = cursor.fetchone()[0]
    conn.close()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: {paid}\n"
        f"📩 Всего заявок: {total}\n"
        f"🆕 Новых: {new_req}\n"
        f"🛡️ Событий безопасности: {sec_events}"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)