# Sample ECU Binary Files

This directory contains sample ECU binary files for the Opel/Vauxhall Z22SE 2.2L engine with GMPT-E15 ECU.

## Directory Contents

### Stock ECU Files (.ORI format)
- `Astra G 2.2 SRi Z22SE GMPT 2001 Hw 09391283 BC.ORI` - 2001 Astra G stock calibration
- `Astra G 2.2 SRi Z22SE GMPT 2004 Hw 12210453 EB.ORI` - 2004 Astra G stock calibration
- `Opel Speedster 2.2 147hp Z22SE Hw 12202073 BZ.ORI` - Speedster stock calibration

### Reference Binary Files (.bin format)
- `OpelAstraG_Z22SE_GMPT-E15_Stock.bin` - Stock ECU binary (baseline for comparison)
- `OpelAstraG_Z22SE_GMPT-E15_Stage 1.bin` - Stage 1 tune (verified reference)
- `OpelAstraG_Z22SE_GMPT-E15_Stage2_PopBang.bin` - Stage 2 with Pop & Bang effects

### Alternative Format Files
- `Opel_Astra-G_2.2_L_2001_Benzin___108.1KWKW_____DD1D.Original` - 2001 original calibration
- `Opel_Astra-G_2.2_L_2001_Benzin___108.1KWKW_____E718.Stage1` - 2001 Stage 1 tune

## File Size
All files are exactly **512 KB** (524,288 bytes) as required by the GMPT-E15 ECU.

## Usage

### With Z22SE_Tuner.py
When using the main tuner application, load files from this directory:
```bash
python Z22SE_Tuner.py
# Then use File > Open to select a file from sample_files/
```

### With Analysis Tools
The analysis scripts (`ecu_analysis.py` and `analyze_oris.py`) are configured to automatically use files from this directory.

```bash
# Generate ECU mapping report
python ecu_analysis.py

# Analyze all .ORI files
python analyze_oris.py
```

## Important Notes

⚠️ **Security Warning**: These files contain:
- ECU calibration data
- Immobilizer PIN codes
- Vehicle identification information

🔒 **Privacy**: Before sharing any ECU files publicly:
- Remove or anonymize PIN codes
- Remove VIN numbers and calibration IDs if sensitive
- Consider if the files contain any personally identifiable information

📝 **Testing**: When creating test fixtures:
- Use anonymized data
- Create minimal 512KB files with only necessary addresses populated
- Never commit real customer ECU files

## File Formats

### .ORI Files
Original ECU dump files, typically from professional tuning tools.

### .bin Files
Standard binary format, compatible with most ECU flashing tools.

### .Original / .Stage1
Alternative naming conventions used by some tuning software.

## Adding Your Own Files

To use your own ECU files:
1. Ensure the file is exactly 512 KB (524,288 bytes)
2. Place it in this directory
3. Load it using Z22SE_Tuner.py
4. Always create backups before modifying!

---

*Last updated: 2026-02-19*
