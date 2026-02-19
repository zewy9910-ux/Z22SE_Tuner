# Z22SE Tuner Quick Reference

## 🚀 Quick Start

1. **Install**: `pip install PyQt6`
2. **Run**: `python Z22SE_Tuner.py`
3. **Load** your stock ECU .bin file
4. **Apply** Stage 1 tune
5. **Save** modified file
6. **Flash** to ECU using your preferred tool

---

## 📊 Tuning Profiles Comparison

| Profile | Ignition | Fuel | Lambda | Rev Limit | Power Gain | Fuel Grade | Hardware |
|---------|----------|------|--------|-----------|------------|------------|----------|
| **Stage 1** | +2 WOT, +1 PL | +2 WOT, +1 PL | -7 WOT | 6500 RPM | +15-20 HP | 95+ RON | Stock OK |
| **Stage 1+** | +3 uniform | +3 uniform | -9 WOT, -3 PL | 6500 RPM | +20-25 HP | 98+ RON | Stock OK |
| **Stage 2** | +5 WOT, +3 PL | +4 WOT, +2 PL | -11 WOT, -5 PL | 6800 RPM | +25-30 HP | 98+ RON | Exhaust rec. |

**Legend**: WOT = Wide Open Throttle, PL = Part Load

---

## 🎯 ECU Memory Map (Most Important Addresses)

### Tables Modified by Stage 1

| Map | Address | Size | What It Does |
|-----|---------|------|--------------|
| Ignition Map #1 | `0x0082C9` | 163 B | Primary timing advance |
| Ignition Map #2 | `0x0083A9` | 163 B | Cold-start timing |
| Ignition Map #3 | `0x008489` | 163 B | Part-load timing |
| Ignition Map #4 | `0x008569` | 163 B | WOT timing reference |
| Fuel Map #1 | `0x0086C9` | 115 B | Warm fuel correction |
| Fuel Map #2 | `0x00876C` | 115 B | Cold fuel correction |
| Fuel Map #3 | `0x00880F` | 115 B | Part-load fuel |
| Fuel Map #4 | `0x0088B2` | 115 B | WOT fuel |
| Lambda Map (primary) | `0x00C7A7` | 163 B | AFR target map |
| Lambda Map (backup) | `0x00C885` | 163 B | AFR duplicate |

### Critical Parameters

| Parameter | Address | Format | Stock Value | Notes |
|-----------|---------|--------|-------------|-------|
| **Rev Limit** | `0x00B568` | uint16 BE | 6500 RPM | Fuel cut activation |
| **PIN Code** | `0x008141` | BCD | 3305 | Immobilizer code |
| **Part Number** | `0x00800C` | ASCII | 12591333 | ECU hardware ID |

---

## ⚙️ Scaling Factors

- **Ignition**: 1 count ≈ 0.5° timing
- **Fuel**: 1 count ≈ 0.78% (128 = 100%)
- **Lambda**: value × (14.7 / 128) = AFR
  - 128 = λ1.0 = 14.7:1 (stoichiometric)
  - 115 = λ0.9 = 13.2:1 (rich, typical WOT)
  - 110 = λ0.86 = 12.6:1 (very rich)

---

## 🔧 Supported ECUs

| Part Number | Cal ID | Year | Vehicle |
|-------------|--------|------|---------|
| 12591333 | W0L0TGF675B000465 | 2004 | Astra G 2.2 |
| 12215796 | W0L0TGF071B022321 | 2001 | Astra G 2.2 |

**ECU Platform**: GMPT-E15 (Delco/Delphi)  
**File Size**: 512 KB (524,288 bytes)

---

## ⚠️ Critical Safety Checklist

Before flashing:
- [ ] **Backup** original ECU file (multiple copies!)
- [ ] **Verify** file size is exactly 512 KB
- [ ] **Check** ECU part number matches
- [ ] **Ensure** stable 12V power (use battery charger)
- [ ] **Use** quality flash tool (MPPS, Kess, K-TAG, etc.)

After flashing:
- [ ] **Monitor** for knock/ping under load
- [ ] **Check** AFR with wideband O2 sensor (if available)
- [ ] **Verify** smooth idle and throttle response
- [ ] **Test drive** cautiously at first
- [ ] **Inspect** spark plugs after 50-100 miles

---

## 🎬 Pop & Bang Effect

**Requirements**:
- Performance exhaust (stock too restrictive)
- Cat-back or decat recommended
- Works with any Stage profile

**Settings**:
- Pop & Bang: -12° overrun retard, +4 fuel
- Burble (aggressive): -20° overrun retard, +7 fuel

**Effect**: Exhaust pops and crackles on deceleration

---

## 📏 RPM Limit Examples

| RPM | Hex Value | Use Case |
|-----|-----------|----------|
| 6500 | `0x1964` | Stock / Stage 1 |
| 6600 | `0x19C8` | Conservative raise |
| 6700 | `0x1A2C` | Moderate raise |
| 6800 | `0x1A90` | Stage 2 (tested) |
| 7000 | `0x1B58` | Aggressive (valve float risk!) |

⚠️ **Warning**: Do not exceed 7000 RPM on stock valve springs!

---

## 📱 Tool Compatibility

**Confirmed Working**:
- MPPS (read/write)
- Kess v2 (read/write)
- K-TAG (read/write via BDM)
- Alientech (read/write)
- Galletto (read/write)

**Communication Methods**:
- OBD-II (K-line) - slower but easier
- BDM (direct) - faster, requires ECU opening

---

## 🔍 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Engine won't start | Wrong ECU file | Flash back to stock |
| Rough idle | Too much ignition advance | Reduce or use Stage 1 instead |
| Knock/ping | Timing too aggressive or low-octane fuel | Use 98 RON or reduce timing |
| Poor fuel economy | Lambda too rich | Normal for Stage 2, use Stage 1 for economy |
| Check engine light | DTC triggered | Clear codes, disable DTCs if persistent |
| Rev limit not working | Wrong address modified | Verify 0x00B568 was changed |

---

## 📊 Expected Results by Stage

### Stage 1 (Stock Hardware)
- **Power**: 147 HP → 165 HP (+18 HP)
- **Torque**: 203 Nm → 218 Nm (+15 Nm)
- **0-100 km/h**: ~9.5s → ~9.0s
- **Fuel economy**: -5% (use 95 RON minimum)

### Stage 2 (With Exhaust)
- **Power**: 147 HP → 175 HP (+28 HP)
- **Torque**: 203 Nm → 228 Nm (+25 Nm)
- **0-100 km/h**: ~9.5s → ~8.6s
- **Fuel economy**: -10% (use 98 RON required)

---

## 🛡️ Warranty & Legal

- ❌ **Voids** manufacturer warranty
- ⚠️ May affect emissions compliance
- 🏁 **Track use only** where modifications restricted
- 📋 Check local laws before modifying

---

## 🔗 Resources

- **Full Documentation**: [README.md](README.md)
- **ECU Mapping**: [ECU_Mapping_Report.md](ECU_Mapping_Report.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **GitHub**: [zewy9910-ux/Z22SE_Tuner](https://github.com/zewy9910-ux/Z22SE_Tuner)

---

*Last updated: 2026-02-19*
