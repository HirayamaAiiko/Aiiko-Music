from PyQt6.QtCore import QObject
from PyQt6.QtGui import QShortcut, QKeySequence
from UI.universal_search import SpotlightSearchDialog
class SearchController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.spotlight_dialog = SpotlightSearchDialog(self.main_window, self.main_window)
    def show_spotlight_search(self):
        self.spotlight_dialog.show()
    def center_if_visible(self):
        if self.spotlight_dialog.isVisible():
            self.spotlight_dialog.center_on_parent()
    def apply_spotlight_theme(self, bg_color, border_color):
        sd = self.spotlight_dialog
        if bg_color and border_color:
            sd.container.setStyleSheet(f"""
                QWidget#SpotlightContainer {{
                    background-color: {bg_color};
                    border-radius: 12px;
                    border: 1px solid {border_color};
                }}
            """)
            sd.search_input.setStyleSheet(f"""
                QLineEdit {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 26px; font-weight: 300;
                    border: none; background: {bg_color}; 
                    color: rgba(255, 255, 255, 0.95);
                    padding-left: 10px;
                    border-radius: 8px;
                }}
            """)
            sd.separator.setStyleSheet(f"background-color: {border_color};")
            sd.results_list.setStyleSheet(f"""
                QListWidget {{ 
                    background: transparent; border: none; outline: none; 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 15px;
                }}
                QListWidget::item {{ 
                    padding: 10px 12px; border-radius: 8px; 
                    color: rgba(255, 255, 255, 0.85); margin-bottom: 2px;
                }}
                QListWidget::item:selected, QListWidget::item:hover {{ 
                    background-color: rgba(255, 255, 255, 0.08); color: white;
                }}
            """)
        else:
            sd.container.setStyleSheet("""
                QWidget#SpotlightContainer {
                    background-color: #1C1C1E;
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
            """)
            sd.search_input.setStyleSheet("""
                QLineEdit {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 26px; font-weight: 300;
                    border: none; background: transparent; 
                    color: rgba(255, 255, 255, 0.95);
                    padding-left: 10px;
                }
            """)
            sd.separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
            sd.results_list.setStyleSheet("""
                QListWidget { 
                    background: transparent; border: none; outline: none; 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 15px;
                }
                QListWidget::item { 
                    padding: 10px 12px; border-radius: 8px; 
                    color: rgba(255, 255, 255, 0.85); margin-bottom: 2px;
                }
                QListWidget::item:selected, QListWidget::item:hover { 
                    background-color: rgba(255, 255, 255, 0.08); color: white;
                }
            """)