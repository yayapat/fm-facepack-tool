"""FM Player Face Tool Pro - Background removal, resize, and facepack builder.

Supports both CLI batch processing and a PyQt6 GUI with drag-and-drop.
Generates FM-compatible config.xml for portrait mapping.
"""

import sys
import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps
from rembg import remove

try:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QIcon, QImage, QIntValidator, QPixmap
    from PyQt6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QButtonGroup,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QProgressBar,
        QPushButton,
        QRadioButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

STYLESHEET = """
/* Base */
QWidget {
    background-color: #ffffff;
    color: #1a1a2e;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}
QLabel {
    color: #64748b;
    background: transparent;
    border: none;
}

/* Buttons */
QPushButton {
    background-color: #f8fafc;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #cbd5e1;
}
QPushButton:pressed {
    background-color: #e2e8f0;
}
QPushButton:disabled {
    background-color: #f8fafc;
    color: #cbd5e1;
    border-color: #f1f5f9;
}

/* Primary action button */
QPushButton#btn_run {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #818cf8, stop:1 #6366f1);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    padding: 11px;
}
QPushButton#btn_run:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #4f46e5);
}
QPushButton#btn_run:disabled {
    background: #e2e8f0;
    color: #94a3b8;
}

/* Clear button */
QPushButton#btn_clear {
    color: #ef4444;
    border-color: #fecaca;
}
QPushButton#btn_clear:hover {
    background-color: #fef2f2;
    border-color: #fca5a5;
}

/* Radio & Checkbox */
QRadioButton, QCheckBox {
    color: #334155;
    spacing: 6px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

/* Inputs */
QLineEdit {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 5px 10px;
    color: #1e293b;
    selection-background-color: #818cf8;
}
QLineEdit:focus {
    border-color: #818cf8;
}
QLineEdit:disabled {
    background-color: #f1f5f9;
    color: #cbd5e1;
}

/* Progress bar */
QProgressBar {
    border: none;
    background-color: #f1f5f9;
    border-radius: 3px;
    height: 6px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #818cf8, stop:1 #6366f1);
    border-radius: 3px;
}

/* Log output */
QTextEdit {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px;
    color: #475569;
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    selection-background-color: #818cf8;
}

/* File list */
QListWidget {
    background-color: #f8fafc;
    border: 1.5px dashed #cbd5e1;
    border-radius: 10px;
    padding: 6px;
    font-size: 12px;
    color: #475569;
    outline: none;
}
QListWidget:focus {
    border-color: #818cf8;
}
QListWidget::item {
    padding: 2px 4px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #eef2ff;
    color: #4338ca;
}
QListWidget::item:hover {
    background-color: #f1f5f9;
}

/* Scrollbars - thin and minimal */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
    border: none;
}
QScrollBar::handle:vertical {
    background: rgba(100, 116, 139, 0.35);
    min-height: 30px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(100, 116, 139, 0.55);
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
    border: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0;
    border: none;
}
QScrollBar::handle:horizontal {
    background: rgba(100, 116, 139, 0.35);
    min-width: 30px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(100, 116, 139, 0.55);
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0;
    border: none;
}
"""

# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------


def resize_maintain_aspect(
    image: Image.Image,
    target_size: tuple[int, int],
    enhance_sharp: bool = False,
) -> Image.Image:
    """Resize *image* to fit *target_size*, center on a transparent canvas."""
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    if enhance_sharp:
        image = image.filter(
            ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3)
        )
    background = Image.new("RGBA", target_size, (250, 250, 250, 0))
    offset = (
        (target_size[0] - image.width) // 2,
        (target_size[1] - image.height) // 2,
    )
    background.paste(image, offset, image)
    return background


