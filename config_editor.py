import json
import os
import sys
from copy import deepcopy

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


DEFAULT_GAME_ROOT = r"D:\Taikonijiro\TaikoNauts-Beta-20260408\publish"
GAME_EXE = "TaikoNauts.exe"
BACKGROUND_REL = os.path.join("Skins", "A-Style", "Image", "10.PlayerCustomize", "Background.png")
ICON_REL = os.path.join("Skins", "A-Style", "Image", "00.Demo", "Animes", "1", "Don.png")
CONFIG_FILES = {
    "GameConfig.json": os.path.join("Config", "GameConfig.json"),
    "SystemConfig.json": os.path.join("Config", "SystemConfig.json"),
}

KEY_NAMES = {
    "skinPath": "皮肤目录",
    "songPath": "歌曲目录",
    "username": "用户名",
    "password": "密码",
    "fullscreen": "全屏",
    "resolution": "分辨率",
    "targetFPS": "目标 FPS",
    "vSync": "垂直同步",
    "masterVolume": "主音量",
    "seVolume": "音效音量",
    "musicVolume": "音乐音量",
    "bgmVolume": "背景音乐音量",
    "voiceVolume": "语音音量",
    "showFPS": "显示 FPS",
    "donLeft1P": "1P左侧咚",
    "donRight1P": "1P右侧咚",
    "kaLeft1P": "1P左侧咔",
    "kaRight1P": "1P右侧咔",
    "donLeft2P": "2P左侧咚",
    "donRight2P": "2P右侧咚",
    "kaLeft2P": "2P左侧咔",
    "kaRight2P": "2P右侧咔",
    "setFavoriteKeys": "收藏键",
    "setMouseModeKeys": "鼠标模式键",
    "quickRetryKey": "快速重试键",
    "quickBackKey": "快速返回键",
    "deviceName": "设备名",
    "type": "类型",
    "key": "键盘按键",
    "button": "手柄按钮",
}


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def has_config_files(root):
    return all(os.path.exists(os.path.join(root, rel)) for rel in CONFIG_FILES.values())


def find_game_root():
    for root in [DEFAULT_GAME_ROOT, app_dir(), os.path.dirname(app_dir()), os.getcwd()]:
        if root and has_config_files(root):
            return os.path.normpath(root)
    return os.path.normpath(DEFAULT_GAME_ROOT)


def to_qss_path(path):
    return path.replace("\\", "/")


def make_relative_path(path, root):
    try:
        rel = os.path.relpath(path, root)
        if not rel.startswith(".."):
            return rel.replace("\\", "/")
    except ValueError:
        pass
    return path.replace("\\", "/")


class PathEditor(QWidget):
    def __init__(self, value, root, is_list=False):
        super().__init__()
        self.root = root
        self.is_list = is_list
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.edit = QLineEdit()
        self.edit.setText(self.format_value(value))
        self.button = QPushButton("选择目录")
        self.button.clicked.connect(self.choose_directory)

        layout.addWidget(self.edit, 1)
        layout.addWidget(self.button)

    def format_value(self, value):
        if self.is_list:
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def choose_directory(self):
        start = self.root
        if not self.is_list and self.edit.text():
            start = os.path.join(self.root, self.edit.text())
        directory = QFileDialog.getExistingDirectory(self, "选择目录", start)
        if not directory:
            return

        rel = make_relative_path(directory, self.root)
        if self.is_list:
            self.edit.setText(json.dumps([rel + "/" if not rel.endswith("/") else rel], ensure_ascii=False))
        else:
            self.edit.setText(rel)

    def value(self, old_value):
        text = self.edit.text()
        if self.is_list:
            return json.loads(text)
        return text


class KeyBindEditor(QPushButton):
    def __init__(self, value):
        super().__init__()
        self.key_text = str(value)
        self.waiting = False
        self.setText(self.display_text())
        self.clicked.connect(self.start_capture)
        self.setFocusPolicy(Qt.StrongFocus)

    def display_text(self):
        return "按下键盘按键..." if self.waiting else f"{self.key_text}  |  绑定按键"

    def start_capture(self):
        self.waiting = True
        self.setText(self.display_text())
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.waiting:
            super().keyPressEvent(event)
            return

        sequence = QKeySequence(event.key()).toString()
        self.key_text = sequence or event.text().upper()
        self.waiting = False
        self.setText(self.display_text())

    def value(self):
        return self.key_text


