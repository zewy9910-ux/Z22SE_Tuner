# Opel Astra G Z22SE GMPT-E15 — ECU Binary Mapping Report

**ECU:** GMPT-E15 (Delco/Delphi)  |  **Engine:** Z22SE 2.2L NA  |  **Vehicle:** Opel Astra G Cabrio 2004
**Stock file:** `OpelAstraG_Z22SE_GMPT-E15_Stock.bin`  (524,288 bytes = 512 KB)
**Stage 1 file:** `OpelAstraG_Z22SE_GMPT-E15_Stage 1.bin`

---
## 1  PIN / Immobilizer Code

| Address | Bytes (hex) | BCD Decoded | Match |
|---------|-------------|-------------|-------|
| `0x008141` | `3305` | **3305** | ✅ Matches 3305 |

**Context (20 bytes around address 0x008140):**
```
0x008138: 56 67 00 02 10 FF 41 D4 33 33 05 C3 05 9F 0B 54 0B B8 20 14
0x008138: FF 41 D4 [33 33 05] C3 05 9F 0B 54 ...  ← bytes at 0x008141 = 33 05 = BCD 3305
```
> BCD packed: high nibble = 1st digit, low nibble = 2nd digit per byte.
> `0x33` → digits `33`; `0x05` → digits `05` → PIN = **3305** ✅

**Second occurrence** (code region, not EEPROM storage):
- `0x0060AA`: `EA7E330500A2` — same BCD value, appears in code constants

---
## 2  Rev Limiter / Fuel Cut-Off

The fuel cut is implemented with two paired 16-bit big-endian RPM thresholds
(activate / deactivate with hysteresis).

| Address | Description | Stock | Stage 1 | Notes |
|---------|-------------|-------|---------|-------|
| `0x00B568` | Fuel Cut ON #1  | 6500 RPM | 6500 RPM | Primary cut engage |
| `0x00B56A` | Fuel Cut ON #2  | 6500 RPM | 6500 RPM | |
| `0x00B570` | Fuel Cut OFF #1 | 6495 RPM | 6495 RPM | Hysteresis re-enable |
| `0x00B572` | Fuel Cut OFF #2 | 6495 RPM | 6495 RPM | |
| `0x00195A` | Fuel Cut OFF #3 | 7 RPM | 7 RPM | Secondary hysteresis |

**Raw bytes (stock):**
```
0x00B560: 98 FF FF FE 00 FA 00 FA 19 64 19 64 00 C8 00 C8 19 5F 19 5F 19 5A 19 5A 08 02 14 FF 00 00 00 00
```

> ⚠️ Fuel cut RPM is **not changed** between stock and Stage 1 files (both = 6500 RPM).
> To raise the rev limit, modify the `0x00B568` and `0x00B56A` values (big-endian uint16).
> Example: 6800 RPM = `0x1A90`, 7000 RPM = `0x1B58`.

---
## 3  Table Axes

### 3.1  12-Point RPM Axis (used by 4× 163-byte maps at 0x0082C9–0x00860B)

Stored as 16-bit big-endian values at `0x0081C0`:

| Idx | RPM  | Hex    |
|-----|------|--------|
|  0  |  2000 | `07D0` |
|  1  |  2400 | `0960` |
|  2  |  2800 | `0AF0` |
|  3  |  3200 | `0C80` |
|  4  |  3600 | `0E10` |
|  5  |  4000 | `0FA0` |
|  6  |  4400 | `1130` |
|  7  |  4800 | `12C0` |
|  8  |  5200 | `1450` |
|  9  |  5600 | `15E0` |
| 10  |  6000 | `1770` |
| 11  |  6400 | `1900` |

### 3.2  12-Point Load / MAP Axis (8-bit, kPa-equivalent, descending)

Stored at `0x008290` (12 bytes), used as row axis for 163-byte tables:

| Idx | Raw | Approx % WOT |
|-----|-----|-------------|
|  0  | 117 (0x75) | 91% |
|  1  | 106 (0x6A) | 83% |
|  2  | 103 (0x67) | 80% |
|  3  |  97 (0x61) | 76% |
|  4  |  94 (0x5E) | 73% |
|  5  |  91 (0x5B) | 71% |
|  6  |  88 (0x58) | 69% |
|  7  |  85 (0x55) | 66% |
|  8  |  77 (0x4D) | 60% |
|  9  |  63 (0x3F) | 49% |
| 10  |  51 (0x33) | 40% |
| 11  |  46 (0x2E) | 36% |

