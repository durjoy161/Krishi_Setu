# app/ui/investor_dashboard.py  — Final (Module 8)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, role_color
from app.services.dashboard_service import get_investor_stats
from app.ui.base_dashboard import BaseDashboard
from app.ui.widgets.stat_card import StatCard
from app.ui.investor_investments_page import (
    InvestorOpportunitiesPage, InvestorPortfolioPage
)
from app.ui.investor_reports_page import InvestorReportsPage


class InvestorDashboard(BaseDashboard):

    def window_title(self):
        return "Krishi Setu — Investor Dashboard"

    def nav_items(self):
        return [
            ("🏠", "Overview",      InvestorOverviewPage(self)),
            ("🌱", "Opportunities", InvestorOpportunitiesPage()),
            ("📈", "My Portfolio",  InvestorPortfolioPage()),
            ("📊", "Reports",       InvestorReportsPage()),      # ← Module 8
        ]


class InvestorOverviewPage(QWidget):

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
        color = role_color("investor")

        greeting = QLabel(f"Welcome, {name}! 💰")
        greeting.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{color};"
        )
        layout.addWidget(greeting)
        sub = QLabel("Support local farmers and grow your portfolio.")
        sub.setStyleSheet("font-size:13px;color:#7a9ab5;margin-top:-10px;")
        layout.addWidget(sub)
        layout.addWidget(_divider())

        stats = get_investor_stats(session.get_id())
        row = QHBoxLayout()
        row.setSpacing(16)
        for card in [
            StatCard("💵", "Total Invested",
                     format_currency(stats["total_invested"]), color),
            StatCard("📈", "Active Investments",
                     str(stats["active_investments"]),         "#52b788"),
            StatCard("🌱", "Open Opportunities",
                     str(stats["open_opportunities"]),         "#4895ef"),
            StatCard("📊", "All Opportunities",
                     str(stats["total_opportunities"]),        "#f4a261"),
        ]:
            row.addWidget(card)
        layout.addLayout(row)

        layout.addWidget(_divider())
        lbl = QLabel("Getting Started")
        lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(lbl)
        for tip in [
            "🌱  Browse Opportunities to see farmers requesting funding.",
            "💰  Click 'Invest Now' to contribute to a project.",
            "📈  Track your active investments in My Portfolio.",
            "📊  View your full investment analytics in Reports.",
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
    return line# app/ui/investor_dashboard.py  — Final (Module 8)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import format_currency, role_color
from app.services.dashboard_service import get_investor_stats
from app.ui.base_dashboard import BaseDashboard
from app.ui.widgets.stat_card import StatCard
from app.ui.investor_investments_page import (
    InvestorOpportunitiesPage, InvestorPortfolioPage
)
from app.ui.investor_reports_page import InvestorReportsPage


class InvestorDashboard(BaseDashboard):

    def window_title(self):
        return "Krishi Setu — Investor Dashboard"

    def nav_items(self):
        return [
            ("🏠", "Overview",      InvestorOverviewPage(self)),
            ("🌱", "Opportunities", InvestorOpportunitiesPage()),
            ("📈", "My Portfolio",  InvestorPortfolioPage()),
            ("📊", "Reports",       InvestorReportsPage()),      # ← Module 8
        ]


class InvestorOverviewPage(QWidget):

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
        color = role_color("investor")

        greeting = QLabel(f"Welcome, {name}! 💰")
        greeting.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{color};"
        )
        layout.addWidget(greeting)
        sub = QLabel("Support local farmers and grow your portfolio.")
        sub.setStyleSheet("font-size:13px;color:#7a9ab5;margin-top:-10px;")
        layout.addWidget(sub)
        layout.addWidget(_divider())

        stats = get_investor_stats(session.get_id())
        row = QHBoxLayout()
        row.setSpacing(16)
        for card in [
            StatCard("💵", "Total Invested",
                     format_currency(stats["total_invested"]), color),
            StatCard("📈", "Active Investments",
                     str(stats["active_investments"]),         "#52b788"),
            StatCard("🌱", "Open Opportunities",
                     str(stats["open_opportunities"]),         "#4895ef"),
            StatCard("📊", "All Opportunities",
                     str(stats["total_opportunities"]),        "#f4a261"),
        ]:
            row.addWidget(card)
        layout.addLayout(row)

        layout.addWidget(_divider())
        lbl = QLabel("Getting Started")
        lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(lbl)
        for tip in [
            "🌱  Browse Opportunities to see farmers requesting funding.",
            "💰  Click 'Invest Now' to contribute to a project.",
            "📈  Track your active investments in My Portfolio.",
            "📊  View your full investment analytics in Reports.",
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