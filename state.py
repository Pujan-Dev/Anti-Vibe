from collections import deque
from dataclasses import dataclass, field
import time
from typing import Optional

from patterns import AI_SUSPICION_WINDOW


@dataclass
class Event:
    ts: float
    kind: str
    detail: str
    severity: int  # 1=info, 2=sus, 3=caught


@dataclass
class State:
    session_start: float = field(default_factory=time.time)
    events: list[Event] = field(default_factory=list)
    log: deque[Event] = field(default_factory=lambda: deque(maxlen=200))

    active_window: str = ""
    in_ai_window: bool = False
    last_left_ai: Optional[float] = None
    ai_window_time: float = 0.0
    last_ai_enter: Optional[float] = None
    ai_visits: int = 0

    last_clipboard: str = ""
    clipboard_copies: int = 0
    ai_copies: int = 0
    sus_copies: int = 0

    file_dumps: int = 0
    watched_files: dict[str, tuple[str, int]] = field(default_factory=dict)

    @property
    def recently_in_ai(self) -> bool:
        if self.in_ai_window:
            return True
        if self.last_left_ai is None:
            return False
        return (time.time() - self.last_left_ai) < AI_SUSPICION_WINDOW

    @property
    def seconds_since_ai(self) -> float:
        if self.in_ai_window:
            return 0.0
        if self.last_left_ai is None:
            return 9999.0
        return time.time() - self.last_left_ai

    @property
    def vibe_score(self) -> int:
        score = 0
        score += min(self.ai_copies * 20, 50)
        score += min(self.sus_copies * 10, 30)
        score += min(int(self.ai_window_time / 30) * 5, 15)
        score += min(self.file_dumps * 10, 5)
        return min(score, 100)

    @property
    def verdict(self) -> str:
        score = self.vibe_score
        if score == 0:
            return "CLEAN"
        if score < 20:
            return "CHILL"
        if score < 40:
            return "SUS"
        if score < 60:
            return "CAUGHT"
        if score < 80:
            return "BUSTED"
        return "FULL AI"

    def add_event(self, kind: str, detail: str, severity: int = 1) -> None:
        event = Event(time.time(), kind, detail, severity)
        self.events.append(event)
        self.log.appendleft(event)
