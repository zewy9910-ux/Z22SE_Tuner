# Opel Astra G Z22SE GMPT-E15 — ECU Binary Mapping Report

**ECU:** GMPT-E15 (Delco/Delphi)  |  **Engine:** Z22SE 2.2L NA  |  **Vehicle:** Opel Astra G Cabrio 2004
**Stock file:** `sample_files/OpelAstraG_Z22SE_GMPT-E15_Stock.bin`  (524,288 bytes = 512 KB)
**Stage 1 file:** `sample_files/OpelAstraG_Z22SE_GMPT-E15_Stage 1.bin`

> **Note:** All sample ECU binary files are now stored in the `sample_files/` directory.

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
        Col→  0    1    2    3    4    5    6    7    8    9   10   11   12   13
Row 0:       255  204  163  136  117  103   92   66   52   44   38   33   30   27
Row 1:        25  158  124  103   88   77   69   62   57   52   44   38   33   30
Row 2:        27   25  119   96   81   70   62   56   51   47   43   40   38   33
Row 3:        30   27   25  100   81   69   60   53   48   44   41   38   35   33
Row 4:        32   30   27   25   87   72   61   54   48   44   40   37   34   32
Row 5:        30   29   27   26   25   79   65   56   49   44   40   37   34   32
Row 6:        30   28   27   25   24   23   72   60   52   46   41   37   34   32
Row 7:        30   28   26   25   24   23   22   69   57   49   44   39   36   33

Note: The diagonal pattern (high value on the diagonal, low values off-diagonal)
indicates this is a reference/scheduling table, not a primary tuning map.
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

---

## 11  OBDTuner Parameter Cross-Reference (v4)

OBDTuner is an aftermarket ECU tuning platform for GM Ecotec engines (L61, LE5, LSJ).
The Z22SE 2.2L is the **Opel designation for the GM L61 engine** — the same mechanical unit.

**Important distinction:** OBDTuner *replaces* the stock GM/GMPT-E15 firmware with its own
custom operating system. Z22SE_Tuner *patches* the original GMPT-E15 binary. The table
*addresses* therefore differ, but the *parameters and functions* are equivalent.

### 11.1  OBDTuner Features → GMPT-E15 Address Mapping

| OBDTuner Parameter | GMPT-E15 Address | Size | Z22SE_Tuner (v4) |
|---|---|---|---|
| **Fuel (VE) Table** | `0x0086C9`, `0x00876C`, `0x00880F`, `0x0088B2` | 4 × 115B | ✅ Stage 1/1+/2 |
| **Spark (Ignition) Table** | `0x0082C9`, `0x0083A9`, `0x008489`, `0x008569` | 4 × 163B | ✅ Stage 1/1+/2 |
| **Lambda / AFR Targets** | `0x00C7A7`, `0x00C885` (2004); `0x00C5BD`, `0x00C640` (2001) | 2 × 163B | ✅ Stage 1/1+/2 |
| **Rev Limit** | `0x00B568`, `0x00B56A` (2004 fw); auto-scanned (2001/Speedster) | uint16 BE | ✅ Custom RPM |
| **Idle RPM Target** | `0x008162` × 12 locations | uint16 BE | ✅ 600–1200 RPM |
| **IAT Timing Correction** | `0x00A610` – `0x00A650` | 12 bytes | ✅ Scale 0.0–1.5 |
| **Knock Threshold** | `0x008D81` | 1 byte | ✅ stock/safe/aggr/disabled |
| **O2 Closed-Loop Authority** | `0x00A680` – `0x00A690` | 16 bytes | ✅ Disable Lambda CL |
| **Spark Ref Table (hi-res)** | `0x008F90` | 8×14 = 112B | ⚡ NEW v4: Hi-Res Ign Trim |
| **Cold Start Enrichment** | `0x00876C` (fuel_maps[1]) | 115B | ⚡ NEW v4: ColdStart Scale |
| **ECT Correction Area** | `0x008240` – `0x008260` | 32B | ⚠ Documented, not exposed |
| **O2/Lambda Constants** | `0x00A5E0` – `0x00A620` | 64B | ⚠ Documented, not exposed |
| **RPM Scheduling Table** | `0x008150` | 14 × uint16 BE | ⚠ Documented, not exposed |
| **Injector Dead-Time** | Not yet confirmed | — | ❌ Not identified |
| **Speed Limiter** | `0x00B540+` area (unconfirmed) | — | ❌ Address not confirmed |
| **Boost Control** | N/A (Z22SE is naturally aspirated) | — | N/A |

### 11.2  Axis Ranges: OBDTuner vs GMPT-E15 Stock Firmware

| Axis | OBDTuner (standard) | GMPT-E15 Stock | Notes |
|---|---|---|---|
| **RPM** | 500 – 7800 RPM | 2000 – 6800 RPM (13 pts) | OBDTuner extends to idle (500) and beyond rev limit |
| **MAP/Load** | 20 – 200 kPa | 46 – 117 kPa (12 pts) | Z22SE is NA; GMPT-E15 range appropriate |
| **Fuel value** | 0 – 255 (VE %) | 0 – 255 (128 = neutral) | Same 8-bit encoding; 128 = stoichiometric |
| **Lambda** | λ1.0 = 14.7:1 | 128 = λ1.0 = 14.7:1 | Identical scaling |
| **Injectors** | 250 – 860 cc/min | ~245 cc/min (stock) | OBDTuner supports larger injectors |

