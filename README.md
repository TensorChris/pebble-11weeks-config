# Pebble 11 Weeks Watchface - Configuration Page

A self-hosted configuration page for the "11 Weeks" Pebble watchface with live preview functionality.

## 🎯 About This Project

This is a repackaged version of the excellent **11 Weeks Watchface** originally created by **[programus@gmail.com](https://github.com/programus/pebble-watchface-11weeks)**.

The original configuration page is no longer accessible at `http://programus.coding.me/pebble-watchface-11weeks/html/config.html`, making it impossible to customize the watchface settings. This repository provides a working alternative hosted on GitHub Pages.

**Full credit goes to the original author** for creating this beautiful watchface. This project only re-hosts the configuration interface.

## 📦 What's Included

- `config.html` - Configuration page with embedded JavaScript
- `js/` - Watch preview rendering libraries
- `resources/images/` - Watchface graphics for live preview
- `.pbw` file - Repackaged watchface pointing to the new config URL

## 🚀 Live Configuration Page

The configuration page is hosted at:
```
https://tensorchris.github.io/pebble-11weeks-config/config.html
```

## 💾 Installation

1. Download the latest `.pbw` file from the releases
2. Install it on your Pebble watch via the Pebble app
3. Open the watchface settings in the Pebble app
4. Configure your preferred options with live preview!

## ⚙️ Configuration Options

The page offers the following customizable settings:

- **Seconds**: Display seconds (increases battery usage)
- **Outline Frame**: Animated frame border (increases battery usage)
- **Pebble Battery**: Show watch battery level
- **Phone Battery & Bluetooth**: Show phone battery and Bluetooth status

**Note:** Disabling the outline frame and seconds reduces battery consumption as the watchface will update once per minute instead of once per second.

## ✨ Features

- ✅ **Live Preview**: See your changes in real-time with a canvas-based watchface preview
- ✅ **Persistent Settings**: Your configuration is saved and loads correctly each time
- ✅ **Multi-language Support**: Auto-detects your browser language
  - English (en)
  - Simplified Chinese (zh-Hans)
  - Traditional Chinese (zh-Hant)
  - Japanese (ja)

## 🔧 For Developers

### Local Testing

```bash
# Start a local HTTP server
cd pebble-11weeks-config
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/config.html
```

### Hosting Your Own

#### Option 1: GitHub Pages (Free)

1. Fork this repository
2. Enable GitHub Pages in Settings → Pages
3. Use the URL: `https://YOUR-USERNAME.github.io/pebble-11weeks-config/config.html`

#### Option 2: Any Web Server

1. Upload all files to your web server
2. Ensure the page is accessible via HTTPS
3. Update the watchface `.pbw` to point to your URL

### Modifying the Watchface

To point the watchface to your own configuration URL:

1. Clone the [original repository](https://github.com/programus/pebble-watchface-11weeks)
2. Edit `src/js/pebble-js-app.js` and change the URL in the `showConfiguration` event
3. Repackage the `.pbw` file (or use the method described in `GITHUB_PAGES_SETUP.md`)

## 📜 Version History

**v2.1** (Current)
- Settings now persist correctly when reopening configuration
- Live canvas-based watchface preview enabled
- Multi-language support maintained
- Configuration page hosted on GitHub Pages

**v2.0** (Original)
- Created by programus@gmail.com
- Original hosting no longer available

## 🙏 Credits

- **Original Watchface & Config Page**: [programus@gmail.com](https://github.com/programus/pebble-watchface-11weeks)
- **Repackaging & GitHub Pages Hosting**: TensorChris

This project exists solely to keep this wonderful watchface usable. All credit for the design and original implementation goes to the original author.

## 📄 License

This project respects the license of the original 11 Weeks Watchface project. Please refer to the [original repository](https://github.com/programus/pebble-watchface-11weeks) for license information.

## 🔗 Links

- **Original Project**: https://github.com/programus/pebble-watchface-11weeks
- **This Config Page**: https://tensorchris.github.io/pebble-11weeks-config/config.html
- **Original Config URL** (no longer available): `http://programus.coding.me/pebble-watchface-11weeks/html/config.html`
