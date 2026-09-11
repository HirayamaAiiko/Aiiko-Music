from PyQt6.QtWidgets import QLabel, QWidget, QSizePolicy, QAbstractItemView, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtProperty, Qt, QPointF, QObject, QEvent, QPropertyAnimation, QEasingCurve, QSize, QVariantAnimation, QRectF
from PyQt6.QtGui import QPainter, QTextDocument, QMouseEvent, QPixmap, QPainterPath, QColor, QFontMetrics
from qfluentwidgets import TransparentToolButton
class InteractiveHeartButton(TransparentToolButton):
    def __init__(self, player, track, parent=None):
        super().__init__(parent)
        self.player = player
        self.track = track
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet("InteractiveHeartButton { border-radius: 14px; padding: 2px; } InteractiveHeartButton:hover { background-color: rgba(150, 150, 150, 30); }")
        self.update_state()
    def update_state(self):
        from settings_manager import settings
        favs = settings.get('favorites', [])
        self.is_fav = self.track.filepath in favs
        self._update_icon(self.underMouse())
    def _update_icon(self, hovered):
        fav_icon = "heart_active.svg" if self.is_fav else "heart.svg"
        from settings_manager import settings
        import theme_manager
        theme_td = theme_manager.get_theme(settings.get('app_theme', 'Oscuro (Dark)'))
        text_color = theme_td.get('text_color', '#FFFFFF')
        from config import ICON_HEART
        fav_color = '#FF5252' if (self.is_fav or hovered) else text_color
        self.setIcon(self.player.playback_ui_controller._get_icon(fav_icon, ICON_HEART, fav_color))
    def enterEvent(self, event):
        self._update_icon(True)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self._update_icon(False)
        super().leaveEvent(event)
class SmoothScrollFilter(QObject):
    def __init__(self, target_widget, step=220, duration=450, parent=None):
        super().__init__(parent)
        self.target = target_widget
        self.step = step
        self.scroll_bar = target_widget.verticalScrollBar()
        if hasattr(target_widget, 'setVerticalScrollMode'):
            target_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.animation = QPropertyAnimation(self.scroll_bar, b"value", self)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.animation.setDuration(duration)
        viewport = self.target.viewport() if hasattr(self.target, 'viewport') else self.target
        viewport.installEventFilter(self)
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta == 0:
                return super().eventFilter(obj, event)
            if abs(delta) < 120:
                return super().eventFilter(obj, event)
            direction = -1 if delta > 0 else 1
            current_target = self.scroll_bar.value()
            if self.animation.state() == QPropertyAnimation.State.Running:
                current_target = self.animation.endValue()
            target_value = current_target + (direction * self.step)
            target_value = max(self.scroll_bar.minimum(), min(target_value, self.scroll_bar.maximum()))
            if target_value != self.scroll_bar.value():
                self.animation.stop()
                self.animation.setStartValue(self.scroll_bar.value())
                self.animation.setEndValue(target_value)
                self.animation.start()
            return True                                 
        return super().eventFilter(obj, event)
