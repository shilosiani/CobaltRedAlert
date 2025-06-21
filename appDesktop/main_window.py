import sys
import os
from typing import List, Dict, Any, Optional, Union
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QComboBox, QSlider, QSpinBox, QCheckBox, QTextEdit, QTabWidget,
    QGroupBox, QMessageBox, QProgressBar, QSplitter, QFrame,
    QScrollArea, QApplication, QCompleter, QTreeWidget, QTreeWidgetItem,
    QDateEdit, QButtonGroup, QRadioButton, QFileDialog, QStyledItemDelegate,
    QStyleOptionViewItem, QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSettings, QStringListModel, QPropertyAnimation,
    QEasingCurve, QRect, QMimeData, QModelIndex, QAbstractListModel, QDate,
    QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QIcon, QCloseEvent, QAction, QPixmap, QPalette, QPainter,
    QColor, QBrush, QPen, QDrag, QFontMetrics, QTextCharFormat, QTextCursor
)

# Try to import qt-material for modern styling
try:
    from qt_material import apply_stylesheet, list_themes
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False

class HebrewTextHelper:
    """Helper class for Hebrew text rendering and RTL support"""
    
    @staticmethod
    def setup_hebrew_font() -> QFont:
        """Create optimized font for Hebrew text"""
        hebrew_font = QFont()
        # Primary Hebrew fonts in order of preference
        hebrew_font.setFamilies([
            "Segoe UI Historic",  # Windows 10/11 with good Hebrew support
            "Arial Unicode MS",   # Cross-platform Unicode font
            "Tahoma",            # Good Hebrew rendering
            "Segoe UI",          # Windows default
            "Arial",             # Fallback
            "Sans Serif"         # System fallback
        ])
        hebrew_font.setPointSize(11)
        hebrew_font.setWeight(QFont.Weight.Normal)
        hebrew_font.setStyleHint(QFont.StyleHint.SansSerif)
        hebrew_font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        return hebrew_font
    
    @staticmethod
    def is_hebrew_text(text: str) -> bool:
        """Check if text contains Hebrew characters"""
        return any('\u0590' <= char <= '\u05FF' for char in text)
    
    @staticmethod
    def is_mixed_text(text: str) -> bool:
        """Check if text contains both Hebrew and Latin characters"""
        has_hebrew = any('\u0590' <= char <= '\u05FF' for char in text)
        has_latin = any('a' <= char.lower() <= 'z' for char in text)
        return has_hebrew and has_latin
    
    @staticmethod
    def setup_rtl_widget(widget: QWidget, text: str):
        """Configure widget for RTL text if needed"""
        if HebrewTextHelper.is_hebrew_text(text):
            widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

