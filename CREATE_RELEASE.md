# Creating a GitHub Release

## 📦 How to Create a Release

1. **Go to your repository on GitHub**:
   https://github.com/TensorChris/pebble-11weeks-config

2. **Click on "Releases"** (right side, under "About")

3. **Click "Create a new release"**

4. **Fill in the release information**:

   **Choose a tag**: `v2.1`
   - Click "Create new tag: v2.1 on publish"

   **Release title**: `v2.1 - Working Config Page & Live Preview`

   **Description**:
   ```markdown
   ## 🎉 11 Weeks Watchface - Repackaged Version

   This is a repackaged version of the excellent **11 Weeks Watchface** originally created by **programus@gmail.com**.

   The original configuration page is no longer accessible, making it impossible to customize the watchface. This release provides a working alternative with the config page hosted on GitHub Pages.

   ### ✨ What's New in v2.1

   - ✅ **Working Configuration Page**: Hosted at https://tensorchris.github.io/pebble-11weeks-config/config.html
   - ✅ **Persistent Settings**: Your configuration now loads correctly when reopening settings
   - ✅ **Live Preview**: See your changes in real-time with canvas-based watchface preview
   - ✅ **Multi-language Support**: English, Chinese (Simplified/Traditional), Japanese

   ### 📦 Installation

   1. Download the `.pbw` file below
   2. Transfer it to your phone
   3. Open it with the Pebble app
   4. The watchface will be installed automatically

   ### ⚙️ Configuration

   After installation, tap the watchface settings in the Pebble app to customize:
   - Seconds display (increases battery usage)
   - Outline frame animation (increases battery usage)
   - Pebble battery indicator
   - Phone battery & Bluetooth status

   ### 🙏 Credits

   **Original Watchface**: [programus@gmail.com](https://github.com/programus/pebble-watchface-11weeks)

   This project exists solely to keep this wonderful watchface usable. All credit for the design and original implementation goes to the original author.
   ```

5. **Attach the .pbw file**:
   - Drag and drop: `/Users/chris/Downloads/11weeks-v2.1-tensorchris-FINAL.pbw`
   - Or click "Attach binaries" and select the file

6. **Click "Publish release"**

## 🎯 After Publishing

The release will be available at:
```
https://github.com/TensorChris/pebble-11weeks-config/releases
```

Users can download the `.pbw` file directly from there!

## 🔄 Future Releases

For future updates:
1. Update the version number in `appinfo.json`
2. Rebuild the `.pbw` file
3. Create a new release with the new tag (e.g., `v2.2`)
