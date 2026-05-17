# Windows 桌面 AI 伴侣 — HermesPet-Win

## 目标
基于 HermesPet (macOS) 的设计思路，创建一个**纯 Python** 的 Windows 桌面 AI 伴侣，保留灵动岛 + 事件驱动核心体验。

## 用户需求
- **标准版功能**：桌面宠物 + AI 聊天 + 灵动岛 + 事件执行 + 文件拖拽 + 语音 + 全局快捷键
- **AI 后端**：支持 mimo API / NVIDIA API（均为 OpenAI 兼容格式）
- **硬件环境**：Windows，16G 内存，6G 显存 4050

---

## 技术架构

```
Python 主程序 (tkinter)
├── 配置管理 (config.json)
├── 灵动岛 UI (DynamicIsland) — 顶部浮动胶囊
│   ├── 左耳: 像素精灵 (PIL 动画)
│   ├── 右耳: 状态指示器 (脉冲/步骤/完成)
│   └── Hover 展开: 显示最近回复预览
├── 聊天窗口 (ChatWindow) — AI 对话界面
│   ├── Markdown 渲染
│   ├── 文件拖拽区
│   └── 输入框 + 发送按钮
├── 桌面宠物 (PetSprite) — 像素精灵漫游
│   ├── 状态动画 (idle/blink/walk/eat)
│   └── 鼠标交互 (hover→跑过来)
├── AI 客户端 (AIClient) — OpenAI 兼容
│   ├── mimo API
│   └── NVIDIA API
├── 事件引擎 (EventEngine)
│   ├── 命令包装器 (wrap)
│   ├── 事件记录 (jobs.json)
│   └── 状态广播
├── 系统托盘 (pystray)
├── 全局快捷键 (keyboard)
└── 语音输入 (可选, speech_recognition)
```

## 依赖

```
pip install pystray pillow keyboard requests markdown speech_recognition pyperclip
```

- `tkinter` — 内置，UI 框架
- `pystray` — 系统托盘
- `Pillow` — 图像处理 + 像素精灵
- `keyboard` — 全局热键
- `requests` — API 调用
- `markdown` — Markdown 渲染
- `speech_recognition` — 语音输入（可选）

## 核心文件结构

```
C:\Users\李振\WorkBuddy\2026-05-17-task-5\hermes-pet-win\
├── main.py                 # 主入口，启动所有组件
├── config.py               # 配置管理 (API key, model, 偏好)
├── ai_client.py            # OpenAI 兼容客户端 (mimo/NVIDIA)
├── dynamic_island.py       # 灵动岛 UI (顶部胶囊)
├── chat_window.py          # AI 聊天窗口
├── pet_sprite.py           # 桌面像素宠物
├── event_engine.py         # 事件引擎 (wrap命令/记录状态)
├── tray.py                 # 系统托盘
├── hotkeys.py              # 全局快捷键
├── assets/                 # 像素精灵图片
│   ├── pet_idle.png
│   ├── pet_blink.png
│   ├── pet_walk1.png
│   └── pet_walk2.png
└── config.json             # 用户配置 (自动生成)
```

## 功能清单

### 1. 灵动岛 (DynamicIsland)
- 顶部居中浮动胶囊，置顶显示
- 左耳：像素精灵图标（Hermes 羽毛 / AI 云朵）
- 右耳：状态指示器
  - 空闲：静止
  - 处理中：旋转脉冲（蓝色）
  - 完成：绿色对勾 ✓
  - 错误：琥珀色 + 点击重试
- 鼠标 hover → 胶囊展开，显示最近回复预览（截断50字）
- 支持拖拽移动位置

### 2. AI 聊天窗口 (ChatWindow)
- 快捷键 `Ctrl+Shift+H` 呼出/收回
- Markdown 渲染（标题/粗体/列表/代码块/表格）
- 流式输出（SSE）
- 文件拖拽上传（读取内容作为上下文）
- 对话历史持久化（conversations.json）

### 3. 桌面宠物 (PetSprite)
- 像素风格小精灵，屏幕右下角漫游
- 动画状态：idle（眨眼）、walk（左右走）、eat（吃文件）、happy（完成任务）
- 鼠标靠近 → 小跑过来打招呼
- 拖文件给宠物 → 嚼嚼吞下 → 自动发给 AI

### 4. 事件引擎 (EventEngine)
- `hermes-pet wrap --name "测试" -- pytest` 包装命令
- 自动记录：开始时间、结束时间、耗时、退出码、状态
- 事件类型：job_started / job_finished / job_failed / approval_needed
- 事件写入 ~/.hermes_pet/jobs.json
- 灵动岛实时反映状态

### 5. 系统托盘
- 菜单：打开聊天 / 查看状态 / 设置 / 退出
- 图标随状态变化（空闲/处理中/错误）

### 6. 全局快捷键
| 快捷键 | 功能 |
|--------|------|
| Ctrl+Shift+H | 呼出/收回聊天窗口 |
| Ctrl+Shift+J | 截屏附加到对话 |
| Ctrl+Shift+Enter | 快速发送当前输入 |

### 7. AI 客户端
- OpenAI 兼容格式，支持流式
- 预设：mimo API / NVIDIA API
- 配置文件存储 API key 和 model

---

## 实现步骤

1. **创建项目目录和配置系统** (config.py)
2. **实现 AI 客户端** (ai_client.py) — 流式调用 OpenAI 兼容 API
3. **创建像素精灵图片** (PIL 生成简单像素图)
4. **实现灵动岛 UI** (dynamic_island.py) — tkinter 浮动胶囊
5. **实现桌面宠物** (pet_sprite.py) — 动画 + 鼠标交互
6. **实现聊天窗口** (chat_window.py) — Markdown 渲染 + 流式输出
7. **实现事件引擎** (event_engine.py) — 命令包装 + 状态记录
8. **实现系统托盘** (tray.py)
9. **实现全局快捷键** (hotkeys.py)
10. **主程序整合** (main.py)

## 输出
- 可直接运行的完整 Python 项目
- `python main.py` 一键启动
- 首次运行自动生成配置模板，用户填入 API Key 即可使用
