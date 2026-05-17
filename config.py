"""配置管理 — API Key / Model / 偏好设置"""
import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".hermes_pet_win")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CONVERSATIONS_PATH = os.path.join(CONFIG_DIR, "conversations.json")
JOBS_PATH = os.path.join(CONFIG_DIR, "jobs.json")

DEFAULT_CONFIG = {
    "api": {
        "backend": "claude",
        "base_url": "http://model.mify.ai.srv/v1",
        "api_key": "",
        "model": "mimo-v2.5-pro",
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "pet": {
        "species": "cat",
        "position_x": -1,
        "position_y": -1,
    },
    "island": {
        "position_x": -1,
        "position_y": -1,
        "opacity": 0.95,
    },
    "hotkeys": {
        "toggle_chat": "ctrl+shift+h",
        "screenshot": "ctrl+shift+j",
        "quick_send": "ctrl+shift+enter",
    },
    "general": {
        "language": "zh",
        "auto_start": False,
        "sound_enabled": True,
    },
}


def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        merged = _deep_merge(DEFAULT_CONFIG, user_cfg)
        return merged
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    ensure_config_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_conversations() -> list:
    ensure_config_dir()
    if os.path.exists(CONVERSATIONS_PATH):
        with open(CONVERSATIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_conversations(convs: list):
    ensure_config_dir()
    with open(CONVERSATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(convs, f, indent=2, ensure_ascii=False)


def load_jobs() -> list:
    ensure_config_dir()
    if os.path.exists(JOBS_PATH):
        with open(JOBS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs: list):
    ensure_config_dir()
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
