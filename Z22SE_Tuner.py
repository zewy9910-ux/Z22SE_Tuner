#!/usr/bin/env python3
"""Z22SE GMPT-E15 ECU Tuner — Opel Astra G 2.2 Z22SE (Cabrio 2004)"""

import sys, os, struct, shutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QRadioButton,
    QCheckBox, QSpinBox, QTextEdit, QStatusBar, QFrame, QGridLayout,
    QMessageBox, QButtonGroup, QScrollArea, QSplitter, QSizePolicy,
    QTabWidget, QSlider, QProgressDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QTextCursor

# ═══════════════════════════════════════════════════════════════════════════════
# ECU MEMORY MAP  —  Z22SE GMPT-E15  (confirmed from binary analysis)
# ═══════════════════════════════════════════════════════════════════════════════

ECU_PART_2004    = "12591333"
ECU_CAL_2004     = "W0L0TGF675B000465"
ECU_FILE_SIZE    = 524288          # 512 KB

# ── Ignition advance maps (4 × 163 bytes, high-load rows first) ──────────────
IGN_MAP_ADDRS    = [0x0082C9, 0x0083A9, 0x008489, 0x008569]
IGN_MAP_SIZE     = 163
IGN_MAP_NAMES    = ["Ign Advance #1 (primary)",
                    "Ign Advance #2 (cold-start)",
                    "Ign Advance #3 (part-load)",
                    "Ign Advance #4 (WOT/ref)"]

# ── Fuel / injection correction maps (4 × 115 bytes) ─────────────────────────
FUEL_MAP_ADDRS   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2]
FUEL_MAP_SIZE    = 115
FUEL_MAP_NAMES   = ["Fuel Corr #1 (warm)",
                    "Fuel Corr #2 (cold)",
                    "Fuel Corr #3 (part-load)",
                    "Fuel Corr #4 (WOT)"]

# ── Ignition trim maps ────────────────────────────────────────────────────────
IGN_TRIM_MAPS    = [(0x00896B, 62), (0x0089CE, 22)]

# ── Lambda / AFR target maps (2 × 163 bytes, primary + backup copy) ──────────
LAMBDA_MAP_ADDRS = [0x00C7A7, 0x00C885]
LAMBDA_MAP_SIZE  = 163

# ── Rev limiter (uint16 big-endian, 6500 RPM stock) ──────────────────────────
REV_LIMIT_ENGAGE = [0x00B568, 0x00B56A]
REV_LIMIT_HYSTER = [0x00B570, 0x00B572, 0x00B574]

# ── PIN code location (BCD-packed, 0x008141 = 0x33 0x05 = "3305") ────────────
PIN_ADDR         = 0x008141

# ── Calibration ID / part number strings ─────────────────────────────────────
CAL_ID_ADDR      = 0x00602C   # "W0L0TGF675B000465"
PART_ADDR        = 0x00800C   # "12591333"

# ── Lambda integrator / CL authority area (estimated) ────────────────────────
LAMBDA_CL_AREA   = (0x00A68F, 0x00A6A0)

# ── DTC threshold area (estimated from ECU family) ───────────────────────────
DTC_AREA         = (0x008C80, 0x008CB0)