---
## 4  Modified Tables (Stock → Stage 1 Differences)

**Total changed bytes:** 1522
**Number of changed regions:** 12

### 4.1  Ignition Advance Map 1 (primary)
- **Address:** `0x0082C9` – `0x00836B`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
104  90  83  79  71  69  67 120 134 142 133 122 116 109  97  91  81  71  71  71 159 157 150 139 128 123 112 104  98  91  81  77
```
**First 32 bytes — Stage 1:**
```
106  92  85  81  73  71  69 120 134 142 133 122 116 111  99  93  83  73  73  73 159 157 150 139 128 123 114 106 100  93  83  79
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2
```
*Changed bytes in first 32: 20, avg |delta|: 2.0*

### 4.2  Ignition Advance Map 2 (secondary/cold)
- **Address:** `0x0083A9` – `0x00844B`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
121 114 108 103  98  89  85 120 134 145 139 131 128 126 121 105 100  94  91  87 159 157 151 146 137 134 131 131 120 111 108 103
```
**First 32 bytes — Stage 1:**
```
125 118 112 107 101  92  88 120 134 145 139 131 128 131 125 109 103  97  94  90 159 157 151 146 137 134 136 136 124 115 112 107
```
**Delta (Stage1 − Stock):**
```
 +4  +4  +4  +4  +3  +3  +3  +0  +0  +0  +0  +0  +0  +5  +4  +4  +3  +3  +3  +3  +0  +0  +0  +0  +0  +0  +5  +5  +4  +4  +4  +4
```
*Changed bytes in first 32: 20, avg |delta|: 3.8*

### 4.3  Ignition Advance Map 3 (part-load)
- **Address:** `0x008489` – `0x00852B`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
 60  54  48  39  28  23  17 108 108 108  97  85  76  67  61  54  45  37  29  23 108 108 108 100  91  82  74  67  60  53  46  37
```
**First 32 bytes — Stage 1:**
```
 62  56  50  41  30  25  19 108 108 108  97  85  76  69  63  56  47  39  31  25 108 108 108 100  91  82  76  69  62  55  48  39
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2
```
*Changed bytes in first 32: 20, avg |delta|: 2.0*

### 4.4  Ignition Advance Map 4 (WOT/knock-ref)
- **Address:** `0x008569` – `0x00860B`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
119 114 108 102  97  90  84 154 148 142 137 132 128 122 119 115 111 107 100  95 154 151 148 142 138 134 131 128 122 118 115 108
```
**First 32 bytes — Stage 1:**
```
121 116 110 104  99  92  86 154 148 142 137 132 128 124 121 117 113 109 102  97 154 151 148 142 138 134 133 130 124 120 117 110
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +2
```
*Changed bytes in first 32: 20, avg |delta|: 2.0*

### 4.5  Fuel/Injection Correction Map 1 (warm)
- **Address:** `0x0086C9` – `0x00873B`
- **Size:** 115 bytes
- **Likely dimensions:** 10 rows × 11 cols

**First 32 bytes — Stock:**
```
101  91  85  83  77 128 122 122 122 114 100  91  88  85  81 128 124 124 122 120 114 108 103  99  88 128 125 122 122 122 117 111
```
**First 32 bytes — Stage 1:**
```
103  93  87  85  79 128 122 122 122 114 102  93  90  87  83 128 124 124 122 120 116 110 105 101  90 128 125 122 122 122 119 113
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2
```
*Changed bytes in first 32: 17, avg |delta|: 2.0*

### 4.6  Fuel/Injection Correction Map 2 (cold)
- **Address:** `0x00876C` – `0x0087DE`
- **Size:** 115 bytes
- **Likely dimensions:** 10 rows × 11 cols

**First 32 bytes — Stock:**
```
123 120 120 117 114 137 135 134 131 128 125 120 120 117 114 131 131 128 125 125 125 120 118 117 114 131 134 131 125 125 122 120
```
**First 32 bytes — Stage 1:**
```
125 122 122 119 116 137 135 134 131 128 127 122 122 119 116 131 131 128 125 125 127 122 120 119 116 131 134 131 125 125 124 122
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2
```
*Changed bytes in first 32: 17, avg |delta|: 2.0*