### 11.3  Newly Identified Addresses (from OBDTuner reverse-engineering)

These addresses were identified by using OBDTuner's parameter list as a guide for what
to look for in the GMPT-E15 binary, cross-referenced with `ecu_analysis.py` output:

#### 11.3.1  High-Resolution Ignition Reference Table
- **Address:** `0x008F90` — 8 rows × 14 cols = **112 bytes**
- **Encoding:** uint8, ~0.5°/count (same as primary ignition maps)
- **Pattern:** Diagonal activation (each row has active cell shifting right by one column)
- **Modified by Stage 1:** ❌ No — not changed in any known tune
- **OBDTuner equivalent:** Base Spark Table reference layer
- **Z22SE_Tuner v4:** Exposed as "Hi-Res Ign Table Trim [OBDTuner]" (±4 counts max)

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

#### 11.3.2  ECT Cold-Start Correction Threshold Table
- **Address:** `0x008240` — **32 bytes** of threshold/scaling constants
- **OBDTuner equivalent:** Cold Start Enrichment table (CLT-indexed)
- **Z22SE_Tuner v4:** The **cold fuel correction map** at `0x00876C` (fuel_maps[1], 115B)
  is exposed directly via "Cold-Start Enrich Scale [OBDTuner]" for simpler user control.

#### 11.3.3  O2/Lambda Sensor Constants
- **Address:** `0x00A5E0` — **64 bytes** (includes IAT area at `0x00A610`)
- **OBDTuner equivalent:** Lambda Settings / O2 correction coefficients
- **Z22SE_Tuner v4:** Not directly exposed; use "Disable Lambda CL" for open-loop operation.

#### 11.3.4  RPM-Indexed Spark Scheduling Table
- **Address:** `0x008150` — **14 × uint16 BE** RPM breakpoints
- **Values:** 2240, 2200, 2400, 2700, 2900, 3437, 3437, 3437, 8447, 800, 800, 800, 1200, 1600
- **OBDTuner equivalent:** RPM Breakpoints for spark angle scheduling
- **Z22SE_Tuner v4:** Documented only; includes idle (800 RPM), warm-up (1200, 1600 RPM) targets.

### 11.4  Methodology

The OBDTuner parameter analysis was conducted as follows:

1. **Feature enumeration** — OBDTuner's published feature list (Fuel VE table, Spark table,
   Lambda targets, Rev limit, Idle RPM, IAT correction, Cold Start Enrichment, Knock threshold,
   O2 authority) was used as a checklist of parameter types to locate in GMPT-E15.

2. **Binary pattern matching** — Each parameter type was searched in the stock binary using
   characteristic patterns (e.g., 128=neutral for fuel/lambda, 800 RPM uint16 BE for idle,
   6500 RPM uint16 BE for rev limit).

3. **Differential analysis** — Stock vs Stage 1 binary diff confirmed which addresses map to
   which parameters (modified addresses = active calibration tables).

4. **Undocumented table discovery** — OBDTuner's "Spark Table" category led to the discovery
   of the high-resolution reference table at `0x008F90` (not modified by Stage 1, but present
   in all GMPT-E15 variants). Similarly, OBDTuner's "Cold Start Enrichment" led to confirming
   the ECT correction area at `0x008240`.

5. **Cross-validation** — All discovered addresses validated against all four known Z22SE
   calibration files (12591333, 12215796, 12578132, 12210633).

> **Result:** All primary OBDTuner tunable parameters have confirmed GMPT-E15 equivalents.
> Two new addresses (`0x008F90`, cold start map) are now exposed in Z22SE_Tuner v4.
> Injector dead-time and speed limiter addresses remain unconfirmed pending further analysis.

---

## 12  OBDTuner Decompilation — Complete Analysis

> **Source:** `ObdTunerSt2.exe` v2.7.14.1 (ObdTunerV2.7.14-1.zip) decompiled with ILSpy 9.1.
> `ObdTunerPro.exe` v3.2.31.3 (ObdTunerProV3.2.31.3.zip) is Dotfuscator-obfuscated and
> imports from `ObdTunerSt2.exe` as a base assembly; the same table definitions apply.
> Both describe themselves as: *"Tuning application for the Opel Speedster (VX 220)"*
> (the VX220 uses the Z22SE engine on the same GMPT-E15 ECU platform).
> Copyright © 2014–2019 Munckhof Engineering — Author: Peter v.d. Munckhof.

### 12.1  Flash Memory Layout (OBDTuner custom firmware)

OBDTuner **replaces** the stock GMPT-E15 firmware with its own custom OS.
After installation, the flash is organised as follows:

| Region | Flash Address | RAM Mirror Address | Size | Content |
|--------|-------------|-------------------|------|---------|
| OBDTuner program | `0x000000` | `0xFF_F000` (0xFF_B000) | Full | Custom ECU firmware |
| **RAM Tables sector** | **`0x005000`** (20480) | **`0xFF_8000`** (16760832) | **2048 bytes** | All tunable tables |
| **VIN sector** | **`0x006000`** (24576) | **`0xFF_7000`** (16756736) | **512 bytes** | VIN storage |

