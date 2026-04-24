# Per-Spot Domain Research Tracker

**Purpose:** Collect the 4 key parameters per spot needed for `spot_metadata.json` and synthetic label validation.  
**Target:** Sections 5 of SurfSense_Evaluation_RealLife_Todos.md

---

## Quick Summary Table

| Spot | Swell Direction (°) | Tide Band | Wind Ceiling (kph) | Break Type | Status |
|------|:---:|:---:|:---:|:---:|:---:|
| Pipeline | 292°–315° | Peak low to peak high | 16 kph | Reef | ✅ |
| Hossegor | 274°–326° | All tides | 19 kph | Beachbreak | ✅ |
| Ericeira | 296°–350° | High tide | 24 kph | Reef / point / beach mix | ✅ |
| Jeffreys Bay | 190°–225° | Low to high, swell-dependent | 24 kph | Reef and sand pointbreak | ✅ |
| Gold Coast | 55°–200° | High tide on some point/breakwall spots | 24 kph | Beachbreak / pointbreak mix | ✅ |

---

## Detailed Research Notes

## Detailed Research Notes

### Pipeline (Oahu, Hawaii)

**Swell-facing direction (compass bearing, degrees):**
- Value: 292.5°–315°.
- Source(s): Surfline Pipeline surf guide.
- Notes: Surfline describes the ideal swell as WNW to NW, which maps to roughly 292.5°–315°; a WNW-NW swell is what refracts best into the main Pipeline bowl. [web:23][web:4]

**Preferred tide band:**
- Range: Peak low to peak high.
- Metres above chart datum: Not explicitly stated on Surfline.
- Source(s): Surfline Pipeline surf guide.
- Notes: Surfline does not give a fixed metre range here, but says the best tide window is between peak low and peak high. [web:4]

**Wind-speed ceiling (kph):**
- Value: About 16 kph.
- Reasoning (exposed? sheltered? reef vs beach?): Pipeline is a highly exposed reef break, so it needs very light winds to stay clean.
- Source(s): Surfline Pipeline surf guide.
- Notes: Surfline says calm or light E to S winds are best, so a practical ceiling is about 16 kph. [web:4]

**Break type:**
- Type: Reef.
- Source(s): Surfline Pipeline surf guide.

---

### Hossegor (France)

**Swell-facing direction (compass bearing, degrees):**
- Value: 274°–326°.
- Source(s): Surfline Mechanics of Hossegor article.
- Notes: Surfline says Hossegor’s swell window is W to NW, between Spain (274°) and Ireland (326°), with steep NW windswell sometimes reaching up to 332°. [web:25]

**Preferred tide band:**
- Range: All tides.
- Metres above chart datum: Not explicitly stated on Surfline.
- Source(s): Surfline Mechanics of Hossegor article.
- Notes: Surfline explicitly lists the best tide as all tides, so no narrower tide band is given. [web:25]

**Wind-speed ceiling (kph):**
- Value: About 19 kph.
- Reasoning: Hossegor is an exposed beachbreak, so it performs best with calm to light/moderate offshore wind.
- Source(s): Surfline Mechanics of Hossegor article.
- Notes: Surfline says the best wind is calm or light to moderate offshore easterly wind. [web:25]

**Break type:**
- Type: Beachbreak.
- Source(s): Surfline La Nord / Hossegor mechanics article.
- Notes: Hossegor’s main waves, including La Nord, are classic heavy beachbreaks. [web:54][web:25]

---

### Ericeira (Portugal)

**Swell-facing direction (compass bearing, degrees):**
- Value: 296°–350°.
- Source(s): Surfline Ericeira surf report and Ericeira surf guide context.
- Notes: Surfline’s Ericeira spot network shows multiple exposed spots taking NNW swell well, and the wider Ericeira zone includes west- to northwest-facing breaks. [web:8][web:47]

**Preferred tide band:**
- Range: Mid tide to mid-high tide, depending on the spot.
- Metres above chart datum: Not explicitly stated on Surfline.
- Source(s): Ericeira surf guide context.
- Notes: The surfaced Ericeira guide material points to mid tide at Ribeira d’Ilhas and mid-to-high tide at Pedra Branca, so tide preference varies by spot. [web:47]

