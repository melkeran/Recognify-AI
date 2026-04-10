# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  Multi-threaded YOLO / RT-DETR Detection Engine
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------
import cv2
import numpy as np
import urllib.request
from pathlib import Path
from collections import defaultdict, Counter
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from ultralytics.utils.plotting import Annotator, colors

from src.core.constants import CATEGORY_MAP

class YOLOWorker(QThread):
    """
    Background worker for Recognify AI.
    Processes video files or images using YOLO/RT-DETR models.
    """
    progress     = pyqtSignal(int, str)
    frame_ready  = pyqtSignal(int, QImage, list, float)  # idx, qimg, d, ts
    result_ready = pyqtSignal(dict)
    error        = pyqtSignal(str)

    def __init__(self, video_path: str, model_name: str, interval_sec: float, conf_thresh: float = 0.35, 
                 line_width: int = 2, font_size: int = 15, mask_alpha: float = 0.4, font: str = "Arial.ttf"):
        super().__init__()
        self.video_path   = video_path
        self.model_name   = model_name
        self.interval_sec = interval_sec
        self.conf_thresh  = conf_thresh
        self.line_width   = line_width
        self.font_size    = font_size
        self.mask_alpha   = mask_alpha
        self.font         = font
        self._paused      = False
        self._stopped     = False

    def pause(self):  self._paused = True
    def resume(self): self._paused = False
    def stop(self):   self._stopped = True

    def run(self):
        try:
            from ultralytics import YOLO
            
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            model_path = model_dir / self.model_name
            
            if not model_path.exists():
                self.progress.emit(0, f"Initializing Download: {self.model_name}...")
                url = f"https://github.com/ultralytics/assets/releases/download/v8.3.0/{self.model_name}"
                def _rep(bn, bs, ts):
                    if ts > 0:
                        pct = int((bn * bs) / ts * 12)
                        self.progress.emit(pct, f"Downloading Model: {(bn*bs)/(1024*1024):.1f}/{ts/(1024*1024):.1f} MB")
                try:
                    urllib.request.urlretrieve(url, str(model_path), _rep)
                except:
                    self.progress.emit(5, "Downloading via API...")

            self.progress.emit(12, "Loading Model weights...")
            model = YOLO(str(model_path))

            self.progress.emit(14, "Opening media…")
            is_image = Path(self.video_path).suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
            
            cap = None
            if is_image:
                frame = cv2.imread(self.video_path)
                if frame is None:
                    self.error.emit(f"Cannot read image: {self.video_path}")
                    return
                total_frames, fps, duration = 1, 1.0, 1.0
                timestamps = [0.0]
            else:
                cap = cv2.VideoCapture(self.video_path)
                if not cap.isOpened():
                    self.error.emit(f"Cannot open video file: {self.video_path}")
                    return
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                duration = total_frames / fps
                timestamps, t = [], 0.0
                while t <= duration:
                    timestamps.append(round(t, 2))
                    t += self.interval_sec
                if not timestamps: timestamps = [0.0]
            
            n = len(timestamps)
            all_dets, category_counts = [], defaultdict(int)
            category_conf, top_objects, frame_timeline = defaultdict(list), Counter(), []

            for idx, ts in enumerate(timestamps):
                if self._stopped: break
                while self._paused and not self._stopped: self.msleep(100)
                
                if not is_image:
                    pos = int(ts * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, min(pos, total_frames - 1))
                    ret, frame = cap.read()
                    if not ret: continue

                h, w = frame.shape[:2]
                scale = min(1.0, 1280 / max(h, w)) if is_image else min(1.0, 640 / max(h, w))
                if scale < 1.0:
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

                results = model(frame, conf=self.conf_thresh, verbose=False)[0]
                frame_dets = []
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    conf = float(box.conf[0])
                    if conf < self.conf_thresh: continue
                    frame_dets.append({"class": cls_name, "confidence": conf, "frame_idx": idx, "timestamp": ts})
                    top_objects[cls_name] += 1
                    for cat, members in CATEGORY_MAP.items():
                        if cls_name in members:
                            category_conf[cat].append(conf)
                            break

                all_dets.extend(frame_dets)
                frame_cats = set()
                for det in frame_dets:
                    for cat, members in CATEGORY_MAP.items():
                        if det["class"] in members: frame_cats.add(cat)
                for cat in frame_cats: category_counts[cat] += 1

                frame_timeline.append({"timestamp": ts, "detections": frame_dets})
                
                # Use Annotator for granular control (results.plot() doesn't support mask_alpha)
                annotator = Annotator(
                    frame.copy(), 
                    line_width=self.line_width, 
                    font_size=self.font_size, 
                    font=self.font
                )
                
                if results.masks is not None:
                    # Move to CPU and numpy
                    m_data = results.masks.data
                    if hasattr(m_data, "cpu"): m_data = m_data.cpu().numpy()
                    
                    # Resize masks if they don't match frame resolution
                    h, w = frame.shape[:2]
                    if m_data.shape[1] != h or m_data.shape[2] != w:
                        m_data = np.array([cv2.resize(m, (w, h)) for m in m_data])
                    
                    # Convert to boolean for Annotator
                    m_data = m_data > 0.5
                    
                    # Draw masks with custom alpha
                    annotator.masks(
                        m_data,
                        colors=[colors(int(x), True) for x in results.boxes.cls], 
                        alpha=self.mask_alpha
                    )
                
                for box in results.boxes:
                    # Move to CPU numpy for reliable annotation
                    b = box.xyxy[0]
                    if hasattr(b, "cpu"): b = b.cpu().numpy()
                    
                    c = int(box.cls)
                    label = f"{model.names[int(c)]} {float(box.conf):.2f}"
                    annotator.box_label(b, label, color=colors(int(c), True))

                annotated = annotator.result()
                
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format.Format_RGB888).copy()
                self.frame_ready.emit(idx, qimg, frame_dets, ts)
                self.progress.emit(12 + int(78 * (idx+1)/n), f"Processing {idx+1}/{n}...")

            if cap: cap.release()
            
            category_summary = {}
            for cat in CATEGORY_MAP:
                f_seen, confs = category_counts.get(cat, 0), category_conf.get(cat, [])
                present = f_seen > 0
                avg_conf = float(np.mean(confs)) if confs else 0.0
                category_summary[cat] = {
                    "present": present, "confidence": "high" if avg_conf >= 0.7 else "medium" if avg_conf >= 0.5 else "low" if present else "—",
                    "avg_conf": round(avg_conf, 2), "frames": f_seen, "total_frames": n,
                    "conf_history": [round(c, 2) for c in confs],
                }

            primary = max((c for c in category_summary if category_summary[c]["present"]), key=lambda c: category_summary[c]["frames"], default="No detections")

            self.result_ready.emit({
                "categories": category_summary, "primary": primary, "top_objects": top_objects.most_common(12),
                "total_dets": len(all_dets), "duration": round(duration, 1), "frames": n,
                "model": self.model_name, "frame_timeline": frame_timeline, "is_image": is_image
            })

        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