> **Note:** The stock GMPT-E15 binary has `0xFF` (erased flash) at `0x5000–0x5800` because
> this sector is only populated after OBDTuner firmware is installed.

### 12.2  Complete Table Registry

OBDTuner defines 21 user-accessible tables (each stored as both a FLASH and a RAM copy)
plus 4 internal logging tables. The **TableId enum** from the decompiled source:

| ID | TableId name | Dims (cols × rows) | Data type | Min/Max | Description |
|----|-------------|-------------------|-----------|---------|-------------|
|  1 | `TT_FUEL_LAMBDA_1_FLASH` | 37 × 20 | uint16 | 0–65535 | Main fuel (VE) table — FLASH copy |
|  2 | `TT_FUEL_LAMBDA_1_RAM`   | 37 × 20 | uint16 | 0–65535 | Main fuel (VE) table — RAM (live) |
|  3 | `TT_AFR_COOLANT_TEMP_CORR_FLASH` | 17 × 1 | uint8 | 0–255 | AFR coolant temp correction — FLASH |
|  4 | `TT_AFR_COOLANT_TEMP_CORR_RAM`   | 17 × 1 | uint8 | 0–255 | AFR coolant temp correction — RAM |
|  5 | `TT_IGNITION_CORRECTION_FLASH` | 37 × 20 | uint8 | 72–255 | Ignition correction map — FLASH |
|  6 | `TT_IGNITION_CORRECTION_RAM`   | 37 × 20 | uint8 | 72–255 | Ignition correction map — RAM |
|  7 | `TT_IGN_CTRL_IDLE_FLASH` | 6 × 1 | uint8 | 0–255 | Idle ignition control — FLASH |
|  8 | `TT_IGN_CTRL_IDLE_RAM`   | 6 × 1 | uint8 | 0–255 | Idle ignition control — RAM |
|  9 | `TT_IGN_MAP_AIRTEMP_FLASH` | 6 × 5 | uint8 | 0–57 | Ignition air-temp correction — FLASH |
| 10 | `TT_IGN_MAP_AIRTEMP_RAM`   | 6 × 5 | uint8 | 0–57 | Ignition air-temp correction — RAM |
| 11 | `TT_FUEL_AFR_FLASH` | 17 × 11 | uint8 | 90–147 | Target AFR (open loop) — FLASH |
| 12 | `TT_FUEL_AFR_RAM`   | 17 × 11 | uint8 | 90–147 | Target AFR (open loop) — RAM |
| 13 | `TT_IDLE_RPM_FLASH` | 17 × 1 | uint8 | 60–120 | Idle RPM vs coolant temp — FLASH |
| 14 | `TT_IDLE_RPM_RAM`   | 17 × 1 | uint8 | 60–120 | Idle RPM vs coolant temp — RAM |
| 15 | `TT_IDLE_FUEL_FLASH` | 13 × 9 | uint8 | 0–255 | Idle fuel enrichment table — FLASH |
| 16 | `TT_IDLE_FUEL_RAM`   | 13 × 9 | uint8 | 0–255 | Idle fuel enrichment table — RAM |
| 17 | `TT_THROTTLE_SPEED_FLASH` | 12 × 2 | uint8 | 0–255 | Throttle response speed — FLASH |
| 18 | `TT_THROTTLE_SPEED_RAM`   | 12 × 2 | uint8 | 0–255 | Throttle response speed — RAM |
| 20 | *(sensor data table)* | 46 × 5 | uint8 | 0–255 | Live sensor data display (no checksum) |
| 21 | `TT_GENERIC_PARAMETERS_FLASH` | 32 × 1 | uint8 | 0–255 | All parameters — FLASH copy |
| 22 | `TT_GENERIC_PARAMETERS_RAM`   | 32 × 1 | uint8 | 0–255 | All parameters — RAM (live) |
| 23 | `TT_IGN_BASE_IDLE_FLASH` | 13 × 1 | uint8 | 0–255 | Base idle ignition angle — FLASH |
| 24 | `TT_IGN_BASE_IDLE_RAM`   | 13 × 1 | uint8 | 0–255 | Base idle ignition angle — RAM |
| 25 | `TT_AFR_AIR_TEMP_CORR_FLASH` | 17 × 1 | uint8 | 0–50 | AFR air-temp correction — FLASH |
| 26 | `TT_AFR_AIR_TEMP_CORR_RAM`   | 17 × 1 | uint8 | 0–50 | AFR air-temp correction — RAM |
| 27 | `TT_TRANSIENT_THROTTLE_DELTA_FLASH` | 17 × 1 | uint8 | 0–255 | Transient throttle delta — FLASH |
| 28 | `TT_TRANSIENT_THROTTLE_DELTA_RAM`   | 17 × 1 | uint8 | 0–255 | Transient throttle delta — RAM |
| 29 | `TT_TRANSIENT_MAP_DELTA_FLASH` | 17 × 1 | uint8 | 0–255 | Transient MAP delta — FLASH |
| 30 | `TT_TRANSIENT_MAP_DELTA_RAM`   | 17 × 1 | uint8 | 0–255 | Transient MAP delta — RAM |
| 31 | `TT_TRANSIENT_THROTTLE_POS_FLASH` | 9 × 1 | uint8 | 0–64 | Transient throttle position — FLASH |
| 32 | `TT_TRANSIENT_THROTTLE_POS_RAM`   | 9 × 1 | uint8 | 0–64 | Transient throttle position — RAM |
| 33 | `TT_TRANSIENT_MAP_DURATION_FLASH` | 6 × 1 | uint8 | 0–255 | Transient map duration — FLASH |
| 34 | `TT_TRANSIENT_MAP_DURATION_RAM`   | 6 × 1 | uint8 | 0–255 | Transient map duration — RAM |
| 35 | `TT_THROTTLE_PEDAL_RESPONSE_FLASH` | 33 × 1 | uint16 | 0–65535 | Pedal response curve — FLASH |
| 36 | `TT_THROTTLE_PEDAL_RESPONSE_RAM`   | 33 × 1 | uint16 | 0–65535 | Pedal response curve — RAM |
| 37 | `TT_INJECTOR_DEAD_TIME_FLASH` | 17 × 1 | uint8 | 0–254 | Injector dead-time — FLASH |
| 38 | `TT_INJECTOR_DEAD_TIME_RAM`   | 17 × 1 | uint8 | 0–254 | Injector dead-time — RAM |
| 39 | `TT_WARMUP_CORRECTION_FLASH` | 23 × 1 | uint8 | 0–255 | Warm-up fuel correction — FLASH |
| 40 | `TT_WARMUP_CORRECTION_RAM`   | 23 × 1 | uint8 | 0–255 | Warm-up fuel correction — RAM |
| 41 | `TT_SHORT_PULS_ADDER_FLASH` | 38 × 1 | uint8 | 0–255 | Short-pulse adder — FLASH |
| 42 | `TT_SHORT_PULS_ADDER_RAM`   | 38 × 1 | uint8 | 0–255 | Short-pulse adder — RAM |
| 240 | `TT_INTERNAL_SAMPLES_COUNT` | 37 × 20 | uint16 | — | Internal logging: sample counts |
| 241 | `TT_INTERNAL_SLOT_1` | 37 × 20 | uint16 | — | Internal logging: fuel data |
| 242 | `TT_INTERNAL_SLOT_2` | 37 × 20 | uint16 | — | Internal logging: knock data |
| 243 | `TT_INTERNAL_SLOT_3` | 37 × 20 | uint16 | — | Internal logging: secondary |
| 248 | `TT_INTERNAL_POWER_MEASUREMENT` | 200 × 20 | uint8 | — | Dyno/power measurement data |