class JsonConfigEditor(QWidget):
    def __init__(self, path, root):
        super().__init__()
        self.path = path
        self.root = root
        self.data = {}
        self.original_data = {}
        self.widgets = {}
        self.build_ui()
        self.load()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.path_label = QLabel(self.path)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setObjectName("pathLabel")
        layout.addWidget(self.path_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.form = QFormLayout(self.content)
        self.form.setContentsMargins(18, 14, 18, 14)
        self.form.setHorizontalSpacing(18)
        self.form.setVerticalSpacing(10)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.reload_button = QPushButton("重新加载")
        self.reload_button.clicked.connect(self.load)
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save)
        buttons.addWidget(self.reload_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

    def load(self):
        self.clear_form()

        if not os.path.exists(self.path):
            self.form.addRow(QLabel("状态"), QLabel("未找到文件"))
            self.data = {}
            self.original_data = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8-sig") as file:
                self.data = json.load(file)
        except Exception as error:
            self.form.addRow(QLabel("状态"), QLabel(f"读取失败: {error}"))
            self.data = {}
            self.original_data = {}
            return

        self.original_data = deepcopy(self.data)
        self.add_fields(self.data)

    def clear_form(self):
        self.widgets.clear()
        while self.form.count():
            item = self.form.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def add_fields(self, data, prefix=()):
        if not prefix and "username" in data and "password" in data:
            self.add_section("登录")
            for key in ["username", "password"]:
                self.add_value(prefix + (key,), data[key])
            self.add_section("配置")

        for key, value in data.items():
            if not prefix and key in {"username", "password"}:
                continue

            path = prefix + (key,)
            if isinstance(value, dict):
                self.add_section(self.label_for_path(path))
                self.add_fields(value, path)
            elif isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                self.add_section(self.label_for_path(path))
                for index, item in enumerate(value):
                    for sub_key, sub_value in item.items():
                        self.add_value(path + (index, sub_key), sub_value)
            else:
                self.add_value(path, value)

    def add_section(self, text):
        title = QLabel(text)
        title.setObjectName("sectionLabel")
        self.form.addRow(title)

    def add_value(self, path, value):
        label = QLabel(self.label_for_path(path))
        editor = self.create_editor(value, path)
        self.form.addRow(label, editor)

    def label_for_path(self, path):
        parts = [part for part in path if not isinstance(part, int)]
        translated = [KEY_NAMES.get(part, str(part)) for part in parts]
        return " / ".join(translated)

    def create_editor(self, value, path):
        last_key = str(path[-1])
        is_path = "path" in last_key.lower()

        if isinstance(value, bool):
            editor = QComboBox()
            editor.addItems(["true", "false"])
            editor.setCurrentText("true" if value else "false")
        elif last_key == "key":
            editor = KeyBindEditor(value)
        elif is_path:
            editor = PathEditor(value, self.root, isinstance(value, list))
        else:
            editor = QLineEdit()
            if last_key == "password":
                editor.setEchoMode(QLineEdit.Password)
            if isinstance(value, (list, dict)):
                editor.setText(json.dumps(value, ensure_ascii=False))
            else:
                editor.setText(str(value))

        editor.setMinimumWidth(280)
        self.widgets[path] = editor
        return editor

    def save(self):
        try:
            updated = deepcopy(self.original_data)
            for path, widget in self.widgets.items():
                old_value = self.value_at_path(self.original_data, path)
                new_value = self.read_widget(widget, old_value)
                self.set_value_at_path(updated, path, new_value)

            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(updated, file, ensure_ascii=False, indent=2)
                file.write("\n")

            self.data = updated
            self.original_data = deepcopy(updated)
            QMessageBox.information(self, "保存完成", f"已保存: {os.path.basename(self.path)}")
        except Exception as error:
            QMessageBox.warning(self, "保存失败", str(error))

    def read_widget(self, widget, old_value):
        if isinstance(widget, QComboBox):
            return widget.currentText() == "true"
        if isinstance(widget, KeyBindEditor):
            return widget.value()
        if isinstance(widget, PathEditor):
            return widget.value(old_value)

        text = widget.text()
        if isinstance(old_value, int) and not isinstance(old_value, bool):
            return int(text)
        if isinstance(old_value, float):
            return float(text)
        if isinstance(old_value, (list, dict)):
            return json.loads(text)
        return text

    def value_at_path(self, data, path):
        value = data
        for part in path:
            value = value[part]
        return value

    def set_value_at_path(self, data, path, value):
        target = data
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.root = find_game_root()
        self.editors = {}
        self.build_ui()
        self.apply_assets()

    def build_ui(self):
        self.setWindowTitle("TaikoNauts JSON 配置编辑器")
        self.resize(980, 720)
        self.setMinimumSize(760, 540)

        central = QWidget()
        central.setObjectName("mainWidget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        self.root_label = QLabel(self.root)
        self.root_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.root_label.setObjectName("rootLabel")

        choose_button = QPushButton("选择目录")
        choose_button.clicked.connect(self.choose_root)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.reload_all)
        launch_button = QPushButton("启动游戏")
        launch_button.clicked.connect(self.launch_game)

        top.addWidget(QLabel("游戏目录"))
        top.addWidget(self.root_label, 1)
        top.addWidget(choose_button)
        top.addWidget(refresh_button)
        top.addWidget(launch_button)
        layout.addLayout(top)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.reload_all()

    def reload_all(self):
        self.tabs.clear()
        self.editors.clear()

        for name, rel_path in CONFIG_FILES.items():
            path = os.path.normpath(os.path.join(self.root, rel_path))
            editor = JsonConfigEditor(path, self.root)
            self.editors[name] = editor
            self.tabs.addTab(editor, name)

    def choose_root(self):
        directory = QFileDialog.getExistingDirectory(self, "选择游戏 publish 目录", self.root)
        if not directory:
            return

        self.root = os.path.normpath(directory)
        self.root_label.setText(self.root)
        self.reload_all()
        self.apply_assets()

        if not has_config_files(self.root):
            QMessageBox.warning(
                self,
                "未找到配置",
                "所选目录下需要存在 Config/GameConfig.json 和 Config/SystemConfig.json。",
            )

    def launch_game(self):
        exe_path = os.path.join(self.root, GAME_EXE)
        if not os.path.exists(exe_path):
            QMessageBox.warning(self, "启动失败", f"未找到: {exe_path}")
            return
        if not QProcess.startDetached(exe_path, [], self.root):
            QMessageBox.warning(self, "启动失败", "无法启动游戏。")

    def apply_assets(self):
        icon_path = os.path.join(self.root, ICON_REL)
        background_path = os.path.join(self.root, BACKGROUND_REL)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        background = ""
        if os.path.exists(background_path):
            background = (
                f'background-image: url("{to_qss_path(background_path)}");'
                "background-position: center;"
                "background-repeat: no-repeat;"
            )

        self.setStyleSheet(
            f"""
            QWidget#mainWidget {{
                {background}
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 10pt;
                color: #202124;
            }}
            QTabWidget::pane {{
                border: 1px solid rgba(210, 216, 226, 190);
                background: rgba(255, 255, 255, 220);
                border-radius: 6px;
            }}
            QTabBar::tab {{
                padding: 9px 18px;
                background: rgba(236, 240, 248, 225);
                border: 1px solid rgba(210, 216, 226, 190);
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: rgba(255, 255, 255, 235);
                font-weight: 600;
            }}
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background: rgba(255, 255, 255, 218);
            }}
            QLabel {{
                background: transparent;
            }}
            QLabel#rootLabel, QLabel#pathLabel {{
                color: #4f5661;
            }}
            QLabel#sectionLabel {{
                color: #0b57d0;
                font-weight: 700;
                margin-top: 10px;
            }}
            QLineEdit, QComboBox {{
                background: rgba(255, 255, 255, 235);
                border: 1px solid #c8d0dc;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 24px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: #0b57d0;
            }}
            QPushButton {{
                background: #0b57d0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #0842a0;
            }}
            """
        )


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
