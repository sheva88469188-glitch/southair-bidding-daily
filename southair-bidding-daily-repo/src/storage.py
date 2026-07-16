from __future__ import annotations

import json
from pathlib import Path

from parser import Announcement


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("seen", []))


def save_seen(path: Path, items: list[Announcement]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = sorted(item.dedupe_key for item in items)
    path.write_text(json.dumps({"seen": seen}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
