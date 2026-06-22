#!/usr/bin/env python3
"""FM Player Face Tool Pro - Background removal, resize, and facepack builder.

Supports both CLI batch processing and a PyQt6 GUI with drag-and-drop.
Generates FM-compatible config.xml for portrait mapping.
"""

import re
import sys
import argparse
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

TRANSLATIONS = {
    "en": {
        "title": "FM Player Face Tool Pro",
        "input_images": "Input Images",
        "add_files": "Add Files",
        "add_folder": "Add Folder",
        "clear": "Clear",
        "change": "Change",
        "size": "Size",
        "custom": "Custom:",
        "filename": "Filename",
        "use_original": "Use original",
        "custom_name": "Custom Name:",
        "filename_hint": "e.g. player_id",
        "enhance_sharpness": "Enhance Sharpness",
        "generate_config": "Generate config.xml",
        "overwrite_config": "Overwrite existing config",
        "overwrite_dupes": "Overwrite duplicate IDs/files",
        "map_all_png": "Map all PNGs in folder",
        "process_images": "Process Image(s)",
        "preview": "Preview",
        "no_preview": "No preview",
        "status_log_placeholder": "Status log will be displayed here...",
        "language": "Language / ภาษา:",
        "error_size": "Error: Enter both Width and Height for custom size.",
        "error_custom_name": "Error: Enter a custom filename.",
        "all_processed_success": "\nAll {} image(s) processed successfully!",
        "finished_errors": "\nFinished with errors. Check the log above.",
        "context_remove": "Remove Selected Item(s)",
        "processing_header": "--- [{}/{}] ---",
        "log_processing": "Processing: {}",
        "log_error_not_found": "Error: File not found '{}'",
        "log_target_size": "Target Size: {}x{} px",
        "log_output_name": "Output Name: {}",
        "log_sharp_enabled": "Option: Unsharp Mask Enabled",
        "log_bg_removal": "Background Removal: Processing...",
        "log_resizing": "Resizing: Centering image with padding...",
        "log_saved": "Saved: {}",
        "log_done": "Done: {}\n",
        "log_xml_no_png": "config.xml: No processed files, skipping.",
        "log_xml_merged": "config.xml: Merged {} new entry(ies) into existing file ({} existing).",
        "log_xml_written": "config.xml: {} entries written.",
    },
    "th": {
        "title": "FM Player Face Tool Pro",
        "input_images": "รูปภาพ",
        "add_files": "เพิ่มไฟล์",
        "add_folder": "เพิ่มโฟลเดอร์",
        "clear": "เคลียร์รายการ",
        "change": "เปลี่ยนโฟลเดอร์",
        "size": "ขนาด (Size)",
        "custom": "กำหนดเอง (Custom):",
        "filename": "ชื่อไฟล์ (Filename)",
        "use_original": "ใช้ชื่อเดิม",
        "custom_name": "ระบุชื่อเอง:",
        "filename_hint": "เช่น player_id",
        "enhance_sharpness": "เพิ่มความคมชัด (Enhance)",
        "generate_config": "สร้างไฟล์ config.xml",
        "overwrite_config": "เขียนทับไฟล์ config.xml เดิม",
        "overwrite_dupes": "เขียนทับรูปภาพ/ID ที่ซ้ำกันทันที",
        "map_all_png": "สร้าง config จากไฟล์ PNG ทั้งหมดในโฟลเดอร์",
        "process_images": "เริ่มประมวลผล (Process)",
        "preview": "พรีวิว (Preview)",
        "no_preview": "ไม่มีรูปพรีวิว",
        "status_log_placeholder": "ข้อมูลและประวัติการทำงานจะแสดงตรงนี้...",
        "language": "ภาษา (Language):",
        "error_size": "ข้อผิดพลาด: กรุณากรอกทั้งความกว้างและความสูงสำหรับขนาดที่กำหนดเอง",
        "error_custom_name": "ข้อผิดพลาด: กรุณาระบุชื่อไฟล์ที่ต้องการตั้ง",
        "all_processed_success": "\nประมวลผลรูปภาพทั้งหมด {} รูปเสร็จสมบูรณ์!",
        "finished_errors": "\nการประมวลผลมีข้อผิดพลาด กรุณาตรวจสอบข้อมูลด้านบน",
        "context_remove": "ลบรายการที่เลือก",
        "processing_header": "--- รูปภาพที่ [{}/{}] ---",
        "log_processing": "กำลังประมวลผล: {}",
        "log_error_not_found": "ข้อผิดพลาด: ไม่พบไฟล์ '{}'",
        "log_target_size": "ขนาดเป้าหมาย: {}x{} px",
        "log_output_name": "ชื่อไฟล์ผลลัพธ์: {}",
        "log_sharp_enabled": "เปิดใช้งาน: เพิ่มความคมชัดภาพ",
        "log_bg_removal": "การลบพื้นหลัง: กำลังประมวลผล...",
        "log_resizing": "การปรับขนาด: กำลังจัดรูปให้อยู่กึ่งกลาง...",
        "log_saved": "เซฟไฟล์สำเร็จ: {}",
        "log_done": "เสร็จเรียบร้อย: {}\n",
        "log_xml_no_png": "config.xml: ไม่มีไฟล์รูปภาพสำหรับสร้าง config, ข้ามขั้นตอน",
        "log_xml_merged": "config.xml: อัปเดตเพิ่มรายการใหม่ {} รายการ (มีอยู่เดิมแล้ว {} รายการ)",
        "log_xml_written": "config.xml: เขียนข้อมูลสำเร็จทั้งหมด {} รายการ",
    }
}

