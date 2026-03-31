# app/ui/orders_ui.py
# Orders page: place orders, track status, cancel, advance status (agent/farmer)

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QDialog, QFormLayout, QComboBox, QDoubleSpinBox,
                              QTextEdit, QMessageBox, QHeaderView, QTabWidget,
                              QAbstractItemView, QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import app.utils.session as session
from app.services import order_service, product_service
from app.ui.styles import STATUS_COLORS


STATUS_DISPLAY = {
    "placed":    "🟦 Placed",
    "confirmed": "🟧 Confirmed",
    "harvested": "🟨 Harvested",
    "delivered": "🟩 Delivered",
    "cancelled": "🔴 Cancelled",
}


class PlaceOrderDialog(QDialog):
    """Dialog to place a new order."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Place New Order")
        self.setMinimumWidth(440)
        self.setStyleSheet("QDialog{background:#0f1923;} QLabel{color:#d8f3dc;}")
        self._products = product_service.get_all_products()
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def _style(w):
            w.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")
            return w

        # Product selector
        self.product_cb = QComboBox()
        for p in self._products:
            self.product_cb.addItem(
                f"{p['name']}  ({p['category']})  —  ৳{p['price']:.2f}/{p['unit']}  [{p['stock_qty']:.0f} in stock]",
                userData=p
            )
        _style(self.product_cb)
        self.product_cb.currentIndexChanged.connect(self._update_total)

        # Quantity
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.1, 10000)
        self.qty_spin.setValue(1)
        self.qty_spin.setDecimals(1)
        _style(self.qty_spin)
        self.qty_spin.valueChanged.connect(self._update_total)

        # Order type
        self.type_cb = QComboBox()
        self.type_cb.addItems(["instant", "advance"])
        _style(self.type_cb)

        # Total label
        self.total_lbl = QLabel("৳ 0.00")
        self.total_lbl.setStyleSheet("font-size:18px;font-weight:bold;color:#52b788;")

        # Notes
        self.notes_inp = QTextEdit()
        self.notes_inp.setFixedHeight(60)
        self.notes_inp.setPlaceholderText("Optional delivery notes…")
        _style(self.notes_inp)

        layout.addRow("Product:", self.product_cb)
        layout.addRow("Quantity:", self.qty_spin)
        layout.addRow("Order Type:", self.type_cb)
        layout.addRow("Total Price:", self.total_lbl)
        layout.addRow("Notes:", self.notes_inp)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background:#1a2940;color:#e76f51;border:1px solid #9b2226;border-radius:6px;padding:8px 14px;")
        cancel_btn.clicked.connect(self.reject)
        place_btn = QPushButton("🛒  Place Order")
        place_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold;")
        place_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(place_btn)
        layout.addRow(btn_row)
        self._update_total()

    def _update_total(self):
        p = self.product_cb.currentData()
        if p:
            total = p["price"] * self.qty_spin.value()
            self.total_lbl.setText(f"৳ {total:,.2f}")

    def _confirm(self):
        p = self.product_cb.currentData()
        if not p:
            QMessageBox.warning(self, "Error", "No product selected.")
            return
        if self.qty_spin.value() > p["stock_qty"] and self.type_cb.currentText() == "instant":
            QMessageBox.warning(self, "Insufficient Stock",
                f"Only {p['stock_qty']:.0f} {p['unit']} in stock.")
            return
        self.accept()

    def get_data(self):
        p = self.product_cb.currentData()
        return {
            "product_id":  p["id"],
            "farmer_id":   p["farmer_id"],
            "quantity":    self.qty_spin.value(),
            "unit_price":  p["price"],
            "order_type":  self.type_cb.currentText(),
            "notes":       self.notes_inp.toPlainText().strip(),
        }


class OrdersPage(QWidget):
    """Orders management page."""

    COLS = ["ID", "Product", "Farmer", "Qty", "Total (৳)", "Type", "Status", "Date"]
    COLS_ALL = ["ID", "Customer", "Product", "Farmer", "Qty", "Total (৳)", "Type", "Status", "Date"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📦  Orders")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        hdr.addWidget(title)
        hdr.addStretch()

        role = session.get_role()
        if role == "customer":
            self.place_btn = QPushButton("🛒  Place New Order")
            self.place_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:7px;padding:8px 18px;font-weight:bold;")
            self.place_btn.clicked.connect(self._place_order)
            hdr.addWidget(self.place_btn)
        layout.addLayout(hdr)

        # Tabs: my orders / all orders (agent sees both)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #1b4332;border-radius:8px;background:#12202e;}
            QTabBar::tab{background:#0d2137;color:#74c69d;padding:8px 18px;border-radius:6px 6px 0 0;margin-right:3px;}
            QTabBar::tab:selected{background:#1b4332;color:white;font-weight:bold;}
        """)

        # My orders tab
        self._my_table = self._make_table(self.COLS)
        self.tabs.addTab(self._my_table, "My Orders" if role != "agent" else "All Orders")

        # Farmer orders (farmers see their product orders)
        if role == "farmer":
            self._all_table = self._make_table(self.COLS_ALL)
            self.tabs.addTab(self._all_table, "Orders for My Products")

        layout.addWidget(self.tabs)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.addStretch()
        if role in ("agent", "farmer"):
            adv_btn = QPushButton("▶  Advance Status")
            adv_btn.setStyleSheet("background:#ca6702;color:white;border:none;border-radius:7px;padding:8px 16px;")
            adv_btn.clicked.connect(self._advance_status)
            action_row.addWidget(adv_btn)
        if role in ("customer", "agent"):
            cancel_btn = QPushButton("✖  Cancel Order")
            cancel_btn.setStyleSheet("background:#9b2226;color:white;border:none;border-radius:7px;padding:8px 16px;")
            cancel_btn.clicked.connect(self._cancel_order)
            action_row.addWidget(cancel_btn)
        layout.addLayout(action_row)

    def _make_table(self, cols):
        t = QTableWidget()
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setStyleSheet("""
            QTableWidget{background:#12202e;alternate-background-color:#172a3a;
                         gridline-color:#1b4332;border:none;}
            QHeaderView::section{background:#1b4332;color:#b7e4c7;padding:8px;border:none;font-weight:bold;}
            QTableWidget::item{padding:6px;}
        """)
        return t

    def _load_table(self, table, orders, include_customer=False):
        table.setRowCount(0)
        for i, o in enumerate(orders):
            table.insertRow(i)
            if include_customer:
                vals = [str(o["id"]), o.get("customer_name","—"), o.get("product_name","—"),
                        o.get("farmer_name","—"), f"{o['quantity']:.1f}",
                        f"৳{o['total_price']:,.2f}", o["order_type"],
                        STATUS_DISPLAY.get(o["status"], o["status"]), o["created_at"][:10]]
            else:
                vals = [str(o["id"]), o.get("product_name","—"), o.get("farmer_name","—"),
                        f"{o['quantity']:.1f}", f"৳{o['total_price']:,.2f}",
                        o["order_type"], STATUS_DISPLAY.get(o["status"], o["status"]), o["created_at"][:10]]
            for ci, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                # Color status cell
                if v in STATUS_DISPLAY.values():
                    color = STATUS_COLORS.get(o["status"], "#ffffff")
                    item.setForeground(QColor(color))
                table.setItem(i, ci, item)

    def refresh(self):
        role = session.get_role()
        uid = session.get_id()
        if role == "customer":
            orders = order_service.get_customer_orders(uid)
            self._load_table(self._my_table, orders)
        elif role == "farmer":
            my_orders = order_service.get_farmer_orders(uid)
            self._load_table(self._my_table, my_orders, include_customer=True)
            all_orders = order_service.get_all_orders()
            self._load_table(self._all_table, all_orders, include_customer=True)
        elif role == "agent":
            all_orders = order_service.get_all_orders()
            self._load_table(self._my_table, all_orders, include_customer=True)

    def _current_order_id(self):
        tab = self.tabs.currentWidget()
        row = tab.currentRow() if isinstance(tab, QTableWidget) else -1
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an order first.")
            return None
        return int(tab.item(row, 0).text())

    def _place_order(self):
        dlg = PlaceOrderDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            order_service.place_order(**d)
            QMessageBox.information(self, "Order Placed", "✅ Your order has been placed successfully!")
            self.refresh()

    def _advance_status(self):
        oid = self._current_order_id()
        if oid is None: return
        if order_service.advance_order_status(oid):
            QMessageBox.information(self, "Updated", "✅ Order status has been advanced.")
            self.refresh()
        else:
            QMessageBox.warning(self, "Cannot Advance", "Order is already delivered or cancelled.")

    def _cancel_order(self):
        oid = self._current_order_id()
        if oid is None: return
        reply = QMessageBox.question(self, "Confirm Cancel", "Cancel this order?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if order_service.cancel_order(oid):
                QMessageBox.information(self, "Cancelled", "Order cancelled.")
                self.refresh()
            else:
                QMessageBox.warning(self, "Cannot Cancel", "Only placed or confirmed orders can be cancelled.")
