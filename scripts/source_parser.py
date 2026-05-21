import re
import json
from pathlib import Path


CLIP_ENTRY_RE = re.compile(
    r'\{\s*t:\s*"([^"]*)"\s*,\s*n:\s*"([^"]*)"\s*,\s*f:\s*"([^"]*)"\s*\}'
)


def parse_index_html(index_path: Path) -> list[dict]:
    html = index_path.read_text(encoding="utf-8")
    clips = []
    for match in CLIP_ENTRY_RE.finditer(html):
        clips.append({
            "tag": match.group(1),
            "title": match.group(2),
            "filename": match.group(3),
        })
    return clips


def verify_clips(clips: list[dict], audio_dir: Path) -> list[dict]:
    verified = []
    missing = []
    for clip in clips:
        filepath = audio_dir / clip["filename"]
        if filepath.exists():
            verified.append(clip)
        else:
            missing.append(clip["filename"])
    if missing:
        print(f"[!] {len(missing)} file mancanti (verranno saltati):")
        for f in missing[:10]:
            print(f"    - {f}")
        if len(missing) > 10:
            print(f"    ... e altri {len(missing) - 10}")
    return verified
