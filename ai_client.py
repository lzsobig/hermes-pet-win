"""AI 客户端 — 支持 OpenAI API / Claude Code 双模式"""
import json
import requests
import threading
import subprocess
import os
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor


class AIClient:
    def __init__(self, config: dict):
        self.base_url = config["api"]["base_url"]
        self.api_key = config["api"]["api_key"]
        self.model = config["api"]["model"]
        self.max_tokens = config["api"]["max_tokens"]
        self.temperature = config["api"]["temperature"]
        self.backend = config["api"].get("backend", "openai")
        # 连接池复用
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=3)

    def update_config(self, config: dict):
        self.base_url = config["api"]["base_url"]
        self.api_key = config["api"]["api_key"]
        self.model = config["api"]["model"]
        self.max_tokens = config["api"]["max_tokens"]
        self.temperature = config["api"]["temperature"]
        self.backend = config["api"].get("backend", "openai")
        # 更新 session headers
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
        })

    def chat_stream(self, messages: list, on_chunk=None, on_done=None, on_error=None):
        """流式调用 AI"""
        if self.backend == "claude":
            self._claude_stream(messages, on_chunk, on_done, on_error)
        else:
            self._openai_stream(messages, on_chunk, on_done, on_error)

    def _openai_stream(self, messages, on_chunk, on_done, on_error):
        """OpenAI 兼容 API 流式"""
        def _worker():
            try:
                url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": True,
                }
                resp = self._session.post(url, json=payload, stream=True, timeout=120)
                resp.raise_for_status()

                full_text = ""
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if not line_str.startswith("data: "):
                        continue
                    data_str = line_str[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_text += content
                            if on_chunk:
                                on_chunk(content, full_text)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

                if on_done:
                    on_done(full_text)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def _claude_stream(self, messages, on_chunk, on_done, on_error):
        """Claude Code CLI 流式（通过 -p 非交互模式）"""
        def _worker():
            try:
                # 把消息历史转成单个 prompt
                prompt_parts = []
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "user":
                        prompt_parts.append(f"Human: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
                prompt = "\n\n".join(prompt_parts)

                # 查找 claude 命令
                claude_cmd = self._find_claude()
                if not claude_cmd:
                    if on_error:
                        on_error("Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code")
                    return

                # 调用 claude -p
                proc = subprocess.Popen(
                    [claude_cmd, "-p", prompt],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env={**os.environ, "NODE_TLS_REJECT_UNAUTHORIZED": "0"},
                )

                full_text = ""
                for line in proc.stdout:
                    if line:
                        full_text += line
                        if on_chunk:
                            on_chunk(line, full_text)

                proc.wait()
                if proc.returncode != 0:
                    stderr = proc.stderr.read()
                    if on_error and stderr.strip():
                        on_error(stderr.strip())
                elif on_done:
                    on_done(full_text)

            except Exception as e:
                if on_error:
                    on_error(str(e))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def _find_claude(self) -> str:
        """查找 claude 可执行文件路径"""
        import shutil
        # 先找 PATH 里的
        path = shutil.which("claude")
        if path:
            return path
        # 常见路径 (缓存结果避免重复查找)
        if not hasattr(self, '_claude_path_cache'):
            self._claude_path_cache = None
            candidates = [
                os.path.expanduser("~/.npm-global/bin/claude"),
                os.path.expanduser("~/node_modules/.bin/claude"),
                "C:/npm-global/claude.cmd",
                "C:/npm-global/claude",
                "/usr/local/bin/claude",
            ]
            for c in candidates:
                if os.path.exists(c):
                    self._claude_path_cache = c
                    break
        return self._claude_path_cache or ""

    def chat_sync(self, messages: list) -> str:
        """同步调用"""
        if self.backend == "claude":
            return self._claude_sync(messages)
        return self._openai_sync(messages)

    def _openai_sync(self, messages) -> str:
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False,
            }
            url = f"{self.base_url}/chat/completions"
            resp = self._session.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Error] {e}"

    def _claude_sync(self, messages) -> str:
        try:
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    prompt_parts.append(f"Human: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            prompt = "\n\n".join(prompt_parts)

            claude_cmd = self._find_claude()
            if not claude_cmd:
                return "[Error] Claude Code CLI not found"

            result = subprocess.run(
                [claude_cmd, "-p", prompt],
                capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="replace",
                env={**os.environ, "NODE_TLS_REJECT_UNAUTHORIZED": "0"},
            )
            if result.returncode == 0:
                return result.stdout
            return f"[Error] {result.stderr}"
        except Exception as e:
            return f"[Error] {e}"
