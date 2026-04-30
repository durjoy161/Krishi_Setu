# app/ui/farmer_investments_page.py
# "Investments" tab inside FarmerDashboard.
# Farmers can create investment requests and track funding progress.

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QMessageBox, QFrame,
    QDialog, QFormLayout, QLineEdit, QTextEdit,
    QDialogButtonBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, investment_status_color
)
from app.services.investment_service import (
    get_investments_by_farmer, create_investment, close_investment
)
from app.ui.widgets.data_table import DataTable


class FarmerInvestmentsPage(QWidget):

    COLUMNS = ["ID", "Title", "Goal", "Raised", "Remaining",
               "ROI %", "Contributors", "Status", "Created"]

    def __init__(self):
        super().__init__()
        self._farmer_id = session.get_id()
        self._investments = []
        self._filtered = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("💰  My Investment Requests")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#52b788;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "open", "funded", "closed"])
        self.status_filter.setFixedWidth(120)
        self.status_filter.setFixedHeight(34)
        self.status_filter.setStyleSheet(_combo_style())
        self.status_filter.currentTextChanged.connect(self._apply_filter)

        btn_add = _btn("＋  New Request", "#1b4332", "#2d6a4f")
        btn_add.clicked.connect(self._open_create_dialog)

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(self.status_filter)
        title_row.addWidget(btn_refresh)
        title_row.addWidget(btn_add)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        self.table = DataTable(self.COLUMNS)
        self.table.itemSelectionChanged.connect(self._on_selection_change)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_close = _btn("🔒  Close Investment", "#3a2a0a", "#6a4a0a")
        self.btn_close.setEnabled(False)
        self.btn_close.clicked.connect(self._close_selected)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        layout.addWidget(self._build_legend())

    def _build_legend(self):
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(16)
        lbl = QLabel("Status:")
        lbl.setStyleSheet("font-size:11px;color:#7a9ab5;")
        lay.addWidget(lbl)
        for status, color in [
            ("Open", "#4895ef"),
            ("Funded", "#52b788"),
            ("Closed", "#888888"),
        ]:
            dot = QLabel(f"● {status}")
            dot.setStyleSheet(f"font-size:11px;color:{color};")
            lay.addWidget(dot)
        lay.addStretch()
        return row

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        self._investments = get_investments_by_farmer(self._farmer_id)
        self._apply_filter()

    def _apply_filter(self):
        sf = self.status_filter.currentText()
        self._filtered = (
            self._investments if sf == "All"
            else [i for i in self._investments if i["status"] == sf]
        )
        rows = []
        for i in self._filtered:
            rows.append([
                i["id"],
                truncate(i["title"], 28),
                format_currency(i["goal_amount"]),
                format_currency(i["raised_amount"]),
                format_currency(i.get("remaining", 0)),
                f"{i['expected_roi']}%",
                str(i.get("contributor_count", 0)),
                i["status"].capitalize(),
                format_date(i["created_at"]),
            ])
        self.table.populate(rows)
        for idx, i in enumerate(self._filtered):
            self.table.color_cell(
                idx, 7, investment_status_color(i["status"])
            )
        count = len(self._filtered)
        self.result_count.setText(
            f"{count} request{'s' if count != 1 else ''}"
        )
        self._on_selection_change()

    def _selected(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._filtered):
            return None
        return self._filtered[idx]

    def _on_selection_change(self):
        inv = self._selected()
        can_close = inv is not None and inv["status"] == "open"
        self.btn_close.setEnabled(can_close)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _open_create_dialog(self):
        dlg = CreateInvestmentDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            result = create_investment(
                farmer_id=self._farmer_id,
                title=data["title"],
                description=data["description"],
                goal_amount=data["goal_amount"],
                expected_roi=data["expected_roi"],
            )
            if result["success"]:
                QMessageBox.information(
                    self, "Created!",
                    "✅ Investment request created successfully!\n"
                    "Investors can now browse and fund your project."
                )
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])

    def _close_selected(self):
        inv = self._selected()
        if not inv:
            return
        reply = QMessageBox.question(
            self, "Close Investment",
            f"Close '{inv['title']}'?\n"
            f"Raised so far: {format_currency(inv['raised_amount'])}\n"
            "This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = close_investment(inv["id"], self._farmer_id)
            if result["success"]:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", result["message"])


# ── Create Investment Dialog ───────────────────────────────────────────────────

class CreateInvestmentDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Investment Request")
        self.setFixedWidth(460)
        self.setModal(True)
        self._build()

    def _build(self):
        self.setStyleSheet("""
            QDialog { background:#12202e; }
            QLabel  { color:#c8dff0; font-size:13px; }
            QLineEdit, QDoubleSpinBox, QTextEdit {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:6px; padding:8px 10px;
                color:#e8f5e9; font-size:13px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border:1px solid #52b788;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title_lbl = QLabel("New Investment Request")
        title_lbl.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#52b788;"
        )
        layout.addWidget(title_lbl)
        layout.addWidget(_divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_title = QLineEdit()
        self.f_title.setPlaceholderText(
            "e.g. Mango Orchard Expansion"
        )

        self.f_goal = QDoubleSpinBox()
        self.f_goal.setMinimum(1000)
        self.f_goal.setMaximum(10000000)
        self.f_goal.setValue(50000)
        self.f_goal.setSingleStep(5000)
        self.f_goal.setPrefix("৳  ")
        self.f_goal.setDecimals(2)

        self.f_roi = QDoubleSpinBox()
        self.f_roi.setMinimum(0)
        self.f_roi.setMaximum(1000)
        self.f_roi.setValue(15)
        self.f_roi.setSingleStep(1)
        self.f_roi.setSuffix("  %")
        self.f_roi.setDecimals(1)

        self.f_desc = QTextEdit()
        self.f_desc.setFixedHeight(100)
        self.f_desc.setPlaceholderText(
            "Describe your project, how funds will be used, "
            "and the expected return timeline…"
        )

        form.addRow("Title *",        self.f_title)
        form.addRow("Goal Amount *",  self.f_goal)
        form.addRow("Expected ROI *", self.f_roi)
        form.addRow("Description",    self.f_desc)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.button(QDialogButtonBox.Ok).setText("✅  Create Request")
        btns.setStyleSheet("""
            QPushButton {
                background:#2d6a4f; color:white; border:none;
                border-radius:6px; padding:8px 20px; font-size:13px;
            }
            QPushButton:hover { background:#40916c; }
        """)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return {
            "title":       self.f_title.text().strip(),
            "goal_amount": self.f_goal.value(),
            "expected_roi":self.f_roi.value(),
            "description": self.f_desc.toPlainText().strip(),
        }


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
            selection-background-color:#2d6a4f;
        }
    """


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
