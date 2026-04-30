# app/ui/agent_reports_page.py
# Reports & Analytics tab for AgentDashboard — platform-wide view.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

from app.utils.helpers import (
    format_currency, order_status_color, truncate
)
from app.services.report_service import (
    get_platform_sales_summary,
    get_top_products_platform,
    get_monthly_revenue_platform,
    get_revenue_by_category,
    get_order_status_breakdown_platform,
    get_top_farmers_by_revenue,
)
from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.bar_chart import BarChart
from app.ui.widgets.data_table import DataTable


class AgentReportsPage(QWidget):

    def __init__(self):
        super().__init__()
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
        # Clear
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── Title ──────────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("📊  Platform Reports & Analytics")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#f4a261;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        btn_ref = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_ref.clicked.connect(self.refresh)
        title_row.addWidget(btn_ref)
        self._layout.addLayout(title_row)
        self._layout.addWidget(_divider())

        # ── Platform Summary ───────────────────────────────────────────────────
        summary = get_platform_sales_summary()
        self._layout.addWidget(_section("Platform Overview"))

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        for icon, label, key, color in [
            ("💵", "Total Revenue",  "total_revenue",  "#52b788"),
            ("⏳", "Outstanding",    "outstanding",    "#e63946"),
            ("📋", "Total Orders",   "total_orders",   "#4895ef"),
            ("✅", "Delivered",      "delivered",      "#52b788"),
            ("❌", "Cancelled",      "cancelled",      "#e63946"),
            ("👥", "Total Users",    "total_users",    "#9b5de5"),
            ("📦", "Products",       "total_products", "#f4a261"),
            ("💰", "Total Invested", "total_invested", "#52b788"),
        ]:
            val = summary.get(key, 0)
            display = (
                format_currency(val)
                if key in ("total_revenue", "outstanding", "total_invested")
                else str(val)
            )
            row1.addWidget(StatCard(icon, label, display, color))
        self._layout.addLayout(row1)

        # ── Monthly Revenue Chart ──────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Platform Revenue — Last 6 Months"))

        monthly = get_monthly_revenue_platform()
        if monthly:
            chart = BarChart(color="#f4a261")
            chart.setFixedHeight(230)
            chart.set_data(
                labels=[r["month"][-5:] for r in monthly],
                values=[r["revenue"]    for r in monthly],
            )
            self._layout.addWidget(chart)
        else:
            self._layout.addWidget(
                _no_data("No revenue data for the last 6 months.")
            )

        # ── Two-column section: Category + Status ──────────────────────────────
        self._layout.addWidget(_divider())
        two_col = QHBoxLayout()
        two_col.setSpacing(24)

        # Category Revenue Chart
        left_col = QVBoxLayout()
        left_col.addWidget(_section("Revenue by Category"))
        cats = get_revenue_by_category()
        if cats:
            cat_chart = BarChart(color="#9b5de5")
            cat_chart.setFixedHeight(200)
            cat_chart.set_data(
                labels=[c["category"]     for c in cats],
                values=[c["total_revenue"] for c in cats],
            )
            left_col.addWidget(cat_chart)
        else:
            left_col.addWidget(_no_data("No category data."))

        # Order Status Chart
        right_col = QVBoxLayout()
        right_col.addWidget(_section("Orders by Status"))
        statuses = get_order_status_breakdown_platform()
        if statuses:
            status_row = QHBoxLayout()
            status_row.setSpacing(10)
            for s in statuses:
                color = order_status_color(s["status"])
                status_row.addWidget(
                    StatCard("●", s["status"].capitalize(),
                             str(s["count"]), color)
                )
            status_row.addStretch()
            right_col.addLayout(status_row)
        else:
            right_col.addWidget(_no_data("No order data."))

        left_w = QWidget()
        left_w.setLayout(left_col)
        right_w = QWidget()
        right_w.setLayout(right_col)
        two_col.addWidget(left_w, stretch=3)
        two_col.addWidget(right_w, stretch=2)
        self._layout.addLayout(two_col)

        # ── Top Products Table ─────────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Top Products by Revenue"))

        top_products = get_top_products_platform()
        if top_products:
            pt = DataTable(
                ["Product", "Category", "Farmer",
                 "Orders", "Qty Sold", "Revenue"]
            )
            pt.setFixedHeight(230)
            pt.populate([
                [
                    truncate(p["name"], 22),
                    p["category"],
                    truncate(p["farmer_name"], 18),
                    str(p["order_count"]),
                    str(round(p["total_qty"], 1)),
                    format_currency(p["total_revenue"]),
                ]
                for p in top_products
            ])
            self._layout.addWidget(pt)
        else:
            self._layout.addWidget(_no_data("No product sales data."))

        # ── Top Farmers Table ──────────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Top Farmers by Revenue"))

        top_farmers = get_top_farmers_by_revenue()
        if top_farmers:
            ft = DataTable(
                ["Farmer", "Farm", "Orders", "Revenue"]
            )
            ft.setFixedHeight(200)
            ft.populate([
                [
                    truncate(f["full_name"], 24),
                    truncate(f.get("farm_name") or "—", 20),
                    str(f["order_count"]),
                    format_currency(f["revenue"]),
                ]
                for f in top_farmers
            ])
            self._layout.addWidget(ft)
        else:
            self._layout.addWidget(_no_data("No farmer data."))

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
