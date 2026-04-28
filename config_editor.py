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
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


DEFAULT_GAME_ROOT = r"D:\Taikonijiro\TaikoNauts-Beta-20260408\publish"
GAME_EXE = "TaikoNauts.exe"
BACKGROUND_REL = os.path.join("Skins", "A-Style", "Image", "10.PlayerCustomize", "Background.png")
ICON_REL = os.path.join("Skins", "A-Style", "Image", "00.Demo", "Animes", "1", "Don.png")
CONFIG_FILES = {
    "游戏设置": os.path.join("Config", "GameConfig.json"),
    "系统设置": os.path.join("Config", "SystemConfig.json"),
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
    "donLeft1P": "1P 左咚",
    "donRight1P": "1P 右咚",
    "kaLeft1P": "1P 左咔",
    "kaRight1P": "1P 右咔",
    "donLeft2P": "2P 左咚",
    "donRight2P": "2P 右咚",
    "kaLeft2P": "2P 左咔",
    "kaRight2P": "2P 右咔",
    "setFavoriteKeys": "收藏键",
    "setMouseModeKeys": "鼠标模式键",
    "quickRetryKey": "快速重试键",
    "quickBackKey": "快速返回键",
    "deviceName": "设备名称",
    "type": "类型",
    "key": "键盘按键",
    "button": "手柄按钮",
}

SECTION_NAMES = {
    "account": "账号设置",
    "paths": "路径设置",
    "display": "显示设置",
    "audio": "音量设置",
    "keys": "按键绑定",
    "device": "设备设置",
    "config": "按键及其他配置",
    "other": "其他设置",
}

