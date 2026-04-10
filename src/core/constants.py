# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  Global Constants, Colors, and Model Configurations
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------

# Categorization of YOLO classes for higher-level UI reporting
CATEGORY_MAP = {
    "Human / Person":      {"person"},
    "Pet / Animal":        {"cat","dog","bird","horse","sheep","cow","elephant",
                            "bear","zebra","giraffe","rabbit","hamster","fish"},
    "Vehicle / Transport": {"bicycle","car","motorcycle","airplane","bus","train",
                            "truck","boat","skateboard","surfboard"},
    "Food / Beverage":     {"banana","apple","sandwich","orange","broccoli","carrot",
                            "hot dog","pizza","donut","cake","cup","wine glass",
                            "bottle","fork","knife","spoon","bowl"},
    "Technology / Screen": {"tv","laptop","mouse","remote","keyboard","cell phone",
                            "microwave","oven","toaster","refrigerator"},
    "Furniture / Indoor":  {"chair","couch","potted plant","bed","dining table",
                            "toilet","sink","clock","vase","scissors",
                            "teddy bear","hair drier","toothbrush","book"},
    "Sports / Recreation": {"frisbee","skis","snowboard","sports ball","kite",
                            "baseball bat","baseball glove","tennis racket"},
    "Bags / Accessories":  {"backpack","umbrella","handbag","tie","suitcase"},
    "Outdoor / Street":    {"traffic light","fire hydrant","stop sign",
                            "parking meter","bench"},
}

CATEGORY_ICONS  = {
    "Human / Person":"👤","Pet / Animal":"🐾","Vehicle / Transport":"🚗",
    "Food / Beverage":"🍕","Technology / Screen":"📱","Furniture / Indoor":"🛋️",
    "Sports / Recreation":"⚽","Bags / Accessories":"👜","Outdoor / Street":"🌆",
}

CATEGORY_COLORS = {
    "Human / Person":      ("#22c55e","#052e16"),
    "Pet / Animal":        ("#f97316","#1c0a00"),
    "Vehicle / Transport": ("#3b82f6","#0a1628"),
    "Food / Beverage":     ("#ec4899","#1a0010"),
    "Technology / Screen": ("#a78bfa","#130a28"),
    "Furniture / Indoor":  ("#f59e0b","#1a1000"),
    "Sports / Recreation": ("#06b6d4","#001a1f"),
    "Bags / Accessories":  ("#84cc16","#0d1a00"),
    "Outdoor / Street":    ("#64748b","#0d1117"),
}

YOLO_MODELS = {
    "YOLO11n-seg (Segment, ~7MB)":   "yolo11n-seg.pt",
    "YOLO11s-seg (Segment, ~23MB)":   "yolo11s-seg.pt",
    "YOLO11m-seg (Segment, ~43MB)":   "yolo11m-seg.pt",
    "YOLO11l-seg (Segment, ~55MB)":   "yolo11l-seg.pt",
    "YOLO11x-seg (Segment, ~120MB)":  "yolo11x-seg.pt",
    "YOLOv8n-seg (Segment, ~7MB)":    "yolov8n-seg.pt",
    "YOLOv8s-seg (Segment, ~24MB)":    "yolov8s-seg.pt",
    "YOLOv8m-seg (Segment, ~55MB)":    "yolov8m-seg.pt",
    "YOLOv8l-seg (Segment, ~95MB)":    "yolov8l-seg.pt",
    "YOLOv8x-seg (Segment, ~140MB)":   "yolov8x-seg.pt",
    "YOLO11n (fastest, ~5MB)":    "yolo11n.pt",
    "YOLO11s (small, ~22MB)":     "yolo11s.pt",
    "YOLO11m (medium, ~39MB)":    "yolo11m.pt",
    "YOLO11l (large, ~49MB)":     "yolo11l.pt",
    "YOLO11x (accurate, ~114MB)": "yolo11x.pt",
    "YOLOv10n (nano, ~6MB)":      "yolov10n.pt",
    "YOLOv10s (small, ~16MB)":    "yolov10s.pt",
    "YOLOv10m (medium, ~32MB)":   "yolov10m.pt",
    "YOLOv10l (large, ~52MB)":    "yolov10l.pt",
    "YOLOv10x (accurate, ~104MB)": "yolov10x.pt",
    "YOLOv9c (compact, ~51MB)":   "yolov9c.pt",
    "YOLOv9e (accurate, ~116MB)":  "yolov9e.pt",
    "YOLOv8n (nano, ~6MB)":       "yolov8n.pt",
    "YOLOv8s (small, ~22MB)":     "yolov8s.pt",
    "YOLOv8m (medium, ~52MB)":    "yolov8m.pt",
    "YOLOv8l (large, ~88MB)":     "yolov8l.pt",
    "YOLOv8x (accurate, ~130MB)":  "yolov8x.pt",
    "RT-DETR-l (Real-time, ~67MB)": "rtdetr-l.pt",
    "RT-DETR-x (Extreme, ~130MB)": "rtdetr-x.pt",
}

# UI Styling Constants (Modern Dark Theme)
STYLE_CONFIG = {
    "BG":      "#060b14",
    "PANEL":   "#080f1e",
    "BORDER":  "#0f1f38",
    "ACCENT":  "#3B82F6",
    "TEXT":    "#e2e8f0",
    "MUTED":   "#334155",
    "DIM":     "#1e3a5f",
}
