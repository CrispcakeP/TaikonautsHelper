#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建Windows可执行文件的脚本
使用PyInstaller打包
"""

import PyInstaller.__main__
import os
import sys

# 项目根目录
project_dir = os.path.dirname(os.path.abspath(__file__))

# 构建命令
build_args = [
    'config_editor.py',              # 主脚本
    '--name=TaikoNauts配置编辑器',    # 输出的exe名称
    '--onefile',                     # 打包成单个exe文件
    '--windowed',                    # 窗口模式（不显示控制台）
    '--clean',                       # 清理临时文件
    '--noconfirm',                   # 不询问确认
    # 注意：不使用 --add-data，配置文件由用户选择目录
]

# 如果有图标文件，可以添加
icon_path = os.path.join(project_dir, 'icon.ico')
if os.path.exists(icon_path):
    build_args.append(f'--icon={icon_path}')

# 执行打包
PyInstaller.__main__.run(build_args)

print("\n" + "="*50)
print("✓ 构建完成！")
print("="*50)
print(f"可执行文件位于: {os.path.join(project_dir, 'dist', 'TaikoNauts配置编辑器.exe')}")
print("\n使用说明:")
print("1. 将生成的exe文件复制到游戏根目录")
print("2. 或者运行exe后点击'选择目录'按钮选择游戏目录")
