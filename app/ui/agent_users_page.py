# app/ui/agent_users_page.py
# "Manage Users" tab inside AgentDashboard.
# Agents can view all users, filter by role, search, and toggle active status.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QFrame,
    QDialog, QMessageBox
)
from PyQt5.QtCore import Qt

from app.utils.helpers import (
    format_currency, format_date, truncate,
    role_label, role_color
)
from app.services.agent_service import (
    get_all_users, toggle_user_active, get_user_stats
)
from app.ui.widgets.data_table import DataTable


class AgentUsersPage(QWidget):
    """Platform-wide user management page for agents."""

    COLUMNS = ["ID", "Username", "Full Name", "Role",
               "Email", "Phone", "Status", "Joined"]

    def __init__(self):
        super().__init__()
        self._users = []
        self._filtered = []
        self._build()
        self.refresh()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title + filters
        title_row = QHBoxLayout()
        title = QLabel("👥  Manage Users")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#f4a261;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search name / username / email…")
        self.search.setFixedHeight(34)
        self.search.setFixedWidth(240)
        self.search.setStyleSheet(_input_style())
        self.search.textChanged.connect(self._apply_filter)

        self.role_filter = QComboBox()
        self.role_filter.addItems(
            ["All", "farmer", "customer", "agent", "investor"]
        )
        self.role_filter.setFixedWidth(130)
        self.role_filter.setFixedHeight(34)
        self.role_filter.setStyleSheet(_combo_style())
        self.role_filter.currentTextChanged.connect(self._apply_filter)

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(self.search)
        title_row.addWidget(self.role_filter)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # Stats summary row
        self._stat_labels = {}
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        for key, label, color in [
            ("farmer",   "Farmers",   "#52b788"),
            ("customer", "Customers", "#4895ef"),
            ("agent",    "Agents",    "#f4a261"),
            ("investor", "Investors", "#9b5de5"),
        ]:
            card = _MiniCard(label, "0", color)
            self._stat_labels[key] = card
            stats_row.addWidget(card)
        stats_row.addStretch()
        layout.addLayout(stats_row)

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

        self.btn_detail = _btn("🔍  View Details", "#1a3a6c", "#2d5fa6")
        self.btn_detail.setEnabled(False)
        self.btn_detail.clicked.connect(self._show_detail)

        self.btn_toggle = _btn("🔒  Toggle Active", "#3a2a0a", "#6a4a0a")
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.clicked.connect(self._toggle_selected)

        btn_row.addWidget(self.btn_detail)
        btn_row.addWidget(self.btn_toggle)
        layout.addLayout(btn_row)

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        self._users = get_all_users()

        # Update mini stat cards
        for role_key in ["farmer", "customer", "agent", "investor"]:
            count = sum(
                1 for u in self._users if u["role"] == role_key
            )
            self._stat_labels[role_key].set_value(str(count))

        self._apply_filter()

    def _apply_filter(self):
        role   = self.role_filter.currentText()
        search = self.search.text().strip().lower()

        self._filtered = [
            u for u in self._users
            if (role == "All" or u["role"] == role)
            and (
                not search
                or search in u["full_name"].lower()
                or search in u["username"].lower()
                or search in (u.get("email") or "").lower()
            )
        ]

        rows = []
        for u in self._filtered:
            status = "✅ Active" if u.get("is_active", 1) else "🔒 Inactive"
            rows.append([
                u["id"],
                u["username"],
                truncate(u["full_name"], 24),
                role_label(u["role"]),
                truncate(u.get("email") or "—", 24),
                u.get("phone") or "—",
                status,
                format_date(u.get("created_at", "")),
            ])
        self.table.populate(rows)

        # Color role column (index 3) and status column (index 6)
        for i, u in enumerate(self._filtered):
            self.table.color_cell(i, 3, role_color(u["role"]))
            status_color = "#52b788" if u.get("is_active", 1) else "#e63946"
            self.table.color_cell(i, 6, status_color)

        count = len(self._filtered)
        self.result_count.setText(
            f"{count} user{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected_user(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        has = self._selected_user() is not None
        self.btn_detail.setEnabled(has)
        self.btn_toggle.setEnabled(has)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _show_detail(self):
        user = self._selected_user()
        if user:
            dlg = UserDetailDialog(user, parent=self)
            dlg.exec_()

    def _toggle_selected(self):
        user = self._selected_user()
        if not user:
            return

        current_status = "Active" if user.get("is_active", 1) else "Inactive"
        new_status     = "Inactive" if user.get("is_active", 1) else "Active"

        reply = QMessageBox.question(
            self, "Toggle User Status",
            f"Change {user['full_name']}'s status\n"
            f"from  {current_status}  →  {new_status}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = toggle_user_active(user["id"])
            if result["success"]:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])


# ── User Detail Dialog ─────────────────────────────────────────────────────────

