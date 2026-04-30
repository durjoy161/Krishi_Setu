# app/ui/widgets/data_table.py
# Reusable styled QTableWidget used across all modules.
# Usage:
#   table = DataTable(columns=["Name", "Price", "Stock"])
#   table.populate(rows)   # rows = list of lists

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class DataTable(QTableWidget):
    """
    A styled, read-only table widget.
    - Alternating row colors
    - Full-row selection
    - No edit triggers
    - Stretching last column
    """

    ROW_HEIGHT     = 38
    HEADER_HEIGHT  = 40

    def __init__(self, columns: list[str], parent=None):
        super().__init__(0, len(columns), parent)
        self._columns = columns
        self._setup()

    def _setup(self):
        self.setHorizontalHeaderLabels(self._columns)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.NoFocus)

        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setLastSectionStretch = True
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setFixedHeight(self.HEADER_HEIGHT)

        self.verticalHeader().setDefaultSectionSize(self.ROW_HEIGHT)

        self.setStyleSheet("""
            QTableWidget {
                background-color: #0f1923;
                alternate-background-color: #111e2c;
                color: #c8dff0;
                border: none;
                font-size: 13px;
                gridline-color: transparent;
                outline: none;
            }
            QTableWidget::item {
                padding: 6px 12px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1a3a5c;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #0d1b2a;
                color: #4a90b8;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid #1a2940;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QScrollBar:vertical {
                background: #0d1b2a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2d4a6a;
                border-radius: 4px;
            }
        """)

    def populate(self, rows: list[list]):
        """
        Fill the table with data.
        Each inner list must have the same length as columns.
        Clears existing rows first.
        """
        self.setRowCount(0)
        for row_data in rows:
            row_idx = self.rowCount()
            self.insertRow(row_idx)
            for col_idx, cell in enumerate(row_data):
                item = QTableWidgetItem(str(cell) if cell is not None else "—")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.setItem(row_idx, col_idx, item)

    def get_selected_row_index(self) -> int | None:
        """Return the currently selected row index, or None."""
        rows = self.selectedItems()
        if not rows:
            return None
        return self.currentRow()

    def color_cell(self, row: int, col: int, color_hex: str):
        """Apply a foreground color to a specific cell (for status badges)."""
        item = self.item(row, col)
        if item:
            item.setForeground(QColor(color_hex))
