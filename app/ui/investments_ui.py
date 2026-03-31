# app/ui/investments_ui.py
# Investments page: farmers create funding requests, investors fund them

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QDialog, QFormLayout, QLineEdit,
                              QDoubleSpinBox, QTextEdit, QMessageBox,
                              QScrollArea, QFrame, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt
import app.utils.session as session
from app.services import investment_service
from app.ui.styles import STATUS_COLORS


class InvestDialog(QDialog):
    """Amount input dialog for investors."""

    def __init__(self, parent, investment: dict):
        super().__init__(parent)
        self.setWindowTitle("Invest in Project")
        self.setFixedWidth(380)
        self.setStyleSheet("QDialog{background:#0f1923;} QLabel{color:#d8f3dc;}")
        self._inv = investment
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        remaining = self._inv["goal_amount"] - self._inv["raised_amount"]
        layout.addRow("Project:", QLabel(f"<b>{self._inv['title']}</b>"))
        layout.addRow("Goal:", QLabel(f"৳ {self._inv['goal_amount']:,.0f}"))
        remaining_lbl = QLabel(f"৳ {remaining:,.0f}")
        remaining_lbl.setStyleSheet("color:#f4a261; font-weight:bold;")
        layout.addRow("Still Needed:", remaining_lbl)
        layout.addRow("Expected ROI:", QLabel(f"{self._inv['expected_roi']}%"))

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(100, max(remaining, 100))
        self.amount_spin.setValue(min(5000, remaining))
        self.amount_spin.setDecimals(0)
        self.amount_spin.setPrefix("৳ ")
        self.amount_spin.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        layout.addRow("Your Investment:", self.amount_spin)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background:#1a2940;color:#e76f51;border:1px solid #9b2226;border-radius:6px;padding:8px 14px;")
        cancel_btn.clicked.connect(self.reject)
        invest_btn = QPushButton("📈  Invest Now")
        invest_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold;")
        invest_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(invest_btn)
        layout.addRow(btn_row)

    def get_amount(self):
        return self.amount_spin.value()


