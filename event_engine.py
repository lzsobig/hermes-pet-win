"""事件引擎 — 命令包装器 + 状态记录 + 事件广播"""
import subprocess
import threading
import time
import json
import os
from datetime import datetime
from config import load_jobs, save_jobs, CONFIG_DIR


class EventEngine:
    """事件引擎：包装命令执行，记录状态，广播事件"""

    def __init__(self, on_event=None):
        self.on_event = on_event  # 回调：on_event(event_type, data)
        self.jobs = load_jobs()
        self._running_job = None

    def wrap_command(self, name: str, command: str, cwd: str = None):
        """包装执行一个命令，自动记录开始/结束/失败"""
        def _worker():
            job = {
                "id": len(self.jobs) + 1,
                "name": name,
                "command": command,
                "status": "running",
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "duration": None,
                "exit_code": None,
                "output": "",
                "error": "",
            }
            self.jobs.append(job)
            self._running_job = job
            self._emit("job_started", job)

            try:
                start = time.time()
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    cwd=cwd, timeout=300
                )
                duration = time.time() - start

                job["end_time"] = datetime.now().isoformat()
                job["duration"] = round(duration, 2)
                job["exit_code"] = result.returncode
                job["output"] = result.stdout[-2000:] if result.stdout else ""
                job["error"] = result.stderr[-2000:] if result.stderr else ""

                if result.returncode == 0:
                    job["status"] = "succeeded"
                    self._emit("job_finished", job)
                else:
                    job["status"] = "failed"
                    self._emit("job_failed", job)

            except subprocess.TimeoutExpired:
                job["status"] = "timeout"
                job["end_time"] = datetime.now().isoformat()
                job["error"] = "命令超时（300秒）"
                self._emit("job_failed", job)
            except Exception as e:
                job["status"] = "error"
                job["end_time"] = datetime.now().isoformat()
                job["error"] = str(e)
                self._emit("job_failed", job)
            finally:
                self._running_job = None
                save_jobs(self.jobs)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def emit_event(self, event_type: str, data: dict = None):
        """手动发射一个事件"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }
        self._emit(event_type, event)

    def get_recent_jobs(self, limit: int = 10) -> list:
        """获取最近的任务"""
        return self.jobs[-limit:]

    def get_failed_jobs(self, limit: int = 5) -> list:
        """获取最近失败的任务"""
        failed = [j for j in self.jobs if j["status"] == "failed"]
        return failed[-limit:]

    def get_job_summary(self) -> str:
        """生成任务摘要"""
        if not self.jobs:
            return "暂无任务记录"

        recent = self.jobs[-5:]
        lines = []
        for j in recent:
            status_icon = {"succeeded": "✓", "failed": "✗",
                           "running": "⟳", "timeout": "⏰"}.get(j["status"], "?")
            dur = f"{j['duration']}s" if j.get("duration") else "..."
            lines.append(f"  {status_icon} {j['name']} ({dur})")
        return "\n".join(lines)

    def _emit(self, event_type: str, data: dict):
        """内部事件发射"""
        if self.on_event:
            try:
                self.on_event(event_type, data)
            except Exception:
                pass