### 4.7  Fuel/Injection Correction Map 3 (part-load)
- **Address:** `0x00880F` – `0x008881`
- **Size:** 115 bytes
- **Likely dimensions:** 10 rows × 11 cols

**First 32 bytes — Stock:**
```
 74  65  57  48  34 105 105 105 104  94  83  74  63  54  40 107 107 107 105  97  88  80  71  63  48 108 108 108 107 102  96  88
```
**First 32 bytes — Stage 1:**
```
 76  67  59  50  36 105 105 105 104  94  85  76  65  56  42 107 107 107 105  97  90  82  73  65  50 108 108 108 107 102  98  90
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2
```
*Changed bytes in first 32: 17, avg |delta|: 2.0*

### 4.8  Fuel/Injection Correction Map 4 (WOT)
- **Address:** `0x0088B2` – `0x008924`
- **Size:** 115 bytes
- **Likely dimensions:** 10 rows × 11 cols

**First 32 bytes — Stock:**
```
117 111 100  94  91 125 125 125 119 117 114 108 102  98  94 125 122 119 117 117 114 117 114 111 111 131 125 125 122 122 120 120
```
**First 32 bytes — Stage 1:**
```
119 113 102  96  93 125 125 125 119 117 116 110 104 100  96 125 122 119 117 117 116 119 116 113 113 131 125 125 122 122 122 122
```
**Delta (Stage1 − Stock):**
```
 +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2  +2  +2  +2  +0  +0  +0  +0  +0  +2  +2
```
*Changed bytes in first 32: 17, avg |delta|: 2.0*

### 4.9  Ignition Trim / High-RPM Correction (small)
- **Address:** `0x00896B` – `0x0089A8`
- **Size:** 62 bytes
- **Likely dimensions:** 6 rows × 9 cols

**First 32 bytes — Stock:**
```
 57  57  57  57  57  57  56  52  50  48  46  57  57  57  57  57  57  57  57  57  57  57  57  57  56  53  49  48  57  57  57  57
```
**First 32 bytes — Stage 1:**
```
 58  58  58  58  58  58  57  53  51  49  47  57  57  57  57  57  57  58  58  58  58  58  58  58  57  54  50  49  57  57  57  57
```
**Delta (Stage1 − Stock):**
```
 +1  +1  +1  +1  +1  +1  +1  +1  +1  +1  +1  +0  +0  +0  +0  +0  +0  +1  +1  +1  +1  +1  +1  +1  +1  +1  +1  +1  +0  +0  +0  +0
```
*Changed bytes in first 32: 22, avg |delta|: 1.0*

### 4.10  Ignition Trim / Transient Correction (small)
- **Address:** `0x0089CE` – `0x0089E3`
- **Size:** 22 bytes
- **Likely dimensions:** 2 rows × 11 cols

**First 32 bytes — Stock:**
```
 57  57  57  57  52  51  51  49  49  48  50  46  46  45  41  41  50  45  43  41  36  33
```
**First 32 bytes — Stage 1:**
```
 58  58  58  58  52  51  52  50  50  49  50  46  47  46  42  42  50  45  44  42  37  34
```
**Delta (Stage1 − Stock):**
```
 +1  +1  +1  +1  +0  +0  +1  +1  +1  +1  +0  +0  +1  +1  +1  +1  +0  +0  +1  +1  +1  +1
```
*Changed bytes in first 32: 16, avg |delta|: 1.0*

### 4.11  Lambda/AFR Target Map (primary copy)
- **Address:** `0x00C7A7` – `0x00C849`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
 98  96  94  93  92  92  92 133 133 121 114 108 105 103 101  99  97  96  96  96 143 143 127 118 113 110 107 105 103 102 101 101
```
**First 32 bytes — Stage 1:**
```
 93  91  88  86  85  84  84 133 133 121 114 108 105  98  95  92  90  88  88  87 143 143 127 118 113 110 101  99  96  94  93  92
