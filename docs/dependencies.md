# Dependency Notes

## Python

- Standard library modules only in current helper/state modular files.
- Curses UI requires terminal support for `curses`.

## External Commands

Anti-Vibe tries these in order for active-window detection:

1. `hyprctl activewindow -j`
2. `swaymsg -t get_tree`
3. `xdotool getactivewindow getwindowname`

Clipboard detection tries:

1. `wl-paste --no-newline`
2. `xclip -selection clipboard -o`
3. stdlib `tkinter` fallback

## Install Suggestions (Linux)

Debian/Ubuntu examples:

```bash
sudo apt update
sudo apt install -y xdotool xclip python3-tk
```

Wayland users may also install:

```bash
sudo apt install -y wl-clipboard
```

## Failure Behavior

If a backend command is unavailable or fails, the code catches the error and falls back to the next backend.