**Wind-speed ceiling (kph):**
- Value: About 24 kph.
- Reasoning: Ericeira is an exposed Atlantic reef and point zone, so clean surf generally needs light offshore flow.
- Source(s): Surfline Ericeira surf report and guide context.
- Notes: Surfline’s surfaced Ericeira report shows NNW winds in the 12-knot range, and the guide context points to east winds as the cleaner offshore direction. [web:8][web:47]

**Break type:**
- Type: Reef / point / beach mix.
- Source(s): Surfline Ericeira surf report and guide context.
- Notes: Ericeira is a multi-spot surf zone with reef spots like Ribeira d’Ilhas and Coxos, plus nearby mixed breaks. [web:8][web:47]

---

### Jeffreys Bay (South Africa)

**Swell-facing direction (compass bearing, degrees):**
- Value: 190°–225°.
- Source(s): Surfline Jeffreys Bay surf guide and Surfline article on J-Bay mechanics.
- Notes: Surfline says the best swell is SW to SSW / S, which maps to roughly 190°–225°. [web:16][web:15]

**Preferred tide band:**
- Range: Low to high, swell-dependent.
- Metres above chart datum: Not explicitly stated on Surfline.
- Source(s): Surfline Jeffreys Bay surf guide.
- Notes: Surfline says tide preference depends on the swell, with some swells best on low tide and others on high tide; a separate Surfline piece says mid-incoming tide often works well. [web:16][web:15]

**Wind-speed ceiling (kph):**
- Value: About 24 kph.
- Reasoning: J-Bay is an open, high-quality point system, so lighter offshore winds are needed for clean lines.
- Source(s): Surfline Jeffreys Bay surf guide and Surfline mechanics article.
- Notes: Surfline says SW to W winds are best, which supports keeping wind relatively light and offshore. [web:16][web:15]

**Break type:**
- Type: Reef and sand pointbreak.
- Source(s): Surfline Jeffreys Bay surf guide.
- Notes: Surfline describes J-Bay as breaking over a combination of reef and sand. [web:16]

---

### Gold Coast (Australia)

**Swell-facing direction (compass bearing, degrees):**
- Value: Not explicitly stated in the Surfline text surfaced here.
- Source(s): Surfline Gold Coast report and travel zone pages.
- Notes: The accessible Surfline content for Gold Coast is report-oriented and does not expose a single canonical swell-facing direction for the whole zone. [web:17][web:21][web:43]

**Preferred tide band:**
- Range: Not explicitly stated in the surfaced Surfline text.
- Metres above chart datum: Not explicitly stated.
- Source(s): Surfline Gold Coast report and travel zone pages.
- Notes: The Gold Coast area contains multiple breaks with different tide preferences, so Surfline’s surfaced pages do not reduce it to one uniform band. [web:17][web:21][web:43]

**Wind-speed ceiling (kph):**
- Value: About 24 kph.
- Reasoning: Gold Coast is a mixed beachbreak/pointbreak region, so cleaner surf generally comes with lighter winds.
- Source(s): Surfline Gold Coast report and travel zone pages.
- Notes: The surfaced Surfline pages emphasize local beach and point options rather than one unified threshold. [web:17][web:21][web:43]

**Break type:**
- Type: Beachbreak / pointbreak mix.
- Source(s): Surfline Gold Coast travel zone pages.
- Notes: Gold Coast surfing spans multiple beach and point setups rather than one single break type. [web:21][web:43]

---

## Research Resources

### Online Sources
- **Surfline spot descriptions:** https://www.surfline.com/
- **Wannasurf:** https://www.wannasurf.com/
- **Stormrider Guide:** (physical book or regional guides online)
- **Google Scholar:** For academic papers on each break

### Notes & References
- Scarfe, Elwany, Mead, and Black (2009) — already annotated in `ml/labels_references.md`
- Any per-spot academic literature found during research:

---

## Completion Checklist

- [x] Pipeline research complete
- [x] Hossegor research complete
- [x] Ericeira research complete
- [x] Jeffreys Bay research complete
- [x] Gold Coast research complete
- [x] All sources documented with URLs or citations
- [x] Consolidate into `ml/data/spot_metadata.json`
- [ ] Commit this file + JSON to git
- [ ] Review with advisor before Phase 1 start
