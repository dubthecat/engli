"""Bundled starter phrase-maps for the Engli "boost" layer.

These ship inside the language package so the boost feature (``Use snippet``,
``Run``, ``prompt "..."``) works with zero external data — the package is fully
self-contained and open-source-ready. Inside the larger monorepo the richer
``engli/translate`` maps are overlaid on top of these at load time
(see ``compiler._load_maps``); extracted on its own, the package still boosts
from exactly what is here.

Contract (mirrors AGENTS.md): additive only, and every command is read-only and
safe — nothing here deletes, writes, exfiltrates, or needs elevated rights.
"""

# Exact English phrase -> a code block to inline verbatim.
FUNCTIONS = {
    "greet the world": 'print("Hello, world!")',
}

# Regex pattern -> template; \1, \2... are the captured groups.
CODES = {
    r"Create a dictionary named (\w*)": r"\1 = {}",
    r"Create a list named (\w*)": r"\1 = []",
    r"Create a set named (\w*)": r"\1 = set()",
    r"Create a counter named (\w*)": r"\1 = 0",
}

# English phrase -> a safe, read-only shell command.
COMMANDS = {
    "list files in the current directory": "ls -la",
    "show the current directory": "pwd",
    "show today's date": "date",
    "show running processes": "ps aux",
    "show disk usage": "df -h",
    "show the git status": "git status",
}

# Role title -> the system-prompt text it expands to.
PROMPTS = {
    "Linux Terminal": "I want you to act as a linux terminal. I will type commands and you will reply with what the terminal should show. I want you to only reply with the terminal output inside one unique code block, and nothing else. do not write explanations. do not type commands unless I instruct you to do so. when i need to tell you something in english, i will do so by putting text inside curly brackets {like this}. my first command is pwd",
    "English Translator": "I want you to act as an English translator and improver. I will speak to you in any language and you will detect the language, translate it and answer in the corrected and improved version of my text, in English. Keep the meaning the same, but make the wording more literary.",
    "Interviewer": "I want you to act as an interviewer. I will be the candidate and you will ask me the interview questions for the position. I want you to only reply as the interviewer. Ask me the questions one by one and wait for my answers.",
}

BUNDLED = {
    "function": FUNCTIONS,
    "code": CODES,
    "command": COMMANDS,
    "prompt": PROMPTS,
}