class CreateInvestmentDialog(QDialog):
    """Farmer creates a new investment request."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Funding Request")
        self.setMinimumWidth(420)
        self.setStyleSheet("QDialog{background:#0f1923;} QLabel{color:#d8f3dc;}")
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setVerticalSpacing(12)

        def inp(ph=""):
            w = QLineEdit(); w.setPlaceholderText(ph)
            w.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")
            return w

        self.title_inp = inp("e.g. Mango Orchard Expansion")
        self.desc_inp = QTextEdit()
        self.desc_inp.setFixedHeight(80)
        self.desc_inp.setPlaceholderText("Describe your project and how funds will be used…")
        self.desc_inp.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.goal_spin = QDoubleSpinBox()
        self.goal_spin.setRange(1000, 10000000)
        self.goal_spin.setValue(50000)
        self.goal_spin.setDecimals(0)
        self.goal_spin.setPrefix("৳ ")
        self.goal_spin.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        self.roi_spin = QDoubleSpinBox()
        self.roi_spin.setRange(1, 100)
        self.roi_spin.setValue(15)
        self.roi_spin.setSuffix(" %")
        self.roi_spin.setStyleSheet("background:#1a2940;border:1px solid #2d6a4f;border-radius:6px;padding:7px;color:#e8f5e9;")

        layout.addRow("Title:", self.title_inp)
        layout.addRow("Description:", self.desc_inp)
        layout.addRow("Funding Goal:", self.goal_spin)
        layout.addRow("Expected ROI:", self.roi_spin)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background:#1a2940;color:#e76f51;border:1px solid #9b2226;border-radius:6px;padding:8px 14px;")
        cancel_btn.clicked.connect(self.reject)
        create_btn = QPushButton("🚀  Create Request")
        create_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:8px 18px;font-weight:bold;")
        create_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn); btn_row.addStretch(); btn_row.addWidget(create_btn)
        layout.addRow(btn_row)

    def get_data(self):
        return {
            "title": self.title_inp.text().strip(),
            "description": self.desc_inp.toPlainText().strip(),
            "goal_amount": self.goal_spin.value(),
            "expected_roi": self.roi_spin.value(),
        }


class InvestmentCard(QFrame):
    """A card widget representing one investment round."""

    def __init__(self, inv: dict, can_invest: bool = False, on_invest=None):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame { background:#12202e; border-radius:12px; border:1px solid #1b4332; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(inv["title"])
        title_lbl.setStyleSheet("font-size:16px;font-weight:bold;color:#52b788;")
        status_color = STATUS_COLORS.get(inv["status"], "#ffffff")
        status_lbl = QLabel(f"  {inv['status'].upper()}  ")
        status_lbl.setStyleSheet(f"font-size:11px;color:{status_color};background:#0d2137;"
                                  "border-radius:4px;padding:2px 6px;font-weight:bold;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(status_lbl)
        layout.addLayout(title_row)

        # Farmer & description
        farmer_lbl = QLabel(f"🧑‍🌾  {inv.get('farmer_name', '—')}  ·  {inv.get('farm_name','')}")
        farmer_lbl.setStyleSheet("font-size:11px;color:#74c69d;")
        layout.addWidget(farmer_lbl)

        if inv.get("description"):
            desc = QLabel(inv["description"][:160] + ("…" if len(inv["description"]) > 160 else ""))
            desc.setStyleSheet("font-size:12px;color:#b7e4c7;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        # Progress
        pct = int((inv["raised_amount"] / inv["goal_amount"]) * 100) if inv["goal_amount"] > 0 else 0
        prog = QProgressBar()
        prog.setRange(0, 100)
        prog.setValue(pct)
        prog.setFormat(f"{pct}%  (৳{inv['raised_amount']:,.0f} of ৳{inv['goal_amount']:,.0f})")
        prog.setFixedHeight(20)
        layout.addWidget(prog)

        # ROI & invest button
        bottom_row = QHBoxLayout()
        roi_lbl = QLabel(f"📈  Expected ROI: {inv['expected_roi']}%")
        roi_lbl.setStyleSheet("font-size:12px;color:#95d5b2;")
        bottom_row.addWidget(roi_lbl)
        bottom_row.addStretch()

        if can_invest and inv["status"] == "open":
            invest_btn = QPushButton("💰  Invest")
            invest_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:6px;padding:7px 18px;font-weight:bold;")
            invest_btn.clicked.connect(lambda: on_invest(inv))
            bottom_row.addWidget(invest_btn)

        layout.addLayout(bottom_row)


class InvestmentsPage(QWidget):
    """Investments module page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("📈  Investments")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        hdr.addWidget(title)
        hdr.addStretch()

        self._role = session.get_role()
        if self._role == "farmer":
            create_btn = QPushButton("🚀  Create Funding Request")
            create_btn.setStyleSheet("background:#2d6a4f;color:white;border:none;border-radius:7px;padding:8px 18px;font-weight:bold;")
            create_btn.clicked.connect(self._create_request)
            hdr.addWidget(create_btn)
        layout.addLayout(hdr)

        # Scrollable cards area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:#0f1923;}")
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

    def refresh(self):
        # Clear old cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        role = self._role
        uid = session.get_id()
        can_invest = (role == "investor")

        if role == "farmer":
            investments = investment_service.get_farmer_investments(uid)
        else:
            investments = investment_service.get_all_investments()

        if not investments:
            no_lbl = QLabel("No investment rounds found.")
            no_lbl.setStyleSheet("color:#74c69d; font-size:14px; padding:24px;")
            no_lbl.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_lbl)
        else:
            for inv in investments:
                card = InvestmentCard(inv, can_invest=can_invest, on_invest=self._do_invest)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _create_request(self):
        dlg = CreateInvestmentDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            if not d["title"]:
                QMessageBox.warning(self, "Invalid", "Title is required.")
                return
            investment_service.create_investment_request(**d)
            QMessageBox.information(self, "Created", "✅ Funding request created successfully!")
            self.refresh()

    def _do_invest(self, inv: dict):
        dlg = InvestDialog(self, inv)
        if dlg.exec_() == QDialog.Accepted:
            amount = dlg.get_amount()
            investment_service.invest(inv["id"], amount)
            QMessageBox.information(self, "Invested",
                f"✅ You've invested ৳{amount:,.0f} in '{inv['title']}'!")
            self.refresh()
