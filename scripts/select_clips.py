#!/usr/bin/env python3
import json
import random
import signal
import sys
from pathlib import Path

from pydub import AudioSegment
from pydub.playback import play
from rich.console import Console
from rich.prompt import Prompt

try:
    from source_parser import parse_index_html, verify_clips
except ImportError:
    from source.scripts.source_parser import parse_index_html, verify_clips

SOURCE_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = SOURCE_DIR / "index.html"
AUDIO_DIR = SOURCE_DIR / "audio"
SELECTION_FILE = SOURCE_DIR / "output" / "selection.json"

console = Console()
clips: list[dict] = []
selection: list[dict] = []
remaining_indices: list[int] = []


def save_selection():
    SELECTION_FILE.write_text(
        json.dumps(selection, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def signal_handler(sig, frame):
    console.print("\n[yellow]Selezione interrotta. Salvo i progressi...[/]")
    save_selection()
    console.print(f"[green]✓ Salvataggio in {SELECTION_FILE}[/]")
    sys.exit(0)


def resume_or_restart() -> bool:
    if not SELECTION_FILE.exists():
        return False
    console.print(f"[cyan]Trovata selezione esistente: {SELECTION_FILE}[/]")
    answer = Prompt.ask(
        "Riprendere da dove hai interrotto?", choices=["y", "n"], default="y"
    )
    if answer == "y":
        return True
    return False


def load_existing_selection() -> set[int]:
    global selection
    data = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    selection = data if isinstance(data, list) else data.get("selected", [])
    chosen_filenames = {c["filename"] for c in selection}
    done_indices = {
        i for i, c in enumerate(clips) if c["filename"] in chosen_filenames
    }
    return done_indices


def get_adaptive_crossfade(clip_path: Path) -> int:
    seg = AudioSegment.from_file(clip_path)
    dur_ms = len(seg)
    return min(500, dur_ms // 2)


def main():
    global clips, remaining_indices, selection

    signal.signal(signal.SIGINT, signal_handler)

    console.print("[bold cyan]🎙 Selezione clip — Best Of La Zanzara[/]")
    console.print(f"[dim]Fonte: {SOURCE_DIR}[/]\n")

    clips = parse_index_html(INDEX_FILE)
    clips = verify_clips(clips, AUDIO_DIR)
    console.print(f"[green]✓ {len(clips)} clip disponibili[/]\n")

    if resume_or_restart():
        done_indices = load_existing_selection()
        remaining_indices = [i for i in range(len(clips)) if i not in done_indices]
        console.print(
            f"[cyan]Riprendo: {len(selection)} già selezionati, "
            f"{len(remaining_indices)} rimanenti[/]\n"
        )
    else:
        selection.clear()
        remaining_indices = list(range(len(clips)))
        random.shuffle(remaining_indices)

    for idx, clip_idx in enumerate(remaining_indices, 1):
        clip = clips[clip_idx]
        total = len(remaining_indices)
        filepath = AUDIO_DIR / clip["filename"]

        console.rule(f"[bold]{idx}/{total}[/]")
        console.print(f"[yellow]Personaggio:[/] {clip['tag']}")
        console.print(f"[yellow]Titolo:[/]     {clip['title']}")
        console.print(f"[yellow]File:[/]       {clip['filename']}")
        console.print()

        try:
            seg = AudioSegment.from_file(filepath)
            crossfade = get_adaptive_crossfade(filepath)
            dur_sec = len(seg) / 1000
            console.print(f"[dim]Durata: {dur_sec:.1f}s | Crossfade: {crossfade}ms[/]")
            console.print("[dim]Riproduco...[/]")
            play(seg)
        except Exception as e:
            console.print(f"[red]Errore riproduzione: {e}[/]")
            answer = Prompt.ask("Includere comunque?", choices=["y", "n"], default="n")
            if answer == "y":
                selection.append(clip)
                save_selection()
            continue

        answer = Prompt.ask("Includere?", choices=["y", "n"], default="n")
        if answer == "y":
            selection.append(clip)
            save_selection()
            console.print("[green]✓ Incluso[/]")
        else:
            console.print("[dim]— Saltato[/]")
        console.print()

    save_selection()
    console.print(f"\n[bold green]✓ Selezione completata![/]")
    console.print(f"[green]{len(selection)} clip selezionati su {len(clips)} totali[/]")
    console.print(f"[green]Salvato in: {SELECTION_FILE}[/]")


if __name__ == "__main__":
    main()
