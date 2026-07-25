_active_invoices: dict[int, dict] = {}


def add_active_invoice(invoice_id: int, user_id: int, amount: float):
    _active_invoices[invoice_id] = {"user_id": user_id, "amount": amount}


def remove_active_invoice(invoice_id: int):
    _active_invoices.pop(invoice_id, None)


def get_active_invoices():
    return dict(_active_invoices)
