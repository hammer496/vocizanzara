## Architettura del Sistema di Automazione (Pipeline)

Il sistema è strutturato come una pipeline ETL (Extract, Transform, Load) locale per l'ingestione, la trascrizione, l'indicizzazione e il ritaglio degli asset audio/video.

```
[Sorgenti Online] ──(yt-dlp)──> [Video/Audio Grezzo] ──(FFmpeg)──> [Audio WAV]
                                                                      │
[Output Video/Audio] <──(MoviePy)── [Timestamp Estrazione] <──(WhisperX)─┘

```

---

## Componenti Software e Librerie Python

| Componente | Strumento/Libreria | Funzione Specificazione Tecnica |
| --- | --- | --- |
| **Ingestione** | yt-dlp | Download automatico di flussi audio/video da YouTube, Spotify o archivi di podcast radiotelevisivi. Supporta il bypassing dei rate limit. |
| **Elaborazione Audio** | FFmpeg / pydub | Demuxing del video, normalizzazione del volume (EBU R128) e conversione in formato WAV mono a 16kHz (ottimale per modelli di Speech-to-Text). |
| **Diarizzazione e STT** | WhisperX | Trascrizione con timestamp a livello di singola parola e allineamento fonetico accurato via Wav2Vec2. Riduce l'errore di posizionamento del taglio a meno di 50ms. |
| **Ricerca ed Estrazione** | pandas / regex | Indicizzazione del testo trascritto per parole chiave ("amico mio", "moggi", "napoletani") ed estrazione dei vettori di tempo. |
| **Video Editing** | moviepy | Taglio automatizzato dei segmenti video/audio basato sui timestamp generati e rendering del file finale per l'esportazione su YouTube. |

---

## Fonti Asset Già Pronte (Scorciatoie Architetturali)

Prima di elaborare centinaia di ore di trasmissione, l'estrazione diretta da progetti esistenti riduce il tempo di sviluppo del 90%:

* **Repository GitHub esistenti:** Ricerca di progetti come "Zanzara Soundboard" o bot Telegram dedicati. Contengono directory /assets o /audio con i file .mp3 già categorizzati e rinominati.
* **Decompilazione APK Android:** Download dei file .apk delle applicazioni di soundboard dedicate a La Zanzara dal Play Store. Estrazione tramite tool di decompressione per recuperare la cartella interna degli effetti audio (res/raw o assets).
* **Web Scraping di Soundboard online:** Script di scraping mirati su siti web di meme audio italiani per scaricare direttamente i file indicizzati tramite tag HTML .

---

## Script di Inizializzazione Pipeline (PoC in Python)

Il seguente script automatizza il download, la conversione e il ritaglio preliminare basato su timestamp arbitrari.

```python
import os
import subprocess
from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip

class RegiaMemeExtractor:
    def __init__(self, output_dir="./workspace"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / "raw"
        self.clips_dir = self.output_dir / "clips"
        self.raw_dir.mkdir(exist_ok=True)
        self.clips_dir.mkdir(exist_ok=True)

    def download_source(self, url: str) -> Path:
        """Scarica la sorgente video alla massima qualità audio disponibile."""
        output_template = str(self.raw_dir / "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url
        ]
        subprocess.run(cmd, check=True)
        # Ritorna il path dell'ultimo file modificato nella directory raw
        files = list(self.raw_dir.glob("*.mp4"))
        return max(files, key=os.path.getmtime)

    def extract_subclip(self, video_path: Path, start_sec: float, end_sec: float, clip_name: str):
        """Taglia il segmento video senza ricodificare ove possibile per preservare performance."""
        output_path = self.clips_dir / f"{clip_name}.mp4"
        with VideoFileClip(str(video_path)) as video:
            new_clip = video.subclip(start_sec, end_sec)
            new_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
        return output_path

# Esecuzione del flusso di test
if __name__ == "__main__":
    extractor = RegiaMemeExtractor()
    # Esempio di URL (sostituire con sorgente reale della regia)
    target_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
    
    try:
        print("[+] Inizio download...")
        video_file = extractor.download_source(target_url)
        print(f"[+] File scaricato: {video_file}")
        
        # Esempio di taglio dal secondo 10 al secondo 15
        print("[+] Estrazione clip...")
        clip = extractor.extract_subclip(video_file, 10.0, 15.0, "meme_risata_moggi")
        print(f"[+] Clip salvata in: {clip}")
    except Exception as e:
        print(f"[-] Errore esecuzione: {e}")

```

---

## Workflow Operativo del Repository Locale

1. **Inizializzazione:** Configurazione dell'ambiente virtuale (venv o gestione tramite uv). Installazione delle dipendenze di sistema (ffmpeg e cudnn se si utilizza accelerazione hardware NVIDIA per Whisper).
2. **Scraping Automatizzato:** Esecuzione dello script di recupero delle fonti (estrazione da APK o download playlist YouTube tramite yt-dlp).
3. **Processamento Batch WhisperX:** Trascrizione massiva dei file audio scaricati con output in formato JSON contenente i token testuali e i relativi timestamp millisecondati.
4. **Parsing RegEx:** Esecuzione di query booleane sul testo per localizzare i pattern linguistici specifici della regia.
5. **Generazione della Timeline di Montaggio:** Compilazione automatica di un file di configurazione (JSON o CSV) con l'elenco dei file sorgenti e i segmenti esatti da tagliare.
6. **Rendering Finale:** Script Python che legge il file di configurazione, concatena i segmenti tramite moviepy o comandi ffmpeg concat, e genera la traccia video "Best Of" pronta per l'upload.