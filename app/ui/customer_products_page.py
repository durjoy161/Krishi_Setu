# app/ui/customer_products_page.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QFrame, QDialog
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, format_date, truncate
from app.services.product_service import (
    get_all_available_products, VALID_CATEGORIES
)
from app.ui.widgets.data_table import DataTable


class CustomerProductsPage(QWidget):

    COLUMNS = ["#", "Product", "Category", "Price",
               "Stock", "Unit", "Farmer", "Expiry"]

    def __init__(self):
        super().__init__()
        self._products = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("🛍️  Browse Products")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#4895ef;")
        layout.addWidget(title)
        layout.addWidget(_divider())

        # Search row
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search products…")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:7px; padding:0 12px;
                color:#e8f5e9; font-size:13px;
            }
            QLineEdit:focus { border:1px solid #4895ef; }
        """)
        self.search_input.textChanged.connect(self.refresh)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All"] + VALID_CATEGORIES)
        self.category_filter.setFixedHeight(36)
        self.category_filter.setFixedWidth(160)
        self.category_filter.setStyleSheet("""
            QComboBox {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:7px; padding:0 12px;
                color:#e8f5e9; font-size:13px;
            }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#1a2940; color:#e8f5e9;
                selection-background-color:#2d5fa6;
            }
        """)
        self.category_filter.currentTextChanged.connect(self.refresh)

        btn_refresh = _make_btn("↻  Refresh", "#1a3a6c", "#2d5fa6")
        btn_refresh.clicked.connect(self.refresh)

        filter_row.addWidget(self.search_input, stretch=1)
        filter_row.addWidget(self.category_filter)
        filter_row.addWidget(btn_refresh)
        layout.addLayout(filter_row)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_detail = _make_btn("🔍  View Details", "#1a3a6c", "#2d5fa6")
        self.btn_detail.setEnabled(False)
        self.btn_detail.clicked.connect(self._show_detail)
        self.btn_order = _make_btn("🛒  Place Order", "#1b4332", "#2d6a4f")
        self.btn_order.setEnabled(False)
        self.btn_order.clicked.connect(self._place_order)
        btn_row.addWidget(self.btn_detail)
        btn_row.addWidget(self.btn_order)
        layout.addLayout(btn_row)

    def refresh(self):
        search   = self.search_input.text()
        category = self.category_filter.currentText()
        self._products = get_all_available_products(search, category)
        rows = []
        for p in self._products:
            rows.append([
                p["id"],
                truncate(p["name"], 28),
                p["category"],
                format_currency(p["price"]),
                str(p["stock_qty"]),
                p["unit"],
                truncate(p.get("farmer_name", "—"), 22),
                format_date(p["expiry_date"]) if p["expiry_date"] else "—",
            ])
        self.table.populate(rows)
        count = len(self._products)
        self.result_count.setText(
            f"{count} product{'s' if count != 1 else ''} found"
        )
        self._on_selection_change()

    def _selected_product(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._products):
            return None
        return self._products[idx]

    def _on_selection_change(self):
        has = self.table.get_selected_row_index() is not None
        self.btn_detail.setEnabled(has)
        self.btn_order.setEnabled(has)

    def _show_detail(self):
        p = self._selected_product()
        if p:
            ProductDetailDialog(p, parent=self).exec_()

    def _place_order(self):
        p = self._selected_product()
        if not p:
            return
        from app.ui.customer_orders_page import PlaceOrderDialog
        dlg = PlaceOrderDialog(
            product=p, customer_id=session.get_id(), parent=self
        )
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()


class ProductDetailDialog(QDialog):

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Product Details")
        self.setFixedWidth(420)
        self.setModal(True)
        self._build(product)

    def _build(self, p):
        self.setStyleSheet(
            "QDialog{background:#12202e;} QLabel{color:#c8dff0;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        name_lbl = QLabel(p.get("name", "—"))
        name_lbl.setStyleSheet(
            "font-size:18px;font-weight:bold;color:#4895ef;"
        )
        name_lbl.setWordWrap(True)
        layout.addWidget(name_lbl)
        layout.addWidget(_divider())

        for label, value in [
            ("Category",    p.get("category", "—")),
            ("Price",       format_currency(p.get("price", 0)) +
                            f" / {p.get('unit', '')}"),
            ("Available",   f"{p.get('stock_qty', 0)} {p.get('unit', '')}"),
            ("Farmer",      p.get("farmer_name", "—")),
            ("Farm",        p.get("farm_name") or "—"),
            ("Expiry Date", format_date(p["expiry_date"])
                            if p.get("expiry_date") else "—"),
            ("Listed On",   format_date(p.get("created_at", ""))),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;min-width:100px;"
            )
            val = QLabel(str(value))
            val.setStyleSheet("font-size:13px;color:#d0e8f5;")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)

        # Description block — plain and simple
        description = p.get("description", "")
        if description:
            layout.addWidget(_divider())
            desc_lbl = QLabel("Description")
            desc_lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;font-weight:bold;"
            )
            layout.addWidget(desc_lbl)
            desc_val = QLabel(description)
            desc_val.setStyleSheet("font-size:13px;color:#c8dff0;")
            desc_val.setWordWrap(True)
            layout.addWidget(desc_val)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background:#1a2940; color:#7a9ab5; border:none;
                border-radius:6px; font-size:13px; margin-top:8px;
            }
            QPushButton:hover { background:#2d4a6a; color:white; }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)


def _make_btn(text, dark, light):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(36)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{dark}; color:white; border:none;
            border-radius:7px; font-size:13px; padding:0 16px;
        }}
        QPushButton:hover {{ background:{light}; }}
        QPushButton:disabled {{ background:#1a2940; color:#3a5a6a; }}
    """)
    return btn


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line