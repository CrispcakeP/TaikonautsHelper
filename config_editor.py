import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QScrollArea, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QLabel, QPushButton, QFrame,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


BASE_PATH = r"D:\Taikonijiro\TaikoNauts-Beta-20260408\publish"

CONFIGS = [
    ("游戏配置", "Config/GameConfig.json"),
    ("系统配置", "Config/SystemConfig.json"),
    ("皮肤配置", "Skins/A-Style/SkinConfig.json"),
]

# 嵌套对象中的键，按选项卡分组，仅显示可编辑的简单字段
# 键绑定的数组对象结构统一，只编辑 key 字段即可
KEY_BINDING_KEYS = [
    "donLeft1P", "donRight1P", "kaLeft1P", "kaRight1P",
    "donLeft2P", "donRight2P", "kaLeft2P", "kaRight2P",
    "setFavoriteKeys", "setMouseModeKeys", "quickRetryKey", "quickBackKey",
]


def get_key_display_name(key):
    """将键名转为中文显示名"""
    names = {
        "donLeft1P": "咚 左 (1P)", "donRight1P": "咚 右 (1P)",
        "kaLeft1P": "咔 左 (1P)", "kaRight1P": "咔 右 (1P)",
        "donLeft2P": "咚 左 (2P)", "donRight2P": "咚 右 (2P)",
        "kaLeft2P": "咔 左 (2P)", "kaRight2P": "咔 右 (2P)",
        "setFavoriteKeys": "收藏键", "setMouseModeKeys": "鼠标模式键",
        "quickRetryKey": "快速重试键", "quickBackKey": "快速返回键",
    }
    return names.get(key, key)


