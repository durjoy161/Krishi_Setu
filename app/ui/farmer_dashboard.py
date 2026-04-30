# app/ui/farmer_dashboard.py  — Final (Module 8)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, role_color
from app.services.dashboard_service import get_farmer_stats
from app.ui.base_dashboard import BaseDashboard
from app.ui.widgets.stat_card import StatCard
from app.ui.farmer_products_page import FarmerProductsPage
from app.ui.farmer_orders_page import FarmerOrdersPage
from app.ui.payments_page import FarmerPaymentsPage
from app.ui.farmer_investments_page import FarmerInvestmentsPage
from app.ui.farmer_reports_page import FarmerReportsPage


class FarmerDashboard(BaseDashboard):

    def window_title(self):
        return "Krishi Setu — Farmer Dashboard"

    def nav_items(self):
        return [
            ("🏠", "Overview",    FarmerOverviewPage(self)),
            ("📦", "Products",    FarmerProductsPage()),
            ("📋", "Orders",      FarmerOrdersPage()),
            ("💳", "Payments",    FarmerPaymentsPage()),
            ("💰", "Investments", FarmerInvestmentsPage()),
            ("📊", "Reports",     FarmerReportsPage()),     # ← Module 8
        ]


class FarmerOverviewPage(QWidget):

    def __init__(self, dashboard):
        super().__init__()
        self._build()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        name  = session.get_name()
        color = role_color("farmer")

        greeting = QLabel(f"Good day, {name}! 🌾")
        greeting.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{color};"
        )
        layout.addWidget(greeting)
        sub = QLabel("Here's a snapshot of your farm activity.")
        sub.setStyleSheet("font-size:13px;color:#7a9ab5;margin-top:-10px;")
        layout.addWidget(sub)
        layout.addWidget(_divider())

        stats = get_farmer_stats(session.get_id())
        row = QHBoxLayout()
        row.setSpacing(16)
        for card in [
            StatCard("📦", "Products",
                     str(stats["total_products"]),   color),
            StatCard("📋", "Total Orders",
                     str(stats["total_orders"]),     "#4895ef"),
            StatCard("⏳", "Pending Orders",
                     str(stats["pending_orders"]),   "#f4a261"),
            StatCard("💵", "Revenue",
                     format_currency(stats["total_revenue"]), "#9b5de5"),
            StatCard("🌱", "Open Investments",
                     str(stats["active_investments"]), "#52b788"),
        ]:
            row.addWidget(card)
        layout.addLayout(row)

        layout.addWidget(_divider())
        tips = QLabel("Quick Tips")
        tips.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(tips)
        for tip in [
            "📦  Use Products to add items and manage stock.",
            "📋  Check Orders to confirm and track deliveries.",
            "💳  Record incoming payments in the Payments tab.",
            "💰  Request funding from investors.",
            "📊  View your sales analytics in Reports.",
        ]:
            lbl = QLabel(tip)
            lbl.setStyleSheet("font-size:12px;color:#7a9ab5;padding:6px 0;")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        layout.addStretch()
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line