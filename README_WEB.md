# SyncExtPack Web Builder

A web interface for building Ford SYNC 2 custom app packages.

## Quick Start (Linux)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure crypto_pack is executable
chmod +x environment/crypto_pack

# Run
python3 webapp.py
# Access at http://localhost:5000
```

## Quick Start (Windows)

```cmd
pip install -r requirements.txt
python webapp.py
:: Access at http://localhost:5000
```

## environment/ Folder

All build tools are pre-packaged in `environment/`. No system PATH search required.

| File | Platform | Description |
|------|----------|-------------|
| `crypto_pack` | Linux | ELF x86-64 binary, encryption/packing tool |
| `crypto_pack.exe` | Windows | PE x86-64 binary, encryption/packing tool |
| `swfmill` | Linux | ELF x86-64 binary, SWF/XML converter |
| `swfmill.exe` | Windows | PE i386 binary, SWF/XML converter |
| `java` | Linux | Wrapper script → `jre-linux/bin/java` |
| `jre-linux/` | Linux | Temurin JRE 17 (complete runtime) |
| `jre-windows/` | Windows | Temurin JRE 17 (complete runtime) |
| `secureSWF.jar` | Cross-platform | SWF obfuscation tool |
| `Installer.xml.bak` | Cross-platform | SWF installer XML template |
| `SecureSWF.ssp4.bak` | Cross-platform | secureSWF configuration template |

## Available Apps

| App | Description |
|-----|-------------|
| AutoKit | CarPlay & Android Auto wireless box (Chinese UI) |
| MirrorLink_EN_NEW | Phone mirroring via EasyConnected (English UI) |
| MirrorLink_NEW | Phone mirroring via EasyConnected (Russian UI) |
| Explorer | Total Commander file manager with OBEX transfer |
| Player_EN | Video player - H.264/MPEG/WMV/DivX/MP3/AAC (English UI) |
| Player | Video player - same codecs (Russian UI) |
| Navitel | Offline GPS navigation |
| DDApp | Digital dashboard & driving restrictions manager |
| Reboot | Reboot button in SYNC menu |

EN and non-EN versions of MirrorLink and Video Player are mutually exclusive.