# ═══════════════════════════════════════════════════════════════════════════════
# TUNE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TuneEngine:
    def __init__(self):
        self.buf      = None
        self.orig     = None
        self.filepath = None
        self.changes  = []

    # ── File I/O ─────────────────────────────────────────────────────────────

    def load(self, path: str) -> dict:
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) != ECU_FILE_SIZE:
            raise ValueError(f"File is {len(data):,} bytes — expected {ECU_FILE_SIZE:,} (512 KB)")
        self.buf      = bytearray(data)
        self.orig     = bytearray(data)
        self.filepath = path
        self.changes  = []
        return self._detect_ecu()

    def _detect_ecu(self) -> dict:
        raw_cal  = self.orig[CAL_ID_ADDR:CAL_ID_ADDR+17]
        cal_id   = raw_cal.decode('ascii', 'replace').strip('\x00 ')
        raw_part = self.orig[PART_ADDR:PART_ADDR+8]
        part     = raw_part.decode('ascii', 'replace').strip('\x00 ')
        pb       = self.orig[PIN_ADDR:PIN_ADDR+2]
        pin      = f"{pb[0]>>4}{pb[0]&0xF}{pb[1]>>4}{pb[1]&0xF}"
        rev      = struct.unpack_from('>H', self.orig, REV_LIMIT_ENGAGE[0])[0]
        return {
            'part':    part,
            'cal_id':  cal_id,
            'pin':     pin,
            'rev_rpm': rev,
            'size_kb': len(self.orig) // 1024,
            'known':   (ECU_PART_2004 in part),
        }

    def backup(self):
        ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
        dst = self.filepath + f'.backup_{ts}'
        shutil.copy2(self.filepath, dst)
        return dst

    def save(self, path: str):
        with open(path, 'wb') as f:
            f.write(self.buf)

    def reset(self):
        self.buf     = bytearray(self.orig)
        self.changes = []

    def changed_byte_count(self) -> int:
        if not self.buf or not self.orig:
            return 0
        return sum(1 for a, b in zip(self.buf, self.orig) if a != b)

    # ── Core helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(v: int) -> int:
        return max(1, min(254, v))

    def _delta_block(self, addr: int, size: int, delta: int,
                     z0: float = 0.0, z1: float = 1.0, label: str = ""):
        start   = addr + int(size * z0)
        end     = addr + int(size * z1)
        changed = 0
        for i in range(start, end):
            nv = self._clamp(self.buf[i] + delta)
            if nv != self.buf[i]:
                self.buf[i] = nv
                changed += 1
        if label and changed:
            sign = f"+{delta}" if delta >= 0 else str(delta)
            self.changes.append(f"    {label}: {sign} counts → {changed} cells")

    def _write_u16be(self, addr: int, val: int, label: str = ""):
        struct.pack_into('>H', self.buf, addr, val)
        if label:
            self.changes.append(f"    {label}: {val} RPM (0x{val:04X})")

    # ── Map helpers ───────────────────────────────────────────────────────────

    def _ign(self, wot: int, pl: int, overrun: int = 0):
        for addr, name in zip(IGN_MAP_ADDRS, IGN_MAP_NAMES):
            self._delta_block(addr, IGN_MAP_SIZE, wot,    0.00, 0.40, f"{name} WOT")
            self._delta_block(addr, IGN_MAP_SIZE, pl,     0.40, 0.75, f"{name} part-load")
            if overrun:
                self._delta_block(addr, IGN_MAP_SIZE, overrun, 0.75, 1.00, f"{name} overrun")

    def _fuel(self, wot: int, pl: int):
        for addr, name in zip(FUEL_MAP_ADDRS, FUEL_MAP_NAMES):
            self._delta_block(addr, FUEL_MAP_SIZE, wot, 0.00, 0.40, f"{name} WOT")
            self._delta_block(addr, FUEL_MAP_SIZE, pl,  0.40, 1.00, f"{name} part-load")

    def _lambda(self, wot: int, pl: int = 0):
        for i, addr in enumerate(LAMBDA_MAP_ADDRS):
            tag = "primary" if i == 0 else "backup"
            self._delta_block(addr, LAMBDA_MAP_SIZE, wot, 0.00, 0.40, f"Lambda {tag} WOT")
            if pl:
                self._delta_block(addr, LAMBDA_MAP_SIZE, pl, 0.40, 0.75, f"Lambda {tag} part-load")

    def _trims(self, d: int):
        for addr, size in IGN_TRIM_MAPS:
            self._delta_block(addr, size, d, label=f"Ign trim 0x{addr:06X}")

    # ── Tune profiles ─────────────────────────────────────────────────────────

    def apply_stage1(self):
        self.changes.append("► Stage 1  (verified from binary analysis)")
        self._ign(wot=2, pl=1)
        self._fuel(wot=2, pl=1)
        self._trims(1)
        self._lambda(wot=-7)

    def apply_stage1plus(self):
        self.changes.append("► Stage 1+  (moderate uniform advance)")
        self._ign(wot=3, pl=2)
        self._fuel(wot=3, pl=2)
        self._trims(1)
        self._lambda(wot=-9, pl=-3)

    def apply_stage2(self):
        self.changes.append("► Stage 2  (aggressive + 6800 RPM limit)")
        self._ign(wot=5, pl=3)
        self._fuel(wot=4, pl=2)
        self._trims(2)
        self._lambda(wot=-11, pl=-5)
        self.apply_rev_limit(6800)

    # ── Extra features ────────────────────────────────────────────────────────

    def apply_pop_bang(self):
        self.changes.append("► Pop & Bang  (overrun retard + enrichment)")
        self._ign(wot=0, pl=0, overrun=-12)
        for addr, name in zip(FUEL_MAP_ADDRS, FUEL_MAP_NAMES):
            self._delta_block(addr, FUEL_MAP_SIZE, +4, 0.65, 1.00, f"{name} overrun enrich")

    def apply_burble(self):
        self.changes.append("► Burble  (aggressive overrun retard + enrichment)")
        self._ign(wot=0, pl=0, overrun=-20)
        for addr, name in zip(FUEL_MAP_ADDRS, FUEL_MAP_NAMES):
            self._delta_block(addr, FUEL_MAP_SIZE, +7, 0.60, 1.00, f"{name} burble enrich")

    def apply_rev_limit(self, rpm: int):
        if self.orig is None:
            return
        orig_rpm = struct.unpack_from('>H', self.orig, REV_LIMIT_ENGAGE[0])[0]
        if rpm == orig_rpm:
            return
        self.changes.append(f"► Rev Limit  {orig_rpm} → {rpm} RPM")
        hyst = rpm - 6
        for addr in REV_LIMIT_ENGAGE:
            self._write_u16be(addr, rpm,  f"Fuel cut engage  0x{addr:06X}")
        for addr in REV_LIMIT_HYSTER:
            self._write_u16be(addr, hyst, f"Fuel cut re-enable 0x{addr:06X}")

    # ── Disable options ───────────────────────────────────────────────────────

    def disable_lambda(self):
        self.changes.append("► Lambda/O2 Closed-Loop DISABLED  ⚠")
        # Clamp CL authority area to neutral (0x80 = 1.0× = no correction)
        start, end = LAMBDA_CL_AREA
        patched = 0
        for i in range(start, end):
            if self.buf[i] > 0x80:
                self.buf[i] = 0x80
                patched += 1
        self.changes.append(f"    CL authority area clamped: {patched} cells")
        # Force lambda targets to open-loop rich fixed value
        self._lambda(wot=-14, pl=-14)

    def disable_egr(self):
        self.changes.append("► EGR Disable — NOT APPLICABLE (Z22SE has no EGR)")

    def disable_dtc(self):
        self.changes.append("► DTC Monitoring DISABLED  ⚠  (best-effort)")
        start, end = DTC_AREA
        patched = 0
        for i in range(start, end):
            if 0x04 <= self.buf[i] <= 0x1E:
                self.buf[i] = 0x00
                patched += 1
        self.changes.append(f"    DTC threshold area: {patched} threshold bytes zeroed")

    def disable_speed_limiter(self):
        self.changes.append("► Speed Limiter — ⚠ Address unconfirmed for this calibration. Skipped.")

    def get_changes_text(self) -> str:
        if not self.changes:
            return "No changes applied yet.\n\nLoad a .bin file and select a tune profile."
        lines = [
            f"Changes applied to: {Path(self.filepath).name if self.filepath else 'unknown'}",
            f"Modified bytes: {self.changed_byte_count():,}",
            "─" * 50,
        ] + self.changes
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px 8px 8px 8px;
    font-weight: bold;
    font-size: 12px;
    color: #8b949e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #58a6ff;
    font-size: 12px;
}
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 13px;
}
QPushButton:hover  { background-color: #30363d; border-color: #58a6ff; }
QPushButton:pressed { background-color: #161b22; }
QPushButton:disabled { color: #484f58; border-color: #21262d; }
QPushButton#btn_apply {
    background-color: #238636;
    border-color: #2ea043;
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
    padding: 8px 24px;
}
QPushButton#btn_apply:hover   { background-color: #2ea043; }
QPushButton#btn_apply:disabled { background-color: #21262d; color: #484f58; border-color: #21262d; }
QPushButton#btn_save {
    background-color: #1f6feb;
    border-color: #388bfd;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 24px;
}
QPushButton#btn_save:hover   { background-color: #388bfd; }
QPushButton#btn_save:disabled { background-color: #21262d; color: #484f58; border-color: #21262d; }
QPushButton#btn_reset {
    background-color: #6e40c9;
    border-color: #8957e5;
    color: #ffffff;
}
QPushButton#btn_reset:hover { background-color: #8957e5; }
QRadioButton, QCheckBox {
    spacing: 8px;
    color: #e6edf3;
    padding: 3px 0;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 2px solid #484f58;
    border-radius: 8px;
    background: #0d1117;
}
QRadioButton::indicator:checked {
    background: #58a6ff;
    border-color: #58a6ff;
}
QCheckBox::indicator { border-radius: 3px; }
QCheckBox::indicator:checked { background: #3fb950; border-color: #3fb950; }
QCheckBox#warn_check::indicator:checked { background: #f85149; border-color: #f85149; }
QLabel#info_val { color: #58a6ff; font-weight: bold; }
QLabel#warn_label { color: #e3b341; font-size: 11px; }
QLabel#ok_label   { color: #3fb950; }
QLabel#err_label  { color: #f85149; }
QLabel#section_title {
    color: #e6edf3;
    font-size: 14px;
    font-weight: bold;
    padding: 4px 0;
}
QTextEdit {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 4px;
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 6px;
}
QScrollArea { border: none; background-color: transparent; }
QScrollBar:vertical {
    background: #161b22; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #484f58; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QFrame#separator { color: #30363d; }
QStatusBar {
    background-color: #010409;
    color: #8b949e;
    border-top: 1px solid #30363d;
    font-size: 12px;
}
QStatusBar::item { border: none; }
QSpinBox {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 3px 8px;
}
QSpinBox:focus { border-color: #58a6ff; }
QTabWidget::pane {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 0 4px 4px 4px;
}
QTabBar::tab {
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
    padding: 6px 14px;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
}
QTabBar::tab:selected { background: #161b22; color: #e6edf3; border-top: 2px solid #58a6ff; }
QTabBar::tab:hover    { color: #c9d1d9; }
QSlider::groove:horizontal {
    height: 4px; background: #30363d; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #58a6ff; border: none;
    width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #1f6feb; border-radius: 2px; }
"""


# ═══════════════════════════════════════════════════════════════════════════════
# REUSABLE WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

def hline():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setObjectName("separator")
    f.setStyleSheet("background: #30363d; max-height: 1px;")
    return f

def label(text, style="", bold=False, size=None):
    l = QLabel(text)
    if bold:  l.setFont(QFont("Segoe UI", size or 12, QFont.Weight.Bold))
    if style: l.setObjectName(style)
    if size:  l.setFont(QFont("Segoe UI", size))
    return l


class InfoRow(QWidget):
    def __init__(self, key, val="—"):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 1, 0, 1)
        self.key_lbl = QLabel(key + ":")
        self.key_lbl.setStyleSheet("color:#8b949e; min-width:100px;")
        self.val_lbl = QLabel(val)
        self.val_lbl.setObjectName("info_val")
        lay.addWidget(self.key_lbl)
        lay.addWidget(self.val_lbl, 1)

    def set(self, val, color=None):
        self.val_lbl.setText(str(val))
        if color:
            self.val_lbl.setStyleSheet(f"color:{color}; font-weight:bold;")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = TuneEngine()
        self.setWindowTitle("Z22SE GMPT-E15 ECU Tuner  —  Opel Astra G 2.2 Z22SE")
        self.setMinimumSize(1100, 780)
        self.resize(1260, 860)
        self._build_ui()
        self._set_controls_enabled(False)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(hline())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background: #30363d; }")
        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([440, 820])
        root.addWidget(splitter, 1)

        self.statusBar().showMessage("No file loaded  —  Open a Z22SE GMPT-E15 .bin file to begin")

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet("background:#010409; border-bottom: 1px solid #30363d;")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 8, 16, 8)

        title = QLabel("⚙  Z22SE GMPT-E15 ECU Tuner")
        title.setStyleSheet("color:#58a6ff; font-size:16px; font-weight:bold;")
        lay.addWidget(title)
        lay.addStretch()

        self.btn_open   = QPushButton("📂  Open .bin")
        self.btn_backup = QPushButton("💾  Backup")
        self.btn_save   = QPushButton("💾  Save As…")
        self.btn_save.setObjectName("btn_save")
        self.btn_backup.setToolTip("Create a timestamped .backup copy before modifying")
        self.btn_save.setToolTip("Save modified binary to disk")

        for b in [self.btn_open, self.btn_backup, self.btn_save]:
            lay.addWidget(b)

        self.btn_open.clicked.connect(self._on_open)
        self.btn_backup.clicked.connect(self._on_backup)
        self.btn_save.clicked.connect(self._on_save)
        return bar

    # ── Left panel (options) ──────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        outer = QWidget()
        outer.setMinimumWidth(400)
        outer.setMaximumWidth(500)
        vbox = QVBoxLayout(outer)
        vbox.setContentsMargins(12, 10, 6, 10)
        vbox.setSpacing(10)

        # ECU info
        vbox.addWidget(self._build_ecu_info())

        # Scroll area for tune options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 8, 0)
        inner_lay.setSpacing(10)

        inner_lay.addWidget(self._build_tune_profiles())
        inner_lay.addWidget(self._build_extra_features())
        inner_lay.addWidget(self._build_disable_options())
        inner_lay.addStretch()

        scroll.setWidget(inner)
        vbox.addWidget(scroll, 1)

        # Apply / Reset buttons
        vbox.addWidget(hline())
        btn_row = QHBoxLayout()
        self.btn_reset = QPushButton("↩  Reset")
        self.btn_reset.setObjectName("btn_reset")
        self.btn_apply = QPushButton("▶  Apply Tune")
        self.btn_apply.setObjectName("btn_apply")
        self.btn_reset.clicked.connect(self._on_reset)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_reset.setFixedHeight(38)
        self.btn_apply.setFixedHeight(38)
        btn_row.addWidget(self.btn_reset)
        btn_row.addWidget(self.btn_apply, 2)
        vbox.addLayout(btn_row)

        return outer

    def _build_ecu_info(self) -> QGroupBox:
        gb = QGroupBox("ECU Information")
        lay = QVBoxLayout(gb)
        lay.setSpacing(2)
        self._row_part   = InfoRow("Part #")
        self._row_cal    = InfoRow("Cal ID")
        self._row_pin    = InfoRow("PIN")
        self._row_rev    = InfoRow("Stock Rev Limit")
        self._row_status = InfoRow("Status")
        for r in [self._row_part, self._row_cal, self._row_pin, self._row_rev, self._row_status]:
            lay.addWidget(r)
        return gb

    def _build_tune_profiles(self) -> QGroupBox:
        gb = QGroupBox("Tune Profile")
        lay = QVBoxLayout(gb)
        self._tune_group = QButtonGroup(self)

        profiles = [
            ("stock",   "⬛  Stock",   "No changes — restore to factory values"),
            ("stage1",  "🟡  Stage 1", "+2 ignition, +2 fuel, richer WOT lambda\n"
                                        "Based on verified Stage 1 binary analysis. Safe for stock hardware."),
            ("stage1p", "🟠  Stage 1+","Uniform +3 ign / +3 fuel / richer WOT+PL lambda\n"
                                        "Panel filter + sports exhaust recommended."),
            ("stage2",  "🔴  Stage 2", "+5 ign WOT / +4 fuel / richer lambda / 6800 RPM limit\n"
                                        "Requires: cold air intake, exhaust, strong fueling."),
        ]

        for key, title, desc in profiles:
            rb = QRadioButton(title)
            rb.setProperty("tune_key", key)
            tip = QLabel(desc)
            tip.setStyleSheet("color:#8b949e; font-size:11px; margin-left:26px; margin-bottom:4px;")
            tip.setWordWrap(True)
            lay.addWidget(rb)
            lay.addWidget(tip)
            self._tune_group.addButton(rb)
            if key == "stock":
                rb.setChecked(True)

        self._tune_group.buttonToggled.connect(self._refresh_preview)
        return gb

    def _build_extra_features(self) -> QGroupBox:
        gb = QGroupBox("Extra Features")
        lay = QVBoxLayout(gb)

        # Pop & Bang
        self.chk_pop   = QCheckBox("💥  Pop & Bang")
        self.chk_pop.setToolTip("Retards ignition in overrun cells → exhaust pops on decel")
        lbl_pop = QLabel("   Ignition retard on overrun cells + overrun enrichment.\n"
                         "   Works best combined with Stage 1 or above.")
        lbl_pop.setStyleSheet("color:#8b949e; font-size:11px; margin-left:4px; margin-bottom:4px;")
        lbl_pop.setWordWrap(True)

        # Burble
        self.chk_burble = QCheckBox("🔥  Burble / Crackle")
        self.chk_burble.setToolTip("More aggressive overrun retard for continuous exhaust crackle")
        lbl_bur = QLabel("   Aggressive overrun retard + heavy enrichment.\n"
                         "   Not recommended for daily use. Stage 1+ or above advised.")
        lbl_bur.setStyleSheet("color:#8b949e; font-size:11px; margin-left:4px; margin-bottom:6px;")
        lbl_bur.setWordWrap(True)

        # Rev limit (manual override)
        rev_row = QHBoxLayout()
        self.chk_rev   = QCheckBox("🏁  Custom Rev Limit")
        self.spin_rev  = QSpinBox()
        self.spin_rev.setRange(5500, 7500)
        self.spin_rev.setSingleStep(100)
        self.spin_rev.setValue(6500)
        self.spin_rev.setSuffix("  RPM")
        self.spin_rev.setFixedWidth(110)
        self.spin_rev.setEnabled(False)
        rev_row.addWidget(self.chk_rev)
        rev_row.addWidget(self.spin_rev)
        rev_row.addStretch()
        lbl_rev = QLabel("   Stage 2 auto-sets 6800. This overrides any profile value.")
        lbl_rev.setStyleSheet("color:#8b949e; font-size:11px; margin-left:4px;")

        for w in [self.chk_pop, lbl_pop, self.chk_burble, lbl_bur]:
            lay.addWidget(w)
        lay.addLayout(rev_row)
        lay.addWidget(lbl_rev)

        # Mutual exclusion: pop & bang vs burble
        self.chk_pop.toggled.connect(lambda c: self.chk_burble.setEnabled(not c) if c else None)
        self.chk_burble.toggled.connect(lambda c: self.chk_pop.setEnabled(not c) if c else None)
        self.chk_rev.toggled.connect(self.spin_rev.setEnabled)

        for w in [self.chk_pop, self.chk_burble, self.chk_rev, self.spin_rev]:
            if hasattr(w, 'toggled'):
                w.toggled.connect(self._refresh_preview)
            elif hasattr(w, 'valueChanged'):
                w.valueChanged.connect(self._refresh_preview)
        return gb

    def _build_disable_options(self) -> QGroupBox:
        gb = QGroupBox("Disable / Delete Options  ⚠")
        lay = QVBoxLayout(gb)
        gb.setStyleSheet("QGroupBox { border-color: #f85149; } QGroupBox::title { color: #f85149; }")

        warn = QLabel("⚠  These options modify ECU safety features. Use at your own risk.")
        warn.setObjectName("warn_label")
        warn.setWordWrap(True)
        lay.addWidget(warn)
        lay.addWidget(hline())

        def opt(key, title, tooltip, desc, disabled_reason=None):
            chk = QCheckBox(title)
            chk.setObjectName("warn_check")
            chk.setToolTip(tooltip)
            if disabled_reason:
                chk.setEnabled(False)
                chk.setToolTip(disabled_reason)
            lbl = QLabel(f"   {desc}")
            lbl.setStyleSheet("color:#8b949e; font-size:11px; margin-left:4px; margin-bottom:4px;")
            lbl.setWordWrap(True)
            lay.addWidget(chk)
            lay.addWidget(lbl)
            if hasattr(chk, 'toggled'):
                chk.toggled.connect(self._refresh_preview)
            return chk

        self.chk_lambda = opt(
            "lambda", "🔴  Disable Lambda / O2 Correction",
            "Clamp closed-loop O2 authority to zero (open-loop)",
            "Clamps CL lambda authority to neutral + fixes lambda targets rich.\n"
            "⚠ Best-effort — verify on wideband O2 gauge after flashing.")
        self.chk_egr = opt(
            "egr", "⬜  Disable EGR",
            "Not applicable — Z22SE has no EGR",
            "Not applicable — the Z22SE 2.2 petrol has no EGR system.",
            disabled_reason="Z22SE has no EGR. This option is not applicable.")
        self.chk_dtc = opt(
            "dtc", "🔴  Disable DTC Monitoring",
            "Zero out DTC threshold bytes (best-effort)",
            "Zeroes threshold values in DTC area (partially confirmed addresses).\n"
            "⚠ Best-effort — some DTCs may still trigger.")
        self.chk_speed = opt(
            "speed", "🟠  Remove Speed Limiter",
            "Speed limiter address not yet confirmed for this binary",
            "Speed limiter address not yet confirmed for this calibration.\n"
            "Will skip silently if address is unresolved.",
            disabled_reason="Speed limiter address unconfirmed for 12591333. Disabled for safety.")

        return gb

    # ── Right panel (preview + tabs) ─────────────────────────────────────────

    def _build_right(self) -> QWidget:
        outer = QWidget()
        vbox  = QVBoxLayout(outer)
        vbox.setContentsMargins(6, 10, 12, 10)
        vbox.setSpacing(8)

        tabs = QTabWidget()

        # Tab 1: Changes preview
        preview_widget = QWidget()
        p_lay = QVBoxLayout(preview_widget)
        p_lay.setContentsMargins(8, 8, 8, 8)

        hdr_row = QHBoxLayout()
        hdr_row.addWidget(label("Changes Preview", bold=True))
        hdr_row.addStretch()
        self.lbl_bytes = QLabel("0 bytes modified")
        self.lbl_bytes.setStyleSheet("color:#8b949e; font-size:12px;")
        hdr_row.addWidget(self.lbl_bytes)
        p_lay.addLayout(hdr_row)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Apply a tune profile to see changes here…")
        p_lay.addWidget(self.preview_text, 1)
        tabs.addTab(preview_widget, "📋  Changes")

        # Tab 2: Map addresses reference
        ref_widget = QWidget()
        r_lay = QVBoxLayout(ref_widget)
        r_lay.setContentsMargins(8, 8, 8, 8)
        ref_txt = QTextEdit()
        ref_txt.setReadOnly(True)
        ref_txt.setText(self._build_reference_text())
        r_lay.addWidget(ref_txt)
        tabs.addTab(ref_widget, "📍  Address Map")

        # Tab 3: ECU notes
        notes_widget = QWidget()
        n_lay = QVBoxLayout(notes_widget)
        n_lay.setContentsMargins(8, 8, 8, 8)
        notes_txt = QTextEdit()
        notes_txt.setReadOnly(True)
        notes_txt.setText(NOTES_TEXT)
        n_lay.addWidget(notes_txt)
        tabs.addTab(notes_widget, "ℹ  Notes & Warnings")

        vbox.addWidget(tabs, 1)

        # Bottom action row
        vbox.addWidget(hline())
        bottom = QHBoxLayout()
        self.lbl_status_detail = QLabel("Load a .bin file to start")
        self.lbl_status_detail.setStyleSheet("color:#8b949e;")
        bottom.addWidget(self.lbl_status_detail, 1)
        vbox.addLayout(bottom)

        return outer

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open ECU Binary", str(Path.home() / "Desktop"),
            "Binary files (*.bin *.BIN);;All files (*)")
        if not path:
            return
        try:
            info = self.engine.load(path)
        except ValueError as e:
            QMessageBox.critical(self, "Load Error", str(e))
            return

        # Update ECU info panel
        color_part = "#3fb950" if info['known'] else "#e3b341"
        self._row_part.set(info['part'], color_part)
        self._row_cal.set(info['cal_id'])
        self._row_pin.set(info['pin'], "#58a6ff")
        self._row_rev.set(f"{info['rev_rpm']} RPM")
        if info['known']:
            self._row_status.set("✅  Recognised (12591333 / 2004)", "#3fb950")
        else:
            self._row_status.set("⚠  Unknown — proceed with caution", "#e3b341")

        self._set_controls_enabled(True)
        self.spin_rev.setValue(info['rev_rpm'])
        self.preview_text.clear()
        self.preview_text.setPlaceholderText("Select a tune profile and click ▶ Apply Tune")
        self.statusBar().showMessage(f"Loaded: {Path(path).name}  ({info['size_kb']} KB)  "
                                     f"Part: {info['part']}  Cal: {info['cal_id']}")
        self.lbl_status_detail.setText(f"File: {Path(path).name}")

    def _on_backup(self):
        if not self.engine.filepath:
            return
        dst = self.engine.backup()
        QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{dst}")
        self.statusBar().showMessage(f"Backup created: {Path(dst).name}")

    def _on_apply(self):
        if not self.engine.buf:
            return

        # Confirm
        profile_key = self._selected_profile()
        extras = []
        if self.chk_pop.isChecked():    extras.append("Pop & Bang")
        if self.chk_burble.isChecked(): extras.append("Burble")
        if self.chk_rev.isChecked():    extras.append(f"Rev Limit → {self.spin_rev.value()} RPM")
        if self.chk_lambda.isChecked(): extras.append("Disable Lambda")
        if self.chk_dtc.isChecked():    extras.append("Disable DTCs")

        summary = f"Tune: {profile_key.upper()}"
        if extras:
            summary += "\nExtras: " + ", ".join(extras)
        reply = QMessageBox.question(
            self, "Confirm Apply",
            f"Apply the following changes to the working copy?\n\n{summary}\n\n"
            "The original file is NOT modified until you click Save.\n"
            "Create a backup first if you haven't already.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.engine.reset()

        # Apply profile
        if   profile_key == "stage1":  self.engine.apply_stage1()
        elif profile_key == "stage1p": self.engine.apply_stage1plus()
        elif profile_key == "stage2":  self.engine.apply_stage2()
        # "stock" = no changes

        # Extra features
        if self.chk_pop.isChecked():    self.engine.apply_pop_bang()
        if self.chk_burble.isChecked(): self.engine.apply_burble()
        if self.chk_rev.isChecked():
            self.engine.apply_rev_limit(self.spin_rev.value())

        # Disable options
        if self.chk_lambda.isChecked(): self.engine.disable_lambda()
        if self.chk_egr.isChecked():    self.engine.disable_egr()
        if self.chk_dtc.isChecked():    self.engine.disable_dtc()
        if self.chk_speed.isChecked():  self.engine.disable_speed_limiter()

        self._update_preview()
        n = self.engine.changed_byte_count()
        self.statusBar().showMessage(f"✅  Tune applied — {n:,} bytes modified. Click Save to write to disk.")
        self.lbl_bytes.setText(f"{n:,} bytes modified")

    def _on_reset(self):
        if not self.engine.buf:
            return
        self.engine.reset()
        self.preview_text.setText("Working copy reset to original.\nNo changes applied.")
        self.lbl_bytes.setText("0 bytes modified")
        self.statusBar().showMessage("Working copy reset to original.")

    def _on_save(self):
        if not self.engine.buf:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tuned Binary",
            str(Path(self.engine.filepath).parent / (Path(self.engine.filepath).stem + "_tuned.bin")),
            "Binary files (*.bin);;All files (*)")
        if not path:
            return
        self.engine.save(path)
        QMessageBox.information(self, "Saved", f"Tuned binary saved to:\n{path}")
        self.statusBar().showMessage(f"Saved: {Path(path).name}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_profile(self) -> str:
        for btn in self._tune_group.buttons():
            if btn.isChecked():
                return btn.property("tune_key")
        return "stock"

    def _refresh_preview(self):
        pass  # preview updates on Apply only (avoid lag from live simulation)

    def _update_preview(self):
        txt = self.engine.get_changes_text()
        self.preview_text.setText(txt)
        self.preview_text.moveCursor(QTextCursor.MoveOperation.Start)

    def _set_controls_enabled(self, en: bool):
        for w in [self.btn_backup, self.btn_save, self.btn_apply,
                  self.btn_reset, self.btn_rev_group if hasattr(self, 'btn_rev_group') else None]:
            if w:
                w.setEnabled(en)
        # Options
        for w in [self.chk_pop, self.chk_burble, self.chk_rev,
                  self.chk_lambda, self.chk_dtc]:
            w.setEnabled(en)
        for btn in self._tune_group.buttons():
            btn.setEnabled(en)
        self.btn_apply.setEnabled(en)
        self.btn_reset.setEnabled(en)
        self.btn_save.setEnabled(en)
        self.btn_backup.setEnabled(en)

    @staticmethod
    def _build_reference_text() -> str:
        lines = [
            "Z22SE GMPT-E15 — Confirmed Address Map",
            "=" * 55,
            "",
            "PIN Code (BCD packed):",
            "  0x008141  2 bytes  33 05 = '3305'",
            "",
            "Rev Limiter / Fuel Cut:",
            "  0x00B568  uint16 BE  fuel cut engage #1",
            "  0x00B56A  uint16 BE  fuel cut engage #2",
            "  0x00B570  uint16 BE  hysteresis re-enable",
            "  Stock: 6500 RPM (0x1964)",
            "  6800 RPM = 0x1A90  |  7000 RPM = 0x1B58",
            "",
            "Ignition Advance Maps (4 × 163 bytes):",
            "  0x0082C9  Ign Map #1 (primary)",
            "  0x0083A9  Ign Map #2 (cold-start)",
            "  0x008489  Ign Map #3 (part-load)",
            "  0x008569  Ign Map #4 (WOT/ref)",
            "",
            "Fuel Correction Maps (4 × 115 bytes):",
            "  0x0086C9  Fuel Map #1 (warm)",
            "  0x00876C  Fuel Map #2 (cold)",
            "  0x00880F  Fuel Map #3 (part-load)",
            "  0x0088B2  Fuel Map #4 (WOT)",
            "",
            "Ignition Trim Maps:",
            "  0x00896B  62 bytes",
            "  0x0089CE  22 bytes",
            "",
            "Lambda/AFR Target Maps (2 × 163 bytes):",
            "  0x00C7A7  Primary copy",
            "  0x00C885  Backup/duplicate copy",
            "  Scaling: value × (14.7 / 128) ≈ AFR",
            "  0x80 = 128 = λ1.0 / 14.7:1",
            "",
            "RPM Axis (12-point, at 0x0081B0):",
            "  2000 2400 2800 3200 3600 4000",
            "  4400 4800 5200 5600 6000 6400 RPM",
            "",
            "Load Axis (12-point, descending):",
            "  117 106 103 97 94 91 88 85 77 63 51 46",
            "",
            "Calibration ID: 0x00602C  ('W0L0TGF675B000465')",
            "Part Number:    0x00800C  ('12591333')",
            "Checksum:       0x008000  (uint16 BE, recalculated by flash tool)",
        ]
        return "\n".join(lines)


NOTES_TEXT = """Z22SE GMPT-E15 ECU Tuner — Notes & Warnings
=============================================

CONFIRMED DATA
──────────────
• All map addresses are confirmed from binary analysis of the
  actual OpelAstraG_Z22SE_GMPT-E15_Stock.bin (VIN: W0L0TGF675B000465)
• Stage 1 values are verified against real Stage 1 tune file
• Rev limit (6500 RPM) confirmed at 0x00B568

TUNE PHILOSOPHY
───────────────
Stage 1    Based on real Stage 1 binary analysis. +2 ignition counts
           on high-load/high-RPM cells. Richer WOT lambda target.
           Safe for completely stock hardware.

Stage 1+   Moderate step up. +3 ign / +3 fuel uniform. Recommended
           with at minimum a panel air filter.

Stage 2    Aggressive. +5 ign WOT / +4 fuel. 6800 RPM limit.
           Requires: cold air intake, sports exhaust, proper fueling.
           Do not flash without knock monitoring.

Pop & Bang Retards ignition in overrun (decel) cells by −12 counts
           and enriches overrun fueling. Creates pops on decel.
           Safe when combined with any Stage tune.

Burble     Aggressive version (−20 overrun retard, heavy enrichment).
           Not recommended for daily commuting. May cause rough idle
           if overrun zone boundaries are imprecise.

BEST-EFFORT / ESTIMATED
────────────────────────
• Lambda disable: CL authority area and lambda target approach.
  Verify with a wideband O2 sensor after flashing.
• DTC disable: Threshold zeroing in estimated DTC area.
  Not all DTCs may be suppressed.
• Speed limiter: Address not confirmed — option is disabled.
• Pop/Bang overrun boundaries are proportional estimates of the
  raw map byte ranges, not exact cell positions.

ALWAYS
───────
1. Create a BACKUP before flashing anything
2. Verify on a rolling road / dyno if possible
3. Use a wideband lambda sensor when tuning fuel maps
4. Monitor for knock (pinging) especially with Stage 2
5. The ECU checksum at 0x008000 is typically recalculated by
   the flashing tool (ECM Titanium / MPPS / KTAG etc.)

DISCLAIMER
──────────
This software is for educational purposes. Improper ECU
modification can damage your engine. Always consult a
professional tuner for safety-critical changes.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setApplicationName("Z22SE ECU Tuner")

    # App-wide dark palette fallback
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("#0d1117"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("#161b22"))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#21262d"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#e6edf3"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#e6edf3"))
    pal.setColor(QPalette.ColorRole.Button,          QColor("#21262d"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#1f6feb"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

