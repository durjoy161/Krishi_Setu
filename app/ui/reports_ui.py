# app/ui/reports_ui.py
# Reports page: Sales, Inventory, and Profit reports with CSV export

import csv
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTabWidget, QTextBrowser,
                              QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
import app.utils.session as session
from app.services import report_service


def _html_table(headers: list, rows: list, col_colors: dict = None) -> str:
    """Generate a styled HTML table string."""
    th_style = ("background:#1b4332;color:#b7e4c7;padding:8px 12px;"
                "font-weight:bold;font-size:13px;border:1px solid #2d6a4f;")
    td_style = ("color:#d8f3dc;padding:7px 12px;font-size:12px;"
                "border:1px solid #172a3a;")
    tr_alt   = "background:#172a3a;"
    tr_norm  = "background:#12202e;"

    html = f"""
    <style>
      body {{ background:#0f1923; font-family:'Segoe UI',Arial,sans-serif; }}
      table {{ width:100%; border-collapse:collapse; border-radius:8px; overflow:hidden; }}
    </style>
    <table>
      <tr>{"".join(f'<th style="{th_style}">{h}</th>' for h in headers)}</tr>
    """
    for i, row in enumerate(rows):
        bg = tr_alt if i % 2 else tr_norm
        html += f"<tr style='{bg}'>"
        for j, cell in enumerate(row):
            extra = ""
            if col_colors and j in col_colors:
                extra = f"color:{col_colors[j]};"
            html += f"<td style='{td_style}{extra}'>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    return html


class ReportsPage(QWidget):
    """Reports and analytics page with three tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📑  Reports & Analytics")
        title.setStyleSheet("font-size:22px;font-weight:bold;color:#52b788;")
        hdr.addWidget(title)
        hdr.addStretch()
        export_btn = QPushButton("📥  Export to CSV")
        export_btn.setStyleSheet("background:#1b4332;color:white;border:1px solid #52b788;border-radius:7px;padding:8px 16px;")
        export_btn.clicked.connect(self._export_csv)
        hdr.addWidget(export_btn)
        layout.addLayout(hdr)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane{border:1px solid #1b4332;border-radius:8px;background:#12202e;}
            QTabBar::tab{background:#0d2137;color:#74c69d;padding:8px 20px;border-radius:6px 6px 0 0;margin-right:3px;}
            QTabBar::tab:selected{background:#1b4332;color:white;font-weight:bold;}
        """)

        self.sales_browser    = self._make_browser()
        self.inventory_browser = self._make_browser()
        self.profit_browser   = self._make_browser()

        self.tabs.addTab(self.sales_browser,    "📊  Sales Report")
        self.tabs.addTab(self.inventory_browser,"📦  Inventory Report")
        self.tabs.addTab(self.profit_browser,   "💰  Profit Report")
        layout.addWidget(self.tabs)

    def _make_browser(self):
        b = QTextBrowser()
        b.setStyleSheet("background:#0f1923;border:none;")
        b.setOpenExternalLinks(False)
        return b

    def refresh(self):
        role = session.get_role()
        fid = session.get_id() if role == "farmer" else None

        # ── Sales ──────────────────────────────────────────────────────────────
        self._sales_data = report_service.get_sales_report(fid)
        headers = ["Product", "Category", "Unit", "Orders", "Total Qty", "Revenue (৳)"]
        rows = [[r["product"], r["category"], r["unit"],
                 str(r["total_orders"]),
                 f"{r['total_qty']:.1f}",
                 f"৳{r['total_revenue']:,.2f}"] for r in self._sales_data]
        if rows:
            self.sales_browser.setHtml(_html_table(headers, rows, {5: "#52b788"}))
        else:
            self.sales_browser.setHtml("<p style='color:#74c69d;padding:20px;'>No sales data available.</p>")

        # ── Inventory ─────────────────────────────────────────────────────────
        self._inv_data = report_service.get_inventory_report(fid)
        headers = ["Product", "Category", "Unit", "Stock", "Price (৳)", "Expiry", "Farmer"]
        rows = []
        for r in self._inv_data:
            stock_val = f"{r['stock_qty']:.1f}"
            rows.append([r["name"], r["category"], r["unit"], stock_val,
                         f"৳{r['price']:.2f}", r.get("expiry_date","—"),
                         r.get("farmer_name","—")])
        if rows:
            self.inventory_browser.setHtml(_html_table(headers, rows, {3: "#f4a261"}))
        else:
            self.inventory_browser.setHtml("<p style='color:#74c69d;padding:20px;'>No inventory data.</p>")

        # ── Profit ────────────────────────────────────────────────────────────
        self._profit_data = report_service.get_profit_report(fid)
        headers = ["Product", "Total Billed (৳)", "Total Received (৳)", "Outstanding (৳)"]
        rows = [[r["product"],
                 f"৳{r['total_due']:,.2f}",
                 f"৳{r['total_paid']:,.2f}",
                 f"৳{r['outstanding']:,.2f}"] for r in self._profit_data]
        if rows:
            self.profit_browser.setHtml(_html_table(headers, rows, {2: "#52b788", 3: "#e76f51"}))
        else:
            self.profit_browser.setHtml("<p style='color:#74c69d;padding:20px;'>No profit data available.</p>")

    def _export_csv(self):
        tab = self.tabs.currentIndex()
        if tab == 0:
            data = self._sales_data
            headers = ["product", "category", "unit", "total_orders", "total_qty", "total_revenue"]
            fname = "sales_report.csv"
        elif tab == 1:
            data = self._inv_data
            headers = ["name", "category", "unit", "stock_qty", "price", "expiry_date", "farmer_name"]
            fname = "inventory_report.csv"
        else:
            data = self._profit_data
            headers = ["product", "total_due", "total_paid", "outstanding"]
            fname = "profit_report.csv"

        if not data:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", os.path.expanduser(f"~/{fname}"), "CSV files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
        QMessageBox.information(self, "Exported", f"✅ Saved to:\n{path}")
