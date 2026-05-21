#!/usr/bin/env python3
import json
from collections import OrderedDict
from pathlib import Path

from pydub import AudioSegment

try:
    from source_parser import parse_index_html, verify_clips
except ImportError:
    from source.scripts.source_parser import parse_index_html, verify_clips

SOURCE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = SOURCE_DIR / "audio"
INDEX_FILE = SOURCE_DIR / "index.html"
SELECTION_FILE = SOURCE_DIR / "output" / "selection.json"
OUTPUT_DIR = SOURCE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "best_of_zanzara.mp3"
CROSSFADE_MS = 500
BITRATE = "320k"


def normalize(audio: AudioSegment) -> AudioSegment:
    return audio.apply_gain(-audio.max_dBFS)


def load_selection(selection_path: Path) -> list[dict]:
    data = json.loads(selection_path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("selected", [])


def group_by_tag(selected: list[dict]) -> OrderedDict:
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for clip in selected:
        tag = clip["tag"]
        if tag not in groups:
            groups[tag] = []
        groups[tag].append(clip)
    return groups


def load_all_clips() -> dict[str, dict]:
    clips = parse_index_html(INDEX_FILE)
    clips = verify_clips(clips, AUDIO_DIR)
    return {c["filename"]: c for c in clips}


def build_clip_list(selected: list[dict], all_clips: dict[str, dict]) -> list[dict]:
    flat = []
    groups = group_by_tag(selected)
    for tag, clips in groups.items():
        for clip in clips:
            entry = all_clips.get(clip["filename"])
            if entry:
                flat.append(entry)
            else:
                print(f"[!] Clip non trovato: {clip['filename']}")
    return flat


def render(clip_list: list[dict]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    segments = []
    for i, clip in enumerate(clip_list, 1):
        filepath = AUDIO_DIR / clip["filename"]
        print(f"[{i}/{len(clip_list)}] Carico: {clip['tag']} — {clip['title']}")
        seg = AudioSegment.from_file(filepath)

        seg = normalize(seg)

        cf = min(CROSSFADE_MS, len(seg) // 2)
        seg = seg.fade(to_gain=-6, start=0, duration=cf)

        segments.append(seg)

    print("\nConcatenazione in corso...")
    combined = segments[0]
    for seg in segments[1:]:
        cf = min(CROSSFADE_MS, len(seg) // 2, len(combined) // 2)
        combined = combined.append(seg, crossfade=cf)

    duration_min = len(combined) / 60000
    print(f"Durata totale: {duration_min:.1f} minuti")

    print(f"Esportazione a {BITRATE}...")
    combined.export(str(OUTPUT_FILE), format="mp3", bitrate=BITRATE)
    print(f"[green]✓ Output: {OUTPUT_FILE}[/]")

    config = {
        "source": str(SOURCE_DIR),
        "total_clips": len(clip_list),
        "crossfade_ms": CROSSFADE_MS,
        "bitrate": BITRATE,
        "duration_min": round(duration_min, 1),
        "tags": list(OrderedDict.fromkeys(c["tag"] for c in clip_list)),
        "clips": [
            {"tag": c["tag"], "title": c["title"], "filename": c["filename"]}
            for c in clip_list
        ],
    }
    config_path = OUTPUT_DIR / "render_config.json"
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    print(f"[green]✓ Config: {config_path}[/]")


def main():
    if not SELECTION_FILE.exists():
        print("[red]Errore: selection.json non trovato. Esegui prima select_clips.py[/]")
        return

    selected = load_selection(SELECTION_FILE)
    if not selected:
        print("[red]Nessun clip selezionato in selection.json[/]")
        return

    print(f"Caricati {len(selected)} clip selezionati\n")

    all_clips = load_all_clips()
    clip_list = build_clip_list(selected, all_clips)

    print(f"Ordinati per personaggio: {len(clip_list)} clip\n")

    render(clip_list)


if __name__ == "__main__":
    main()
