import curses
import hashlib
import os
import sys
import threading
import time
from datetime import datetime

from helper import (
    expand_watch_paths,
    fmt_dur,
    get_active_window,
    get_clipboard,
    looks_like_code,
    window_is_ai,
)
from patterns import AI_SUSPICION_WINDOW
from state import State

KIND_LABELS = {"window": "W", "clipboard": "C", "file": "F"}
SEV_COLORS = {1: 2, 2: 3, 3: 1}  # green=1, yellow=2(sus), red=3(caught)


def window_worker(state: State, stop: threading.Event) -> None:
    while not stop.is_set():
        title, wm_class = get_active_window()
        state.active_window = title or wm_class
        is_ai = window_is_ai(title, wm_class)

        if is_ai and not state.in_ai_window:
            state.in_ai_window = True
            state.last_ai_enter = time.time()
            state.ai_visits += 1
            state.add_event("window", f"Entered AI: {title[:50]}", severity=1)

        elif not is_ai and state.in_ai_window:
            state.in_ai_window = False
            state.last_left_ai = time.time()
            if state.last_ai_enter:
                state.ai_window_time += time.time() - state.last_ai_enter
                state.last_ai_enter = None
            state.add_event("window", f"Left AI -> now in: {title[:40]}", severity=1)

        stop.wait(1.5)


