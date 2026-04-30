# app/ui/farmer_products_page.py
# The Products tab page shown inside FarmerDashboard.
# Farmers can: view their products, add new ones, edit existing, delete.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QDialogButtonBox,
    QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, format_date, truncate
from app.services.product_service import (
    get_products_by_farmer, add_product,
    update_product, delete_product,
    VALID_CATEGORIES, VALID_UNITS
)
from app.ui.widgets.data_table import DataTable


class FarmerProductsPage(QWidget):
    """
    Full product management page for farmers.
    Shows a table of their products with Add / Edit / Delete buttons.
    """

    COLUMNS = ["#", "Name", "Category", "Price", "Stock", "Unit", "Expiry", "Added"]

    def __init__(self):
        super().__init__()
        self._farmer_id = session.get_id()
        self._products: list[dict] = []
        self._build()
        self.refresh()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── Title row ──────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("📦  My Products")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#52b788;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        self.btn_add = _action_btn("＋  Add Product", "#2d6a4f", "#40916c")
        self.btn_add.clicked.connect(self._open_add_dialog)
        title_row.addWidget(self.btn_add)
        layout.addLayout(title_row)

        # ── Divider ───────────────────────────────────────────────────────────
        layout.addWidget(_divider())

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        # ── Bottom action row ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_edit = _action_btn("✏️  Edit", "#1a3a6c", "#2d5fa6")
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._open_edit_dialog)

        self.btn_delete = _action_btn("🗑️  Delete", "#5a1a1a", "#8b0000")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_selected)

        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload products from DB and repopulate the table."""
        self._products = get_products_by_farmer(self._farmer_id)
        rows = []
        for p in self._products:
            rows.append([
                p["id"],
                truncate(p["name"], 30),
                p["category"],
                format_currency(p["price"]),
                p["stock_qty"],
                p["unit"],
                format_date(p["expiry_date"]) if p["expiry_date"] else "—",
                format_date(p["created_at"]),
            ])
        self.table.populate(rows)
        self._on_selection_change()

    def _selected_product(self) -> dict | None:
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._products):
            return None
        return self._products[idx]

    def _on_selection_change(self):
        has = self.table.get_selected_row_index() is not None
        self.btn_edit.setEnabled(has)
        self.btn_delete.setEnabled(has)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _open_add_dialog(self):
        dlg = ProductFormDialog(title="Add New Product", parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            result = add_product(
                farmer_id=self._farmer_id, **data
            )
            if result["success"]:
                QMessageBox.information(self, "Success", "Product added successfully!")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])

    def _open_edit_dialog(self):
        product = self._selected_product()
        if not product:
            return
        dlg = ProductFormDialog(
            title="Edit Product", product=product, parent=self
        )
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            result = update_product(
                product_id=product["id"],
                farmer_id=self._farmer_id,
                **data
            )
            if result["success"]:
                QMessageBox.information(self, "Success", "Product updated successfully!")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])

    def _delete_selected(self):
        product = self._selected_product()
        if not product:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{product['name']}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = delete_product(product["id"], self._farmer_id)
            if result["success"]:
                QMessageBox.information(self, "Deleted", "Product deleted.")
                self.refresh()
            else:
                QMessageBox.warning(self, "Cannot Delete", result["message"])


# ── Product Form Dialog ────────────────────────────────────────────────────────

class ProductFormDialog(QDialog):
    """
    Reusable Add / Edit product dialog.
    Pass product=dict to pre-fill fields for editing.
    """

    def __init__(self, title: str, product: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(460)
        self.setModal(True)
        self._product = product
        self._build()
        if product:
            self._populate(product)

    def _build(self):
        self.setStyleSheet("""
            QDialog { background:#12202e; }
            QLabel  { color:#c8dff0; font-size:13px; }
            QLineEdit, QComboBox, QTextEdit {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:6px; padding:8px 10px;
                color:#e8f5e9; font-size:13px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
                border:1px solid #52b788;
            }
            QComboBox QAbstractItemView {
                background:#1a2940; color:#e8f5e9;
                selection-background-color:#2d6a4f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title_lbl = QLabel(self.windowTitle())
        title_lbl.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#52b788;"
        )
        layout.addWidget(title_lbl)
        layout.addWidget(_divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_name     = QLineEdit()
        self.f_category = QComboBox()
        self.f_category.addItems(VALID_CATEGORIES)
        self.f_price    = QLineEdit()
        self.f_price.setPlaceholderText("e.g. 35.00")
        self.f_stock    = QLineEdit()
        self.f_stock.setPlaceholderText("e.g. 100")
        self.f_unit     = QComboBox()
        self.f_unit.addItems(VALID_UNITS)
        self.f_expiry   = QLineEdit()
        self.f_expiry.setPlaceholderText("YYYY-MM-DD  (optional)")
        self.f_desc     = QTextEdit()
        self.f_desc.setFixedHeight(80)
        self.f_desc.setPlaceholderText("Short description (optional)")

        form.addRow("Name *",        self.f_name)
        form.addRow("Category *",    self.f_category)
        form.addRow("Price (৳) *",  self.f_price)
        form.addRow("Stock *",       self.f_stock)
        form.addRow("Unit *",        self.f_unit)
        form.addRow("Expiry Date",   self.f_expiry)
        form.addRow("Description",   self.f_desc)

        layout.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        btns.setStyleSheet("""
            QPushButton {
                background:#2d6a4f; color:white; border:none;
                border-radius:6px; padding:8px 20px; font-size:13px;
            }
            QPushButton:hover { background:#40916c; }
            QPushButton[text="Cancel"] { background:#1a2940; color:#7a9ab5; }
        """)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, p: dict):
        self.f_name.setText(str(p.get("name", "")))
        idx = self.f_category.findText(p.get("category", ""))
        if idx >= 0:
            self.f_category.setCurrentIndex(idx)
        self.f_price.setText(str(p.get("price", "")))
        self.f_stock.setText(str(p.get("stock_qty", "")))
        idx_u = self.f_unit.findText(p.get("unit", "kg"))
        if idx_u >= 0:
            self.f_unit.setCurrentIndex(idx_u)
        self.f_expiry.setText(p.get("expiry_date") or "")
        self.f_desc.setPlainText(p.get("description") or "")

    def get_data(self) -> dict:
        return {
            "name":        self.f_name.text().strip(),
            "category":    self.f_category.currentText(),
            "price":       self.f_price.text().strip(),
            "stock_qty":   self.f_stock.text().strip(),
            "unit":        self.f_unit.currentText(),
            "expiry_date": self.f_expiry.text().strip(),
            "description": self.f_desc.toPlainText().strip(),
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _action_btn(text: str, color_dark: str, color_light: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(36)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{color_dark};color:white;border:none;
            border-radius:7px;font-size:13px;padding:0 16px;
        }}
        QPushButton:hover {{ background:{color_light}; }}
        QPushButton:disabled {{ background:#1a2940;color:#3a5a6a; }}
    """)
    return btn


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