class ResponsiveGridHelper(QObject):
    CELL_W = 180
    CELL_H = 265
    def __init__(self, list_view, spacing=15, parent=None):
        super().__init__(parent)
        self._view = list_view
        self._spacing = spacing
        self._last_width = -1
        self._active = True
        self._is_list_mode = False
        self._list_columns = 4
        self._list_height = 70
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(30)                
        self._debounce_timer.timeout.connect(self._do_recalculate)
        self._view.setSpacing(self._spacing)
        vp = self._view.viewport()
        if vp:
            vp.installEventFilter(self)
    def eventFilter(self, obj, event):
        if not getattr(self, '_active', True):
            return False
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            if self._view.viewMode() != self._view.ViewMode.IconMode:
                return False
            self._debounce_timer.start()
        return False
    def _do_recalculate(self):
        if getattr(self, '_is_recalculating', False):
            return
        self._is_recalculating = True
        try:
            vp_width = self._view.width() - 20                                       
            if vp_width < 50 or vp_width == self._last_width:
                return
            self._last_width = vp_width
            if self._is_list_mode:
                cols = self._list_columns
                if cols == 3 and vp_width <= 1100:
                    cols = 2
                cell_w = max(100, (vp_width // cols) - self._spacing)
                icon_size = 56
                cell_h = self._list_height
                left_margin = 0                                     
            else:
                cell_w = 190
                icon_size = 160
                cell_h = 265
                cols = max(1, vp_width // cell_w)
                used_space = cols * cell_w
                left_margin = max(0, (vp_width - used_space) // 2)
            if self._view.gridSize().width() != cell_w or self._view.gridSize().height() != cell_h:
                self._view.setIconSize(QSize(icon_size, icon_size))
                self._view.setGridSize(QSize(cell_w, cell_h))
            current_margins = self._view.viewportMargins()
            if current_margins.left() != left_margin:
                self._view.setViewportMargins(left_margin, 15, left_margin, 0)
        finally:
            self._is_recalculating = False
    def set_active(self, is_active):
        self._active = is_active
        if is_active:
            self._last_width = -1                    
            self._do_recalculate()
        else:
            self._view.setViewportMargins(0, 15, 0, 0)
    def set_list_mode(self, is_list_mode, columns=4, height=70):
        self._is_list_mode = is_list_mode
        self._list_columns = columns
        self._list_height = height
        self._last_width = -1
        self._do_recalculate()
    def force_recalculate(self):
        self._last_width = -1
        self._do_recalculate()
class MarqueeHtmlLabel(QWidget):
    linkActivated = pyqtSignal(str)
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._html = text
        self._doc = QTextDocument(self)
        self._doc.setDocumentMargin(0)
        self._text_width = 0
        self._offset = 0.0
        self._is_scrolling = False
        self._space = 60                              
        self._paused = False
        self._pause_timer = QTimer(self)
        self._pause_timer.setSingleShot(True)
        self._pause_timer.timeout.connect(self._resume_scroll)
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._update_offset)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setMinimumHeight(20)
        if text:
            self.setText(text)
    def setText(self, html):
        self._html = html
        self._doc.setHtml(html)
        self._doc.setDefaultFont(self.font())
        self._text_width = self._doc.idealWidth()
        self._offset = 0.0
        self._paused = False
        self._is_scrolling = self._text_width > self.width() and self.width() > 0
        self.update()
    def text(self):
        return self._html
    def setStyleSheet(self, ss):
        super().setStyleSheet(ss)
        if self._html:
            self.setText(self._html)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._is_scrolling = self._text_width > self.width() and self.width() > 0
        if not self._is_scrolling:
            self._offset = 0.0
        self.update()
    def showEvent(self, event):
        super().showEvent(event)
        if self._is_scrolling and not self._scroll_timer.isActive():
            self._scroll_timer.start(30)
        win = self.window()
        if win and not getattr(self, '_window_filter_installed', False):
            win.installEventFilter(self)
            self._window_filter_installed = True
    def eventFilter(self, obj, event):
        if obj == self.window() and event.type() == QEvent.Type.WindowStateChange:
            if self.window().isMinimized():
                if self._scroll_timer.isActive():
                    self._scroll_timer.stop()
            else:
                if self._is_scrolling and not self._scroll_timer.isActive():
                    self._scroll_timer.start(30)
        return super().eventFilter(obj, event)
    def hideEvent(self, event):
        super().hideEvent(event)
        if self._scroll_timer.isActive():
            self._scroll_timer.stop()
    def _update_offset(self):
        window = self.window()
        if window and (window.isMinimized() or window.isHidden()):
            return
        if self._is_scrolling and not self._paused:
            self._offset -= 0.7
            if -self._offset >= self._text_width + self._space:
                self._offset = 0.0
                self._paused = True
                self._pause_timer.start(1500)
            self.update()
    def _resume_scroll(self):
        self._paused = False
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(self.rect())
        self._doc.setDefaultFont(self.font())
        h = self._doc.size().height()
        y_offset = max(0, (self.height() - h) / 2)
        if not self._is_scrolling:
            x_offset = max(0, (self.width() - self._text_width) / 2)
            painter.translate(QPointF(x_offset, y_offset))
            self._doc.drawContents(painter)
        else:
            painter.save()
            painter.translate(QPointF(self._offset, y_offset))
            self._doc.drawContents(painter)
            painter.restore()
            painter.save()
            painter.translate(QPointF(self._offset + self._text_width + self._space, y_offset))
            self._doc.drawContents(painter)
            painter.restore()
        painter.end()
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            h = self._doc.size().height()
            y_offset = max(0, (self.height() - h) / 2)
            if not self._is_scrolling:
                x_offset = max(0, (self.width() - self._text_width) / 2)
                doc_pos = QPointF(event.position().x() - x_offset, event.position().y() - y_offset)
            else:
                doc_pos = QPointF(event.position().x() - self._offset, event.position().y() - y_offset)
            anchor = self._doc.documentLayout().anchorAt(doc_pos)
            if anchor:
                self.linkActivated.emit(anchor)
                return
        super().mousePressEvent(event)
class ScalingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._max_font_size = 48
        self._min_font_size = 14
        self.setWordWrap(False)
        self.setMinimumHeight(40)
    def setMaxFontSize(self, size):
        self._max_font_size = size
        self._adjust_font()
    def setText(self, text):
        super().setText(text)
        self._adjust_font()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_font()
    def _adjust_font(self):
        text = self.text()
        if not text:
            return
        w = self.width()
        if w <= 0:
            return
        font = self.font()
        low = self._min_font_size
        high = self._max_font_size
        best = low
        while low <= high:
            mid = (low + high) // 2
            font.setPixelSize(mid)
            fm = QFontMetrics(font)
            if fm.horizontalAdvance(text) <= w - 10:
                best = mid
                low = mid + 1
            else:
                high = mid - 1
        font.setPixelSize(best)
        self.setFont(font)
class MarqueeLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_offset)
        self.space = 40                                          
        self.text_width = 0
        self.is_scrolling = False
        self._text = text
        self._updating_text = False                                         
    def setText(self, text):
        if self._updating_text: return
        self._text = text
        self._updating_text = True
        fm = self.fontMetrics()
        self.text_width = fm.horizontalAdvance(text)
        self.offset = 0
        if self.text_width > self.width() and self.width() > 0:
            self.is_scrolling = True
            super().setText("")                                   
            if not self.timer.isActive():
                self.timer.start(30)                    
        else:
            self.is_scrolling = False
            super().setText(text)
            if self.timer.isActive():
                self.timer.stop()                           
        self._updating_text = False
        self.update()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setText(self._text) 
    def showEvent(self, event):
        super().showEvent(event)
        if self.is_scrolling and not self.timer.isActive():
            self.timer.start(30)
        win = self.window()
        if win and not getattr(self, '_window_filter_installed', False):
            win.installEventFilter(self)
            self._window_filter_installed = True
    def eventFilter(self, obj, event):
        if obj == self.window() and event.type() == QEvent.Type.WindowStateChange:
            if self.window().isMinimized():
                if self.timer.isActive():
                    self.timer.stop()
            else:
                if self.is_scrolling and not self.timer.isActive():
                    self.timer.start(30)
        return super().eventFilter(obj, event)
    def hideEvent(self, event):
        super().hideEvent(event)
        if self.timer.isActive():
            self.timer.stop()
    def update_offset(self):
        window = self.window()
        if window and (window.isMinimized() or window.isHidden()):
            return
        if self.is_scrolling:
            self.offset -= 1
            if -self.offset >= self.text_width + self.space:
                self.offset = 0
            self.update()
    def paintEvent(self, event):
        if not self.is_scrolling:
            super().paintEvent(event)
        else:
            painter = QPainter(self)
            painter.setPen(self.palette().color(self.foregroundRole()))                       
            fm = self.fontMetrics()
            y = (self.height() + fm.ascent() - fm.descent()) // 2
            painter.drawText(self.offset, y, self._text)
            painter.drawText(self.offset + self.text_width + self.space, y, self._text)
            painter.end()
class MiniPlayerWidget(QWidget):
    clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MiniPlayer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
class AspectRatioLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(500, 500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pixmap = None
        self._old_pixmap = None
        self._fade_opacity = 1.0
        from settings_manager import settings
        self._radius = 0 if settings.get('square_covers', False) else 16
    def update_cover_style(self):
        from settings_manager import settings
        self._radius = 0 if settings.get('square_covers', False) else 16
        self.update()
    @pyqtProperty(float)
    def fade_opacity(self):
        return self._fade_opacity
    @fade_opacity.setter
    def fade_opacity(self, val):
        self._fade_opacity = val
        self.update()
    def setPixmap(self, pixmap):
        is_new_image = (pixmap is not None and not pixmap.isNull() and
                        (self._pixmap is None or self._pixmap.isNull() or
                         pixmap.cacheKey() != self._pixmap.cacheKey()))
        if is_new_image:
            if hasattr(self, '_anim') and self._anim is not None:
                self._anim.stop()
                self._anim.deleteLater()
            self._old_pixmap = self._pixmap
            self._pixmap = pixmap
            self._fade_opacity = 0.0
            self._anim = QPropertyAnimation(self, b"fade_opacity", self)
            self._anim.setDuration(350)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()
        else:
            self._pixmap = pixmap
        self.update()
    def clear(self):
        self._old_pixmap = None
        self._pixmap = None
        self._fade_opacity = 1.0
        self.update()
    def sizeHint(self):
        return QSize(450, 450)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        side = min(self.width(), self.height())
        x_offset = (self.width() - side) / 2.0
        y_offset = float(self.height() - side)
        square_rect = QRectF(x_offset, y_offset, side, side)
        path = QPainterPath()
        path.addRoundedRect(square_rect, self._radius, self._radius)
        painter.setClipPath(path)
        has_painted_something = False
        if self._old_pixmap and not self._old_pixmap.isNull() and self._fade_opacity < 1.0:
            scaled_old = self._old_pixmap.scaled(int(side), int(side), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            img_x_old = x_offset + (side - scaled_old.width()) / 2.0
            img_y_old = y_offset + (side - scaled_old.height()) / 2.0
            painter.setOpacity(1.0)                                           
            painter.drawPixmap(int(img_x_old), int(img_y_old), scaled_old)
            has_painted_something = True
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(int(side), int(side), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            img_x = x_offset + (side - scaled.width()) / 2.0
            img_y = y_offset + (side - scaled.height()) / 2.0
            painter.setOpacity(self._fade_opacity)
            painter.drawPixmap(int(img_x), int(img_y), scaled)
            has_painted_something = True
        if not has_painted_something:
            painter.setOpacity(1.0)
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(square_rect)
        painter.end()
class SquareCoverLabel(QWidget):
    def __init__(self, parent=None, radius=12):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pixmap = None
        self._old_pixmap = None
        self._fade_opacity = 1.0
        self._radius = radius
    @pyqtProperty(float)
    def fade_opacity(self):
        return self._fade_opacity
    @fade_opacity.setter
    def fade_opacity(self, val):
        self._fade_opacity = val
        self.update()
    def setPixmap(self, pixmap):
        is_new_image = (pixmap is not None and not pixmap.isNull() and
                        (self._pixmap is None or self._pixmap.isNull() or
                         pixmap.cacheKey() != self._pixmap.cacheKey()))
        if is_new_image:
            if hasattr(self, '_anim') and self._anim is not None:
                self._anim.stop()
                self._anim.deleteLater()
            self._old_pixmap = self._pixmap
            self._pixmap = pixmap
            self._fade_opacity = 0.0
            self._anim = QPropertyAnimation(self, b"fade_opacity", self)
            self._anim.setDuration(350)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()
        else:
            self._pixmap = pixmap
        self.update()
    def clear(self):
        self._old_pixmap = None
        self._pixmap = None
        self._fade_opacity = 1.0
        self.update()
    def sizeHint(self):
        return QSize(450, 450)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        left_rect = QRectF(0, 0, 10, self.height())
        path.addRect(left_rect)
        painter.setClipPath(path)
        has_painted_something = False
        if self._old_pixmap and not self._old_pixmap.isNull() and self._fade_opacity < 1.0:
            scaled_old = self._old_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x_old = (self.width() - scaled_old.width()) // 2
            y_old = (self.height() - scaled_old.height()) // 2
            painter.setOpacity(1.0)
            painter.drawPixmap(x_old, y_old, scaled_old)
            has_painted_something = True
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.setOpacity(self._fade_opacity)
            painter.drawPixmap(x, y, scaled)
            has_painted_something = True
        if not has_painted_something:
            painter.setOpacity(1.0)
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
        painter.end()
class BannerLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._fade_opacity = 1.0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
    @pyqtProperty(float)
    def fade_opacity(self):
        return self._fade_opacity
    @fade_opacity.setter
    def fade_opacity(self, val):
        self._fade_opacity = val
        self.update()
    def setPixmap(self, pixmap):
        is_new_image = (pixmap is not None and not pixmap.isNull() and
                        (self._pixmap is None or self._pixmap.isNull() or
                         pixmap.cacheKey() != getattr(self, '_original_cache_key', 0)))
        if is_new_image:
            self._original_cache_key = pixmap.cacheKey()
            from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
            from PyQt6.QtGui import QPainter, QPixmap
            scaled = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
            scene = QGraphicsScene()
            item = QGraphicsPixmapItem(scaled)
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(30)
            item.setGraphicsEffect(blur)
            scene.addItem(item)
            blurred_res = QPixmap(scaled.size())
            blurred_res.fill(Qt.GlobalColor.transparent)
            painter = QPainter(blurred_res)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            scene.render(painter)
            painter.end()
            scene.clear()
            scene.deleteLater()
            self._pixmap = blurred_res
        if is_new_image:
            if hasattr(self, '_anim') and self._anim is not None:
                self._anim.stop()
                self._anim.deleteLater()
            self._fade_opacity = 0.0
            self._anim = QPropertyAnimation(self, b"fade_opacity", self)
            self._anim.setDuration(400)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()
        self.update()
    def clear(self):
        self._pixmap = None
        self._fade_opacity = 1.0
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(0, 0, self.width(), self.height()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill)
        path.addRoundedRect(rect, 10, 10)
        path.addRect(QRectF(0.5, 0.5, 10, rect.height()))
        painter.setClipPath(path)
        painter.setBrush(QColor(25, 25, 35))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        if self._pixmap and not self._pixmap.isNull():
            target_size = self.size()
            target_size.setWidth(target_size.width() + 60)
            target_size.setHeight(target_size.height() + 60)
            scaled_pixmap = self._pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.setOpacity(self._fade_opacity)
            painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
from UI.components.custom_animated_tabs import CustomAnimatedTabs
class CustomLibraryTabs(CustomAnimatedTabs):
    def __init__(self, parent=None):
        super().__init__(parent)
        from qfluentwidgets import BodyLabel
        self.lbl_count = BodyLabel("0 canciones")
        self.lbl_count.setStyleSheet("color: #606060; font-size: 12px; padding-right: 4px;")
        self.layout.addWidget(self.lbl_count)