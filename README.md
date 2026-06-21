# FM Player Face Tool Pro

A desktop tool for Football Manager facepack creation. Removes image backgrounds, resizes portraits to FM-compatible dimensions, and generates the required `config.xml` mapping file.

Supports both a graphical interface (PyQt6) and command-line batch processing.

---

## Features

- Background removal powered by U2Net (via rembg)
- Resize to standard FM sizes (220x276, 192x192) or custom dimensions
- Batch processing - process entire folders at once
- Drag and drop support in the GUI
- Live preview of processed images
- Automatic `config.xml` generation for FM facepacks
- Optional sharpness enhancement (unsharp mask)
- Cross-platform: Linux and Windows

---

## Installation

### Prerequisites

- Python 3.10 or later
- pip

### Clone and install dependencies

```bash
git clone https://github.com/your-username/fmtool.git
cd fmtool
```

**Linux (Ubuntu/Debian)**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

### GUI Mode

Run without arguments to open the graphical interface:

```bash
python fm_tool.py
```

1. Click **Add Files** or **Add Folder**, or drag and drop images into the list.
2. Choose an output folder and target size.
3. Check **Generate config.xml** if building a facepack.
4. Click **Process Image(s)**.

### CLI Mode

Pass `-i` to run in command-line mode:

```bash
# Single image
python fm_tool.py -i photo.jpg -n 12345 -o output/

# Batch process a folder
python fm_tool.py -i ./faces/ -o output/ --config

# Custom size with sharpness
python fm_tool.py -i photo.jpg -s 300x300 --sharp
```

**CLI arguments**

| Argument | Description | Default |
|---|---|---|
| `-i`, `--input` | Image path or folder (triggers CLI mode) | - |
| `-s`, `--size` | Output size, e.g. `220x276` | `220x276` |
| `-o`, `--output` | Output directory | `fm_outputs` |
| `-n`, `--name` | Output filename without extension | input filename |
| `--sharp` | Apply unsharp mask filter | off |
| `--config` | Generate `config.xml` after processing | off |

---

## Building Executables

### Prerequisites

```bash
pip install pyinstaller
```

### Windows (.exe)

```bash
build_windows.bat
```

Output: `dist/FMFaceTool.exe`

### Linux (AppImage)

Download [appimagetool](https://github.com/AppImage/AppImageKit/releases) first:

```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

Then build:

```bash
./build_linux.sh
```

Output: `dist/FMFaceTool-x86_64.AppImage`

---

## Project Structure

```
fmtool/
  assets/
    icon.png            # App icon (Linux / PyQt6)
    icon.ico            # App icon (Windows)
  fm_tool.py            # Application source
  requirements.txt      # Python dependencies
  build.spec            # PyInstaller configuration
  build_linux.sh        # Linux AppImage build script
  build_windows.bat     # Windows .exe build script
  .gitignore
  README.md
```

---

## config.xml Format

The generated `config.xml` follows the standard FM resource mapping format:

```xml
<record>
    <boolean id="preload" value="false"/>
    <boolean id="amap" value="false"/>
    <list id="maps">
        <record from="12345" to="graphics/pictures/person/12345/portrait"/>
        <record from="67890" to="graphics/pictures/person/67890/portrait"/>
    </list>
</record>
```

Image filenames (without `.png`) are used as the UID for mapping.

---

## License

MIT
