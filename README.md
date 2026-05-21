# voci da La Zanzara 🦟

Raccolta di clip audio divertenti dalla trasmissione radiofonica *La Zanzara* di Radio 24, condotta da Giuseppe Cruciani e David Parenzo. Naviga, cerca e ascolta centinaia di perle radiofoniche con un'interfaccia moderna, mobile-first e installabile come PWA.

## Key Features

- **200+ Clip Audio** — Personaggi celebri, momenti iconici e uscite memorabili
- **Ricerca e Ordinamento** — Cerca per personaggio o titolo, ordina per categoria, durata o alfabetico
- **PWA Installabile** — Funziona offline su Android e iOS con supporto home screen
- **Condivisione Nativa** — Condividi ogni clip via link diretto o app di messaggistica
- **Best Of Automatizzato** — Script Python per selezionare e compilare una compilation personalizzata

## Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (nessun framework)
- **Backend Scripts**: Python 3.12+, pydub, FFmpeg
- **Hosting**: GitHub Pages
- **PWA**: Service Worker, Manifest JSON, iOS meta tags
- **Audio**: MP3 files hosted on GitHub Pages

## Prerequisites

- Python 3.12 or higher (per gli script di automazione)
- FFmpeg (richiesto da pydub per la manipolazione audio)
- Git (per clonare e deployare)
- Un browser moderno (Chrome, Safari, Firefox) per la web app

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/hammer496/vocizanzara.git
cd vocizanzara
```

### 2. Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verifica che FFmpeg sia installato:

```bash
ffmpeg -version
```

Se non lo è:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 3. Serve the Web App Locally (Opzionale)

Usa un semplice server HTTP per visualizzare l'app in locale:

```bash
python3 -m http.server 8080
```

Apri [http://localhost:8080](http://localhost:8080) nel browser.

### 4. Usare gli Script di Automazione

**Selezionare clip per una compilation:**

```bash
python3 scripts/select_clips.py
```

Un'interfaccia interattiva ti mostrerà ogni clip uno per volta. Usa `y` per includere, `n` per saltare. La selezione viene salvata automaticamente in `output/selection.json` e la procedura può essere interrotta e ripresa in qualsiasi momento con `Ctrl+C`.

**Renderizzare la compilation:**

```bash
python3 scripts/render_compilation.py
```

Legge `output/selection.json`, raggruppa i clip per personaggio, applica crossfade e normalizzazione, e genera `output/best_of_zanzara.mp3` a 320kbps.

## Architecture

### Directory Structure

```
├── index.html              # Single-page app — tutto il frontend in un file
├── manifest.json           # PWA manifest (home screen, splash screen)
├── sitemap.xml             # SEO sitemap per Google
├── icona.png               # Icona app
├── icona2.png              # Icona alternativa
├── iconav.png              # Icona PWA (apple-touch-icon)
├── google22ee3901ceb9885f.html  # Verifica Google Search Console
│
├── audio/                  # Audio clip MP3 (200+ file)
│   ├── *.mp3
│   └── ...
│
├── scripts/                # Python automation scripts
│   ├── __init__.py
│   ├── source_parser.py    # Estrae i clip da index.html via regex
│   ├── select_clips.py     # Selettore interattivo per compilation
│   └── render_compilation.py # Render MP3 con crossfade e normalizzazione
│
├── doc/
│   └── plan.md             # Pipeline ETL architecture plan
│
├── output/                 # Output generato (.gitignored)
│   ├── selection.json      # Selezione clip salvata
│   ├── best_of_zanzara.mp3 # Compilation renderizzata
│   └── render_config.json  # Metadati della renderizzazione
│
├── requirements.txt        # Dipendenze Python
└── .gitignore
```

### Frontend Architecture (`index.html`)

L'app è una **Single-Page Application** (SPA) in vanilla JavaScript, senza framework:

| Componente | Descrizione |
|---|---|
| **Database inline** | Array `audioList` con ~250 clip (tag, titolo, filename) |
| **Motore di ricerca** | Filtra in tempo reale per personaggio (`t`) o titolo (`n`) |
| **Ordinamento** | 5 modalità: raggruppato per categoria, A-Z, Z-A, durata crescente/decrescente |
| **Player fisso** | Barra in basso con `<audio>` e nome traccia corrente |
| **PWA** | Manifest, service worker, iOS `apple-mobile-web-app-capable` |
| **Condivisione** | API `navigator.share` nativa su mobile, clipboard su desktop |

**Ciclo di vita di una richiesta:**

1. L'utente cerca o seleziona un ordinamento
2. JS filtra/ordina `audioList` in memoria
3. Il DOM viene rigenerato con `innerHTML`
4. Al click su una card, l'URL del file MP3 viene impostato sul player
5. I file audio sono serviti staticamente da GitHub Pages

### Python Scripts Pipeline

```
source_parser.py           select_clips.py           render_compilation.py
     │                           │                           │
     │ Estrae clip da            │ Interfaccia                │ Legge selection.json
     │ index.html tramite regex  │ interattiva per             │ Raggruppa per tag
     │ Restituisce:              │ selezionare y/n             │ Normalizza volume
     │ [{tag,title,filename}]    │ Salva in output/            │ Crossfade 500ms
     │                           │ supporta resume             │ Export 320k MP3
     ▼                           ▼                             ▼
