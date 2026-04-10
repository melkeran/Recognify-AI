# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  Main Application Window & UI Orchestration
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------
import sys
from pathlib import Path
from collections import defaultdict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QScrollArea, QFrame,
    QGridLayout, QSizePolicy, QComboBox, QFileDialog, QSplitter,
    QDoubleSpinBox, QSlider, QListView
)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QIcon, QCursor, QImage

from src.core.constants import YOLO_MODELS, STYLE_CONFIG, CATEGORY_MAP, CATEGORY_ICONS
from src.core.worker import YOLOWorker
from src.ui.components import (
    ZoomableLabel, FrameThumb, FrameViewer, TimelineWidget, 
    CategoryCard, DropZone
)
from src.core.report import ReportGenerator

# Extract style shortcuts
BG = STYLE_CONFIG["BG"]
PANEL = STYLE_CONFIG["PANEL"]
BORDER = STYLE_CONFIG["BORDER"]
ACCENT = STYLE_CONFIG["ACCENT"]
TEXT = STYLE_CONFIG["TEXT"]
MUTED = STYLE_CONFIG["MUTED"]
DIM = STYLE_CONFIG["DIM"]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recognify AI — Pro Object Recognition")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(f"""
            QMainWindow {{ background: {BG}; }}
            QLabel {{ color: {TEXT}; }}
            QSplitter::handle {{
                background-color: {BORDER};
                border-radius: 4px;
                margin: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: #3B82F6;
            }}
            QSplitter::handle:pressed {{
                background-color: #60A5FA;
            }}
        """)
        
        self._all_thumbs = []
        self._result_data = {}
        self._active_filter = ""
        self._worker = None
        self._last_video_path = None
        
        self._init_ui()
        self._setup_frame_viewer()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Main horizontal splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("mainSplitter")
        self._splitter.setHandleWidth(8)
        root_layout.addWidget(self._splitter)

        # ── LEFT PANEL ──────────────────────────────────────────────────────
        left_widget = QWidget()
        left_widget.setMinimumWidth(280)
        left_widget.setStyleSheet(f"background: {BG};")
        ll = QVBoxLayout(left_widget)
        ll.setContentsMargins(18, 22, 18, 18)
        ll.setSpacing(12)

        logo = QLabel("⬡ Recognify AI")
        logo.setStyleSheet(f"color: {ACCENT}; font-size: 24px; font-weight: 900; font-family: 'Courier New';")
        ll.addWidget(logo)
        sub = QLabel("BY MOHAMED ELKERAN")
        sub.setStyleSheet(f"color: {DIM}; font-size: 10px; letter-spacing: 2px; font-family: 'Courier New';")
        ll.addWidget(sub)

        # Model
        ll.addSpacing(10)
        ll.addWidget(self._hdr_lbl("MODEL"))
        m_row = QHBoxLayout()
        self._model_combo = QComboBox()
        self._model_combo.addItems(YOLO_MODELS.keys())
        self._model_combo.setView(QListView())
        self._model_combo.setStyleSheet(self._combo_style())
        m_row.addWidget(self._model_combo, 1)
        self._remodel_btn = self._make_refresh_btn()
        m_row.addWidget(self._remodel_btn)
        ll.addLayout(m_row)

        # Sample Rate
        ll.addSpacing(10)
        ll.addWidget(self._hdr_lbl("SAMPLE EVERY"))
        sr_row = QHBoxLayout()
        self._interval_slider = QSlider(Qt.Orientation.Horizontal)
        self._interval_slider.setRange(1, 100); self._interval_slider.setValue(10)
        self._interval_slider.setStyleSheet(self._slider_style())
        sr_row.addWidget(self._interval_slider)
        self._interval_lbl = QLabel(f"{self._interval_slider.value()/10.0:.1f} sec")
        self._interval_lbl.setStyleSheet(f"color: {MUTED}; font-size: 18px; font-family: 'Courier New'; min-width: 80px;")
        self._interval_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        sr_row.addWidget(self._interval_lbl)
        self._interval_slider.valueChanged.connect(lambda v: self._interval_lbl.setText(f"{v/10.0:.1f} sec"))
        self._resample_btn = self._make_refresh_btn()
        sr_row.addWidget(self._resample_btn)
        ll.addLayout(sr_row)

        # Confidence
        ll.addSpacing(10)
        ll.addWidget(self._hdr_lbl("MIN CONFIDENCE"))
        cl_row = QHBoxLayout()
        self._conf_slider = QSlider(Qt.Orientation.Horizontal)
        self._conf_slider.setRange(20, 95); self._conf_slider.setValue(35)
        self._conf_slider.setStyleSheet(self._slider_style())
        cl_row.addWidget(self._conf_slider)
        self._conf_val_lbl = QLabel(f"{self._conf_slider.value()}%")
        self._conf_val_lbl.setStyleSheet(f"color: {MUTED}; font-size: 18px; font-family: 'Courier New'; min-width: 60px;")
        self._conf_val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._conf_slider.valueChanged.connect(lambda v: self._conf_val_lbl.setText(f"{v}%"))
        cl_row.addWidget(self._conf_val_lbl)
        self._reconf_btn = self._make_refresh_btn()
        cl_row.addWidget(self._reconf_btn)
        ll.addLayout(cl_row)

        # Visuals Section
        ll.addSpacing(15)
        ll.addWidget(self._hdr_lbl("VISUALS"))
        
        # BBox Thickness
        thick_row = QHBoxLayout()
        t_lbl = QLabel("THICKNESS")
        t_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700;")
        thick_row.addWidget(t_lbl, 1)
        self._thick_slider = QSlider(Qt.Orientation.Horizontal)
        self._thick_slider.setRange(1, 10); self._thick_slider.setValue(2)
        self._thick_slider.setStyleSheet(self._slider_style())
        thick_row.addWidget(self._thick_slider, 2)
        self._thick_val = QLabel(str(self._thick_slider.value()))
        self._thick_val.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-family: 'Courier New'; min-width: 30px;")
        self._thick_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._thick_slider.valueChanged.connect(lambda v: self._thick_val.setText(str(v)))
        thick_row.addWidget(self._thick_val)
        ll.addLayout(thick_row)

        # Alpha (Segmentation)
        alpha_row = QHBoxLayout()
        a_lbl = QLabel("MASK ALPHA")
        a_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700;")
        alpha_row.addWidget(a_lbl, 1)
        self._alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self._alpha_slider.setRange(0, 100); self._alpha_slider.setValue(40)
        self._alpha_slider.setStyleSheet(self._slider_style())
        alpha_row.addWidget(self._alpha_slider, 2)
        self._alpha_val = QLabel(f"{self._alpha_slider.value()}%")
        self._alpha_val.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-family: 'Courier New'; min-width: 45px;")
        self._alpha_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._alpha_slider.valueChanged.connect(lambda v: self._alpha_val.setText(f"{v}%"))
        alpha_row.addWidget(self._alpha_val)
        ll.addLayout(alpha_row)

        # Font Selection
        font_row = QHBoxLayout()
        f_lbl = QLabel("LABEL FONT")
        f_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700;")
        font_row.addWidget(f_lbl, 1)
        self._font_combo = QComboBox()
        self._font_combo.addItems(["Arial.ttf", "CourierNew.ttf", "Verdana.ttf", "Tahoma.ttf"])
        self._font_combo.setStyleSheet(self._combo_style())
        font_row.addWidget(self._font_combo, 2)
        ll.addLayout(font_row)

        # Font Size
        fs_row = QHBoxLayout()
        fsz_lbl = QLabel("FONT SIZE")
        fsz_lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-weight: 700;")
        fs_row.addWidget(fsz_lbl, 1)
        self._fsize_slider = QSlider(Qt.Orientation.Horizontal)
        self._fsize_slider.setRange(5, 50); self._fsize_slider.setValue(15)
        self._fsize_slider.setStyleSheet(self._slider_style())
        fs_row.addWidget(self._fsize_slider, 2)
        self._fsize_val = QLabel(str(self._fsize_slider.value()))
        self._fsize_val.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-family: 'Courier New'; min-width: 30px;")
        self._fsize_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._fsize_slider.valueChanged.connect(lambda v: self._fsize_val.setText(str(v)))
        fs_row.addWidget(self._fsize_val)
        self._revisual_btn = self._make_refresh_btn()
        fs_row.addWidget(self._revisual_btn)
        ll.addLayout(fs_row)

        # Drop zone
        self._drop = DropZone()
        self._drop.file_dropped.connect(self._on_file)
        ll.addWidget(self._drop)

        # Progress & Status
        self._prog = QProgressBar()
        self._prog.setTextVisible(False); self._prog.setFixedHeight(4); self._prog.setVisible(False)
        self._prog.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border-radius: 2px; border: none; }} QProgressBar::chunk {{ background: {ACCENT}; border-radius: 2px; }}")
        ll.addWidget(self._prog)
        
        self._status = QLabel("READY")
        self._status.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-family: 'Courier New'; font-weight: 700;")
        self._status.setWordWrap(True)
        ll.addWidget(self._status)

        # Workers Controls
        self._ctrl_row = QWidget(); self._ctrl_row.setVisible(False)
        chm = QHBoxLayout(self._ctrl_row); chm.setContentsMargins(0,0,0,0); chm.setSpacing(6)
        self._pause_btn = QPushButton("⏸"); self._pause_btn.setFixedSize(44, 36); self._pause_btn.setCheckable(True)
        self._pause_btn.setStyleSheet(f"QPushButton {{ background: {PANEL}; color: {ACCENT}; border: 1px solid {DIM}; border-radius: 6px; }}")
        self._pause_btn.clicked.connect(self._toggle_pause)
        chm.addWidget(self._pause_btn)
        self._stop_btn = QPushButton("⏹"); self._stop_btn.setFixedSize(44, 36)
        self._stop_btn.setStyleSheet(f"QPushButton {{ background: {PANEL}; color: #ef4444; border: 1px solid {DIM}; border-radius: 6px; }}")
        self._stop_btn.clicked.connect(self._stop_analysis)
        chm.addWidget(self._stop_btn); chm.addStretch()
        ll.addWidget(self._ctrl_row)

        # Frames Grid
        ll.addSpacing(10); ll.addWidget(self._hdr_lbl("SAMPLED FRAMES"))
        fs = QScrollArea(); fs.setWidgetResizable(True); fs.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }} QScrollBar:vertical {{ background: {BG}; width: 5px; }} QScrollBar::handle:vertical {{ background: {DIM}; border-radius: 2px; }}")
        self._frames_container = QWidget(); self._frames_grid = QGridLayout(self._frames_container); self._frames_grid.setSpacing(5)
        fs.setWidget(self._frames_container)
        ll.addWidget(fs, 1)

        self._splitter.addWidget(left_widget)

        # ── RIGHT PANEL ─────────────────────────────────────────────────────
        right_widget = QWidget(); right_widget.setMinimumWidth(400); right_widget.setStyleSheet(f"background: {BG};")
        rl = QVBoxLayout(right_widget); rl.setContentsMargins(22, 22, 22, 22); rl.setSpacing(14)
        
        self._right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._right_splitter.setObjectName("rightSplitter")
        self._right_splitter.setHandleWidth(8)
        rl.addWidget(self._right_splitter)

        # Top: Hero
        self._hero_frame = QFrame(); self._hero_frame.setMinimumHeight(280); self._hero_frame.setStyleSheet(f"background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;")
        hl = QVBoxLayout(self._hero_frame); hl.setContentsMargins(0,0,0,0)
        self._hero_img = ZoomableLabel(); hl.addWidget(self._hero_img)
        self._hero_meta = QLabel(); self._hero_meta.setFixedHeight(40); self._hero_meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hero_meta.setStyleSheet(f"background: {BORDER}aa; color: {ACCENT}; font-size: 14px; font-family: 'Courier New';")
        hl.addWidget(self._hero_meta)
        self._right_splitter.addWidget(self._hero_frame)

        # Bottom Results
        lower = QWidget(); lrl = QVBoxLayout(lower); lrl.setContentsMargins(0,0,0,0); lrl.setSpacing(16)
        self._right_splitter.addWidget(lower)

        # Summary
        self._summary = QFrame(); self._summary.setVisible(False); self._summary.setStyleSheet(f"background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;")
        sl = QHBoxLayout(self._summary); sl.setContentsMargins(20, 15, 20, 15)
        sum_l = QVBoxLayout()
        self._sum_primary = QLabel()
        self._sum_primary.setStyleSheet(f"color: {TEXT}; font-size: 24px; font-weight: 800;")
        sum_l.addWidget(self._sum_primary)
        self._sum_desc = QLabel()
        self._sum_desc.setStyleSheet(f"color: {MUTED}; font-size: 11px;")
        sum_l.addWidget(self._sum_desc)
        sl.addLayout(sum_l, 1)
        
        # Export Button
        self._export_btn = QPushButton("PDF REPORT")
        self._export_btn.setFixedSize(120, 36)
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setStyleSheet(f"QPushButton {{ background: {ACCENT}22; color: {ACCENT}; border: 1px solid {ACCENT}44; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 1px; }} QPushButton:hover {{ background: {ACCENT}; color: {BG}; border-color: {ACCENT}; }}")
        self._export_btn.clicked.connect(self._on_export)
        sl.addWidget(self._export_btn)
        sl.addSpacing(10)

        self._sum_dets = QLabel()
        self._sum_dets.setStyleSheet(f"color: {ACCENT}; font-size: 32px; font-weight: 900;")
        sl.addWidget(self._sum_dets)
        lrl.addWidget(self._summary)

        # Timeline
        self._tl_frame = QFrame(); self._tl_frame.setVisible(False); self._tl_frame.setStyleSheet(f"background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        tl_i = QVBoxLayout(self._tl_frame); tl_i.setContentsMargins(12, 10, 12, 10)
        tl_i.addWidget(self._hdr_lbl("DETECTION TIMELINE"))
        self._timeline = TimelineWidget(); self._timeline.frame_clicked.connect(self._jump_to_frame); tl_i.addWidget(self._timeline)
        lrl.addWidget(self._tl_frame)

        # Filters
        self._filter_frame = QFrame(); self._filter_frame.setVisible(False); self._filter_frame.setStyleSheet(f"background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px;")
        fl_i = QVBoxLayout(self._filter_frame); fl_i.setContentsMargins(12, 10, 12, 10)
        fl_i.addWidget(self._hdr_lbl("FILTER BY CLASS"))
        self._filter_scroll = QScrollArea(); self._filter_scroll.setWidgetResizable(True); self._filter_scroll.setFixedHeight(50); self._filter_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._filter_row_w = QWidget(); self._filter_row = QHBoxLayout(self._filter_row_w); self._filter_row.setContentsMargins(0,0,0,0)
        self._filter_scroll.setWidget(self._filter_row_w); fl_i.addWidget(self._filter_scroll)
        lrl.addWidget(self._filter_frame)

        # Categories
        cs = QScrollArea(); cs.setWidgetResizable(True); cs.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }} QScrollBar:vertical {{ background: {BG}; width: 6px; }} QScrollBar::handle:vertical {{ background: {DIM}; border-radius: 3px; }}")
        self._cats_w = QWidget(); self._cats_l = QVBoxLayout(self._cats_w); self._cats_l.setSpacing(8); self._cats_l.setContentsMargins(0,0,0,0)
        cs.setWidget(self._cats_w); lrl.addWidget(cs, 1)

        self._splitter.addWidget(right_widget)
        self._splitter.setSizes([340, 760]); self._right_splitter.setSizes([340, 420])
        
        # Explicitly enable mouse tracking for handles to ensure hover triggers immediately
        h1 = self._splitter.handle(1)
        if h1: 
            h1.setMouseTracking(True)
            h1.setAttribute(Qt.WidgetAttribute.WA_Hover) # Force hover events
            
        h2 = self._right_splitter.handle(1)
        if h2: 
            h2.setMouseTracking(True)
            h2.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def _hdr_lbl(self, text):
        l = QLabel(text); l.setStyleSheet(f"color: {DIM}; font-size: 11px; font-weight: 700; letter-spacing: 2px;")
        return l

    def _combo_style(self):
        return f"QComboBox {{ background: {PANEL}; color: {TEXT}; border: 1px solid {DIM}; border-radius: 8px; padding: 7px 12px; font-family: 'Courier New'; }} QComboBox::drop-down {{ border: none; }} QComboBox QAbstractItemView {{ background: {PANEL}; color: {TEXT}; border: 1px solid {DIM}; selection-background-color: {ACCENT}; }}"

    def _slider_style(self):
        return f"QSlider::groove:horizontal {{ background: {BORDER}; height: 8px; border-radius: 4px; }} QSlider::handle:horizontal {{ background: {ACCENT}; width: 22px; height: 22px; margin: -7px 0; border-radius: 11px; }}"

    def _make_refresh_btn(self):
        btn = QPushButton("↺")
        btn.setFixedSize(44, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background: {BORDER}; color: {ACCENT}; border: 1px solid {DIM}; border-radius: 6px; font-size: 18px; font-weight: 700; }} QPushButton:hover {{ background: {PANEL}; border-color: {ACCENT}; color: {TEXT}; }} QPushButton:disabled {{ background: {PANEL}; color: {DIM}aa; border-color: {DIM}aa; }}")
        btn.setEnabled(False)
        btn.clicked.connect(self._reanalyze)
        return btn

    def _set_refresh_enabled(self, enabled):
        self._remodel_btn.setEnabled(enabled)
        self._resample_btn.setEnabled(enabled)
        self._reconf_btn.setEnabled(enabled)
        self._revisual_btn.setEnabled(enabled)

    def _reanalyze(self):
        if self._last_video_path:
            self._on_file(self._last_video_path)

    def _setup_frame_viewer(self):
        self._frame_viewer = FrameViewer(self)

    def _on_file(self, path):
        self._last_video_path = path
        self._status.setText("INITIALIZING PIPELINE...")
        self._prog.setVisible(True); self._prog.setValue(0); self._ctrl_row.setVisible(True)
        self._set_refresh_enabled(False)
        self._clear_ui()
        
        model_file = YOLO_MODELS[self._model_combo.currentText()]
        interval = self._interval_slider.value() / 10.0
        conf_t = self._conf_slider.value() / 100.0
        thick = self._thick_slider.value()
        alpha = self._alpha_slider.value() / 100.0
        font = self._font_combo.currentText()
        fsize = self._fsize_slider.value()
        
        self._worker = YOLOWorker(path, model_file, interval, conf_t, 
                                  line_width=thick, font_size=fsize, 
                                  mask_alpha=alpha, font=font)
        self._worker.progress.connect(self._on_progress)
        self._worker.frame_ready.connect(self._on_frame)
        self._worker.result_ready.connect(self._on_results)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, val, msg):
        self._prog.setValue(val); self._status.setText(msg.upper())

    def _on_frame(self, idx, qimg, dets, ts):
        pix = QPixmap.fromImage(qimg)
        if idx == 0: 
            self._on_thumb_hover(pix, ts, dets)
        
        t = FrameThumb(idx); t.set_data(pix, ts, dets)
        t.hovered.connect(self._on_thumb_hover); t.clicked.connect(self._on_thumb_click)
        cols = 3; self._frames_grid.addWidget(t, idx // cols, idx % cols)
        self._all_thumbs.append(t)

    def _on_thumb_hover(self, pix, ts, dets):
        self._hero_img.set_pixmap(pix)
        self._hero_meta.setText(f"⏱ {ts:.2f}s  ·  {len(dets)} detections")

    def _on_thumb_click(self, pix, ts, dets):
        self._on_thumb_hover(pix, ts, dets)
        self._frame_viewer.show_frame(pix, ts, dets)

    def _jump_to_frame(self, idx):
        if idx < len(self._all_thumbs):
            t = self._all_thumbs[idx]
            self._on_thumb_click(t._pixmap, t._ts, t._dets)

    def _on_results(self, data):
        self._result_data = data
        self._prog.hide(); self._ctrl_row.hide()
        self._set_refresh_enabled(True)
        is_img = data.get("is_image", False)
        
        self._status.setText(f"✓ {data['total_dets']} OBJECTS DETECTED" if is_img else f"✓ {data['total_dets']} DETECTIONS COMPLET")
        
        # Adjust layout for image vs video
        self._tl_frame.setVisible(not is_img)
        self._frames_container.parent().parent().setVisible(not is_img) # Hide frames grid for image
        
        # Summary
        p = data["primary"]
        self._sum_primary.setText(f"{CATEGORY_ICONS.get(p, '●')}  {p}")
        self._sum_desc.setText("Image analyzed" if is_img else f"{data['frames']} frames sampled  ·  {data['duration']}s duration")
        self._sum_dets.setText(str(data["total_dets"])); self._summary.setVisible(True)
        
        # Timeline
        if not is_img:
            self._timeline.set_data(data["frame_timeline"], data["duration"])
        
        # Filters
        self._build_filter_tags(data["top_objects"]); self._filter_frame.setVisible(True)
        
        # Cards
        self._rebuild_cats()

    def _build_filter_tags(self, top):
        while self._filter_row.count():
            w = self._filter_row.takeAt(0).widget()
            if w: w.deleteLater()
            
        from PyQt6.QtWidgets import QButtonGroup
        self._filter_group = QButtonGroup(self)
        self._filter_group.setExclusive(True)

        # "All" button
        all_btn = self._make_filter_btn("All", "")
        all_btn.setChecked(True)
        self._filter_row.addWidget(all_btn)
        self._filter_group.addButton(all_btn)

        for name, count in top:
            btn = self._make_filter_btn(name, count)
            self._filter_row.addWidget(btn)
            self._filter_group.addButton(btn)
        
        self._filter_row.addStretch()

    def _make_filter_btn(self, name, count):
        btn = QPushButton(f"{name} {count}" if count else name)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.setStyleSheet(f"QPushButton {{ background: {PANEL}; color: {MUTED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 2px 12px; font-size: 11px; font-family: 'Courier New'; }} QPushButton:checked {{ background: {ACCENT}22; color: {ACCENT}; border-color: {ACCENT}77; font-weight: 700; }} QPushButton:hover {{ border-color: {ACCENT}44; color: {TEXT}; }}")
        btn.clicked.connect(lambda: self._filter_by(name if name != "All" else ""))
        return btn

    def _filter_by(self, name):
        self._active_filter = name
        
        # Sync filter buttons if they exist
        if hasattr(self, "_filter_group"):
            for btn in self._filter_group.buttons():
                # Compare without count suffix
                btn_name = btn.text().split(" ")[0]
                if (name == "" and btn_name == "All") or btn_name == name:
                    btn.blockSignals(True)
                    btn.setChecked(True)
                    btn.blockSignals(False)
                else:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)

        for t in self._all_thumbs:
            if not name:
                t.set_filtered(True, False)
            else:
                matches = any(d["class"] == name for d in t._dets)
                t.set_filtered(matches, True)

    def _rebuild_cats(self):
        while self._cats_l.count():
            w = self._cats_l.takeAt(0).widget()
            if w: w.deleteLater()
        
        for name, data in self._result_data["categories"].items():
            if data["present"]:
                card = CategoryCard(name, data, self._result_data["frames"])
                card.filter_requested.connect(self._filter_by)
                self._cats_l.addWidget(card)
        self._cats_l.addStretch()

    def _clear_ui(self):
        while self._frames_grid.count():
            w = self._frames_grid.takeAt(0).widget()
            if w: w.deleteLater()
        self._all_thumbs = []
        self._summary.hide(); self._tl_frame.hide(); self._filter_frame.hide()
        self._frames_container.parent().parent().setVisible(True) # Ensure visible for next run
        while self._cats_l.count():
            w = self._cats_l.takeAt(0).widget()
            if w: w.deleteLater()

    def _toggle_pause(self, checked):
        if self._worker:
            if checked: self._worker.pause(); self._pause_btn.setText("▶")
            else: self._worker.resume(); self._pause_btn.setText("⏸")

    def _stop_analysis(self):
        if self._worker: self._worker.stop(); self._ctrl_row.hide(); self._status.setText("STOPPED")

    def _on_export(self):
        if not self._result_data: return
        
        default_name = f"RecognifyAI_{Path(self._last_video_path).stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", default_name, "PDF Files (*.pdf)")
        
        if path:
            temp_dir = Path("temp_report")
            temp_dir.mkdir(exist_ok=True)
            
            highlight_paths = []
            try:
                # 1. Save Main Hero
                hero_path = temp_dir / "hero.jpg"
                pix = self._hero_img.pixmap()
                if pix and not pix.isNull():
                    pix.save(str(hero_path), "JPG")
                    highlight_paths.append(str(hero_path))
                
                # 2. Save ALL thumbnails for the appendix
                # Sorted by confidence/detection count
                sorted_thumbs = sorted(self._all_thumbs, key=lambda t: len(t._dets), reverse=True)
                all_thumb_paths = []
                for i, thumb in enumerate(sorted_thumbs):
                    t_path = temp_dir / f"appendix_{i}.jpg"
                    thumb._pixmap.save(str(t_path), "JPG")
                    all_thumb_paths.append(str(t_path))

                gen = ReportGenerator(self._result_data, all_thumb_paths)
                gen.generate(path)
                self._status.setText(f"✓ FULL DOSSIER EXPORTED: {Path(path).name}")
                
                import os
                os.startfile(path)
            except Exception as e:
                self._on_error(f"Export failed: {str(e)}")
            finally:
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

    def _on_error(self, err):
        self._status.setText(f"ERROR: {err}"); self._prog.hide(); self._ctrl_row.hide()
        self._set_refresh_enabled(True)
import datetime
