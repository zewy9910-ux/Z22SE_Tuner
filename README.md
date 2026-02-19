# Z22SE ECU Tuner

<div align="center">

**Professional ECU Calibration Tool for Opel/Vauxhall Z22SE Engines**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ECU](https://img.shields.io/badge/ECU-GMPT--E15-green.svg)]()
[![Engine](https://img.shields.io/badge/engine-Z22SE%202.2L-orange.svg)]()

*An advanced PyQt6-based GUI application for analyzing, modifying, and tuning GMPT-E15 ECU binary files*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Supported Vehicles](#-supported-vehicles)
- [ECU Information](#-ecu-information)
- [Installation](#-installation)
- [Usage](#-usage)
- [Tuning Profiles](#-tuning-profiles)
- [ECU Memory Mapping](#-ecu-memory-mapping)
- [Safety & Disclaimers](#-safety--disclaimers)
- [Technical Documentation](#-technical-documentation)
- [Contributing](#-contributing)
- [License](#-license)

> 📖 **Quick Reference**: See [QUICKREF.md](QUICKREF.md) for a concise cheat sheet with tables, addresses, and troubleshooting tips.

---

## 🎯 Overview

Z22SE_Tuner is a comprehensive ECU tuning solution designed specifically for the Opel/Vauxhall Z22SE 2.2L naturally aspirated engine equipped with the GMPT-E15 (Delco/Delphi) engine control unit. This tool provides a user-friendly graphical interface for:

- **Binary Analysis**: Compare stock and modified ECU files
- **Map Editing**: Modify ignition timing, fuel, and lambda (AFR) tables
- **Pre-built Profiles**: Apply proven Stage 1, Stage 1+, and Stage 2 tunes
- **Custom Features**: Pop & Bang, burble effects, rev limiter adjustment
- **Safety**: Automatic backups, change tracking, and validation

**Key Advantages:**
- ✅ No expensive tuning software required
- ✅ Based on verified binary analysis of real Stage 1 tunes
- ✅ Full transparency - see exactly what changes are made
- ✅ Cross-platform (Windows, Linux, macOS)
- ✅ Open source and customizable

---

## ⭐ Features

### Core Functionality
- 📂 **File Management**: Load, analyze, and save ECU binary files (512 KB .bin files)
- 🔍 **ECU Detection**: Automatic identification of part number, calibration ID, and PIN code
- 📊 **Binary Comparison**: Visual diff showing changed bytes between stock and modified files
- 💾 **Automatic Backups**: Timestamped backups created before any modifications
- 📝 **Change Log**: Real-time tracking of all applied modifications

### Tuning Capabilities
- 🎚️ **Ignition Timing**: Modify advance across 4 maps (primary, cold-start, part-load, WOT)
- ⛽ **Fuel Maps**: Adjust fuel/injection correction across 4 maps (warm, cold, part-load, WOT)
- 🌬️ **Lambda/AFR Targets**: Rich/lean fuel mixture adjustments (2 synchronized maps)
- 🔄 **Ignition Trims**: Fine-tuning of high-RPM and transient corrections
- 🚀 **Rev Limiter**: Configurable RPM limit (stock: 6500 RPM, tested up to 7000 RPM)
- 💥 **Pop & Bang**: Overrun burble/crackle effects (ignition retard + fuel enrichment)

### Built-in Tuning Profiles
1. **Stage 1**: Conservative tune (+15-20 HP est.) based on binary-verified tuning file
2. **Stage 1+**: Moderate tune with enhanced mid-range response
3. **Stage 2**: Aggressive tune (+25-30 HP est.) with raised rev limit to 6800 RPM
4. **Pop & Bang**: Overrun entertainment effects (works with any stage)

### Advanced Options
- 🔓 **Lambda Closed-Loop Disable**: Forces open-loop mode (for dyno/testing)
- ⚠️ **DTC Disable**: Best-effort disabling of diagnostic trouble codes
- 🔢 **PIN Code Display**: Extract immobilizer PIN code from binary

---

## 🚗 Supported Vehicles

This tuner is designed for Opel/Vauxhall vehicles equipped with the **Z22SE 2.2L 16V naturally aspirated engine** and **GMPT-E15 ECU** (2000-2005):

| Model | Years | Notes |
|-------|-------|-------|
| **Opel Astra G** | 2000-2005 | Saloon, Estate, Cabrio, Coupe |
| **Vauxhall Astra Mk4** | 2000-2005 | UK-market equivalent |
| **Opel Zafira A** | 2000-2005 | 7-seater MPV |
| **Vauxhall Zafira A** | 2000-2005 | UK-market equivalent |

### Known ECU Variants
- **Part Number**: 12591333 (2004 calibration - primary support)
- **Part Number**: 12215796 (2001 calibration - compatible)
- **Calibration IDs**: W0L0TGF675B000465, W0L0TGF071B022321
- **ECU Type**: GMPT-E15 (Delco/Delphi)
- **File Size**: 512 KB (524,288 bytes)

⚠️ **Important**: Always verify your ECU part number before flashing. Incompatible files can prevent engine start.

---

## 🔧 ECU Information

### Z22SE Engine Specifications
- **Displacement**: 2.2L (2198cc)
- **Configuration**: Inline-4, 16-valve DOHC
- **Aspiration**: Naturally aspirated
- **Stock Power**: 108 kW (147 HP) @ 5600 RPM
- **Stock Torque**: 203 Nm (150 lb-ft) @ 4000 RPM
- **Compression**: 10.0:1
- **Fuel System**: Sequential multi-port injection

### GMPT-E15 ECU Platform
- **Manufacturer**: Delco/Delphi
- **Architecture**: Motorola MPC5xx series (PowerPC-based)
- **Flash Memory**: 512 KB calibration area
- **Communication**: OBD-II / ISO 9141 K-line
- **Programmable via**: BDM, K-line (with compatible tools)

### Tuning Potential
| Modification | Expected Gain | Notes |
|--------------|---------------|-------|
| Stage 1 (software only) | +15-20 HP / +15 Nm | Safe on stock hardware |
| Stage 1+ (software only) | +20-25 HP / +20 Nm | Recommended with premium fuel (98 RON+) |
| Stage 2 (software + rev limit) | +25-30 HP / +25 Nm | Requires free-flowing exhaust |
| With cold air intake | +5-8 HP additional | Helps engine breathe |
| With performance exhaust | +8-12 HP additional | Reduces backpressure |

---

## 📦 Installation

### Prerequisites
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, Linux (Ubuntu 20.04+), or macOS 10.15+
- **Dependencies**: PyQt6 (automatically installed)

### Installation Steps

1. **Clone the repository**:
```bash
git clone https://github.com/zewy9910-ux/Z22SE_Tuner.git
cd Z22SE_Tuner
```

2. **Install Python dependencies**:
```bash
pip install PyQt6
```

3. **Run the application**:
```bash
python Z22SE_Tuner.py
```

### Optional: Create Desktop Shortcut

**Windows:**
```bash
pythonw Z22SE_Tuner.py
```

**Linux:**
```bash
chmod +x Z22SE_Tuner.py
./Z22SE_Tuner.py
```

---

## 🎮 Usage

### Quick Start Guide

1. **Load Your ECU File**
   - Click "Load ECU File" and select your stock .bin file
   - The tool will verify file size (must be 512 KB) and detect ECU information
   - Review the detected Part Number, Calibration ID, PIN code, and current rev limit

2. **Choose a Tuning Profile**
   - Select from Stage 1, Stage 1+, or Stage 2 radio buttons
   - Optionally enable "Pop & Bang" for overrun effects
   - Optionally adjust rev limiter (e.g., 6800 RPM for Stage 2)

3. **Apply Modifications**
   - Click "Apply Selected Tune"
   - Review the change log showing all modifications
   - The status bar will display the number of changed bytes

4. **Save Modified File**
   - Click "Save As..." to export your tuned file
   - A timestamped backup of the original is created automatically
   - Flash the new file to your ECU using your preferred tool

5. **Reset if Needed**
   - Click "Reset to Original" to undo all changes
   - You can re-apply different settings without reloading the file

### Advanced Usage

**Binary Analysis Mode:**
- Use `ecu_analysis.py` to compare stock vs. tuned files
- Generates a detailed markdown report (`ECU_Mapping_Report.md`)
- Shows table-by-table differences, addresses, and scaling factors

```bash
python ecu_analysis.py
```

**Custom Modifications:**
- Edit `Z22SE_Tuner.py` to create your own tuning profiles
- All map addresses are documented in the ECU_MEMORY_MAP section
- Use the `_delta_block()` method to modify specific table regions

---

## 🚀 Tuning Profiles

### Stage 1 (Verified)
**Description**: Conservative tune based on binary-verified commercial Stage 1 file

**Modifications**:
- Ignition timing: +1-2° advance at WOT, +1° at part-load
- Fuel correction: +2 counts enrichment (WOT), +1 count (part-load)
- Lambda targets: -5 to -8 counts richer at WOT (≈14.5:1 to 13.5:1 AFR)
- Ignition trims: +1 count uniform advance
- Rev limit: **Unchanged** (6500 RPM)

**Expected Results**:
- Power: +15-20 HP / +12-15 Nm
- Fuel economy: -5% (premium fuel recommended)
- Hardware: Stock components OK
- Risk: **Low** (tested and verified)

---

### Stage 1+
**Description**: Moderate uniform advance with enhanced mid-range response

**Modifications**:
- Ignition timing: +3° advance at WOT, +2° at part-load
- Fuel correction: +3 counts (WOT), +2 counts (part-load)
- Lambda targets: -9 counts (WOT), -3 counts (part-load)
- Ignition trims: +1 count uniform
- Rev limit: **Unchanged** (6500 RPM)

**Expected Results**:
- Power: +20-25 HP / +15-20 Nm
- Fuel: 98 RON minimum required
- Hardware: Stock OK, upgraded exhaust recommended
- Risk: **Low-Medium** (conservative tune)

---

### Stage 2
**Description**: Aggressive tune with raised rev limit for maximum NA power

**Modifications**:
- Ignition timing: +5° advance (WOT), +3° (part-load)
- Fuel correction: +4 counts (WOT), +2 counts (part-load)
- Lambda targets: -11 counts (WOT), -5 counts (part-load)
- Ignition trims: +2 counts uniform
- **Rev limit: 6800 RPM** (vs 6500 stock)

**Expected Results**:
- Power: +25-30 HP / +20-25 Nm
- Fuel: 98+ RON **required**
- Hardware: Performance exhaust + cold air intake strongly recommended
- Risk: **Medium** (requires premium fuel, monitor knock)

⚠️ **Note**: Stage 2 is not recommended for daily driving without supporting modifications.

---

### Pop & Bang / Burble
**Description**: Overrun entertainment effects (can be added to any stage)

**Modifications**:
- **Pop & Bang**: -12° ignition retard on overrun, +4 counts fuel enrichment
- **Burble**: -20° ignition retard on overrun, +7 counts fuel enrichment

**Effect**: Produces exhaust crackles and pops during deceleration (requires performance exhaust with minimal restriction)

---

## 🗺️ ECU Memory Mapping

### Key Calibration Tables

| Map Name | Address | Size | Dimensions | Notes |
|----------|---------|------|------------|-------|
| **Ignition Advance #1** (primary) | `0x0082C9` | 163 bytes | 12×13 | Main timing map |
| **Ignition Advance #2** (cold-start) | `0x0083A9` | 163 bytes | 12×13 | Cold engine enrichment |
| **Ignition Advance #3** (part-load) | `0x008489` | 163 bytes | 12×13 | Cruise/economy mode |
| **Ignition Advance #4** (WOT/knock-ref) | `0x008569` | 163 bytes | 12×13 | High-load reference |
| **Fuel Correction #1** (warm) | `0x0086C9` | 115 bytes | 10×11 | Normal operating temp |
| **Fuel Correction #2** (cold) | `0x00876C` | 115 bytes | 10×11 | Cold-start enrichment |
| **Fuel Correction #3** (part-load) | `0x00880F` | 115 bytes | 10×11 | Cruise/economy mode |
| **Fuel Correction #4** (WOT) | `0x0088B2` | 115 bytes | 10×11 | Wide-open throttle |
| **Lambda Target #1** (primary) | `0x00C7A7` | 163 bytes | 12×13 | AFR target map |
| **Lambda Target #2** (backup) | `0x00C885` | 163 bytes | 12×13 | Duplicate copy |
| **Ignition Trim** (high-RPM) | `0x00896B` | 62 bytes | 6×9 | Fine correction |
| **Ignition Trim** (transient) | `0x0089CE` | 22 bytes | 2×11 | Tip-in correction |

### Table Axes

**12-Point RPM Axis** (`0x0081C0`, 16-bit big-endian):
```
2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000, 6400 RPM
```

**12-Point Load Axis** (`0x008290`, 8-bit):
```
117, 106, 103, 97, 94, 91, 88, 85, 77, 63, 51, 46 (raw units)
Approx: 91%, 83%, 80%, 76%, 73%, 71%, 69%, 66%, 60%, 49%, 40%, 36% WOT
```

### Special Addresses

| Parameter | Address | Format | Stock Value | Notes |
|-----------|---------|--------|-------------|-------|
| **PIN Code** (immobilizer) | `0x008141` | BCD packed | `3305` | Used for immobilizer sync |
| **Rev Limit** (engage) | `0x00B568` | uint16 BE | `6500` RPM | Fuel cut activation |
| **Rev Limit** (hysteresis) | `0x00B570` | uint16 BE | `6495` RPM | Fuel cut re-enable |
| **Part Number** | `0x00800C` | ASCII | `12591333` | ECU hardware ID |
| **Calibration ID** | `0x00602C` | ASCII | `W0L0TGF675B000465` | Software version |

### Scaling Factors

- **Ignition**: 1 count ≈ 0.5° (varies by map region)
- **Fuel**: 1 count ≈ 0.78% (128 = 100% = stoichiometric)
- **Lambda**: value × (14.7 / 128) = AFR  (128 = λ1.0 = 14.7:1)
- **RPM**: 16-bit big-endian (6500 RPM = `0x1964`)

For full mapping documentation, see [ECU_Mapping_Report.md](ECU_Mapping_Report.md).

---

## ⚠️ Safety & Disclaimers

### Important Safety Information

⚠️ **READ BEFORE USE** ⚠️

1. **Always Create Backups**
   - Read and save your stock ECU file before making any changes
   - Keep multiple backups in different locations
   - The tool creates automatic timestamped backups, but manual backups are recommended

2. **Hardware Limitations**
   - Stage 1 is safe on stock hardware with 95+ RON fuel
   - Stage 1+ and Stage 2 require 98+ RON fuel and supporting modifications
   - Aggressive tuning without proper hardware can cause engine damage

3. **Monitor Engine Health**
   - Watch for knock/ping under load (indicates excessive timing advance)
   - Monitor coolant and oil temperatures
   - Check spark plugs regularly for signs of detonation
   - Use a wideband O2 sensor to verify AFR if possible

4. **ECU Flashing Risks**
   - Ensure stable power supply during flash (use battery charger)
   - Never interrupt the flashing process
   - Have a backup plan (spare ECU or recovery method)
   - Use professional tools (MPPS, Kess, Alientech, etc.)

5. **Emissions & Legal**
   - Modifying ECU calibration may affect emissions compliance
   - Check local laws regarding ECU tuning
   - May void manufacturer warranty
   - **Track use only** in jurisdictions where modifications are restricted

### Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. The authors and contributors are not responsible for:
- Engine damage or mechanical failures
- ECU failures or bricking
- Emissions compliance violations
- Warranty voidance
- Legal consequences

**Use at your own risk.** ECU tuning requires mechanical knowledge and understanding of engine management principles. If you are not confident, seek professional tuning services.

---

## 📚 Technical Documentation

### Additional Resources

- **[ECU_Mapping_Report.md](ECU_Mapping_Report.md)**: Comprehensive binary analysis report
  - Complete table-by-table comparison of stock vs. Stage 1
  - Detailed address mapping with examples
  - Cross-file analysis of 2001 vs. 2004 calibrations
  - PIN code extraction methodology
  - Future tuning opportunities

- **[ecu_analysis.py](ecu_analysis.py)**: Binary analysis tool source code
  - Automated diff analysis
  - Table detection and classification
  - BCD PIN code decoding
  - Report generation

### Binary File Structure

The GMPT-E15 ECU uses a 512 KB calibration file organized as follows:

```
0x000000 - 0x007FFF : Code region (bootloader, main program)
0x008000 - 0x00CFFF : Calibration data (maps, tables, constants)
0x00D000 - 0x07FFFF : Extended data / unused / padding
```

**Key Regions**:
- `0x008000 - 0x008FFF`: Axes, ignition, and fuel maps
- `0x00A000 - 0x00BFFF`: Temperature corrections, lambda control
- `0x00C000 - 0x00CFFF`: Lambda targets, backup tables

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues
- Open an issue on GitHub with detailed description
- Include ECU part number, calibration ID, and error messages
- Attach logs if applicable (remove sensitive data like PIN codes)

### Submitting Improvements
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes with clear commit messages
4. Test thoroughly with real ECU files
5. Submit a pull request with description of changes

### Areas for Contribution
- [ ] Support for additional Z22SE ECU variants (e.g., Vectra C)
- [ ] Graphical table editors (2D/3D visualization)
- [ ] Checksum calculation (auto-fix ECU checksums)
- [ ] Additional tuning profiles (E85, economy mode)
- [ ] Real-time logging integration (via OBD-II)
- [ ] Automated testing framework

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Z22SE_Tuner Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **ECU Analysis**: Binary mapping verified against real-world Stage 1 tuning files
- **Community**: Opel/Vauxhall Z22SE tuning community for knowledge sharing
- **Tools**: PyQt6 framework for cross-platform GUI development
- **Inspiration**: Open-source ECU tuning movement (TunerStudio, RomRaider, etc.)

---

## 📧 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/zewy9910-ux/Z22SE_Tuner/issues)
- **Discussions**: Share tuning results and ask questions in the Discussions tab
- **Repository**: [https://github.com/zewy9910-ux/Z22SE_Tuner](https://github.com/zewy9910-ux/Z22SE_Tuner)

---

<div align="center">

**⚡ Happy Tuning! ⚡**

*Made with ❤️ for the Z22SE community*

</div>