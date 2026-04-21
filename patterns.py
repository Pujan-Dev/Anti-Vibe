AI_PATTERNS = [
    "claude.ai", "claude",
    "chatgpt", "chat.openai", "openai",
    "gemini", "bard",
    "copilot", "github copilot",
    "phind", "perplexity",
    "mistral", "ollama", "llama",
    "aider", "cursor",
    "you.com", "poe.com",
]

BROWSER_PATTERNS = [
    "firefox", "chromium", "chrome", "brave",
    "librewolf", "zen", "vivaldi", "opera",
]

TERMINAL_EDITORS = ["nvim", "vim", "nano", "helix", "emacs", "micro"]
TERMINAL_EMULATORS = ["kitty", "alacritty", "wezterm", "foot", "ghostty", "st", "urxvt", "xterm"]

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".cpp",
    ".c", ".h", ".java", ".rb", ".php", ".swift", ".kt", ".sh", ".lua", ".cs",
}

# How long (seconds) after leaving AI site we still consider a copy as "from AI"
AI_SUSPICION_WINDOW = 60  # 60 seconds grace period

__all__ = [
    "AI_PATTERNS",
    "BROWSER_PATTERNS",
    "TERMINAL_EDITORS",
    "TERMINAL_EMULATORS",
    "CODE_EXTENSIONS",
    "AI_SUSPICION_WINDOW",
]
