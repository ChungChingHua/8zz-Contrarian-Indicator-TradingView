"""Compatibility entry point; use fetch_social.py for both platforms. MPL-2.0."""
from datetime import datetime
from zoneinfo import ZoneInfo
TAIPEI=ZoneInfo("Asia/Taipei")
def build_tooltip(post_text: str, direction: int, strength: int, action: str, dt: datetime) -> str:
    dir_label = "偏多 ▲" if direction == 1 else "偏空 ▼"
    stars = {1: "★☆☆", 2: "★★☆", 3: "★★★"}.get(strength, "★☆☆")
    snippet = post_text.replace("\n", " ").strip()
    if len(snippet) > 60:
        snippet = snippet[:57] + "..."
    date_str = dt.astimezone(TAIPEI).strftime("FB %m/%d %H:%M")
    return (
        f"{action or '貼文'}\n"
        f"指標: {dir_label} | 強度: {stars}\n"
        f"{date_str} {snippet}"
    )



if __name__ == "__main__":
    from fetch_social import main
    main()
