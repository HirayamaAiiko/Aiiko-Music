import re
from PyQt6.QtCore import Qt, QRect, QRectF, QSize
from PyQt6.QtWidgets import QWidget, QPlainTextEdit, QLabel, QPushButton
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QPen, QSyntaxHighlighter, QTextCharFormat
class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(10)
    def setText(self, text):
        self.full_text = text
        self.update_elided_text()
    def resizeEvent(self, event):
        self.update_elided_text()
        super().resizeEvent(event)
    def update_elided_text(self):
        from PyQt6.QtGui import QFontMetrics
        from PyQt6.QtCore import Qt
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.full_text, Qt.TextElideMode.ElideRight, self.width() - 5)
        super().setText(elided)
class LyricsHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, accent_color="#1DB954"):
        super().__init__(parent)
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor(accent_color))
    def highlightBlock(self, text):
        pattern = r"\[\d{2}:\d{2}\.\d{2}\]"
        for match in re.finditer(pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.timestamp_format)
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)
    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: transparent;
                color: #E0E0E0;
                border: none;
                font-family: Consolas, "Courier New", monospace;
                font-size: 14px;
            }
        """)
    def lineNumberAreaWidth(self):
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val /= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))
    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(255, 255, 255, 5))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(0, top, self.lineNumberArea.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            blockNumber += 1
class EditorContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.overlay_widget = None
    def set_overlay(self, widget):
        self.overlay_widget = widget
        widget.setParent(self)
        self.update_overlay_pos()
        self.overlay_widget.show()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_overlay_pos()
    def update_overlay_pos(self):
        if self.overlay_widget:
            self.overlay_widget.adjustSize()
            x = self.width() - self.overlay_widget.width() - 15
            y = 10
            self.overlay_widget.move(x, y)
            self.overlay_widget.raise_()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2B2B2B"))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 8.0, 8.0)
        pen = QPen(QColor("#454545"))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 7.5, 7.5)
        painter.end()
class OutlineButton(QPushButton):
    def __init__(self, text, color_hex, hover_bg_alpha=15, parent=None):
        super().__init__(text, parent)
        self._color = QColor(color_hex)
        self._hover_bg_alpha = hover_bg_alpha
        self._hovered = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"QPushButton {{ color: {color_hex}; background: transparent; border: none; padding: 0 15px; font-size: 14px; font-weight: 500; }}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hovered:
            bg = QColor(self._color)
            bg.setAlpha(self._hover_bg_alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5), 6.0, 6.0)
        pen = QPen(self._color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 5.5, 5.5)
        painter.end()
        super().paintEvent(event)