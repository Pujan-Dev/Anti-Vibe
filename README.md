# Anti-Vibe

Anti-Vibe is a Linux terminal tracker that detects suspicious copy/paste behavior during coding sessions.

It monitors:
- Active window titles/classes (Wayland/X11)
- Clipboard changes
- Large file growth bursts in watched source files

The app computes a session score and displays a live curses dashboard.

## Current Entry Point

Run the tracker from:

```bash
python3 main.py [path ...]
```

Examples:

```bash
# Watch current folder recursively
python3 main.py .

# Watch one file and one folder
python3 main.py main.py ./src
```

## What Gets Tracked

- `AI window visits`: when focused window appears to match known AI assistant sites/tools.
- `Direct AI code copies`: code-like clipboard content copied while currently in an AI window.
- `Suspicious post-AI copies`: code-like clipboard content copied soon after leaving an AI window.
- `File dumps`: large single-step line increases in watched files.

## Scoring Model

`vibe_score` is capped at `100` and combines:
- Direct AI copies
- Suspicious post-AI copies
- Time spent in AI windows
- File dump events

The final verdict is one of:
- `CLEAN`
- `CHILL`
- `SUS`
- `CAUGHT`
- `BUSTED`
- `FULL AI`

## Requirements

- Python `3.10+`
- Linux desktop environment
- At least one active-window backend:
  - `hyprctl` (Hyprland), or
  - `swaymsg` (Sway), or
  - `xdotool` (X11)
- Clipboard access command (recommended):
  - `wl-paste` (Wayland), or
  - `xclip` (X11)
- Optional fallback: Python stdlib `tkinter` clipboard access

## Project Structure

- `main.py`: runnable tracker entrypoint (workers + curses UI + session report).
- `helper.py`: reusable helpers for window/clipboard detection and file path expansion.
- `patterns.py`: pattern constants and extension lists.
- `state.py`: typed state/event dataclasses and scoring properties.
- `docs/`: detailed documentation.

## Notes

- This project is Linux-focused.
- Detection is heuristic-based and not perfect.
- False positives are possible for copied snippets that look like code.

## Documentation

See:
- `docs/usage.md`
- `docs/architecture.md`
- `docs/dependencies.md`