[audioList from index] → [output/selection.json] → [output/best_of_zanzara.mp3]
```

### Database dei Clip

Non c'è un database tradizionale. I metadati dei clip sono definiti nell'array `audioList` dentro `index.html`:

```javascript
{ t: "Personaggio", n: "Titolo clip", f: "filename.mp3" }
```

- **t** (tag) — Personaggio o categoria (es. "Cruciani", "Parenzo", "varie")
- **n** (title) — Nome descrittivo del clip
- **f** (filename) — Nome file MP3 nella directory `audio/`

Lo script `source_parser.py` estrae questi dati tramite regex per usarli negli script Python, garantendo che la fonte della verità rimanga `index.html`.

### Gestione delle Durate

Le durate dei clip sono calcolate lato client via `Audio.loadmetadata` e memorizzate in `durationCache`. Vengono caricate in batch asincrono con aggiornamento progressivo dell'interfaccia. Il caricamento completo abilita l'ordinamento per durata.

## Available Scripts

| Comando | Descrizione |
|---|---|
| `python3 -m http.server 8080` | Avvia server di sviluppo locale |
| `python3 scripts/select_clips.py` | Selettore interattivo per compilation |
| `python3 scripts/render_compilation.py` | Render compilation MP3 |
| `python3 scripts/source_parser.py` | (Libreria, non eseguibile direttamente) |

## Testing

Non sono presenti test automatizzati. Il progetto segue un approccio manuale:

- Verifica visiva dell'interfaccia su Chrome, Safari e Firefox
- Test su dispositivo mobile reale o emulato (iOS + Android)
- Verifica PWA: installazione su home screen e funzionamento offline
- Per gli script Python: esecuzione end-to-end con verifica del file generato

## Deployment

### GitHub Pages (Current)

Il sito è deployato su GitHub Pages all'indirizzo:

```
https://hammer496.github.io/vocizanzara/
```

Il deployment avviene automaticamente pushando sul branch `main`. GitHub Pages serve i file statici dalla root del repository.

### PWA

L'app è installabile su dispositivi mobili:

- **Android**: Chrome mostra il banner "Aggiungi alla schermata Home"
- **iOS**: Usa il menu Condividi → "Aggiungi a Home" (un tooltip nativo guida l'utente)
- Una volta installata, funziona in modalità standalone (nessuna barra del browser)

### Deploy Manuale

```bash
# Qualsiasi hosting statico (Netlify, Vercel, etc.)
# Basta puntare il server alla root del progetto

# Esempio con rsync su VPS
rsync -avz --exclude 'output/' --exclude 'scripts/' --exclude '.git/' ./ utente@server:/var/www/vocizanzara/
```

## Environment Variables

Nessuna variabile d'ambiente è richiesta. La root URL per i file audio è hardcoded in `index.html`:

```javascript
const GITHUB_URL = "https://hammer496.github.io/vocizanzara/audio/";
```

Per ambienti locali, sostituire con il percorso del server locale.

## Troubleshooting

### I clip audio non vengono riprodotti

**Causa:** L'URL hardcoded punta a GitHub Pages — in ambiente locale il percorso non esiste.

**Soluzione:** Modifica `GITHUB_URL` in `index.html` (riga ~344) per puntare al tuo server locale:
```javascript
const GITHUB_URL = "/audio/";
```

### La ricerca non trova clip

**Causa:** La ricerca filtra su `t` (tag) e `n` (title) — cerca per personaggio o titolo, non per nome file.

**Soluzione:** Usa il menu a tendina "Ordina" → "Raggruppa per categoria" per esplorare tutte le categorie.

### "Errore riproduzione" in select_clips.py

**Causa:** FFmpeg non installato o file audio corrotto.

**Soluzione:**
```bash
# Verifica FFmpeg
ffmpeg -version

# Se manca:
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS
```

### PWA non installabile su iOS

**Nota:** iOS non mostra il banner automatico. Segui: Condividi (icona quadrato con freccia) → "Aggiungi a Home".

### Script non trova i clip

```bash
# Esegui sempre gli script dalla root del progetto
cd /path/to/vocizanzara
python3 scripts/select_clips.py
```

## License

Progetto amatoriale indipendente e non ufficiale. Tutti i diritti appartengono a Radio 24. Il materiale audio è utilizzato a scopo di intrattenimento. Per richieste di rimozione, contattare l'autore tramite il [gruppo Facebook](https://www.facebook.com/groups/vocidalazanzara).