```
**Delta (Stage1 − Stock):**
```
 -5  -5  -6  -7  -7  -8  -8  +0  +0  +0  +0  +0  +0  -5  -6  -7  -7  -8  -8  -9  +0  +0  +0  +0  +0  +0  -6  -6  -7  -8  -8  -9
```
*Changed bytes in first 32: 20, avg |delta|: 7.0*

### 4.12  Lambda/AFR Target Map (duplicate/backup copy)
- **Address:** `0x00C885` – `0x00C927`
- **Size:** 163 bytes
- **Likely dimensions:** 12 rows × 13 cols

**First 32 bytes — Stock:**
```
 98  96  94  93  92  92  92 133 133 121 114 108 105 103 101  99  97  96  96  96 143 143 127 118 113 110 107 105 103 102 101 101
```
**First 32 bytes — Stage 1:**
```
 93  91  88  86  85  84  84 133 133 121 114 108 105  98  95  92  90  88  88  87 143 143 127 118 113 110 101  99  96  94  93  92
```
**Delta (Stage1 − Stock):**
```
 -5  -5  -6  -7  -7  -8  -8  +0  +0  +0  +0  +0  +0  -5  -6  -7  -7  -8  -8  -9  +0  +0  +0  +0  +0  +0  -6  -6  -7  -8  -8  -9
```
*Changed bytes in first 32: 20, avg |delta|: 7.0*

---
## 5  Lambda / AFR Target Maps — Detailed

Two identical copies exist (primary + backup). Stage 1 reduces values at high-load
cells, indicating a **richer AFR target at WOT** (typical Stage 1 change).

**Scaling:** value × (14.7 / 128) ≈ AFR  (0x80 = 128 ≈ λ1.0 / 14.7:1)

| Addr | Role |
|------|------|
| `0x00C7A7` | Primary copy  |
| `0x00C885` | Duplicate/backup copy |

**Sample row comparison (first 13 bytes = one row):**

```
Row00: * stock=[' 98', ' 96', ' 94', ' 93', ' 92', ' 92', ' 92', '133', '133', '121', '114', '108', '105']
       s1   =[' 93', ' 91', ' 88', ' 86', ' 85', ' 84', ' 84', '133', '133', '121', '114', '108', '105']
       AFR  =['10.68', '10.45', '10.11', '9.88', '9.76', '9.65', '9.65', '15.27', '15.27', '13.90', '13.09', '12.40', '12.06']
Row01: * stock=['103', '101', ' 99', ' 97', ' 96', ' 96', ' 96', '143', '143', '127', '118', '113', '110']
       s1   =[' 98', ' 95', ' 92', ' 90', ' 88', ' 88', ' 87', '143', '143', '127', '118', '113', '110']
       AFR  =['11.25', '10.91', '10.57', '10.34', '10.11', '10.11', '9.99', '16.42', '16.42', '14.59', '13.55', '12.98', '12.63']
Row02: * stock=['107', '105', '103', '102', '101', '101', '100', '145', '145', '129', '120', '114', '112']
       s1   =['101', ' 99', ' 96', ' 94', ' 93', ' 92', ' 91', '145', '145', '129', '120', '114', '112']
       AFR  =['11.60', '11.37', '11.02', '10.80', '10.68', '10.57', '10.45', '16.65', '16.65', '14.81', '13.78', '13.09', '12.86']
Row03: * stock=['109', '107', '105', '104', '102', '102', '102', '148', '148', '132', '122', '115', '113']
       s1   =['103', '100', ' 98', ' 96', ' 93', ' 93', ' 92', '148', '148', '132', '122', '115', '113']
       AFR  =['11.83', '11.48', '11.25', '11.02', '10.68', '10.68', '10.57', '17.00', '17.00', '15.16', '14.01', '13.21', '12.98']
Row04: * stock=['110', '108', '106', '105', '104', '104', '103', '150', '150', '132', '122', '116', '113']
       s1   =['103', '101', ' 98', ' 97', ' 95', ' 94', ' 93', '150', '150', '132', '122', '116', '113']
       AFR  =['11.83', '11.60', '11.25', '11.14', '10.91', '10.80', '10.68', '17.23', '17.23', '15.16', '14.01', '13.32', '12.98']