KEY_GROUP_NAMES = {
    "1p": "1P",
    "2p": "2P",
    "system": "系统相关",
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
        layout.setSpacing(6)

        self.edit = QLineEdit()
        self.edit.setText(self.format_value(value))
        self.edit.setObjectName("pathEdit")

        self.button = QPushButton("选择目录")
        self.button.setObjectName("smallButton")
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
            normalized = rel + "/" if not rel.endswith("/") else rel
            self.edit.setText(json.dumps([normalized], ensure_ascii=False))
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
        self.setObjectName("keyBindButton")
        self.setText(self.display_text())
        self.clicked.connect(self.start_capture)
        self.setFocusPolicy(Qt.StrongFocus)

    def display_text(self):
        return "按下键盘按键..." if self.waiting else self.key_text

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
        self.section_forms = {}
        self.section_counts = {}
        self.build_ui()
        self.load()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.path_label = QLabel(self.path)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setObjectName("pathLabel")
        layout.addWidget(self.path_label)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sectionList")
        self.sidebar.setFixedWidth(132)
        self.sidebar.currentRowChanged.connect(self.switch_section)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("sectionStack")
        body.addWidget(self.stack, 1)

        layout.addLayout(body, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 9, 16, 9)
        footer.setSpacing(8)
        self.status_label = QLabel("已加载配置文件")
        self.status_label.setObjectName("statusLabel")
        footer.addWidget(self.status_label, 1)

        self.reload_button = QPushButton("重新加载")
        self.reload_button.setObjectName("secondaryButton")
        self.reload_button.clicked.connect(self.load)
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.save)
        footer.addWidget(self.reload_button)
        footer.addWidget(self.save_button)
        layout.addLayout(footer)

    def load(self):
        self.clear_sections()

        if not os.path.exists(self.path):
            self.add_message_section("状态", "未找到文件")
            self.status_label.setText("未找到配置文件")
            self.data = {}
            self.original_data = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8-sig") as file:
                self.data = json.load(file)
        except Exception as error:
            self.add_message_section("状态", f"读取失败: {error}")
            self.status_label.setText("读取配置失败")
            self.data = {}
            self.original_data = {}
            return

        self.original_data = deepcopy(self.data)
        self.add_fields(self.data)
        if self.sidebar.count():
            self.sidebar.setCurrentRow(0)
        self.status_label.setText("已加载配置文件")

    def clear_sections(self):
        self.widgets.clear()
        self.section_forms.clear()
        self.section_counts.clear()
        self.sidebar.clear()
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def switch_section(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)

    def add_message_section(self, title, message):
        form = self.ensure_section("other", title)
        form.addRow(QLabel(message))

    def add_fields(self, data, prefix=()):
        if not prefix and "username" in data and "password" in data:
            for key in ["username", "password"]:
                self.add_value(prefix + (key,), data[key], "account")

        for key, value in data.items():
            if not prefix and key in {"username", "password"}:
                continue

            path = prefix + (key,)
            if isinstance(value, dict):
                self.add_fields(value, path)
            elif isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                for index, item in enumerate(value):
                    for sub_key, sub_value in item.items():
                        self.add_value(path + (index, sub_key), sub_value)
            else:
                self.add_value(path, value)

    def ensure_section(self, section_key, title=None):
        if section_key in self.section_forms:
            return self.section_forms[section_key]

        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("sectionContent")
        page_layout = QVBoxLayout(content)
        page_layout.setContentsMargins(20, 16, 20, 20)
        page_layout.setSpacing(12)

        section_title = QLabel(title or SECTION_NAMES.get(section_key, section_key))
        section_title.setObjectName("sectionTitle")
        page_layout.addWidget(section_title)

        if section_key == "config":
            key_grid = QWidget()
            key_grid.setObjectName("keybindGrid")
            key_layout = QGridLayout(key_grid)
            key_layout.setContentsMargins(0, 0, 0, 0)
            key_layout.setHorizontalSpacing(10)
            key_layout.setVerticalSpacing(7)
            key_layout.setColumnStretch(0, 1)
            key_layout.setColumnStretch(1, 1)
            page_layout.addWidget(key_grid)
            self.section_forms["keys"] = key_layout

            other_title = QLabel("其他")
            other_title.setObjectName("keyGroupHeader")
            page_layout.addWidget(other_title)

        form_host = QWidget()
        form_host.setObjectName("formHost")
        form = QFormLayout(form_host)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        page_layout.addWidget(form_host)

        page_layout.addStretch()

        page.setWidget(content)
        self.stack.addWidget(page)

        item = QListWidgetItem(title or SECTION_NAMES.get(section_key, section_key))
        self.sidebar.addItem(item)
        self.section_forms[section_key] = form
        return form

    def add_value(self, path, value, section_key=None):
        if self.is_hidden_key_field(path):
            return

        section_key = section_key or self.section_for_path(path)
        form = self.ensure_section(section_key)

        label = QLabel(self.label_for_path(path))
        label.setObjectName("fieldLabel")
        editor = self.create_editor(value, path)
        if self.is_keyboard_key_field(path):
            key_form = self.section_forms["keys"]
            self.add_key_group_header(key_form, path)

            row = QWidget()
            row.setObjectName("keybindRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(11, 6, 11, 6)
            row_layout.setSpacing(8)

            key_name = QLabel(self.label_for_key_path(path))
            key_name.setObjectName("keybindName")
            row_layout.addWidget(key_name, 1)
            row_layout.addWidget(editor)

            index = self.section_counts.get("keys", 0)
            key_form.addWidget(row, index // 2, index % 2)
            self.section_counts["keys"] = index + 1
        else:
            form.addRow(label, editor)

    def is_hidden_key_field(self, path):
        return self.is_key_config_field(path) and str(path[-1]).lower() in {"type", "button"}

    def is_keyboard_key_field(self, path):
        return self.is_key_config_field(path) and str(path[-1]).lower() == "key"

    def is_key_config_field(self, path):
        last = str(path[-1]).lower()
        return "key" in last or last in {"button", "type"}

    def key_group_for_path(self, path):
        text = "/".join(str(part).lower() for part in path if not isinstance(part, int))
        if "1p" in text:
            return "1p"
        if "2p" in text:
            return "2p"
        return "system"

    def add_key_group_header(self, form, path):
        group = self.key_group_for_path(path)
        marker_key = f"keys:{group}:header"
        if marker_key in self.section_counts:
            return

        index = self.section_counts.get("keys", 0)
        if index % 2:
            index += 1

        header = QLabel(KEY_GROUP_NAMES[group])
        header.setObjectName("keyGroupHeader")
        form.addWidget(header, index // 2, 0, 1, 2)
        self.section_counts[marker_key] = 1
        self.section_counts["keys"] = index + 2

    def section_for_path(self, path):
        keys = [str(part) for part in path if not isinstance(part, int)]
        lowered = [key.lower() for key in keys]
        last = lowered[-1] if lowered else ""

        if last in {"username", "password"}:
            return "account"
        if "path" in last:
            return "paths"
        if last in {"fullscreen", "resolution", "targetfps", "vsync", "showfps"}:
            return "display"
        if "volume" in last:
            return "audio"
        if "key" in last or last in {"button", "type"}:
            return "config"
        if "device" in last:
            return "device"
        return "config"

    def label_for_path(self, path):
        parts = [part for part in path if not isinstance(part, int)]
        translated = [KEY_NAMES.get(part, str(part)) for part in parts]
        return " / ".join(translated)

    def label_for_key_path(self, path):
        parts = [part for part in path if not isinstance(part, int)]
        if parts and parts[-1] == "key":
            parts = parts[:-1]
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
        editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if isinstance(editor, KeyBindEditor):
            editor.setMinimumWidth(68)
            editor.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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
            self.status_label.setText(f"已保存 {os.path.basename(self.path)}")
            QMessageBox.information(self, "保存完成", f"已保存 {os.path.basename(self.path)}")
        except Exception as error:
            self.status_label.setText("保存失败")
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
        self.tab_buttons = {}
        self.current_config = None
        self.build_ui()
        self.apply_assets()

    def build_ui(self):
        self.setWindowTitle("TaikoNauts 配置编辑器")
        self.resize(980, 720)
        self.setMinimumSize(760, 540)

        central = QWidget()
        central.setObjectName("mainWidget")
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(0)

        shell = QWidget()
        shell.setObjectName("appShell")
        outer.addWidget(shell)

        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titlebar = QHBoxLayout()
        titlebar.setContentsMargins(16, 9, 16, 9)
        titlebar.setSpacing(10)

        icon = QLabel()
        icon.setObjectName("titleIcon")
        icon.setFixedSize(20, 20)
        title = QLabel("TaikoNauts 配置编辑器")
        title.setObjectName("titleText")
        version = QLabel("v1.0")
        version.setObjectName("titleSub")

        titlebar.addWidget(icon)
        titlebar.addWidget(title)
        titlebar.addStretch()
        titlebar.addWidget(version)
        layout.addLayout(titlebar)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 8, 16, 8)
        toolbar.setSpacing(8)

        label = QLabel("游戏目录")
        label.setObjectName("toolbarLabel")
        self.root_label = QLabel(self.root)
        self.root_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.root_label.setObjectName("rootLabel")

        choose_button = QPushButton("选择目录")
        choose_button.setObjectName("secondaryButton")
        choose_button.clicked.connect(self.choose_root)
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.reload_all)
        launch_button = QPushButton("▶ 启动游戏")
        launch_button.setObjectName("primaryButton")
        launch_button.clicked.connect(self.launch_game)

        toolbar.addWidget(label)
        toolbar.addWidget(self.root_label, 1)
        toolbar.addWidget(choose_button)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(launch_button)
        layout.addLayout(toolbar)

        tabbar = QHBoxLayout()
        tabbar.setContentsMargins(16, 0, 16, 0)
        tabbar.setSpacing(0)
        self.tabbar_host = QWidget()
        self.tabbar_host.setObjectName("tabbarHost")
        self.tabbar_host.setLayout(tabbar)
        layout.addWidget(self.tabbar_host)

        self.editor_stack = QStackedWidget()
        self.editor_stack.setObjectName("editorStack")
        layout.addWidget(self.editor_stack, 1)

        self.reload_all()

    def reload_all(self):
        self.editors.clear()
        self.tab_buttons.clear()

        while self.editor_stack.count():
            widget = self.editor_stack.widget(0)
            self.editor_stack.removeWidget(widget)
            widget.deleteLater()

        tab_layout = self.tabbar_host.layout()
        while tab_layout.count():
            item = tab_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for index, (name, rel_path) in enumerate(CONFIG_FILES.items()):
            path = os.path.normpath(os.path.join(self.root, rel_path))
            editor = JsonConfigEditor(path, self.root)
            self.editors[name] = editor
            self.editor_stack.addWidget(editor)

            button = QPushButton(name)
            button.setCheckable(True)
            button.setObjectName("tabButton")
            button.clicked.connect(lambda checked=False, tab_name=name: self.switch_config(tab_name))
            tab_layout.addWidget(button)
            self.tab_buttons[name] = button

            if index == 0:
                self.current_config = name

        tab_layout.addStretch()
        if self.current_config not in self.editors:
            self.current_config = next(iter(self.editors), None)
        if self.current_config:
            self.switch_config(self.current_config)

    def switch_config(self, name):
        editor = self.editors.get(name)
        if editor is None:
            return
        self.current_config = name
        self.editor_stack.setCurrentWidget(editor)
        for tab_name, button in self.tab_buttons.items():
            button.setChecked(tab_name == name)

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
            QMessageBox.warning(self, "启动失败", f"未找到 {exe_path}")
            return
        if not QProcess.startDetached(exe_path, [], self.root):
            QMessageBox.warning(self, "启动失败", "无法启动游戏。")

    def apply_assets(self):
        icon_path = os.path.join(self.root, ICON_REL)
        background_path = os.path.join(self.root, BACKGROUND_REL)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        background = (
            "background-color: #f7ece3;"
            "background-image: repeating-linear-gradient(45deg, rgba(226,75,74,0.08) 0px, "
            "rgba(226,75,74,0.08) 2px, transparent 2px, transparent 20px);"
        )
        if os.path.exists(background_path):
            background = (
                f'background-image: url("{to_qss_path(background_path)}");'
                "background-position: center;"
                "background-repeat: repeat;"
                "background-size: 380px auto;"
            )

        self.setStyleSheet(
            f"""
            QWidget#mainWidget {{
                {background}
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 10pt;
                color: #3a2010;
            }}
            QWidget#appShell {{
                background: rgba(255, 252, 248, 205);
                border: 1px solid rgba(210, 180, 160, 130);
                border-radius: 8px;
            }}
            QLabel#titleIcon {{
                background: #e24b4a;
                border-radius: 4px;
            }}
            QLabel#titleText {{
                color: #3a2a20;
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#titleSub {{
                color: #a08070;
                font-size: 12px;
            }}
            QLabel#toolbarLabel {{
                color: #7a6050;
                font-size: 12px;
            }}
            QLabel#rootLabel, QLabel#pathLabel {{
                background: rgba(255, 245, 235, 205);
                border: 1px solid rgba(200, 160, 130, 100);
                border-radius: 6px;
                color: #7a6050;
                font-family: Consolas, "Microsoft YaHei", monospace;
                font-size: 11px;
                padding: 5px 10px;
            }}
            QLabel#pathLabel {{
                border-left: none;
                border-right: none;
                border-radius: 0;
                padding: 7px 16px;
            }}
            QWidget#tabbarHost {{
                background: rgba(255, 245, 235, 155);
                border-top: 1px solid rgba(210, 170, 140, 90);
                border-bottom: 1px solid rgba(210, 170, 140, 90);
            }}
            QPushButton#tabButton {{
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0;
                color: #9a7060;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton#tabButton:checked {{
                color: #3a2010;
                border-bottom-color: #e24b4a;
                font-weight: 600;
            }}
            QStackedWidget#editorStack {{
                background: transparent;
            }}
            QListWidget#sectionList {{
                background: rgba(255, 245, 235, 155);
                border: none;
                border-right: 1px solid rgba(210, 170, 140, 80);
                outline: none;
                padding: 10px 0;
            }}
            QListWidget#sectionList::item {{
                color: #9a7060;
                padding: 7px 16px;
                border-left: 2px solid transparent;
                min-height: 24px;
            }}
            QListWidget#sectionList::item:selected {{
                background: rgba(255, 240, 225, 205);
                border-left-color: #e24b4a;
                color: #3a1a10;
                font-weight: 600;
            }}
            QWidget#sectionContent, QScrollArea {{
                background: rgba(255, 252, 248, 65);
                border: none;
            }}
            QLabel#sectionTitle {{
                color: #b07050;
                border-bottom: 1px solid rgba(200, 160, 130, 80);
                font-size: 11px;
                font-weight: 600;
                padding-bottom: 7px;
                text-transform: uppercase;
            }}
            QLabel#fieldLabel {{
                color: #8a6050;
                font-size: 12px;
                padding-top: 7px;
            }}
            QWidget#keybindRow {{
                background: rgba(255, 245, 235, 190);
                border: 1px solid rgba(200, 160, 130, 90);
                border-radius: 6px;
            }}
            QLabel#keybindName {{
                color: #8a6050;
                font-size: 12px;
                background: transparent;
            }}
            QLabel#keyGroupHeader {{
                background: #fcebeb;
                border-radius: 6px;
                color: #a32d2d;
                font-size: 11px;
                font-weight: 600;
                margin-top: 4px;
                padding: 3px 10px;
            }}
            QLabel#statusLabel {{
                color: #9a7060;
                font-size: 12px;
            }}
            QLineEdit, QComboBox {{
                background: rgba(255, 248, 240, 220);
                border: 1px solid rgba(200, 155, 120, 115);
                border-radius: 6px;
                color: #3a2010;
                min-height: 26px;
                padding: 5px 9px;
            }}
            QLineEdit#pathEdit {{
                font-family: Consolas, "Microsoft YaHei", monospace;
                font-size: 11px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: #e24b4a;
                background: rgba(255, 252, 248, 240);
            }}
            QPushButton {{
                background: rgba(255, 245, 235, 220);
                border: 1px solid rgba(200, 150, 120, 125);
                border-radius: 6px;
                color: #4a3020;
                padding: 6px 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 230, 210, 240);
            }}
            QPushButton#smallButton {{
                padding: 5px 10px;
                font-size: 12px;
            }}
            QPushButton#primaryButton {{
                background: #e24b4a;
                border-color: #e24b4a;
                color: white;
            }}
            QPushButton#primaryButton:hover {{
                background: #c83938;
                border-color: #c83938;
            }}
            QPushButton#keyBindButton {{
                background: rgba(255, 252, 248, 225);
                border: 1px solid rgba(200, 150, 120, 125);
                border-radius: 4px;
                color: #4a2010;
                font-family: Consolas, "Microsoft YaHei", monospace;
                font-size: 12px;
                min-width: 68px;
                min-height: 22px;
                padding: 2px 8px;
            }}
            QPushButton#keyBindButton:hover {{
                background: rgba(255, 238, 224, 240);
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
