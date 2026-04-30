# app/ui/register_ui.py
# Registration window — pure UI logic only.
# All validation and DB work is done in auth_service.

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox,
    QMessageBox, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from app.services.auth_service import register_user, get_password_strength_label


class RegisterWindow(QWidget):
    """
    Registration window with:
    - Full form validation
    - Real-time password strength indicator
    - Role selection
    - Links back to Login
    """

    def __init__(self, parent_login=None):
        super().__init__()
        self.parent_login = parent_login
        self.setWindowTitle("Krishi Setu — Create Account")
        self.setFixedSize(960, 680)
        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_left_pane())
        root.addWidget(self._build_right_pane())

    def _build_left_pane(self) -> QWidget:
        left = QWidget()
        left.setMinimumWidth(340)
        left.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #0d2137, stop:0.5 #2d6a4f, stop:1 #1b4332);
        """)
        layout = QVBoxLayout(left)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        for text, style in [
            ("🌱",          "font-size:72px;"),
            ("Join Krishi Setu",
                            "font-size:26px;font-weight:bold;color:white;letter-spacing:2px;"),
            ("Create your account and become\npart of the farming revolution.",
                            "font-size:12px;color:#b7e4c7;"),
            ("🔒  Your password is securely\n     hashed with bcrypt.",
                            "font-size:11px;color:#74c69d;margin-top:20px;"),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(style)
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        return left

    def _build_right_pane(self) -> QWidget:
        right = QWidget()
        right.setStyleSheet("background-color:#0f1923;")

        # Wrap card in a scroll area so it works on smaller screens
        scroll = QScrollArea(right)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")

        outer = QVBoxLayout(right)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.addWidget(self._build_card())
        return right

    def _build_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("RegCard")
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QWidget#RegCard {
                background:#12202e;border-radius:18px;
                border:1px solid #2d6a4f;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(36, 30, 36, 30)

        layout.addWidget(self._lbl("Create Account",
                                   "font-size:22px;font-weight:bold;color:#52b788;", center=True))
        layout.addWidget(self._lbl("Fill in the details below to get started",
                                   "font-size:11px;color:#74c69d;margin-bottom:6px;", center=True))

        # Full name
        layout.addWidget(self._lbl("Full Name *", _field_label_style()))
        self.input_name = self._field("e.g. Rahim Uddin")
        layout.addWidget(self.input_name)

        # Username
        layout.addWidget(self._lbl("Username *  (letters, numbers, _ only)", _field_label_style()))
        self.input_user = self._field("e.g. farmer_rahim")
        layout.addWidget(self.input_user)

        # Email
        layout.addWidget(self._lbl("Email  (optional)", _field_label_style()))
        self.input_email = self._field("e.g. rahim@example.com")
        layout.addWidget(self.input_email)

        # Phone
        layout.addWidget(self._lbl("Phone  (optional)", _field_label_style()))
        self.input_phone = self._field("e.g. 01711111111")
        layout.addWidget(self.input_phone)

        # Role
        layout.addWidget(self._lbl("Role *", _field_label_style()))
        self.combo_role = QComboBox()
        self.combo_role.addItems(["farmer", "customer", "agent", "investor"])
        self.combo_role.setStyleSheet("""
            QComboBox {
                background:#1a2940;border:1px solid #2d6a4f;border-radius:8px;
                padding:9px 14px;color:#e8f5e9;font-size:13px;
            }
            QComboBox:focus { border:1px solid #52b788; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView {
                background:#1a2940;color:#e8f5e9;selection-background-color:#2d6a4f;
            }
        """)
        layout.addWidget(self.combo_role)

        # Password
        layout.addWidget(self._lbl("Password *", _field_label_style()))
        self.input_pass = self._field("Min 8 chars, upper, lower, digit, special", password=True)
        self.input_pass.textChanged.connect(self._update_strength_bar)
        layout.addWidget(self.input_pass)

        # Password strength indicator
        self.lbl_strength = QLabel("Password strength: —")
        self.lbl_strength.setStyleSheet("font-size:11px;color:#526e58;")
        layout.addWidget(self.lbl_strength)

        # Confirm password
        layout.addWidget(self._lbl("Confirm Password *", _field_label_style()))
        self.input_confirm = self._field("Re-enter your password", password=True)
        self.input_confirm.returnPressed.connect(self.handle_register)
        layout.addWidget(self.input_confirm)

        # Register button
        self.btn_register = QPushButton("✅  Create Account")
        self.btn_register.setCursor(Qt.PointingHandCursor)
        self.btn_register.setFixedHeight(44)
        self.btn_register.setStyleSheet("""
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2d6a4f,stop:1 #40916c);
                color:white;border:none;border-radius:8px;
                font-size:14px;font-weight:bold;
            }
            QPushButton:hover {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #40916c,stop:1 #52b788);
            }
            QPushButton:pressed { background:#1b4332; }
        """)
        self.btn_register.clicked.connect(self.handle_register)
        layout.addWidget(self.btn_register)

        # Back to login
        back_row = QHBoxLayout()
        back_row.addWidget(self._lbl("Already have an account?", "color:#526e58;font-size:12px;"))
        btn_back = QPushButton("Sign In")
        btn_back.setFlat(True)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(
            "color:#52b788;font-size:12px;font-weight:bold;text-decoration:underline;border:none;"
        )
        btn_back.clicked.connect(self.back_to_login)
        back_row.addWidget(btn_back)
        back_row.addStretch()
        layout.addLayout(back_row)

        return card

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def handle_register(self):
        """Collect form data, call register_user(), show result via QMessageBox."""
        self.btn_register.setEnabled(False)
        self.btn_register.setText("Creating account…")

        result = register_user(
            username=self.input_user.text().strip(),
            password=self.input_pass.text(),
            confirm_password=self.input_confirm.text(),
            role=self.combo_role.currentText(),
            full_name=self.input_name.text().strip(),
            email=self.input_email.text().strip(),
            phone=self.input_phone.text().strip(),
        )

        self.btn_register.setEnabled(True)
        self.btn_register.setText("✅  Create Account")

        if result["success"]:
            QMessageBox.information(self, "Account Created!", result["message"])
            self.back_to_login()
        else:
            QMessageBox.warning(self, "Registration Failed", result["message"])

    def back_to_login(self):
        """Return to the login window."""
        if self.parent_login:
            self.parent_login.show()
        else:
            # If opened standalone, create a new LoginWindow
            from app.ui.login_ui import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
        self.close()

    def _update_strength_bar(self, text: str):
        """Update the password strength label in real-time as the user types."""
        if not text:
            self.lbl_strength.setText("Password strength: —")
            self.lbl_strength.setStyleSheet("font-size:11px;color:#526e58;")
            return
        label, color = get_password_strength_label(text)
        self.lbl_strength.setText(f"Password strength:  {label}")
        self.lbl_strength.setStyleSheet(f"font-size:11px;font-weight:bold;color:{color};")

    # ── Widget Factories ───────────────────────────────────────────────────────

    @staticmethod
    def _lbl(text: str, style: str, center: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        if center:
            lbl.setAlignment(Qt.AlignCenter)
        return lbl

    @staticmethod
    def _field(placeholder: str, password: bool = False) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        if password:
            field.setEchoMode(QLineEdit.Password)
        field.setStyleSheet("""
            QLineEdit {
                background:#1a2940;border:1px solid #2d6a4f;border-radius:8px;
                padding:9px 14px;color:#e8f5e9;font-size:13px;
            }
            QLineEdit:focus { border:1px solid #52b788; }
        """)
        return field


def _field_label_style() -> str:
    return "font-size:11px;color:#95d5b2;font-weight:bold;"
