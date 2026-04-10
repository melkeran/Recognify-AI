# -----------------------------------------------------------------------------
# Project: Recognify AI — Pro Object Recognition
# Module:  Application Launcher & Initialization
# Author:  Mohamed Elkeran
# -----------------------------------------------------------------------------
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase

# Add the project root to sys.path to allow relative imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Try to set a modern font if possible
    # In a real "pro" app, we might bundle Inter or Roboto
    # For now, we'll suggest a system sans-serif
    app.setFont(QFont("Segoe UI", 10))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
