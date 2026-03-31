# app/ui/products_ui.py
# Products page: list, add, edit, delete products (farmer/agent/anyone can view)

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QDialog, QFormLayout, QLineEdit, QComboBox,
                              QDoubleSpinBox, QTextEdit, QMessageBox,
                              QHeaderView, QDateEdit, QAbstractItemView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import app.utils.session as session
from app.services import product_service
from app.ui.styles import STATUS_COLORS


class ProductDialog(QDialog):
    """Add / Edit product dialog."""

    def __init__(self, parent=None, product: dict = None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add New Product")
        self.setMinimumWidth(420)
        self.setStyleSheet("QDialog { background:#0f1923; } QLabel { color:#d8f3dc; }")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        def inp(placeholder=""):
            w = QLineEdit()
            w.setPlaceholderText(placeholder)
            w.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")
            return w

        self.name_inp = inp("e.g. Tomato")
        self.cat_inp = QComboBox()
        self.cat_inp.addItems(product_service.CATEGORIES)
        self.cat_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.desc_inp = QTextEdit()
        self.desc_inp.setPlaceholderText("Short description…")
        self.desc_inp.setFixedHeight(70)
        self.desc_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.price_inp = QDoubleSpinBox()
        self.price_inp.setRange(0.01, 999999)
        self.price_inp.setDecimals(2)
        self.price_inp.setPrefix("৳ ")
        self.price_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.stock_inp = QDoubleSpinBox()
        self.stock_inp.setRange(0, 999999)
        self.stock_inp.setDecimals(1)
        self.stock_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.unit_inp = QComboBox()
        self.unit_inp.addItems(["kg", "ltr", "piece", "dozen", "bag", "bundle"])
        self.unit_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.expiry_inp = QDateEdit()
        self.expiry_inp.setCalendarPopup(True)
        self.expiry_inp.setDate(QDate.currentDate().addMonths(3))
        self.expiry_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        # Pre-fill if editing
        if self.product:
            self.name_inp.setText(self.product["name"])
            idx = self.cat_inp.findText(self.product["category"])
            if idx >= 0: self.cat_inp.setCurrentIndex(idx)
            self.desc_inp.setText(self.product.get("description", ""))
            self.price_inp.setValue(self.product["price"])
            self.stock_inp.setValue(self.product["stock_qty"])
            uid = self.unit_inp.findText(self.product["unit"])
            if uid >= 0: self.unit_inp.setCurrentIndex(uid)
            if self.product.get("expiry_date"):
                d = QDate.fromString(self.product["expiry_date"], "yyyy-MM-dd")
                self.expiry_inp.setDate(d)

        layout.addRow("Name:", self.name_inp)
        layout.addRow("Category:", self.cat_inp)
        layout.addRow("Description:", self.desc_inp)
        layout.addRow("Price:", self.price_inp)
        layout.addRow("Stock Qty:", self.stock_inp)
        layout.addRow("Unit:", self.unit_inp)
        layout.addRow("Expiry Date:", self.expiry_inp)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background:#1a2940;color:#e76f51;border:1px solid #9b2226;border-radius:6px;padding:8px 16px;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("💾  Save Product")
        save_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:8px 20px;font-weight:bold;")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addRow(btn_row)

    def get_data(self):
        return {
            "name":        self.name_inp.text().strip(),
            "category":    self.cat_inp.currentText(),
            "description": self.desc_inp.toPlainText().strip(),
            "price":       self.price_inp.value(),
            "stock_qty":   self.stock_inp.value(),
            "unit":        self.unit_inp.currentText(),
            "expiry_date": self.expiry_inp.date().toString("yyyy-MM-dd"),
        }


class ProductsPage(QWidget):
    """Products listing with CRUD controls."""

    COLS = ["ID", "Name", "Category", "Price (৳)", "Stock", "Unit", "Expiry", "Farmer"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🌿  Products & Inventory")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        hdr.addWidget(title)
        hdr.addStretch()

        role = session.get_role()

        # Category filter
        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All Categories"] + product_service.CATEGORIES)
        self.cat_filter.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:6px 10px;color:#e8f5e9;min-width:140px;")
        self.cat_filter.currentIndexChanged.connect(self._apply_filter)
        hdr.addWidget(self.cat_filter)

        if role == "farmer":
            add_btn = QPushButton("➕  Add Product")
            add_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:7px;padding:8px 18px;font-weight:bold;")
            add_btn.clicked.connect(self._add_product)
            hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { background:#12202e; alternate-background-color:#172a3a;
                           gridline-color:#1b4332; border:none; border-radius:8px; }
            QHeaderView::section { background:#1b4332; color:#b7e4c7; padding:8px;
                                   border:none; font-weight:bold; }
            QTableWidget::item { padding:6px; }
        """)
        layout.addWidget(self.table)

        # Action row (for farmers)
        if role == "farmer":
            action_row = QHBoxLayout()
            action_row.addStretch()
            edit_btn = QPushButton("✏️  Edit Selected")
            edit_btn.setStyleSheet("background:#ca6702;color:white;border:none;border-radius:7px;padding:8px 16px;")
            edit_btn.clicked.connect(self._edit_product)
            del_btn = QPushButton("🗑️  Delete Selected")
            del_btn.setStyleSheet("background:#9b2226;color:white;border:none;border-radius:7px;padding:8px 16px;")
            del_btn.clicked.connect(self._delete_product)
            action_row.addWidget(edit_btn)
            action_row.addWidget(del_btn)
            layout.addLayout(action_row)

        self._all_products = []

    def refresh(self):
        """Reload product data from DB."""
        role = session.get_role()
        if role == "farmer":
            self._all_products = product_service.get_farmer_products(session.get_id())
        else:
            self._all_products = product_service.get_all_products()
        self._apply_filter()

    def _apply_filter(self):
        cat = self.cat_filter.currentText()
        if cat == "All Categories":
            filtered = self._all_products
        else:
            filtered = [p for p in self._all_products if p["category"] == cat]
        self._load_table(filtered)

    def _load_table(self, products):
        self.table.setRowCount(0)
        for row_idx, p in enumerate(products):
            self.table.insertRow(row_idx)
            values = [
                str(p["id"]),
                p["name"],
                p["category"],
                f"৳{p['price']:.2f}",
                f"{p['stock_qty']:.1f}",
                p["unit"],
                p.get("expiry_date", "—"),
                p.get("farmer_name", "—"),
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                # Highlight low stock
                if col_idx == 4 and p["stock_qty"] < 20:
                    item.setForeground(QColor("#e76f51"))
                self.table.setItem(row_idx, col_idx, item)
        self.table.setData = products   # Store for reference

    def _selected_product_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a product first.")
            return None
        return int(self.table.item(row, 0).text())

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if not d["name"]:
                QMessageBox.warning(self, "Invalid", "Product name is required.")
                return
            product_service.add_product(**d)
            self.refresh()

    def _edit_product(self):
        pid = self._selected_product_id()
        if pid is None: return
        p = product_service.get_product_by_id(pid)
        if not p: return
        dlg = ProductDialog(self, product=p)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            product_service.update_product(pid, **d)
            self.refresh()

    def _delete_product(self):
        pid = self._selected_product_id()
        if pid is None: return
        reply = QMessageBox.question(self, "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            product_service.delete_product(pid)
            self.refresh()
