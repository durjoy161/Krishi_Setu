# app/ui/widgets/bar_chart.py
# Pure PyQt5 bar chart widget. No matplotlib or external libs needed.
# Usage:
#   chart = BarChart(title="Monthly Revenue")
#   chart.set_data(
#       labels=["Jan", "Feb", "Mar"],
#       values=[1200.0, 3400.0, 2800.0],
#       color="#52b788"
#   )

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush


class BarChart(QWidget):
    """
    Simple vertical bar chart drawn with QPainter.
    Supports a title, colored bars, value labels on top,
    and x-axis labels below each bar.
    """

    def __init__(self, title: str = "", color: str = "#52b788",
                 parent=None):
        super().__init__(parent)
        self._title  = title
        self._color  = color
        self._labels = []
        self._values = []
        self.setMinimumHeight(220)
        self.setMinimumWidth(300)

    def set_data(self, labels: list, values: list, color: str = None):
        """Update chart data and trigger a repaint."""
        self._labels = labels
        self._values = [float(v) for v in values]
        if color:
            self._color = color
        self.update()

    def paintEvent(self, event):
        if not self._values:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Margins
        left   = 60
        right  = 20
        top    = 40
        bottom = 50

        chart_w = w - left - right
        chart_h = h - top - bottom

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0f1923"))

        # Title
        if self._title:
            painter.setPen(QColor("#d0e8f5"))
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRect(0, 8, w, 24),
                Qt.AlignHCenter | Qt.AlignVCenter,
                self._title
            )

        max_val = max(self._values) if self._values else 1
        if max_val == 0:
            max_val = 1

        n = len(self._values)
        bar_spacing = 8
        bar_w = max(10, (chart_w - bar_spacing * (n + 1)) // n)

        # Y-axis grid lines
        grid_color = QColor("#1a2940")
        painter.setPen(QPen(grid_color, 1))
        for i in range(5):
            y = top + int(chart_h * i / 4)
            painter.drawLine(left, y, left + chart_w, y)

            # Y-axis value label
            val = max_val * (4 - i) / 4
            painter.setPen(QColor("#4a6a8a"))
            font_s = QFont("Segoe UI", 7)
            painter.setFont(font_s)
            label = _fmt_value(val)
            painter.drawText(
                QRect(0, y - 8, left - 4, 16),
                Qt.AlignRight | Qt.AlignVCenter,
                label
            )
            painter.setPen(QPen(grid_color, 1))

        # Bars
        bar_color  = QColor(self._color)
        hover_color = bar_color.lighter(130)

        for idx, (label, value) in enumerate(
            zip(self._labels, self._values)
        ):
            bar_h = int((value / max_val) * chart_h)
            x = left + bar_spacing + idx * (bar_w + bar_spacing)
            y = top + chart_h - bar_h

            # Bar body
            painter.setBrush(QBrush(bar_color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

            # Value label on top of bar
            painter.setPen(QColor("#d0e8f5"))
            font_v = QFont("Segoe UI", 7, QFont.Bold)
            painter.setFont(font_v)
            val_text = _fmt_value(value)
            painter.drawText(
                QRect(x - 10, y - 18, bar_w + 20, 16),
                Qt.AlignHCenter | Qt.AlignBottom,
                val_text
            )

            # X-axis label
            painter.setPen(QColor("#7a9ab5"))
            font_l = QFont("Segoe UI", 7)
            painter.setFont(font_l)
            short_label = label[:8] if len(label) > 8 else label
            painter.drawText(
                QRect(x - 4, top + chart_h + 6, bar_w + 8, 20),
                Qt.AlignHCenter | Qt.AlignTop,
                short_label
            )

        # Axis lines
        painter.setPen(QPen(QColor("#2d4a6a"), 1))
        painter.drawLine(left, top, left, top + chart_h)
        painter.drawLine(left, top + chart_h, left + chart_w, top + chart_h)

        painter.end()


def _fmt_value(val: float) -> str:
    """Format a number compactly for chart labels."""
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.1f}K"
    return f"{val:.0f}"
