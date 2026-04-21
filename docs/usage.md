# Usage Guide

## Basic Command

```bash
python3 main.py [path ...]
```

If no paths are passed, file monitoring is disabled, but window and clipboard tracking still run.

## Path Behavior

- File path: watched directly.
- Directory path: scanned recursively for source files matching configured code extensions.

Extensions currently include:
- `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.go`, `.rs`, `.cpp`, `.c`, `.h`, `.java`, `.rb`, `.php`, `.swift`, `.kt`, `.sh`, `.lua`, `.cs`

## Runtime Controls

Inside the curses UI:
- Press `q`, `Q`, or `Esc` to stop.

After quit, a text session summary is printed in the terminal.

## Tips

- Start tracker before your coding session.
- Pass only relevant project folders to reduce noise.
- Keep clipboard backend tools (`wl-paste` or `xclip`) installed for reliable detection.
