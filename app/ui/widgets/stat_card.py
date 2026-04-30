# app/ui/widgets/stat_card.py
# Reusable stat card widget for dashboard overview pages.
# Usage:
#   card = StatCard(icon="🌾", label="Total Products", value="12", color="#52b788")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class StatCard(QWidget):
    """
    A single metric card showing: icon, value, and label.
    Used in rows of 3–4 across dashboard overview pages.
    """

    def __init__(self, icon: str, label: str, value: str,
                 color: str = "#52b788", parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        self.setMinimumWidth(160)
        self._color = color
        self._build(icon, label, value)

    def _build(self, icon: str, label: str, value: str):
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #12202e, stop:1 #0d1b2a);
                border: 1px solid {self._color}33;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        # Top row: icon
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size:22px;background:transparent;border:none;")

        # Value
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size:24px;font-weight:bold;color:{self._color};"
            f"background:transparent;border:none;"
        )

        # Label
        label_lbl = QLabel(label)
        label_lbl.setStyleSheet(
            "font-size:11px;color:#7a9ab5;background:transparent;border:none;"
        )

        layout.addWidget(icon_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(label_lbl)

    def update_value(self, new_value: str):
        """Call this to refresh the displayed number without rebuilding."""
        self.value_lbl.setText(new_value)