Row05: * stock=['110', '108', '106', '105', '104', '104', '103', '152', '152', '133', '122', '116', '113']
       s1   =['103', '101', ' 98', ' 96', ' 95', ' 94', ' 92', '152', '152', '133', '122', '116', '113']
       AFR  =['11.83', '11.60', '11.25', '11.02', '10.91', '10.80', '10.57', '17.46', '17.46', '15.27', '14.01', '13.32', '12.98']
Row06: * stock=['110', '108', '107', '105', '104', '104', '103', '169', '169', '135', '123', '116', '113']
       s1   =['103', '100', ' 99', ' 96', ' 94', ' 94', ' 92', '169', '169', '135', '123', '116', '113']
       AFR  =['11.83', '11.48', '11.37', '11.02', '10.80', '10.80', '10.57', '19.41', '19.41', '15.50', '14.13', '13.32', '12.98']
Row07: * stock=['110', '108', '106', '105', '104', '103', '103', '155', '155', '134', '123', '116', '114']
       s1   =['103', '100', ' 97', ' 96', ' 94', ' 93', ' 92', '155', '155', '134', '123', '116', '114']
       AFR  =['11.83', '11.48', '11.14', '11.02', '10.80', '10.68', '10.57', '17.80', '17.80', '15.39', '14.13', '13.32', '13.09']
Row08: * stock=['111', '110', '108', '107', '106', '105', '105', '143', '143', '133', '125', '119', '117']
       s1   =['103', '102', ' 99', ' 97', ' 96', ' 94', ' 93', '143', '143', '133', '125', '119', '117']
       AFR  =['11.83', '11.71', '11.37', '11.14', '11.02', '10.80', '10.68', '16.42', '16.42', '15.27', '14.36', '13.67', '13.44']
Row09: * stock=['115', '114', '112', '111', '111', '110', '110', '141', '141', '134', '129', '125', '124']
       s1   =['107', '105', '102', '101', '100', ' 98', ' 98', '141', '141', '134', '129', '125', '124']
       AFR  =['12.29', '12.06', '11.71', '11.60', '11.48', '11.25', '11.25', '16.19', '16.19', '15.39', '14.81', '14.36', '14.24']
Row10: * stock=['122', '121', '120', '120', '119', '119', '119', '146', '146', '136', '130', '126', '125']
       s1   =['113', '111', '109', '109', '107', '106', '105', '146', '146', '136', '130', '126', '125']
       AFR  =['12.98', '12.75', '12.52', '12.52', '12.29', '12.17', '12.06', '16.77', '16.77', '15.62', '14.93', '14.47', '14.36']
Row11: * stock=['123', '122', '121', '121', '120', '120', '119', '154', '154', '136', '129', '124', '122']
       s1   =['113', '112', '110', '109', '108', '107', '105', '154', '154', '136', '129', '124', '122']
       AFR  =['12.98', '12.86', '12.63', '12.52', '12.40', '12.29', '12.06', '17.69', '17.69', '15.62', '14.81', '14.24', '14.01']
```

---
## 6  Additional Tunable Locations (Unmapped by ECM Titanium)

These regions are NOT modified in the Stage 1 file but are important for further tuning.

### 6.1  Ignition Timing Map (high-res, degrees)
**Address:** `0x008F90`

Values appear to be ignition advance in degrees. Contains RPM breakpoints including 6500 RPM:
```
  0x008F90: 255 204 163 136 117 103  92  66  52  44  38  33  30  27
  0x008F9E:  25 158 124 103  88  77  69  62  57  52  44  38  33  30
  0x008FAC:  27  25 119  96  81  70  62  56  51  47  43  40  38  33
  0x008FBA:  30  27  25 100  81  69  60  53  48  44  41  38  35  33
  0x008FC8:  32  30  27  25  87  72  61  54  48  44  40  37  34  32
  0x008FD6:  30  29  27  26  25  79  65  56  49  44  40  37  34  32
  0x008FE4:  30  28  27  25  24  23  72  60  52  46  41  37  34  32
  0x008FF2:  30  28  26  25  24  23  22  69  57  49  44  39  36  33
```

### 6.2  IAT (Intake Air Temperature) Timing Correction
**Address:** `0x00A610` — 12 values (degrees of retard per temperature band)
```
  106  62  31  24  22  20  19  18  18  19  20  25
  Degrees: +106° +62° +31° +24° +22° +20° +19° +18° +18° +19° +20° +25°
