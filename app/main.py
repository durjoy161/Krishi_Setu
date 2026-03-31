# app/main.py
# Entry point for Krishi Setu desktop application

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from app.database.db_manager import initialize_database
from app.ui.login_ui import LoginWindow
from app.ui.styles import APP_STYLE


def main():
    # 1. Initialize / migrate the database and seed sample data
    initialize_database()

    # 2. Create the Qt application
    app = QApplication(sys.argv)

    # 3. Set global font and stylesheet
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    app.setStyleSheet(APP_STYLE)

    # 4. Show the login window
    window = LoginWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()