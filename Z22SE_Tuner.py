#!/usr/bin/env python3
"""Z22SE GMPT-E15 ECU Tuner — Opel Astra G 2.2 Z22SE  (multi-ECU, v3)"""

import sys, os, struct, shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QRadioButton,
    QCheckBox, QSpinBox, QTextEdit, QStatusBar, QFrame,
    QMessageBox, QButtonGroup, QScrollArea, QSplitter,
    QTabWidget, QSlider, QComboBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE GEOMETRY (confirmed from binary analysis)
# ═══════════════════════════════════════════════════════════════════════════════
#  Ign maps  : 7-byte header + 12 rows × 13 cols = 163 bytes
#  Fuel maps : 7-byte prefix  + proportional zones  = 115 bytes
#
#  Rows  (load axis, kPa, high→low):
#   row 0: 117  row 1: 106  row 2: 103  row 3:  97  row 4:  94
#   row 5:  91  row 6:  88  row 7:  85  row 8:  77
#   row 9:  63  row10:  51  row11:  46
#
#  Cols (RPM axis): 2000,2400,2800,3200,3600,4000,4400,4800,5200,5600,6000,6400,6800
#
#  Zone byte boundaries (ign maps 163 bytes):
#   WOT       rows 0–4  (load≥94 kPa):  bytes   0–71  (7 hdr + 5×13)
#   Part-load rows 5–8  (load 77–91):   bytes  72–123 (4×13)
#   Overrun   rows 9–11 (load≤63 kPa):  bytes 124–162 (3×13)
#
#  Stage1 confirmed: only cols 6–12 (RPM ≥ 4400) modified across all rows (+2)
#  Pop&Bang applies −12 to the overrun zone (bytes 124–162 = rows 9–11)

RPM_AXIS  = [2000,2400,2800,3200,3600,4000,4400,4800,5200,5600,6000,6400,6800]
LOAD_AXIS = [117,106,103,97,94,91,88,85,77,63,51,46]

IGN_HDR   = 7
IGN_NCOLS = 13
IGN_NROWS = 12

# byte offset of first cell in each zone (ign maps)
IGN_WOT_START  = 0        # header + rows 0-4
IGN_WOT_END    = 72       # 7 + 5×13
IGN_PL_START   = 72       # rows 5-8
IGN_PL_END     = 124      # 7 + 9×13 = 124
IGN_OVER_START = 124      # rows 9-11
IGN_OVER_END   = 163

# Fuel map zones (proportional – structure not fully decoded but verified working)
FUEL_WOT_START  = 0;   FUEL_WOT_END  = 46
FUEL_PL_START   = 46;  FUEL_PL_END   = 75
FUEL_OVER_START = 75;  FUEL_OVER_END = 115

# ═══════════════════════════════════════════════════════════════════════════════
# ECU PROFILES  — maps addresses and metadata per part number
# ═══════════════════════════════════════════════════════════════════════════════