class UserDetailDialog(QDialog):
    """Full user detail popup including activity statistics."""

    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"User Details — {user['username']}")
        self.setFixedWidth(460)
        self.setModal(True)
        self._build(user)

    def _build(self, u: dict):
        self.setStyleSheet(
            "QDialog{background:#12202e;} QLabel{color:#c8dff0;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        # Header
        color = role_color(u["role"])
        name_lbl = QLabel(u["full_name"])
        name_lbl.setStyleSheet(
            f"font-size:18px;font-weight:bold;color:{color};"
        )
        layout.addWidget(name_lbl)

        role_lbl = QLabel(role_label(u["role"]))
        role_lbl.setStyleSheet(
            f"font-size:12px;color:{color};"
            f"background:{color}22;border:1px solid {color}44;"
            "border-radius:8px;padding:2px 10px;"
        )
        layout.addWidget(role_lbl)
        layout.addWidget(_divider())

        # Profile info
        profile_title = QLabel("Profile")
        profile_title.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#7a9ab5;"
        )
        layout.addWidget(profile_title)

        for label, value in [
            ("Username",   u.get("username", "—")),
            ("Email",      u.get("email") or "—"),
            ("Phone",      u.get("phone") or "—"),
            ("Address",    u.get("address") or "—"),
            ("Farm Name",  u.get("farm_name") or "—"),
            ("Farm Size",  u.get("farm_size") or "—"),
            ("Status",     "✅ Active" if u.get("is_active", 1) else "🔒 Inactive"),
            ("Joined",     format_date(u.get("created_at", ""))),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;min-width:90px;"
            )
            val = QLabel(str(value))
            val.setStyleSheet("font-size:13px;color:#d0e8f5;")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)

        # Activity stats
        layout.addWidget(_divider())
        stats_title = QLabel("Activity")
        stats_title.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#7a9ab5;"
        )
        layout.addWidget(stats_title)

        stats = get_user_stats(u["id"], u["role"])
        if not stats:
            no_stats = QLabel("No activity data available.")
            no_stats.setStyleSheet("font-size:12px;color:#2d4a6a;")
            layout.addWidget(no_stats)
        else:
            stat_labels = {
                "products":    ("📦 Products Listed", str),
                "orders":      ("📋 Orders",          str),
                "revenue":     ("💵 Revenue",         format_currency),
                "spent":       ("💵 Total Spent",     format_currency),
                "invested":    ("💰 Total Invested",  format_currency),
                "investments": ("📈 Investments",     str),
            }
            for key, val in stats.items():
                if key in stat_labels:
                    lbl_text, fmt = stat_labels[key]
                    row = QHBoxLayout()
                    lbl = QLabel(f"{lbl_text}:")
                    lbl.setStyleSheet(
                        "font-size:12px;color:#7a9ab5;min-width:140px;"
                    )
                    val_lbl = QLabel(fmt(val))
                    val_lbl.setStyleSheet(
                        f"font-size:13px;color:{color};font-weight:bold;"
                    )
                    row.addWidget(lbl)
                    row.addWidget(val_lbl)
                    row.addStretch()
                    layout.addLayout(row)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background:#1a2940; color:#7a9ab5; border:none;
                border-radius:6px; font-size:13px; margin-top:8px;
            }
            QPushButton:hover { background:#2d4a6a; color:white; }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)


# ── Mini stat card ─────────────────────────────────────────────────────────────

class _MiniCard(QWidget):
    def __init__(self, label, value, color):
        super().__init__()
        self.setFixedHeight(64)
        self.setMinimumWidth(110)
        self.setStyleSheet(f"""
            QWidget {{
                background:#12202e;
                border:1px solid {color}33;
                border-radius:10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"font-size:18px;font-weight:bold;color:{color};"
            "background:transparent;border:none;"
        )
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "font-size:10px;color:#7a9ab5;"
            "background:transparent;border:none;"
        )
        layout.addWidget(self._val)
        layout.addWidget(lbl)

    def set_value(self, value):
        self._val.setText(value)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _btn(text, dark, light):
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{dark}; color:white; border:none;
            border-radius:7px; font-size:12px; padding:0 14px;
        }}
        QPushButton:hover {{ background:{light}; }}
        QPushButton:disabled {{ background:#1a2940; color:#3a5a6a; }}
    """)
    return btn


def _input_style():
    return """
        QLineEdit {
            background:#1a2940; border:1px solid #2d4a6a;
            border-radius:7px; padding:0 12px;
            color:#e8f5e9; font-size:12px;
        }
        QLineEdit:focus { border:1px solid #f4a261; }
    """


def _combo_style():
    return """
        QComboBox {
            background:#1a2940; border:1px solid #2d4a6a;
            border-radius:7px; padding:0 10px;
            color:#e8f5e9; font-size:12px;
        }
        QComboBox::drop-down { border:none; }
        QComboBox QAbstractItemView {
            background:#1a2940; color:#e8f5e9;
            selection-background-color:#2d5fa6;
        }
    """


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
