# app/ui/login_ui.py
# Login window — pure UI logic only.
# All auth decisions are delegated to auth_service.

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
    QCheckBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.services.auth_service import login, login_with_token
import app.utils.session as session


class LoginWindow(QWidget):
    """
    Two-pane login window.
    Left pane: decorative branding.
    Right pane: login card with Remember Me and link to Register.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krishi Setu — Login")
        self.setFixedSize(900, 620)
        self.setObjectName("LoginRoot")
        self._build_ui()
        self._try_auto_login()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_pane())
        root.addWidget(self._build_right_pane())

    def _build_left_pane(self) -> QWidget:
        left = QWidget()
        left.setMinimumWidth(380)
        left.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #0d2137);
        """)
        layout = QVBoxLayout(left)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        for text, style in [
            ("🌾",                         "font-size:80px;"),
            ("Krishi Setu",                 "font-size:32px;font-weight:bold;color:white;letter-spacing:3px;"),
            ("Farmer · Customer · Agent · Investor",
                                            "font-size:12px;color:#95d5b2;"),
            ("Connecting farms to families,\neliminating middlemen.",
                                            "font-size:13px;color:#b7e4c7;margin-top:20px;"),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(style)
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        return left

    def _build_right_pane(self) -> QWidget:
        right = QWidget()
        right.setStyleSheet("background-color:#0f1923;")
        layout = QVBoxLayout(right)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.addWidget(self._build_card())
        return right

    def _build_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("LoginCard")
        card.setFixedWidth(370)
        card.setStyleSheet("""
            QWidget#LoginCard {
                background:#12202e; border-radius:18px;
                border:1px solid #2d6a4f;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(36, 36, 36, 36)

        # Title
        layout.addWidget(self._label("Welcome Back", "font-size:24px;font-weight:bold;color:#52b788;", center=True))
        layout.addWidget(self._label("Sign in to your Krishi Setu account",
                                     "font-size:11px;color:#74c69d;margin-bottom:8px;", center=True))

        # Username field
        layout.addWidget(self._label("Username", "font-size:12px;color:#95d5b2;font-weight:bold;"))
        self.input_user = self._line_edit("Enter your username")
        self.input_user.returnPressed.connect(lambda: self.input_pass.setFocus())
        layout.addWidget(self.input_user)

        # Password field
        layout.addWidget(self._label("Password", "font-size:12px;color:#95d5b2;font-weight:bold;"))
        self.input_pass = self._line_edit("Enter your password", password=True)
        self.input_pass.returnPressed.connect(self.handle_login)
        layout.addWidget(self.input_pass)

        # Remember Me checkbox
        self.chk_remember = QCheckBox("Remember Me")
        self.chk_remember.setStyleSheet("color:#95d5b2;font-size:12px;")
        self.chk_remember.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.chk_remember)

        # Login button
        self.btn_login = QPushButton("🔑  Sign In")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(44)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2d6a4f,stop:1 #40916c);
                color:white;border:none;border-radius:8px;
                font-size:15px;font-weight:bold;letter-spacing:1px;
            }
            QPushButton:hover {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #40916c,stop:1 #52b788);
            }
            QPushButton:pressed { background:#1b4332; }
        """)
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

        # Divider
        divider = QLabel("─────────  or  ─────────")
        divider.setStyleSheet("color:#2d4a3e;font-size:11px;")
        divider.setAlignment(Qt.AlignCenter)
        layout.addWidget(divider)

        # Register link
        reg_row = QHBoxLayout()
        reg_row.addWidget(self._label("Don't have an account?", "color:#526e58;font-size:12px;"))
        btn_reg = QPushButton("Register")
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.setFlat(True)
        btn_reg.setStyleSheet(
            "color:#52b788;font-size:12px;font-weight:bold;text-decoration:underline;border:none;"
        )
        btn_reg.clicked.connect(self.open_register)
        reg_row.addWidget(btn_reg)
        reg_row.addStretch()
        layout.addLayout(reg_row)

        return card

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def handle_login(self):
        """Read inputs, call auth_service.login(), respond via QMessageBox."""
        username = self.input_user.text().strip()
        password = self.input_pass.text()
        remember = self.chk_remember.isChecked()

        if not username or not password:
            QMessageBox.warning(self, "Missing Info",
                                "Please enter both username and password.")
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText("Signing in…")

        result = login(username, password, remember_me=remember)

        self.btn_login.setEnabled(True)
        self.btn_login.setText("🔑  Sign In")

        if result["success"]:
            # Persist token locally if Remember Me was checked
            if remember and result.get("token"):
                session.save_remember_token(result["token"])
            else:
                session.delete_remember_token()
            self._open_main_window()
        else:
            QMessageBox.warning(self, "Login Failed", result["message"])
            self.input_pass.clear()
            self.input_pass.setFocus()

    def open_register(self):
        """Open the registration window."""
        from app.ui.register_ui import RegisterWindow
        self.register_window = RegisterWindow(parent_login=self)
        self.register_window.show()
        self.hide()

    def _try_auto_login(self):
        """
        On startup, check for a saved Remember Me token and auto-login if valid.
        Silently skips if no token or token is invalid.
        """
        token = session.load_remember_token()
        if not token:
            return
        result = login_with_token(token)
        if result["success"]:
            self._open_main_window()

    def _open_main_window(self):
        from app.services.role_router import open_dashboard_for_role
        import app.utils.session as session
        role = session.get_role()
        self.dashboard = open_dashboard_for_role(role, parent=self)

    # ── Widget Factories ───────────────────────────────────────────────────────

    @staticmethod
    def _label(text: str, style: str, center: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        if center:
            lbl.setAlignment(Qt.AlignCenter)
        return lbl

    @staticmethod
    def _line_edit(placeholder: str, password: bool = False) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        if password:
            field.setEchoMode(QLineEdit.Password)
        field.setStyleSheet("""
            QLineEdit {
                background:#1a2940;border:1px solid #2d6a4f;border-radius:8px;
                padding:10px 14px;color:#e8f5e9;font-size:13px;
            }
            QLineEdit:focus { border:1px solid #52b788; }
        """)
        return field