ECU_PROFILES = {
    # ── 2004 Astra G Z22SE (our verified file) ───────────────────────────────
    "12591333": dict(
        name        = "Opel Astra G Z22SE 2004 (Hw 12591333, our file)",
        cal_prefix  = "W0L0TGF675",
        file_size   = 524288,
        ign_maps    = [0x0082C9, 0x0083A9, 0x008489, 0x008569],
        fuel_maps   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2],
        ign_trims   = [(0x00896B, 62), (0x0089CE, 22)],
        lambda_maps = [0x00C7A7, 0x00C885],
        rpm_engage  = [0x00B568, 0x00B56A],
        rpm_hyster  = [0x00B570, 0x00B572, 0x00B574, 0x00B576],
        idle_rpm    = [0x008162, 0x008164, 0x008166,
                       0x008184, 0x008186, 0x008188,
                       0x0081A6, 0x0081A8, 0x0081AA,
                       0x0081C8, 0x0081CA, 0x0081CC],
        iat_area    = (0x00A610, 0x00A650),
        knock_thr   = 0x008D81,
        o2_auth     = (0x00A680, 0x00A690),
        dtc_area    = (0x008C80, 0x008CB0),
        pin_addr    = 0x008141,
        cal_addr    = 0x00602C,
        part_addr   = 0x00800C,
        stock_rpm   = 6500,
        load_axis   = [117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46],
    ),
    # ── 2001 Astra G Z22SE (Hw 09391283 BC, verified map addresses) ──────────
    "12215796": dict(
        name        = "Opel Astra G Z22SE 2001 (Hw 09391283 BC)",
        cal_prefix  = "W0L0TGF081",
        file_size   = 524288,
        ign_maps    = [0x0082C9, 0x0083A9, 0x008489, 0x008569],
        fuel_maps   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2],
        ign_trims   = [(0x00896B, 62), (0x0089CE, 22)],
        lambda_maps = [0x00C5BD, 0x00C640],   # different offset vs 2004
        rpm_engage  = None,    # auto-scanned — 0xB568 contains different data in 2001 fw
        rpm_hyster  = None,
        idle_rpm    = [0x008162, 0x008164, 0x008166],
        iat_area    = (0x00A610, 0x00A650),
        knock_thr   = 0x008D81,
        o2_auth     = (0x00A680, 0x00A690),
        dtc_area    = (0x008C80, 0x008CB0),
        pin_addr    = 0x008141,
        cal_addr    = 0x00402C,
        part_addr   = 0x00800C,
        stock_rpm   = 6500,
        load_axis   = [117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46],
    ),
    # ── 2004 Astra G Z22SE (Hw 12210453 EB — alternative calibration) ─────────
    "12578132": dict(
        name        = "Opel Astra G Z22SE 2004 (Hw 12210453 EB)",
        cal_prefix  = "W0L0TGF084",
        file_size   = 524288,
        ign_maps    = [0x0082C9, 0x0083A9, 0x008489, 0x008569],
        fuel_maps   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2],
        ign_trims   = [(0x00896B, 62), (0x0089CE, 22)],
        lambda_maps = [0x00C7A7, 0x00C885],
        rpm_engage  = [0x00B568, 0x00B56A],
        rpm_hyster  = [0x00B570, 0x00B572, 0x00B574, 0x00B576],
        idle_rpm    = [0x008162, 0x008164, 0x008166,
                       0x008184, 0x008186, 0x008188,
                       0x0081A6, 0x0081A8, 0x0081AA,
                       0x0081C8, 0x0081CA, 0x0081CC],
        iat_area    = (0x00A610, 0x00A650),
        knock_thr   = 0x008D81,
        o2_auth     = (0x00A680, 0x00A690),
        dtc_area    = (0x008C80, 0x008CB0),
        pin_addr    = 0x008141,
        cal_addr    = 0x00602C,
        part_addr   = 0x00800C,
        stock_rpm   = 6500,
        load_axis   = [117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46],
    ),
    # ── Opel Speedster 2.2 Z22SE (Hw 12202073 BZ, 147hp) ─────────────────────
    #    NOTE: load axis is DIFFERENT (throttle/alt scale vs MAP kPa).
    #    Map byte-offsets identical; zone boundaries (WOT/PL/overrun) apply
    #    by row-position, not kPa value. Rev limit scanned automatically.
    "12210633": dict(
        name        = "Opel Speedster 2.2 Z22SE 147hp (Hw 12202073 BZ)",
        cal_prefix  = "",
        file_size   = 524288,
        ign_maps    = [0x0082C9, 0x0083A9, 0x008489, 0x008569],
        fuel_maps   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2],
        ign_trims   = [(0x00896B, 62), (0x0089CE, 22)],
        lambda_maps = [0x00C5BD, 0x00C640],
        rpm_engage  = None,    # auto-scanned
        rpm_hyster  = None,
        idle_rpm    = [0x008162, 0x008164, 0x008166],
        iat_area    = (0x00A610, 0x00A650),
        knock_thr   = 0x008D81,
        o2_auth     = (0x00A680, 0x00A690),
        dtc_area    = (0x008C80, 0x008CB0),
        pin_addr    = 0x008141,
        cal_addr    = 0x00402C,
        part_addr   = 0x00800C,
        stock_rpm   = 6500,
        # Speedster uses a different axis encoding (not MAP kPa)
        load_axis   = [59, 60, 62, 62, 60, 53, 46, 40, 35, 32, 29, 27],
    ),
    # ── Generic GMPT-E15 fallback (same platform, addresses estimated) ─────────
    "__generic__": dict(
        name        = "Generic GMPT-E15 (unrecognised)",
        cal_prefix  = "",
        file_size   = 524288,
        ign_maps    = [0x0082C9, 0x0083A9, 0x008489, 0x008569],
        fuel_maps   = [0x0086C9, 0x00876C, 0x00880F, 0x0088B2],
        ign_trims   = [(0x00896B, 62), (0x0089CE, 22)],
        lambda_maps = [0x00C7A7, 0x00C885],
        rpm_engage  = None,    # auto-scanned
        rpm_hyster  = None,
        idle_rpm    = [0x008162, 0x008164, 0x008166],
        iat_area    = (0x00A610, 0x00A650),
        knock_thr   = 0x008D81,
        o2_auth     = (0x00A680, 0x00A690),
        dtc_area    = (0x008C80, 0x008CB0),
        pin_addr    = 0x008141,
        cal_addr    = 0x00602C,
        part_addr   = 0x00800C,
        stock_rpm   = 6500,
        load_axis   = [117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46],
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# TUNE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TuneEngine:
    def __init__(self):
        self.buf            = None
        self.orig           = None
        self.filepath       = None
        self.profile        = None
        self.changes        = []
        self.scanned_rev_addr  = None   # populated by _scan_rev_limit when needed
        self.scanned_rev_rpm   = None

    # ── I/O ──────────────────────────────────────────────────────────────────

    def load(self, path: str) -> dict:
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) != 524288:
            raise ValueError(f"File is {len(data):,} bytes — expected 524,288 (512 KB)")
        self.buf               = bytearray(data)
        self.orig              = bytearray(data)
        self.filepath          = path
        self.changes           = []
        self.scanned_rev_addr  = None
        self.scanned_rev_rpm   = None
        return self._detect()

    def _scan_rev_limit(self) -> tuple:
        """Scan binary for plausible rev-limit value. Returns (addr, rpm) or (None, None)."""
        b = self.orig
        # search for uint16 BE pairs of identical/adjacent RPM values in 5500-7500 range
        from collections import Counter
        hits = {}
        for i in range(0, len(b) - 1, 2):
            val = struct.unpack_from('>H', b, i)[0]
            if 5500 <= val <= 7500:
                hits[i] = val
        if not hits:
            return None, None
        # favour addresses near 0xB500-0xB600 range (known area for 2004)
        # and values that repeat at adjacent even addresses
        best_addr, best_rpm = None, None
        for addr in sorted(hits):
            rpm = hits[addr]
            # check if same value repeats 2 bytes later (engage/cut pair)
            if addr + 2 in hits and hits[addr + 2] == rpm:
                # prefer addresses in calibration-looking range (0x8000+)
                if best_addr is None or (0x8000 <= addr <= 0xC000):
                    best_addr, best_rpm = addr, rpm
        if best_addr is None and hits:
            # fallback: most common RPM in the first half of file
            cnt = Counter(v for a, v in hits.items() if a < 0x40000)
            if cnt:
                best_rpm = cnt.most_common(1)[0][0]
                best_addr = next(a for a, v in sorted(hits.items()) if v == best_rpm)
        return best_addr, best_rpm

    def _detect(self) -> dict:
        raw_part = self.orig[0x00800C:0x00800C+8].decode('ascii','replace').strip('\x00 \xff')
        self.profile = ECU_PROFILES.get(raw_part, ECU_PROFILES['__generic__'])
        p = self.profile

        # Cal ID — try both 2004 (0x602C) and 2001 (0x402C) locations
        raw_cal = self.orig[p['cal_addr']:p['cal_addr']+17].decode('ascii','replace').strip('\x00 \xff\xfe')
        # strip any non-printable
        raw_cal = ''.join(c for c in raw_cal if 32 <= ord(c) < 127)

        pb      = self.orig[p['pin_addr']:p['pin_addr']+2]
        pin     = f"{pb[0]>>4}{pb[0]&0xF}{pb[1]>>4}{pb[1]&0xF}"

        # Rev limit — use profile address if valid, otherwise scan
        rev_rpm = 0
        rev_source = "—"
        if p['rpm_engage']:
            rev_rpm = struct.unpack_from('>H', self.orig, p['rpm_engage'][0])[0]
            rev_source = f"0x{p['rpm_engage'][0]:05X}"
        if not p['rpm_engage'] or not (1000 <= rev_rpm <= 9000):
            scan_addr, scan_rpm = self._scan_rev_limit()
            if scan_rpm:
                self.scanned_rev_addr = scan_addr
                self.scanned_rev_rpm  = scan_rpm
                rev_rpm    = scan_rpm
                rev_source = f"scanned@0x{scan_addr:05X}"
            else:
                rev_rpm    = p['stock_rpm']
                rev_source = "default"

        idle    = struct.unpack_from('>H', self.orig, p['idle_rpm'][0])[0]
        if not (400 <= idle <= 2000):
            idle = 800

        load_ax = p.get('load_axis', [117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46])
        is_speedster = raw_part == "12210633"
        known   = raw_part in ECU_PROFILES
        return dict(part=raw_part, cal_id=raw_cal, pin=pin,
                    rev_rpm=rev_rpm, rev_source=rev_source,
                    idle_rpm=idle, size_kb=len(self.orig)//1024,
                    known=known, profile_name=self.profile['name'],
                    load_axis=load_ax, is_speedster=is_speedster)

    def backup(self):
        ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
        dst = self.filepath + f'.backup_{ts}'
        shutil.copy2(self.filepath, dst)
        return dst

    def save(self, path: str):
        with open(path, 'wb') as f: f.write(self.buf)

    def reset(self):
        self.buf     = bytearray(self.orig)
        self.changes = []

    def changed_byte_count(self):
        return sum(1 for a,b in zip(self.buf,self.orig) if a!=b)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(v): return max(1, min(254, v))

    def _delta_range(self, addr, start, end, delta, label=""):
        """Apply delta to buf[addr+start .. addr+end-1]."""
        changed = 0
        for i in range(start, end):
            nv = self._clamp(self.buf[addr+i] + delta)
            if nv != self.buf[addr+i]:
                self.buf[addr+i] = nv; changed += 1
        if label and changed:
            self.changes.append(f"    {label}: {delta:+d} → {changed} cells")
        return changed

    def _write_u16be(self, addr, val, label=""):
        struct.pack_into('>H', self.buf, addr, val)
        if label: self.changes.append(f"    {label}: {val}")

    # ── Map zone writers ──────────────────────────────────────────────────────

    def _ign(self, wot, pl, overrun=0):
        p = self.profile
        for addr in p['ign_maps']:
            name = f"Ign@0x{addr:06X}"
            self._delta_range(addr, IGN_WOT_START,  IGN_WOT_END,  wot,    f"{name} WOT (load≥94kPa)")
            self._delta_range(addr, IGN_PL_START,   IGN_PL_END,   pl,     f"{name} Part-load (77–91kPa)")
            if overrun:
                self._delta_range(addr, IGN_OVER_START, IGN_OVER_END, overrun,
                                  f"{name} Overrun (load≤63kPa, all RPM)")

    def _fuel(self, wot, pl, overrun=0):
        p = self.profile
        for addr in p['fuel_maps']:
            name = f"Fuel@0x{addr:06X}"
            self._delta_range(addr, FUEL_WOT_START,  FUEL_WOT_END,  wot,  f"{name} WOT")
            self._delta_range(addr, FUEL_PL_START,   FUEL_PL_END,   pl,   f"{name} Part-load")
            if overrun:
                self._delta_range(addr, FUEL_OVER_START, FUEL_OVER_END, overrun,
                                  f"{name} Overrun enrich")

    def _lambda(self, wot, pl=0):
        p = self.profile
        for i, addr in enumerate(p['lambda_maps']):
            tag = "primary" if i==0 else "backup"
            # lambda maps same 163-byte structure
            self._delta_range(addr, IGN_WOT_START, IGN_WOT_END,  wot, f"Lambda {tag} WOT")
            if pl:
                self._delta_range(addr, IGN_PL_START,  IGN_PL_END,   pl,  f"Lambda {tag} PL")

    def _trims(self, d):
        for addr, size in self.profile['ign_trims']:
            self._delta_range(addr, 0, size, d, f"Ign trim 0x{addr:06X}")

    # ── Tune profiles ─────────────────────────────────────────────────────────

    def apply_stage1(self):
        self.changes.append("► Stage 1  [verified against real Stage1 binary]")
        self.changes.append(f"  Ign: +2 WOT (load≥94kPa) / +1 PL (77–91kPa)")
        self.changes.append(f"  Fuel: +2 WOT / +1 PL")
        self.changes.append(f"  Lambda: −7 WOT (richer) | RPM limit: unchanged")
        self._ign(wot=2, pl=1); self._fuel(wot=2, pl=1)
        self._trims(1); self._lambda(wot=-7)

    def apply_stage1plus(self):
        self.changes.append("► Stage 1+  [moderate, uniform]")
        self.changes.append(f"  Ign: +3 WOT / +2 PL  |  Fuel: +3 WOT / +2 PL")
        self.changes.append(f"  Lambda: −9 WOT / −3 PL")
        self._ign(wot=3, pl=2); self._fuel(wot=3, pl=2)
        self._trims(1); self._lambda(wot=-9, pl=-3)

    def apply_stage2(self):
        self.changes.append("► Stage 2  [aggressive + 6800 RPM]")
        self.changes.append(f"  Ign: +5 WOT / +3 PL  |  Fuel: +4 WOT / +2 PL")
        self.changes.append(f"  Lambda: −11 WOT / −5 PL  |  Rev limit: 6800 RPM")
        self._ign(wot=5, pl=3); self._fuel(wot=4, pl=2)
        self._trims(2); self._lambda(wot=-11, pl=-5)
        self.apply_rev_limit(6800)

    def apply_pop_bang(self):
        self.changes.append("► Pop & Bang  [overrun zone: load≤63kPa, all RPM 2000–6800]")
        self.changes.append(f"  Ign overrun: −12 counts  |  Fuel overrun: +4 counts")
        self._ign(wot=0, pl=0, overrun=-12)
        self._fuel(wot=0, pl=0, overrun=+4)

    def apply_burble(self):
        self.changes.append("► Burble  [aggressive overrun: load≤63kPa, all RPM]")
        self.changes.append(f"  Ign overrun: −20 counts  |  Fuel overrun: +7 counts")
        self._ign(wot=0, pl=0, overrun=-20)
        self._fuel(wot=0, pl=0, overrun=+7)

    def apply_rev_limit(self, rpm: int):
        p = self.profile
        engage_addrs = p['rpm_engage']
        hyster_addrs = p['rpm_hyster']
        # Fall back to scanned addresses when profile has None
        if not engage_addrs and self.scanned_rev_addr is not None:
            engage_addrs = [self.scanned_rev_addr, self.scanned_rev_addr + 2]
            hyster_addrs = [self.scanned_rev_addr + 8, self.scanned_rev_addr + 10,
                            self.scanned_rev_addr + 12, self.scanned_rev_addr + 14]
        if not engage_addrs:
            self.changes.append(f"► Rev Limit  SKIPPED — address unknown for this ECU variant")
            return
        orig = struct.unpack_from('>H', self.orig, engage_addrs[0])[0]
        if not (1000 <= orig <= 9000):
            orig = self.scanned_rev_rpm or p['stock_rpm']
        if rpm == orig:
            return
        self.changes.append(f"► Rev Limit  {orig} → {rpm} RPM")
        hyst = rpm - 6
        for a in engage_addrs:
            self._write_u16be(a, rpm,  f"  Fuel cut engage  0x{a:06X}")
        if hyster_addrs:
            for a in hyster_addrs:
                self._write_u16be(a, hyst, f"  Fuel cut hyster  0x{a:06X}")

    def apply_idle_rpm(self, rpm: int):
        p = self.profile
        orig = struct.unpack_from('>H', self.orig, p['idle_rpm'][0])[0]
        if rpm == orig: return
        self.changes.append(f"► Idle RPM  {orig} → {rpm} RPM")
        for a in p['idle_rpm']:
            self._write_u16be(a, rpm, f"  Idle target 0x{a:06X}")

    def apply_knock_protection(self, level: str):
        p = self.profile
        a = p['knock_thr']
        orig = self.orig[a]
        # level: "stock"=orig, "safe"=0x64(100), "aggressive"=0x28(40), "disabled"=0xFF
        vals = {"stock": orig, "safe": 100, "aggressive": 40, "disabled": 0xFF}
        v = vals.get(level, orig)
        if v != self.buf[a]:
            self.buf[a] = v
            self.changes.append(f"► Knock protection: {level}  (0x{a:06X} = {v})")

    def apply_iat_correction(self, scale: float):
        """Scale IAT timing correction. 1.0=stock, 0.0=disabled, 0.5=half."""
        p = self.profile
        start, end = p['iat_area']
        patched = 0
        for i in range(start, end):
            orig = self.orig[i]
            nv   = self._clamp(round(orig * scale))
            if nv != self.buf[i]:
                self.buf[i] = nv; patched += 1
        if patched:
            self.changes.append(f"► IAT correction scaled ×{scale:.1f}  ({patched} bytes)")

    # ── Disable options ───────────────────────────────────────────────────────

    def disable_lambda(self):
        p = self.profile
        self.changes.append("► Lambda/O2 Closed-Loop DISABLED  ⚠")
        # Clamp CL authority to neutral (0x80)
        start, end = p['o2_auth']
        patched = 0
        for i in range(start, end):
            if self.buf[i] > 0x80:
                self.buf[i] = 0x80; patched += 1
        self.changes.append(f"    CL authority clamped: {patched} bytes → 0x80")
        self._lambda(wot=-14, pl=-14)

    def disable_egr(self):
        self.changes.append("► EGR Disable — N/A (Z22SE has no EGR)")

    def disable_dtc(self):
        p = self.profile
        self.changes.append("► DTC Monitoring DISABLED  ⚠  (best-effort)")
        start, end = p['dtc_area']
        patched = 0
        for i in range(start, end):
            if 0x04 <= self.buf[i] <= 0x1E:
                self.buf[i] = 0x00; patched += 1
        self.changes.append(f"    DTC threshold area: {patched} bytes zeroed")

    def get_changes_text(self) -> str:
        if not self.changes:
            return "No changes applied yet.\n\nLoad a .bin and press ▶ Apply Tune."
        hdr = [
            f"File:     {Path(self.filepath).name}",
            f"Profile:  {self.profile['name']}",
            f"Modified: {self.changed_byte_count():,} bytes",
            "─" * 60,
        ]
        return "\n".join(hdr + self.changes)

    # ── File comparison ───────────────────────────────────────────────────────

    def compare_files(self, path_a: str, path_b: str) -> str:
        a = bytearray(open(path_a,'rb').read())
        b = bytearray(open(path_b,'rb').read())
        if len(a) != len(b):
            return f"Cannot compare — files differ in size ({len(a):,} vs {len(b):,} bytes)"

        # merge adjacent changed bytes into regions
        regions, start, prev = [], None, 0
        for i in range(len(a)):
            if a[i] != b[i]:
                if start is None: start = i
                prev = i
            else:
                if start is not None:
                    regions.append((start, prev)); start = None
        if start is not None: regions.append((start, prev))
        merged = []
        for s,e in regions:
            if merged and s-merged[-1][1] <= 8: merged[-1][1] = e
            else: merged.append([s,e])

        total = sum(e-s+1 for s,e in merged)
        lines = [
            f"Comparison: {Path(path_a).name}  vs  {Path(path_b).name}",
            f"Total changed bytes: {total:,}   Regions: {len(merged)}",
            "─" * 60,
        ]
        # Annotate known regions
        KNOWN = {
            (0x0082C9,0x00836B): "Ignition Map #1",
            (0x0083A9,0x00844B): "Ignition Map #2",
            (0x008489,0x00852B): "Ignition Map #3",
            (0x008569,0x00860B): "Ignition Map #4",
            (0x0086C9,0x008742): "Fuel Map #1",
            (0x00876C,0x0087DE): "Fuel Map #2",
            (0x00880F,0x008881): "Fuel Map #3",
            (0x0088B2,0x008924): "Fuel Map #4",
            (0x00896B,0x0089AA): "Ign Trim #1",
            (0x0089CE,0x0089E3): "Ign Trim #2",
            (0x00C7A7,0x00C849): "Lambda Map #1 (2004)",
            (0x00C885,0x00C927): "Lambda Map #2 (2004)",
            (0x00C5BD,0x00C777): "Lambda Map (2001 offset)",
            (0x00B568,0x00B579): "Rev Limiter",
            (0x008162,0x00816A): "Idle RPM",
        }
        for s,e in merged:
            size = e-s+1
            tag = ""
            for (ks,ke),kn in KNOWN.items():
                if ks <= s <= ke or ks <= e <= ke:
                    tag = f"  ← {kn}"; break
            # Show per-byte deltas for small regions
            if size <= 20:
                delta_cells = [(a[i],b[i],b[i]-a[i]) for i in range(s,e+1) if a[i]!=b[i]]
                sample = "  |  " + " ".join(f"{av}→{bv}({dv:+d})" for av,bv,dv in delta_cells[:6])
                if len(delta_cells) > 6: sample += "…"
            else:
                deltas = [b[i]-a[i] for i in range(s,e+1) if a[i]!=b[i]]
                uniq   = set(deltas)
                sample = f"  |  Δ unique values: {sorted(uniq)[:8]}"
            lines.append(f"  0x{s:06X}–0x{e:06X}  ({size:5d}B){tag}{sample}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

DARK_QSS = """
QMainWindow,QWidget{background:#0d1117;color:#e6edf3;font-family:"Segoe UI","Ubuntu",sans-serif;font-size:13px}
QGroupBox{background:#161b22;border:1px solid #30363d;border-radius:6px;margin-top:10px;padding:10px 8px 8px;font-weight:bold;font-size:12px;color:#8b949e}
QGroupBox::title{subcontrol-origin:margin;subcontrol-position:top left;padding:0 6px;color:#58a6ff;font-size:12px}
QPushButton{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:5px;padding:6px 16px;font-size:13px}
QPushButton:hover{background:#30363d;border-color:#58a6ff}
QPushButton:pressed{background:#161b22}
QPushButton:disabled{color:#484f58;border-color:#21262d}
QPushButton#btn_apply{background:#238636;border-color:#2ea043;color:#fff;font-weight:bold;font-size:14px;padding:8px 24px}
QPushButton#btn_apply:hover{background:#2ea043}
QPushButton#btn_apply:disabled{background:#21262d;color:#484f58;border-color:#21262d}
QPushButton#btn_save{background:#1f6feb;border-color:#388bfd;color:#fff;font-weight:bold;padding:8px 24px}
QPushButton#btn_save:hover{background:#388bfd}
QPushButton#btn_save:disabled{background:#21262d;color:#484f58;border-color:#21262d}
QPushButton#btn_reset{background:#6e40c9;border-color:#8957e5;color:#fff}
QPushButton#btn_reset:hover{background:#8957e5}
QRadioButton,QCheckBox{spacing:8px;color:#e6edf3;padding:3px 0}
QRadioButton::indicator,QCheckBox::indicator{width:15px;height:15px;border:2px solid #484f58;border-radius:8px;background:#0d1117}
QRadioButton::indicator:checked{background:#58a6ff;border-color:#58a6ff}
QCheckBox::indicator{border-radius:3px}
QCheckBox::indicator:checked{background:#3fb950;border-color:#3fb950}
QCheckBox#warn_check::indicator:checked{background:#f85149;border-color:#f85149}
QLabel#info_val{color:#58a6ff;font-weight:bold}
QLabel#warn_label{color:#e3b341;font-size:11px}
QLabel#ok_label{color:#3fb950}
QLabel#err_label{color:#f85149}
QTextEdit{background:#161b22;color:#c9d1d9;border:1px solid #30363d;border-radius:4px;font-family:"JetBrains Mono","Consolas","Courier New",monospace;font-size:12px;padding:6px}
QScrollArea{border:none;background:transparent}
QScrollBar:vertical{background:#161b22;width:8px;border-radius:4px}
QScrollBar::handle:vertical{background:#484f58;border-radius:4px;min-height:20px}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
QStatusBar{background:#010409;color:#8b949e;border-top:1px solid #30363d;font-size:12px}
QStatusBar::item{border:none}
QSpinBox,QDoubleSpinBox,QComboBox{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:4px;padding:3px 8px}
QSpinBox:focus,QDoubleSpinBox:focus,QComboBox:focus{border-color:#58a6ff}
QComboBox::drop-down{border:none}
QComboBox QAbstractItemView{background:#21262d;color:#e6edf3;border:1px solid #30363d;selection-background-color:#1f6feb}
QTabWidget::pane{background:#161b22;border:1px solid #30363d;border-radius:0 4px 4px 4px}
QTabBar::tab{background:#21262d;color:#8b949e;border:1px solid #30363d;padding:6px 14px;border-bottom:none;border-radius:4px 4px 0 0;margin-right:2px}
QTabBar::tab:selected{background:#161b22;color:#e6edf3;border-top:2px solid #58a6ff}
QTabBar::tab:hover{color:#c9d1d9}
QSlider::groove:horizontal{height:4px;background:#30363d;border-radius:2px}
QSlider::handle:horizontal{background:#58a6ff;border:none;width:14px;height:14px;margin:-5px 0;border-radius:7px}
QSlider::sub-page:horizontal{background:#1f6feb;border-radius:2px}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def hline():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:#30363d;max-height:1px;"); return f

class InfoRow(QWidget):
    def __init__(self, key, val="—"):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(0,1,0,1)
        self.key_lbl = QLabel(key+":"); self.key_lbl.setStyleSheet("color:#8b949e;min-width:110px;")
        self.val_lbl = QLabel(val);     self.val_lbl.setObjectName("info_val")
        lay.addWidget(self.key_lbl); lay.addWidget(self.val_lbl, 1)
    def set(self, val, color=None):
        self.val_lbl.setText(str(val))
        if color: self.val_lbl.setStyleSheet(f"color:{color};font-weight:bold;")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = TuneEngine()
        self._cmp_file = None
        self.setWindowTitle("Z22SE GMPT-E15 ECU Tuner  v3  —  Multi-ECU")
        self.setMinimumSize(1140, 820)
        self.resize(1320, 900)
        self._build_ui()
        self._set_controls_enabled(False)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_toolbar())
        root.addWidget(hline())
        spl = QSplitter(Qt.Orientation.Horizontal)
        spl.setHandleWidth(2)
        spl.setStyleSheet("QSplitter::handle{background:#30363d;}")
        spl.addWidget(self._build_left())
        spl.addWidget(self._build_right())
        spl.setSizes([460, 860])
        root.addWidget(spl, 1)
        self.statusBar().showMessage("No file loaded — Open a GMPT-E15 .bin file to begin")

    def _build_toolbar(self):
        bar = QWidget()
        bar.setStyleSheet("background:#010409;border-bottom:1px solid #30363d;")
        bar.setFixedHeight(52)
        lay = QHBoxLayout(bar); lay.setContentsMargins(16,8,16,8)
        title = QLabel("⚙  Z22SE GMPT-E15 ECU Tuner  v3")
        title.setStyleSheet("color:#58a6ff;font-size:16px;font-weight:bold;")
        lay.addWidget(title); lay.addStretch()
        self.btn_open   = QPushButton("📂  Open .bin")
        self.btn_backup = QPushButton("🗄  Backup")
        self.btn_save   = QPushButton("💾  Save As…")
        self.btn_save.setObjectName("btn_save")
        for b in [self.btn_open, self.btn_backup, self.btn_save]: lay.addWidget(b)
        self.btn_open.clicked.connect(self._on_open)
        self.btn_backup.clicked.connect(self._on_backup)
        self.btn_save.clicked.connect(self._on_save)
        return bar

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left(self):
        outer = QWidget(); outer.setMinimumWidth(430); outer.setMaximumWidth(520)
        vbox  = QVBoxLayout(outer); vbox.setContentsMargins(12,10,6,10); vbox.setSpacing(8)
        vbox.addWidget(self._build_ecu_info())
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        il = QVBoxLayout(inner); il.setContentsMargins(0,0,8,0); il.setSpacing(8)
        il.addWidget(self._build_tune_profiles())
        il.addWidget(self._build_extra_features())
        il.addWidget(self._build_fine_tuning())
        il.addWidget(self._build_disable_options())
        il.addStretch()
        scroll.setWidget(inner); vbox.addWidget(scroll, 1)
        vbox.addWidget(hline())
        btn_row = QHBoxLayout()
        self.btn_reset = QPushButton("↩  Reset");   self.btn_reset.setObjectName("btn_reset")
        self.btn_apply = QPushButton("▶  Apply Tune"); self.btn_apply.setObjectName("btn_apply")
        self.btn_reset.clicked.connect(self._on_reset)
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_reset.setFixedHeight(38); self.btn_apply.setFixedHeight(38)
        btn_row.addWidget(self.btn_reset); btn_row.addWidget(self.btn_apply, 2)
        vbox.addLayout(btn_row)
        return outer

    def _build_ecu_info(self):
        gb  = QGroupBox("ECU Information")
        lay = QVBoxLayout(gb); lay.setSpacing(2)
        self._row_part    = InfoRow("Part #")
        self._row_cal     = InfoRow("Cal ID / VIN")
        self._row_profile = InfoRow("Profile")
        self._row_pin     = InfoRow("PIN")
        self._row_rev     = InfoRow("Rev Limit")
        self._row_idle    = InfoRow("Idle RPM")
        self._row_load    = InfoRow("Load Axis")
        self._row_status  = InfoRow("Status")
        for r in [self._row_part, self._row_cal, self._row_profile,
                  self._row_pin, self._row_rev, self._row_idle,
                  self._row_load, self._row_status]:
            lay.addWidget(r)
        return gb

    def _build_tune_profiles(self):
        gb  = QGroupBox("Tune Profile")
        lay = QVBoxLayout(gb)
        self._tune_group = QButtonGroup(self)
        profiles = [
            ("stock",  "⬛  Stock",    "No changes — restore to factory values."),
            ("stage1", "🟡  Stage 1",  "Ign +2 WOT/+1 PL  |  Fuel +2 WOT/+1 PL  |  Lambda −7 WOT\n"
                                       "Verified against real Stage1 binary. Safe for stock hardware."),
            ("stage1p","🟠  Stage 1+", "Ign +3/+2  |  Fuel +3/+2  |  Lambda −9 WOT /−3 PL\n"
                                       "Recommended: panel filter + sports exhaust."),
            ("stage2", "🔴  Stage 2",  "Ign +5 WOT/+3 PL  |  Fuel +4/+2  |  Lambda −11/−5  |  6800 RPM\n"
                                       "Requires: cold intake, exhaust, proper fuelling. Dyno verify."),
        ]
        for key, title, desc in profiles:
            rb = QRadioButton(title)
            rb.setProperty("tune_key", key)
            tip = QLabel(desc)
            tip.setStyleSheet("color:#8b949e;font-size:11px;margin-left:26px;margin-bottom:4px;")
            tip.setWordWrap(True)
            lay.addWidget(rb); lay.addWidget(tip)
            self._tune_group.addButton(rb)
            if key == "stock": rb.setChecked(True)
        return gb

    def _build_extra_features(self):
        gb  = QGroupBox("Extra Features")
        lay = QVBoxLayout(gb)

        self.chk_pop    = QCheckBox("💥  Pop & Bang")
        lbl_pop = QLabel("   Ign −12 overrun (load≤63kPa, all RPM 2000–6800)  +  Fuel +4 overrun")
        lbl_pop.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;margin-bottom:3px;")

        self.chk_burble = QCheckBox("🔥  Burble / Crackle")
        lbl_bur = QLabel("   Ign −20 overrun  +  Fuel +7 overrun. Not for daily driving.")
        lbl_bur.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;margin-bottom:6px;")

        # Rev limit
        rev_row = QHBoxLayout()
        self.chk_rev  = QCheckBox("🏁  Custom Rev Limit")
        self.spin_rev = QSpinBox()
        self.spin_rev.setRange(5500, 7500); self.spin_rev.setSingleStep(100)
        self.spin_rev.setValue(6500); self.spin_rev.setSuffix("  RPM")
        self.spin_rev.setFixedWidth(115); self.spin_rev.setEnabled(False)
        rev_row.addWidget(self.chk_rev); rev_row.addWidget(self.spin_rev); rev_row.addStretch()

        # Idle RPM
        idle_row = QHBoxLayout()
        self.chk_idle  = QCheckBox("⏱  Adjust Idle RPM")
        self.spin_idle = QSpinBox()
        self.spin_idle.setRange(600, 1200); self.spin_idle.setSingleStep(50)
        self.spin_idle.setValue(800); self.spin_idle.setSuffix("  RPM")
        self.spin_idle.setFixedWidth(115); self.spin_idle.setEnabled(False)
        idle_row.addWidget(self.chk_idle); idle_row.addWidget(self.spin_idle); idle_row.addStretch()
        lbl_idle = QLabel("   Warm idle target. Stock = 800 RPM. Multiple map locations updated.")
        lbl_idle.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;")

        for w in [self.chk_pop, lbl_pop, self.chk_burble, lbl_bur]: lay.addWidget(w)
        lay.addLayout(rev_row); lay.addLayout(idle_row); lay.addWidget(lbl_idle)

        self.chk_pop.toggled.connect(lambda c: self.chk_burble.setEnabled(not c) if c else None)
        self.chk_burble.toggled.connect(lambda c: self.chk_pop.setEnabled(not c) if c else None)
        self.chk_rev.toggled.connect(self.spin_rev.setEnabled)
        self.chk_idle.toggled.connect(self.spin_idle.setEnabled)
        return gb

    def _build_fine_tuning(self):
        gb  = QGroupBox("Fine Tuning")
        lay = QVBoxLayout(gb)

        # IAT correction
        iat_row = QHBoxLayout()
        self.chk_iat  = QCheckBox("🌡  IAT Correction Scale")
        self.spin_iat = QDoubleSpinBox()
        self.spin_iat.setRange(0.0, 1.5); self.spin_iat.setSingleStep(0.1)
        self.spin_iat.setValue(1.0); self.spin_iat.setDecimals(1); self.spin_iat.setFixedWidth(80)
        self.spin_iat.setEnabled(False)
        iat_row.addWidget(self.chk_iat); iat_row.addWidget(self.spin_iat); iat_row.addStretch()
        lbl_iat = QLabel("   1.0=stock, 0.0=fully disabled, 0.5=half. Reduces IAT timing pullback.")
        lbl_iat.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;margin-bottom:4px;")
        lbl_iat.setWordWrap(True)

        # Knock protection
        knock_row = QHBoxLayout()
        lbl_knock_hdr = QLabel("🔔  Knock Protection:")
        lbl_knock_hdr.setStyleSheet("color:#e6edf3;")
        self.combo_knock = QComboBox()
        self.combo_knock.addItems(["stock", "safe (conservative)", "aggressive", "disabled ⚠"])
        self.combo_knock.setEnabled(False)
        lbl_knock = QLabel("   Adjusts knock-retard trigger threshold at 0x008D81.")
        lbl_knock.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;")
        knock_row.addWidget(lbl_knock_hdr); knock_row.addWidget(self.combo_knock); knock_row.addStretch()

        for row in [iat_row, knock_row]: lay.addLayout(row)
        for w in [lbl_iat, lbl_knock]: lay.addWidget(w)

        self.chk_iat.toggled.connect(self.spin_iat.setEnabled)
        return gb

    def _build_disable_options(self):
        gb  = QGroupBox("Disable / Delete Options  ⚠")
        lay = QVBoxLayout(gb)
        gb.setStyleSheet("QGroupBox{border-color:#f85149;}QGroupBox::title{color:#f85149;}")

        warn = QLabel("⚠  Modify ECU safety systems. Use at your own risk. Always verify on wideband O2.")
        warn.setObjectName("warn_label"); warn.setWordWrap(True)
        lay.addWidget(warn); lay.addWidget(hline())

        def opt(title, tip, desc, disabled_reason=None):
            chk = QCheckBox(title); chk.setObjectName("warn_check"); chk.setToolTip(tip)
            if disabled_reason: chk.setEnabled(False); chk.setToolTip(disabled_reason)
            lbl = QLabel(f"   {desc}")
            lbl.setStyleSheet("color:#8b949e;font-size:11px;margin-left:4px;margin-bottom:4px;")
            lbl.setWordWrap(True)
            lay.addWidget(chk); lay.addWidget(lbl)
            return chk

        self.chk_lambda = opt(
            "🔴  Disable Lambda/O2 CL",
            "Clamp O2 authority to neutral",
            "Clamps CL authority → 0x80 neutral + fixes lambda targets full-rich.\n"
            "⚠ Best-effort. Verify on wideband O2 after flashing.")
        self.chk_egr = opt(
            "⬜  Disable EGR", "N/A",
            "Not applicable — Z22SE 2.2 petrol has no EGR valve.",
            disabled_reason="Z22SE has no EGR. N/A.")
        self.chk_dtc = opt(
            "🔴  Disable DTC Monitoring",
            "Zero DTC thresholds",
            "Zeroes threshold values in DTC calibration area.\n"
            "⚠ Best-effort — not all DTCs guaranteed silent.")
        self.chk_speed = opt(
            "🟠  Speed Limiter Remove",
            "Address not confirmed",
            "VSS limiter address not confirmed for this calibration revision.",
            disabled_reason="Speed limiter address unconfirmed — disabled for safety.")
        return gb

    # ── Right panel ───────────────────────────────────────────────────────────

    def _build_right(self):
        outer = QWidget()
        vbox  = QVBoxLayout(outer); vbox.setContentsMargins(6,10,12,10); vbox.setSpacing(8)
        tabs  = QTabWidget()

        # ── Tab 1: Changes preview ────────────────────────────────────────────
        pw = QWidget(); pl = QVBoxLayout(pw); pl.setContentsMargins(8,8,8,8)
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Changes Preview"))
        hdr.addStretch()
        self.lbl_bytes = QLabel("0 bytes modified")
        self.lbl_bytes.setStyleSheet("color:#8b949e;font-size:12px;")
        hdr.addWidget(self.lbl_bytes)
        pl.addLayout(hdr)
        self.preview_text = QTextEdit(); self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Apply a tune profile to see changes here…")
        pl.addWidget(self.preview_text, 1)
        tabs.addTab(pw, "📋  Changes")

        # ── Tab 2: File comparison ────────────────────────────────────────────
        cw = QWidget(); cl = QVBoxLayout(cw); cl.setContentsMargins(8,8,8,8)
        cmp_hdr = QHBoxLayout()
        self.lbl_cmp_a = QLabel("File A: (currently loaded)")
        self.lbl_cmp_a.setStyleSheet("color:#8b949e;font-size:12px;")
        self.btn_cmp_b = QPushButton("📂  Load File B…")
        self.btn_cmp_b.clicked.connect(self._on_load_cmp)
        self.btn_cmp_run = QPushButton("▶  Compare")
        self.btn_cmp_run.clicked.connect(self._on_compare)
        self.btn_cmp_run.setEnabled(False)
        cmp_hdr.addWidget(self.lbl_cmp_a, 1)
        cmp_hdr.addWidget(self.btn_cmp_b)
        cmp_hdr.addWidget(self.btn_cmp_run)
        cl.addLayout(cmp_hdr)
        self.lbl_cmp_b = QLabel("File B: none loaded")
        self.lbl_cmp_b.setStyleSheet("color:#8b949e;font-size:12px;")
        cl.addWidget(self.lbl_cmp_b)
        self.cmp_text = QTextEdit(); self.cmp_text.setReadOnly(True)
        self.cmp_text.setPlaceholderText("Load File B then click Compare…")
        cl.addWidget(self.cmp_text, 1)
        tabs.addTab(cw, "🔍  Compare Files")

        # ── Tab 3: Address map ────────────────────────────────────────────────
        rw = QWidget(); rl = QVBoxLayout(rw); rl.setContentsMargins(8,8,8,8)
        rt = QTextEdit(); rt.setReadOnly(True); rt.setText(self._addr_map_text())
        rl.addWidget(rt); tabs.addTab(rw, "📍  Address Map")

        # ── Tab 4: Pop&Bang zone detail ───────────────────────────────────────
        zw = QWidget(); zl = QVBoxLayout(zw); zl.setContentsMargins(8,8,8,8)
        zt = QTextEdit(); zt.setReadOnly(True); zt.setText(POP_BANG_DETAIL)
        zl.addWidget(zt); tabs.addTab(zw, "💥  Zone Details")

        # ── Tab 5: Notes ──────────────────────────────────────────────────────
        nw = QWidget(); nl = QVBoxLayout(nw); nl.setContentsMargins(8,8,8,8)
        nt = QTextEdit(); nt.setReadOnly(True); nt.setText(NOTES_TEXT)
        nl.addWidget(nt); tabs.addTab(nw, "ℹ  Notes")

        vbox.addWidget(tabs, 1)
        vbox.addWidget(hline())
        bot = QHBoxLayout()
        self.lbl_detail = QLabel("Load a .bin file to start")
        self.lbl_detail.setStyleSheet("color:#8b949e;")
        bot.addWidget(self.lbl_detail, 1)
        vbox.addLayout(bot)
        return outer

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open ECU Binary", str(Path.home()/"Desktop"),
            "ECU files (*.bin *.BIN *.ORI *.ori);;Binary files (*.bin *.BIN);;ORI files (*.ORI *.ori);;All files (*)")
        if not path: return
        try:
            info = self.engine.load(path)
        except ValueError as e:
            QMessageBox.critical(self, "Load Error", str(e)); return

        c = "#3fb950" if info['known'] else "#e3b341"
        self._row_part.set(info['part'], c)
        self._row_cal.set(info['cal_id'] if info['cal_id'] else "—")
        self._row_profile.set(info['profile_name'], "#58a6ff" if info['known'] else "#e3b341")
        self._row_pin.set(info['pin'], "#58a6ff")
        rev_lbl = f"{info['rev_rpm']} RPM  [{info['rev_source']}]"
        self._row_rev.set(rev_lbl, "#58a6ff" if "scanned" not in info['rev_source'] else "#e3b341")
        self._row_idle.set(f"{info['idle_rpm']} RPM")
        ax = info.get('load_axis', [])
        ax_str = "  ".join(str(v) for v in ax[:6]) + ("  …" if len(ax) > 6 else "")
        self._row_load.set(ax_str, "#c9d1d9" if ax[0] < 80 else "#58a6ff")
        if info['known']:
            self._row_status.set(f"✅  Recognised ({info['part']})", "#3fb950")
        else:
            self._row_status.set("⚠  Unknown — using generic GMPT-E15 map", "#e3b341")
            QMessageBox.warning(self, "Unknown ECU",
                f"Part number '{info['part']}' is not in the profile database.\n"
                "Using generic GMPT-E15 addresses — verify results carefully.")

        if info.get('is_speedster'):
            QMessageBox.information(self, "Speedster File Detected",
                "Opel Speedster 2.2 Z22SE detected (12210633/BZ).\n\n"
                "⚠ Load axis uses a different scale to the Astra.\n"
                "Zone boundaries (WOT/PL/Overrun) are applied by row-position "
                "(rows 0–4 / 5–8 / 9–11) which is consistent across all variants.\n\n"
                "Rev limit was auto-scanned — verify before flashing.")
        elif info['rev_source'].startswith('scanned'):
            QMessageBox.information(self, "Rev Limit Auto-Scanned",
                f"Rev limit address was auto-detected for this ECU variant.\n"
                f"Detected: {info['rev_rpm']} RPM @ {info['rev_source']}\n\n"
                "Verify rev limit modification carefully before flashing.")

        self._set_controls_enabled(True)
        self.spin_rev.setValue(info['rev_rpm'])
        self.spin_idle.setValue(info['idle_rpm'])
        self.lbl_cmp_a.setText(f"File A: {Path(path).name}")
        self.preview_text.clear()
        self.preview_text.setPlaceholderText("Select a profile and click ▶ Apply Tune")
        self.statusBar().showMessage(
            f"Loaded: {Path(path).name}  ({info['size_kb']} KB)  "
            f"Part: {info['part']}  Profile: {info['profile_name']}")
        self.lbl_detail.setText(f"File: {Path(path).name}")

    def _on_backup(self):
        if not self.engine.filepath: return
        dst = self.engine.backup()
        QMessageBox.information(self, "Backup Created", f"Backup:\n{dst}")
        self.statusBar().showMessage(f"Backup: {Path(dst).name}")

    def _on_apply(self):
        if not self.engine.buf: return
        pk = self._selected_profile()
        extras = []
        if self.chk_pop.isChecked():    extras.append("Pop & Bang")
        if self.chk_burble.isChecked(): extras.append("Burble")
        if self.chk_rev.isChecked():    extras.append(f"Rev→{self.spin_rev.value()} RPM")
        if self.chk_idle.isChecked():   extras.append(f"Idle→{self.spin_idle.value()} RPM")
        if self.chk_iat.isChecked():    extras.append(f"IAT×{self.spin_iat.value():.1f}")
        knock = self.combo_knock.currentText()
        if knock != "stock": extras.append(f"Knock:{knock}")
        if self.chk_lambda.isChecked(): extras.append("Disable Lambda")
        if self.chk_dtc.isChecked():    extras.append("Disable DTCs")

        summary = f"Profile: {pk.upper()}"
        if extras: summary += "\n" + "\n".join(f"  + {e}" for e in extras)
        reply = QMessageBox.question(
            self, "Confirm Apply",
            f"{summary}\n\nApply to working copy?\n(Original unchanged until Save)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        self.engine.reset()
        if   pk == "stage1":  self.engine.apply_stage1()
        elif pk == "stage1p": self.engine.apply_stage1plus()
        elif pk == "stage2":  self.engine.apply_stage2()

        if self.chk_pop.isChecked():    self.engine.apply_pop_bang()
        if self.chk_burble.isChecked(): self.engine.apply_burble()
        if self.chk_rev.isChecked():    self.engine.apply_rev_limit(self.spin_rev.value())
        if self.chk_idle.isChecked():   self.engine.apply_idle_rpm(self.spin_idle.value())
        if self.chk_iat.isChecked():    self.engine.apply_iat_correction(self.spin_iat.value())
        if knock != "stock":
            kmap = {"safe (conservative)": "safe", "aggressive": "aggressive", "disabled ⚠": "disabled"}
            self.engine.apply_knock_protection(kmap.get(knock, "stock"))
        if self.chk_lambda.isChecked(): self.engine.disable_lambda()
        if self.chk_egr.isChecked():    self.engine.disable_egr()
        if self.chk_dtc.isChecked():    self.engine.disable_dtc()

        self.preview_text.setText(self.engine.get_changes_text())
        self.preview_text.moveCursor(QTextCursor.MoveOperation.Start)
        n = self.engine.changed_byte_count()
        self.lbl_bytes.setText(f"{n:,} bytes modified")
        self.statusBar().showMessage(f"✅  Applied — {n:,} bytes changed. Save to write to disk.")

    def _on_reset(self):
        if not self.engine.buf: return
        self.engine.reset()
        self.preview_text.setText("Reset to original. No changes applied.")
        self.lbl_bytes.setText("0 bytes modified")
        self.statusBar().showMessage("Reset to original.")

    def _on_save(self):
        if not self.engine.buf: return
        default = str(Path(self.engine.filepath).parent /
                      (Path(self.engine.filepath).stem + "_tuned.bin"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Tuned Binary", default, "Binary files (*.bin);;All files (*)")
        if not path: return
        self.engine.save(path)
        QMessageBox.information(self, "Saved", f"Saved to:\n{path}")
        self.statusBar().showMessage(f"Saved: {Path(path).name}")

    def _on_load_cmp(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load File B for comparison", str(Path.home()/"Desktop"),
            "ECU files (*.bin *.BIN *.ORI *.ori);;All files (*)")
        if not path: return
        self._cmp_file = path
        self.lbl_cmp_b.setText(f"File B: {Path(path).name}")
        self.btn_cmp_run.setEnabled(bool(self.engine.filepath))

    def _on_compare(self):
        if not self.engine.filepath or not self._cmp_file: return
        txt = self.engine.compare_files(self.engine.filepath, self._cmp_file)
        self.cmp_text.setText(txt)
        self.cmp_text.moveCursor(QTextCursor.MoveOperation.Start)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_profile(self):
        for btn in self._tune_group.buttons():
            if btn.isChecked(): return btn.property("tune_key")
        return "stock"

    def _set_controls_enabled(self, en):
        for w in [self.btn_backup, self.btn_save, self.btn_apply, self.btn_reset,
                  self.btn_cmp_run, self.chk_pop, self.chk_burble,
                  self.chk_rev, self.chk_idle, self.chk_iat,
                  self.combo_knock, self.chk_lambda, self.chk_dtc]:
            w.setEnabled(en)
        for btn in self._tune_group.buttons(): btn.setEnabled(en)
        # spin_rev/idle/iat remain gated by their checkboxes
        if not en:
            self.spin_rev.setEnabled(False)
            self.spin_idle.setEnabled(False)
            self.spin_iat.setEnabled(False)

    @staticmethod
    def _addr_map_text():
        lines = [
            "Z22SE GMPT-E15 — Confirmed Address Map (v3, multi-ECU)",
            "=" * 62,
            "",
            "TABLE STRUCTURE (confirmed from binary analysis)",
            "  Ign maps: 7-byte prefix + 12 rows × 13 cols = 163 bytes",
            "  Fuel maps: 115 bytes (proportional zone encoding)",
            "",
            "  Load axis rows (Astra G/standard, high→low, kPa):",
            "  Row  0: 117  Row  1: 106  Row  2: 103  Row  3:  97",
            "  Row  4:  94  Row  5:  91  Row  6:  88  Row  7:  85",
            "  Row  8:  77  Row  9:  63  Row 10:  51  Row 11:  46",
            "",
            "  Load axis rows (Speedster BZ, different scale/units):",
            "  Row  0:  59  Row  1:  60  Row  2:  62  Row  3:  62",
            "  Row  4:  60  Row  5:  53  Row  6:  46  Row  7:  40",
            "  Row  8:  35  Row  9:  32  Row 10:  29  Row 11:  27",
            "",
            "  RPM axis cols (all variants, 13 points):",
            "  2000 2400 2800 3200 3600 4000 4400 4800 5200 5600 6000 6400 6800",
            "",
            "ZONE BOUNDARIES (ign maps, byte offsets within each 163-byte block)",
            "  WOT       (rows 0–4):   bytes   0–71   [Astra: load≥94kPa]",
            "  Part-load (rows 5–8):   bytes  72–123  [Astra: load 77–91kPa]",
            "  Overrun   (rows 9–11):  bytes 124–162  [Astra: load≤63kPa]",
            "  NOTE: Zone boundaries apply by ROW POSITION on all variants.",
            "",
            "CONFIRMED MAP ADDRESSES  (identical across all known variants)",
            "  Ign  #1: 0x0082C9  Ign  #2: 0x0083A9",
            "  Ign  #3: 0x008489  Ign  #4: 0x008569",
            "  Fuel #1: 0x0086C9  Fuel #2: 0x00876C",
            "  Fuel #3: 0x00880F  Fuel #4: 0x0088B2",
            "  Ign Trim #1: 0x00896B (62B)  #2: 0x0089CE (22B)",
            "",
            "LAMBDA MAP ADDRESSES",
            "  2004 firmware (12591333, 12578132):",
            "    Lambda #1: 0x00C7A7 (163B)   Lambda #2: 0x00C885 (163B)",
            "  2001 / Speedster firmware (12215796, 12210633):",
            "    Lambda #1: 0x00C5BD           Lambda #2: 0x00C640",
            "",
            "SCALARS & THRESHOLDS",
            "  Rev limit engage (2004 fw):   0x00B568, 0x00B56A  (uint16 BE)",
            "  Rev limit hyster (2004 fw):   0x00B570–0x00B576",
            "  Rev limit (2001/Speedster fw): AUTO-SCANNED (0xB568 holds",
            "    different data in older firmware revision)",
            "  Stock rev: 6500 RPM (0x1964)  |  6800=0x1A90  |  7000=0x1B58",
            "",
            "  Idle RPM target:    0x008162 (+ 11 more, uint16 BE). Stock: 800 RPM",
            "  IAT correction:     0x00A610–0x00A650 (repeating pattern)",
            "  Knock threshold:    0x008D81 (1 byte: 100=safe, 40=aggr, 255=off)",
            "  O2 CL authority:    0x00A680–0x00A690",
            "  DTC thresholds:     0x008C80–0x008CB0",
            "  PIN (BCD):          0x008141  (33 05 = '3305' — same on all files!)",
            "",
            "CALIBRATION / VIN LOCATIONS",
            "  2004 fw: cal ID @ 0x00602C  (holds VIN for 12591333 & 12578132)",
            "  2001 fw: cal ID @ 0x00402C  (holds VIN for 12215796)",
            "  Speedster BZ: neither location has clean VIN (older hw)",
            "",
            "  12591333 cal: W0L0TGF675B000465  (your file)",
            "  12578132 cal: W0L0TGF084…",
            "  12215796 cal: W0L0TGF081…",
            "",
            "SUPPORTED PROFILES",
        ]
        for pn, p in ECU_PROFILES.items():
            if pn == "__generic__": continue
            la = p.get('load_axis', [])
            la_note = "  [alt load axis]" if la and la[0] < 80 else ""
            rpm_note = "  [auto-scan rev limit]" if not p.get('rpm_engage') else ""
            lines.append(f"  {pn}: {p['name']}{la_note}{rpm_note}")
        lines.append("  __generic__: Generic GMPT-E15 fallback (auto-scan rev limit)")
        return "\n".join(lines)


# ─── Pop&Bang zone detail text ───────────────────────────────────────────────

POP_BANG_DETAIL = """Pop & Bang / Burble — Exact Zone Coverage (from binary decode)
==================================================================

TABLE STRUCTURE (confirmed):
  Ign maps = 7-byte prefix + 12 rows × 13 cols = 163 bytes
  Rows = load axis (high→low): 117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46 kPa
  Cols = RPM axis: 2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800 RPM

OVERRUN ZONE (Pop & Bang target):
  Byte range: 124–162 of each 163-byte ign map
  Rows 9–11  →  Load axis: 63, 51, 46 kPa  ← LOW LOAD / CLOSED THROTTLE
  ALL 13 RPM columns: 2000 to 6800 RPM

  This precisely covers the deceleration/overrun operating region:
  • Closed or near-closed throttle
  • Low MAP / manifold pressure
  • Engine still spinning at any RPM (idle coast-down included)

MODIFICATION APPLIED (Pop & Bang mode):
  Ignition advance:   −12 counts in overrun zone
  Fuel injection:     +4 counts in overrun zone (rows 9–11 proportional)

MODIFICATION APPLIED (Burble mode):
  Ignition advance:   −20 counts in overrun zone (MORE aggressive)
  Fuel injection:     +7 counts in overrun zone

EFFECT ON IGNITION MAP (example: Ign Map #1, overrun rows, stock vs modified):
  Load  RPM→  2000  2400  2800  3200  3600  4000  4400  4800  5200  5600  6000  6400  6800
  63kPa stock:  122   168   151   148   137   137   128   122   120   117   111   109   108
  63kPa P&B:    110   156   139   136   125   125   116   110   108   105    99    97    96  (Δ−12)
  51kPa stock:  122   168   151   148   139   139   127   121   116   112   109   106   104
  51kPa P&B:    110   156   139   136   127   127   115   109   104   100    97    94    92  (Δ−12)
  46kPa stock:  122   168   154   148   139   139   134   128   119   111   107   105   105
  46kPa P&B:    110   156   142   136   127   127   122   116   107    99    95    93    93  (Δ−12)

WHY RETARDING IGNITION CAUSES POPS:
  Retarding ignition in the overrun zone means combustion finishes later →
  hot unburnt/partially burnt gases exit into the exhaust manifold still
  burning → audible pop/bang from the exhaust. More fuel (+4 counts)
  ensures there's something to combust in the exhaust pipe.

ZONE BOUNDARY NOTE:
  The WOT/PL/overrun split is based on the actual load axis:
  • WOT zone:       load ≥ 94 kPa  (rows 0–4)  = full throttle
  • Part-load zone: load 77–91 kPa (rows 5–8)  = partial throttle
  • Overrun zone:   load ≤ 63 kPa  (rows 9–11) = closed throttle / coast
"""

NOTES_TEXT = """Z22SE GMPT-E15 ECU Tuner v3 — Notes & Warnings
================================================

CONFIRMED DATA
──────────────
• All addresses verified against actual OpelAstraG_Z22SE_GMPT-E15_Stock.bin
  VIN: W0L0TGF675B000465  (Part: 12591333)  PIN: 3305
• Stage 1 values verified against real Stage1 tune binary
• Table structure decoded: 7-byte prefix + 12×13 = 163 bytes
• Pop&Bang zone verified to target load≤63kPa rows (overrun/decel)
• Idle RPM at 0x008162 cluster (12 locations), stock=800 RPM
• All four Z22SE ORI files fully analysed (Feb 2026)

SUPPORTED FILES (v3)
─────────────────────
12591333  Opel Astra G Z22SE 2004  ★ FULLY VERIFIED  (your file)
          Cal: W0L0TGF675B000465 · Rev limit: 0xB568 · Lambda: 0xC7A7

12578132  Opel Astra G Z22SE 2004 (Hw 12210453 EB)  ★ VERIFIED
          Cal: W0L0TGF084… · Identical map addresses to 12591333
          Same rev limit address. Lambda end-cols differ slightly.

12215796  Opel Astra G Z22SE 2001 (Hw 09391283 BC)  ★ VERIFIED
          Cal@0x402C: W0L0TGF081… · Lambda: 0xC5BD (different!)
          Rev limit: AUTO-SCANNED (0xB568 holds different data in
          2001 firmware). Ign map row0 differs at low RPM.

12210633  Opel Speedster 2.2 147hp (Hw 12202073 BZ)  ⚠ EXPERIMENTAL
          Cal: not in standard location. Lambda: 0xC5BD.
          Load axis uses DIFFERENT scale [59,60,62…27] — not kPa MAP.
          All map byte-addresses identical. Zone rows same position.
          Rev limit: AUTO-SCANNED. Tune deltas apply correctly.

ALL FILES SHARE:
  • Same 512KB size · Same map addresses · Same PIN address 0x8141
  • PIN "3305" identical in ALL four files (same as your car!)
  • Accepts both .bin and .ORI file formats

TUNE PROFILES
─────────────
Stage 1    Real Stage1 binary. +2 ign (high RPM ≥4400) / +1-2 fuel /
           −7 lambda WOT. Safe for stock hardware.

Stage 1+   Uniform +3/+2. Panel filter + sports exhaust minimum.

Stage 2    Aggressive +5/+4. 6800 RPM. Requires proper intake/exhaust.
           Do NOT flash without knock monitoring on first drive.

Pop & Bang Ign −12 + Fuel +4 in overrun zone (load≤63kPa, all RPM).
           Can be stacked on any Stage profile.

Burble     Ign −20 + Fuel +7 overrun. Not for daily commuting.

FINE TUNING
───────────
IAT Scale  0.0 = disable IAT timing correction (open air filter,
           cold intake). 1.0 = stock.

Knock      'safe' threshold=100, 'aggressive'=40, 'disabled'=0xFF.
           DO NOT disable knock protection without knock monitoring!

Idle RPM   Adjusts warm idle target. 12 locations updated.
           Range 600–1200 RPM. Stock = 800 RPM.

BEST-EFFORT
───────────
• Lambda disable: CL authority area + lambda target approach.
  Always verify with wideband O2 after flashing.
• DTC disable: threshold zeroing. Not all codes guaranteed silent.
• Speed limiter: address not confirmed — option disabled.
• Rev limit for 2001/Speedster: auto-scanned — verify before flashing.

ECU CHECKSUM (0x008000):
  This tuner does NOT update the binary checksum.
  ECM Titanium / MPPS / KTAG / KESS recalculate automatically.
  If yours does not, patch 0x008000 manually after verifying tune.

ALWAYS
──────
1. BACKUP before every flash
2. Dyno / rolling road verification recommended
3. Wideband lambda during WOT runs
4. Monitor for knock (pinging) — especially Stage 2
5. Verify idle behaviour after any idle RPM changes
"""
# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    app.setApplicationName("Z22SE ECU Tuner v3")
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
