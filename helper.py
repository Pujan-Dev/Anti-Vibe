import json
import os
import re
import subprocess
from typing import Iterable

import patterns


def get_active_windows():
    # Hyprland
    try:
        out = subprocess.check_output(
            ["hyprctl", "activewindow", "-j"], stderr=subprocess.DEVNULL, timeout=1
        )
        data = json.loads(out)
        return (data.get("title") or "").lower(), (data.get("class") or "").lower()
    except Exception:
        pass
    # Sway
    try:
        out = subprocess.check_output(
            ["swaymsg", "-t", "get_tree"], stderr=subprocess.DEVNULL, timeout=1
        )

        def find_focused(node):
            if node.get("focused"):
                return node.get("name", ""), node.get("app_id", "") or node.get(
                    "window_properties", {}
                ).get("class", "")
            for child in node.get("nodes", []) + node.get("floating_nodes", []):
                r = find_focused(child)
                if r[0] or r[1]:
                    return r
            return "", ""

        t, c = find_focused(json.loads(out))
        if t or c:
            return t.lower(), c.lower()
    except Exception:
        pass

    # X11
    try:
        out = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            stderr=subprocess.DEVNULL,
            timeout=1,
        )
        return out.decode(errors="replace").strip().lower(), ""
    except Exception:
        pass

    return "", ""


def get_active_window() -> tuple[str, str]:
    """Compatibility wrapper for singular naming used by runtime."""
    return get_active_windows()


def window_is_ai(title: str, wm_class=""):
    combined = title + " " + wm_class
    is_terminal = any(t in combined for t in patterns.TERMINAL_EMULATORS)
    if is_terminal:
        for ed in patterns.TERMINAL_EDITORS:
            if re.search(rf"\b{ed}\b", combined):
                return False  # It's just an editor in terminal
    return any(p in combined for p in patterns.AI_PATTERNS)


def get_clipboard():
    try:
        out = subprocess.check_output(
            ["wl-paste", "--no-newline"], stderr=subprocess.DEVNULL, timeout=1
        )
        return out.decode(errors="replace")
    except Exception:
        pass
    # X11
    try:
        out = subprocess.check_output(
            ["xclip", "-selection", "clipboard", "-o"],
            stderr=subprocess.DEVNULL,
            timeout=1,
        )
        return out.decode(errors="replace")
    except Exception:
        pass
    # stdlib fallback
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        data = root.clipboard_get()
        root.destroy()
        return data or ""
    except Exception:
        pass
    return ""


def looks_like_code(text: str) -> bool:
    """Check if clipboard text looks like code."""
    if len(text) < 50:
        return False
    code_signals = [
        r"def \w+\(",  # python function
        r"function \w+\(",  # js function
        r"class \w+",  # class def
        r"import \w+",  # imports
        r"#include",  # c/cpp
        r"const |let |var ",  # js vars
        r"=>",  # arrow functions
        r"^\s{2,}",  # indented code
    ]
    line_count = text.count("\n")
    if line_count > 4:
        return True
    return any(re.search(p, text, re.MULTILINE) for p in code_signals)


# formated time
def fmt_dur(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m:02d}m {s:02d}s"


def expand_watch_paths(inputs: Iterable[str]) -> list[str]:
    """Expand file/folder cli inputs into concrete source file paths."""
    watch_paths: list[str] = []
    for item in inputs:
        if os.path.isfile(item):
            watch_paths.append(os.path.abspath(item))
            continue

        if os.path.isdir(item):
            for root, _, files in os.walk(item):
                for name in files:
                    if any(name.endswith(ext) for ext in patterns.CODE_EXTENSIONS):
                        watch_paths.append(os.path.join(root, name))

    return watch_paths
