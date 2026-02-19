#!/usr/bin/env python3
import struct, os, sys

BASE = "/home/zewy/Desktop/Z22SEECUMapping"
FILES = {
    "Stock_2004":   BASE+"/OpelAstraG_Z22SE_GMPT-E15_Stock.bin",
    "Astra2004_EB": BASE+"/Astra G 2.2 SRi Z22SE GMPT 2004 Hw 12210453 EB.ORI",
    "Astra2001_BC": BASE+"/Astra G 2.2 SRi Z22SE GMPT 2001 Hw 09391283 BC.ORI",
    "Speedster_BZ": BASE+"/Opel Speedster 2.2 147hp Z22SE Hw 12202073 BZ.ORI",
}

HDR=7; NCOLS=13; NROWS=12
IGN_MAPS  = [0x82C9, 0x83A9, 0x8489, 0x8569]
FUEL_MAPS = [0x86C9, 0x876C, 0x880F, 0x88B2]

def u16(b,a): return struct.unpack_from('>H',b,a)[0]
def ign_row(b,base,row): return [b[base+HDR+row*NCOLS+c] for c in range(NCOLS)]

out = []
bufs = {}
for name,path in FILES.items():
    b = bytearray(open(path,'rb').read())
    bufs[name] = b

out.append("="*72)
out.append("  Z22SE GMPT-E15 — Full File Comparison")
out.append("="*72)

for name,b in bufs.items():
    pn    = b[0x800C:0x8014].decode('ascii','replace').strip('\x00 \xff')
    cal04 = b[0x602C:0x6041].decode('ascii','replace').strip('\x00 \xff')
    cal01 = b[0x402C:0x4041].decode('ascii','replace').strip('\x00 \xff')
    pb    = b[0x8141:0x8143]
    pin   = f"{pb[0]>>4}{pb[0]&0xF}{pb[1]>>4}{pb[1]&0xF}"
    rev   = u16(b,0xB568); rev2 = u16(b,0xB56A); hyst = u16(b,0xB570)
    idle  = u16(b,0x8162)
    rpm_axis  = [u16(b,0x81B0+i*2) for i in range(13)]
    load_axis = list(b[0x8290:0x829C])
    kn    = b[0x8D81]
    iat   = list(b[0xA610:0xA620])

    # Ignition maps row0 (WOT), row9 (overrun)
    ign_rows = {}
    for mi,ma in enumerate(IGN_MAPS):
        ign_rows[mi] = {
            'wot':   ign_row(b,ma,0),
            'wot4':  ign_row(b,ma,4),
            'pl5':   ign_row(b,ma,5),
            'pl8':   ign_row(b,ma,8),
            'over9': ign_row(b,ma,9),
            'over11':ign_row(b,ma,11),
        }
    # Lambda @0xC7A7
    lam_wot  = ign_row(b,0xC7A7,0)
    lam_over = ign_row(b,0xC7A7,9)

    out.append(f"\n{'─'*72}")
    out.append(f"  FILE:       {name}  ({len(b):,} bytes)")
    out.append(f"  Part#:      '{pn}'")
    out.append(f"  Cal@602C:   '{cal04}'")
    out.append(f"  Cal@402C:   '{cal01}'")
    out.append(f"  PIN:        {pin}  (raw: {pb.hex()})")
    out.append(f"  Rev limit:  {rev}/{rev2} RPM  hysteresis: {hyst} RPM")
    out.append(f"  Idle RPM:   {idle}")
    out.append(f"  Knock thr:  {kn} (0x{kn:02X})  [100=safe,40=aggr,0xFF=off]")
    out.append(f"  RPM axis:   {rpm_axis}")
    out.append(f"  Load axis:  {load_axis}")
    out.append(f"  IAT(0xA610): {iat}")
    out.append(f"  Ign#1 row0  WOT  (117kPa): {ign_rows[0]['wot']}")
    out.append(f"  Ign#1 row4  WOT  ( 94kPa): {ign_rows[0]['wot4']}")
    out.append(f"  Ign#1 row5  PL   ( 91kPa): {ign_rows[0]['pl5']}")
    out.append(f"  Ign#1 row8  PL   ( 77kPa): {ign_rows[0]['pl8']}")
    out.append(f"  Ign#1 row9  OVR  ( 63kPa): {ign_rows[0]['over9']}")
    out.append(f"  Ign#1 row11 OVR  ( 46kPa): {ign_rows[0]['over11']}")
    out.append(f"  Lambda WOT  row0: {lam_wot}")
    out.append(f"  Lambda OVR  row9: {lam_over}")

