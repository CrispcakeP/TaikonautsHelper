<p align="center">
  <img src="https://static.wikia.nocookie.net/taiko/images/1/15/Donmula_I.gif/revision/latest?cb=20210120145511&path-prefix=zh-hk" width="120" />
</p>

<h1 align="center">TaikøNautsConfigHelper a.k.a TCH</h1>

<p align="center">
  <strong>一个功能完整的 GUI 配置编辑工具，用于管理 TaikøNauts 游戏的各项设置</strong>
</p>


## 功能特性

- 🎮 **完整的配置管理**：支持编辑游戏配置和系统配置
- 🎯 **分类管理**：按账号、路径、显示、音量、按键等分类组织设置
- ⌨️ **按键绑定编辑器**：直观的按键捕获和编辑界面
- 📁 **目录选择器**：轻松选择和管理游戏路径
- 🎨 **自定义主题**：根据游戏资源动态加载背景和图标
- 🚀 **快速启动**：内置游戏启动功能
- 💾 **配置备份**：编辑前自动保留原始配置
- 🔄 **实时刷新**：支持重新加载配置文件

## 系统要求

- Python 3.8+
- PySide6
- Windows

## 安装

### 方式一：从源代码运行

1. 克隆或下载项目
2. 安装依赖：
```bash
pip install PySide6
```

3. 运行应用：
```bash
python config_editor.py
```

### 方式二：使用打包的 EXE（推荐）

```bash
python build_exe.py
```

打包完成后在 `dist` 目录下会生成 `TaikoNautsConfigEditor.exe`

## 使用指南

### 启动应用

**从源代码：**
```bash
python config_editor.py
```

**从 EXE：**
直接双击 `TaikoNautsConfigEditor.exe`

### 选择游戏目录

1. 点击工具栏中的 "选择目录" 按钮
2. 选择游戏的 `publish` 目录
3. 应用会自动检查配置文件是否存在

**默认搜索位置：**
- `D:\Taikonijiro\TaikoNauts-Beta-20260408\publish`
- 应用所在目录的上级目录
- 当前工作目录

### 编辑配置

#### 配置文件

- **游戏设置**：`Config/GameConfig.json` - 游戏相关配置
- **系统设置**：`Config/SystemConfig.json` - 系统相关配置

#### 配置分类

| 分类 | 说明 | 包含项目 |
|------|------|---------|
| 账号设置 | 账户信息 | 用户名、密码 |
| 路径设置 | 游戏路径 | 皮肤目录、歌曲目录 |
| 显示设置 | 图形相关 | 分辨率、全屏、FPS、垂直同步 |
| 音量设置 | 音频控制 | 主音量、音效、音乐、背景音乐、语音 |
| 按键绑定 | 控制映射 | 1P/2P 控制、系统按键 |
| 设备设置 | 设备配置 | 设备名称等 |

#### 按键绑定
- 点击按钮开始录制
- 按下想要绑定的键
- 按键将自动记录并显示

#### 其他数值
- 直接编辑输入框中的值
- 支持整数、浮点数和字符串

### 工具栏

| 组件 | 功能 |
|------|------|
| 游戏目录 | 显示当前游戏目录 |
| 选择目录 | 浏览并选择新的游戏目录 |
| 刷新 | 重新加载配置文件 |
| ▶ 启动游戏 | 启动 `TaikoNauts.exe` |

### 编辑区

- **左侧边栏**：配置分类列表
- **右侧编辑区**：当前分类的配置项
- **状态栏**：显示操作状态

### 按钮

| 按钮 | 功能 |
|------|------|
| 重新加载 | 丢弃更改，重新加载文件 |
| 保存 | 保存更改到文件 |

## 配置项详解

### 账号设置

```json
{
  "username": "玩家名称",
  "password": "密码"
}
```

### 路径设置

```json
{
  "skinPath": "相对路径/皮肤目录",
  "songPath": ["相对路径/歌曲目录/"]
}
```

