# app/ui/customer_dashboard.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, role_color
from app.services.dashboard_service import get_customer_stats
from app.ui.base_dashboard import BaseDashboard
from app.ui.widgets.stat_card import StatCard
from app.ui.customer_products_page import CustomerProductsPage
from app.ui.customer_orders_page import CustomerOrdersPage
from app.ui.payments_page import CustomerPaymentsPage


class CustomerDashboard(BaseDashboard):

    def window_title(self):
        return "Krishi Setu — Customer Dashboard"

    def nav_items(self):
        return [
            ("🏠", "Overview",  CustomerOverviewPage(self)),
            ("🛍️", "Products",  CustomerProductsPage()),
            ("📋", "My Orders", CustomerOrdersPage()),
            ("💳", "Payments",  CustomerPaymentsPage()),
        ]


class CustomerOverviewPage(QWidget):

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
        color = role_color("customer")

        greeting = QLabel(f"Welcome back, {name}! 🛒")
        greeting.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{color};"
        )
        layout.addWidget(greeting)

        sub = QLabel("Fresh produce from local farmers, delivered to you.")
        sub.setStyleSheet("font-size:13px;color:#7a9ab5;margin-top:-10px;")
        layout.addWidget(sub)

        layout.addWidget(_divider())

        stats = get_customer_stats(session.get_id())
        row = QHBoxLayout()
        row.setSpacing(16)
        for card in [
            StatCard("📋", "Total Orders",
                     str(stats["total_orders"]), color),
            StatCard("⏳", "Active Orders",
                     str(stats["active_orders"]), "#f4a261"),
            StatCard("💵", "Total Spent",
                     format_currency(stats["total_spent"]), "#9b5de5"),
            StatCard("🌿", "Products Available",
                     str(stats["available_products"]), "#52b788"),
        ]:
            row.addWidget(card)
        layout.addLayout(row)

        layout.addWidget(_divider())

        tips_lbl = QLabel("What you can do")
        tips_lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(tips_lbl)

        for tip in [
            "🛍️  Browse Products to explore what local farmers are selling.",
            "📋  Track your active orders in the My Orders tab.",
            "💳  View your full payment history in the Payments tab.",
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