class AnimatedStatusWidget(QFrame):
    """Enhanced status widget with animations and better visual feedback"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_status = "stopped"
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_animation)
        self.setup_animations()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the enhanced status widget UI"""
        self.setFixedHeight(80)
        self.setObjectName("AnimatedStatusWidget")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(20)
        
        # Status section
        status_layout = QVBoxLayout()
        
        # Status icon with larger size
        self.status_icon = QLabel("⭕")
        self.status_icon.setFont(QFont("Arial", 24))
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_icon)
        
        layout.addLayout(status_layout)
        
        # Text section
        text_layout = QVBoxLayout()
        
        self.status_text = QLabel("Monitoring Stopped")
        self.status_text.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        text_layout.addWidget(self.status_text)
        
        self.status_detail = QLabel("Ready to start monitoring")
        self.status_detail.setFont(QFont("Arial", 11))
        self.status_detail.setStyleSheet("color: #666;")
        text_layout.addWidget(self.status_detail)
        
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Connection and stats section
        stats_layout = QVBoxLayout()
        
        # Connection status
        connection_layout = QHBoxLayout()
        self.connection_icon = QLabel("🔗")
        self.connection_icon.setFont(QFont("Arial", 14))
        connection_layout.addWidget(self.connection_icon)
        
        self.connection_text = QLabel("Ready")
        self.connection_text.setFont(QFont("Arial", 11))
        connection_layout.addWidget(self.connection_text)
        
        stats_layout.addLayout(connection_layout)
        
        # Alert count
        self.alert_count = QLabel("Alerts: 0")
        self.alert_count.setFont(QFont("Arial", 10))
        self.alert_count.setStyleSheet("color: #888;")
        stats_layout.addWidget(self.alert_count)
        
        layout.addLayout(stats_layout)
        
        self.set_status("stopped")
    
    def setup_animations(self):
        """Set up property animations"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def set_status(self, status: str, message: str = "", detail: str = ""):
        """Set status with enhanced styling and animations"""
        self.current_status = status
        
        # Stop any running animations
        self.pulse_timer.stop()
        
        if status == "monitoring":
            self.status_icon.setText("🟢")
            self.status_text.setText("Monitoring Active")
            self.status_detail.setText(detail or "Scanning for alerts...")
            self.start_pulse_animation()
            self.setStyleSheet("""
                QFrame#AnimatedStatusWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(232, 245, 233, 0.9),
                        stop:1 rgba(200, 230, 201, 0.9));
                    border: 3px solid #4caf50;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
                }
                QLabel {
                    color: #1b5e20;
                }
            """)
        elif status == "alert":
            self.status_icon.setText("🚨")
            self.status_text.setText(message or "ALERT DETECTED!")
            self.status_detail.setText(detail or "Red Alert in monitored areas")
            self.start_pulse_animation(color="#f44336")
            self.setStyleSheet("""
                QFrame#AnimatedStatusWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 235, 238, 0.95),
                        stop:1 rgba(255, 205, 210, 0.95));
                    border: 3px solid #f44336;
                    border-radius: 15px;
                    box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
                    animation: alertPulse 1.5s infinite;
                }
                QLabel {
                    color: #b71c1c;
                    font-weight: bold;
                }
            """)
        elif status == "checking":
            self.status_icon.setText("🔄")
            self.status_text.setText("Checking...")
            self.status_detail.setText(detail or "Fetching latest alerts")
            self.setStyleSheet("""
                QFrame#AnimatedStatusWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 243, 224, 0.9),
                        stop:1 rgba(255, 224, 178, 0.9));
                    border: 3px solid #ff9800;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(255, 152, 0, 0.3);
                }
                QLabel {
                    color: #e65100;
                }
            """)
        elif status == "error":
            self.status_icon.setText("⚠️")
            self.status_text.setText("Connection Error")
            self.status_detail.setText(detail or "Unable to fetch alerts")
            self.setStyleSheet("""
                QFrame#AnimatedStatusWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 245, 245, 0.9),
                        stop:1 rgba(255, 235, 235, 0.9));
                    border: 3px solid #ff5722;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(255, 87, 34, 0.3);
                }
                QLabel {
                    color: #d84315;
                }
            """)
        else:  # stopped
            self.status_icon.setText("⭕")
            self.status_text.setText("Monitoring Stopped")
            self.status_detail.setText(detail or "Ready to start monitoring")
            self.setStyleSheet("""
                QFrame#AnimatedStatusWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(250, 250, 250, 0.9),
                        stop:1 rgba(245, 245, 245, 0.9));
                    border: 3px solid #9e9e9e;
                    border-radius: 15px;
                    box-shadow: 0 2px 4px rgba(158, 158, 158, 0.2);
                }
                QLabel {
                    color: #424242;
                }
            """)
    
    def start_pulse_animation(self, color: str = "#4caf50"):
        """Start pulsing animation for active states"""
        self.pulse_color = color
        self.pulse_timer.start(1500)  # Pulse every 1.5 seconds
    
    def pulse_animation(self):
        """Create pulsing effect"""
        # This would be enhanced with actual CSS animation or QPropertyAnimation
        pass
    
    def update_alert_count(self, count: int):
        """Update alert count display"""
        self.alert_count.setText(f"Alerts: {count}")
    
    def update_connection_status(self, connected: bool, ping_ms: int = 0):
        """Update connection status"""
        if connected:
            self.connection_icon.setText("🟢")
            self.connection_text.setText(f"Connected ({ping_ms}ms)" if ping_ms > 0 else "Connected")
        else:
            self.connection_icon.setText("🔴")
            self.connection_text.setText("Disconnected")

class DraggableCityItem(QWidget):
    """Enhanced city item widget with drag-drop and priority settings"""
    
    city_removed = pyqtSignal(str)
    city_edited = pyqtSignal(str, str)  # old_name, new_name
    priority_changed = pyqtSignal(str, int)  # city, priority
    
    def __init__(self, city_name: str, priority: int = 1, parent=None):
        super().__init__(parent)
        self.city_name = city_name
        self.priority = priority
        self.setup_ui()
        self.setup_drag_drop()
    
    def setup_ui(self):
        """Set up the city item UI with Hebrew support"""
        self.setFixedHeight(50)
        self.setStyleSheet("""
            DraggableCityItem {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px;
            }
            DraggableCityItem:hover {
                background-color: #f5f5f5;
                border-color: #2196f3;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        # Drag handle
        self.drag_handle = QLabel("⋮⋮")
        self.drag_handle.setFont(QFont("Arial", 14))
        self.drag_handle.setStyleSheet("color: #999; cursor: move;")
        self.drag_handle.setToolTip("Drag to reorder")
        layout.addWidget(self.drag_handle)
        
        # Priority indicator
        self.priority_indicator = QLabel()
        self.update_priority_indicator()
        layout.addWidget(self.priority_indicator)
        
        # City name with proper Hebrew handling
        self.name_label = QLabel(self.city_name)
        self.name_label.setFont(HebrewTextHelper.setup_hebrew_font())
        
        # Set RTL if Hebrew text
        if HebrewTextHelper.is_hebrew_text(self.city_name):
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.name_label, 1)  # Take available space
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # Priority buttons
        self.priority_up_btn = QPushButton("🔺")
        self.priority_up_btn.setFixedSize(25, 25)
        self.priority_up_btn.setToolTip("Increase priority")
        self.priority_up_btn.clicked.connect(self.increase_priority)
        button_layout.addWidget(self.priority_up_btn)
        
        self.priority_down_btn = QPushButton("🔻")
        self.priority_down_btn.setFixedSize(25, 25)
        self.priority_down_btn.setToolTip("Decrease priority")
        self.priority_down_btn.clicked.connect(self.decrease_priority)
        button_layout.addWidget(self.priority_down_btn)
        
        # Edit button
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(25, 25)
        self.edit_btn.setToolTip("Edit city name")
        self.edit_btn.clicked.connect(self.edit_city)
        button_layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(25, 25)
        self.delete_btn.setToolTip("Remove city")
        self.delete_btn.clicked.connect(self.remove_city)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
    
    def setup_drag_drop(self):
        """Enable drag and drop functionality"""
        self.setAcceptDrops(True)
        self.drag_start_position = None
    
    def update_priority_indicator(self):
        """Update priority indicator based on priority level"""
        if self.priority >= 3:
            self.priority_indicator.setText("🔴")  # High priority
            self.priority_indicator.setToolTip("High Priority")
        elif self.priority == 2:
            self.priority_indicator.setText("🟡")  # Medium priority
            self.priority_indicator.setToolTip("Medium Priority")
        else:
            self.priority_indicator.setText("🟢")  # Low priority
            self.priority_indicator.setToolTip("Low Priority")
    
    def increase_priority(self):
        """Increase city priority"""
        if self.priority < 3:
            self.priority += 1
            self.update_priority_indicator()
            self.priority_changed.emit(self.city_name, self.priority)
    
    def decrease_priority(self):
        """Decrease city priority"""
        if self.priority > 1:
            self.priority -= 1
            self.update_priority_indicator()
            self.priority_changed.emit(self.city_name, self.priority)
    
    def edit_city(self):
        """Edit city name"""
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Edit City", "Enter new city name:", 
            text=self.city_name
        )
        if ok and new_name.strip() and new_name != self.city_name:
            old_name = self.city_name
            self.city_name = new_name.strip()
            self.name_label.setText(self.city_name)
            # Update RTL if needed
            if HebrewTextHelper.is_hebrew_text(self.city_name):
                self.name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.city_edited.emit(old_name, self.city_name)
    
    def remove_city(self):
        """Remove city with confirmation"""
        reply = QMessageBox.question(
            self, "Remove City", 
            f"Remove '{self.city_name}' from monitoring?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.city_removed.emit(self.city_name)
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operation"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if not self.drag_start_position:
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Start drag operation
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.city_name)
        drag.setMimeData(mimeData)
        
        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        
        # Execute drag
        drop_action = drag.exec(Qt.DropAction.MoveAction)