### 显示设置

```json
{
  "fullscreen": true/false,
  "resolution": "1920x1080",
  "targetFPS": 60,
  "vSync": true/false,
  "showFPS": false
}
```

### 音量设置

```json
{
  "masterVolume": 100,
  "seVolume": 100,
  "musicVolume": 100,
  "bgmVolume": 100,
  "voiceVolume": 100
}
```

### 按键绑定

```json
{
  "keys": [
    {
      "deviceName": "Keyboard",
      "type": "keyboard",
      "key": "Z",
      "button": ""
    }
  ]
}
```

## 常见问题

### Q: 找不到配置文件？
A: 确保游戏目录下存在 `Config/GameConfig.json` 和 `Config/SystemConfig.json` 文件。使用 "选择目录" 按钮选择正确的游戏 `publish` 目录。

### Q: 修改后没有保存怎么办？
A: 点击 "保存" 按钮保存更改。点击 "重新加载" 可以丢弃未保存的更改。

### Q: EXE 没有显示自定义图标？
A: 确保 `icon.ico` 文件存在于 EXE 相同目录下，或者重新运行 `python build_exe.py` 重新打包。

### Q: 如何恢复原始设置？
A: 
1. 关闭编辑器
2. 从备份恢复原始配置文件
3. 重新打开编辑器

### Q: 支持游戏手柄吗？
A: 目前编辑器在 UI 上隐藏了手柄按钮字段。可以直接编辑 JSON 文件或在 `config_editor.py` 中修改 `is_hidden_key_field()` 方法。

## 文件结构

```
TaikoNautsHelper/
├── config_editor.py           # 主程序文件
├── build_exe.py               # EXE 打包脚本
├── icon.ico                   # 应用图标
├── requirements.txt           # 依赖列表
├── CONFIG_EDITOR_README.md    # 配置编辑器说明
└── dist/
    └── TaikoNautsConfigEditor.exe  # 打包后的可执行文件
```

## 技术栈

- **PySide6 / Qt for Python**：UI 框架
- **Python JSON**：配置文件解析
- **PyInstaller**：EXE 打包

## 配置优先级

应用按以下顺序搜索游戏目录：
1. 用户选择的目录
2. 代码中指定的默认目录
3. 应用目录
4. 应用上级目录
5. 当前工作目录

## 注意事项

- ⚠️ 编辑配置前建议备份原文件
- ⚠️ 请勿修改 JSON 文件格式，否则可能无法正常加载
- ⚠️ 某些配置修改需要重启游戏才能生效
- ⚠️ 按键绑定应为有效的键盘按键

## 故障排查

### 应用无法启动

1. 检查 Python 版本（需要 3.8+）
2. 确保已安装 PySide6：`pip install PySide6`
3. 查看命令行输出错误信息

### 配置无法保存

1. 检查文件权限（确保有写入权限）
2. 检查 JSON 格式是否正确
3. 确保磁盘空间充足

### 按键绑定无反应

1. 点击按钮后必须立即按下键
2. 确保没有其他应用占用按键
3. 某些特殊键可能不被支持

## 开发信息

### 添加新的配置分类

在 `SECTION_NAMES` 字典中添加新的分类：
```python
SECTION_NAMES = {
    "custom": "自定义分类",
}
```

### 自定义键名显示

在 `KEY_NAMES` 字典中添加新的键：
```python
KEY_NAMES = {
    "myKey": "我的键",
}
```

### 修改主题样式

编辑 `apply_assets()` 方法中的 QSS 样式表。

## 许可证

查看 LICENSE 文件了解许可证信息。

## 更新日志

### v1.0
- ✨ 初始版本发布
- ✨ 支持完整的配置编辑功能
- ✨ 按键绑定编辑器
- ✨ 游戏启动功能
- ✨ 自定义主题支持

## 反馈和贡献

如有问题或建议，欢迎提出反馈。

---

**最后更新**：2026年4月28日

