# app/ui/styles.py
# Shared QSS stylesheet for Krishi Setu — modern green/amber agricultural theme

APP_STYLE = """
/* ── Global ── */
QWidget {
    background-color: #0f1923;
    color: #e8f5e9;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ── */
#Sidebar {
    background-color: #0d2137;
    border-right: 2px solid #1b4332;
    min-width: 210px;
    max-width: 210px;
}
#AppTitle {
    font-size: 20px;
    font-weight: bold;
    color: #52b788;
    padding: 20px 12px 8px 16px;
    letter-spacing: 1px;
}
#AppSubtitle {
    font-size: 10px;
    color: #74c69d;
    padding: 0 12px 20px 16px;
}
#NavButton {
    background-color: transparent;
    color: #b7e4c7;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}
#NavButton:hover {
    background-color: #1b4332;
    color: #ffffff;
}
#NavButton:checked {
    background-color: #2d6a4f;
    color: #ffffff;
    font-weight: bold;
    border-left: 3px solid #52b788;
}
#UserCard {
    background-color: #1b4332;
    border-radius: 10px;
    padding: 10px;
    margin: 8px;
}
#UserName {
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}
#UserRole {
    font-size: 11px;
    color: #95d5b2;
}

/* ── Content Area ── */
#ContentArea {
    background-color: #0f1923;
    padding: 20px;
}
#PageTitle {
    font-size: 22px;
    font-weight: bold;
    color: #52b788;
    margin-bottom: 4px;
}
#PageSubtitle {
    font-size: 12px;
    color: #74c69d;
    margin-bottom: 16px;
}

/* ── Stat Cards ── */
#StatCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1b4332, stop:1 #0d2137);
    border-radius: 12px;
    border: 1px solid #2d6a4f;
    padding: 16px;
    min-width: 160px;
    min-height: 90px;
}
#StatValue {
    font-size: 26px;
    font-weight: bold;
    color: #52b788;
}
#StatLabel {
    font-size: 11px;
    color: #95d5b2;
}
#StatIcon {
    font-size: 28px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #2d6a4f;
    color: white;
    border: none;
    border-radius: 7px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #40916c;
}
QPushButton:pressed {
    background-color: #1b4332;
}
#DangerButton {
    background-color: #9b2226;
}
#DangerButton:hover {
    background-color: #ae2012;
}
#WarningButton {
    background-color: #ca6702;
}
#WarningButton:hover {
    background-color: #ee9b00;
    color: #001219;
}
#SuccessButton {
    background-color: #1b4332;
    border: 1px solid #52b788;
}
#SuccessButton:hover {
    background-color: #2d6a4f;
}

/* ── Inputs ── */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1a2940;
    border: 1px solid #2d6a4f;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e8f5e9;
    selection-background-color: #40916c;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #52b788;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #1a2940;
    selection-background-color: #2d6a4f;
    color: #e8f5e9;
}
QDateEdit {
    background-color: #1a2940;
    border: 1px solid #2d6a4f;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e8f5e9;
}

/* ── Table ── */
QTableWidget {
    background-color: #12202e;
    alternate-background-color: #172a3a;
    gridline-color: #1b4332;
    border: none;
    border-radius: 8px;
    selection-background-color: #2d6a4f;
}
QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #1b4332;
}
QHeaderView::section {
    background-color: #1b4332;
    color: #b7e4c7;
    padding: 8px 10px;
    border: none;
    font-weight: bold;
    font-size: 12px;
}
QScrollBar:vertical {
    background: #0d2137;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2d6a4f;
    border-radius: 4px;
}

/* ── Tabs ── */
QTabWidget::pane {
    border: 1px solid #1b4332;
    border-radius: 8px;
    background: #12202e;
}
QTabBar::tab {
    background: #0d2137;
    color: #74c69d;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #1b4332;
    color: #ffffff;
    font-weight: bold;
}

/* ── Group Box ── */
QGroupBox {
    border: 1px solid #2d6a4f;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    color: #95d5b2;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #52b788;
}

/* ── Dialog ── */
QDialog {
    background-color: #0f1923;
}
QLabel {
    color: #d8f3dc;
}

/* ── Progress Bar ── */
QProgressBar {
    border: 1px solid #2d6a4f;
    border-radius: 6px;
    text-align: center;
    background: #12202e;
    color: white;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #52b788, stop:1 #95d5b2);
    border-radius: 5px;
}

/* ── Message Box ── */
QMessageBox {
    background-color: #0f1923;
}
QMessageBox QLabel {
    color: #d8f3dc;
}

/* ── Login specific ── */
#LoginCard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0d2137, stop:1 #1b4332);
    border-radius: 18px;
    border: 1px solid #2d6a4f;
    padding: 40px 50px;
}
#LoginTitle {
    font-size: 36px;
    font-weight: bold;
    color: #52b788;
    letter-spacing: 2px;
}
#LoginSubtitle {
    font-size: 13px;
    color: #74c69d;
    margin-bottom: 8px;
}
#LoginInput {
    background-color: rgba(255,255,255,0.07);
    border: 1px solid #2d6a4f;
    border-radius: 8px;
    padding: 10px 14px;
    color: #e8f5e9;
    font-size: 14px;
    min-height: 20px;
}
#LoginInput:focus {
    border: 1px solid #52b788;
    background-color: rgba(255,255,255,0.1);
}
#LoginButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2d6a4f, stop:1 #40916c);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 1px;
    margin-top: 8px;
}
#LoginButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #40916c, stop:1 #52b788);
}

/* ── Status badges ── */
#BadgePlaced    { color: #90e0ef; }
#BadgeConfirmed { color: #f4a261; }
#BadgeHarvested { color: #e9c46a; }
#BadgeDelivered { color: #52b788; }
#BadgeCancelled { color: #e76f51; }
#BadgePaid      { color: #52b788; font-weight: bold; }
#BadgePartial   { color: #f4a261; }
#BadgeUnpaid    { color: #e76f51; }
"""


STATUS_COLORS = {
    "placed":    "#90e0ef",
    "confirmed": "#f4a261",
    "harvested": "#e9c46a",
    "delivered": "#52b788",
    "cancelled": "#e76f51",
    "paid":      "#52b788",
    "partial":   "#f4a261",
    "unpaid":    "#e76f51",
    "open":      "#90e0ef",
    "funded":    "#52b788",
    "closed":    "#8d8d8d",
}
