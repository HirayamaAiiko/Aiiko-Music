from PyQt6.QtCore import Qt, QMimeData, QUrl, QVariantAnimation, QRectF
from PyQt6.QtWidgets import QListView, QApplication, QAbstractItemView
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QPainterPath, QPen
from PyQt6.QtCore import QVariant, QByteArray
class StealthMimeData(QMimeData):
    def __init__(self, internal_mime):
        super().__init__()
        self.internal_mime = internal_mime
    def formats(self):
        return super().formats()
    def hasFormat(self, mimetype: str) -> bool:
        if super().hasFormat(mimetype):
            return True
        if self.internal_mime and self.internal_mime.hasFormat(mimetype):
            return True
        return False
    def retrieveData(self, mimetype: str, preferredType) -> QVariant:
        if self.internal_mime and self.internal_mime.hasFormat(mimetype):
            return QVariant(QByteArray(self.internal_mime.data(mimetype)))
        return super().retrieveData(mimetype, preferredType)
class DraggableTrackListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        from PyQt6.QtCore import QTimer
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._on_drag_timer_timeout)
        self._drag_ready = False
        self._drag_pos = None
        self._drag_progress = 0.0
        self._progress_animation = QVariantAnimation(self)
        self._progress_animation.setDuration(270)                     
        self._progress_animation.setStartValue(0.0)
        self._progress_animation.setEndValue(1.0)
        self._progress_animation.valueChanged.connect(self._on_progress_changed)
        self._animation_delay_timer = QTimer(self)
        self._animation_delay_timer.setSingleShot(True)
        self._animation_delay_timer.timeout.connect(self._start_visual_animation)
    def _on_progress_changed(self, value):
        self._drag_progress = value
        if self._drag_pos is not None:
            self.viewport().update(
                self._drag_pos.x() - 20, 
                self._drag_pos.y() - 20, 
                40, 40
            )
    def _start_visual_animation(self):
        self._drag_progress = 0.0
        self._progress_animation.start()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_ready = False
            self._drag_pos = event.pos()
            self._drag_progress = 0.0
            self._animation_delay_timer.start(80) 
            self._drag_timer.start(350)                                               
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        self._drag_timer.stop()
        self._animation_delay_timer.stop()
        self._progress_animation.stop()
        self._drag_progress = 0.0
        if self._drag_pos is not None:
            self.viewport().update(self._drag_pos.x() - 20, self._drag_pos.y() - 20, 40, 40)
        self._drag_pos = None
        self._drag_ready = False
        super().mouseReleaseEvent(event)
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self._drag_ready:
                if self._drag_pos is not None:
                    if (event.pos() - self._drag_pos).manhattanLength() > QApplication.startDragDistance():
                        self._drag_timer.stop()
                        self._animation_delay_timer.stop()
                        self._progress_animation.stop()
                        self._drag_progress = 0.0
                        self.viewport().update(self._drag_pos.x() - 20, self._drag_pos.y() - 20, 40, 40)
                        self._drag_pos = None
                was_enabled = self.dragEnabled()
                self.setDragEnabled(False)
                super().mouseMoveEvent(event)
                self.setDragEnabled(was_enabled)
                return
            else:
                if self.state() == QAbstractItemView.State.DragSelectingState:
                    self.setState(QAbstractItemView.State.NoState)
                self._animation_delay_timer.stop()
                self._progress_animation.stop()
                self._drag_progress = 0.0
                if self._drag_pos is not None:
                    self.viewport().update(self._drag_pos.x() - 20, self._drag_pos.y() - 20, 40, 40)
                supported_actions = self.model().supportedDragActions() if self.model() else Qt.DropAction.CopyAction
                self.startDrag(supported_actions)
                return
        super().mouseMoveEvent(event)
    def _on_drag_timer_timeout(self):
        self._drag_ready = True
    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drag_progress > 0 and self._drag_progress < 1.0 and self._drag_pos is not None:
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect_size = 28
            rect = QRectF(
                self._drag_pos.x() - rect_size / 2, 
                self._drag_pos.y() - rect_size / 2, 
                rect_size, rect_size
            )
            bg_pen = QPen(QColor(255, 255, 255, 40), 3)
            painter.setPen(bg_pen)
            painter.drawEllipse(rect)
            fg_pen = QPen(QColor(255, 0, 159), 3)
            fg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(fg_pen)
            start_angle = 90 * 16
            span_angle = -int(360 * self._drag_progress * 16)
            painter.drawArc(rect, start_angle, span_angle)
            painter.end()
    def dragEnterEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
        super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
        super().dragMoveEvent(event)
    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
        super().dropEvent(event)
    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        urls = []
        processed_rows = set()
        import os
        for index in indexes:
            if index.row() in processed_rows:
                continue
            processed_rows.add(index.row())
            track = index.data(Qt.ItemDataRole.UserRole)
            if track and hasattr(track, 'filepath'):
                abs_path = os.path.abspath(track.filepath)
                urls.append(QUrl.fromLocalFile(abs_path))
        internal_mime = self.model().mimeData(indexes)
        mimeData = StealthMimeData(internal_mime)
        if urls:
            mimeData.setUrls(urls)
            if mimeData.hasFormat("text/plain"):
                mimeData.removeFormat("text/plain")
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPainterPath
        from PyQt6.QtCore import QRect, QPoint
        import os
        first_track = indexes[0].data(Qt.ItemDataRole.UserRole)
        cover_pixmap = None
        main_window = self.window()
        if hasattr(main_window, 'player') and hasattr(main_window.player, 'image_cache'):
            icon = main_window.player.image_cache.get_cached_icon(first_track, 65)
            if icon and not icon.isNull():
                cover_pixmap = icon.pixmap(65, 65)
        if not cover_pixmap and first_track and hasattr(first_track, 'cover_path') and first_track.cover_path and os.path.exists(first_track.cover_path):
            raw_pix = QPixmap(first_track.cover_path)
            if not raw_pix.isNull():
                scaled = raw_pix.scaled(65, 65, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                cover_pixmap = QPixmap(65, 65)
                cover_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(cover_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 65, 65, 8, 8)
                painter.setClipPath(path)
                x_offset = (65 - scaled.width()) // 2
                y_offset = (65 - scaled.height()) // 2
                painter.drawPixmap(x_offset, y_offset, scaled)
                painter.end()
        if not cover_pixmap:
            icon = indexes[0].data(Qt.ItemDataRole.DecorationRole)
            if icon and not icon.isNull():
                cover_pixmap = icon.pixmap(65, 65)
        if cover_pixmap:
            pixmap = QPixmap(65, 65)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.drawPixmap(0, 0, cover_pixmap)
            if len(urls) > 1:
                painter.setBrush(QColor(255, 0, 159))                  
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(40, -2, 24, 24)
                painter.setPen(Qt.GlobalColor.white)
                font = painter.font()
                font.setPixelSize(12)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(QRect(40, -2, 24, 24), Qt.AlignmentFlag.AlignCenter, str(len(urls)))
            painter.end()
        else:
            if len(indexes) == 1:
                rect = self.visualRect(indexes[0])
                pixmap = self.viewport().grab(rect)
            else:
                pixmap = QPixmap(180, 40)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QColor(45, 45, 50, 230))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(0, 0, 180, 40, 8, 8)
                painter.setPen(Qt.GlobalColor.white)
                painter.drawText(QRect(0, 0, 180, 40), Qt.AlignmentFlag.AlignCenter, f"{len(urls)} canciones")
                painter.end()
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        default_drop_action = Qt.DropAction.CopyAction
        drag.exec(supportedActions | Qt.DropAction.CopyAction, default_drop_action)