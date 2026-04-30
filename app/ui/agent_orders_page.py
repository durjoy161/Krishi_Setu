# app/ui/agent_orders_page.py
# "All Orders" tab inside AgentDashboard.
# Agents can view all orders platform-wide and cancel any non-delivered order.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt

from app.utils.helpers import (
    format_currency, format_date, truncate, order_status_color
)
from app.services.order_service import (
    get_all_orders, cancel_order, STATUS_PIPELINE
)
from app.ui.widgets.data_table import DataTable
import app.utils.session as session


class AgentOrdersPage(QWidget):
    """Platform-wide order view for agents."""

    COLUMNS = ["ID", "Product", "Customer", "Farmer", "Qty", "Total", "Status", "Date"]

    def __init__(self):
        super().__init__()
        self._orders: list[dict] = []
        self._filtered: list[dict] = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title + filters
        title_row = QHBoxLayout()
        title = QLabel("📋  All Orders")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#f4a261;")
        title_row.addWidget(title)
        title_row.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search product / customer…")
        self.search.setFixedHeight(34)
        self.search.setFixedWidth(230)
        self.search.setStyleSheet(_input_style())
        self.search.textChanged.connect(self._apply_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", "placed", "confirmed", "harvested", "delivered", "cancelled"]
        )
        self.status_filter.setFixedWidth(140)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _action_btn("↻", "#1a3a5c", "#2d4a7a")
        btn_refresh.setFixedWidth(36)
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(self.search)
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
        self.btn_cancel = _action_btn("✖  Cancel Order", "#5a1a1a", "#8b0000")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_selected)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        self._orders = get_all_orders()
        self._apply_filter()

    def _apply_filter(self):
        sf     = self.status_filter.currentText()
        search = self.search.text().strip().lower()

        self._filtered = [
            o for o in self._orders
            if (sf == "All" or o["status"] == sf)
            and (
                not search
                or search in o["product_name"].lower()
                or search in o["customer_name"].lower()
                or search in o["farmer_name"].lower()
            )
        ]

        rows = [[
            o["id"],
            truncate(o["product_name"], 22),
            truncate(o["customer_name"], 18),
            truncate(o["farmer_name"],   18),
            f"{o['quantity']} {o['product_unit']}",
            format_currency(o["total_price"]),
            o["status"].capitalize(),
            format_date(o["created_at"]),
        ] for o in self._filtered]

        self.table.populate(rows)
        for i, o in enumerate(self._filtered):
            self.table.color_cell(i, 6, order_status_color(o["status"]))

        count = len(self._filtered)
        self.result_count.setText(
            f"{count} order{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected_order(self) -> dict | None:
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        order = self._selected_order()
        can = order is not None and order["status"] not in ("delivered", "cancelled")
        self.btn_cancel.setEnabled(can)

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
            result = cancel_order(
                order["id"], session.get_id(), "agent"
            )
            if result["success"]:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _action_btn(text, dark, light) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{dark};color:white;border:none;
            border-radius:7px;font-size:12px;padding:0 14px;
        }}
        QPushButton:hover {{ background:{light}; }}
        QPushButton:disabled {{ background:#1a2940;color:#3a5a6a; }}
    """)
    return btn


def _input_style() -> str:
    return """
        QLineEdit {
            background:#1a2940;border:1px solid #2d4a6a;
            border-radius:7px;padding:0 12px;color:#e8f5e9;font-size:12px;
        }
        QLineEdit:focus { border:1px solid #f4a261; }
    """


def _combo_style() -> str:
    return """
        QComboBox {
            background:#1a2940;border:1px solid #2d4a6a;
            border-radius:7px;padding:0 10px;color:#e8f5e9;font-size:12px;
        }
        QComboBox::drop-down { border:none; }
        QComboBox QAbstractItemView {
            background:#1a2940;color:#e8f5e9;
            selection-background-color:#2d5fa6;
        }
    """


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
