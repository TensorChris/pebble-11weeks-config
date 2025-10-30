# Pebble 11 Weeks Watchface - Konfigurationsseite

Diese standalone Version der Konfigurationsseite für das "11 Weeks" Pebble Watchface kann selbst gehostet werden.

## 📁 Inhalt

- `config.html` - Standalone Konfigurationsseite (alle Ressourcen eingebettet)

## 🚀 Verwendung

### Option 1: Lokales Hosten mit Python

Der einfachste Weg zum Testen:

```bash
# Im Ordner pebble-11weeks-config:
cd "/Users/chris/Library/CloudStorage/OneDrive-TensorFiveGmbH/Apps/pebble-11weeks-config"

# Python 3 HTTP Server starten:
python3 -m http.server 8000
```

Dann kannst du die Seite im Browser öffnen: `http://localhost:8000/config.html`

### Option 2: Auf einem Webserver hosten

1. Lade die `config.html` auf deinen Webserver hoch
2. Stelle sicher, dass die Datei über HTTPS erreichbar ist
3. Notiere dir die URL (z.B. `https://deine-domain.de/pebble/config.html`)

### Option 3: GitHub Pages (kostenlos)

1. Erstelle ein neues GitHub Repository
2. Lade `config.html` hoch
3. Aktiviere GitHub Pages in den Repository-Einstellungen
4. Die URL wird etwa so aussehen: `https://username.github.io/repo-name/config.html`

### Option 4: OneDrive/Dropbox Direct Link

Da die Datei bereits in deinem OneDrive liegt:
1. Erstelle einen öffentlichen Link für die `config.html`
2. Verwende einen OneDrive Direct Link Generator (z.B. https://syncwithtec.blogspot.com/p/direct-download-link-generator.html)

## 🔧 In der Pebble App verwenden

1. Öffne die Pebble App auf deinem Smartphone
2. Gehe zu den Einstellungen deines "11 Weeks" Watchfaces
3. Wenn nach einer Config URL gefragt wird, gib deine gehostete URL ein
4. Alternativ: Falls das Watchface die alte URL hartcodiert hat, musst du eventuell das Watchface neu kompilieren mit der neuen URL

## ⚙️ Konfigurationsoptionen

Die Seite bietet folgende Einstellungen:

- **Seconds (Sekunden)**: Zeigt Sekunden an (mehr Batterieverbrauch)
- **Outline Frame (Rahmen)**: Zeigt animierten Rahmen (mehr Batterieverbrauch)
- **Pebble Battery (Pebble Batterie)**: Zeigt Batteriestatus der Uhr
- **Phone Battery & Bluetooth**: Zeigt Handy-Batterie und Bluetooth-Status

## 📝 Hinweise

- Die Preview-Funktion ist in dieser standalone Version deaktiviert, da sie externe Bild-Ressourcen benötigt
- Die Einstellungen werden korrekt gespeichert und an die Pebble-Uhr übertragen
- Die Einstellungen werden im localStorage deines Browsers gespeichert

## 🌐 Mehrsprachigkeit

Die Konfigurationsseite unterstützt:
- Englisch (en)
- Vereinfachtes Chinesisch (zh-Hans)
- Traditionelles Chinesisch (zh-Hant)
- Japanisch (ja)

Die Sprache wird automatisch basierend auf deiner Browser-Einstellung ausgewählt.

## 🔗 Original Projekt

Das Original-Projekt findest du hier: https://github.com/programus/pebble-watchface-11weeks

Die originale (nicht mehr verfügbare) Config URL war:
`http://programus.coding.me/pebble-watchface-11weeks/html/config.html`

