# app/ui/agent_dashboard.py  — Final (Module 8)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, role_color
from app.services.dashboard_service import get_agent_stats
from app.ui.base_dashboard import BaseDashboard
from app.ui.widgets.stat_card import StatCard
from app.ui.agent_orders_page import AgentOrdersPage
from app.ui.payments_page import AgentPaymentsPage
from app.ui.agent_users_page import AgentUsersPage
from app.ui.agent_reports_page import AgentReportsPage


class AgentDashboard(BaseDashboard):

    def window_title(self):
        return "Krishi Setu — Agent Dashboard"

    def nav_items(self):
        return [
            ("🏠", "Overview",     AgentOverviewPage(self)),
            ("👥", "Manage Users", AgentUsersPage()),
            ("📋", "All Orders",   AgentOrdersPage()),
            ("💳", "Payments",     AgentPaymentsPage()),
            ("📊", "Reports",      AgentReportsPage()),    # ← Module 8
        ]


class AgentOverviewPage(QWidget):

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
        color = role_color("agent")

        greeting = QLabel(f"Hello, {name}! 🤝")
        greeting.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{color};"
        )
        layout.addWidget(greeting)
        sub = QLabel("Platform overview — visibility across all roles.")
        sub.setStyleSheet("font-size:13px;color:#7a9ab5;margin-top:-10px;")
        layout.addWidget(sub)
        layout.addWidget(_divider())

        stats = get_agent_stats()
        row = QHBoxLayout()
        row.setSpacing(16)
        for card in [
            StatCard("🌾", "Farmers",
                     str(stats["total_farmers"]),   color),
            StatCard("🛒", "Customers",
                     str(stats["total_customers"]), "#4895ef"),
            StatCard("📋", "Total Orders",
                     str(stats["total_orders"]),    "#9b5de5"),
            StatCard("⏳", "Pending Orders",
                     str(stats["pending_orders"]),  "#f4a261"),
            StatCard("💵", "Total Revenue",
                     format_currency(stats["total_revenue"]), "#52b788"),
        ]:
            row.addWidget(card)
        layout.addLayout(row)

        layout.addWidget(_divider())
        lbl = QLabel("Agent Responsibilities")
        lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(lbl)
        for tip in [
            "👥  Manage Users — view, search, and toggle user accounts.",
            "📋  All Orders — monitor and update order statuses.",
            "💳  Payments — record and track all platform payments.",
            "📊  Reports — view platform-wide analytics and charts.",
        ]:
            t = QLabel(tip)
            t.setStyleSheet("font-size:12px;color:#7a9ab5;padding:6px 0;")
            t.setWordWrap(True)
            layout.addWidget(t)

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