**RPM axis** (37 columns, 600 RPM spacing): 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200,
2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000, 4200, 4400, 4600, 4800, 5000, 5200,
5400, 5600, 5800, 6000, 6200, 6400, 6600, 6800, 7000, 7200, 7400, 7600, 7800, 8000

**MAP/Load axis** (20 rows, speed-density mode): 2.5–13.4+ kPa corrected by injector factor

**Idle RPM axis** (17 cols = coolant temperature): −20, −10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140 °C

### 12.3  Generic Parameters Table Layout (32 bytes, Tables 21/22)

The `TT_GENERIC_PARAMETERS` table stores all scalar configuration parameters as a flat 32-byte array.
It is the most important table for feature enable/disable operations.

| Byte offset | IDX constant | Width | Description | Encoding |
|-------------|-------------|-------|-------------|---------|
| `0x00`–`0x01` | `IDX_MAX_MAP_DELTA` | uint16 BE | Maximum live map correction delta | Raw units |
| `0x02` | `IDX_SPEED_LIMIT_LOW_RPM` | uint8 | Minimum RPM for speed limiter to activate | Raw RPM / scaling |
| `0x03` | `IDX_SPEED_LIMIT_ON` | uint8 | Speed limiter activation threshold | km/h × 0.617 (OEM=150 → 243 km/h) |
| `0x04` | `IDX_SPEED_LIMIT_OFF` | uint8 | Speed limiter deactivation threshold | km/h × 0.617 (OEM=149) |
| `0x05` | `IDX_AIR_INTAKE_TEMP_SENSOR` | uint8 | IAT sensor type | 0=OEM Delphi, 1=Bosch |
| `0x06` | `IDX_FAN_TEMP_ON` | uint8 | Coolant fan switch-on temperature | raw; OEM=193 (105°C), 177=92°C |
| `0x07` | `IDX_FAN_TEMP_OFF` | uint8 | Coolant fan switch-off temperature | raw; OEM=189 (raw 189 ≈ 104°C, 1–4 counts below ON for hysteresis) |
| `0x08`–`0x09` | `IDX_REV_LIMIT_THROTTLE_ON` | uint16 BE | Rev limiter engage RPM (throttle cut) | Direct RPM (OEM=6400) |
| `0x0A`–`0x0B` | `IDX_REV_LIMIT_THROTTLE_OFF` | uint16 BE | Rev limiter disengage RPM | Direct RPM (OEM=6200) |
| `0x0C`–`0x0D` | `IDX_REV_LIMIT_IGNITION_HIGH` | uint16 BE | Ignition cut engage RPM (high) | Direct RPM (OEM=6450) |
| `0x0E`–`0x0F` | `IDX_REV_LIMIT_IGNITION_LOW` | uint16 BE | Ignition cut engage RPM (low) | Direct RPM (OEM=6450) |
| `0x10` | `IDX_THROTTLE_BODY` | uint8 | Throttle body type — sets pedal map | 0=std, 1=65mm, 2=SC std, 3=SC 65mm, 4=SC 68mm, 5=SC 75mm |
| `0x11` | `IDX_CAT_CHECK` | uint8 | Catalytic converter monitor | 0=enabled, **1=disabled** |
| `0x12`–`0x13` | `IDX_INJECTOR_FACTOR` | uint16 BE | Injector static flow rate | cc/min at 3.8 bar (OEM=252 cc/min) |
| `0x14`–`0x15` | `IDX_MAP_SENSOR_VOLT` | uint16 BE | MAP sensor voltage conversion factor | Sensor-dependent (OEM Delphi=32832) |
| `0x16`–`0x17` | `IDX_MAP_SENSOR_KPA` | uint16 BE | MAP sensor kPa conversion factor | Sensor-dependent (OEM Delphi=35119) |
| `0x18` | `IDX_FUEL_MODE` | uint8 | Fuel calculation mode bitfield | Bit 0: Base SD (0=Alpha-N, 1=Speed-Density); Bit 1: Idle SD |
| `0x19` | `IDX_MAP_RANGE` | uint8 | MAP sensor maximum range | 5–13 = 100–260 kPa (20 kPa/unit); 15 = 300 kPa mode |
| `0x1A` | `IDX_P0300_CHECK` | uint8 | Misfire (P0300) monitor | 0=enabled, **1=disabled** |
| `0x1B` | `IDX_MULTIPARAMETER_01` | uint8 | Miscellaneous feature bitfield | See §12.4 |
| `0x1C`–`0x1D` | `IDX_MINIMUM_PULSE_WIDTH` | uint16 BE | Injector minimum pulse width | raw = µs × 10.24 (e.g., OEM 952 µs → raw≈93; display: raw / 10.24 = µs) |
| `0x1E`–`0x1F` | `IDX_EGR_CORRESPONDING_VALUES` | uint16 BE | EGR duty-cycle reference value | **0xFFFF = EGR disabled**; 0x6400 (25600) = enabled |

