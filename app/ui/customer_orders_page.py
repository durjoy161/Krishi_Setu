# app/ui/customer_orders_page.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QMessageBox, QFrame,
    QDialog, QFormLayout, QTextEdit,
    QDialogButtonBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, order_status_color
)
from app.services.order_service import (
    get_orders_for_customer, cancel_order
)
from app.ui.widgets.data_table import DataTable


class CustomerOrdersPage(QWidget):

    COLUMNS = ["ID", "Product", "Qty", "Total",
               "Type", "Status", "Farmer", "Date"]

    def __init__(self):
        super().__init__()
        self._customer_id = session.get_id()
        self._orders = []
        self._filtered = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("📋  My Orders")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#4895ef;")
        title_row.addWidget(title)
        title_row.addStretch()

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#7a9ab5;font-size:12px;")
        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", "placed", "confirmed", "harvested", "delivered", "cancelled"]
        )
        self.status_filter.setFixedWidth(150)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _make_btn("↻  Refresh", "#1a3a6c", "#2d5fa6")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(filter_lbl)
        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = _make_btn("✖  Cancel Order", "#5a1a1a", "#8b0000")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_selected)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        # Legend
        legend = QWidget()
        leg_layout = QHBoxLayout(legend)
        leg_layout.setContentsMargins(0, 4, 0, 0)
        leg_layout.setSpacing(16)
        leg_lbl = QLabel("Status:")
        leg_lbl.setStyleSheet("font-size:11px;color:#7a9ab5;")
        leg_layout.addWidget(leg_lbl)
        for status, color in [
            ("Placed", "#4895ef"), ("Confirmed", "#f4a261"),
            ("Harvested", "#9b5de5"), ("Delivered", "#52b788"),
            ("Cancelled", "#e63946"),
        ]:
            dot = QLabel(f"● {status}")
            dot.setStyleSheet(f"font-size:11px;color:{color};")
            leg_layout.addWidget(dot)
        leg_layout.addStretch()
        layout.addWidget(legend)

    def refresh(self):
        self._orders = get_orders_for_customer(self._customer_id)
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered = (
            self._orders if sf == "All"
            else [o for o in self._orders if o["status"] == sf]
        )
        rows = []
        for o in self._filtered:
            rows.append([
                o["id"],
                truncate(o["product_name"], 25),
                f"{o['quantity']} {o['product_unit']}",
                format_currency(o["total_price"]),
                o["order_type"].capitalize(),
                o["status"].capitalize(),
                truncate(o["farmer_name"], 20),
                format_date(o["created_at"]),
            ])
        self.table.populate(rows)
        for i, o in enumerate(self._filtered):
            self.table.color_cell(i, 5, order_status_color(o["status"]))
        count = len(self._filtered)
        self.result_count.setText(f"{count} order{'s' if count != 1 else ''}")
        self._on_selection_change()

    def _selected_order(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        order = self._selected_order()
        self.btn_cancel.setEnabled(
            order is not None and order["status"] == "placed"
        )

    def _cancel_selected(self):
        order = self._selected_order()
        if not order:
            return
        reply = QMessageBox.question(
            self, "Cancel Order",
            f"Cancel order #{order['id']} for '{order['product_name']}'?\n"
            "Stock will be restored.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = cancel_order(order["id"], self._customer_id, "customer")
            if result["success"]:
                QMessageBox.information(
                    self, "Cancelled", "Order cancelled. Stock restored."
                )
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])


class PlaceOrderDialog(QDialog):

    def __init__(self, product, customer_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Place Order")
        self.setFixedWidth(420)
        self.setModal(True)
        self._product    = product
        self._customer_id = customer_id
        self._build()

    def _build(self):
        from app.services.order_service import place_order
        self._place_order_fn = place_order

        self.setStyleSheet("""
            QDialog { background:#12202e; }
            QLabel  { color:#c8dff0; font-size:13px; }
            QDoubleSpinBox, QComboBox, QTextEdit {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:6px; padding:8px 10px;
                color:#e8f5e9; font-size:13px;
            }
            QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border:1px solid #4895ef;
            }
            QComboBox QAbstractItemView {
                background:#1a2940; color:#e8f5e9;
                selection-background-color:#2d5fa6;
            }
        """)

        p = self._product
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel(f"Order: {p['name']}")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#4895ef;")
        layout.addWidget(title)

        info_row = QHBoxLayout()
        for txt in [
            f"Price: {format_currency(p['price'])} / {p['unit']}",
            f"Available: {p['stock_qty']} {p['unit']}",
        ]:
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size:12px;color:#7a9ab5;")
            info_row.addWidget(lbl)
        info_row.addStretch()
        layout.addLayout(info_row)
        layout.addWidget(_divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_qty = QDoubleSpinBox()
        self.f_qty.setMinimum(0.1)
        self.f_qty.setMaximum(float(p["stock_qty"]))
        self.f_qty.setSingleStep(0.5)
        self.f_qty.setValue(1.0)
        self.f_qty.setSuffix(f"  {p['unit']}")
        self.f_qty.valueChanged.connect(self._update_total)

        self.f_type = QComboBox()
        self.f_type.addItems(["instant", "advance"])

        self.f_notes = QTextEdit()
        self.f_notes.setFixedHeight(70)
        self.f_notes.setPlaceholderText("Special requests… (optional)")

        form.addRow("Quantity *",   self.f_qty)
        form.addRow("Order Type *", self.f_type)
        form.addRow("Notes",        self.f_notes)
        layout.addLayout(form)

        self.total_lbl = QLabel()
        self.total_lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#52b788;"
        )
        layout.addWidget(self.total_lbl)
        self._update_total()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("✅  Place Order")
        btns.setStyleSheet("""
            QPushButton {
                background:#2d6a4f; color:white; border:none;
                border-radius:6px; padding:8px 20px; font-size:13px;
            }
            QPushButton:hover { background:#40916c; }
        """)
        btns.accepted.connect(self._submit)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_total(self):
        total = round(self._product["price"] * self.f_qty.value(), 2)
        self.total_lbl.setText(f"Total:  {format_currency(total)}")

    def _submit(self):
        result = self._place_order_fn(
            customer_id=self._customer_id,
            product_id=self._product["id"],
            quantity=self.f_qty.value(),
            order_type=self.f_type.currentText(),
            notes=self.f_notes.toPlainText(),
        )
        if result["success"]:
            QMessageBox.information(
                self, "Order Placed!",
                f"✅ Order #{result['order_id']} placed successfully!\n"
                "Check 'My Orders' to track its status."
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Order Failed", result["message"])


def _make_btn(text, dark, light):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{dark}; color:white; border:none;
            border-radius:7px; font-size:12px; padding:0 14px;
        }}
        QPushButton:hover {{ background:{light}; }}
        QPushButton:disabled {{ background:#1a2940; color:#3a5a6a; }}
    """)
    return btn


def _combo_style():
    return """
        QComboBox {
            background:#1a2940; border:1px solid #2d4a6a;
            border-radius:7px; padding:0 10px;
            color:#e8f5e9; font-size:12px;
        }
        QComboBox::drop-down { border:none; }
        QComboBox QAbstractItemView {
            background:#1a2940; color:#e8f5e9;
            selection-background-color:#2d5fa6;
        }
    """


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line