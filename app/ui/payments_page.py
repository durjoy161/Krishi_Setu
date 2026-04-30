# app/ui/payments_page.py
# Contains three payment pages + one shared dialog — all imports at the top.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame,
    QDialog, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, payment_status_color
)
from app.services.payment_service import (
    get_payments_for_customer,
    get_payments_for_farmer,
    get_all_payments,
    get_payment_summary,
    record_payment,
    VALID_METHODS,
)


# ── Customer Payments Page ─────────────────────────────────────────────────────

class CustomerPaymentsPage(QWidget):
    """Read-only payment history for customers."""

    COLUMNS = ["Order#", "Product", "Farmer", "Amount Due",
               "Amount Paid", "Remaining", "Method", "Status", "Paid On"]

    def __init__(self):
        super().__init__()
        self._customer_id = session.get_id()
        self._payments: list = []
        self._filtered: list = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("💳  Payment History")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#4895ef;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#7a9ab5;font-size:12px;")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "unpaid", "partial", "paid"])
        self.status_filter.setFixedWidth(130)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _btn("↻  Refresh", "#1a3a6c", "#2d5fa6")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(filter_lbl)
        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # Summary cards
        self._summary_widgets = {}
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, label, color in [
            ("due",         "Total Due",   "#f4a261"),
            ("paid",        "Total Paid",  "#52b788"),
            ("outstanding", "Outstanding", "#e63946"),
        ]:
            card = _SummaryCard(label, "৳ 0.00", color)
            self._summary_widgets[key] = card
            summary_row.addWidget(card)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        from app.ui.widgets.data_table import DataTable
        self.table = DataTable(self.COLUMNS)
        layout.addWidget(self.table)

        layout.addWidget(_legend([
            ("Unpaid", "#e63946"),
            ("Partial", "#f4a261"),
            ("Paid", "#52b788"),
        ]))

    def refresh(self):
        self._payments = get_payments_for_customer(self._customer_id)
        total_due  = sum(p["amount_due"]  for p in self._payments)
        total_paid = sum(p["amount_paid"] for p in self._payments)
        outstanding = max(0.0, total_due - total_paid)
        self._summary_widgets["due"].set_value(format_currency(total_due))
        self._summary_widgets["paid"].set_value(format_currency(total_paid))
        self._summary_widgets["outstanding"].set_value(format_currency(outstanding))
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered = (
            self._payments if sf == "All"
            else [p for p in self._payments if p["status"] == sf]
        )
        rows = []
        for p in self._filtered:
            remaining = round(p["amount_due"] - p["amount_paid"], 2)
            rows.append([
                p["order_id"],
                truncate(p["product_name"], 22),
                truncate(p["farmer_name"],  18),
                format_currency(p["amount_due"]),
                format_currency(p["amount_paid"]),
                format_currency(remaining),
                p["method"] or "—",
                p["status"].capitalize(),
                format_date(p["paid_at"]) if p["paid_at"] else "—",
            ])
        self.table.populate(rows)
        for i, p in enumerate(self._filtered):
            self.table.color_cell(i, 7, payment_status_color(p["status"]))
        count = len(self._filtered)
        self.result_count.setText(
            f"{count} record{'s' if count != 1 else ''}"
        )


# ── Farmer Payments Page ───────────────────────────────────────────────────────

