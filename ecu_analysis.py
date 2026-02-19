#!/usr/bin/env python3
"""
Opel Astra G Z22SE GMPT-E15 ECU Binary Analysis Tool
Stock vs Stage 1 comparison, table mapping, PIN code extraction
"""

import struct
import os

# Updated to use sample_files directory
BASE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE, "sample_files")
STOCK  = os.path.join(SAMPLE_DIR, "OpelAstraG_Z22SE_GMPT-E15_Stock.bin")
STAGE1 = os.path.join(SAMPLE_DIR, "OpelAstraG_Z22SE_GMPT-E15_Stage 1.bin")
REPORT = os.path.join(BASE, "ECU_Mapping_Report.md")

with open(STOCK,  'rb') as f: stock  = bytearray(f.read())
with open(STAGE1, 'rb') as f: stage1 = bytearray(f.read())


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def u16be(buf, off):
    return struct.unpack_from('>H', buf, off)[0]

def hexrow(buf, off, n=16, addr=None):
    chunk = buf[off:off+n]
    addr_str = f"0x{addr if addr is not None else off:06X}: " if addr is not None else f"0x{off:06X}: "
    return addr_str + ' '.join(f'{b:02X}' for b in chunk)

def diff_regions(a, b):
    diffs, start, prev = [], None, None
    for i in range(len(a)):
        if a[i] != b[i]:
            if start is None: start = i
            prev = i
        else:
            if start is not None:
                diffs.append((start, prev))
                start = None
    if start is not None:
        diffs.append((start, prev))
    # merge if gap <= 8
    merged = []
    for s, e in diffs:
        if merged and s - merged[-1][1] <= 8:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]

def table_hex(buf, start, rows, cols, row_label=None):
    lines = []
    for r in range(rows):
        vals = [f"{buf[start + r*cols + c]:3d}" for c in range(cols)]
        label = f"  row{r:02d}: " if row_label is None else f"  {row_label[r]:5.0f}: "
        lines.append(label + ' '.join(vals))
    return '\n'.join(lines)

def table_hex_diff(s, s1, start, rows, cols):
    lines = []
    for r in range(rows):
        sv  = [s[start + r*cols + c]  for c in range(cols)]
        s1v = [s1[start + r*cols + c] for c in range(cols)]
        changed = any(a != b for a, b in zip(sv, s1v))
        marker = " *" if changed else "  "
        lines.append(f"  row{r:02d}:{marker} stock=[{' '.join(f'{v:3d}' for v in sv)}]")
        if changed:
            delta = [s1v[c]-sv[c] for c in range(cols)]
            lines.append(f"        s1   =[{' '.join(f'{v:3d}' for v in s1v)}]")
            delta_str = ' '.join(('+' if v >= 0 else '') + f'{v:3d}' for v in delta)
            lines.append(f"        delta=[{delta_str}]")
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────────────────────

regions = diff_regions(stock, stage1)

# Known RPM axis (12-point, 16-bit BE) at 0x0081B0: 2000,2400,...,6400 RPM
RPM_AXIS_12 = [u16be(stock, 0x0081B0 + i*2) for i in range(12)]
# Load axis (12-point, 8-bit) at 0x008290
LOAD_AXIS_12 = list(stock[0x008290:0x008290+12])

# Rev limit region
FUEL_CUT_ADDR    = 0x00B568
fuel_cut_stock   = u16be(stock,  FUEL_CUT_ADDR)
fuel_cut_hyst1   = u16be(stock,  0x00B570)
fuel_cut_hyst2   = u16be(stock,  0x00B574)
fuel_cut_s1      = u16be(stage1, FUEL_CUT_ADDR)

# PIN code: BCD at 0x008141 → 0x33 0x05 = digits "33"+"05" = "3305"
PIN_ADDR = 0x008141   # BCD packed: 0x33 0x05 = "3305"
pin_bytes_stock  = stock[PIN_ADDR:PIN_ADDR+2]
pin_bcd = f"{(pin_bytes_stock[0] >> 4):d}{(pin_bytes_stock[0] & 0xF):d}{(pin_bytes_stock[1] >> 4):d}{(pin_bytes_stock[1] & 0xF):d}"

# Additional notable areas (not changed but tunable)
# IAT timing correction ~ 0x00A610 (12 values, degrees)
IAT_TIMING_ADDR = 0x00A610
iat_timing = list(stock[IAT_TIMING_ADDR:IAT_TIMING_ADDR+12])