class ConfigEditor(QWidget):
    """单个配置文件的编辑器"""

    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.config_data = {}
        self.widget_map = {}  # (key_path_tuple) -> widget
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.form = QFormLayout(self.content)
        self.form.setSpacing(10)
        self.form.setContentsMargins(16, 16, 16, 16)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.reload_btn = QPushButton("重新加载")
        self.reload_btn.clicked.connect(self.load_config)
        btn_row.addWidget(self.reload_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def load_config(self):
        # 清除现有控件
        for i in reversed(range(self.form.count())):
            item = self.form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        self.widget_map.clear()

        if not os.path.exists(self.config_path):
            self.form.addRow(QLabel(f"配置文件不存在: {self.config_path}"))
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            self._build_fields(self.config_data)
        except Exception as e:
            self.form.addRow(QLabel(f"加载配置失败: {e}"))

    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _build_fields(self, data):
        """为顶层键构建编辑字段"""
        for key, value in data.items():
            if key in KEY_BINDING_KEYS and isinstance(value, list):
                self._build_key_binding(key, value)
            elif isinstance(value, bool):
                self.form.addRow(self._label(key), self._bool_combo(key, value))
            elif isinstance(value, int):
                self.form.addRow(self._label(key), self._int_spin(key, value))
            elif isinstance(value, float):
                self.form.addRow(self._label(key), self._float_spin(key, value))
            elif isinstance(value, str):
                self.form.addRow(self._label(key), self._str_edit(key, value))
            elif isinstance(value, list):
                # 简单数组（如 songPath）
                edit = QLineEdit(json.dumps(value, ensure_ascii=False))
                edit.setMinimumWidth(220)
                self.widget_map[(key,)] = edit
                self.form.addRow(self._label(key), edit)

    def _build_key_binding(self, key, bindings):
        """构建键绑定分组"""
        group = QGroupBox(get_key_display_name(key))
        g_layout = QFormLayout(group)
        g_layout.setSpacing(6)

        for idx, binding in enumerate(bindings):
            if isinstance(binding, dict):
                for bkey, bval in binding.items():
                    w = self._create_widget_for_value(bval)
                    if w:
                        path = (key, idx, bkey)
                        self.widget_map[path] = w
                        g_layout.addRow(self._label(bkey), w)

        self.form.addRow(group)

    def _create_widget_for_value(self, value):
        if isinstance(value, bool):
            return self._bool_combo(None, value)
        elif isinstance(value, int):
            return self._int_spin(None, value)
        elif isinstance(value, float):
            return self._float_spin(None, value)
        elif isinstance(value, str):
            return self._str_edit(None, value)
        return None

    def _bool_combo(self, key, value):
        combo = QComboBox()
        combo.addItems(["true", "false"])
        combo.setCurrentText(str(value).lower())
        combo.setMinimumWidth(220)
        if key is not None:
            self.widget_map[(key,)] = combo
        return combo

    def _int_spin(self, key, value):
        spin = QSpinBox()
        spin.setRange(-999999, 999999)
        spin.setValue(value)
        spin.setMinimumWidth(220)
        if key is not None:
            self.widget_map[(key,)] = spin
        return spin

    def _float_spin(self, key, value):
        spin = QDoubleSpinBox()
        spin.setRange(-999999.0, 999999.0)
        spin.setDecimals(6)
        spin.setValue(value)
        spin.setMinimumWidth(220)
        if key is not None:
            self.widget_map[(key,)] = spin
        return spin

    def _str_edit(self, key, value):
        edit = QLineEdit(value)
        edit.setMinimumWidth(220)
        if key is not None:
            self.widget_map[(key,)] = edit
        return edit

    def _label(self, key):
        lbl = QLabel(key)
        lbl.setMinimumWidth(200)
        return lbl

    def save_config(self):
        try:
            self._collect_values()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败: {e}")

    def _collect_values(self):
        """从控件回写值到 config_data"""
        for path, widget in self.widget_map.items():
            if len(path) == 1:
                key = path[0]
                self.config_data[key] = self._widget_value(widget, self.config_data[key])
            elif len(path) == 3:
                key, idx, bkey = path
                self.config_data[key][idx][bkey] = self._widget_value(
                    widget, self.config_data[key][idx][bkey]
                )

    def _widget_value(self, widget, original):
        if isinstance(widget, QComboBox):
            return widget.currentText() == "true"
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            if isinstance(original, list):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return original
            return text
        return original


LIGHT_QSS = """
QMainWindow, QWidget {
    background-color: #f8f8f8;
    color: #2c2c2c;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QTabWidget::pane {
    border: 1px solid #d4d4d4;
    background-color: #ffffff;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #e8e8e8;
    border: 1px solid #d4d4d4;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 20px;
    margin-right: 2px;
    color: #555;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2c2c2c;
    font-weight: bold;
}
QScrollArea {
    background-color: #ffffff;
    border: none;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #c8c8c8;
    padding: 6px 8px;
    border-radius: 4px;
    color: #2c2c2c;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #0078d4;
}
QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 9px 20px;
    border-radius: 5px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1a86d9;
}
QPushButton:pressed {
    background-color: #005a9e;
}
QLabel {
    color: #2c2c2c;
}
QGroupBox {
    border: 1px solid #d4d4d4;
    border-radius: 6px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    background-color: #fafafa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #444;
}
QScrollBar:vertical {
    border: none;
    background: #f0f0f0;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #c0c0c0;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}
QTabWidget::pane {
    border: 1px solid #2d2d44;
    background-color: #16213e;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #1a1a2e;
    border: 1px solid #2d2d44;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 20px;
    margin-right: 2px;
    color: #999;
}
QTabBar::tab:selected {
    background-color: #16213e;
    color: #e0e0e0;
    font-weight: bold;
}
QScrollArea {
    background-color: #16213e;
    border: none;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0f3460;
    border: 1px solid #2d2d44;
    padding: 6px 8px;
    border-radius: 4px;
    color: #e0e0e0;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1.5px solid #0078d4;
}
QComboBox QAbstractItemView {
    background-color: #0f3460;
    color: #e0e0e0;
    selection-background-color: #0078d4;
}
QPushButton {
    background-color: #e94560;
    color: #ffffff;
    border: none;
    padding: 9px 20px;
    border-radius: 5px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #ff6b81;
}
QPushButton:pressed {
    background-color: #c73a54;
}
QLabel {
    color: #e0e0e0;
}
QGroupBox {
    border: 1px solid #2d2d44;
    border-radius: 6px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    background-color: #1a1a2e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: #ccc;
}
QScrollBar:vertical {
    border: none;
    background: #1a1a2e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3a3a5c;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, base_path):
        super().__init__()
        self.base_path = base_path
        self.is_dark = False
        self.init_ui()
        self.setStyleSheet(LIGHT_QSS)

    def init_ui(self):
        self.setWindowTitle("TaikoNauts 配置编辑器")
        self.setGeometry(100, 100, 820, 620)
        self.setMinimumSize(640, 460)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.theme_btn = QPushButton("暗色模式")
        self.theme_btn.setFixedWidth(100)
        self.theme_btn.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 选项卡
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.editors = []
        for name, rel_path in CONFIGS:
            full_path = os.path.join(self.base_path, rel_path)
            editor = ConfigEditor(full_path)
            self.tabs.addTab(editor, name)
            self.editors.append(editor)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        if self.is_dark:
            self.setStyleSheet(DARK_QSS)
            self.theme_btn.setText("亮色模式")
        else:
            self.setStyleSheet(LIGHT_QSS)
            self.theme_btn.setText("暗色模式")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    window = MainWindow(BASE_PATH)
    window.show()
    sys.exit(app.exec())
