# app/ui/profile_ui.py
# Profile page: shows logged-in user's profile details

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QGridLayout)
from PyQt5.QtCore import Qt
import app.utils.session as session


ROLE_ICONS = {
    "farmer":   "🧑‍🌾",
    "customer": "🛒",
    "agent":    "🤝",
    "investor": "💼",
}


class ProfilePage(QWidget):
    """Displays the current user's profile."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(16)

    def refresh(self):
        # Clear old content
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        user = session.get_user()
        role = user.get("role", "")

        # ── Header ────────────────────────────────────────────────────────────
        title = QLabel("👤  My Profile")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        self._layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#1b4332;")
        self._layout.addWidget(line)

        # ── Profile card ──────────────────────────────────────────────────────
        card = QWidget()
        card.setStyleSheet("""
            QWidget { background:#12202e; border-radius:14px; border:1px solid #1b4332; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 28, 30, 28)
        card_layout.setSpacing(6)

        # Avatar area
        avatar_row = QHBoxLayout()
        icon = QLabel(ROLE_ICONS.get(role, "👤"))
        icon.setStyleSheet("font-size:60px;")
        icon.setAlignment(Qt.AlignCenter)

        name_col = QVBoxLayout()
        name_lbl = QLabel(user.get("full_name", "—"))
        name_lbl.setStyleSheet("font-size:24px;font-weight:bold;color:#52b788;")
        role_lbl = QLabel(f"{role.capitalize()}  ·  @{user.get('username','—')}")
        role_lbl.setStyleSheet("font-size:13px;color:#74c69d;")
        name_col.addWidget(name_lbl)
        name_col.addWidget(role_lbl)
        name_col.setAlignment(Qt.AlignVCenter)

        avatar_row.addWidget(icon)
        avatar_row.addSpacing(16)
        avatar_row.addLayout(name_col)
        avatar_row.addStretch()
        card_layout.addLayout(avatar_row)

        card_layout.addSpacing(16)

        # Details grid
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(24)

        fields = [
            ("📧  Email",   user.get("email", "—")),
            ("📞  Phone",   user.get("phone", "—")),
            ("📍  Address", user.get("address", "—")),
            ("🕒  Joined",  (user.get("created_at","—") or "—")[:10]),
        ]
        if role == "farmer":
            fields += [
                ("🏡  Farm Name", user.get("farm_name", "—")),
                ("📐  Farm Size", user.get("farm_size", "—")),
            ]

        for i, (label, value) in enumerate(fields):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:12px;color:#74c69d;font-weight:bold;")
            val = QLabel(value or "—")
            val.setStyleSheet("font-size:13px;color:#d8f3dc;")
            val.setWordWrap(True)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)

        card_layout.addLayout(grid)
        self._layout.addWidget(card)

        # Role note
        notes = {
            "farmer":   "As a Farmer, you can list products, manage orders, and create investment requests.",
            "customer": "As a Customer, you can browse products, place orders, and track payments.",
            "agent":    "As an Agent, you oversee all orders, payments, and platform activity.",
            "investor": "As an Investor, you can browse and fund farmer investment rounds.",
        }
        note = QLabel(f"ℹ️  {notes.get(role,'')}")
        note.setStyleSheet("""
            font-size:12px; color:#74c69d;
            background:#0d2137; border:1px solid #1b4332;
            border-radius:8px; padding:12px 16px;
        """)
        note.setWordWrap(True)
        self._layout.addWidget(note)
        self._layout.addStretch()
