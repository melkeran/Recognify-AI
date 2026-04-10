# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  Custom Interactive UI Components & Widgets
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QScrollArea, QPushButton, QGraphicsDropShadowEffect,
    QFileDialog, QListView
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRect, QSize
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QPen, QBrush, 
    QPainterPath, QCursor, QDragEnterEvent, QDropEvent
)
from pathlib import Path
from src.core.constants import (
    CATEGORY_ICONS, CATEGORY_COLORS, STYLE_CONFIG
)

# Extract style shortcuts
BG = STYLE_CONFIG["BG"]
PANEL = STYLE_CONFIG["PANEL"]
BORDER = STYLE_CONFIG["BORDER"]
ACCENT = STYLE_CONFIG["ACCENT"]
TEXT = STYLE_CONFIG["TEXT"]
MUTED = STYLE_CONFIG["MUTED"]
DIM = STYLE_CONFIG["DIM"]

class ZoomableLabel(QLabel):
    """Integrated label that supports zooming to cursor and panning."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pixmap = None
        self._scale = 1.0
        self._pan_pos = QPointF(0, 0)
        self._last_mouse_pos = QPointF(0, 0)
        self._auto_fit = True
        self.setMouseTracking(True)

    def set_pixmap(self, pix: QPixmap):
        self._pixmap = pix
        self._auto_fit = True
        self.reset_view()

    def reset_view(self):
        self._pan_pos = QPointF(0, 0)
        self._scale = 1.0
        if self._pixmap and not self._pixmap.isNull():
            w, h = self.width(), self.height()
            pw, ph = self._pixmap.width(), self._pixmap.height()
            if pw > 0 and ph > 0:
                self._scale = min(w/pw, h/ph) * 0.95
        self.update()

    def resizeEvent(self, e):
        if self._auto_fit: self.reset_view()
        super().resizeEvent(e)

    def wheelEvent(self, e):
        if not self._pixmap: return
        delta = e.angleDelta().y()
        factor = 1.15 if delta > 0 else 0.85
        self._auto_fit = False
        new_scale = self._scale * factor
        new_scale = max(0.1, min(new_scale, 20.0))
        mpos = e.position()
        center = QPointF(self.rect().center())
        content_pos = (mpos - center - self._pan_pos) / self._scale
        self._scale = new_scale
        self._pan_pos = mpos - center - (content_pos * self._scale)
        self.update()

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.reset_view()
        super().mouseDoubleClickEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._last_mouse_pos = e.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif e.button() == Qt.MouseButton.RightButton:
            self.reset_view()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self._auto_fit = False
            curr_pos = e.position()
            self._pan_pos += curr_pos - self._last_mouse_pos
            self._last_mouse_pos = curr_pos
            self.update()
        super().mouseMoveEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._pixmap:
            p.setPen(QColor(DIM))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "READY")
            return
        p.translate(QPointF(self.rect().center()))
        p.translate(self._pan_pos)
        p.scale(self._scale, self._scale)
        w, h = self._pixmap.width(), self._pixmap.height()
        target = QRect(-w // 2, -h // 2, w, h)
        p.drawPixmap(target, self._pixmap)

class DropZone(QLabel):
    file_dropped = pyqtSignal(str)
    EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._idle()

    def _idle(self):
        self.setText("🎬\n\nDrag & drop a video\nor click to browse\n\n.mp4 · .mov · .avi · .mkv")
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {DIM};
                border-radius: 12px;
                background: {PANEL};
                color: {MUTED};
                font-family: 'Courier New';
                font-size: 12px;
                padding: 20px;
            }}
        """)

    def _hover(self):
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {ACCENT};
                border-radius: 12px;
                background: #0a1f3d;
                color: {ACCENT};
                font-family: 'Courier New';
                font-size: 12px;
                padding: 20px;
            }}
        """)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._hover()

    def dragLeaveEvent(self, e): self._idle()

    def dropEvent(self, e: QDropEvent):
        self._idle()
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).suffix.lower() in self.EXTS:
                self.file_dropped.emit(path)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.mov *.avi *.mkv *.webm *.m4v)")
            if path: self.file_dropped.emit(path)

class FrameThumb(QLabel):
    hovered = pyqtSignal(object, float, list)
    clicked = pyqtSignal(object, float, list)

    def __init__(self, index: int):
        super().__init__()
        self.index = index
        self._pixmap = None
        self._ts = 0.0
        self._dets = []
        self.setFixedSize(112, 70)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMouseTracking(True)
        self._set_empty()

    def _set_empty(self):
        self.setText(f"F{self.index+1}")
        self.setStyleSheet(f"QLabel {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; color: {MUTED}; font-size: 18px; font-family: 'Courier New'; }}")

    def set_data(self, pixmap: QPixmap, ts: float, dets: list):
        self._pixmap, self._ts, self._dets = pixmap, ts, dets
        scaled = pixmap.scaled(112, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled)
        self._update_style()

    def set_filtered(self, matches, active):
        if not active:
            self.setGraphicsEffect(None)
            self._update_style()
        else:
            if matches:
                self.setGraphicsEffect(None)
                self.setStyleSheet(f"QLabel {{ background: #040a14; border: 2px solid #22c55e; border-radius: 8px; }}")
            else:
                from PyQt6.QtWidgets import QGraphicsOpacityEffect
                eff = QGraphicsOpacityEffect(self)
                eff.setOpacity(0.25)
                self.setGraphicsEffect(eff)
                self._update_style(dimmed=True)

    def _update_style(self, dimmed=False):
        if not self._dets:
            self.setStyleSheet(f"QLabel {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; }}")
            return
        det_count = len(self._dets)
        border_col = "#22c55e" if det_count > 3 else ACCENT if det_count > 0 else MUTED
        if dimmed: border_col = BORDER
        self.setStyleSheet(f"QLabel {{ background: #040a14; border: 1px solid {border_col}; border-radius: 8px; }}")

    def enterEvent(self, e):
        if self._pixmap: self.hovered.emit(self._pixmap, self._ts, self._dets)
        super().enterEvent(e)

    def mousePressEvent(self, e):
        if self._pixmap and e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._pixmap, self._ts, self._dets)
        super().mousePressEvent(e)

class FrameViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self._overlay = QWidget(parent)
        self._overlay.setStyleSheet("background: rgba(0,0,0,180);")
        self._overlay.hide()
        self._overlay.installEventFilter(self)
        self._card = QFrame(parent)
        self._card.setStyleSheet(f"QFrame {{ background: #0a1628; border: 1px solid {ACCENT}88; border-radius: 16px; }}")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(59, 130, 246, 120))
        shadow.setOffset(0, 8)
        self._card.setGraphicsEffect(shadow)
        self._card.hide()
        cl = QVBoxLayout(self._card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(12)
        top = QHBoxLayout()
        self._ts_lbl = QLabel()
        self._ts_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 13px; font-weight: 700; font-family: 'Courier New';")
        top.addWidget(self._ts_lbl); top.addStretch()
        cb = QPushButton("✕")
        cb.setFixedSize(28, 28)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setStyleSheet(f"QPushButton {{ background: {BORDER}; color: {TEXT}; border: none; border-radius: 14px; font-size: 13px; }} QPushButton:hover {{ background: #ef444433; color: #ef4444; }}")
        cb.clicked.connect(self.close_viewer)
        top.addWidget(cb); cl.addLayout(top)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet("border-radius: 10px; background: #040a14;")
        cl.addWidget(self._img_lbl, 1)
        self._dets_scroll = QScrollArea()
        self._dets_scroll.setWidgetResizable(True)
        self._dets_scroll.setMaximumHeight(120)
        self._dets_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }} QScrollBar:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }} QScrollBar::handle:horizontal {{ background: {ACCENT}; border-radius: 2px; }}")
        self._dets_inner = QWidget()
        self._dets_row = QHBoxLayout(self._dets_inner)
        self._dets_row.setContentsMargins(0, 0, 0, 0)
        self._dets_row.setSpacing(6)
        self._dets_scroll.setWidget(self._dets_inner)
        cl.addWidget(self._dets_scroll)

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj == self._overlay and event.type() == QEvent.Type.MouseButtonPress: self.close_viewer()
        return super().eventFilter(obj, event)

    def show_frame(self, pixmap, ts, dets):
        parent = self.parent()
        if not parent: return
        pr = parent.rect()
        self._overlay.setGeometry(pr); self._overlay.show(); self._overlay.raise_()
        cw, ch = min(pr.width() - 80, 860), min(pr.height() - 80, 620)
        cx, cy = pr.x() + (pr.width() - cw) // 2, pr.y() + (pr.height() - ch) // 2
        self._card.setGeometry(cx, cy, cw, ch); self._card.show(); self._card.raise_()
        self._ts_lbl.setText(f"⏱ Frame at {ts:.2f}s")
        self._img_lbl.setPixmap(pixmap.scaled(cw-32, ch-160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        while self._dets_row.count():
            w = self._dets_row.takeAt(0).widget()
            if w: w.deleteLater()
        if dets:
            for d in dets:
                conf = d["confidence"]
                c = "#22c55e" if conf > 0.7 else "#f59e0b" if conf > 0.5 else "#ef4444"
                tag = QLabel(f"{d['class']} {conf:.0%}")
                tag.setStyleSheet(f"background: {c}22; color: {c}; border: 1px solid {c}55; border-radius: 6px; padding: 4px 10px; font-family: 'Courier New'; font-size: 12px;")
                self._dets_row.addWidget(tag)
        else:
            e = QLabel("No detections"); e.setStyleSheet(f"color: {MUTED}; font-family: 'Courier New'; font-size: 12px;")
            self._dets_row.addWidget(e)
        self._dets_row.addStretch()

    def close_viewer(self): self._overlay.hide(); self._card.hide()

class ConfidenceChart(QWidget):
    def __init__(self, values, color, total_frames, parent=None):
        super().__init__(parent)
        self.values, self.color, self.total_frames = values, QColor(color), total_frames
        self.setFixedHeight(32); self.setMinimumWidth(80)

    def paintEvent(self, e):
        if not self.values: return
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = max(len(self.values), 1); bar_w = max(4, w / n - 2)
        for i, v in enumerate(self.values):
            bh = int(v * (h-4)) + 4; x = int(i * (w/n)); y = h - bh
            col = QColor(self.color); col.setAlphaF(0.3 + 0.7 * v)
            p.setBrush(QBrush(col)); p.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath(); path.addRoundedRect(x, y, bar_w, bh, 2, 2)
            p.fillPath(path, col)

class TimelineWidget(QWidget):
    frame_clicked = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timeline, self.duration = [], 1; self.setFixedHeight(10); self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_data(self, timeline, duration): self.timeline, self.duration = timeline, max(duration, 1); self.update()

    def paintEvent(self, e):
        if not self.timeline: return
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(BORDER))); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(0, h//2-2, w, 4, 2, 2)
        for entry in self.timeline:
            x = int(entry["timestamp"] / self.duration * w)
            n = len(entry["detections"])
            col = QColor("#22c55e" if n > 3 else ACCENT if n > 0 else MUTED)
            col.setAlphaF(0.9 if n > 0 else 0.3); tick_h = min(6 + n, h)
            p.setBrush(QBrush(col)); p.drawRoundedRect(x-1, (h-tick_h)//2, 3, tick_h, 1, 1)

    def mousePressEvent(self, e):
        if not self.timeline: return
        tr = e.position().x() / max(self.width(), 1) * self.duration
        b = min(range(len(self.timeline)), key=lambda i: abs(self.timeline[i]["timestamp"]-tr))
        self.frame_clicked.emit(b)

class CategoryCard(QFrame):
    filter_requested = pyqtSignal(str)
    def __init__(self, name, data, total_frames):
        super().__init__()
        self.name, self.data, self.total_frames = name, data, total_frames; self._expanded = False
        p = data["present"]; c = data["confidence"]; f = data["frames"]; ac = data["avg_conf"]
        icon = CATEGORY_ICONS.get(name, "●")
        accent, bg = CATEGORY_COLORS.get(name, ("#64748b", "#0d1117"))
        if not p: accent, bg = "#1e293b", "#0a0f1a"
        self.accent, self.bg = accent, bg
        self.setStyleSheet(f"QFrame#cat_outer {{ background: {bg}; border: 1px solid {accent}{'44' if p else '11'}; border-radius: 10px; }} QFrame#cat_outer:hover {{ border-color: {accent}{'99' if p else '22'}; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bg}, stop:1 #0f172a); }}")
        self.setObjectName("cat_outer")
        if p: self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._outer = QVBoxLayout(self); self._outer.setContentsMargins(0, 0, 0, 0); self._outer.setSpacing(0)
        h = QFrame(); h.setFixedHeight(64); hl = QHBoxLayout(h); hl.setContentsMargins(14, 0, 14, 0); hl.setSpacing(10)
        il = QLabel(icon if p else "·"); il.setStyleSheet(f"color: {accent}; font-size: 20px;"); il.setFixedWidth(28); hl.addWidget(il)
        txt = QVBoxLayout(); txt.setSpacing(2); nl = QLabel(name); nl.setStyleSheet(f"color: {TEXT if p else '#1e3a5f'}; font-weight: 700; font-size: 13px;"); txt.addWidget(nl)
        dl = QLabel(f"Seen in {f}/{total_frames} frames" if p else "Not detected"); dl.setStyleSheet(f"color: {'#475569' if p else '#1e3a5f'}; font-size: 11px;"); txt.addWidget(dl); hl.addLayout(txt, 1)
        if p and data.get("conf_history"):
            ch = ConfidenceChart(data["conf_history"], accent, total_frames); hl.addWidget(ch)
        if p and c != "—":
            pc = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(c, "#64748b")
            pill = QLabel(c.upper()); pill.setStyleSheet(f"background: {pc}22; color: {pc}; border: 1px solid {pc}55; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 700;"); pill.setFixedHeight(20); hl.addWidget(pill)
        b_w = 50; bar = QFrame(); bar.setFixedSize(b_w, 5); bar.setStyleSheet(f"background: {BORDER}; border-radius: 2px;"); fill = QFrame(bar); fw = int(b_w * f / max(total_frames, 1)) if p else 0; fill.setGeometry(0, 0, fw, 5); fill.setStyleSheet(f"background: {accent}; border-radius: 2px;"); hl.addWidget(bar)
        if p: self._arrow = QLabel("▸"); self._arrow.setStyleSheet(f"color: {accent}; font-size: 14px;"); self._arrow.setFixedWidth(18); hl.addWidget(self._arrow)
        self._outer.addWidget(h)
        self._detail = QWidget(); self._detail.setVisible(False); dl = QVBoxLayout(self._detail); dl.setContentsMargins(14, 0, 14, 12); dl.setSpacing(6)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet(f"color: {accent}22;"); dl.addWidget(sep)
        if p and data.get("conf_history"):
            hlb = QLabel("Confidence history:"); hlb.setStyleSheet(f"color: {MUTED}; font-size: 11px;"); dl.addWidget(hlb)
            bc = ConfidenceChart(data["conf_history"], accent, total_frames); bc.setFixedHeight(50); dl.addWidget(bc)
            slb = QLabel(f"Avg: {ac:.0%}  ·  Count: {len(data['conf_history'])}"); slb.setStyleSheet(f"color: {accent}; font-size: 11px; font-family: 'Courier New';"); dl.addWidget(slb)
        self._outer.addWidget(self._detail)

    def mousePressEvent(self, e):
        if self.data["present"] and e.button() == Qt.MouseButton.LeftButton:
            self._expanded = not self._expanded; self._detail.setVisible(self._expanded)
            if hasattr(self, "_arrow"): self._arrow.setText("▾" if self._expanded else "▸")
            self.filter_requested.emit(self.name)
        super().mousePressEvent(e)