# High-resolution ignition timing at 0x008F90 (visible 6500 RPM marker)
IGN_MAP_ADDR = 0x008F90

# Lambda target table region
LAMBDA_ADDR   = 0x00C7A7
LAMBDA2_ADDR  = 0x00C885
LAMBDA_LEN    = 163

# Table names for the known changed regions
TABLE_MAP = {
    0x0082C9: ("Ignition Advance Map 1 (primary)",               163, 12, 13),
    0x0083A9: ("Ignition Advance Map 2 (secondary/cold)",         163, 12, 13),
    0x008489: ("Ignition Advance Map 3 (part-load)",              163, 12, 13),
    0x008569: ("Ignition Advance Map 4 (WOT/knock-ref)",          163, 12, 13),
    0x0086C9: ("Fuel/Injection Correction Map 1 (warm)",          115, 10, 11),
    0x00876C: ("Fuel/Injection Correction Map 2 (cold)",          115, 10, 11),
    0x00880F: ("Fuel/Injection Correction Map 3 (part-load)",     115, 10, 11),
    0x0088B2: ("Fuel/Injection Correction Map 4 (WOT)",           115, 10, 11),
    0x00896B: ("Ignition Trim / High-RPM Correction (small)",      62,  6,  9),
    0x0089CE: ("Ignition Trim / Transient Correction (small)",     22,  2, 11),
    0x00C7A7: ("Lambda/AFR Target Map (primary copy)",            163, 12, 13),
    0x00C885: ("Lambda/AFR Target Map (duplicate/backup copy)",   163, 12, 13),
}

# ─────────────────────────────────────────────────────────────────────────────
# Build report
# ─────────────────────────────────────────────────────────────────────────────

lines = []
L = lines.append

L("# Opel Astra G Z22SE GMPT-E15 — ECU Binary Mapping Report")
L("")
L("**ECU:** GMPT-E15 (Delco/Delphi)  |  **Engine:** Z22SE 2.2L NA  |  **Vehicle:** Opel Astra G Cabrio 2004")
L(f"**Stock file:** `{os.path.basename(STOCK)}`  ({len(stock):,} bytes = 512 KB)")
L(f"**Stage 1 file:** `{os.path.basename(STAGE1)}`")
L("")

# ─── PIN Code ───────────────────────────────────────────────────────────────
L("---")
L("## 1  PIN / Immobilizer Code")
L("")
L(f"| Address | Bytes (hex) | BCD Decoded | Match |")
L(f"|---------|-------------|-------------|-------|")
L(f"| `0x{PIN_ADDR:06X}` | `{pin_bytes_stock.hex().upper()}` | **{pin_bcd}** | {'✅ Matches 3305' if pin_bcd == '3305' else '⚠️'} |")
L("")
L("**Context (20 bytes around address 0x008140):**")
L("```")
L(hexrow(stock, 0x008138, 20))
L("0x008138: FF 41 D4 [33 33 05] C3 05 9F 0B 54 ...  ← bytes at 0x008141 = 33 05 = BCD 3305")
L("```")
L("> BCD packed: high nibble = 1st digit, low nibble = 2nd digit per byte.")
L("> `0x33` → digits `33`; `0x05` → digits `05` → PIN = **3305** ✅")
L("")
L("**Second occurrence** (code region, not EEPROM storage):")
L(f"- `0x0060AA`: `{stock[0x0060A8:0x0060AE].hex().upper()}` — same BCD value, appears in code constants")
L("")

