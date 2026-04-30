# app/ui/farmer_reports_page.py
# Reports & Analytics tab for FarmerDashboard.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, order_status_color, truncate
)
from app.services.report_service import (
    get_farmer_sales_summary,
    get_top_products_for_farmer,
    get_monthly_revenue_for_farmer,
    get_order_status_breakdown_farmer,
)
from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.bar_chart import BarChart
from app.ui.widgets.data_table import DataTable


class FarmerReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        self._farmer_id = session.get_id()
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")

        self._content = QWidget()
        self._content.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(28, 24, 28, 28)
        self._layout.setSpacing(24)

        scroll.setWidget(self._content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        # Clear existing content
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        fid = self._farmer_id

        # ── Title ──────────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("📊  My Reports & Analytics")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#52b788;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)
        title_row.addWidget(btn_refresh)
        self._layout.addLayout(title_row)
        self._layout.addWidget(_divider())

        # ── Summary cards ──────────────────────────────────────────────────────
        summary = get_farmer_sales_summary(fid)
        sec_lbl = _section("Sales Summary")
        self._layout.addWidget(sec_lbl)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        for icon, label, key, color in [
            ("💵", "Total Revenue",  "total_revenue",  "#52b788"),
            ("⏳", "Outstanding",    "outstanding",    "#e63946"),
            ("📋", "Total Orders",   "total_orders",   "#4895ef"),
            ("✅", "Delivered",      "delivered",      "#52b788"),
            ("❌", "Cancelled",      "cancelled",      "#e63946"),
            ("🕒", "Pending",        "pending",        "#f4a261"),
        ]:
            val = summary.get(key, 0)
            display = (
                format_currency(val)
                if key in ("total_revenue", "outstanding")
                else str(val)
            )
            cards_row.addWidget(StatCard(icon, label, display, color))
        self._layout.addLayout(cards_row)

        # ── Monthly Revenue Chart ──────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Revenue — Last 6 Months"))

        monthly = get_monthly_revenue_for_farmer(fid)
        if monthly:
            chart = BarChart(color="#52b788")
            chart.setFixedHeight(220)
            chart.set_data(
                labels=[r["month"][-5:] for r in monthly],
                values=[r["revenue"] for r in monthly],
            )
            self._layout.addWidget(chart)
        else:
            self._layout.addWidget(
                _no_data("No revenue data for the last 6 months.")
            )

        # ── Order Status Breakdown ─────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Order Status Breakdown"))

        breakdown = get_order_status_breakdown_farmer(fid)
        if breakdown:
            status_row = QHBoxLayout()
            status_row.setSpacing(14)
            for row in breakdown:
                color = order_status_color(row["status"])
                status_row.addWidget(
                    StatCard("●", row["status"].capitalize(),
                             str(row["count"]), color)
                )
            status_row.addStretch()
            self._layout.addLayout(status_row)
        else:
            self._layout.addWidget(_no_data("No orders yet."))

        # ── Top Products Table ─────────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Top Products by Revenue"))

        top = get_top_products_for_farmer(fid)
        if top:
            table = DataTable(
                ["Product", "Orders", "Qty Sold", "Revenue", "Unit"]
            )
            table.setFixedHeight(220)
            rows = []
            for p in top:
                rows.append([
                    truncate(p["name"], 28),
                    str(p["order_count"]),
                    str(round(p["total_qty"], 1)),
                    format_currency(p["total_revenue"]),
                    p["unit"],
                ])
            table.populate(rows)
            self._layout.addWidget(table)
        else:
            self._layout.addWidget(
                _no_data("No sales data yet.")
            )

        self._layout.addStretch()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size:14px;font-weight:bold;color:#d0e8f5;"
    )
    return lbl


def _no_data(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size:13px;color:#2d4a6a;padding:12px 0;"
    )
    return lbl


def _btn(text, dark, light):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(32)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{dark}; color:white; border:none;
            border-radius:6px; font-size:12px; padding:0 12px;
        }}
        QPushButton:hover {{ background:{light}; }}
    """)
    return btn


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
