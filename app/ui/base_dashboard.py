# app/ui/base_dashboard.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import role_label, role_color
from app.services.auth_service import logout


class BaseDashboard(QMainWindow):
    """
    Shared dashboard shell: sidebar + header + swappable content area.
    Subclass this and implement nav_items() and window_title().
    """

    def nav_items(self):
        raise NotImplementedError

    def window_title(self):
        return "Krishi Setu"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.window_title())
        self.setMinimumSize(1150, 720)
        self._nav_buttons = []
        self._stack = QStackedWidget()
        self._build_shell()

    def _build_shell(self):
        root = QWidget()
        root.setStyleSheet("background:#0b1520;")
        self.setCentralWidget(root)

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_sidebar())

        right_zone = QWidget()
        right_zone.setStyleSheet("background:#0f1923;")
        right_layout = QVBoxLayout(right_zone)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_header())
        right_layout.addWidget(self._stack, stretch=1)

        outer.addWidget(right_zone, stretch=1)

        items = self.nav_items()
        for _icon, _label, page in items:
            if page is not None:
                self._stack.addWidget(page)

        if items:
            self._activate_nav(0)

    def _build_sidebar(self):
        role  = session.get_role()
        color = role_color(role)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            "QWidget { background:#0d1b2a; border-right:1px solid #1a2940; }"
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand block
        brand = QWidget()
        brand.setFixedHeight(72)
        brand.setStyleSheet(
            "background:#0a1628; border-bottom:1px solid #1a2940;"
        )
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(18, 0, 18, 0)

        icon_lbl = QLabel("🌾")
        icon_lbl.setStyleSheet("font-size:22px;")
        text_lbl = QLabel("Krishi Setu")
        text_lbl.setStyleSheet(
            f"font-size:15px;font-weight:bold;color:{color};letter-spacing:1px;"
        )
        brand_layout.addWidget(icon_lbl)
        brand_layout.addWidget(text_lbl)
        brand_layout.addStretch()
        layout.addWidget(brand)

        # Nav label
        nav_lbl = QLabel("NAVIGATION")
        nav_lbl.setStyleSheet(
            "font-size:10px;color:#2d4a6a;font-weight:bold;"
            "letter-spacing:2px;padding:18px 20px 6px 20px;"
        )
        layout.addWidget(nav_lbl)

        # Nav buttons
        for idx, (icon, label, _page) in enumerate(self.nav_items()):
            btn = self._make_nav_btn(icon, label, idx, color)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Logout
        logout_btn = QPushButton("  🚪  Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(48)
        logout_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#e63946; border:none;
                border-top:1px solid #1a2940; font-size:13px;
                font-weight:bold; text-align:left; padding-left:20px;
            }
            QPushButton:hover { background:#1a0a0a; }
        """)
        logout_btn.clicked.connect(self._handle_logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _make_nav_btn(self, icon, label, index, color):
        btn = QPushButton(f"  {icon}  {label}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(46)
        btn.setCheckable(True)
        btn.setProperty("nav_index", index)
        btn.setProperty("active_color", color)
        btn.setStyleSheet(self._nav_style(color, False))
        btn.clicked.connect(lambda checked, i=index: self._activate_nav(i))
        return btn

    @staticmethod
    def _nav_style(color, active):
        if active:
            return f"""
                QPushButton {{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {color}22,stop:1 transparent);
                    color:{color}; border:none;
                    border-left:3px solid {color};
                    font-size:13px; font-weight:bold;
                    text-align:left; padding-left:17px;
                }}
            """
        return f"""
            QPushButton {{
                background:transparent; color:#7a9ab5; border:none;
                border-left:3px solid transparent;
                font-size:13px; text-align:left; padding-left:17px;
            }}
            QPushButton:hover {{
                background:{color}11; color:{color};
                border-left:3px solid {color}66;
            }}
        """

    def _activate_nav(self, index):
        self._stack.setCurrentIndex(index)
        for btn in self._nav_buttons:
            is_active = btn.property("nav_index") == index
            color = btn.property("active_color")
            btn.setStyleSheet(self._nav_style(color, is_active))
            btn.setChecked(is_active)

    def _build_header(self):
        role  = session.get_role()
        name  = session.get_name()
        color = role_color(role)

        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(
            "background:#0d1b2a; border-bottom:1px solid #1a2940;"
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 0, 28, 0)

        self.header_title = QLabel("Overview")
        self.header_title.setStyleSheet(
            "font-size:18px;font-weight:bold;color:#d0e8f5;"
        )
        layout.addWidget(self.header_title)
        layout.addStretch()

        badge = QLabel(f" {role_label(role)} ")
        badge.setStyleSheet(
            f"background:{color}22; color:{color};"
            f"border:1px solid {color}55; border-radius:10px;"
            "font-size:11px; font-weight:bold; padding:3px 10px;"
        )
        user_lbl = QLabel(name)
        user_lbl.setStyleSheet(
            "font-size:13px; color:#7a9ab5; margin-left:12px;"
        )

        layout.addWidget(badge)
        layout.addWidget(user_lbl)
        return header

    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Logout", "Are you sure you want to log out?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            logout(clear_token=True)
            from app.ui.login_ui import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def set_page_title(self, title):
        self.header_title.setText(title)