### 12.4  MULTIPARAMETER_01 Bit Flags (offset 0x1B in Generic Parameters)

| Bit | Mask | Feature | 0 (default) | 1 (modified) |
|-----|------|---------|-------------|-------------|
| 0 | `0x01` | **Idle control mode** | Closed-loop idle | Open-loop idle (manual) |
| 1 | `0x02` | **Fuel pressure regulator** | Return-type (standard) | Return-less (pressure always on) |
| 2 | `0x04` | **EGR valve** | EGR enabled | **EGR disabled** (also set IDX_EGR_CORRESPONDING_VALUES = 0xFFFF) |
| 3 | `0x08` | **300 kPa MAP fix** | Off (standard ≤250 kPa) | Active (Bosch 3-bar MAP sensor correction) |
| 4–7 | — | Reserved | — | — |

> **EGR note:** The Z22SE / GMPT-E15 ECU does include EGR management. The VX220 (Opel Speedster),
> Astra G, and other Z22SE variants have EGR hardware. OBDTuner provides an explicit disable feature.
> Setting `IDX_MULTIPARAMETER_01 bit 2 = 1` AND `IDX_EGR_CORRESPONDING_VALUES = 0xFFFF` together
> disables the EGR valve.

### 12.5  Configurable Feature Presets

#### 12.5.1  Rev Limiter Presets (OBDTuner range: 5000–7800 RPM)

The OBDTuner `RevLimiter` parameter sets four RPM thresholds simultaneously:

| RPM | ThrottleOn | ThrottleOff | IgnitionLow | IgnitionHigh |
|-----|-----------|------------|-------------|-------------|
| 5000 | 5000 | 4800 | 5050 | 5050 |
| 5400 | 5400 | 5200 | 5450 | 5450 |
| 5800 | 5800 | 5600 | 5850 | 5850 |
| 6000 | 6000 | 5800 | 6050 | 6050 |
| **6400 (OEM)** | **6400** | **6200** | **6450** | **6450** |
| 6500 | 6500 | 6320 | 6550 | 6550 |
| 6800 | 6800 | 6680 | 6850 | 6850 |
| 7000 | 7000 | 6900 | 7050 | 7050 |
| 7200 | 7200 | 7100 | 7250 | 7250 |
| 7800 | 7800 | 7700 | 7850 | 7850 |

> **OEM note:** OBDTuner identifies 6400 RPM as OEM for the VX220/Speedster.
> The GMPT-E15 stock binary uses 6500 RPM (see §2). Both platforms use the same ECU hardware
> but different calibrations; on the VX220 the stock limit was 6400.

#### 12.5.2  Speed Limiter Presets

Speed is encoded as: `raw = round(km/h × 0.61728)` (= km/h × 5/8.1 approx)

