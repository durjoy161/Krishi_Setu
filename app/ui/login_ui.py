# app/ui/login_ui.py
# Modern login window with role-aware access for Krishi Setu

from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                              QVBoxLayout, QHBoxLayout, QMessageBox,
                              QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QColor
from app.controllers.auth_controller import authenticate
import app.utils.session as session


class LoginWindow(QWidget):
    """Modern, animated login window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krishi Setu — Login")
        self.setFixedSize(900, 600)
        self.setObjectName("LoginRoot")
        self._build_ui()

    def _build_ui(self):
        # ── Outer layout (full-screen, two panes) ─────────────────────────────
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left decorative panel
        left = QWidget()
        left.setMinimumWidth(380)
        left.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #1b4332, stop:0.5 #2d6a4f, stop:1 #0d2137);
        """)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignCenter)

        hero_icon = QLabel("🌾")
        hero_icon.setStyleSheet("font-size:80px;")
        hero_icon.setAlignment(Qt.AlignCenter)

        hero_title = QLabel("Krishi Setu")
        hero_title.setStyleSheet("font-size:32px; font-weight:bold; color:white; letter-spacing:3px;")
        hero_title.setAlignment(Qt.AlignCenter)

        hero_sub = QLabel("Farmer · Customer · Agent · Investor")
        hero_sub.setStyleSheet("font-size:12px; color:#95d5b2; margin-top:6px;")
        hero_sub.setAlignment(Qt.AlignCenter)

        tagline = QLabel("Connecting farms to families,\neliminating middlemen.")
        tagline.setStyleSheet("font-size:13px; color:#b7e4c7; margin-top:24px; line-height:1.6;")
        tagline.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(hero_icon)
        left_layout.addWidget(hero_title)
        left_layout.addWidget(hero_sub)
        left_layout.addWidget(tagline)

        # Right login card
        right = QWidget()
        right.setStyleSheet("background-color: #0f1923;")
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.setContentsMargins(60, 40, 60, 40)

        # Card widget
        card = QWidget()
        card.setObjectName("LoginCard")
        card.setFixedWidth(360)
        card.setStyleSheet("""
            QWidget#LoginCard {
                background: #12202e;
                border-radius: 18px;
                border: 1px solid #2d6a4f;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(36, 36, 36, 36)

        # Title
        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size:24px; font-weight:bold; color:#52b788;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Sign in to your Krishi Setu account")
        subtitle.setStyleSheet("font-size:11px; color:#74c69d; margin-bottom:12px;")
        subtitle.setAlignment(Qt.AlignCenter)

        # Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size:12px; color:#95d5b2; font-weight:bold;")

        self.input_user = QLineEdit()
        self.input_user.setObjectName("LoginInput")
        self.input_user.setPlaceholderText("e.g. farmer1, customer1 …")
        self.input_user.setStyleSheet("""
            QLineEdit { background:#1a2940; border:1px solid #2d6a4f; border-radius:8px;
                        padding:10px 14px; color:#e8f5e9; font-size:13px; }
            QLineEdit:focus { border:1px solid #52b788; }
        """)

        # Password
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("font-size:12px; color:#95d5b2; font-weight:bold;")

        self.input_pass = QLineEdit()
        self.input_pass.setObjectName("LoginInput")
        self.input_pass.setEchoMode(QLineEdit.Password)
        self.input_pass.setPlaceholderText("Password (default: 1234)")
        self.input_pass.setStyleSheet("""
            QLineEdit { background:#1a2940; border:1px solid #2d6a4f; border-radius:8px;
                        padding:10px 14px; color:#e8f5e9; font-size:13px; }
            QLineEdit:focus { border:1px solid #52b788; }
        """)
        self.input_pass.returnPressed.connect(self.handle_login)

        # Login button
        self.btn_login = QPushButton("🔑  Login")
        self.btn_login.setObjectName("LoginButton")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(44)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2d6a4f,stop:1 #40916c);
                color:white; border:none; border-radius:8px;
                font-size:15px; font-weight:bold; letter-spacing:1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #40916c,stop:1 #52b788);
            }
            QPushButton:pressed { background:#1b4332; }
        """)
        self.btn_login.clicked.connect(self.handle_login)

        # Demo hint
        hint = QLabel("Demo: farmer1 · customer1 · agent1 · investor1\nAll passwords: 1234")
        hint.setStyleSheet("font-size:10px; color:#526e58; margin-top:8px;")
        hint.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(lbl_user)
        card_layout.addWidget(self.input_user)
        card_layout.addWidget(lbl_pass)
        card_layout.addWidget(self.input_pass)
        card_layout.addWidget(self.btn_login)
        card_layout.addWidget(hint)

        right_layout.addWidget(card)
        root.addWidget(left)
        root.addWidget(right)

    def handle_login(self):
        """Validate credentials and open the main window on success."""
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Info", "Please enter both username and password.")
            return

        if authenticate(username, password):
            user = session.get_user()
            from app.ui.main_window import MainWindow
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "❌ Invalid username or password.\nCheck demo credentials below the button.")
            self.input_pass.clear()
            self.input_pass.setFocus()