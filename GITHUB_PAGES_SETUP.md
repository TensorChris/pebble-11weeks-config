# GitHub Pages Setup Guide

## 📋 Step-by-Step Instructions

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository with the following settings:
   - **Repository name**: `pebble-11weeks-config` (or any name you prefer)
   - **Description**: "Configuration page for Pebble 11 Weeks Watchface"
   - **Visibility**: Public (required for GitHub Pages!)
   - **DO NOT** check "Initialize this repository with a README" (we already have files)
3. Click "Create repository"

### Step 2: Push Repository to GitHub

After creating the repository, GitHub will show you commands. Use these in the terminal:

```bash
cd "/Users/chris/Library/CloudStorage/OneDrive-TensorFiveGmbH/Apps/pebble-11weeks-config"

# Add the GitHub repository as remote
git remote add origin https://github.com/YOUR-USERNAME/pebble-11weeks-config.git

# Push to the repository
git push -u origin main
```

**Important**: Replace `YOUR-USERNAME` with your GitHub username!

### Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** (top right)
3. Scroll in the left menu to **Pages**
4. Under "Source" select:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
5. Click **Save**

### Step 4: Wait for Deployment

1. GitHub Pages automatically builds your site (takes 1-2 minutes)
2. When finished, you'll see a green box with the URL:
   ```
   Your site is live at https://YOUR-USERNAME.github.io/pebble-11weeks-config/
   ```
3. Your config page will be at:
   ```
   https://YOUR-USERNAME.github.io/pebble-11weeks-config/config.html
   ```

## 🎯 The Final URL

After deployment, you can use this URL in your Pebble app:

```
https://YOUR-USERNAME.github.io/pebble-11weeks-config/config.html
```

## 🔄 Pushing Updates

If you make changes later:

```bash
cd "/Users/chris/Library/CloudStorage/OneDrive-TensorFiveGmbH/Apps/pebble-11weeks-config"
git add .
git commit -m "Update configuration page"
git push
```

GitHub Pages will automatically rebuild!

## ✅ Testing

After deployment:
1. Open the URL in your browser
2. Test all settings
3. Click "SAVE" - it should generate a URL with your settings

## 🔧 Troubleshooting

**Problem**: "404 - File not found"
- **Solution**: Wait 2-3 minutes, GitHub Pages needs time to build

**Problem**: GitHub asks for authentication when pushing
- **Solution**: Use a Personal Access Token instead of password
  - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
  - "Generate new token" → Select "repo" scope
  - Use the token as password

**Problem**: The page isn't displayed
- **Solution**: Check if the repository is **Public**
