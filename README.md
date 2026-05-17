# Hermes Pet Win

Windows 桌面 AI 伴侣 —— 灵动岛 + 像素宠物 + Claude Code / mimo / NVIDIA API

基于 macOS [HermesPet](https://github.com/basionwang-bot/HermesPet) 的设计思路，用纯 Python (tkinter) 实现的 Windows 版本。

## Features

- **Dynamic Island** — 顶部浮动胶囊，实时显示 AI 状态，hover 展开预览
- **Pixel Pet** — 桌面像素小猫，idle 眨眼 / walk 闲逛 / eat 吃文件 / happy 开心动画
- **AI Chat** — Markdown 渲染，流式输出，文件拖拽
- **Event Engine** — 命令包装器，自动记录任务状态
- **System Tray** — 托盘图标 + 状态指示
- **Global Hotkeys** — Ctrl+Shift+H 呼出聊天

## AI Backend

支持两种后端，启动时选择：

| Backend | 说明 |
|---------|------|
| **Claude Code** | 直接调用本地 `claude` CLI，零配置 |
| **OpenAI API** | 填入 API Key，支持 mimo / NVIDIA / DeepSeek 等 |

## Quick Start

```bash
# 安装依赖
pip install pystray Pillow keyboard requests markdown

# 运行
python main.py
```

需要 Python 3.10+ 和 tkinter。

## Requirements

- Python 3.10+
- tkinter (Python 默认包含)
- Claude Code CLI (可选，用于 Claude Code 后端)

## License

MIT