def clipboard_worker(state: State, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            cb = get_clipboard()
            if cb and cb != state.last_clipboard:
                state.clipboard_copies += 1
                state.last_clipboard = cb
                is_code = looks_like_code(cb)

                if is_code:
                    if state.in_ai_window:
                        state.ai_copies += 1
                        state.add_event(
                            "clipboard",
                            f"Code copied FROM AI ({len(cb)} chars)",
                            severity=3,
                        )
                    elif state.recently_in_ai:
                        secs = int(state.seconds_since_ai)
                        state.sus_copies += 1
                        state.add_event(
                            "clipboard",
                            f"Code copied {secs}s after leaving AI ({len(cb)} chars) - sus",
                            severity=2,
                        )
                    else:
                        state.add_event(
                            "clipboard",
                            f"Code copied (no AI context, {len(cb)} chars)",
                            severity=1,
                        )
        except Exception:
            pass

        stop.wait(1.0)


def file_worker(state: State, stop: threading.Event, paths: list[str]) -> None:
    def read_file_info(path: str) -> tuple[str | None, int]:
        try:
            with open(path, "r", errors="replace") as handle:
                lines = handle.readlines()
            digest = hashlib.md5("".join(lines).encode()).hexdigest()
            return digest, len(lines)
        except Exception:
            return None, 0

    for path in paths:
        digest, line_count = read_file_info(path)
        if digest:
            state.watched_files[path] = (digest, line_count)

    while not stop.is_set():
        for path in paths:
            digest, line_count = read_file_info(path)
            if not digest:
                continue

            prev_digest, prev_line_count = state.watched_files.get(path, (None, 0))
            if prev_digest and digest != prev_digest:
                delta = line_count - prev_line_count
                if delta > 20:
                    state.file_dumps += 1
                    severity = 3 if delta > 80 else (2 if delta > 40 else 1)
                    state.add_event(
                        "file",
                        f"+{delta} lines dumped into {os.path.basename(path)}",
                        severity=severity,
                    )

            state.watched_files[path] = (digest, line_count)

        stop.wait(3)


def draw_bar(win, y: int, x: int, width: int, percent: int, pair: int) -> None:
    filled = int(width * percent / 100)
    win.attron(curses.color_pair(pair))
    win.addstr(y, x, "#" * filled)
    win.attroff(curses.color_pair(pair))
    try:
        win.addstr(y, x + filled, "." * (width - filled))
    except curses.error:
        pass


def tui(stdscr, state: State, stop: threading.Event) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_WHITE, -1)

    while not stop.is_set():
        try:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):
                stop.set()
                break

            height, width = stdscr.getmaxyx()
            stdscr.erase()
            now = time.time()
            elapsed = now - state.session_start

            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(0, 0, "-" * width)
            title = " ANTI-VIBE TRACKER "
            stdscr.addstr(1, max(0, (width - len(title)) // 2), title)
            ts = datetime.now().strftime("%H:%M:%S")
            stdscr.addstr(1, width - len(ts) - 2, ts)
            stdscr.addstr(2, 0, "-" * width)
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

            row = 3
            score = state.vibe_score
            score_color = 3 if score < 30 else (2 if score < 60 else 1)

            stdscr.attron(curses.color_pair(score_color) | curses.A_BOLD)
            stdscr.addstr(row, 2, f"VIBE SCORE: {score:3d}/100  {state.verdict}")
            stdscr.attroff(curses.color_pair(score_color) | curses.A_BOLD)
            row += 1
            draw_bar(stdscr, row, 2, min(width - 6, 60), score, score_color)
            row += 2

            stdscr.attron(curses.color_pair(6))
            stdscr.addstr(
                row, 2, f"Session: {fmt_dur(elapsed)}   Events: {len(state.events)}"
            )
            stdscr.attroff(curses.color_pair(6))
            row += 1

            if state.in_ai_window:
                ai_label = "IN AI WINDOW RIGHT NOW"
                ai_color = 1
            elif state.recently_in_ai:
                secs = int(state.seconds_since_ai)
                remaining = max(0, AI_SUSPICION_WINDOW - secs)
                ai_label = f"Left AI {secs}s ago (suspicious for {remaining}s)"
                ai_color = 2
            else:
                ai_label = "Not in AI window"
                ai_color = 3

            stdscr.attron(curses.color_pair(ai_color) | curses.A_BOLD)
            stdscr.addstr(row, 2, ai_label)
            stdscr.attroff(curses.color_pair(ai_color) | curses.A_BOLD)
            row += 2

            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(row, 2, "DETECTORS")
            stdscr.attroff(curses.color_pair(4))
            row += 1

            stats = [
                ("Total clipboard copies", state.clipboard_copies, 6),
                ("Direct AI copies", state.ai_copies, 1 if state.ai_copies else 3),
                ("Sus copies after AI", state.sus_copies, 2 if state.sus_copies else 3),
                ("AI window visits", state.ai_visits, 2 if state.ai_visits else 3),
                ("Time in AI", fmt_dur(state.ai_window_time), 6),
                (
                    "File dumps (>20 lines)",
                    state.file_dumps,
                    1 if state.file_dumps else 3,
                ),
            ]

            col_width = (width - 4) // 2
            for idx, (label, value, color) in enumerate(stats):
                stat_row = row + (idx // 2)
                col = 2 + (idx % 2) * col_width
                try:
                    stdscr.addstr(stat_row, col, f"{label}: ")
                    stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
                    stdscr.addstr(str(value))
                    stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
                except curses.error:
                    pass

            row += (len(stats) // 2) + 2

            stdscr.attron(curses.color_pair(6))
            stdscr.addstr(row, 2, "Active: ")
            stdscr.attroff(curses.color_pair(6))
            active_color = (
                1 if state.in_ai_window else (2 if state.recently_in_ai else 6)
            )
            try:
                stdscr.attron(curses.color_pair(active_color))
                stdscr.addstr(state.active_window[: width - 12] or "(unknown)")
                stdscr.attroff(curses.color_pair(active_color))
            except curses.error:
                pass
            row += 2

            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(row, 2, "EVENT LOG (newest first)")
            stdscr.attroff(curses.color_pair(4))
            row += 1

            for idx, event in enumerate(list(state.log)[: height - row - 3]):
                if row + idx >= height - 2:
                    break
                age = int(now - event.ts)
                icon = KIND_LABELS.get(event.kind, "*")
                color = SEV_COLORS.get(event.severity, 6)
                line = f" {icon} [{age:4d}s ago] {event.detail}"[: width - 4]
                try:
                    stdscr.attron(curses.color_pair(color))
                    stdscr.addstr(row + idx, 2, line)
                    stdscr.attroff(curses.color_pair(color))
                except curses.error:
                    pass

            stdscr.attron(curses.color_pair(6))
            try:
                stdscr.addstr(height - 2, 0, "-" * width)
            except curses.error:
                pass
            stdscr.addstr(height - 1, 2, " [Q] quit ")
            stdscr.attroff(curses.color_pair(6))

            stdscr.refresh()
        except curses.error:
            pass

    stop.set()


def run() -> None:
    watch_paths = expand_watch_paths(sys.argv[1:])
    state = State()
    stop = threading.Event()

    threads = [
        threading.Thread(target=window_worker, args=(state, stop), daemon=True),
        threading.Thread(target=clipboard_worker, args=(state, stop), daemon=True),
    ]
    if watch_paths:
        threads.append(
            threading.Thread(
                target=file_worker, args=(state, stop, watch_paths), daemon=True
            )
        )

    for thread in threads:
        thread.start()

    try:
        curses.wrapper(tui, state, stop)
    except KeyboardInterrupt:
        stop.set()

    elapsed = time.time() - state.session_start
    print("\n" + "=" * 50)
    print("  ANTI-VIBE SESSION REPORT")
    print("=" * 50)
    print(f"  Duration          : {fmt_dur(elapsed)}")
    print(f"  Final score       : {state.vibe_score}/100  {state.verdict}")
    print(f"  AI window time    : {fmt_dur(state.ai_window_time)}")
    print(f"  Direct AI copies  : {state.ai_copies}")
    print(f"  Sus copies        : {state.sus_copies}")
    print(f"  File dumps        : {state.file_dumps}")
    print(f"  Total events      : {len(state.events)}")


if __name__ == "__main__":
    print("somethign")
    print("hello")
    run()
