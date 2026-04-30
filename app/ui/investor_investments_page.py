# app/ui/investor_investments_page.py
# Two pages for investors:
#   InvestorOpportunitiesPage — browse open investments and contribute
#   InvestorPortfolioPage     — track your own contributions

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QDialog,
    QFormLayout, QDoubleSpinBox, QDialogButtonBox,
    QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt

import app.utils.session as session
from app.utils.helpers import (
    format_currency, format_date, truncate, investment_status_color
)
from app.services.investment_service import (
    get_open_investments, get_portfolio, contribute
)
from app.ui.widgets.data_table import DataTable


# ── Opportunities Page ─────────────────────────────────────────────────────────

class InvestorOpportunitiesPage(QWidget):
    """Browse and fund open investment requests."""

    COLUMNS = ["ID", "Title", "Farmer", "Goal",
               "Raised", "Remaining", "ROI %", "Progress", "Contributors"]

    def __init__(self):
        super().__init__()
        self._investments = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("🌱  Investment Opportunities")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#9b5de5;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search title / farmer…")
        self.search.setFixedHeight(34)
        self.search.setFixedWidth(240)
        self.search.setStyleSheet(_input_style())
        self.search.textChanged.connect(self.refresh)

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)

        title_row.addWidget(self.search)
        title_row.addWidget(btn_refresh)
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

        self.btn_detail = _btn("🔍  View Details", "#2a1a4a", "#4a2a8a")
        self.btn_detail.setEnabled(False)
        self.btn_detail.clicked.connect(self._show_detail)

        self.btn_invest = _btn("💰  Invest Now", "#1b4332", "#2d6a4f")
        self.btn_invest.setEnabled(False)
        self.btn_invest.clicked.connect(self._open_invest_dialog)

        btn_row.addWidget(self.btn_detail)
        btn_row.addWidget(self.btn_invest)
        layout.addLayout(btn_row)

    def refresh(self):
        search = self.search.text()
        self._investments = get_open_investments(search)
        rows = []
        for i in self._investments:
            pct = i.get("progress_pct", 0) or 0
            rows.append([
                i["id"],
                truncate(i["title"], 26),
                truncate(i.get("farmer_name", "—"), 18),
                format_currency(i["goal_amount"]),
                format_currency(i["raised_amount"]),
                format_currency(i.get("remaining", 0)),
                f"{i['expected_roi']}%",
                f"{pct}%",
                str(i.get("contributor_count", 0)),
            ])
        self.table.populate(rows)
        count = len(self._investments)
        self.result_count.setText(
            f"{count} open opportunit{'ies' if count != 1 else 'y'}"
        )
        self._on_selection_change()

    def _selected(self):
        idx = self.table.get_selected_row_index()
        if idx is None or idx >= len(self._investments):
            return None
        return self._investments[idx]

    def _on_selection_change(self):
        has = self._selected() is not None
        self.btn_detail.setEnabled(has)
        self.btn_invest.setEnabled(has)

    def _show_detail(self):
        inv = self._selected()
        if inv:
            InvestmentDetailDialog(inv, parent=self).exec_()

    def _open_invest_dialog(self):
        inv = self._selected()
        if not inv:
            return
        dlg = ContributeDialog(inv, session.get_id(), parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()


# ── Portfolio Page ─────────────────────────────────────────────────────────────

class InvestorPortfolioPage(QWidget):
    """Track the investor's own contributions."""

    COLUMNS = ["Inv#", "Title", "Farmer", "My Contribution",
               "Total Raised", "Goal", "ROI %", "Status", "Date"]

    def __init__(self):
        super().__init__()
        self._portfolio = []
        self._build()
        self.refresh()

    def _build(self):
        self.setStyleSheet("background:#0f1923;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("📈  My Portfolio")
        title.setStyleSheet(
            "font-size:20px;font-weight:bold;color:#9b5de5;"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        btn_refresh = _btn("↻  Refresh", "#1a3a5c", "#2d4a7a")
        btn_refresh.clicked.connect(self.refresh)
        title_row.addWidget(btn_refresh)
        layout.addLayout(title_row)
        layout.addWidget(_divider())

        # Summary cards
        self._summary = {}
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)
        for key, label, color in [
            ("total_invested", "Total Invested",    "#9b5de5"),
            ("active_count",   "Active Investments","#4895ef"),
            ("funded_count",   "Funded Projects",   "#52b788"),
        ]:
            card = _MiniCard(label, "0", color)
            self._summary[key] = card
            summary_row.addWidget(card)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        self.result_count = QLabel("")
        self.result_count.setStyleSheet("font-size:11px;color:#7a9ab5;")
        layout.addWidget(self.result_count)

        self.table = DataTable(self.COLUMNS)
        layout.addWidget(self.table)

    def refresh(self):
        investor_id = session.get_id()
        self._portfolio = get_portfolio(investor_id)

        total_invested = sum(p.get("my_contribution", 0) for p in self._portfolio)
        active_count   = sum(1 for p in self._portfolio if p["status"] == "open")
        funded_count   = sum(1 for p in self._portfolio if p["status"] == "funded")

        self._summary["total_invested"].set_value(format_currency(total_invested))
        self._summary["active_count"].set_value(str(active_count))
        self._summary["funded_count"].set_value(str(funded_count))

        rows = []
        for p in self._portfolio:
            rows.append([
                p["id"],
                truncate(p["title"], 24),
                truncate(p.get("farmer_name", "—"), 18),
                format_currency(p.get("my_contribution", 0)),
                format_currency(p["raised_amount"]),
                format_currency(p["goal_amount"]),
                f"{p['expected_roi']}%",
                p["status"].capitalize(),
                format_date(p.get("contributed_at", "")),
            ])
        self.table.populate(rows)

        for i, p in enumerate(self._portfolio):
            self.table.color_cell(
                i, 7, investment_status_color(p["status"])
            )

        count = len(self._portfolio)
        self.result_count.setText(
            f"{count} investment{'s' if count != 1 else ''}"
        )


# ── Investment Detail Dialog ───────────────────────────────────────────────────

class InvestmentDetailDialog(QDialog):

    def __init__(self, investment: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Investment Details")
        self.setFixedWidth(460)
        self.setModal(True)
        self._build(investment)

    def _build(self, i: dict):
        self.setStyleSheet(
            "QDialog{background:#12202e;} QLabel{color:#c8dff0;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        title_lbl = QLabel(i.get("title", "—"))
        title_lbl.setStyleSheet(
            "font-size:16px;font-weight:bold;color:#9b5de5;"
        )
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)
        layout.addWidget(_divider())

        pct = i.get("progress_pct", 0) or 0
        for label, value in [
            ("Farmer",       i.get("farmer_name", "—")),
            ("Farm",         i.get("farm_name") or "—"),
            ("Goal Amount",  format_currency(i["goal_amount"])),
            ("Raised",       format_currency(i["raised_amount"])),
            ("Remaining",    format_currency(i.get("remaining", 0))),
            ("Progress",     f"{pct}%"),
            ("Expected ROI", f"{i['expected_roi']}%"),
            ("Contributors", str(i.get("contributor_count", 0))),
            ("Status",       i["status"].capitalize()),
            ("Created",      format_date(i.get("created_at", ""))),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;min-width:110px;"
            )
            val = QLabel(str(value))
            val.setStyleSheet("font-size:13px;color:#d0e8f5;")
            val.setWordWrap(True)
            row.addWidget(lbl)
            row.addWidget(val, stretch=1)
            layout.addLayout(row)

        desc = i.get("description", "")
        if desc:
            layout.addWidget(_divider())
            desc_lbl = QLabel("Description")
            desc_lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;font-weight:bold;"
            )
            layout.addWidget(desc_lbl)
            desc_val = QLabel(desc)
            desc_val.setStyleSheet("font-size:13px;color:#c8dff0;")
            desc_val.setWordWrap(True)
            layout.addWidget(desc_val)

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


# ── Contribute Dialog ──────────────────────────────────────────────────────────

class ContributeDialog(QDialog):

    def __init__(self, investment: dict, investor_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invest Now")
        self.setFixedWidth(420)
        self.setModal(True)
        self._investment = investment
        self._investor_id = investor_id
        self._build()

    def _build(self):
        i = self._investment
        remaining = round(
            i["goal_amount"] - i["raised_amount"], 2
        )

        self.setStyleSheet("""
            QDialog { background:#12202e; }
            QLabel  { color:#c8dff0; font-size:13px; }
            QDoubleSpinBox {
                background:#1a2940; border:1px solid #2d4a6a;
                border-radius:6px; padding:8px 10px;
                color:#e8f5e9; font-size:13px;
            }
            QDoubleSpinBox:focus { border:1px solid #9b5de5; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title_lbl = QLabel(f"Invest in: {i['title']}")
        title_lbl.setStyleSheet(
            "font-size:15px;font-weight:bold;color:#9b5de5;"
        )
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)
        layout.addWidget(_divider())

        for label, value in [
            ("Goal",        format_currency(i["goal_amount"])),
            ("Raised",      format_currency(i["raised_amount"])),
            ("Remaining",   format_currency(remaining)),
            ("Expected ROI",f"{i['expected_roi']}%"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                "font-size:12px;color:#7a9ab5;min-width:110px;"
            )
            val = QLabel(str(value))
            val.setStyleSheet("font-size:13px;color:#d0e8f5;font-weight:bold;")
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)

        layout.addWidget(_divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(100)
        self.amount_spin.setMaximum(remaining if remaining > 0 else 100)
        self.amount_spin.setValue(min(1000, remaining))
        self.amount_spin.setSingleStep(500)
        self.amount_spin.setPrefix("৳  ")
        self.amount_spin.setDecimals(2)

        form.addRow("Amount *", self.amount_spin)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btns.button(QDialogButtonBox.Ok).setText("✅  Confirm Investment")
        btns.setStyleSheet("""
            QPushButton {
                background:#6a3fa0; color:white; border:none;
                border-radius:6px; padding:8px 20px; font-size:13px;
            }
            QPushButton:hover { background:#9b5de5; }
        """)
        btns.accepted.connect(self._on_confirm)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_confirm(self):
        result = contribute(
            investor_id=self._investor_id,
            investment_id=self._investment["id"],
            amount=self.amount_spin.value(),
        )
        if result["success"]:
            msg = (
                f"✅ Investment of {format_currency(self.amount_spin.value())} confirmed!"
            )
            if result.get("new_status") == "funded":
                msg += "\n\n🎉 This project is now FULLY FUNDED!"
            QMessageBox.information(self, "Investment Confirmed!", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", result["message"])


# ── Shared small widgets ────────────────────────────────────────────────────────

class _MiniCard(QWidget):
    def __init__(self, label, value, color):
        super().__init__()
        self.setFixedHeight(64)
        self.setMinimumWidth(130)
        self.setStyleSheet(f"""
            QWidget {{
                background:#12202e;
                border:1px solid {color}33;
                border-radius:10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(2)
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"font-size:16px;font-weight:bold;color:{color};"
            "background:transparent;border:none;"
        )
        lbl = QLabel(label)
        lbl.setStyleSheet(
            "font-size:10px;color:#7a9ab5;"
            "background:transparent;border:none;"
        )
        layout.addWidget(self._val)
        layout.addWidget(lbl)

    def set_value(self, v):
        self._val.setText(v)


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
        QLineEdit:focus { border:1px solid #9b5de5; }
    """


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("color:#1a2940;")
    return line