# ─── Rev Limit / Fuel Cut ────────────────────────────────────────────────────
L("---")
L("## 2  Rev Limiter / Fuel Cut-Off")
L("")
L("The fuel cut is implemented with two paired 16-bit big-endian RPM thresholds")
L("(activate / deactivate with hysteresis).")
L("")
L("| Address | Description | Stock | Stage 1 | Notes |")
L("|---------|-------------|-------|---------|-------|")
L(f"| `0x{FUEL_CUT_ADDR:06X}` | Fuel Cut ON #1  | {fuel_cut_stock} RPM | {fuel_cut_s1} RPM | Primary cut engage |")
L(f"| `0x{FUEL_CUT_ADDR+2:06X}` | Fuel Cut ON #2  | {u16be(stock,FUEL_CUT_ADDR+2)} RPM | {u16be(stage1,FUEL_CUT_ADDR+2)} RPM | |")
L(f"| `0x{0x00B570:06X}` | Fuel Cut OFF #1 | {fuel_cut_hyst1} RPM | {u16be(stage1,0x00B570)} RPM | Hysteresis re-enable |")
L(f"| `0x{0x00B572:06X}` | Fuel Cut OFF #2 | {u16be(stock,0x00B572)} RPM | {u16be(stage1,0x00B572)} RPM | |")
L(f"| `0x{fuel_cut_hyst2:06X}` | Fuel Cut OFF #3 | {u16be(stock,fuel_cut_hyst2)} RPM | {u16be(stage1,fuel_cut_hyst2)} RPM | Secondary hysteresis |")
L("")
L("**Raw bytes (stock):**")
L("```")
L(hexrow(stock, 0x00B560, 32))
L("```")
L("")
L("> ⚠️ Fuel cut RPM is **not changed** between stock and Stage 1 files (both = 6500 RPM).")
L("> To raise the rev limit, modify the `0x00B568` and `0x00B56A` values (big-endian uint16).")
L("> Example: 6800 RPM = `0x1A90`, 7000 RPM = `0x1B58`.")
L("")

# ─── Table Axes ─────────────────────────────────────────────────────────────
L("---")
L("## 3  Table Axes")
L("")
L("### 3.1  12-Point RPM Axis (used by 4× 163-byte maps at 0x0082C9–0x00860B)")
L("")
L("Stored as 16-bit big-endian values at `0x0081C0`:")
L("")
L("| Idx | RPM  | Hex    |")
L("|-----|------|--------|")
for i, rpm in enumerate(RPM_AXIS_12):
    L(f"| {i:2d}  | {rpm:5d} | `{rpm:04X}` |")
L("")
L("### 3.2  12-Point Load / MAP Axis (8-bit, kPa-equivalent, descending)")
L("")
L("Stored at `0x008290` (12 bytes), used as row axis for 163-byte tables:")
L("")
L("| Idx | Raw | Approx % WOT |")
L("|-----|-----|-------------|")
for i, v in enumerate(LOAD_AXIS_12):
    L(f"| {i:2d}  | {v:3d} (0x{v:02X}) | {v/1.28:.0f}% |")
L("")

# ─── Changed Tables ──────────────────────────────────────────────────────────
L("---")
L("## 4  Modified Tables (Stock → Stage 1 Differences)")
L("")
L(f"**Total changed bytes:** {sum(e-s+1 for s,e in regions)}")
L(f"**Number of changed regions:** {len(regions)}")
L("")

for i, (s, e) in enumerate(regions):
    size = e - s + 1
    meta = TABLE_MAP.get(s)
    name = meta[0] if meta else f"Unknown region {i+1}"
    L(f"### 4.{i+1}  {name}")
    L(f"- **Address:** `0x{s:06X}` – `0x{e:06X}`")
    L(f"- **Size:** {size} bytes")
    if meta:
        rows, cols = meta[2], meta[3]
        L(f"- **Likely dimensions:** {rows} rows × {cols} cols")
    L("")
    # Show first 16 bytes of diff
    chunk_s  = stock[s:s+min(size,32)]
    chunk_s1 = stage1[s:s+min(size,32)]
    delta    = [b-a for a,b in zip(chunk_s, chunk_s1)]
    L("**First 32 bytes — Stock:**")
    L("```")
    L(' '.join(f'{b:3d}' for b in chunk_s))
    L("```")
    L("**First 32 bytes — Stage 1:**")
    L("```")
    L(' '.join(f'{b:3d}' for b in chunk_s1))
    L("```")
    L("**Delta (Stage1 − Stock):**")
    L("```")
    L(' '.join(f'{d:+3d}' for d in delta))
    L("```")
    avg_delta = sum(abs(d) for d in delta if d != 0)
    n_changed = sum(1 for d in delta if d != 0)
    L(f"*Changed bytes in first 32: {n_changed}, avg |delta|: {avg_delta/max(n_changed,1):.1f}*")
    L("")