from PIL import Image, ImageFilter, ImageOps
from rembg import remove

try:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QAction, QIcon, QImage, QIntValidator, QPixmap
    from PyQt6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMenu,
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

/* Dropdowns */
QComboBox {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 5px 12px;
    color: #334155;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #cbd5e1;
    background-color: #f1f5f9;
}
QComboBox:focus {
    border-color: #818cf8;
}
QComboBox:disabled {
    background-color: #f1f5f9;
    color: #cbd5e1;
    border-color: #e2e8f0;
}
QComboBox::drop-down {
    width: 0px;
    border: none;
}
QComboBox::down-arrow {
    width: 0px;
    height: 0px;
    border: none;
}
QComboBox::down-arrow:disabled {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    outline: 0px;
    selection-background-color: #eef2ff;
    selection-color: #4338ca;
}
QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    border-radius: 6px;
    color: #475569;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #f1f5f9;
    color: #1e293b;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #eef2ff;
    color: #4338ca;
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
    lang: str = "en",
) -> Image.Image | None:
    """Remove background, resize, and save a single face image.

    Returns the processed PIL Image on success, ``None`` on failure.
    """
    input_path = Path(input_image_path)
    output_dir = Path(output_folder)
    t = TRANSLATIONS[lang]

    if not input_path.exists():
        logger(t["log_error_not_found"].format(input_path.name))
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    # Strip any extension the user may have typed and force .png
    clean_filename = Path(output_filename).stem + ".png"
    output_path = output_dir / clean_filename

    logger(t["log_processing"].format(input_path.name))
    logger(t["log_target_size"].format(target_dimensions[0], target_dimensions[1]))
    logger(t["log_output_name"].format(clean_filename))
    if enhance_sharp:
        logger(t["log_sharp_enabled"])
    logger(t["log_bg_removal"])

    try:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            no_bg = remove(img, model="u2net")

            logger(t["log_resizing"])
            final = resize_maintain_aspect(
                no_bg, target_dimensions, enhance_sharp=enhance_sharp
            )
            final.save(output_path, "PNG", optimize=True)
            logger(t["log_saved"].format(output_path.name))

        logger(t["log_done"].format(output_dir.resolve()))
        return final
    except Exception as e:
        logger(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# config.xml generation
# ---------------------------------------------------------------------------


def _parse_existing_records(config_path: Path) -> list[tuple[str, str]]:
    """Parse existing config.xml and return a list of (from_id, to_path) tuples, preserving order."""
    records: list[tuple[str, str]] = []
    if not config_path.exists():
        return records
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        maps_list = root.find(".//list[@id='maps']")
        if maps_list is not None:
            for rec in maps_list.findall("record"):
                f = rec.get("from")
                t = rec.get("to")
                if f and t:
                    records.append((f, t))
            if records:
                return records
    except Exception:
        pass

    # Fallback to regex in case of XML parse errors or partial content
    try:
        text = config_path.read_text(encoding="utf-8")
        pattern = r'<record\s+from="([^"]+)"\s+to="([^"]+)"\s*/?>'
        for m in re.finditer(pattern, text):
            records.append((m.group(1), m.group(2)))
    except Exception:
        pass
    return records

def generate_config_xml(
    output_folder: str,
    processed_names: list[str] = None,
    overwrite: bool = False,
    logger=print,
    lang: str = "en",
) -> bool:
    """Generate or merge an FM-compatible ``config.xml`` from PNGs in *output_folder*.

    If processed_names is None, scans the folder for all PNG files and maps them.
    """
    output_dir = Path(output_folder)
    t = TRANSLATIONS[lang]
    if processed_names is None:
        png_files = sorted(output_dir.glob("*.png"))
        processed_names = [f.stem for f in png_files]

    if not processed_names:
        logger(t["log_xml_no_png"])
        return False

    config_path = output_dir / "config.xml"
    existing_records = [] if overwrite else _parse_existing_records(config_path)
    
    existing_uids = {rec[0] for rec in existing_records}
    existing_mappings = {(rec[0], rec[1]) for rec in existing_records}

    all_record_lines: list[str] = []
    # Build list of existing records to preserve them
    for uid, target in existing_records:
        all_record_lines.append(
            f'\t\t<record from="{uid}" to="{target}"/>'
        )

    new_count = 0
    # Add new records for the specified PNGs
    for stem in processed_names:
        uid = Path(stem).stem
        expected_target = f"graphics/pictures/person/{uid}/portrait"
        
        # If this mapping is already present, skip adding a duplicate line
        if (uid, expected_target) in existing_mappings:
            continue
            
        line = f'\t\t<record from="{uid}" to="{expected_target}"/>'
        all_record_lines.append(line)
        new_count += 1

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
    lines.extend(all_record_lines)
    lines.append("\t</list>")
    lines.append("</record>")

    config_path.write_text("\n".join(lines), encoding="utf-8")
    if existing_records:
        logger(
            t["log_xml_merged"].format(new_count, len(existing_records))
        )
    else:
        logger(t["log_xml_written"].format(len(all_record_lines)))
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
            overwrite_config: bool = False,
            overwrite_dupes: bool = False,
            map_all_png: bool = False,
            lang: str = "en",
        ):
            super().__init__()
            self.input_paths = input_paths
            self.target_dimensions = target_dimensions
            self.output_folder = output_folder
            self.output_filenames = output_filenames
            self.enhance_sharp = enhance_sharp
            self.gen_config = gen_config
            self.overwrite_config = overwrite_config
            self.overwrite_dupes = overwrite_dupes
            self.map_all_png = map_all_png
            self.lang = lang

        def run(self):
            total = len(self.input_paths)
            all_ok = True
            t = TRANSLATIONS[self.lang]
            processed_names = []

            for i, (path, name) in enumerate(
                zip(self.input_paths, self.output_filenames)
            ):
                self.progress_signal.emit(i, total)
                self.status_signal.emit(t["processing_header"].format(i + 1, total))
                result = process_fm_face(
                    path,
                    self.target_dimensions,
                    self.output_folder,
                    name,
                    enhance_sharp=self.enhance_sharp,
                    logger=self._log,
                    lang=self.lang,
                )
                if result is None:
                    all_ok = False
                else:
                    self.preview_signal.emit(result)
                    processed_names.append(name)

            self.progress_signal.emit(total, total)
            if self.gen_config:
                names_to_map = None if self.map_all_png else processed_names
                generate_config_xml(
                    self.output_folder,
                    processed_names=names_to_map,
                    overwrite=self.overwrite_config,
                    logger=self._log,
                    lang=self.lang,
                )
            self.finished_signal.emit(all_ok)

        def _log(self, text: str):
            self.status_signal.emit(text)

    class DropListWidget(QListWidget):
        """QListWidget subclass that accepts dropped image files/folders."""

        files_dropped = pyqtSignal(list)
        delete_requested = pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAcceptDrops(True)
            self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
            self.setSelectionMode(
                QAbstractItemView.SelectionMode.ExtendedSelection
            )
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)

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

        def keyPressEvent(self, event):
            if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self.delete_requested.emit()
            else:
                super().keyPressEvent(event)

        def _show_context_menu(self, pos):
            if not self.selectedItems():
                return
            menu = QMenu(self)
            parent_window = self.window()
            lang = "en"
            if hasattr(parent_window, "current_lang"):
                lang = parent_window.current_lang
            
            remove_action = QAction(TRANSLATIONS[lang]["context_remove"], self)
            remove_action.triggered.connect(self.delete_requested.emit)
            menu.addAction(remove_action)
            menu.exec(self.mapToGlobal(pos))

    class FMGraphicsApp(QWidget):
        """Main application window."""

        def __init__(self):
            super().__init__()
            self.file_list: list[str] = []
            self.selected_output_dir = str(Path("fm_outputs").resolve())
            
            # Load language preference from QSettings
            from PyQt6.QtCore import QSettings
            self.settings = QSettings("FMPortraitTool", "FMFacepackToolPro")
            self.current_lang = self.settings.value("language", "en")
            if self.current_lang not in TRANSLATIONS:
                self.current_lang = "en"

            self._init_ui()
            self.file_list_widget.delete_requested.connect(self._remove_selected_files)
            self._apply_language()
            self._toggle_config_options()

        # ---- UI construction -------------------------------------------------

        def _init_ui(self):
            self.setWindowTitle("FM Player Face Tool Pro")
            self.resize(720, 710)
            self.setStyleSheet(STYLESHEET)
            icon_path = Path(__file__).resolve().parent / "assets" / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))

            root = QVBoxLayout()
            root.setSpacing(12)
            root.setContentsMargins(24, 24, 24, 24)

            root.addLayout(self._build_title_bar())
            root.addLayout(self._build_file_header())
            root.addWidget(self._build_file_list())
            root.addLayout(self._build_output_row())
            root.addLayout(self._build_size_row())
            root.addLayout(self._build_filename_row())
            root.addLayout(self._build_options_row())
            root.addWidget(self._build_run_button())
            root.addWidget(self._build_progress_bar())
            root.addLayout(self._build_bottom_panel(), stretch=1)

            self.setLayout(root)

        def _build_title_bar(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.lbl_title = QLabel()
            self.lbl_title.setStyleSheet(
                "font-weight: 700; color: #4f46e5; font-size: 16px;"
            )
            
            self.lbl_lang = QLabel()
            self.lbl_lang.setStyleSheet("color: #64748b; font-weight: 500;")
            self.cmb_lang = QComboBox()
            self.cmb_lang.addItem("English", "en")
            self.cmb_lang.addItem("ไทย", "th")
            self.cmb_lang.setFixedWidth(100)
            
            idx = self.cmb_lang.findData(self.current_lang)
            if idx >= 0:
                self.cmb_lang.setCurrentIndex(idx)
            self.cmb_lang.currentIndexChanged.connect(self._change_language)
            
            row.addWidget(self.lbl_title)
            row.addStretch()
            row.addWidget(self.lbl_lang)
            row.addWidget(self.cmb_lang)
            return row

        def _build_file_header(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.lbl_file_header = QLabel()
            self.lbl_file_header.setStyleSheet(
                "font-weight: 600; color: #1e293b; font-size: 13px;"
            )
            self.btn_files = QPushButton()
            self.btn_folder = QPushButton()
            self.btn_clear = QPushButton()
            self.btn_clear.setObjectName("btn_clear")

            self.btn_files.clicked.connect(self._browse_files)
            self.btn_folder.clicked.connect(self._browse_folder)
            self.btn_clear.clicked.connect(self._clear_files)

            row.addWidget(self.lbl_file_header)
            row.addStretch()
            row.addWidget(self.btn_files)
            row.addWidget(self.btn_folder)
            row.addWidget(self.btn_clear)
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
            self.btn_change_output = QPushButton()
            self.btn_change_output.clicked.connect(self._browse_output_folder)
            row.addWidget(self.lbl_output_path, stretch=4)
            row.addWidget(self.btn_change_output, stretch=0)
            return row

        def _build_size_row(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.lbl_size_title = QLabel()
            self.lbl_size_title.setStyleSheet("font-weight: 600; color: #1e293b;")
            row.addWidget(self.lbl_size_title)

            self.btn_group = QButtonGroup(self)
            self.rad_220 = QRadioButton("220 x 276")
            self.rad_220.setChecked(True)
            self.rad_192 = QRadioButton("192 x 192")
            self.rad_custom = QRadioButton()
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

        def _build_filename_row(self) -> QHBoxLayout:
            row = QHBoxLayout()
            self.lbl_filename_title = QLabel()
            self.lbl_filename_title.setStyleSheet("font-weight: 600; color: #1e293b;")
            row.addWidget(self.lbl_filename_title)

            self.filename_group = QButtonGroup(self)
            self.rad_orig_name = QRadioButton()
            self.rad_orig_name.setChecked(True)
            self.rad_custom_name = QRadioButton()
            
            self.filename_group.addButton(self.rad_orig_name)
            self.filename_group.addButton(self.rad_custom_name)

            row.addWidget(self.rad_orig_name)
            row.addWidget(self.rad_custom_name)

            self.txt_custom_name = QLineEdit()
            self.txt_custom_name.setFixedWidth(120)
            self.txt_custom_name.setEnabled(False)
            row.addWidget(self.txt_custom_name)
            row.addStretch()

            self.filename_group.buttonToggled.connect(self._toggle_filename_inputs)
            return row

        def _build_options_row(self) -> QVBoxLayout:
            layout = QVBoxLayout()
            layout.setSpacing(8)
            
            row1 = QHBoxLayout()
            self.chk_sharp = QCheckBox()
            self.chk_sharp.setStyleSheet("color: #f59e0b; font-weight: 500;")
            
            self.chk_config = QCheckBox()
            self.chk_config.setChecked(True)
            self.chk_config.setStyleSheet("color: #6366f1; font-weight: 500;")
            self.chk_config.toggled.connect(self._toggle_config_options)
            
            row1.addWidget(self.chk_sharp)
            row1.addWidget(self.chk_config)
            row1.addStretch()
            
            row2 = QHBoxLayout()
            row2.setContentsMargins(20, 0, 0, 0)
            row2.setSpacing(16)
            
            self.chk_overwrite = QCheckBox()
            self.chk_overwrite.setChecked(False)
            self.chk_overwrite.setStyleSheet("color: #475569;")
            
            self.chk_overwrite_dupes = QCheckBox()
            self.chk_overwrite_dupes.setChecked(False)
            self.chk_overwrite_dupes.setStyleSheet("color: #475569;")
            
            self.chk_map_all = QCheckBox()
            self.chk_map_all.setChecked(False)
            self.chk_map_all.setStyleSheet("color: #475569;")
            
            row2.addWidget(self.chk_overwrite)
            row2.addWidget(self.chk_overwrite_dupes)
            row2.addWidget(self.chk_map_all)
            row2.addStretch()
            
            layout.addLayout(row1)
            layout.addLayout(row2)
            return layout

        def _build_run_button(self) -> QPushButton:
            self.btn_run = QPushButton()
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
            self.lbl_preview_title = QLabel()
            self.lbl_preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_preview_title.setStyleSheet(
                "font-weight: 600; color: #64748b; font-size: 11px;"
            )
            self.lbl_preview = QLabel()
            self.lbl_preview.setFixedSize(180, 220)
            self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_preview.setStyleSheet(
                "background-color: #f8fafc; border: 1px solid #e2e8f0;"
                "border-radius: 10px; color: #cbd5e1; font-size: 12px;"
            )
            preview_col.addWidget(self.lbl_preview_title)
            preview_col.addWidget(self.lbl_preview)
            preview_col.addStretch()
            panel.addLayout(preview_col)

            # Log
            self.log_output = QTextEdit()
            self.log_output.setReadOnly(True)
            panel.addWidget(self.log_output, stretch=1)
            return panel

        # ---- Slots -----------------------------------------------------------

        def _change_language(self):
            lang = self.cmb_lang.currentData()
            if lang and lang != self.current_lang:
                self.current_lang = lang
                self.settings.setValue("language", lang)
                self._apply_language()

        def _apply_language(self):
            t = TRANSLATIONS[self.current_lang]
            self.setWindowTitle(t["title"])
            self.lbl_title.setText(t["title"])
            self.lbl_lang.setText(t["language"])
            
            # File header
            self.lbl_file_header.setText(t["input_images"])
            self.btn_files.setText(t["add_files"])
            self.btn_folder.setText(t["add_folder"])
            self.btn_clear.setText(t["clear"])
            
            # Output row
            self.btn_change_output.setText(t["change"])
            
            # Size row
            self.lbl_size_title.setText(t["size"])
            self.rad_custom.setText(t["custom"])
            
            # Filename row
            self.lbl_filename_title.setText(t["filename"])
            self.rad_orig_name.setText(t["use_original"])
            self.rad_custom_name.setText(t["custom_name"])
            self.txt_custom_name.setPlaceholderText(t["filename_hint"])
            
            # Options row
            self.chk_sharp.setText(t["enhance_sharpness"])
            self.chk_config.setText(t["generate_config"])
            self.chk_overwrite.setText(t["overwrite_config"])
            self.chk_overwrite_dupes.setText(t["overwrite_dupes"])
            self.chk_map_all.setText(t["map_all_png"])
            
            # Process button
            self.btn_run.setText(t["process_images"])
            
            # Preview and Log
            self.lbl_preview_title.setText(t["preview"])
            if not self.file_list:
                self.lbl_preview.setText(t["no_preview"])
            self.log_output.setPlaceholderText(t["status_log_placeholder"])

        def _toggle_custom_inputs(self):
            is_custom = self.rad_custom.isChecked()
            self.txt_width.setEnabled(is_custom)
            self.txt_height.setEnabled(is_custom)
            if not is_custom:
                self.txt_width.clear()
                self.txt_height.clear()

        def _toggle_filename_inputs(self):
            is_custom = self.rad_custom_name.isChecked()
            self.txt_custom_name.setEnabled(is_custom)
            if not is_custom:
                self.txt_custom_name.clear()

        def _toggle_config_options(self):
            enabled = self.chk_config.isChecked()
            self.chk_overwrite.setEnabled(enabled)
            self.chk_overwrite_dupes.setEnabled(enabled)
            self.chk_map_all.setEnabled(enabled)

        def _remove_selected_files(self):
            selected_rows = [self.file_list_widget.row(item) for item in self.file_list_widget.selectedItems()]
            if not selected_rows:
                return
            
            # Sort in descending order to avoid index shifts when deleting
            for row in sorted(selected_rows, reverse=True):
                if 0 <= row < len(self.file_list):
                    self.file_list.pop(row)
                    self.file_list_widget.takeItem(row)
            
            self.btn_run.setEnabled(bool(self.file_list))
            if not self.file_list:
                self.lbl_preview.setPixmap(QPixmap())
                self.lbl_preview.setText(TRANSLATIONS[self.current_lang]["no_preview"])

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
            self.lbl_preview.setText(TRANSLATIONS[self.current_lang]["no_preview"])

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

            use_custom_name = self.rad_custom_name.isChecked()
            custom_name = ""
            if use_custom_name:
                custom_name = self.txt_custom_name.text().strip()
                if not custom_name:
                    t = TRANSLATIONS[self.current_lang]
                    self.log_output.setText(t["error_custom_name"])
                    return

            overwrite_config = self.chk_overwrite.isChecked()
            overwrite_dupes = self.chk_overwrite_dupes.isChecked()

            output_names = []
            used_in_batch = set()

            # Get existing UIDs from config if we are NOT overwriting config, and we are NOT overwriting dupes
            existing_uids = set()
            if self.chk_config.isChecked() and not overwrite_config and not overwrite_dupes:
                config_path = Path(self.selected_output_dir) / "config.xml"
                existing_records = _parse_existing_records(config_path)
                existing_uids = {rec[0] for rec in existing_records}

            for i, img_path in enumerate(self.file_list):
                if use_custom_name:
                    base_name = custom_name
                else:
                    base_name = Path(img_path).stem

                final_name = base_name
                
                # Resolve naming collisions:
                # 1. Already used in this batch
                # 2. OR (overwrite_dupes is False and (exists in config or on disk))
                counter = 1
                while (
                    final_name in used_in_batch
                    or (
                        not overwrite_dupes
                        and (
                            final_name in existing_uids
                            or (Path(self.selected_output_dir) / f"{final_name}.png").exists()
                        )
                    )
                ):
                    final_name = f"{base_name}_{counter}"
                    counter += 1
                
                used_in_batch.add(final_name)
                output_names.append(final_name)

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
                overwrite_config=overwrite_config,
                overwrite_dupes=overwrite_dupes,
                map_all_png=self.chk_map_all.isChecked(),
                lang=self.current_lang,
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
                    TRANSLATIONS[self.current_lang]["error_size"]
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
            t = TRANSLATIONS[self.current_lang]
            if success:
                self.log_output.append(t["all_processed_success"].format(n))
            else:
                self.log_output.append(t["finished_errors"])


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

    # Resolve output names
    output_names = []
    used_in_batch = set()
    
    existing_uids = set()
    if args.config and not args.overwrite_config and not args.overwrite_dupes:
        config_path = Path(args.output) / "config.xml"
        existing_records = _parse_existing_records(config_path)
        existing_uids = {rec[0] for rec in existing_records}

    for i, img_path in enumerate(image_paths):
        if not is_batch and args.name:
            base_name = args.name
        else:
            base_name = Path(img_path).stem

        final_name = base_name
        counter = 1
        while (
            final_name in used_in_batch
            or (
                not args.overwrite_dupes
                and (
                    final_name in existing_uids
                    or (Path(args.output) / f"{final_name}.png").exists()
                )
            )
        ):
            final_name = f"{base_name}_{counter}"
            counter += 1
            
        used_in_batch.add(final_name)
        output_names.append(final_name)

    all_ok = True
    processed_names = []
    for i, (img_path, name) in enumerate(zip(image_paths, output_names)):
        if is_batch:
            print(f"--- [{i + 1}/{len(image_paths)}] ---")
        result = process_fm_face(
            img_path, target_dims, args.output, name, enhance_sharp=args.sharp
        )
        if result is None:
            all_ok = False
        else:
            processed_names.append(name)

    if args.config:
        names_to_map = None if args.map_all_png else processed_names
        generate_config_xml(
            args.output,
            processed_names=names_to_map,
            overwrite=args.overwrite_config,
        )

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
    parser.add_argument(
        "--overwrite-config", action="store_true",
        help="Overwrite existing config.xml completely instead of merging"
    )
    parser.add_argument(
        "--overwrite-dupes", action="store_true",
        help="Overwrite duplicate IDs/files instead of appending suffixes"
    )
    parser.add_argument(
        "--map-all-png", action="store_true",
        help="Scan and map all PNGs in the output folder"
    )
    args = parser.parse_args()

    if args.input is not None:
        _run_cli(args)
    else:
        _run_gui()


if __name__ == "__main__":
    main()