# app/ui/investor_reports_page.py
# Reports & Analytics tab for InvestorDashboard.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, investment_status_color
)
from app.services.report_service import get_investor_report_data
from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.bar_chart import BarChart
from app.ui.widgets.data_table import DataTable


class InvestorReportsPage(QWidget):

    def __init__(self):
        super().__init__()
        self._investor_id = session.get_id()
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
        # Clear existing widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        data = get_investor_report_data(self._investor_id)

        # ── Title ──────────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("📊  My Investment Reports")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#9b5de5;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        btn_ref = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_ref.clicked.connect(self.refresh)
        title_row.addWidget(btn_ref)
        self._layout.addLayout(title_row)
        self._layout.addWidget(_divider())

        # ── Summary Cards ──────────────────────────────────────────────────────
        self._layout.addWidget(_section("Portfolio Summary"))

        summary = data.get("summary", {})
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        for icon, label, key, color in [
            ("💵", "Total Invested",     "total_invested",     "#9b5de5"),
            ("📈", "Active Investments", "active_count",       "#4895ef"),
            ("✅", "Funded Projects",    "funded_count",       "#52b788"),
            ("🔒", "Closed Projects",    "closed_count",       "#888888"),
            ("🌱", "Open Projects",      "open_count",         "#4895ef"),
            ("📊", "Total Projects",     "total_count",        "#f4a261"),
        ]:
            val = summary.get(key, 0)
            display = (
                format_currency(val)
                if key == "total_invested"
                else str(val)
            )
            cards_row.addWidget(StatCard(icon, label, display, color))
        self._layout.addLayout(cards_row)

        # ── Contribution Bar Chart ─────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("My Contributions by Project"))

        contributions = data.get("contributions", [])
        if contributions:
            chart = BarChart(color="#9b5de5")
            chart.setFixedHeight(230)
            chart.set_data(
                labels=[truncate(c["title"], 12) for c in contributions],
                values=[c["my_contribution"]     for c in contributions],
            )
            self._layout.addWidget(chart)
        else:
            self._layout.addWidget(
                _no_data("No contributions yet.")
            )

        # ── Status Breakdown ───────────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Portfolio by Status"))

        status_data = data.get("status_breakdown", [])
        if status_data:
            status_row = QHBoxLayout()
            status_row.setSpacing(14)
            for s in status_data:
                color = investment_status_color(s["status"])
                invested = format_currency(s["total_invested"])
                status_row.addWidget(
                    StatCard("●",
                             f"{s['status'].capitalize()} ({s['count']})",
                             invested, color)
                )
            status_row.addStretch()
            self._layout.addLayout(status_row)
        else:
            self._layout.addWidget(_no_data("No portfolio data."))

        # ── Full Portfolio Table ───────────────────────────────────────────────
        self._layout.addWidget(_divider())
        self._layout.addWidget(_section("Full Portfolio Details"))

        portfolio = data.get("portfolio", [])
        if portfolio:
            table = DataTable([
                "Project", "Farmer", "My Contribution",
                "Goal", "Raised", "ROI %", "Status", "Date"
            ])
            table.setFixedHeight(260)
            rows = []
            for p in portfolio:
                rows.append([
                    truncate(p["title"], 22),
                    truncate(p.get("farmer_name", "—"), 18),
                    format_currency(p.get("my_contribution", 0)),
                    format_currency(p["goal_amount"]),
                    format_currency(p["raised_amount"]),
                    f"{p['expected_roi']}%",
                    p["status"].capitalize(),
                    format_date(p.get("contributed_at", "")),
                ])
            table.populate(rows)
            for i, p in enumerate(portfolio):
                table.color_cell(
                    i, 6, investment_status_color(p["status"])
                )
            self._layout.addWidget(table)
        else:
            self._layout.addWidget(
                _no_data("No portfolio data yet.")
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