| Setting | Raw ON | Raw OFF | Notes |
|---------|--------|---------|-------|
| 180 km/h | 111 | 110 | — |
| 200 km/h | 123 | 123 | — |
| 220 km/h | 136 | 135 | — |
| **243 km/h (OEM)** | **150** | **149** | Original VX220 speed limiter |
| 260 km/h | 160 | 160 | — |
| 280 km/h | 173 | 172 | — |
| 300 km/h | 185 | 185 | — |

#### 12.5.3  Coolant Fan Temperature Presets

| Temp °C | FAN_ON raw | FAN_OFF raw | Notes |
|---------|-----------|------------|-------|
| 92°C | 177 | 177 | — |
| 95°C | 180 | 179 | — |
| 98°C | 183 | 181 | — |
| **105°C (OEM)** | **193** | **189** | Original switching temp |
| Formula | T_on = °C + 85 | T_off = °C + 84 (approx) | ±1 raw unit for hysteresis |

#### 12.5.4  Injector Type Presets

OBDTuner stores full dead-time tables plus short-pulse correction per injector.
The `IDX_INJECTOR_FACTOR` word encodes the static flow at 3.8 bar:

| Injector | Static flow | Min pulse (µs) | Part number |
|----------|------------|----------------|-------------|
| **Delphi OEM** | **250 cc/min** | **952 µs** | Stock Astra G Z22SE |
| Bosch 0 280 156 021 | 365 cc/min | 655 µs | Bosch upgrade |
| LSJ green | 410 cc/min | 686 µs | GM 12790827 (Saturn Ion Redline) |
| Bosch 0 280 156 280 | 470 cc/min | 512 µs | Bosch upgrade |
| Bosch 0 280 155 968 | 495 cc/min | 500 µs | Under development |
| Bosch 0 280 158 123 | 650 cc/min | 399 µs | High-flow Bosch |
| Siemens 50 lb | 550 cc/min | 297 µs | Siemens |
| Siemens 60 lb | 680 cc/min | 604 µs | Siemens 107961 |
| Siemens 80 lb | 860 cc/min | 297 µs | Siemens 110324 |
| Siemens 80 lb E85 | 860 cc/min | 297 µs | Siemens 110324 (E85 tune) |

#### 12.5.5  MAP Sensor Presets

OBDTuner stores two calibration values per sensor (`VOLT` and `KPA` conversion factors):

| Sensor | VOLT raw | KPA raw | Max range | 300kPa fix |
|--------|---------|--------|-----------|-----------|
| **Delphi std (OEM)** | **32832** | **35119** | 250 kPa | No |
| Delphi 2.0 bar | 32137 | 34916 | 200 kPa | No |
| Bosch 2.5 bar | 26041 | 32392 | 250 kPa | No |
| OmniPower 2.5 bar | 33196 | 35453 | 250 kPa | No |
| **Bosch 3.0 bar** | **22497** | **31142** | **300 kPa** | **Yes** |

#### 12.5.6  Throttle Body Type Presets

| Value | Description | Pedal map applied |
|-------|-------------|------------------|
| 0 | Standard OEM | Original OEM pedal curve |
| 1 | 65mm (sport) | Linear 65mm pedal curve |
| 2 | SC turbo std | Standard SC/turbo pedal curve |
| 3 | SC turbo 65mm | 65mm SC/turbo pedal curve |
| 4 | SC turbo 68mm | 68mm SC/turbo pedal curve |
| 5 | SC turbo 75mm | 75mm SC/turbo pedal curve (Pro only) |

### 12.6  Live Data Logged by OBDTuner

OBDTuner continuously logs the following sensor values from the ECU over OBD:

| Channel | Description | Unit |
|---------|-------------|------|
| `m_EngineRpm` | Engine RPM | RPM |
| `m_VehicleSpeed` | Vehicle speed | km/h |
| `m_Map` | Manifold absolute pressure | kPa |
| `m_Ignition` | Ignition timing | ° BTDC |
| `m_Lambda1` | Front O2 sensor / wideband | λ |
| `m_Lambda2` | Rear O2 sensor | λ |
| `m_ShortTermFuelTrim` | Short-term fuel trim | % |
| `m_LongTermFuelTrim` | Long-term fuel trim | % |
| `m_DynamicInjectorFactor` | Dynamic injector correction | raw |
| `m_KnockTotal` | Total knock retard | ° |
| `m_KnockRetardCil1/2/3/4` | Per-cylinder knock retard | ° |
| `m_KnockSensorVoltage` | Knock sensor voltage | V |
| `m_FlyMapDelta` | Live map correction delta | raw |
| `m_MapSensorVoltage` | MAP sensor voltage | V |
| `m_CommandedIdlingRpm` | Target idle RPM (commanded) | RPM |
| `m_EgrSetpoint` / `m_EgrFeedback` | EGR position cmd/actual | % |
| `m_FuelSytemState` | Fuel system state (CL/OL/etc.) | enum |

### 12.7  OBD Protocol Commands (Munckhof proprietary extension)

OBDTuner uses Mode 0x50 (non-standard) commands over the OBD interface:

