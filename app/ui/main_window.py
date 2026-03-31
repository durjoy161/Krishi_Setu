# app/ui/main_window.py
# Main application shell with sidebar navigation and stacked content pages.
# Navigation items are shown/hidden based on the logged-in user's role.

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QLabel, QPushButton, QStackedWidget, QFrame,
                              QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
import app.utils.session as session


# Role → which nav items to show
ROLE_NAV = {
    "farmer":   ["dashboard", "products", "orders", "investments", "reports", "profile"],
    "customer": ["dashboard", "products", "orders", "payments", "profile"],
    "agent":    ["dashboard", "products", "orders", "payments", "reports", "profile"],
    "investor": ["dashboard", "investments", "profile"],
}

NAV_ITEMS = [
    ("dashboard",   "📊", "Dashboard"),
    ("products",    "🌿", "Products"),
    ("orders",      "📦", "Orders"),
    ("payments",    "💳", "Payments"),
    ("investments", "📈", "Investments"),
    ("reports",     "📑", "Reports"),
    ("profile",     "👤", "Profile"),
]


class MainWindow(QMainWindow):
    """The main window container with sidebar + stacked pages."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krishi Setu — " + session.get_name())
        self.setMinimumSize(1100, 700)
        self._page_map = {}
        self._nav_buttons = {}
        self._build_ui()
        self._navigate("dashboard")   # Default page

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_content_area(), 1)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(210)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 12)
        sb_layout.setSpacing(0)

        # App title
        title = QLabel("🌾 Krishi Setu")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Farm-to-Table Marketplace")
        subtitle.setObjectName("AppSubtitle")
        sb_layout.addWidget(title)
        sb_layout.addWidget(subtitle)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #1b4332; margin: 0 12px;")
        sb_layout.addWidget(line)
        sb_layout.addSpacing(8)

        # Navigation buttons
        role = session.get_role()
        allowed = ROLE_NAV.get(role, [])
        for key, icon, label in NAV_ITEMS:
            if key not in allowed:
                continue
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda checked, k=key: self._navigate(k))
            sb_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sb_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Divider
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("color: #1b4332; margin: 0 12px;")
        sb_layout.addWidget(line2)

        # User info card
        user_card = QWidget()
        user_card.setObjectName("UserCard")
        uc_layout = QVBoxLayout(user_card)
        uc_layout.setContentsMargins(10, 8, 10, 8)
        uc_layout.setSpacing(2)

        uc_name = QLabel(session.get_name())
        uc_name.setObjectName("UserName")
        uc_role = QLabel(f"Role: {session.get_role().capitalize()}")
        uc_role.setObjectName("UserRole")

        uc_layout.addWidget(uc_name)
        uc_layout.addWidget(uc_role)
        sb_layout.addWidget(user_card)
        sb_layout.addSpacing(8)

        # Logout button
        logout_btn = QPushButton("🔒  Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: #12202e; color: #e76f51; border: 1px solid #9b2226;
                border-radius: 7px; margin: 0 8px; font-size: 13px;
            }
            QPushButton:hover { background: #9b2226; color: white; }
        """)
        logout_btn.clicked.connect(self._logout)
        sb_layout.addWidget(logout_btn)

        return sidebar

    # ── Content Stack ─────────────────────────────────────────────────────────
    def _build_content_area(self):
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentArea")

        # Lazy-import each page to avoid circular imports
        from app.ui.dashboard_ui import DashboardPage
        from app.ui.products_ui import ProductsPage
        from app.ui.orders_ui import OrdersPage
        from app.ui.payments_ui import PaymentsPage
        from app.ui.investments_ui import InvestmentsPage
        from app.ui.reports_ui import ReportsPage
        from app.ui.profile_ui import ProfilePage

        pages = {
            "dashboard":   DashboardPage(self),
            "products":    ProductsPage(self),
            "orders":      OrdersPage(self),
            "payments":    PaymentsPage(self),
            "investments": InvestmentsPage(self),
            "reports":     ReportsPage(self),
            "profile":     ProfilePage(self),
        }
        for key, widget in pages.items():
            self.stack.addWidget(widget)
            self._page_map[key] = widget

        return self.stack

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate(self, key: str):
        """Switch the stacked widget to the selected page."""
        # Uncheck all, check selected
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)

        if key in self._page_map:
            page = self._page_map[key]
            # Refresh data if the page has a refresh method
            if hasattr(page, "refresh"):
                page.refresh()
            self.stack.setCurrentWidget(page)

    # ── Logout ────────────────────────────────────────────────────────────────
    def _logout(self):
        session.clear()
        from app.ui.login_ui import LoginWindow
        self.login = LoginWindow()
        self.login.show()
        self.close()