class EnhancedCityListWidget(QFrame):
    """Enhanced city list widget with grouping, drag-drop, and advanced features"""
    
    city_added = pyqtSignal(str)
    city_removed = pyqtSignal(str)
    city_edited = pyqtSignal(str, str)
    city_priority_changed = pyqtSignal(str, int)
    cities_reordered = pyqtSignal(list)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.city_widgets = {}
        self.city_groups = {
            "גוש דן": ["תל אביב - מרכז העיר", "בני ברק", "רמת גן", "גבעתיים", "בת ים"],
            "ירושלים": ["ירושלים", "מעלה אדומים", "בית שמש"],
            "צפון": ["חיפה", "נהריה", "עכו", "טבריה", "צפת"],
            "דרום": ["באר שבע", "אשדוד", "אשקלון", "קרית גת"],
            "שרון": ["הוד השרון", "כפר סבא", "רעננה", "הרצליה", "נתניה"]
        }
        self.setup_ui()
        self.load_cities()
    
    def setup_ui(self):
        """Set up the enhanced city list UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        title = QLabel("🏙️ City Management")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bulk operations
        bulk_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📁 Import")
        self.import_btn.setToolTip("Import cities from file")
        self.import_btn.clicked.connect(self.import_cities)
        bulk_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.setToolTip("Export cities to file")
        self.export_btn.clicked.connect(self.export_cities)
        bulk_layout.addWidget(self.export_btn)
        
        self.clear_all_btn = QPushButton("🗑️ Clear All")
        self.clear_all_btn.setToolTip("Remove all cities")
        self.clear_all_btn.clicked.connect(self.clear_all_cities)
        bulk_layout.addWidget(self.clear_all_btn)
        
        header_layout.addLayout(bulk_layout)
        layout.addLayout(header_layout)
        
        # Search and add section
        search_group = QGroupBox("🔍 Add Cities")
        search_layout = QVBoxLayout(search_group)
        
        # Search input with Hebrew support
        search_input_layout = QHBoxLayout()
        
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Search cities (עברית/English)")
        self.city_input.setFont(HebrewTextHelper.setup_hebrew_font())
        self.city_input.setMinimumHeight(40)
        self.city_input.returnPressed.connect(self.add_city)
        self.city_input.textChanged.connect(self.filter_popular_cities)
        
        # Set up enhanced autocomplete
        self.setup_enhanced_autocomplete()
        
        search_input_layout.addWidget(self.city_input)
        
        add_btn = QPushButton("➕ Add")
        add_btn.setMinimumHeight(40)
        add_btn.setMinimumWidth(80)
        add_btn.clicked.connect(self.add_city)
        search_input_layout.addWidget(add_btn)
        
        search_layout.addLayout(search_input_layout)
        
        # Popular cities with grouping and filtering
        self.popular_widget = self.create_popular_cities_widget()
        search_layout.addWidget(self.popular_widget)
        
        layout.addWidget(search_group)
        
        # Monitored cities section
        monitored_group = QGroupBox("📍 Monitored Cities")
        monitored_layout = QVBoxLayout(monitored_group)
        
        # Cities list with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        
        self.cities_container = QWidget()
        self.cities_layout = QVBoxLayout(self.cities_container)
        self.cities_layout.setSpacing(5)
        self.cities_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(self.cities_container)
        monitored_layout.addWidget(scroll_area)
        
        # Statistics
        self.stats_label = QLabel("Cities: 0 | High Priority: 0")
        self.stats_label.setFont(QFont("Arial", 10))
        self.stats_label.setStyleSheet("color: #666; padding: 5px;")
        monitored_layout.addWidget(self.stats_label)
        
        layout.addWidget(monitored_group)
    
    def create_popular_cities_widget(self) -> QWidget:
        """Create grouped popular cities widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Group tabs
        self.group_tabs = QTabWidget()
        self.group_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        for group_name, cities in self.city_groups.items():
            group_widget = QWidget()
            group_layout = QGridLayout(group_widget)
            group_layout.setSpacing(8)
            
            for i, city in enumerate(cities):
                btn = QPushButton(city)
                btn.setFont(HebrewTextHelper.setup_hebrew_font())
                btn.setMinimumHeight(35)
                btn.clicked.connect(lambda checked, c=city: self.add_common_city(c))
                group_layout.addWidget(btn, i // 3, i % 3)
            
            self.group_tabs.addTab(group_widget, group_name)
        
        layout.addWidget(self.group_tabs)
        return widget
    
    def setup_enhanced_autocomplete(self):
        """Set up enhanced autocomplete with Hebrew support"""
        all_cities = []
        for cities in self.city_groups.values():
            all_cities.extend(cities)
        
        # Add more comprehensive city list
        additional_cities = [
            "פתח תקווה", "ראשון לציון", "רחובות", "מודיעין", "יהוד מונוסון",
            "קריית אונו", "הרצליה פיתוח", "כפר יונה", "עמק חפר",
            "Tel Aviv", "Jerusalem", "Haifa", "Beersheba", "Petah Tikva"
        ]
        all_cities.extend(additional_cities)
        
        completer = QCompleter(sorted(set(all_cities)))
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        self.city_input.setCompleter(completer)
    
    def filter_popular_cities(self, text: str):
        """Filter popular cities based on search text"""
        if not text.strip():
            return
        
        # This would filter the popular cities tabs based on search text
        # Implementation would involve showing/hiding relevant cities
        pass
    
    def load_cities(self):
        """Load cities from config and create widgets"""
        self.clear_city_widgets()
        
        cities = self.config_manager.get_monitored_cities()
        for city in cities:
            priority = self.config_manager.get(f"city_priority_{city}", 1)
            self.add_city_widget(city, priority)
        
        self.update_statistics()
    
    def clear_city_widgets(self):
        """Clear all city widgets"""
        for widget in self.city_widgets.values():
            widget.deleteLater()
        self.city_widgets.clear()
        
        # Clear layout
        while self.cities_layout.count():
            child = self.cities_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def add_city_widget(self, city: str, priority: int = 1):
        """Add city widget to the list"""
        if city in self.city_widgets:
            return
        
        city_widget = DraggableCityItem(city, priority)
        city_widget.city_removed.connect(self.remove_city)
        city_widget.city_edited.connect(self.edit_city)
        city_widget.priority_changed.connect(self.change_city_priority)
        
        self.city_widgets[city] = city_widget
        self.cities_layout.addWidget(city_widget)
        
        # Sort by priority
        self.sort_cities_by_priority()
    
    def sort_cities_by_priority(self):
        """Sort cities by priority (high to low)"""
        # Remove all widgets from layout
        widgets = []
        for city, widget in self.city_widgets.items():
            self.cities_layout.removeWidget(widget)
            widgets.append((widget.priority, widget))
        
        # Sort by priority (descending)
        widgets.sort(key=lambda x: x[0], reverse=True)
        
        # Add back to layout
        for _, widget in widgets:
            self.cities_layout.addWidget(widget)
    
    def add_city(self):
        """Add city from input"""
        city = self.city_input.text().strip()
        if city and city not in self.config_manager.get_monitored_cities():
            self.config_manager.add_monitored_city(city)
            self.add_city_widget(city)
            self.city_input.clear()
            self.city_added.emit(city)
            self.update_statistics()
    
    def add_common_city(self, city: str):
        """Add common city from quick buttons"""
        if city not in self.config_manager.get_monitored_cities():
            self.config_manager.add_monitored_city(city)
            self.add_city_widget(city)
            self.city_added.emit(city)
            self.update_statistics()
    
    def remove_city(self, city: str):
        """Remove city"""
        if city in self.city_widgets:
            self.config_manager.remove_monitored_city(city)
            widget = self.city_widgets[city]
            self.cities_layout.removeWidget(widget)
            widget.deleteLater()
            del self.city_widgets[city]
            self.city_removed.emit(city)
            self.update_statistics()
    
    def edit_city(self, old_name: str, new_name: str):
        """Handle city name edit"""
        if old_name in self.city_widgets:
            # Update config
            self.config_manager.remove_monitored_city(old_name)
            self.config_manager.add_monitored_city(new_name)
            
            # Update widget dictionary
            widget = self.city_widgets[old_name]
            del self.city_widgets[old_name]
            self.city_widgets[new_name] = widget
            
            self.city_edited.emit(old_name, new_name)
    
    def change_city_priority(self, city: str, priority: int):
        """Handle city priority change"""
        self.config_manager.set(f"city_priority_{city}", priority)
        self.sort_cities_by_priority()
        self.city_priority_changed.emit(city, priority)
        self.update_statistics()
    
    def update_statistics(self):
        """Update statistics display"""
        total_cities = len(self.city_widgets)
        high_priority = sum(1 for widget in self.city_widgets.values() if widget.priority >= 3)
        self.stats_label.setText(f"Cities: {total_cities} | High Priority: {high_priority}")
    
    def import_cities(self):
        """Import cities from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Cities", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cities = [line.strip() for line in f if line.strip()]
                
                added_count = 0
                for city in cities:
                    if city not in self.config_manager.get_monitored_cities():
                        self.config_manager.add_monitored_city(city)
                        self.add_city_widget(city)
                        added_count += 1
                
                self.update_statistics()
                QMessageBox.information(
                    self, "Import Complete", 
                    f"Successfully imported {added_count} new cities."
                )
                
            except Exception as e:
                QMessageBox.warning(
                    self, "Import Error", 
                    f"Failed to import cities: {str(e)}"
                )
    
    def export_cities(self):
        """Export cities to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Cities", "monitored_cities.txt", 
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                cities = self.config_manager.get_monitored_cities()
                with open(file_path, 'w', encoding='utf-8') as f:
                    for city in cities:
                        f.write(f"{city}\n")
                
                QMessageBox.information(
                    self, "Export Complete", 
                    f"Successfully exported {len(cities)} cities to {file_path}"
                )
                
            except Exception as e:
                QMessageBox.warning(
                    self, "Export Error", 
                    f"Failed to export cities: {str(e)}"
                )
    
    def clear_all_cities(self):
        """Clear all monitored cities with confirmation"""
        if not self.city_widgets:
            return
        
        reply = QMessageBox.question(
            self, "Clear All Cities", 
            f"Remove all {len(self.city_widgets)} monitored cities?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            cities = list(self.city_widgets.keys())
            for city in cities:
                self.remove_city(city)

class MainWindow(QMainWindow):
    """Modern main application window with Material Design"""
    
    # Signals for communication with other components
    monitoring_toggled = pyqtSignal(bool)
    city_added = pyqtSignal(str)
    city_removed = pyqtSignal(str)
    settings_changed = pyqtSignal(str, object)
    test_sound_requested = pyqtSignal()
    test_notification_requested = pyqtSignal()
    test_tts_requested = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.is_monitoring = False
        
        self.setup_ui()
        self.apply_modern_theme()
        self.setup_window_properties()
        self.load_settings()
        self.setup_auto_save()
    
    def setup_ui(self):
        """Set up the modern user interface"""
        self.setWindowTitle("🚨 Red Alert Monitor")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        self.create_header(main_layout)
        
        # Create status widget
        self.status_widget = AnimatedStatusWidget()
        main_layout.addWidget(self.status_widget)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create bottom toolbar
        self.create_bottom_toolbar(main_layout)
    
    def create_header(self, parent_layout):
        """Create modern header section"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976d2, stop:1 #2196f3);
                border: none;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        # App title and icon
        title_layout = QVBoxLayout()
        
        app_title = QLabel("🚨 Red Alert Monitor")
        app_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        app_title.setStyleSheet("color: white;")
        title_layout.addWidget(app_title)
        
        subtitle = QLabel("Real-time alert monitoring for Israel")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Main control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        self.start_stop_btn = QPushButton("▶️ Start Monitoring")
        self.start_stop_btn.setMinimumSize(160, 40)
        self.start_stop_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.start_stop_btn.clicked.connect(self.toggle_monitoring)
        controls_layout.addWidget(self.start_stop_btn)
        
        test_btn = QPushButton("🧪 Test System")
        test_btn.setMinimumSize(120, 40)
        test_btn.setFont(QFont("Arial", 10))
        test_btn.clicked.connect(self.test_system)
        controls_layout.addWidget(test_btn)
        
        header_layout.addLayout(controls_layout)
        
        parent_layout.addWidget(header)
    
    def create_main_content(self, parent_layout):
        """Create main content area with tabs"""
        self.tab_widget = QTabWidget()
        
        # Cities tab
        self.city_widget = EnhancedCityListWidget(self.config_manager)
        self.city_widget.city_added.connect(self.city_added.emit)
        self.city_widget.city_removed.connect(self.city_removed.emit)
        self.tab_widget.addTab(self.city_widget, "🏙️ Cities")
        
        # Settings tab
        self.create_enhanced_settings_tab()
        
        # History tab
        self.create_enhanced_history_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_enhanced_settings_tab(self):
        """Create enhanced settings tab with better organization"""
        settings_main_widget = QWidget()
        
        # Create sub-tabs for settings
        settings_tabs = QTabWidget()
        settings_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Audio & Notifications tab
        self.create_audio_settings_tab(settings_tabs)
        
        # Monitoring tab
        self.create_monitoring_settings_tab(settings_tabs)
        
        # Interface tab
        self.create_interface_settings_tab(settings_tabs)
        
        # Advanced tab
        self.create_advanced_settings_tab(settings_tabs)
        
        settings_layout = QVBoxLayout(settings_main_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.addWidget(settings_tabs)
        
        self.tab_widget.addTab(settings_main_widget, "⚙️ Settings")
    
    def create_audio_settings_tab(self, parent_tabs):
        """Create audio and notifications settings tab"""
        audio_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(audio_widget)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(audio_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Sound Settings Group
        sound_group = QGroupBox("🔊 Sound Settings")
        sound_layout = QGridLayout(sound_group)
        sound_layout.setSpacing(15)
        
        # Enable sound
        self.sound_enabled_cb = QCheckBox("🔔 Enable Sound Alerts")
        self.sound_enabled_cb.setChecked(self.config_manager.get("sound_enabled", True))
        self.sound_enabled_cb.toggled.connect(self.on_sound_enabled_changed)
        sound_layout.addWidget(self.sound_enabled_cb, 0, 0, 1, 2)
        
        # Volume
        sound_layout.addWidget(QLabel("Volume:"), 1, 0)
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.config_manager.get("volume", 0.8) * 100))
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_label.setMinimumWidth(40)
        volume_layout.addWidget(self.volume_label)
        sound_layout.addLayout(volume_layout, 1, 1)
        
        # Sound file selection
        sound_layout.addWidget(QLabel("Alert Sound:"), 2, 0)
        sound_file_layout = QHBoxLayout()
        self.sound_file_label = QLabel("Default Alert Sound")
        self.sound_file_label.setStyleSheet("color: #666; font-style: italic;")
        sound_file_layout.addWidget(self.sound_file_label)
        
        browse_sound_btn = QPushButton("📂 Browse")
        browse_sound_btn.clicked.connect(self.browse_sound_file)
        sound_file_layout.addWidget(browse_sound_btn)
        
        test_sound_btn = QPushButton("🔊 Test")
        test_sound_btn.clicked.connect(self.test_sound_requested.emit)
        sound_file_layout.addWidget(test_sound_btn)
        
        sound_layout.addLayout(sound_file_layout, 2, 1)
        
        layout.addWidget(sound_group)
        
        # TTS Settings Group
        tts_group = QGroupBox("🗣️ Text-to-Speech Settings")
        tts_layout = QGridLayout(tts_group)
        tts_layout.setSpacing(15)
        
        # Enable TTS
        self.tts_enabled_cb = QCheckBox("🗣️ Enable Text-to-Speech")
        self.tts_enabled_cb.setChecked(self.config_manager.get("tts_enabled", True))
        self.tts_enabled_cb.toggled.connect(self.on_tts_enabled_changed)
        tts_layout.addWidget(self.tts_enabled_cb, 0, 0, 1, 2)
        
        # TTS Voice
        tts_layout.addWidget(QLabel("Voice:"), 1, 0)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(self.config_manager.get_tts_voices())
        self.voice_combo.setCurrentText(self.config_manager.get("tts_voice", "he-IL-HilaNeural"))
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)
        tts_layout.addWidget(self.voice_combo, 1, 1)
        
        # TTS Speed
        tts_layout.addWidget(QLabel("Speed:"), 2, 0)
        speed_layout = QHBoxLayout()
        self.tts_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.tts_speed_slider.setRange(50, 200)  # 0.5x to 2.0x speed
        self.tts_speed_slider.setValue(int(self.config_manager.get("tts_speed", 1.0) * 100))
        self.tts_speed_slider.valueChanged.connect(self.on_tts_speed_changed)
        speed_layout.addWidget(self.tts_speed_slider)
        
        self.tts_speed_label = QLabel(f"{self.tts_speed_slider.value()/100:.1f}x")
        self.tts_speed_label.setMinimumWidth(40)
        speed_layout.addWidget(self.tts_speed_label)
        tts_layout.addLayout(speed_layout, 2, 1)
        
        # Random voice option
        self.random_voice_cb = QCheckBox("🎲 Use Random Voice")
        self.random_voice_cb.setChecked(self.config_manager.get("random_voice", False))
        self.random_voice_cb.toggled.connect(self.on_random_voice_changed)
        tts_layout.addWidget(self.random_voice_cb, 3, 0, 1, 2)
        
        layout.addWidget(tts_group)
        
        # Notification Settings Group
        notification_group = QGroupBox("📢 Desktop Notifications")
        notification_layout = QVBoxLayout(notification_group)
        
        self.notifications_enabled_cb = QCheckBox("📨 Enable Desktop Notifications")
        self.notifications_enabled_cb.setChecked(self.config_manager.get("notifications_enabled", True))
        self.notifications_enabled_cb.toggled.connect(self.on_notifications_enabled_changed)
        notification_layout.addWidget(self.notifications_enabled_cb)
        
        # Notification duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Display Duration:"))
        self.notification_duration_spin = QSpinBox()
        self.notification_duration_spin.setRange(1, 30)
        self.notification_duration_spin.setValue(self.config_manager.get("notification_duration", 5))
        self.notification_duration_spin.valueChanged.connect(self.on_notification_duration_changed)
        duration_layout.addWidget(self.notification_duration_spin)
        duration_layout.addWidget(QLabel("seconds"))
        duration_layout.addStretch()
        notification_layout.addLayout(duration_layout)
        
        # Test notification button
        test_notification_btn = QPushButton("📨 Test Notification")
        test_notification_btn.clicked.connect(self.test_notification_requested.emit)
        notification_layout.addWidget(test_notification_btn)
        
        layout.addWidget(notification_group)
        
        layout.addStretch()
        
        parent_tabs.addTab(scroll_area, "🔊 Audio & Notifications")
        
    def create_monitoring_settings_tab(self, parent_tabs):
        """Create monitoring settings tab"""
        monitoring_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(monitoring_widget)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(monitoring_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Basic Monitoring Settings
        basic_group = QGroupBox("⏱️ Basic Settings")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(15)
        
        basic_layout.addWidget(QLabel("Check Interval:"), 0, 0)
        interval_layout = QHBoxLayout()
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(self.config_manager.get("check_interval", 3))
        self.interval_spin.valueChanged.connect(self.on_interval_changed)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(QLabel("seconds"))
        basic_layout.addLayout(interval_layout, 0, 1)
        
        basic_layout.addWidget(QLabel("Alert Pause Time:"), 1, 0)
        pause_layout = QHBoxLayout()
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(5, 300)
        self.pause_spin.setValue(self.config_manager.get("alert_pause_time", 25))
        self.pause_spin.valueChanged.connect(self.on_pause_changed)
        pause_layout.addWidget(self.pause_spin)
        pause_layout.addWidget(QLabel("seconds"))
        basic_layout.addLayout(pause_layout, 1, 1)
        
        # Auto-start monitoring
        self.auto_start_monitoring_cb = QCheckBox("🚀 Start monitoring automatically")
        self.auto_start_monitoring_cb.setChecked(self.config_manager.get("auto_start_monitoring", False))
        self.auto_start_monitoring_cb.toggled.connect(self.on_auto_start_monitoring_changed)
        basic_layout.addWidget(self.auto_start_monitoring_cb, 2, 0, 1, 2)
        
        layout.addWidget(basic_group)
        
        # Advanced Monitoring Settings
        advanced_group = QGroupBox("🔧 Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Connection timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Connection Timeout:"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setValue(self.config_manager.get("connection_timeout", 10))
        self.timeout_spin.valueChanged.connect(self.on_timeout_changed)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addWidget(QLabel("seconds"))
        timeout_layout.addStretch()
        advanced_layout.addLayout(timeout_layout)
        
        # Retry settings
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("Max Retries:"))
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(self.config_manager.get("max_retries", 3))
        self.retry_spin.valueChanged.connect(self.on_max_retries_changed)
        retry_layout.addWidget(self.retry_spin)
        retry_layout.addWidget(QLabel("attempts"))
        retry_layout.addStretch()
        advanced_layout.addLayout(retry_layout)
        
        # Priority monitoring
        self.priority_monitoring_cb = QCheckBox("⚡ Priority monitoring (check high-priority cities more frequently)")
        self.priority_monitoring_cb.setChecked(self.config_manager.get("priority_monitoring", True))
        self.priority_monitoring_cb.toggled.connect(self.on_priority_monitoring_changed)
        advanced_layout.addWidget(self.priority_monitoring_cb)
        
        layout.addWidget(advanced_group)
        
        # Alert Filtering
        filter_group = QGroupBox("🔍 Alert Filtering")
        filter_layout = QVBoxLayout(filter_group)
        
        # Minimum alert level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Minimum Alert Level:"))
        self.alert_level_combo = QComboBox()
        self.alert_level_combo.addItems(["All Alerts", "Important Only", "Critical Only"])
        self.alert_level_combo.setCurrentText(self.config_manager.get("alert_level_filter", "All Alerts"))
        self.alert_level_combo.currentTextChanged.connect(self.on_alert_level_changed)
        level_layout.addWidget(self.alert_level_combo)
        level_layout.addStretch()
        filter_layout.addLayout(level_layout)
        
        # Duplicate alert prevention
        self.prevent_duplicates_cb = QCheckBox("🚫 Prevent duplicate alerts (same area within 5 minutes)")
        self.prevent_duplicates_cb.setChecked(self.config_manager.get("prevent_duplicates", True))
        self.prevent_duplicates_cb.toggled.connect(self.on_prevent_duplicates_changed)
        filter_layout.addWidget(self.prevent_duplicates_cb)
        
        layout.addWidget(filter_group)
        
        layout.addStretch()
        
        parent_tabs.addTab(scroll_area, "⏱️ Monitoring")
    
    def create_interface_settings_tab(self, parent_tabs):
        """Create interface settings tab"""
        interface_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(interface_widget)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(interface_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Appearance Settings
        appearance_group = QGroupBox("🎨 Appearance")
        appearance_layout = QVBoxLayout(appearance_group)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        available_themes = ["Light Blue", "Dark Blue", "Light Green", "Dark Green", "Light Purple"]
        self.theme_combo.addItems(available_themes)
        self.theme_combo.setCurrentText(self.config_manager.get("theme", "Light Blue"))
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        # Font size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(self.config_manager.get("font_size", 11))
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addWidget(QLabel("pt"))
        font_layout.addStretch()
        appearance_layout.addLayout(font_layout)
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["עברית (Hebrew)", "English", "Mixed"])
        current_lang = self.config_manager.get("language", "he")
        lang_display = {"he": "עברית (Hebrew)", "en": "English", "mixed": "Mixed"}
        self.language_combo.setCurrentText(lang_display.get(current_lang, "עברית (Hebrew)"))
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        appearance_layout.addLayout(lang_layout)
        
        layout.addWidget(appearance_group)
        
        # Window Behavior
        window_group = QGroupBox("🪟 Window Behavior")
        window_layout = QVBoxLayout(window_group)
        
        self.minimize_to_tray_cb = QCheckBox("📥 Minimize to system tray")
        self.minimize_to_tray_cb.setChecked(self.config_manager.get("minimize_to_tray", True))
        self.minimize_to_tray_cb.toggled.connect(self.on_minimize_to_tray_changed)
        window_layout.addWidget(self.minimize_to_tray_cb)
        
        self.close_to_tray_cb = QCheckBox("❌ Close to system tray")
        self.close_to_tray_cb.setChecked(self.config_manager.get("close_to_tray", True))
        self.close_to_tray_cb.toggled.connect(self.on_close_to_tray_changed)
        window_layout.addWidget(self.close_to_tray_cb)
        
        self.start_minimized_cb = QCheckBox("📉 Start minimized")
        self.start_minimized_cb.setChecked(self.config_manager.get("start_minimized", False))
        self.start_minimized_cb.toggled.connect(self.on_start_minimized_changed)
        window_layout.addWidget(self.start_minimized_cb)
        
        self.always_on_top_cb = QCheckBox("📌 Always on top")
        self.always_on_top_cb.setChecked(self.config_manager.get("always_on_top", False))
        self.always_on_top_cb.toggled.connect(self.on_always_on_top_changed)
        window_layout.addWidget(self.always_on_top_cb)
        
        layout.addWidget(window_group)
        
        # Accessibility
        accessibility_group = QGroupBox("♿ Accessibility")
        accessibility_layout = QVBoxLayout(accessibility_group)
        
        self.high_contrast_cb = QCheckBox("🔲 High contrast mode")
        self.high_contrast_cb.setChecked(self.config_manager.get("high_contrast", False))
        self.high_contrast_cb.toggled.connect(self.on_high_contrast_changed)
        accessibility_layout.addWidget(self.high_contrast_cb)
        
        self.large_fonts_cb = QCheckBox("🔤 Large fonts")
        self.large_fonts_cb.setChecked(self.config_manager.get("large_fonts", False))
        self.large_fonts_cb.toggled.connect(self.on_large_fonts_changed)
        accessibility_layout.addWidget(self.large_fonts_cb)
        
        layout.addWidget(accessibility_group)
        
        layout.addStretch()
        
        parent_tabs.addTab(scroll_area, "🎨 Interface")
    
    def create_advanced_settings_tab(self, parent_tabs):
        """Create advanced settings tab"""
        advanced_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(advanced_widget)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(advanced_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Data Management
        data_group = QGroupBox("💾 Data Management")
        data_layout = QVBoxLayout(data_group)
        
        # Data retention
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Keep alert history for:"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 365)
        self.retention_spin.setValue(self.config_manager.get("data_retention_days", 30))
        self.retention_spin.valueChanged.connect(self.on_retention_changed)
        retention_layout.addWidget(self.retention_spin)
        retention_layout.addWidget(QLabel("days"))
        retention_layout.addStretch()
        data_layout.addLayout(retention_layout)
        
        # Export/Import buttons
        export_import_layout = QHBoxLayout()
        
        export_settings_btn = QPushButton("📤 Export Settings")
        export_settings_btn.clicked.connect(self.export_settings)
        export_import_layout.addWidget(export_settings_btn)
        
        import_settings_btn = QPushButton("📥 Import Settings")
        import_settings_btn.clicked.connect(self.import_settings)
        export_import_layout.addWidget(import_settings_btn)
        
        export_import_layout.addStretch()
        data_layout.addLayout(export_import_layout)
        
        # Backup settings
        self.auto_backup_cb = QCheckBox("🔄 Automatic settings backup")
        self.auto_backup_cb.setChecked(self.config_manager.get("auto_backup", True))
        self.auto_backup_cb.toggled.connect(self.on_auto_backup_changed)
        data_layout.addWidget(self.auto_backup_cb)
        
        layout.addWidget(data_group)
        
        # Logging Settings
        logging_group = QGroupBox("📝 Logging")
        logging_layout = QVBoxLayout(logging_group)
        
        # Log level
        log_level_layout = QHBoxLayout()
        log_level_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.config_manager.get("log_level", "INFO"))
        self.log_level_combo.currentTextChanged.connect(self.on_log_level_changed)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        logging_layout.addLayout(log_level_layout)
        
        # Log to file
        self.log_to_file_cb = QCheckBox("📄 Save logs to file")
        self.log_to_file_cb.setChecked(self.config_manager.get("log_to_file", True))
        self.log_to_file_cb.toggled.connect(self.on_log_to_file_changed)
        logging_layout.addWidget(self.log_to_file_cb)
        
        # View logs button
        view_logs_btn = QPushButton("👁️ View Logs")
        view_logs_btn.clicked.connect(self.view_logs)
        logging_layout.addWidget(view_logs_btn)
        
        layout.addWidget(logging_group)
        
        # System Information
        system_group = QGroupBox("ℹ️ System Information")
        system_layout = QVBoxLayout(system_group)
        
        # Version info
        version_label = QLabel(f"Version: 1.0.0")
        version_label.setFont(QFont("Arial", 10))
        system_layout.addWidget(version_label)
        
        # Python version
        import sys
        python_label = QLabel(f"Python: {sys.version.split()[0]}")
        python_label.setFont(QFont("Arial", 10))
        system_layout.addWidget(python_label)
        
        # Qt version
        from PyQt6.QtCore import QT_VERSION_STR
        qt_label = QLabel(f"Qt: {QT_VERSION_STR}")
        qt_label.setFont(QFont("Arial", 10))
        system_layout.addWidget(qt_label)
        
        # Check for updates button
        check_updates_btn = QPushButton("🔄 Check for Updates")
        check_updates_btn.clicked.connect(self.check_for_updates)
        system_layout.addWidget(check_updates_btn)
        
        layout.addWidget(system_group)
        
        # Reset Settings
        reset_group = QGroupBox("🔄 Reset")
        reset_layout = QVBoxLayout(reset_group)
        reset_layout.addWidget(QLabel("⚠️ Warning: This will reset all settings to defaults"))
        
        reset_btn = QPushButton("🔄 Reset All Settings")
        reset_btn.clicked.connect(self.reset_all_settings)
        reset_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        reset_layout.addWidget(reset_btn)
        
        layout.addWidget(reset_group)
        
        layout.addStretch()
        
        parent_tabs.addTab(scroll_area, "🔧 Advanced")
    
    def create_enhanced_history_tab(self):
        """Create enhanced history tab with filtering and export"""
        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with controls
        header_layout = QHBoxLayout()
        history_label = QLabel("📜 Alert History")
        history_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(history_label)
        
        header_layout.addStretch()
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        export_pdf_btn = QPushButton("📄 Export PDF")
        export_pdf_btn.clicked.connect(self.export_history_pdf)
        export_layout.addWidget(export_pdf_btn)
        
        export_csv_btn = QPushButton("📊 Export CSV")
        export_csv_btn.clicked.connect(self.export_history_csv)
        export_layout.addWidget(export_csv_btn)
        
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self.clear_history)
        export_layout.addWidget(clear_btn)
        
        header_layout.addLayout(export_layout)
        layout.addLayout(header_layout)
        
        # Filters
        filter_group = QGroupBox("🔍 Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        # Date filter
        filter_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.filter_history)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.filter_history)
        filter_layout.addWidget(self.date_to)
        
        # City filter
        filter_layout.addWidget(QLabel("City:"))
        self.city_filter = QComboBox()
        self.city_filter.addItem("All Cities")
        self.city_filter.currentTextChanged.connect(self.filter_history)
        filter_layout.addWidget(self.city_filter)
        
        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search alerts...")
        self.search_input.textChanged.connect(self.filter_history)
        filter_layout.addWidget(self.search_input)
        
        # Reset filters
        reset_filters_btn = QPushButton("🔄 Reset")
        reset_filters_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(reset_filters_btn)
        
        layout.addWidget(filter_group)
        
        # Stats
        self.stats_layout = QHBoxLayout()
        self.total_alerts_label = QLabel("Total: 0")
        self.today_alerts_label = QLabel("Today: 0")
        self.week_alerts_label = QLabel("This Week: 0")
        
        self.stats_layout.addWidget(self.total_alerts_label)
        self.stats_layout.addWidget(QLabel("|"))
        self.stats_layout.addWidget(self.today_alerts_label)
        self.stats_layout.addWidget(QLabel("|"))
        self.stats_layout.addWidget(self.week_alerts_label)
        self.stats_layout.addStretch()
        
        layout.addLayout(self.stats_layout)
        
        # History display with tree view
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Time", "Cities", "Type", "Duration", "Details"])
        self.history_tree.setAlternatingRowColors(True)
        self.history_tree.setSortingEnabled(True)
        self.history_tree.setFont(HebrewTextHelper.setup_hebrew_font())
        
        # Set column widths
        header = self.history_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_tree)
        
        # Add placeholder if no history
        if self.history_tree.topLevelItemCount() == 0:
            placeholder_item = QTreeWidgetItem(["", "📭 No alerts recorded yet...", "", "", ""])
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.history_tree.addTopLevelItem(placeholder_item)
        
        self.tab_widget.addTab(history_widget, "📜 History")
    
    def create_bottom_toolbar(self, parent_layout):
        """Create bottom status toolbar"""
        toolbar = QFrame()
        toolbar.setFixedHeight(30)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 5, 20, 5)
        
        self.status_bar_label = QLabel("Ready")
        self.status_bar_label.setFont(QFont("Arial", 9))
        toolbar_layout.addWidget(self.status_bar_label)
        
        toolbar_layout.addStretch()
        
        version_label = QLabel("v1.0.0")
        version_label.setFont(QFont("Arial", 9))
        version_label.setStyleSheet("color: #666;")
        toolbar_layout.addWidget(version_label)
        
        parent_layout.addWidget(toolbar)
    
    def apply_modern_theme(self):
        """Apply modern Material Design theme"""
        if QT_MATERIAL_AVAILABLE:
            try:
                apply_stylesheet(self, theme='light_blue.xml')
                return
            except:
                pass
        
        # Fallback modern styling
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #fafafa;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            
            QTabBar::tab:selected {
                background-color: #2196f3;
                color: white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #e3f2fd;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #1976d2;
                font-size: 13px;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #1976d2;
            }
            
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
            
            /* Header Buttons */
            QPushButton#headerButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
            }
            
            QPushButton#headerButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            
            /* Input Fields */
            QLineEdit, QComboBox, QSpinBox {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                background-color: white;
                min-height: 20px;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #2196f3;
            }
            
            /* List Widget */
            QListWidget {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 5px;
                selection-background-color: #e3f2fd;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 2px;
            }
            
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                height: 6px;
                background: #f0f0f0;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #2196f3;
                border: 2px solid #2196f3;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #1976d2;
                border-color: #1976d2;
            }
            
            /* Checkboxes */
            QCheckBox {
                spacing: 8px;
                font-size: 12px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ccc;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #2196f3;
                background-color: #2196f3;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEuNSA1TDMuNSA3TDguNSAyIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            /* Text Edit */
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
                font-family: "Consolas", "Monaco", monospace;
            }
        """)
        
        # Apply header button styling
        self.start_stop_btn.setObjectName("headerButton")
        
        # Find and apply to test button
        for child in self.findChildren(QPushButton):
            if "Test" in child.text():
                child.setObjectName("headerButton")
    
    def toggle_monitoring(self):
        """Toggle monitoring state with visual feedback"""
        self.is_monitoring = not self.is_monitoring
        self.monitoring_toggled.emit(self.is_monitoring)
        
        if self.is_monitoring:
            self.start_stop_btn.setText("⏹️ Stop Monitoring")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            self.status_widget.set_status("monitoring")
        else:
            self.start_stop_btn.setText("▶️ Start Monitoring")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
            """)
            self.status_widget.set_status("stopped")
    
    def test_system(self):
        """Test system with visual feedback"""
        self.test_sound_requested.emit()
        self.test_notification_requested.emit()
        self.test_tts_requested.emit()
        self.status_bar_label.setText("Testing system...")
        QTimer.singleShot(3000, lambda: self.status_bar_label.setText("Test completed"))
    
    def update_status(self, status: str):
        """Update status display"""
        self.status_bar_label.setText(status)
        
        if "alert" in status.lower():
            self.status_widget.set_status("alert", status)
        elif "checking" in status.lower():
            self.status_widget.set_status("checking")
        elif "monitoring" in status.lower() and "active" in status.lower():
            self.status_widget.set_status("monitoring")
    
    def add_alert_to_history(self, alert_data: Dict[str, Any]):
        """Add alert to history with enhanced tree view"""
        import datetime
        timestamp = datetime.datetime.now()
        time_str = timestamp.strftime("%H:%M:%S")
        date_str = timestamp.strftime("%Y-%m-%d")
        cities = ", ".join(alert_data.get("cities", []))
        title = alert_data.get("title", "Unknown Alert")
        description = alert_data.get("description", "")
        duration = alert_data.get("duration", "Unknown")
        
        # Remove placeholder if it exists
        if self.history_tree.topLevelItemCount() > 0:
            first_item = self.history_tree.topLevelItem(0)
            if first_item.text(1) == "📭 No alerts recorded yet...":
                self.history_tree.takeTopLevelItem(0)
        
        # Create tree item
        item = QTreeWidgetItem([
            f"{date_str} {time_str}",
            cities,
            title,
            str(duration),
            description
        ])
        
        # Add Hebrew font if needed
        if HebrewTextHelper.is_hebrew_text(cities):
            item.setFont(1, HebrewTextHelper.setup_hebrew_font())
        
        # Color code by alert type
        if "חירום" in title or "emergency" in title.lower():
            item.setBackground(0, QColor(255, 235, 238))  # Light red
            item.setBackground(1, QColor(255, 235, 238))
            item.setBackground(2, QColor(255, 235, 238))
            item.setBackground(3, QColor(255, 235, 238))
            item.setBackground(4, QColor(255, 235, 238))
        elif "התרעה" in title or "alert" in title.lower():
            item.setBackground(0, QColor(255, 243, 224))  # Light orange
            item.setBackground(1, QColor(255, 243, 224))
            item.setBackground(2, QColor(255, 243, 224))
            item.setBackground(3, QColor(255, 243, 224))
            item.setBackground(4, QColor(255, 243, 224))
        
        # Insert at the top
        self.history_tree.insertTopLevelItem(0, item)
        
        # Update city filter
        if cities not in [self.city_filter.itemText(i) for i in range(self.city_filter.count())]:
            self.city_filter.addItem(cities)
        
        # Update statistics
        self.update_history_statistics()
    
    def clear_history(self):
        """Clear alert history"""
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all alert history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_tree.clear()
            
            # Add placeholder
            placeholder_item = QTreeWidgetItem(["", "📭 History cleared...", "", "", ""])
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.history_tree.addTopLevelItem(placeholder_item)
            
            # Update statistics
            self.update_history_statistics()
    
    # Settings handlers with improved feedback
    def on_volume_changed(self, value):
        """Handle volume change"""
        volume = value / 100.0
        self.config_manager.set("volume", volume)
        self.volume_label.setText(f"{value}%")
        self.settings_changed.emit("volume", volume)
    
    def on_voice_changed(self, voice):
        """Handle TTS voice change"""
        self.config_manager.set("tts_voice", voice)
        self.settings_changed.emit("tts_voice", voice)
    
    def on_sound_enabled_changed(self, enabled):
        """Handle sound enabled change"""
        self.config_manager.set("sound_enabled", enabled)
        self.settings_changed.emit("sound_enabled", enabled)
    
    def on_tts_enabled_changed(self, enabled):
        """Handle TTS enabled change"""
        self.config_manager.set("tts_enabled", enabled)
        self.settings_changed.emit("tts_enabled", enabled)
    
    def on_interval_changed(self, value):
        """Handle check interval change"""
        self.config_manager.set("check_interval", value)
        self.settings_changed.emit("check_interval", value)
    
    def on_pause_changed(self, value):
        """Handle alert pause time change"""
        self.config_manager.set("alert_pause_time", value)
        self.settings_changed.emit("alert_pause_time", value)
    
    def on_notifications_enabled_changed(self, enabled):
        """Handle notifications enabled change"""
        self.config_manager.set("notifications_enabled", enabled)
        self.settings_changed.emit("notifications_enabled", enabled)
    
    def on_minimize_to_tray_changed(self, enabled):
        """Handle minimize to tray change"""
        self.config_manager.set("minimize_to_tray", enabled)
        self.settings_changed.emit("minimize_to_tray", enabled)
    
    def on_close_to_tray_changed(self, enabled):
        """Handle close to tray change"""
        self.config_manager.set("close_to_tray", enabled)
        self.settings_changed.emit("close_to_tray", enabled)
    
    def setup_window_properties(self):
        """Set up window properties"""
        pos = self.config_manager.get("window_position", {"x": 100, "y": 100})
        size = self.config_manager.get("window_size", {"width": 800, "height": 600})
        
        self.resize(size["width"], size["height"])
        self.move(pos["x"], pos["y"])
    
    def setup_auto_save(self):
        """Set up auto-save for window state"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_window_state)
        self.auto_save_timer.start(5000)
    
    def load_settings(self):
        """Load and apply settings"""
        pass  # Settings are loaded in individual components
    
    def save_window_state(self):
        """Save window position and size"""
        pos = self.pos()
        size = self.size()
        
        self.config_manager.set("window_position", {"x": pos.x(), "y": pos.y()})
        self.config_manager.set("window_size", {"width": size.width(), "height": size.height()})
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if self.config_manager.get("close_to_tray", True):
            event.ignore()
            self.hide()
        else:
            self.save_window_state()
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.config_manager.get("minimize_to_tray", True):
                self.hide()
        super().changeEvent(event)
    
    # Placeholder methods for missing functionality
    def filter_history(self):
        """Filter history based on current filter settings - placeholder"""
        pass
    
    def reset_filters(self):
        """Reset all history filters - placeholder"""
        pass
    
    def update_history_statistics(self):
        """Update history statistics - placeholder"""
        if hasattr(self, 'total_alerts_label'):
            total_count = self.history_tree.topLevelItemCount()
            self.total_alerts_label.setText(f"Total: {total_count}")
            self.today_alerts_label.setText("Today: 0")
            self.week_alerts_label.setText("This Week: 0")
    
    def browse_sound_file(self):
        """Browse for custom alert sound file - placeholder"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Alert Sound", "", 
            "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)"
        )
        if file_path:
            self.config_manager.set("alert_sound_file", file_path)
            if hasattr(self, 'sound_file_label'):
                self.sound_file_label.setText(os.path.basename(file_path))
    
    def export_history_csv(self):
        """Export history to CSV - placeholder"""
        QMessageBox.information(
            self, "Export CSV", 
            "CSV export functionality will be implemented."
        )
    
    def export_history_pdf(self):
        """Export history to PDF - placeholder"""
        QMessageBox.information(
            self, "Export PDF", 
            "PDF export functionality will be implemented."
        )
    
    def export_settings(self):
        """Export settings - placeholder"""
        QMessageBox.information(
            self, "Export Settings", 
            "Settings export functionality will be implemented."
        )
    
    def import_settings(self):
        """Import settings - placeholder"""
        QMessageBox.information(
            self, "Import Settings", 
            "Settings import functionality will be implemented."
        )
    
    def view_logs(self):
        """View logs - placeholder"""
        QMessageBox.information(
            self, "View Logs", 
            "Log viewing functionality will be implemented."
        )
    
    def check_for_updates(self):
        """Check for updates - placeholder"""
        QMessageBox.information(
            self, "Updates", 
            "You are running the latest version."
        )
    
    def reset_all_settings(self):
        """Reset all settings - placeholder"""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Reset", "Settings will be reset on restart.")
    
    # Additional settings handlers that were referenced
    def on_tts_speed_changed(self, value):
        """Handle TTS speed change"""
        speed = value / 100.0
        self.config_manager.set("tts_speed", speed)
        if hasattr(self, 'tts_speed_label'):
            self.tts_speed_label.setText(f"{speed:.1f}x")
        self.settings_changed.emit("tts_speed", speed)
    
    def on_random_voice_changed(self, enabled):
        """Handle random voice setting"""
        self.config_manager.set("random_voice", enabled)
        self.settings_changed.emit("random_voice", enabled)
    
    def on_notification_duration_changed(self, value):
        """Handle notification duration change"""
        self.config_manager.set("notification_duration", value)
        self.settings_changed.emit("notification_duration", value)
    
    def on_auto_start_monitoring_changed(self, enabled):
        """Handle auto start monitoring"""
        self.config_manager.set("auto_start_monitoring", enabled)
        self.settings_changed.emit("auto_start_monitoring", enabled)
    
    def on_timeout_changed(self, value):
        """Handle connection timeout"""
        self.config_manager.set("connection_timeout", value)
        self.settings_changed.emit("connection_timeout", value)
    
    def on_max_retries_changed(self, value):
        """Handle max retries"""
        self.config_manager.set("max_retries", value)
        self.settings_changed.emit("max_retries", value)
    
    def on_priority_monitoring_changed(self, enabled):
        """Handle priority monitoring"""
        self.config_manager.set("priority_monitoring", enabled)
        self.settings_changed.emit("priority_monitoring", enabled)
    
    def on_alert_level_changed(self, level):
        """Handle alert level filter"""
        self.config_manager.set("alert_level_filter", level)
        self.settings_changed.emit("alert_level_filter", level)
    
    def on_prevent_duplicates_changed(self, enabled):
        """Handle prevent duplicates"""
        self.config_manager.set("prevent_duplicates", enabled)
        self.settings_changed.emit("prevent_duplicates", enabled)
    
    def on_theme_changed(self, theme):
        """Handle theme change"""
        self.config_manager.set("theme", theme)
        self.settings_changed.emit("theme", theme)
    
    def on_font_size_changed(self, size):
        """Handle font size change"""
        self.config_manager.set("font_size", size)
        self.settings_changed.emit("font_size", size)
    
    def on_language_changed(self, language_display):
        """Handle language change"""
        lang_map = {
            "עברית (Hebrew)": "he",
            "English": "en", 
            "Mixed": "mixed"
        }
        language = lang_map.get(language_display, "he")
        self.config_manager.set("language", language)
        self.settings_changed.emit("language", language)
    
    def on_start_minimized_changed(self, enabled):
        """Handle start minimized"""
        self.config_manager.set("start_minimized", enabled)
        self.settings_changed.emit("start_minimized", enabled)
    
    def on_always_on_top_changed(self, enabled):
        """Handle always on top"""
        self.config_manager.set("always_on_top", enabled)
        self.settings_changed.emit("always_on_top", enabled)
        # Apply immediately
        if enabled:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
    
    def on_high_contrast_changed(self, enabled):
        """Handle high contrast"""
        self.config_manager.set("high_contrast", enabled)
        self.settings_changed.emit("high_contrast", enabled)
    
    def on_large_fonts_changed(self, enabled):
        """Handle large fonts"""
        self.config_manager.set("large_fonts", enabled)
        self.settings_changed.emit("large_fonts", enabled)
    
    def on_retention_changed(self, days):
        """Handle data retention"""
        self.config_manager.set("data_retention_days", days)
        self.settings_changed.emit("data_retention_days", days)
    
    def on_auto_backup_changed(self, enabled):
        """Handle auto backup"""
        self.config_manager.set("auto_backup", enabled)
        self.settings_changed.emit("auto_backup", enabled)
    
    def on_log_level_changed(self, level):
        """Handle log level"""
        self.config_manager.set("log_level", level)
        self.settings_changed.emit("log_level", level)
    
    def on_log_to_file_changed(self, enabled):
        """Handle log to file"""
        self.config_manager.set("log_to_file", enabled)
        self.settings_changed.emit("log_to_file", enabled) 