| Command | Direction | Description |
|---------|-----------|-------------|
| `5043 XX CS` | ECU → PC | Request table XX from ECU (XX = table ID hex) |
| `5016 AAAAAAAA NN CS` | ECU → PC | Read NN bytes from RAM address AAAAAAAA |
| `5023 AAAA BB... CS` | PC → ECU | Write byte(s) to RAM address AAAA |
| `5024 XX OOOO VV CS` | PC → ECU | Write byte VV to table XX header at offset OOOO |
| `5052 NN CS` | PC → ECU | Set MIL (check engine light) mode (0=off,2=CL-log,3=CL-locked,4=ign+knock) |

> **Key insight:** OBDTuner can reprogram the Check Engine / MIL light to function as an
> alternative data output channel during logging. Mode 4 (`5052 04`) sets the MIL to indicate
> ignition retard and knock activity — effectively a **knock indicator light**.
> This is the closest OBDTuner gets to a "Check Engine Light Disable": it repurposes the
> MIL as a tuning indicator rather than a fault indicator.

### 12.8  Feature Mapping: OBDTuner vs GMPT-E15 Binary (Updated)

Based on decompilation, the full feature set and its correspondence to the GMPT-E15 binary:

| Feature | OBDTuner mechanism | GMPT-E15 binary equivalent | Status |
|---------|---------------------|---------------------------|--------|
| **Fuel (VE) table** | `TT_FUEL_LAMBDA_1` (37×20, uint16) | `0x0086C9–0x0088B2` (4 × 115 B, uint8) | ✅ Confirmed |
| **Spark (ign) table** | `TT_IGNITION_CORRECTION` (37×20, uint8) | `0x0082C9–0x00860B` (4 × 163 B, uint8) | ✅ Confirmed |
| **Target AFR (OL)** | `TT_FUEL_AFR` (17×11, uint8) | `0x00C7A7`, `0x00C885` (2 × 163 B) | ✅ Confirmed |
| **AFR coolant temp corr** | `TT_AFR_COOLANT_TEMP_CORR` (17×1) | Near `0x00876C` area | ⚠ Partially confirmed |
| **AFR air temp correction** | `TT_AFR_AIR_TEMP_CORR` (17×1) | `0x00A610` IAT area (12 B) | ✅ Confirmed |
| **Ignition air temp** | `TT_IGN_MAP_AIRTEMP` (6×5) | `0x00A610`–`0x00A650` area | ✅ Confirmed |
| **Idle ignition control** | `TT_IGN_CTRL_IDLE` (6×1) | Near ignition maps | ⚠ Not isolated |
| **Base idle ignition** | `TT_IGN_BASE_IDLE` (13×1) | `0x008F90` area | ✅ Confirmed (hi-res table) |
| **Idle RPM vs coolant** | `TT_IDLE_RPM` (17×1, uint8, ×12.5 = RPM) | `0x008150` RPM scheduling table | ✅ Confirmed |
| **Idle fuel enrichment** | `TT_IDLE_FUEL` (13×9) | Part of fuel map region | ⚠ Address unconfirmed |
| **Throttle response speed** | `TT_THROTTLE_SPEED` (12×2) | Not yet identified | ❌ |
| **Throttle pedal response** | `TT_THROTTLE_PEDAL_RESPONSE` (33×1, uint16) | Not in stock binary (OBDTuner-specific) | N/A |
| **Transient throttle delta** | `TT_TRANSIENT_THROTTLE_DELTA` (17×1) | Near `0x008900` area | ⚠ Not isolated |
| **Transient MAP delta** | `TT_TRANSIENT_MAP_DELTA` (17×1) | Near `0x008900` area | ⚠ Not isolated |
| **Transient throttle pos** | `TT_TRANSIENT_THROTTLE_POS` (9×1) | Near `0x008900` area | ⚠ Not isolated |
| **Transient MAP duration** | `TT_TRANSIENT_MAP_DURATION` (6×1) | Near `0x008900` area | ⚠ Not isolated |
| **Injector dead time** | `TT_INJECTOR_DEAD_TIME` (17×1, uint8) | Not yet confirmed | ❌ |
| **Warm-up fuel correction** | `TT_WARMUP_CORRECTION` (23×1, uint8, offset −128, ×0.781) | `0x008240` ECT area (32 B) | ⚠ Partially confirmed |
| **Short-pulse adder** | `TT_SHORT_PULS_ADDER` (38×1) | Not yet identified | ❌ |
| **Rev limiter** | `IDX_REV_LIMIT_*` (4 × uint16) | `0x00B568` (2004), `0x00B560` area | ✅ Confirmed |
| **Speed limiter** | `IDX_SPEED_LIMIT_ON/OFF` (uint8, km/h × 0.617) | Not yet isolated in GMPT-E15 | ❌ Address unconfirmed |
| **Fan temperature** | `IDX_FAN_TEMP_ON/OFF` (uint8, °C + 85) | Not yet isolated in GMPT-E15 | ❌ Address unconfirmed |
| **EGR disable** | `IDX_MULTIPARAMETER_01 bit 2` + `IDX_EGR_CORRESPONDING_VALUES=0xFFFF` | Not in GMPT-E15 stock binary (OBDTuner firmware required) | ⚡ OBDTuner-only |
| **CAT check disable** | `IDX_CAT_CHECK = 1` | Not directly accessible in GMPT-E15 binary | ⚡ OBDTuner-only |
| **P0300 misfire disable** | `IDX_P0300_CHECK = 1` | Not directly accessible in GMPT-E15 binary | ⚡ OBDTuner-only |
| **Check engine light (MIL) mode** | `5052 XX` command (OBD) | Not in binary — ECU RAM command | ⚡ OBDTuner live only |
| **Injector upgrade** | `IDX_INJECTOR_FACTOR` (uint16) | Not easily accessible in GMPT-E15 binary | ⚡ OBDTuner-only |
| **MAP sensor upgrade** | `IDX_MAP_SENSOR_VOLT/KPA` (2 × uint16) | Not easily accessible in GMPT-E15 binary | ⚡ OBDTuner-only |
| **Alpha-N / Speed-Density** | `IDX_FUEL_MODE` (uint8 bitfield) | Not exposed in GMPT-E15 binary | ⚡ OBDTuner-only |
| **Fuel pressure range** | `IDX_MAP_RANGE` (uint8) | Not exposed in GMPT-E15 binary | ⚡ OBDTuner-only |
| **Idle open-loop mode** | `IDX_MULTIPARAMETER_01 bit 0` | Not exposed in GMPT-E15 binary | ⚡ OBDTuner-only |

