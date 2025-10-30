# GitHub Pages Setup Anleitung

## 📋 Schritt-für-Schritt Anleitung

### Schritt 1: GitHub Repository erstellen

1. Gehe zu https://github.com/new
2. Erstelle ein neues Repository mit folgenden Einstellungen:
   - **Repository name**: `pebble-11weeks-config` (oder ein anderer Name deiner Wahl)
   - **Description**: "Configuration page for Pebble 11 Weeks Watchface"
   - **Visibility**: Public (wichtig für GitHub Pages!)
   - **NICHT** "Initialize this repository with a README" ankreuzen (wir haben bereits Dateien)
3. Klicke auf "Create repository"

### Schritt 2: Repository auf GitHub pushen

Nach dem Erstellen zeigt GitHub dir Befehle an. Verwende diese im Terminal:

```bash
cd "/Users/chris/Library/CloudStorage/OneDrive-TensorFiveGmbH/Apps/pebble-11weeks-config"

# Füge das GitHub Repository als Remote hinzu
git remote add origin https://github.com/DEIN-USERNAME/pebble-11weeks-config.git

# Push zum Repository
git push -u origin main
```

**Wichtig**: Ersetze `DEIN-USERNAME` mit deinem GitHub Benutzernamen!

### Schritt 3: GitHub Pages aktivieren

1. Gehe zu deinem Repository auf GitHub
2. Klicke auf **Settings** (oben rechts)
3. Scrolle im linken Menü zu **Pages**
4. Unter "Source" wähle:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
5. Klicke auf **Save**

### Schritt 4: Auf Deployment warten

1. GitHub Pages baut deine Seite automatisch (dauert 1-2 Minuten)
2. Wenn fertig, siehst du eine grüne Box mit der URL:
   ```
   Your site is live at https://DEIN-USERNAME.github.io/pebble-11weeks-config/
   ```
3. Deine Config-Seite ist dann unter:
   ```
   https://DEIN-USERNAME.github.io/pebble-11weeks-config/config.html
   ```

## 🎯 Die finale URL

Nach dem Deployment kannst du diese URL in deiner Pebble App verwenden:

```
https://DEIN-USERNAME.github.io/pebble-11weeks-config/config.html
```

## 🔄 Änderungen hochladen

Falls du später Änderungen machst:

```bash
cd "/Users/chris/Library/CloudStorage/OneDrive-TensorFiveGmbH/Apps/pebble-11weeks-config"
git add .
git commit -m "Update configuration page"
git push
```

GitHub Pages wird automatisch neu gebaut!

## ✅ Testen

Nach dem Deployment:
1. Öffne die URL im Browser
2. Teste alle Einstellungen
3. Klicke auf "SAVE" - es sollte eine URL mit den Einstellungen generiert werden

## 🔧 Troubleshooting

**Problem**: "404 - File not found"
- **Lösung**: Warte 2-3 Minuten, GitHub Pages braucht Zeit zum Bauen

**Problem**: GitHub fragt nach Authentifizierung beim Push
- **Lösung**: Verwende ein Personal Access Token statt Passwort
  - Gehe zu GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
  - "Generate new token" → Wähle "repo" Scope
  - Verwende das Token als Passwort

**Problem**: Die Seite wird nicht angezeigt
- **Lösung**: Prüfe, ob das Repository **Public** ist