class FarmerPaymentsPage(QWidget):
    """Payments tab for farmers — view + record incoming payments."""

    COLUMNS = ["Order#", "Product", "Customer", "Amount Due",
               "Amount Paid", "Remaining", "Method", "Status"]

    def __init__(self):
        super().__init__()
        self._farmer_id = session.get_id()
        self._payments: list = []
        self._filtered: list = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("💳  Payments")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#52b788;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#7a9ab5;font-size:12px;")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "unpaid", "partial", "paid"])
        self.status_filter.setFixedWidth(130)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(filter_lbl)
        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # Summary cards
        self._summary_widgets = {}
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, label, color in [
            ("due",         "Total Due",   "#f4a261"),
            ("paid",        "Received",    "#52b788"),
            ("outstanding", "Outstanding", "#e63946"),
        ]:
            card = _SummaryCard(label, "৳ 0.00", color)
            self._summary_widgets[key] = card
            summary_row.addWidget(card)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        from app.ui.widgets.data_table import DataTable
        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_record = _btn("💵  Record Payment", "#1b4332", "#2d6a4f")
        self.btn_record.setEnabled(False)
        self.btn_record.clicked.connect(self._open_record_dialog)
        btn_row.addWidget(self.btn_record)
        layout.addLayout(btn_row)

    def refresh(self):
        self._payments = get_payments_for_farmer(self._farmer_id)
        total_due  = sum(p["amount_due"]  for p in self._payments)
        total_paid = sum(p["amount_paid"] for p in self._payments)
        outstanding = max(0.0, total_due - total_paid)
        self._summary_widgets["due"].set_value(format_currency(total_due))
        self._summary_widgets["paid"].set_value(format_currency(total_paid))
        self._summary_widgets["outstanding"].set_value(format_currency(outstanding))
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered = (
            self._payments if sf == "All"
            else [p for p in self._payments if p["status"] == sf]
        )
        rows = []
        for p in self._filtered:
            remaining = round(p["amount_due"] - p["amount_paid"], 2)
            rows.append([
                p["order_id"],
                truncate(p["product_name"],  22),
                truncate(p["customer_name"], 18),
                format_currency(p["amount_due"]),
                format_currency(p["amount_paid"]),
                format_currency(remaining),
                p["method"] or "—",
                p["status"].capitalize(),
            ])
        self.table.populate(rows)
        for i, p in enumerate(self._filtered):
            self.table.color_cell(i, 7, payment_status_color(p["status"]))
        count = len(self._filtered)
        self.result_count.setText(
            f"{count} record{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected_payment(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        pay = self._selected_payment()
        self.btn_record.setEnabled(
            pay is not None and pay["status"] != "paid"
        )

    def _open_record_dialog(self):
        pay = self._selected_payment()
        if not pay:
            return
        dlg = RecordPaymentDialog(pay, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()


# ── Agent Payments Page ────────────────────────────────────────────────────────

class AgentPaymentsPage(QWidget):
    """Platform-wide payment ledger for agents."""

    COLUMNS = ["Order#", "Product", "Customer", "Farmer",
               "Due", "Paid", "Remaining", "Method", "Status", "Paid On"]

    def __init__(self):
        super().__init__()
        self._payments: list = []
        self._filtered: list = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("💳  All Payments")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#f4a261;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#7a9ab5;font-size:12px;")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "unpaid", "partial", "paid"])
        self.status_filter.setFixedWidth(130)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(filter_lbl)
        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # 6-card summary row
        self._summary_widgets = {}
        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        for key, label, color in [
            ("total_due",         "Total Due",    "#f4a261"),
            ("total_paid",        "Total Paid",   "#52b788"),
            ("total_outstanding", "Outstanding",  "#e63946"),
            ("unpaid_count",      "Unpaid",       "#e63946"),
            ("partial_count",     "Partial",      "#f4a261"),
            ("paid_count",        "Fully Paid",   "#52b788"),
        ]:
            card = _SummaryCard(label, "0", color)
            self._summary_widgets[key] = card
            summary_row.addWidget(card)
        layout.addLayout(summary_row)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        from app.ui.widgets.data_table import DataTable
        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_record = _btn("💵  Record Payment", "#1b4332", "#2d6a4f")
        self.btn_record.setEnabled(False)
        self.btn_record.clicked.connect(self._open_record_dialog)
        btn_row.addWidget(self.btn_record)
        layout.addLayout(btn_row)

    def refresh(self):
        self._payments = get_all_payments()
        summary = get_payment_summary()
        for key, widget in self._summary_widgets.items():
            val = summary.get(key, 0)
            if isinstance(val, float):
                widget.set_value(format_currency(val))
            else:
                widget.set_value(str(val))
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered = (
            self._payments if sf == "All"
            else [p for p in self._payments if p["status"] == sf]
        )
        rows = []
        for p in self._filtered:
            remaining = round(p["amount_due"] - p["amount_paid"], 2)
            rows.append([
                p["order_id"],
                truncate(p["product_name"],  20),
                truncate(p["customer_name"], 16),
                truncate(p["farmer_name"],   16),
                format_currency(p["amount_due"]),
                format_currency(p["amount_paid"]),
                format_currency(remaining),
                p["method"] or "—",
                p["status"].capitalize(),
                format_date(p["paid_at"]) if p["paid_at"] else "—",
            ])
        self.table.populate(rows)
        for i, p in enumerate(self._filtered):
            self.table.color_cell(i, 8, payment_status_color(p["status"]))
        count = len(self._filtered)
        self.result_count.setText(
            f"{count} record{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected_payment(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        pay = self._selected_payment()
        self.btn_record.setEnabled(
            pay is not None and pay["status"] != "paid"
        )

    def _open_record_dialog(self):
        pay = self._selected_payment()
        if not pay:
            return
        dlg = RecordPaymentDialog(pay, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()


# ── Record Payment Dialog ──────────────────────────────────────────────────────

class RecordPaymentDialog(QDialog):
    """
    Dialog for recording a payment against an order.
    Used by both FarmerPaymentsPage and AgentPaymentsPage.
    """

    def __init__(self, payment: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Payment")
        self.setFixedWidth(420)
        self.setModal(True)
        self._payment = payment
        self._build()

    def _build(self):
        pay       = self._payment
        remaining = round(pay["amount_due"] - pay["amount_paid"], 2)

        self.setStyleSheet("""
            QDialog {
                background: #12202e;
            }
            QLabel {
                color: #c8dff0;
                font-size: 13px;
            }
            QDoubleSpinBox, QComboBox {
                background: #1a2940;
                border: 1px solid #2d4a6a;
                border-radius: 6px;
                padding: 8px 10px;
                color: #e8f5e9;
                font-size: 13px;
            }
            QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #52b788;
            }
            QComboBox QAbstractItemView {
                background: #1a2940;
                color: #e8f5e9;
                selection-background-color: #2d6a4f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Title
        title_lbl = QLabel(f"Record Payment — Order #{pay['order_id']}")
        title_lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#52b788;"
        )
        layout.addWidget(title_lbl)
        layout.addWidget(_divider())

        # Order summary
        for label, value in [
            ("Product",      pay.get("product_name", "—")),
            ("Amount Due",   format_currency(pay["amount_due"])),
            ("Already Paid", format_currency(pay["amount_paid"])),
            ("Remaining",    format_currency(remaining)),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;min-width:120px;"
            )
            val = QLabel(str(value))
            val.setStyleSheet("font-size:13px;color:#d0e8f5;font-weight:bold;")
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)

        layout.addWidget(_divider())

        # Input fields
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(0.01)
        self.amount_spin.setMaximum(remaining if remaining > 0 else 0.01)
        self.amount_spin.setValue(remaining if remaining > 0 else 0.01)
        self.amount_spin.setPrefix("৳  ")
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(10.0)

        self.method_combo = QComboBox()
        self.method_combo.addItems(VALID_METHODS)

        form.addRow("Amount *", self.amount_spin)
        form.addRow("Method *", self.method_combo)
        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.button(QDialogButtonBox.Ok).setText("✅  Confirm Payment")
        btns.setStyleSheet("""
            QPushButton {
                background: #2d6a4f;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #40916c;
            }
        """)
        btns.accepted.connect(self._on_confirm)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_confirm(self):
        result = record_payment(
            order_id=self._payment["order_id"],
            amount=self.amount_spin.value(),
            method=self.method_combo.currentText(),
        )
        if result["success"]:
            QMessageBox.information(
                self, "Payment Recorded",
                f"✅ Payment of {format_currency(self.amount_spin.value())} recorded.\n"
                f"New status: {result['new_status'].capitalize()}"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])


# ── Shared small widgets ────────────────────────────────────────────────────────

class _SummaryCard(QWidget):
    """Small inline stat card for the payments summary row."""

    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.setFixedHeight(72)
        self.setMinimumWidth(130)
        self._color = color
        self.setStyleSheet(f"""
            QWidget {{
                background: #12202e;
                border: 1px solid {color}33;
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self._val_lbl = QLabel(value)
        self._val_lbl.setStyleSheet(
            f"font-size:16px;font-weight:bold;color:{color};"
            "background:transparent;border:none;"
        )
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "font-size:10px;color:#7a9ab5;"
            "background:transparent;border:none;"
        )
        layout.addWidget(self._val_lbl)
        layout.addWidget(lbl)

    def set_value(self, value: str):
        self._val_lbl.setText(value)


# ── Module-level helpers ────────────────────────────────────────────────────────

def _btn(text: str, dark: str, light: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {dark};
            color: white;
            border: none;
            border-radius: 7px;
            font-size: 12px;
            padding: 0 14px;
        }}
        QPushButton:hover {{ background: {light}; }}
        QPushButton:disabled {{
            background: #1a2940;
            color: #3a5a6a;
        }}
    """)
    return btn


def _combo_style() -> str:
    return """
        QComboBox {
            background: #1a2940;
            border: 1px solid #2d4a6a;
            border-radius: 7px;
            padding: 0 10px;
            color: #e8f5e9;
            font-size: 12px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: #1a2940;
            color: #e8f5e9;
            selection-background-color: #2d5fa6;
        }
    """


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color: #1a2940;")
    return line


def _legend(items: list) -> QWidget:
    """Build a colored status legend row."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 4, 0, 0)
    layout.setSpacing(16)
    lbl = QLabel("Status:")
    lbl.setStyleSheet("font-size:11px;color:#7a9ab5;")
    layout.addWidget(lbl)
    for label, color in items:
        dot = QLabel(f"● {label}")
        dot.setStyleSheet(f"font-size:11px;color:{color};")
        layout.addWidget(dot)
    layout.addStretch()
    return row