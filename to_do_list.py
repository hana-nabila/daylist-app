import sys
from datetime import date
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QFrame, QScrollArea, 
                             QCheckBox, QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

# KOMPONEN

class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(130, 130)
        self._value = 0

    @pyqtProperty(float)
    def value(self): return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#edf2f7"), 10))
        painter.drawEllipse(15, 15, 100, 100)
        pen = QPen(QColor("#4fd1c5"), 10)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(15, 15, 100, 100), 90 * 16, int(-self._value * 3.6 * 16))
        painter.setPen(QPen(QColor("#2d3748")))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{int(self._value)}%")
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QPen(QColor("#a0aec0")))
        painter.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter, "Day's Progress")

class TaskItem(QFrame):
    def __init__(self, text, priority="High", due="Today", is_completed=False, parent=None):
        super().__init__(parent)
        self.task_text = text
        self.priority = priority
        self.due = due
        self.is_completed = is_completed
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.is_completed)
        self.checkbox.setAccessibleName(f"Mark {self.task_text} as completed")
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { width: 24px; height: 24px; border: 2px solid #cbd5e0; border-radius: 12px; background: white; }
            QCheckBox::indicator:checked { background-color: #48bb78; border-color: #48bb78; }
        """)
        self.checkbox.stateChanged.connect(self.toggle_complete)
        self.layout.addWidget(self.checkbox)

        v_info = QVBoxLayout()
        self.title_lbl = QLabel(self.task_text)
        self.title_lbl.setWordWrap(True)
        
        today_str = date.today().strftime("%Y-%m-%d")
        self.details_lbl = QLabel(f"{today_str} • {self.due} • {self.priority}")
        self.details_lbl.setStyleSheet("color: #a0aec0; font-size: 11px; border: none; background: transparent;")
        
        v_info.addWidget(self.title_lbl)
        v_info.addWidget(self.details_lbl)
        self.layout.addLayout(v_info)
        self.layout.addStretch()

        self.btn_del = QPushButton("✕")
        self.btn_del.setFixedSize(32, 32)
        self.btn_del.setAccessibleName(f"Delete task {self.task_text}")
        self.btn_del.setToolTip("Remove Task")
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.setStyleSheet("""
            QPushButton { border: none; background: transparent; color: #cbd5e0; font-size: 14px; font-weight: bold; border-radius: 16px; }
            QPushButton:hover { background: #fff5f5; color: #f56565; }
        """)
        self.layout.addWidget(self.btn_del)
        self.update_appearance()

    def toggle_complete(self):
        self.is_completed = self.checkbox.isChecked()
        self.update_appearance()
        # Find the parent 
        top_lvl = self.window()
        if hasattr(top_lvl, 'update_dashboard'):
            top_lvl.update_dashboard()

    def update_appearance(self):
        prio_color = "#3182ce" if self.priority == "High" else "#f6ad55"
        if self.is_completed:
            self.setStyleSheet("QFrame { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 5px; }")
            self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #cbd5e0; text-decoration: line-through; background: transparent;")
        else:
            self.setStyleSheet(f"QFrame {{ background: white; border: 1px solid #edf2f7; border-left: 4px solid {prio_color}; border-radius: 12px; margin-bottom: 5px; }}")
            self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1a202c; background: transparent;")

class Daylist(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.last_deleted = None # Storage for Undo
        self.setWindowTitle('Daylist')
        self.setFixedSize(500, 800)
        self.setStyleSheet("background-color: #f7fafc;")
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # HEADER 
        header = QFrame()
        header.setStyleSheet("background: white; border-radius: 20px; border: 1px solid #e2e8f0;")
        h_layout = QVBoxLayout(header)
        
        title_row = QHBoxLayout()
        logo = QLabel("Daylist")
        logo.setStyleSheet("font-size: 22px; font-weight: 900; color: #2d3748;")
        title_row.addWidget(logo)
        title_row.addStretch()
        
        self.filter_group = QButtonGroup(self)
        for i, t in enumerate(["All", "Active", "Done"]):
            btn = QPushButton(t)
            btn.setCheckable(True)
            btn.setFixedSize(65, 30)
            btn.setAccessibleName(f"Filter by {t} tasks")
            btn.setStyleSheet("QPushButton { background: #edf2f7; font-size: 11px; border-radius: 8px; font-weight: bold; color: #718096; border: none; } QPushButton:checked { background: #3182ce; color: white; }")
            btn.clicked.connect(lambda checked, tag=t: self.filter_tasks(tag))
            self.filter_group.addButton(btn, i)
            title_row.addWidget(btn)
            if t == "All": btn.setChecked(True)
        h_layout.addLayout(title_row)

        input_container = QVBoxLayout()
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("What needs to be done?")
        self.input_field.setAccessibleName("Input task description")
        self.input_field.returnPressed.connect(self.add_task_logic)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.setFixedSize(70, 44)
        self.add_btn.setToolTip("Add Task (Enter)")
        self.add_btn.setStyleSheet("background: #3182ce; color: white; border-radius: 12px; font-weight: bold;")
        self.add_btn.clicked.connect(self.add_task_logic)
        
        input_row.addWidget(self.input_field)
        input_row.addWidget(self.add_btn)
        input_container.addLayout(input_row)

        # Priority & Due select
        sel_row = QHBoxLayout()
        self.prio_group = QButtonGroup(self)
        for i, p in enumerate(["High", "Medium"]):
            btn = QPushButton(p)
            btn.setCheckable(True)
            btn.setFixedSize(60, 26)
            btn.setStyleSheet("QPushButton { background: #edf2f7; border-radius: 6px; font-size: 10px; color: #718096; border: none; } QPushButton:checked { background: white; border: 1px solid #3182ce; color: #3182ce; font-weight: bold; }")
            self.prio_group.addButton(btn, i)
            sel_row.addWidget(btn)
            if p == "High": btn.setChecked(True)

        sel_row.addSpacing(10)
        self.due_group = QButtonGroup(self)
        for i, d in enumerate(["Today", "Tomorrow"]):
            btn = QPushButton(d)
            btn.setCheckable(True)
            btn.setFixedSize(70, 26)
            btn.setStyleSheet("QPushButton { background: #edf2f7; border-radius: 6px; font-size: 10px; color: #718096; border: none; } QPushButton:checked { background: white; border: 1px solid #4a5568; color: #4a5568; font-weight: bold; }")
            self.due_group.addButton(btn, i)
            sel_row.addWidget(btn)
            if d == "Today": btn.setChecked(True)
        sel_row.addStretch()
        input_container.addLayout(sel_row)
        h_layout.addLayout(input_container)
        self.main_layout.addWidget(header)

        # PROGRESS & EMPTY STATE 
        self.mid_container = QFrame()
        mid_vbox = QVBoxLayout(self.mid_container)
        self.prog_circle = CircularProgress()
        mid_vbox.addWidget(self.prog_circle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.empty_label = QLabel("✨ All clear! Time to relax or add a new goal.")
        self.empty_label.setStyleSheet("color: #a0aec0; font-style: italic; font-size: 13px; margin-top: 5px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mid_vbox.addWidget(self.empty_label)
        self.main_layout.addWidget(self.mid_container)

        # SCROLL AREA 
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.task_layout = QVBoxLayout(self.container)
        self.task_layout.setSpacing(8)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

        # UNDO BAR (Hidden by default)
        self.undo_bar = QFrame()
        self.undo_bar.setVisible(False)
        self.undo_bar.setStyleSheet("background: #2d3748; border-radius: 12px;")
        self.undo_bar.setFixedHeight(50)
        undo_layout = QHBoxLayout(self.undo_bar)
        self.undo_lbl = QLabel("Task deleted")
        self.undo_lbl.setStyleSheet("color: white; font-weight: bold;")
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setFixedSize(60, 30)
        self.undo_btn.setStyleSheet("background: #4fd1c5; color: #2d3748; border-radius: 6px; font-weight: 900;")
        self.undo_btn.clicked.connect(self.undo_delete)
        undo_layout.addWidget(self.undo_lbl)
        undo_layout.addStretch()
        undo_layout.addWidget(self.undo_btn)
        self.main_layout.addWidget(self.undo_bar)

        # FOOTER 
        self.stats_summary = QLabel("No tasks yet")
        self.stats_summary.setStyleSheet("color: #718096; font-size: 12px; margin-bottom: 5px;")
        self.main_layout.addWidget(self.stats_summary, alignment=Qt.AlignmentFlag.AlignCenter)

        bulk_layout = QHBoxLayout()
        self.btn_bulk_done = QPushButton("Finish Selected")
        self.btn_bulk_done.setStyleSheet("QPushButton { background: #48bb78; color: white; padding: 12px; border-radius: 12px; font-weight: bold; } QPushButton:disabled { background: #cbd5e0; }")
        self.btn_bulk_done.clicked.connect(self.bulk_complete)
        
        self.btn_bulk_del = QPushButton("Remove Tasks")
        self.btn_bulk_del.setStyleSheet("QPushButton { background: #f56565; color: white; padding: 12px; border-radius: 12px; font-weight: bold; } QPushButton:disabled { background: #cbd5e0; }")
        self.btn_bulk_del.clicked.connect(self.bulk_delete)
        
        bulk_layout.addWidget(self.btn_bulk_done)
        bulk_layout.addWidget(self.btn_bulk_del)
        self.main_layout.addLayout(bulk_layout)
        
        self.update_dashboard()

    def add_task_logic(self):
        text = self.input_field.text()
        if text.strip():
            prio = self.prio_group.checkedButton().text()
            due = self.due_group.checkedButton().text()
            item = TaskItem(text, prio, due)
            item.btn_del.clicked.connect(lambda: self.confirm_delete(item))
            self.task_layout.addWidget(item)
            self.tasks.append(item)
            self.input_field.clear()
            self.update_dashboard()

    def confirm_delete(self, item):
        
        self.last_deleted = {
            "text": item.task_text,
            "priority": item.priority,
            "due": item.due,
            "is_completed": item.is_completed
        }
        self.remove_single_task(item)
        self.show_undo_notification()

    def remove_single_task(self, item):
        self.task_layout.removeWidget(item)
        if item in self.tasks: self.tasks.remove(item)
        item.deleteLater()
        self.update_dashboard()

    def show_undo_notification(self):
        self.undo_bar.setVisible(True)
        QTimer.singleShot(5000, lambda: self.undo_bar.setVisible(False))

    def undo_delete(self):
        if self.last_deleted:
            item = TaskItem(
                self.last_deleted["text"], 
                self.last_deleted["priority"], 
                self.last_deleted["due"],
                self.last_deleted["is_completed"]
            )
            item.btn_del.clicked.connect(lambda: self.confirm_delete(item))
            self.task_layout.addWidget(item)
            self.tasks.append(item)
            self.last_deleted = None
            self.undo_bar.setVisible(False)
            self.update_dashboard()

    def filter_tasks(self, tag):
        for task in self.tasks:
            if tag == "All": task.show()
            elif tag == "Active": task.setVisible(not task.is_completed)
            elif tag == "Done": task.setVisible(task.is_completed)
        self.update_dashboard()

    def bulk_complete(self):
        for task in self.tasks:
            if task.isVisible() and not task.is_completed:
                task.checkbox.setChecked(True)
        self.update_dashboard()

    def bulk_delete(self):
        to_remove = [t for t in self.tasks if t.isVisible()]
        if to_remove:
            reply = QMessageBox.question(self, 'Confirm Bulk Delete', f"Remove {len(to_remove)} tasks?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for t in to_remove:
                    self.task_layout.removeWidget(t)
                    if t in self.tasks: self.tasks.remove(t)
                    t.deleteLater()
                self.update_dashboard()

    def update_dashboard(self):
        total = len(self.tasks)
        visible_tasks = [t for t in self.tasks if t.isVisible()]
        current_filter = self.filter_group.checkedButton().text()
        
        # Accessibility & State
        self.mid_container.setVisible(len(visible_tasks) < 4)
        self.empty_label.setVisible(len(visible_tasks) == 0)
        
        if total == 0:
            self.empty_label.setText("✨ All clear! Time to relax.")
        elif not visible_tasks:
            self.empty_label.setText(f"No {current_filter.lower()} tasks found.")

        done = sum(1 for t in self.tasks if t.is_completed)
        self.stats_summary.setText(f"{total - done} task(s) left to go!")
        
        self.btn_bulk_del.setEnabled(len(visible_tasks) > 0)
        self.btn_bulk_done.setEnabled(current_filter != "Done" and any(not t.is_completed for t in visible_tasks))

        target = (done / total * 100) if total > 0 else 0
        self.anim = QPropertyAnimation(self.prog_circle, b"value")
        self.anim.setDuration(600)
        self.anim.setStartValue(self.prog_circle.value)
        self.anim.setEndValue(target)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.bulk_delete()
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    # Accessibility 
    app.setStyleSheet("""
        QWidget:focus { border: 2px solid #3182ce; border-radius: 4px; }
        QLineEdit { color: #1a202c !important; font-size: 14px; font-weight: 600; background-color: #ffffff; border: 2px solid #cbd5e0; padding: 12px; border-radius: 12px; }
        QLineEdit:focus { border: 2px solid #3182ce; }
        QToolTip { background-color: #2d3748; color: white; border: none; padding: 5px; border-radius: 4px; }
    """)
    window = Daylist()
    window.show()
    sys.exit(app.exec())