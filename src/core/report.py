# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  PDF Report Generator (Dossier Suite v2)
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------
import datetime
import matplotlib.pyplot as plt
from pathlib import Path
from fpdf import FPDF
from src.core.constants import STYLE_CONFIG

class ReportGenerator:
    """
    Generates an ultimate technical dossier with deep analytics, timelines, and an appendix.
    """
    def __init__(self, data: dict, all_thumbnails: list = None):
        self.data = data
        self.thumbs = all_thumbnails or []
        self.date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Style configuration
        self.accent_hex = STYLE_CONFIG["ACCENT"]
        self.accent_rgb = tuple(int(self.accent_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        self.text_dark = (31, 41, 55)
        self.text_muted = (107, 114, 128)
        self.bg_light = (249, 250, 251)
        
    def _generate_bar_chart(self, output_path: str):
        top = self.data.get("top_objects", [])[:10]
        if not top: return None
        names, counts = zip(*top)
        plt.style.use('bmh')
        plt.figure(figsize=(7, 4), facecolor="white")
        plt.barh(names, counts, color=self.accent_hex, alpha=0.9, edgecolor="#1e293b", linewidth=0.5)
        plt.title("DETECTION FREQUENCY BY CLASS", fontsize=11, fontweight="bold", pad=15)
        plt.gca().invert_yaxis(); plt.tight_layout()
        plt.savefig(output_path, dpi=180); plt.close()
        return output_path

    def _generate_timeline_chart(self, output_path: str):
        """Generates a timeline of detections across the media duration."""
        timeline = self.data.get("frame_timeline", [])
        if not timeline: return None
        
        times = [d["timestamp"] for d in timeline]
        counts = [len(d["detections"]) for d in timeline]
        
        plt.figure(figsize=(9, 3.5), facecolor="white")
        plt.plot(times, counts, color=self.accent_hex, linewidth=2, marker='o', markersize=3, alpha=0.8)
        plt.fill_between(times, counts, color=self.accent_hex, alpha=0.1)
        plt.title("RECOGNITION TEMPORAL TIMELINE", fontsize=11, fontweight="bold", pad=12)
        plt.xlabel("TIME (SECONDS)", fontsize=9); plt.ylabel("INSTANCES", fontsize=9)
        plt.grid(True, linestyle="--", alpha=0.4); plt.tight_layout()
        plt.savefig(output_path, dpi=180); plt.close()
        return output_path

    def _generate_donut_chart(self, output_path: str):
        all_confs = []
        for c in self.data["categories"].values(): all_confs.extend(c.get("conf_history", []))
        if not all_confs: return None
        stats = [sum(1 for c in all_confs if c < 0.5), sum(1 for c in all_confs if 0.5 <= c < 0.8), sum(1 for c in all_confs if c >= 0.8)]
        plt.figure(figsize=(5, 4), facecolor="white")
        cmap = ["#f87171", "#fbbf24", "#34d399"]
        plt.pie(stats, labels=[f"LOW", f"MED", f"HIGH"], autopct="%1.0f%%", startangle=140, colors=cmap, wedgeprops={'width': 0.35})
        plt.title("RELIABILITY MATRIX", fontsize=11, fontweight="bold", pad=15)
        plt.tight_layout(); plt.savefig(output_path, dpi=180); plt.close()
        return output_path

    def generate(self, output_path: str):
        t_bar, t_timeline, t_pie = "m_bar.png", "m_time.png", "m_pie.png"
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        
        # --- PRESTIGE HEADER ---
        pdf.set_fill_color(15, 23, 42); pdf.rect(0, 0, 210, 30, "F")
        pdf.set_font("Helvetica", "B", 22); pdf.set_text_color(255, 255, 255)
        pdf.text(12, 16, "RECOGNIFY AI")
        pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*self.accent_rgb)
        pdf.text(12, 23, "FULL ANALYSIS DOSSIER - INDUSTRIAL EDITION")
        
        pdf.set_font("Helvetica", "", 7); pdf.set_text_color(255, 255, 255)
        pdf.set_xy(140, 10); pdf.cell(60, 4, f"SESSION ID: {datetime.datetime.now().strftime('%Y%H%M%S')}", 0, 1, "R")
        pdf.set_x(140); pdf.cell(60, 4, f"TIMESTAMP: {self.date_str}", 0, 1, "R")

        # --- EXECUTIVE SUMMARY GRID ---
        pdf.ln(20)
        pdf.set_fill_color(*self.bg_light); pdf.rect(10, pdf.get_y(), 190, 24, "F")
        pdf.set_draw_color(229, 231, 235); pdf.rect(10, pdf.get_y(), 190, 24)
        
        y = pdf.get_y() + 4
        pdf.set_xy(15, y); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(*self.text_dark); pdf.cell(60, 5, "CORE METRICS", ln=True)
        pdf.set_font("Helvetica", "", 8); pdf.set_x(15); pdf.cell(30, 4, "Object Count:"); pdf.set_font("Helvetica", "B", 9); pdf.cell(0, 4, str(self.data.get('total_dets')), ln=True)
        pdf.set_font("Helvetica", "", 8); pdf.set_x(15); pdf.cell(30, 4, "Source Engine:"); pdf.set_font("Helvetica", "B", 9); pdf.cell(0, 4, self.data.get('model'), ln=True)
        
        pdf.set_xy(90, y); pdf.set_font("Helvetica", "B", 9); pdf.cell(60, 5, "ANALYTICS HEALTH", ln=True)
        all_confs = []
        for v in self.data["categories"].values(): all_confs.extend(v.get("conf_history", []))
        avg = sum(all_confs)/len(all_confs) if all_confs else 0
        pdf.set_xy(90, y + 5); pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(16, 185, 129) if avg > 0.7 else pdf.set_text_color(245, 158, 11)
        pdf.cell(50, 6, f"{int(avg*100)}% RELIABILITY", ln=True)

        # --- PRIMARY EVIDENCE ---
        pdf.ln(15)
        pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(*self.text_dark); pdf.cell(0, 10, "PRIMARY VISUAL EVIDENCE", ln=True)
        if self.thumbs:
            pdf.image(self.thumbs[0], x=10, y=pdf.get_y(), w=115)
            # Three side-thumbs
            for i, s in enumerate(self.thumbs[1:4]):
                pdf.image(s, x=130, y=pdf.get_y() + (i * 22), w=70)
            pdf.ln(70)

        # --- ANALYTICS ROW 1 (Timeline) ---
        time_path = self._generate_timeline_chart(t_timeline)
        if time_path:
            pdf.ln(5); pdf.image(time_path, x=10, w=190); pdf.ln(80)

        # --- ANALYTICS ROW 2 (Frequency + Spread) ---
        pdf.add_page(); pdf.ln(10)
        pdf.set_font("Helvetica", "B", 13); pdf.cell(0, 10, "ADVANCED DATA VISUALIZATION", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
        
        bar_path = self._generate_bar_chart(t_bar)
        if bar_path: pdf.image(bar_path, x=7, y=pdf.get_y(), w=110)
        pie_path = self._generate_donut_chart(t_pie)
        if pie_path: pdf.image(pie_path, x=122, y=pdf.get_y(), w=82)
        pdf.ln(85)
        
        # --- AUDIT TABLE ---
        pdf.set_font("Helvetica", "B", 13); pdf.cell(0, 10, "CLASSIFICATION AUDIT LOG", ln=True)
        pdf.set_fill_color(30, 41, 59); pdf.set_font("Helvetica", "B", 9); pdf.set_text_color(255, 255, 255)
        pdf.cell(60, 9, " CATEGORY", 0, 0, "L", fill=True); pdf.cell(25, 9, " COUNT", 0, 0, "C", fill=True); pdf.cell(25, 9, " AVG CONF", 0, 0, "C", fill=True); pdf.cell(25, 9, " PEAK", 0, 0, "C", fill=True); pdf.cell(55, 9, " STATUS", 0, 1, "C", fill=True)
        pdf.set_font("Helvetica", "", 8); pdf.set_text_color(*self.text_dark); is_alt = False
        for name, data in self.data["categories"].items():
            if data["present"]:
                pdf.set_fill_color(249, 250, 251) if is_alt else pdf.set_fill_color(255, 255, 255)
                pdf.cell(60, 7, f" {name}", "B", 0, "L", fill=True); pdf.cell(25, 7, f"{data['frames']}", "B", 0, "C", fill=True); pdf.cell(25, 7, f"{int(data['avg_conf']*100)}%", "B", 0, "C", fill=True); pdf.cell(25, 7, f"{int(max(data.get('conf_history', [0]))*100)}%", "B", 0, "C", fill=True)
                stat = data["confidence"].upper(); pdf.set_text_color(16, 185, 129) if stat=="HIGH" else pdf.set_text_color(245, 158, 11)
                pdf.cell(55, 7, f"RECOGNIZE_{stat}", "B", 1, "C", fill=True); pdf.set_text_color(*self.text_dark); is_alt = not is_alt

        # --- APPENDIX: COMPACT VISUAL REPOSITORY ---
        if self.thumbs:
            pdf.add_page(); pdf.ln(10)
            pdf.set_font("Helvetica", "B", 18); pdf.set_text_color(*self.text_dark); pdf.cell(0, 10, "APPENDIX A: VISUAL EVIDENCE LOG", ln=True)
            pdf.set_font("Helvetica", "I", 9); pdf.set_text_color(*self.text_muted); pdf.cell(0, 5, "Comprehensive documentation of unique recognition events captured during session.", ln=True)
            pdf.ln(10)
            
            # Grid layout: 4 columns for higher density
            x_start, y_start = 10, pdf.get_y()
            col_w, row_h = 45, 36
            gap = 3
            
            page_idx = 0
            for t in self.thumbs:
                # Manual page break check (leaving space for footer)
                if y_start + ((page_idx // 4) * row_h) > 260:
                    pdf.add_page()
                    y_start = 20
                    page_idx = 0 # Reset item counter for new page
                
                col = page_idx % 4
                row = page_idx // 4
                
                # Image with a subtle grouping border
                ix = x_start + (col * (col_w + gap))
                iy = y_start + (row * row_h)
                pdf.set_draw_color(229, 231, 235); pdf.rect(ix - 0.5, iy - 0.5, col_w + 1, (col_w * 0.75) + 1)
                pdf.image(t, x=ix, y=iy, w=col_w)
                
                page_idx += 1
            
        # --- FOOTER ---
        pdf.set_y(-18); pdf.set_font("Helvetica", "I", 7); pdf.set_text_color(*self.text_muted)
        pdf.cell(0, 10, f"Recognify AI Proprietary Industrial Output  |  Dossier ID: {datetime.datetime.now().strftime('%Y%j%H%M%S')}  |  Page {pdf.page_no()}", 0, 0, "C")
        
        pdf.output(output_path)
        for p in [t_bar, t_timeline, t_pie]:
            if Path(p).exists(): Path(p).unlink()
        return output_path
