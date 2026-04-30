# app/ui/farmer_orders_page.py
# "Orders" tab inside FarmerDashboard.
# Farmers can view incoming orders and advance their status.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QMessageBox, QFrame,
    QDialog, QVBoxLayout as QVBox
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, order_status_color
)
from app.services.order_service import (
    get_orders_for_farmer, advance_order_status,
    cancel_order, next_status, STATUS_PIPELINE
)
from app.ui.widgets.data_table import DataTable


class FarmerOrdersPage(QWidget):
    """Order management page for farmers — view and advance order statuses."""

    COLUMNS = ["ID", "Product", "Customer", "Qty", "Total", "Type", "Status", "Date"]

    def __init__(self):
        super().__init__()
        self._farmer_id = session.get_id()
        self._orders: list[dict] = []
        self._filtered_orders: list[dict] = []
        self._build()
        self.refresh()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title + filter row
        title_row = QHBoxLayout()
        title = QLabel("📋  Incoming Orders")
        title.setStyleSheet("font-size:20px;font-weight:bold;color:#52b788;")
        title_row.addWidget(title)
        title_row.addStretch()

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All", "placed", "confirmed", "harvested", "delivered", "cancelled"]
        )
        self.status_filter.setFixedWidth(150)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _action_btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        filter_lbl = QLabel("Filter:")
        filter_lbl.setStyleSheet("color:#7a9ab5;font-size:12px;")
        title_row.addWidget(filter_lbl)
        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # Result count
        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        # Table
        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_advance = _action_btn("▶  Advance Status", "#1b4332", "#2d6a4f")
        self.btn_advance.setEnabled(False)
        self.btn_advance.clicked.connect(self._advance_selected)

        self.btn_cancel = _action_btn("✖  Cancel", "#5a1a1a", "#8b0000")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_selected)

        # Status info label
        self.status_info = QLabel("")
        self.status_info.setStyleSheet("font-size:12px;color:#7a9ab5;")

        btn_row.addWidget(self.status_info)
        btn_row.addSpacing(16)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_advance)
        layout.addLayout(btn_row)

        layout.addWidget(self._build_pipeline_legend())

    def _build_pipeline_legend(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        lbl = QLabel("Pipeline:")
        lbl.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(lbl)

        for i, status in enumerate(STATUS_PIPELINE):
            color = order_status_color(status)
            dot = QLabel(f"● {status.capitalize()}")
            dot.setStyleSheet(f"font-size:11px;color:{color};")
            layout.addWidget(dot)
            if i < len(STATUS_PIPELINE) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size:11px;color:#2d4a6a;")
                layout.addWidget(arrow)
        layout.addStretch()
        return row

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        self._orders = get_orders_for_farmer(self._farmer_id)
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered_orders = (
            self._orders if sf == "All"
            else [o for o in self._orders if o["status"] == sf]
        )
        rows = []
        for o in self._filtered_orders:
            rows.append([
                o["id"],
                truncate(o["product_name"], 22),
                truncate(o["customer_name"], 20),
                f"{o['quantity']} {o['product_unit']}",
                format_currency(o["total_price"]),
                o["order_type"].capitalize(),
                o["status"].capitalize(),
                format_date(o["created_at"]),
            ])
        self.table.populate(rows)

        # Color the status column (index 6)
        for row_idx, o in enumerate(self._filtered_orders):
            self.table.color_cell(
                row_idx, 6, order_status_color(o["status"])
            )

        count = len(self._filtered_orders)
        self.result_count.setText(
            f"{count} order{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected_order(self) -> dict | None:
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered_orders):
            return None
        return self._filtered_orders[idx]

    def _on_selection_change(self):
        order = self._selected_order()
        if order is None:
            self.btn_advance.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.status_info.setText("")
            return

        status  = order["status"]
        nxt     = next_status(status)
        can_adv = nxt is not None and status != "cancelled"
        can_can = status not in ("delivered", "cancelled")

        self.btn_advance.setEnabled(can_adv)
        self.btn_cancel.setEnabled(can_can)

        if can_adv:
            color = order_status_color(nxt)
            self.status_info.setText(
                f"Next:  <span style='color:{color};font-weight:bold;'>"
                f"{nxt.capitalize()}</span>"
            )
            self.status_info.setTextFormat(Qt.RichText)
        else:
            self.status_info.setText(f"Status: {status.capitalize()} (final)")

    # ── Actions ────────────────────────────────────────────────────────────────

    def _advance_selected(self):
        order = self._selected_order()
        if not order:
            return
        nxt = next_status(order["status"])
        reply = QMessageBox.question(
            self, "Advance Order Status",
            f"Mark order #{order['id']} as '{nxt}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            result = advance_order_status(order["id"], self._farmer_id)
            if result["success"]:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])

    def _cancel_selected(self):
        order = self._selected_order()
        if not order:
            return
        reply = QMessageBox.question(
            self, "Cancel Order",
            f"Cancel order #{order['id']}?\nStock will be restored.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Farmers use agent-level cancel (can cancel any non-delivered order)
            result = cancel_order(order["id"], self._farmer_id, "agent")
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