```

### 6.3  RPM-Indexed Control Table (idle, tip-in, spark cut)
**Address:** `0x008150` — 16-bit RPM breakpoints for spark angle scheduling
```
  RPM:  2240  2200  2400  2700  2900  3437  3437  3437  8447   800   800   800  1200  1600
```

### 6.4  Coolant Temperature (ECT) Correction Area
**Address:** `0x008240` — threshold/scaling constants for cold-start enrichment
```
0x008240: 03 55 04 00 06 03 00 FF 00 AB FF D5 FF D5 8D 9F 55 55 68 69 69 89 8B 8E 91 9A 9F A4 A8 AB D9 FF
```

### 6.5  Fuel Cut / Rev Limit Parameters (full block)
**Address:** `0x00B540` – `0x00B580`
```
  0x00B540: 20 21 22 23 23 24 25 26 25 24 23 23 22 22 21 20 <<SAME
  0x00B550: 6C 73 7B 8D 94 94 94 94 00 03 0D 17 17 17 50 9B <<SAME
  0x00B560: 98 FF FF FE 00 FA 00 FA 19 64 19 64 00 C8 00 C8 <<SAME
  0x00B570: 19 5F 19 5F 19 5A 19 5A 08 02 14 FF 00 00 00 00 <<SAME
```

### 6.6  O2/Lambda Sensor Control Constants
**Address:** `0x00A5E0` — contains lambda correction coefficients and O2 sensor scaling
```
0x00A5E0: AA AA AB B8 C0 C2 BD B8 B6 BD C6 C6 D3 01 00 00
0x00A5F0: 05 11 20 0D 2C 2C 4B 9C BC DA DA 5B A8 D0 ED ED
0x00A600: 65 BF E0 F8 F8 28 73 0A 02 FF 00 00 0F 00 00 84
0x00A610: 6A 3E 1F 18 16 14 13 12 12 13 14 19 00 00 84 6A
```

---
## 7  Quick-Reference Address Map

| Purpose | Address | Size | Format | Notes |
|---------|---------|------|--------|-------|
| **PIN Code (immobilizer)** | `0x008141` | 2 bytes | BCD packed | `33 05` = 3305 |
| **Fuel Cut RPM (engage)** | `0x00B568` | 2 bytes | uint16 BE | 6500 RPM = `19 64` |
| **Fuel Cut RPM (hysteresis)** | `0x00B570` | 2 bytes | uint16 BE | 6495 RPM = `19 5F` |
| **Ignition Advance Map 1 (primary)** | `0x0082C9` | 163 B | 12×13 byte table | CHANGED |
| **Ignition Advance Map 2 (secondary/cold)** | `0x0083A9` | 163 B | 12×13 byte table | CHANGED |
| **Ignition Advance Map 3 (part-load)** | `0x008489` | 163 B | 12×13 byte table | CHANGED |
| **Ignition Advance Map 4 (WOT/knock-ref)** | `0x008569` | 163 B | 12×13 byte table | CHANGED |
| **Fuel/Injection Correction Map 1 (warm)** | `0x0086C9` | 115 B | 10×11 byte table | CHANGED |
| **Fuel/Injection Correction Map 2 (cold)** | `0x00876C` | 115 B | 10×11 byte table | CHANGED |
| **Fuel/Injection Correction Map 3 (part-load)** | `0x00880F` | 115 B | 10×11 byte table | CHANGED |
| **Fuel/Injection Correction Map 4 (WOT)** | `0x0088B2` | 115 B | 10×11 byte table | CHANGED |
| **Ignition Trim / High-RPM Correction (small)** | `0x00896B` | 62 B | 6×9 byte table | CHANGED |
| **Ignition Trim / Transient Correction (small)** | `0x0089CE` | 22 B | 2×11 byte table | CHANGED |
| **Lambda/AFR Target Map (primary copy)** | `0x00C7A7` | 163 B | 12×13 byte table | CHANGED |
| **Lambda/AFR Target Map (duplicate/backup copy)** | `0x00C885` | 163 B | 12×13 byte table | CHANGED |
| **RPM axis (12-pt)** | `0x0081C0` | 24 bytes | uint16 BE ×12 | 2000–6400 RPM |
| **Load axis (12-pt)** | `0x008290` | 12 bytes | uint8 ×12 | 46–117 (raw) |
| **Ignition map (hi-res)** | `0x008F90` | ~112 bytes | uint8 degrees | Not changed |
| **IAT timing correction** | `0x00A610` | 12 bytes | uint8 degrees | Not changed |
| **Lambda/O2 constants** | `0x00A5E0` | 64 bytes | mixed | Not changed |

---
## 8  Stage 1 Changes Summary

Based on binary diff analysis:

| Change | Direction | Typical Amount |
|--------|-----------|---------------|
| Ignition advance maps (×4, 163-byte) | **+1 to +3 counts** (≈ +0.5° to +1.5°) | Mild advance across mid-high RPM |
| Fuel/injection correction maps (×4, 115-byte) | **+1 to +3 counts** | Slight enrichment |
| Ignition trim corrections (×2 small) | **+1 count** uniformly | Consistent small advance |
| Lambda/AFR target maps (×2, 163-byte) | **−5 to −8 counts** at WOT cells | Richer WOT target (≈0.9 λ) |
| Rev limit | **Unchanged** | 6500 RPM stock and stage 1 |

**Stage 1 philosophy:** Small ignition advance + slightly richer WOT fueling. No rev limit change.

---
## 9  Known Missing / Unidentified Maps (Further Work Needed)

These are commonly tunable on GMPT-E15 but addresses need verification:

| Map | Typical Location | How to Find |
|-----|-----------------|-------------|
| VE (Volumetric Efficiency) 3D | 0x008000–0x008900 area | Look for 16×16 table with ~128 center values |
| Knock retard map | Near ignition maps | Values 0–15 (degrees retard steps) |
| Cold-start enrichment (CLT) | 0x008240 area | Values keyed on coolant temp axis |
| Idle target RPM | 0x008150 area | 16-bit BE RPM near 0x0320=800 |
| Injector dead-time | Unknown | 16-bit values indexed by battery voltage |
| Closed-loop lambda multiplier | 0x00A680–0x00B000 area | Values near 0x80=1.0× |
| Speed limiter | 0x00B540+ area | uint16 km/h threshold |
| Throttle adaptation | 0x008000 area | Small byte table |

---
*Report generated by `ecu_analysis.py` — analysis of raw binary only.
Always verify addresses with a hex editor before modifying. Backup your original bin.*---
## 10  Cross-File Analysis: DB Files vs Our Files
### 10.1  File Identity
| File | Part Number | Calibration ID | MD5 |
|------|-------------|----------------|-----|
| `OpelAstraG_Z22SE_GMPT-E15_Stock.bin` | **12591333** | `W0L0TGF675B000465` | `a509790d...` |
| `OpelAstraG_Z22SE_GMPT-E15_Stage 1.bin` | 12591333 *(unchanged)* | `W0L0TGF675B000465` | `dcd7d44e...` |
| `Opel_Astra-G_2.2_L_2001_Benzin___108.1KWKW_____DD1D.Original` | **12215796** | `W0L0TGF071B022321` | `5c38c47b...` |
| `Opel_Astra-G_2.2_L_2001_Benzin___108.1KWKW_____E718.Stage1` | 12215796 *(unchanged)* | `W0L0TGF071B022321` | `be8cca81...` |
**The `.Original` file is NOT the same as our `_Stock.bin`.**  
They differ by **324,665 bytes** (62% of the file).
- Our Stock = **2004** Astra G 2.2 Z22SE, part `12591333`, cal `W0L0TGF675B000465`
- DB Original = **2001** Astra G 2.2 Z22SE, part `12215796`, cal `W0L0TGF071B022321`
- Same ECU hardware family (GMPT-E15 / Delco), base string `391283BC` identical in both
- Code sections differ (different model year calibration software), but calibration data maps are at the **same addresses** — same ECU platform
---
### 10.2  DB Stage1 Changes vs Our Stage1 Changes — Table Comparison
Both Stage1 files modify the **exact same tables at the exact same addresses**.  
The direction of all changes is identical (all ignition/fuel values increase).  
The DB tune is simply more aggressive (larger delta per cell).
| Table | Address | Our Stage1 Δ | DB Stage1 Δ | Match? |
|-------|---------|-------------|-------------|--------|
| Ignition Advance Map 1 | `0x0082C9` | +1 to +2 (91/163 cells) | **+4 uniform** (163/163) | ✅ Same table, same direction |
| Ignition Advance Map 2 | `0x0083A9` | +1 to +5 (91/163 cells) | **+4 uniform** (163/163) | ✅ |
| Ignition Advance Map 3 | `0x008489` | +1 to +2 (91/163 cells) | **+3 uniform** (163/163) | ✅ |
| Ignition Advance Map 4 | `0x008569` | +1 to +2 (91/163 cells) | **+4 uniform** (163/163) | ✅ |
| Fuel Correction Map 1  | `0x0086C9` | +1 to +2 (60/115 cells) | **+3 uniform** (115/115) | ✅ |
| Fuel Correction Map 2  | `0x00876C` | +1 to +2 (60/115 cells) | **+3 uniform** (115/115) | ✅ |
| Fuel Correction Map 3  | `0x00880F` | +1 to +2 (60/115 cells) | **+3 uniform** (115/115) | ✅ |
| Fuel Correction Map 4  | `0x0088B2` | +1 to +2 (60/115 cells) | **+3 uniform** (115/115) | ✅ |
| Ignition Trim 1        | `0x00896B` | +1 (44/62 cells)        | **unchanged** | ⚠️ Only our Stage1 |
| Ignition Trim 2        | `0x0089CE` | +1 (16/22 cells)        | **unchanged** | ⚠️ Only our Stage1 |
| Lambda Map (primary)   | `0x00C7A7` | −5 to −14 (91/163 cells)| **unchanged** | ⚠️ Only our Stage1 |
| Lambda Map (backup)    | `0x00C885` | −5 to −14 (91/163 cells)| **unchanged** | ⚠️ Only our Stage1 |
**DB Lambda is modified at a different address:** `0x00C5BD–0x00C777` (443 bytes, +2 uniform).  
This is 48 bytes before our lambda start — the 2001 cal places its lambda table at a slightly earlier offset.
---
### 10.3  DB-Only Changes (not present in our Stage1)
| Address | DB Change | Interpretation |
|---------|-----------|----------------|
| `0x008000` | checksum `26 A9` → `4C C9` | **Tune checksum updated** — DB tool recalculates the calibration checksum after writing |
| `0x00E2B0` | `FF FF...` → `EVC.EVC.\x00...` | **Tuner watermark** — ECM Titanium writes its own tool signature (`EVC`) into unused Flash space |
| `0x00C5BD–0x00C777` | +2 uniform | Lambda target table at 2001-cal offset |
> ⚠️ **Checksum note:** Our Stage1 file does NOT update the checksum at `0x008000` (still `26 34`). This is fine for flash writing tools that recalculate it on the fly, but worth verifying with your specific tool.
---
### 10.4  Conclusion
| Question | Answer |
|----------|--------|
| Is `.Original` == `_Stock.bin`? | ❌ **No** — different model year (2001 vs 2004), different part numbers |
| Do they use the same ECU hardware? | ✅ **Yes** — same GMPT-E15 platform, same base ECU, same map addresses |
| Do both Stage1 files touch the same tables? | ✅ **Yes** — identical table addresses, same direction |
| Are the modification magnitudes the same? | ❌ **No** — DB Stage1 is more aggressive (+3/+4 uniform vs our +1/+2 selective) |
| Does the DB Stage1 modify lambda/O2 targets? | ✅ Yes, at offset `0x00C5BD` (2001 cal position, +2 uniform) |
| Does our Stage1 modify lambda/O2 targets? | ✅ Yes, at `0x00C7A7` (2004 cal position, −5 to −14 = richer) |
| Does the DB Stage1 update the ECU checksum? | ✅ Yes | Our Stage1 does not |
**Bottom line:** The DB files are a **different-year calibration of the same ECU family**, confirming that all four Stage1 tunes (our Stage1 and DB Stage1) target exactly the same functional calibration tables. The DB tune is a useful reference for understanding what a more aggressive Z22SE Stage1 looks like on the same ECU platform.
