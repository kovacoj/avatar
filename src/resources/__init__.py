from pathlib import Path

path = Path(__file__).resolve().parents[0]

user_prompt = (path / "templates/user.prompt").read_text(encoding="utf-8")
system_prompt = (path / "templates/system.prompt").read_text(encoding="utf-8")


__all__ = [
    "user_prompt",
    "system_prompt",
]
