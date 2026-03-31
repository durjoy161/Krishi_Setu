# app/ui/payments_ui.py
# Payments page: view payment status and make dummy payments

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QDialog, QFormLayout, QDoubleSpinBox, QComboBox,
                              QMessageBox, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import app.utils.session as session
from app.services import payment_service
from app.ui.styles import STATUS_COLORS


class PayDialog(QDialog):
    """Dialog for making a payment."""

    def __init__(self, parent=None, amount_due=0, amount_paid=0):
        super().__init__(parent)
        self.setWindowTitle("Make Payment")
        self.setFixedWidth(360)
        self.setStyleSheet("QDialog{background:#0f1923;} QLabel{color:#d8f3dc;}")
        self._amount_due = amount_due
        self._amount_paid = amount_paid
        self._build(amount_due, amount_paid)

    def _build(self, amount_due, amount_paid):
        layout = QFormLayout(self)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        due_lbl = QLabel(f"৳ {amount_due:,.2f}")
        due_lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#e76f51;")
        paid_lbl = QLabel(f"৳ {amount_paid:,.2f}")
        paid_lbl.setStyleSheet("font-size:14px; color:#52b788;")
        remaining = amount_due - amount_paid
        rem_lbl = QLabel(f"৳ {remaining:,.2f}")
        rem_lbl.setStyleSheet("font-size:14px; color:#f4a261;")

        layout.addRow("Total Due:", due_lbl)
        layout.addRow("Already Paid:", paid_lbl)
        layout.addRow("Remaining:", rem_lbl)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(1, remaining)
        self.amount_spin.setValue(remaining)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("৳ ")
        self.amount_spin.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.method_cb = QComboBox()
        self.method_cb.addItems(["online", "cash", "bkash", "nagad"])
        self.method_cb.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        layout.addRow("Pay Amount:", self.amount_spin)
        layout.addRow("Method:", self.method_cb)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background:#1a2940;color:#e76f51;border:1px solid #9b2226;border-radius:6px;padding:8px 14px;")
        cancel_btn.clicked.connect(self.reject)
        pay_btn = QPushButton("💳  Pay Now")
        pay_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold;")
        pay_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(pay_btn)
        layout.addRow(btn_row)

    def get_data(self):
        return self.amount_spin.value(), self.method_cb.currentText()


class PaymentsPage(QWidget):
    """Payments listing and payment action page."""

    COLS_CUSTOMER = ["ID", "Product", "Order Type", "Amount Due (৳)", "Amount Paid (৳)", "Status", "Method", "Paid At"]
    COLS_AGENT    = ["ID", "Customer", "Product", "Amount Due (৳)", "Amount Paid (৳)", "Status", "Method", "Paid At"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("💳  Payments")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        self._role = session.get_role()
        cols = self.COLS_CUSTOMER if self._role == "customer" else self.COLS_AGENT

        self.table = QTableWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget{background:#12202e;alternate-background-color:#172a3a;
                         gridline-color:#1b4332;border:none;}
            QHeaderView::section{background:#1b4332;color:#b7e4c7;padding:8px;border:none;font-weight:bold;}
            QTableWidget::item{padding:6px;}
        """)
        layout.addWidget(self.table)

        # Pay button (customers only)
        if self._role == "customer":
            action_row = QHBoxLayout()
            action_row.addStretch()
            pay_btn = QPushButton("💳  Pay Selected")
            pay_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:7px;padding:9px 22px;font-size:14px;font-weight:bold;")
            pay_btn.clicked.connect(self._pay)
            action_row.addWidget(pay_btn)
            layout.addLayout(action_row)

        self._payments = []

    def refresh(self):
        uid = session.get_id()
        if self._role == "customer":
            self._payments = payment_service.get_payments_for_customer(uid)
        else:
            self._payments = payment_service.get_all_payments()
        self._load_table()

    def _load_table(self):
        self.table.setRowCount(0)
        for i, p in enumerate(self._payments):
            self.table.insertRow(i)
            if self._role == "customer":
                vals = [str(p["id"]), p.get("product_name","—"), p.get("order_type","—"),
                        f"৳{p['amount_due']:,.2f}", f"৳{p['amount_paid']:,.2f}",
                        p["status"].upper(), p.get("method","—"), p.get("paid_at","—") or "—"]
            else:
                vals = [str(p["id"]), p.get("customer_name","—"), p.get("product_name","—"),
                        f"৳{p['amount_due']:,.2f}", f"৳{p['amount_paid']:,.2f}",
                        p["status"].upper(), p.get("method","—"), p.get("paid_at","—") or "—"]
            for ci, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if p["status"] == "paid" and ci == (5 if self._role == "customer" else 5):
                    item.setForeground(QColor("#52b788"))
                elif p["status"] == "partial" and ci == 5:
                    item.setForeground(QColor("#f4a261"))
                elif p["status"] == "unpaid" and ci == 5:
                    item.setForeground(QColor("#e76f51"))
                self.table.setItem(i, ci, item)

    def _pay(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a payment to pay.")
            return
        p = self._payments[row]
        if p["status"] == "paid":
            QMessageBox.information(self, "Already Paid", "This payment is already fully paid. ✅")
            return
        dlg = PayDialog(self, amount_due=p["amount_due"], amount_paid=p["amount_paid"])
        if dlg.exec_() == QDialog.Accepted:
            amount, method = dlg.get_data()
            payment_service.pay_partial(p["id"], amount, method)
            QMessageBox.information(self, "Payment Successful",
                f"✅ Payment of ৳{amount:,.2f} via {method} recorded successfully!")
            self.refresh()
