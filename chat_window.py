"""AI 聊天窗口 — Markdown 渲染 + 流式输出 + 文件拖拽"""
import tkinter as tk
from tkinter import scrolledtext, filedialog
import json
import os
import re


class ChatWindow:
    """AI 聊天主窗口"""

    def __init__(self, root: tk.Tk, config: dict, ai_client=None,
                 on_state_change=None):
        self.root = root
        self.config = config
        self.ai_client = ai_client
        self.on_state_change = on_state_change
        self.messages = []  # 对话历史
        self.is_visible = False
        self._stream_buf = ""

        self._build_ui()

    def _build_ui(self):
        """构建聊天窗口 UI"""
        self.frame = tk.Frame(self.root, bg="#0f0f23")

        # 顶部栏
        top_bar = tk.Frame(self.frame, bg="#1a1a2e", pady=8, padx=12)
        top_bar.pack(fill="x")

        tk.Label(top_bar, text="✦ Hermes AI", fg="#e2e8f0",
                 bg="#1a1a2e", font=("Segoe UI", 12, "bold")).pack(side="left")

        tk.Button(top_bar, text="✕", fg="#94a3b8", bg="#1a1a2e",
                  font=("Segoe UI", 11), bd=0, relief="flat",
                  activebackground="#2d2d44", activeforeground="#e2e8f0",
                  command=self.hide).pack(side="right")

        tk.Button(top_bar, text="清空", fg="#94a3b8", bg="#1a1a2e",
                  font=("Segoe UI", 9), bd=0, relief="flat",
                  activebackground="#2d2d44", activeforeground="#e2e8f0",
                  command=self.clear_chat).pack(side="right", padx=(0, 8))

        tk.Button(top_bar, text="📎 附件", fg="#94a3b8", bg="#1a1a2e",
                  font=("Segoe UI", 9), bd=0, relief="flat",
                  activebackground="#2d2d44", activeforeground="#e2e8f0",
                  command=self._attach_file).pack(side="right", padx=(0, 8))

        # 对话区
        self.chat_area = scrolledtext.ScrolledText(
            self.frame, wrap="word", bg="#0f0f23", fg="#e2e8f0",
            font=("Consolas", 10), insertbackground="#e2e8f0",
            selectbackground="#2d2d44", relief="flat", padx=16, pady=12,
            state="disabled"
        )
        self.chat_area.pack(fill="both", expand=True)

        # Markdown 标签样式
        self.chat_area.tag_configure("user_msg", foreground="#7dd3fc",
                                     font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("ai_msg", foreground="#e2e8f0")
        self.chat_area.tag_configure("code_block", background="#1e1e3f",
                                     foreground="#a5f3fc",
                                     font=("Consolas", 10),
                                     lmargin1=20, lmargin2=20, rmargin=20)
        self.chat_area.tag_configure("heading", foreground="#f0abfc",
                                     font=("Segoe UI", 12, "bold"))
        self.chat_area.tag_configure("bold", foreground="#fbbf24",
                                     font=("Consolas", 10, "bold"))
        self.chat_area.tag_configure("bullet", foreground="#4ade80",
                                     lmargin1=20, lmargin2=30)
        self.chat_area.tag_configure("error", foreground="#f87171")

        # 输入区
        input_frame = tk.Frame(self.frame, bg="#1a1a2e", pady=8, padx=12)
        input_frame.pack(fill="x")

        self.input_box = tk.Text(input_frame, height=3, bg="#2d2d44",
                                  fg="#e2e8f0", font=("Segoe UI", 10),
                                  insertbackground="#e2e8f0",
                                  relief="flat", padx=12, pady=8,
                                  wrap="word")
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        send_btn = tk.Button(input_frame, text="发送", fg="#0f0f23",
                             bg="#7dd3fc", font=("Segoe UI", 10, "bold"),
                             relief="flat", padx=16, pady=6,
                             activebackground="#38bdf8",
                             command=self.send_message)
        send_btn.pack(side="right", padx=(8, 0))

    def _on_enter(self, event):
        """Enter 发送，Shift+Enter 换行"""
        if not (event.state & 0x1):
            self.send_message()
            return "break"

    def show(self):
        """显示聊天窗口"""
        self.frame.pack(fill="both", expand=True)
        self.is_visible = True
        self.input_box.focus_set()

    def hide(self):
        """隐藏聊天窗口"""
        self.frame.pack_forget()
        self.is_visible = False

    def toggle(self):
        """切换显示/隐藏"""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def clear_chat(self):
        """清空对话"""
        self.messages.clear()
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.config(state="disabled")

    def _append_text(self, text: str, tag: str = None):
        """追加文本到聊天区 - 批量更新减少刷新次数"""
        self.chat_area.config(state="normal")
        if tag:
            self.chat_area.insert("end", text, tag)
        else:
            self.chat_area.insert("end", text)
        self.chat_area.config(state="disabled")
        self.chat_area.see("end")

    def _render_markdown_line(self, line: str):
        """简单 Markdown 单行渲染"""
        if line.startswith("### "):
            self._append_text(line[4:] + "\n", "heading")
        elif line.startswith("## "):
            self._append_text(line[3:] + "\n", "heading")
        elif line.startswith("# "):
            self._append_text(line[2:] + "\n", "heading")
        elif line.startswith("```"):
            return  # 代码块边界，跳过
        elif line.startswith("- ") or line.startswith("* "):
            self._append_text(f"  • {line[2:]}\n", "bullet")
        elif re.match(r"^\d+\.\s", line):
            self._append_text(f"  {line}\n", "bullet")
        else:
            # 粗体处理
            parts = re.split(r"\*\*(.*?)\*\*", line)
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    self._append_text(part, "bold")
                else:
                    self._append_text(part, "ai_msg")
            self._append_text("\n")

    def _render_markdown(self, text: str):
        """渲染完整 Markdown 文本"""
        in_code = False
        for line in text.split("\n"):
            if line.strip().startswith("```"):
                if in_code:
                    self._append_text("\n", "code_block")
                    in_code = False
                else:
                    in_code = True
                continue
            if in_code:
                self._append_text(line + "\n", "code_block")
            else:
                self._render_markdown_line(line)

    def send_message(self):
        """发送用户消息"""
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            return

        self.input_box.delete("1.0", "end")

        # 显示用户消息
        self._append_text(f"\n  你: ", "user_msg")
        self._append_text(f"{text}\n\n", "user_msg")

        # 添加到对话历史
        self.messages.append({"role": "user", "content": text})

        # 通知状态变化
        if self.on_state_change:
            self.on_state_change("thinking")

        # 流式调用 AI
        if self.ai_client:
            self._stream_buf = ""
            self._append_text("  AI: ", "ai_msg")
            
            # 批量累积 chunk 减少 UI 刷新次数
            chunk_buffer = []
            buffer_size = 4  # 每 4 个字符刷新一次

            def flush_buffer():
                nonlocal chunk_buffer
                if chunk_buffer:
                    text_to_add = "".join(chunk_buffer)
                    self.root.after(0, lambda: self._append_text(text_to_add, "ai_msg"))
                    chunk_buffer = []

            def on_chunk(chunk, full):
                chunk_buffer.append(chunk)
                if len(chunk_buffer) >= buffer_size:
                    flush_buffer()

            def on_done(full):
                flush_buffer()  # 刷新剩余缓冲
                self.messages.append({"role": "assistant", "content": full})
                if self.on_state_change:
                    self.root.after(0, lambda: self.on_state_change("done", full))

            def on_error(err):
                flush_buffer()  # 清空缓冲
                self.root.after(0, lambda: self._append_text(
                    f"\n  [错误] {err}\n", "error"))
                if self.on_state_change:
                    self.root.after(0, lambda: self.on_state_change("error"))

            self.ai_client.chat_stream(self.messages,
                                       on_chunk=on_chunk,
                                       on_done=on_done,
                                       on_error=on_error)
        else:
            self._append_text("  [未配置 API]\n", "error")

    def _attach_file(self):
        """附加文件到对话"""
        filepath = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("文本文件", "*.txt *.md *.py *.json *.csv *.log"),
                       ("所有文件", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(8000)
                fname = os.path.basename(filepath)
                self._append_text(f"\n  📎 已附加: {fname}\n\n", "bold")
                self.messages.append({
                    "role": "user",
                    "content": f"[附件: {fname}]\n{content}"
                })
            except Exception as e:
                self._append_text(f"\n  [读取失败] {e}\n", "error")
