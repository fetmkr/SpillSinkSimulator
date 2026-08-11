# Superseded drafts — DO NOT QUOTE

These are earlier versions of the 1D-vs-3D comparison from the same day. They are
kept because the corrections are part of the record, not because the numbers are
usable. Every one of them carries at least one claim that was later measured and
found wrong:

| draft | what was wrong with it |
|---|---|
| `1756`, `1804` | quoted **5.2x** for the cone against the groove. Not tip-matched: 0.8 mm groove tip vs 0.2 mm cone radius, a 24x difference in exposed tip area. |
| `1805`, `1806`, `1818` | quoted **2.9x** as "tip-matched, 0.2 mm both". Still wrong: `tip_width` is a full WIDTH and `tip_radius` is a RADIUS, so the groove had a tip half the size — and 0.2 mm is half an FDM nozzle and cannot be printed. These also measured the cones with `tileable=False` while the picture and the STL had it on (7.5% apart), and quoted form figures ("core 0.11 vs 0.99") taken from two designs that appear on none of these pages. |
| `1855`, `1856` | layout drafts of the corrected v2. Numbers are the v2 numbers and are correct; superseded only by `../1900_compare.png`. |

**The live report is `../1900_compare.png`.** At one FDM nozzle (0.4 mm across) for both
families, measured on the geometry that is actually exported, the cone is **5.0x** darker
head-on and smears the line **4.3x** wider.