# Cross-file diff summary
out.append(f"\n\n{'='*72}")
out.append("  DIFF SUMMARY vs Stock_2004")
out.append("="*72)

stock = bufs["Stock_2004"]
for name,b in bufs.items():
    if name == "Stock_2004": continue
    diffs = [(i,stock[i],b[i]) for i in range(min(len(stock),len(b))) if stock[i]!=b[i]]
    # Cluster into regions
    regions = []; s0=None; e0=None
    for addr,sv,bv in diffs:
        if s0 is None: s0=addr; e0=addr
        elif addr-e0<=4: e0=addr
        else:
            regions.append((s0,e0))
            s0=addr; e0=addr
    if s0: regions.append((s0,e0))

    total_bytes = sum(e-s+1 for s,e in regions)
    out.append(f"\n  vs {name}: {len(diffs)} changed bytes, {len(regions)} regions, {total_bytes} total span")

    KNOWN = [
        (0x82C9,0x836B,"Ign Map #1"),
        (0x83A9,0x844B,"Ign Map #2"),
        (0x8489,0x852B,"Ign Map #3"),
        (0x8569,0x860B,"Ign Map #4"),
        (0x86C9,0x8742,"Fuel Map #1"),
        (0x876C,0x87DE,"Fuel Map #2"),
        (0x880F,0x8881,"Fuel Map #3"),
        (0x88B2,0x8924,"Fuel Map #4"),
        (0x896B,0x89AA,"Ign Trim #1"),
        (0x89CE,0x89E3,"Ign Trim #2"),
        (0xC7A7,0xC849,"Lambda Map #1"),
        (0xC885,0xC927,"Lambda Map #2"),
        (0xC5BD,0xC777,"Lambda 2001"),
        (0xB568,0xB57A,"Rev Limiter"),
        (0x8141,0x8145,"PIN"),
        (0x8000,0x8010,"Checksum/PN"),
        (0x602C,0x6042,"CalID 2004"),
        (0x402C,0x4042,"CalID 2001"),
        (0x8162,0x816C,"Idle RPM"),
        (0x8D80,0x8DC0,"Knock area"),
        (0xA610,0xA650,"IAT area"),
        (0x81B0,0x81D0,"RPM axis"),
        (0x8290,0x82A0,"Load axis"),
    ]

    for s,e in regions:
        size = e-s+1
        tag = ""
        for ks,ke,kn in KNOWN:
            if ks<=s<=ke or ks<=e<=ke or (s<ks and e>ke):
                tag = f"  ← {kn}"; break
        changed = [(i,stock[i],b[i]) for i in range(s,e+1) if stock[i]!=b[i]]
        if size<=32:
            detail = "  | " + "  ".join(f"[0x{i:05X}]:{sv}→{bv}({bv-sv:+d})" for i,sv,bv in changed[:8])
            if len(changed)>8: detail += f"  …+{len(changed)-8}more"
        else:
            deltas = [bv-sv for _,sv,bv in changed]
            uniq = sorted(set(deltas))
            avg = sum(deltas)/len(deltas)
            detail = f"  | Δ values:{uniq[:8]}  avg:{avg:+.1f}  n={len(changed)}"
        out.append(f"    0x{s:05X}–0x{e:05X}  ({size:4d}B){tag}")
        out.append(f"         {detail}")

text = "\n".join(out)
print(text)
with open("/tmp/ori_analysis.txt","w") as f:
    f.write(text)
print("\nDone. Written to /tmp/ori_analysis.txt")