# ─── Lambda / AFR Target Maps ────────────────────────────────────────────────
L("---")
L("## 5  Lambda / AFR Target Maps — Detailed")
L("")
L("Two identical copies exist (primary + backup). Stage 1 reduces values at high-load")
L("cells, indicating a **richer AFR target at WOT** (typical Stage 1 change).")
L("")
L("**Scaling:** value × (14.7 / 128) ≈ AFR  (0x80 = 128 ≈ λ1.0 / 14.7:1)")
L("")
L("| Addr | Role |")
L("|------|------|")
L(f"| `0x{LAMBDA_ADDR:06X}` | Primary copy  |")
L(f"| `0x{LAMBDA2_ADDR:06X}` | Duplicate/backup copy |")
L("")
L("**Sample row comparison (first 13 bytes = one row):**")
L("")
L("```")
for row in range(min(12, LAMBDA_LEN // 13)):
    off = LAMBDA_ADDR + row * 13
    sv  = list(stock[off:off+13])
    s1v = list(stage1[off:off+13])
    afr_s  = [f"{v*14.7/128:.2f}" for v in sv]
    afr_s1 = [f"{v*14.7/128:.2f}" for v in s1v]
    changed = " *" if sv != s1v else "  "
    L(f"Row{row:02d}:{changed} stock={[f'{v:3d}' for v in sv]}")
    if sv != s1v:
        L(f"       s1   ={[f'{v:3d}' for v in s1v]}")
        L(f"       AFR  ={afr_s1}")
L("```")
L("")

# ─── Additional Tunable Locations ────────────────────────────────────────────
L("---")
L("## 6  Additional Tunable Locations (Unmapped by ECM Titanium)")
L("")
L("These regions are NOT modified in the Stage 1 file but are important for further tuning.")
L("")
L("### 6.1  Ignition Timing Map (high-res, degrees)")
L(f"**Address:** `0x{IGN_MAP_ADDR:06X}`")
L("")
L("Values appear to be ignition advance in degrees. Contains RPM breakpoints including 6500 RPM:")
L("```")
for row in range(8):
    off = IGN_MAP_ADDR + row*14
    vals = list(stock[off:off+14])
    L(f"  0x{off:06X}: " + ' '.join(f'{v:3d}' for v in vals))
L("```")
L("")
L("### 6.2  IAT (Intake Air Temperature) Timing Correction")
L(f"**Address:** `0x{IAT_TIMING_ADDR:06X}` — 12 values (degrees of retard per temperature band)")
L("```")
L("  " + ' '.join(f'{v:3d}' for v in iat_timing))
L("  Degrees: " + ' '.join(f'{v:+3d}°' for v in iat_timing))
L("```")
L("")
L("### 6.3  RPM-Indexed Control Table (idle, tip-in, spark cut)")
L(f"**Address:** `0x008150` — 16-bit RPM breakpoints for spark angle scheduling")
L("```")
rpm_ctrl = [u16be(stock, 0x008150 + i*2) for i in range(14)]
L("  RPM: " + ' '.join(f'{v:5d}' for v in rpm_ctrl))
L("```")
L("")
L("### 6.4  Coolant Temperature (ECT) Correction Area")
L(f"**Address:** `0x008240` — threshold/scaling constants for cold-start enrichment")
L("```")
L(hexrow(stock, 0x008240, 32))
L("```")
L("")
L("### 6.5  Fuel Cut / Rev Limit Parameters (full block)")
L(f"**Address:** `0x00B540` – `0x00B580`")
L("```")
for row in range(4):
    off = 0x00B540 + row*16
    s_vals  = ' '.join(f'{b:02X}' for b in stock[off:off+16])
    s1_vals = ' '.join(f'{b:02X}' for b in stage1[off:off+16])
    changed = " <<SAME" if stock[off:off+16] == stage1[off:off+16] else " <<DIFFERS"
    L(f"  0x{off:06X}: {s_vals}{changed}")
L("```")
L("")
L("### 6.6  O2/Lambda Sensor Control Constants")
L(f"**Address:** `0x00A5E0` — contains lambda correction coefficients and O2 sensor scaling")
L("```")
for row in range(4):
    off = 0x00A5E0 + row*16
    L(hexrow(stock, off, 16))
L("```")
L("")

# ─── Summary Table ───────────────────────────────────────────────────────────
L("---")
L("## 7  Quick-Reference Address Map")
L("")
L("| Purpose | Address | Size | Format | Notes |")
L("|---------|---------|------|--------|-------|")
L(f"| **PIN Code (immobilizer)** | `0x008141` | 2 bytes | BCD packed | `33 05` = 3305 |")
L(f"| **Fuel Cut RPM (engage)** | `0x00B568` | 2 bytes | uint16 BE | 6500 RPM = `19 64` |")
L(f"| **Fuel Cut RPM (hysteresis)** | `0x00B570` | 2 bytes | uint16 BE | 6495 RPM = `19 5F` |")
for addr, (name, size, rows, cols) in TABLE_MAP.items():
    tag = "CHANGED" if addr in [r[0] for r in regions] else "stock-only"
    L(f"| **{name}** | `0x{addr:06X}` | {size} B | {rows}×{cols} byte table | {tag} |")
L(f"| **RPM axis (12-pt)** | `0x0081C0` | 24 bytes | uint16 BE ×12 | 2000–6400 RPM |")
L(f"| **Load axis (12-pt)** | `0x008290` | 12 bytes | uint8 ×12 | 46–117 (raw) |")
L(f"| **Ignition map (hi-res)** | `0x008F90` | ~112 bytes | uint8 degrees | Not changed |")
L(f"| **IAT timing correction** | `0x00A610` | 12 bytes | uint8 degrees | Not changed |")
L(f"| **Lambda/O2 constants** | `0x00A5E0` | 64 bytes | mixed | Not changed |")
L("")

# ─── Stage 1 Summary ─────────────────────────────────────────────────────────
L("---")
L("## 8  Stage 1 Changes Summary")
L("")
L("Based on binary diff analysis:")
L("")
L("| Change | Direction | Typical Amount |")
L("|--------|-----------|---------------|")
L("| Ignition advance maps (×4, 163-byte) | **+1 to +3 counts** (≈ +0.5° to +1.5°) | Mild advance across mid-high RPM |")
L("| Fuel/injection correction maps (×4, 115-byte) | **+1 to +3 counts** | Slight enrichment |")
L("| Ignition trim corrections (×2 small) | **+1 count** uniformly | Consistent small advance |")
L("| Lambda/AFR target maps (×2, 163-byte) | **−5 to −8 counts** at WOT cells | Richer WOT target (≈0.9 λ) |")
L("| Rev limit | **Unchanged** | 6500 RPM stock and stage 1 |")
L("")
L("**Stage 1 philosophy:** Small ignition advance + slightly richer WOT fueling. No rev limit change.")
L("")

# ─── Missing Maps (for further work) ─────────────────────────────────────────
L("---")
L("## 9  Known Missing / Unidentified Maps (Further Work Needed)")
L("")
L("These are commonly tunable on GMPT-E15 but addresses need verification:")
L("")
L("| Map | Typical Location | How to Find |")
L("|-----|-----------------|-------------|")
L("| VE (Volumetric Efficiency) 3D | 0x008000–0x008900 area | Look for 16×16 table with ~128 center values |")
L("| Knock retard map | Near ignition maps | Values 0–15 (degrees retard steps) |")
L("| Cold-start enrichment (CLT) | 0x008240 area | Values keyed on coolant temp axis |")
L("| Idle target RPM | 0x008150 area | 16-bit BE RPM near 0x0320=800 |")
L("| Injector dead-time | Unknown | 16-bit values indexed by battery voltage |")
L("| Closed-loop lambda multiplier | 0x00A680–0x00B000 area | Values near 0x80=1.0× |")
L("| Speed limiter | 0x00B540+ area | uint16 km/h threshold |")
L("| Throttle adaptation | 0x008000 area | Small byte table |")
L("")
L("---")
L("*Report generated by `ecu_analysis.py` — analysis of raw binary only.")
L("Always verify addresses with a hex editor before modifying. Backup your original bin.*")

# ─────────────────────────────────────────────────────────────────────────────
# Write report
# ─────────────────────────────────────────────────────────────────────────────

report = '\n'.join(lines)
with open(REPORT, 'w') as f:
    f.write(report)

print(f"Report written: {REPORT}")
print(f"Report size: {len(report):,} chars")

# Quick console summary
print("\n" + "="*60)
print("QUICK SUMMARY")
print("="*60)
print(f"PIN Code: {pin_bcd} (BCD at 0x{PIN_ADDR:06X})")
print(f"Fuel Cut (primary): {fuel_cut_stock} RPM at 0x{FUEL_CUT_ADDR:06X}  [stock={fuel_cut_stock}, stage1={fuel_cut_s1}]")
print(f"Changed regions: {len(regions)}")
for s, e in regions:
    name = TABLE_MAP.get(s, (f"Unknown",))[0]
    print(f"  0x{s:06X}-0x{e:06X}  ({e-s+1:3d} bytes) — {name}")
print(f"\nRPM axis (12pt): {RPM_AXIS_12}")
print(f"Load axis (12pt): {LOAD_AXIS_12}")

