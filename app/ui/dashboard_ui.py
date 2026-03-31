# app/ui/dashboard_ui.py
# Role-aware dashboard with stat cards and recent activity summary

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGridLayout, QSizePolicy, QSpacerItem,
                              QScrollArea)
from PyQt5.QtCore import Qt
import app.utils.session as session
from app.services.report_service import get_dashboard_stats


class StatCard(QWidget):
    """A single stat card widget."""

    def __init__(self, icon: str, label: str, value: str, color: str = "#52b788"):
        super().__init__()
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QWidget#StatCard {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1b4332,stop:1 #0d2137);
                border-radius: 14px;
                border: 1px solid #2d6a4f;
                min-width: 180px;
                min-height: 100px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 28px;")

        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("font-size: 11px; color: #95d5b2; letter-spacing: 0.5px;")

        layout.addWidget(icon_lbl)
        layout.addWidget(val_lbl)
        layout.addWidget(name_lbl)


class DashboardPage(QWidget):
    """Role-aware dashboard page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(16)
        self._cards_area = None

    def refresh(self):
        """Rebuild the dashboard content on each navigation."""
        # Clear old content
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        role = session.get_role()
        user_id = session.get_id()
        name = session.get_name()
        stats = get_dashboard_stats(role, user_id)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel(f"Welcome back, {name.split()[0]}! 👋")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #52b788;")
        subtitle = QLabel(f"Role: {role.capitalize()}  ·  Here's your overview for today")
        subtitle.setStyleSheet("font-size: 12px; color: #74c69d;")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_layout.addLayout(title_col)
        h_layout.addStretch()
        self._layout.addWidget(header)

        # ── Divider ─────────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #1b4332;")
        self._layout.addWidget(line)

        # ── Stat Cards ───────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        if role == "farmer":
            cards = [
                ("🌿", "My Products",         stats.get("products", 0),           "#52b788"),
                ("📦", "Active Orders",        stats.get("orders", 0),             "#f4a261"),
                ("💰", "Revenue Received (৳)", f'{stats.get("revenue", 0):,.0f}',  "#95d5b2"),
                ("📈", "Investment Requests", stats.get("investment_requests", 0), "#74c69d"),
            ]
        elif role == "customer":
            cards = [
                ("🛒", "My Orders",        stats.get("my_orders", 0),                "#52b788"),
                ("⏳", "Pending Orders",   stats.get("pending_orders", 0),           "#f4a261"),
                ("💸", "Amount Spent (৳)", f'{stats.get("amount_spent", 0):,.0f}',   "#95d5b2"),
                ("⚠️", "Unpaid (৳)",       f'{stats.get("unpaid", 0):,.0f}',          "#e76f51"),
            ]
        elif role == "agent":
            cards = [
                ("📦", "Total Orders",     stats.get("total_orders", 0),              "#52b788"),
                ("⏳", "Active Orders",    stats.get("active_orders", 0),             "#f4a261"),
                ("💰", "Total Revenue (৳)",f'{stats.get("total_revenue", 0):,.0f}',   "#95d5b2"),
                ("🧑‍🌾", "Registered Farmers", stats.get("farmers", 0),             "#74c69d"),
            ]
        elif role == "investor":
            cards = [
                ("📈", "Open Rounds",       stats.get("open_rounds", 0),             "#52b788"),
                ("🔢", "Total Projects",    stats.get("total_investments", 0),        "#f4a261"),
                ("💰", "My Invested (৳)",  f'{stats.get("my_invested", 0):,.0f}',    "#95d5b2"),
                ("🤝", "My Contributions",  stats.get("my_rounds", 0),               "#74c69d"),
            ]
        else:
            cards = []

        for icon, label, value, color in cards:
            card = StatCard(icon, label, str(value), color)
            cards_row.addWidget(card)
        cards_row.addStretch()
        self._layout.addLayout(cards_row)

        # ── Quick Tips ───────────────────────────────────────────────────────
        self._layout.addSpacing(12)
        tips_box = QWidget()
        tips_box.setStyleSheet("""
            QWidget { background:#12202e; border-radius:10px; border:1px solid #1b4332; }
        """)
        tips_layout = QVBoxLayout(tips_box)
        tips_layout.setContentsMargins(20, 14, 20, 14)
        tips_layout.setSpacing(6)

        tip_title = QLabel("💡  Quick Guide")
        tip_title.setStyleSheet("font-size:13px; font-weight:bold; color:#52b788;")
        tips_layout.addWidget(tip_title)

        role_tips = {
            "farmer": [
                "🌿  Go to Products to add or edit your listed produce.",
                "📦  Check Orders to see what customers have requested.",
                "📈  Use Investments to raise funds for farm expansion.",
                "📑  View Reports to track your earnings and stock.",
            ],
            "customer": [
                "🌿  Browse Products and place an order (instant or advance).",
                "📦  Track your order status in the Orders section.",
                "💳  Pay for your orders in the Payments section.",
            ],
            "agent": [
                "📦  View all platform orders and advance their status.",
                "💳  Monitor all payments across the platform.",
                "📑  Generate full platform reports in the Reports section.",
            ],
            "investor": [
                "📈  Browse open investment rounds in the Investments section.",
                "💰  Click 'Invest' to fund a farmer's project.",
                "📊  Track your total contribution from this dashboard.",
            ],
        }
        for tip in role_tips.get(role, []):
            lbl = QLabel(tip)
            lbl.setStyleSheet("font-size:12px; color:#b7e4c7; padding:2px 0;")
            tips_layout.addWidget(lbl)

        self._layout.addWidget(tips_box)
        self._layout.addStretch()
