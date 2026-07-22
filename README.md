# SyncExtPack Online Builder

A web-based tool for building custom app installation packages for Ford SYNC 2 APIM modules. Users submit their device serial number and select apps — the server builds and delivers a ready-to-install ZIP package.

**Live site:** https://sync.dpdns.org

## Features

- **Online building** — no local setup required, just enter your APIM serial number and pick apps
- **Bilingual UI** — English / Chinese with automatic browser language detection
- **Concurrent builds** — multiple users can build simultaneously, each in an isolated working directory
- **Self-contained environment** — all build tools (crypto_pack, swfmill, JRE, secureSWF) are bundled in `environment/`, no system PATH dependencies
- **Cloudflare Turnstile** — bot protection integrated
- **Auto-cleanup** — finished jobs and build directories are automatically purged after 1 hour

## Available Apps

| App | Description | Language |
|-----|-------------|----------|
| Navitel | Offline GPS navigation | Multi-language |
| AutoKit | CarPlay & Android Auto wireless adapter | CN |
| MirrorLink | Phone screen mirroring via EasyConnected | EN / RU |
| Video Player | H.264/MPEG/WMV/DivX/MP3/AAC/FLAC player | EN / RU |
| Explorer | Total Commander with OBEX file transfer | Multi-language |
| Reboot Button | Add a reboot button to the apps menu | EN |

## Deployment

### Prerequisites

- Python 3.10+
- Linux or Windows

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure Turnstile

Set the Cloudflare Turnstile secret key as an environment variable:

```bash
export TURNSTILE_SECRET='your_secret_key_here'
```

### Prepare environment tools

Place the following in the `environment/` folder:

| File | Purpose |
|------|---------|
| `crypto_pack` / `crypto_pack.exe` | Encrypts and packs app binaries |
| `swfmill` / `swfmill.exe` | Converts SWF/XML for installer build |
| `secureSWF.jar` | Obfuscates the installer SWF |
| `java` (Linux wrapper) or `jre-windows/` | Java runtime for secureSWF |
| `Installer.xml.bak` | Installer XML template |
| `SecureSWF.ssp4.bak` | secureSWF config template |

### Run

```bash
python webapp.py
```

The server listens on `0.0.0.0:5000`.

For production, use a reverse proxy (nginx, Caddy) with Cloudflare for SSL and rate limiting.

## Project Structure

```
syncextpack_website/
├── webapp.py              # Flask web server
├── build_pack.py          # CLI entry: build install/update packs
├── build_installer.py     # CLI entry: build installer (swfmill + secureSWF)
├── build_archive.py       # CLI entry: create ZIP archive
├── builder/               # Core build logic
│   ├── build.py           # Build orchestrator
│   ├── packer.py          # Packing & encryption
│   ├── units_map.py       # App unit registry
│   ├── utils.py           # Shared utilities
│   └── units/             # Individual app definitions
├── templates/
│   └── index.html         # Frontend (Build / Guide / Resources tabs)
├── static/guide/          # Installation guide screenshots
├── environment/           # Pre-bundled build tools (not in git)
├── FullPack/              # Source app binaries & templates
├── requirements.txt       # Python dependencies
└── .gitignore
```

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** Vanilla HTML/CSS/JS (no framework)
- **Build tools:** crypto_pack, swfmill, secureSWF, JRE 17
- **Security:** Cloudflare Turnstile, input validation, path traversal protection

## License

This project is licensed under the [MIT License](LICENSE).

Note: The project is open-source and non-commercial in intent. See the disclaimer on the [live site](https://sync.dpdns.org) for usage terms.

## Credits

- Original SyncExtPack builder by İsmet Ertekin
- Web adaptation and concurrent build support by [sectlying](https://github.com/sectlying)