def process_fm_face(
    input_image_path: str,
    target_dimensions: tuple[int, int],
    output_folder: str,
    output_filename: str,
    enhance_sharp: bool = False,
    logger=print,
) -> Image.Image | None:
    """Remove background, resize, and save a single face image.

    Returns the processed PIL Image on success, ``None`` on failure.
    """
    input_path = Path(input_image_path)
    output_dir = Path(output_folder)

    if not input_path.exists():
        logger(f"Error: File not found '{input_path.name}'")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    # Strip any extension the user may have typed and force .png
    clean_filename = Path(output_filename).stem + ".png"
    output_path = output_dir / clean_filename

    logger(f"Processing: {input_path.name}")
    logger(f"Target Size: {target_dimensions[0]}x{target_dimensions[1]} px")
    logger(f"Output Name: {clean_filename}")
    if enhance_sharp:
        logger("Option: Unsharp Mask Enabled")
    logger("Background Removal: Processing...")

    try:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            no_bg = remove(img, model="u2net")

            logger("Resizing: Centering image with padding...")
            final = resize_maintain_aspect(
                no_bg, target_dimensions, enhance_sharp=enhance_sharp
            )
            final.save(output_path, "PNG", optimize=True)
            logger(f"Saved: {output_path.name}")

        logger(f"Done: {output_dir.resolve()}\n")
        return final
    except Exception as e:
        logger(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# config.xml generation
# ---------------------------------------------------------------------------


def generate_config_xml(output_folder: str, logger=print) -> bool:
    """Generate an FM-compatible ``config.xml`` from all PNGs in *output_folder*."""
    output_dir = Path(output_folder)
    png_files = sorted(output_dir.glob("*.png"))

    if not png_files:
        logger("config.xml: No PNG files found, skipping.")
        return False

    lines = [
        "<record>",
        "\t<!-- resource manager options -->",
        "",
        "\t<!-- dont preload anything in this folder -->",
        '\t<boolean id="preload" value="false"/>',
        "",
        "\t<!-- turn off auto mapping -->",
        '\t<boolean id="amap" value="false"/>',
        "",
        '\t<list id="maps">',
    ]
    for png in png_files:
        uid = png.stem
        lines.append(
            f'\t\t<record from="{uid}" '
            f'to="graphics/pictures/person/{uid}/portrait"/>'
        )
    lines.append("\t</list>")
    lines.append("</record>")

    config_path = output_dir / "config.xml"
    config_path.write_text("\n".join(lines), encoding="utf-8")
    logger(f"config.xml: {len(png_files)} entries written.")
    return True


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def collect_images(path: str) -> list[str]:
    """Return image file paths. Accepts a single file or a directory."""
    p = Path(path)
    if p.is_dir():
        return sorted(
            str(f)
            for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        )
    return [str(p)]


# ---------------------------------------------------------------------------
# GUI (PyQt6) — only defined when the library is available
# ---------------------------------------------------------------------------

if PYQT6_AVAILABLE:

    class WorkerThread(QThread):
        """Background thread that processes images without blocking the UI."""

        status_signal = pyqtSignal(str)
        progress_signal = pyqtSignal(int, int)
        preview_signal = pyqtSignal(object)
        finished_signal = pyqtSignal(bool)

        def __init__(
            self,
            input_paths: list[str],
            target_dimensions: tuple[int, int],
            output_folder: str,
            output_filenames: list[str],
            enhance_sharp: bool,
            gen_config: bool,
        ):
            super().__init__()
            self.input_paths = input_paths
            self.target_dimensions = target_dimensions
            self.output_folder = output_folder
            self.output_filenames = output_filenames
            self.enhance_sharp = enhance_sharp
            self.gen_config = gen_config

        def run(self):
            total = len(self.input_paths)
            all_ok = True

            for i, (path, name) in enumerate(
                zip(self.input_paths, self.output_filenames)
            ):
                self.progress_signal.emit(i, total)
                self.status_signal.emit(f"--- [{i + 1}/{total}] ---")
                result = process_fm_face(
                    path,
                    self.target_dimensions,
                    self.output_folder,
                    name,
                    enhance_sharp=self.enhance_sharp,
                    logger=self._log,
                )
                if result is None:
                    all_ok = False
                else:
                    self.preview_signal.emit(result)

            self.progress_signal.emit(total, total)
            if self.gen_config:
                generate_config_xml(self.output_folder, logger=self._log)
            self.finished_signal.emit(all_ok)

        def _log(self, text: str):
            self.status_signal.emit(text)

    class DropListWidget(QListWidget):
        """QListWidget subclass that accepts dropped image files/folders."""

        files_dropped = pyqtSignal(list)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
            self.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )

        def dragEnterEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                super().dragEnterEvent(event)

        def dragMoveEvent(self, event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                super().dragMoveEvent(event)

        def dropEvent(self, event):
            if not event.mimeData().hasUrls():
                super().dropEvent(event)
                return
            paths: list[str] = []
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                    paths.append(str(p))
                elif p.is_dir():
                    paths.extend(collect_images(str(p)))
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()

    class FMGraphicsApp(QWidget):
        """Main application window."""

        def __init__(self):
            super().__init__()
            self.file_list: list[str] = []
            self.selected_output_dir = str(Path("fm_outputs").resolve())
            self._init_ui()

        # ---- UI construction -------------------------------------------------

        def _init_ui(self):
            self.setWindowTitle("FM Player Face Tool Pro")
            self.resize(720, 680)
            self.setStyleSheet(STYLESHEET)
            icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

            root = QVBoxLayout()
            root.setSpacing(12)
            root.setContentsMargins(24, 24, 24, 24)

            root.addLayout(self._build_file_header())
            root.addWidget(self._build_file_list())
            root.addLayout(self._build_output_row())
            root.addLayout(self._build_size_row())
            root.addLayout(self._build_options_row())
            root.addWidget(self._build_run_button())
            root.addWidget(self._build_progress_bar())
            root.addLayout(self._build_bottom_panel(), stretch=1)

            self.setLayout(root)

        def _build_file_header(self) -> QHBoxLayout:
            row = QHBoxLayout()
            lbl = QLabel("Input Images")
            lbl.setStyleSheet(
                "font-weight: 600; color: #1e293b; font-size: 13px;"
            )
            btn_files = QPushButton("Add Files")
            btn_folder = QPushButton("Add Folder")
            btn_clear = QPushButton("Clear")
            btn_clear.setObjectName("btn_clear")

            btn_files.clicked.connect(self._browse_files)
            btn_folder.clicked.connect(self._browse_folder)
            btn_clear.clicked.connect(self._clear_files)

            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(btn_files)
            row.addWidget(btn_folder)
            row.addWidget(btn_clear)
            return row

        def _build_file_list(self) -> DropListWidget:
            self.file_list_widget = DropListWidget()
            self.file_list_widget.setMinimumHeight(80)
            self.file_list_widget.setMaximumHeight(120)
            self.file_list_widget.files_dropped.connect(self._add_files)
            return self.file_list_widget

        def _build_output_row(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.lbl_output_path = QLabel(Path(self.selected_output_dir).name)
            self.lbl_output_path.setToolTip(self.selected_output_dir)
            self.lbl_output_path.setStyleSheet(
                "color: #6366f1; font-weight: 600;"
            )
            btn = QPushButton("Change")
            btn.clicked.connect(self._browse_output_folder)
            row.addWidget(self.lbl_output_path, stretch=4)
            row.addWidget(btn, stretch=0)
            return row

        def _build_size_row(self) -> QHBoxLayout:
            row = QHBoxLayout()
            lbl = QLabel("Size")
            lbl.setStyleSheet("font-weight: 600; color: #1e293b;")
            row.addWidget(lbl)

            self.btn_group = QButtonGroup(self)
            self.rad_220 = QRadioButton("220 x 276")
            self.rad_220.setChecked(True)
            self.rad_192 = QRadioButton("192 x 192")
            self.rad_custom = QRadioButton("Custom:")
            for rb in (self.rad_220, self.rad_192, self.rad_custom):
                self.btn_group.addButton(rb)
                row.addWidget(rb)

            self.txt_width = QLineEdit()
            self.txt_width.setPlaceholderText("W")
            self.txt_width.setFixedWidth(44)
            self.txt_width.setValidator(QIntValidator(1, 9999))
            self.txt_width.setEnabled(False)

            lbl_x = QLabel("x")
            lbl_x.setStyleSheet("color: #94a3b8;")

            self.txt_height = QLineEdit()
            self.txt_height.setPlaceholderText("H")
            self.txt_height.setFixedWidth(44)
            self.txt_height.setValidator(QIntValidator(1, 9999))
            self.txt_height.setEnabled(False)

            row.addWidget(self.txt_width)
            row.addWidget(lbl_x)
            row.addWidget(self.txt_height)
            row.addStretch()

            self.btn_group.buttonToggled.connect(self._toggle_custom_inputs)
            return row

        def _build_options_row(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.chk_sharp = QCheckBox("Enhance Sharpness")
            self.chk_sharp.setStyleSheet("color: #f59e0b;")
            self.chk_config = QCheckBox("Generate config.xml")
            self.chk_config.setChecked(True)
            self.chk_config.setStyleSheet("color: #6366f1;")
            row.addWidget(self.chk_sharp)
            row.addWidget(self.chk_config)
            row.addStretch()
            return row

        def _build_run_button(self) -> QPushButton:
            self.btn_run = QPushButton("Process Image(s)")
            self.btn_run.setObjectName("btn_run")
            self.btn_run.setEnabled(False)
            self.btn_run.clicked.connect(self._start_processing)
            return self.btn_run

        def _build_progress_bar(self) -> QProgressBar:
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(False)
            return self.progress_bar

        def _build_bottom_panel(self) -> QHBoxLayout:
            panel = QHBoxLayout()
            panel.setSpacing(14)

            # Preview
            preview_col = QVBoxLayout()
            preview_col.setSpacing(6)
            lbl_title = QLabel("Preview")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_title.setStyleSheet(
                "font-weight: 600; color: #64748b; font-size: 11px;"
            )
            self.lbl_preview = QLabel("No preview")
            self.lbl_preview.setFixedSize(180, 220)
            self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_preview.setStyleSheet(
                "background-color: #f8fafc; border: 1px solid #e2e8f0;"
                "border-radius: 10px; color: #cbd5e1; font-size: 12px;"
            )
            preview_col.addWidget(lbl_title)
            preview_col.addWidget(self.lbl_preview)
            preview_col.addStretch()
            panel.addLayout(preview_col)

            # Log
            self.log_output = QTextEdit()
            self.log_output.setReadOnly(True)
            self.log_output.setPlaceholderText(
                "Status log will be displayed here..."
            )
            panel.addWidget(self.log_output, stretch=1)
            return panel

        # ---- Slots -----------------------------------------------------------

        def _toggle_custom_inputs(self):
            is_custom = self.rad_custom.isChecked()
            self.txt_width.setEnabled(is_custom)
            self.txt_height.setEnabled(is_custom)
            if not is_custom:
                self.txt_width.clear()
                self.txt_height.clear()

        def _add_files(self, paths: list[str]):
            """Append *paths* to the input list, skipping duplicates."""
            existing = set(self.file_list)
            for p in paths:
                if p not in existing:
                    self.file_list.append(p)
                    self.file_list_widget.addItem(Path(p).name)
                    existing.add(p)
            self.btn_run.setEnabled(bool(self.file_list))

        def _browse_files(self):
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Images",
                "",
                "Image Files (*.jpg *.jpeg *.png *.webp *.bmp *.tiff)",
            )
            if files:
                self._add_files(files)

        def _browse_folder(self):
            folder = QFileDialog.getExistingDirectory(
                self, "Select Folder with Images"
            )
            if not folder:
                return
            images = collect_images(folder)
            if images:
                self._add_files(images)
            else:
                self.log_output.setText(f"No image files found in: {folder}")

        def _clear_files(self):
            self.file_list.clear()
            self.file_list_widget.clear()
            self.btn_run.setEnabled(False)
            self.lbl_preview.setPixmap(QPixmap())
            self.lbl_preview.setText("No preview")

        def _browse_output_folder(self):
            folder = QFileDialog.getExistingDirectory(
                self, "Select Output Folder"
            )
            if folder:
                self.selected_output_dir = folder
                self.lbl_output_path.setText(Path(folder).name)
                self.lbl_output_path.setToolTip(folder)

        def _start_processing(self):
            if not self.file_list:
                return

            target_dims = self._get_target_dimensions()
            if target_dims is None:
                return

            output_names = [Path(p).stem for p in self.file_list]

            self.btn_run.setEnabled(False)
            self.progress_bar.setRange(0, len(self.file_list))
            self.progress_bar.setValue(0)
            self.log_output.clear()

            self._worker = WorkerThread(
                self.file_list,
                target_dims,
                self.selected_output_dir,
                output_names,
                self.chk_sharp.isChecked(),
                self.chk_config.isChecked(),
            )
            self._worker.status_signal.connect(self._on_log)
            self._worker.progress_signal.connect(self._on_progress)
            self._worker.preview_signal.connect(self._on_preview)
            self._worker.finished_signal.connect(self._on_finished)
            self._worker.start()

        def _get_target_dimensions(self) -> tuple[int, int] | None:
            """Read the selected size. Returns ``None`` on validation error."""
            if self.rad_220.isChecked():
                return (220, 276)
            if self.rad_192.isChecked():
                return (192, 192)
            w_str = self.txt_width.text().strip()
            h_str = self.txt_height.text().strip()
            if not w_str or not h_str:
                self.log_output.setText(
                    "Error: Enter both Width and Height for custom size."
                )
                return None
            return (int(w_str), int(h_str))

        def _on_log(self, text: str):
            self.log_output.append(text)

        def _on_progress(self, current: int, total: int):
            self.progress_bar.setValue(current)

        def _on_preview(self, pil_image: Image.Image):
            """Convert a PIL Image to QPixmap and display it."""
            buf = BytesIO()
            pil_image.save(buf, format="PNG")
            buf.seek(0)
            qimg = QImage()
            qimg.loadFromData(buf.read())
            pixmap = QPixmap.fromImage(qimg).scaled(
                self.lbl_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_preview.setPixmap(pixmap)

        def _on_finished(self, success: bool):
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.btn_run.setEnabled(True)
            n = len(self.file_list)
            if success:
                self.log_output.append(
                    f"\nAll {n} image(s) processed successfully!"
                )
            else:
                self.log_output.append(
                    "\nFinished with errors. Check the log above."
                )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _run_cli(args: argparse.Namespace):
    """Execute CLI batch/single processing."""
    try:
        w, h = args.size.strip().lower().split("x")
        target_dims = (int(w), int(h))
    except (ValueError, TypeError):
        print(f"Error: Invalid size '{args.size}'. Use e.g. '220x276'.")
        sys.exit(1)

    image_paths = collect_images(args.input)
    if not image_paths:
        print(f"Error: No image files found at '{args.input}'")
        sys.exit(1)

    is_batch = len(image_paths) > 1
    if is_batch:
        print(f"Batch mode: {len(image_paths)} images found.")

    all_ok = True
    for i, img_path in enumerate(image_paths):
        if is_batch:
            print(f"--- [{i + 1}/{len(image_paths)}] ---")
        # In batch mode always use the original filename
        name = Path(img_path).stem if is_batch else (args.name or Path(img_path).stem)
        result = process_fm_face(
            img_path, target_dims, args.output, name, enhance_sharp=args.sharp
        )
        if result is None:
            all_ok = False

    if args.config:
        generate_config_xml(args.output)

    sys.exit(0 if all_ok else 1)


def _run_gui():
    """Launch the PyQt6 GUI."""
    if not PYQT6_AVAILABLE:
        print("Error: PyQt6 is not installed.")
        sys.exit(1)
    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = FMGraphicsApp()
    window.show()
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(
        description="FM Player Face Converter & Resizer (CLI & GUI)"
    )
    parser.add_argument(
        "-i", "--input", help="Image path or folder (triggers CLI mode)"
    )
    parser.add_argument(
        "-s", "--size", default="220x276",
        help="Output size, e.g. '220x276' (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output", default="fm_outputs", help="Output directory"
    )
    parser.add_argument(
        "-n", "--name",
        help="Output filename (no extension). Ignored in batch mode.",
    )
    parser.add_argument(
        "--sharp", action="store_true", help="Apply unsharp mask"
    )
    parser.add_argument(
        "--config", action="store_true", help="Generate config.xml"
    )
    args = parser.parse_args()

    if args.input is not None:
        _run_cli(args)
    else:
        _run_gui()


if __name__ == "__main__":
    main()