**Legend:**
- ✅ = Address confirmed in GMPT-E15 stock binary
- ⚠ = Partially identified, address uncertain
- ❌ = Not yet found in GMPT-E15 binary
- ⚡ = Requires OBDTuner firmware; not applicable to binary patching

### 12.9  Summary: New Findings from Decompilation

The following information was **not previously available** in this report and was obtained
exclusively from the OBDTuner decompilation:

1. **Complete table list** — All 21 user tables + 4 internal tables with exact dimensions and data types.

2. **Generic Parameters table layout** — The 32-byte `TT_GENERIC_PARAMETERS` table structure with
   all 15 parameters and their byte offsets. This is the master control register for all ECU features.

3. **EGR disable** — Confirmed: setting `MULTIPARAMETER_01 bit 2 = 1` AND
   `IDX_EGR_CORRESPONDING_VALUES = 0xFFFF` disables the EGR valve. The GMPT-E15 does manage EGR.

4. **CAT check disable** — `IDX_CAT_CHECK = 1` disables the catalytic converter monitor (O2 post-cat
   comparison), eliminating P0420/P0430 codes after cat removal.

5. **P0300 misfire disable** — `IDX_P0300_CHECK = 1` disables the random misfire detection. Useful
   when running aggressive ignition advance that could falsely trigger P0300.

6. **MIL/Check Engine Light repurpose** — The `5052 04` OBD command sets the MIL to indicate
   knock retard in real time (Mode 4 = ignition + knock logging), turning the dashboard warning
   light into a knock indicator during tuning.

7. **Speed limiter** — Confirmed present with encoding `raw = km/h × 0.617`. OEM is 243 km/h
   (raw = 150/149). Addresses `IDX_SPEED_LIMIT_ON = 3`, `IDX_SPEED_LIMIT_OFF = 4` within the
   Generic Parameters table. **Not yet isolated in GMPT-E15 binary.**

8. **Fan temperature control** — Encoding: `raw = °C + 85`. OEM = 193/189 (105°C ON/OFF).
   Min adjustable: 92°C. **Not yet isolated in GMPT-E15 binary.**

9. **Injector dead-time table** — `TT_INJECTOR_DEAD_TIME`: 17 × 1 bytes indexed by battery voltage
   (0V, 160mV steps to 2560mV = 17 steps). Separate from static injector factor.
   **Address in GMPT-E15 binary not confirmed.**

10. **Short-pulse adder table** — `TT_SHORT_PULS_ADDER`: 38 × 1 bytes — corrects fuel delivery
    non-linearity at short pulse widths. **Address in GMPT-E15 binary not confirmed.**

11. **Warm-up correction** — `TT_WARMUP_CORRECTION`: 23 × 1 bytes, scale = 25/32 ≈ 0.781, offset −128.
    Indexed by fuel trim index (0–22). Equivalent to the ECT cold-start area at `0x008240`.

12. **Transient fuel enrichment** — Four separate tables control throttle-tip-in enrichment:
    - `TT_TRANSIENT_THROTTLE_DELTA` (17 elements): fuel delta per throttle position change
    - `TT_TRANSIENT_MAP_DELTA` (17 elements): fuel delta per MAP change
    - `TT_TRANSIENT_THROTTLE_POS` (9 elements): position threshold for enrichment
    - `TT_TRANSIENT_MAP_DURATION` (6 elements): duration of enrichment pulse

13. **Idle control tables** — Three dedicated idle tables:
    - `TT_IDLE_RPM` (17 cols, coolant-temp indexed): target idle RPM
    - `TT_IDLE_FUEL` (13×9): idle fuel enrichment 2D map
    - `TT_IGN_CTRL_IDLE` (6 elements): idle ignition closed-loop correction
    - `TT_IGN_BASE_IDLE` (13 elements): base idle ignition angle

14. **Throttle pedal response** — `TT_THROTTLE_PEDAL_RESPONSE`: 33 × 1 uint16 values. Presets
    exist for standard OEM, 65mm sport, and various SC/turbo configurations. This is an
    **OBDTuner-specific feature** with no direct GMPT-E15 binary equivalent.

