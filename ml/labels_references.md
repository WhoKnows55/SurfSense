# Synthetic Score: Reference Map to Scarfe et al. (2009)

**Primary reference.** Scarfe, B.E., Healy, T.R., Rennie, H.G. (2009).
*Research-Based Surfing Literature for Coastal Management and the Science of
Surfing: A Review.* Journal of Coastal Research, 25(3), 539-557.

**Attribution note.** The task brief names the paper as "Scarfe, Elwany, Mead,
and Black (2009)". That author combination is the 2003a conference paper
(*The science of surfing waves and surfing breaks: a review*) listed in the
2009 bibliography, not the 2009 review itself. The 2009 paper reuses the same
physics discussion, so the grounding below applies in either case, but the
thesis citation should be corrected to one of:
Scarfe, Healy, Rennie (2009) for the review framing, or
Scarfe, Elwany, Mead, Black (2003a) for the earlier conference treatment.

## Formula under review

From `app/agents/condition_agent.py`:

```python
wave_score     = min(wave_avg / max_wave, 1.0) * 40
period_score   = min(swell_period / 14, 1.0) * 30
wind_penalty   = max(0, (wind_speed - max_wind) / 10) * 20
offshore_bonus = 10 if is_offshore else 0
score          = wave_score + period_score - wind_penalty + offshore_bonus
# Unsafe override: wind_speed > 1.5*max_wind OR wave_avg > 1.5*max_wave
```

## Term-by-term grounding

### 1. `wave_score` (weight 40)

*What it encodes.* Wave height scaled to the surfer's skill-level maximum,
saturating at the threshold.

*Grounding.*
- p.544, Surfing Wave Parameters section: breaking wave height H_B is
  identified as a primary descriptor and is explicitly said to dictate the
  skill level required to ride the wave. This is the strongest textual
  support for wave height being the dominant term.
- p.544: the surfable range from Mack (2003) is cited as roughly 1 to 20 m,
  with smaller waves rideable by lighter or more skilled surfers. This
  justifies a skill-conditioned cap rather than a single global cutoff.
- Figure 6 (p.546) and Table 2 (p.547) map discrete skill ranks to wave
  height bands (rank 3-4 near 2.5 m, rank 5-7 near 3 m). These are the
  empirical shape behind the per-skill `max_wave` constants in
  `SkillLevelThresholds`.

*Why it carries the largest weight.* The paper treats H_B as primary
throughout; our weighting mirrors that emphasis.

### 2. `period_score` (weight 30)

*What it encodes.* Swell period scaled against an ideal reference of 14 s,
with linear growth below and saturation above.

*Grounding.*
- p.546, Winds paragraph: distant-origin surfing waves arrive with long
  periods (above about 8 s is flagged as favorable). This is direct
  support for period being a monotonically positive term.
- p.547, Headland or point break definition: refraction around a point
  filters out short-period energy, leaving longer-period waves that are
  more likely to be surfable. Reinforces the "longer period, higher
  surfability" direction of the term.

*Caveat worth flagging in the thesis.* The paper anchors "favorable" at
around 8 s; the formula saturates at 14 s. The 14 s choice reflects
groundswell quality for world-class breaks but is an engineering choice,
not a number the paper states.

### 3. `wind_penalty` (weight 20)

*What it encodes.* A linear cost for wind speed above the skill-level
threshold.

*Grounding.*
- p.546, Winds paragraph: cross-shore and strong winds are stated to
  detract from surfing wave quality. Direct justification for a monotonic
  penalty above a threshold.
- p.546: Mack (2003) is cited for a directionless maximum usable wind
  around 5 m/s (roughly 18 km/h), which anchors the intermediate
  `max_wind` default of 20 km/h.

*Caveat.* The paper distinguishes onshore from offshore winds with
asymmetric effects: onshore winds make waves break less predictably
without necessarily increasing required skill, while strong offshore
winds raise required skill and flatten weak swells. A single scalar
penalty collapses both regimes and is lossy. A forward-looking fix is
to split the penalty by wind-wave relative direction, which the ML
model can learn from sin/cos wind-direction features.

### 4. `offshore_bonus` (+10 flat)

*What it encodes.* A fixed positive adjustment when wind is classified
as offshore.

*Grounding.*
- p.546: an offshore wind is described as steepening the wave face and
  producing plunging (barreling) waves at some breaks.
- p.546: a light offshore wind is noted to groom the face smoother
  (Schrope, 2006).
- p.546: Chen, Kaihatu, and Hwang (2004) and Feddersen and Veron (2005)
  are cited for the finding that offshore winds delay breaking via
  modification of the breaker-to-depth ratio gamma_b, producing larger
  breaking heights. This is the physical mechanism the +10 bonus is
  acting as a crude proxy for.

*Important caveat.* The same page reports (via Feddersen and Veron 2005)
that offshore winds *increase* the skill level required to surf a given
wave, because gamma_b can change by up to 100%. A blanket +10 therefore
overstates goodness for beginners when offshore winds are strong. A
forward-looking fix is to gate or scale the bonus by wind magnitude
and skill, or to let the ML model learn the non-monotonic interaction.

### 5. Unsafe override (1.5x threshold)

*What it encodes.* A hard "unsafe" label when either wave height or
wind speed exceeds 1.5 times the skill-level threshold.

*Grounding.*
- Figure 6 (p.546): rank 8-9 waves are described as being ridden under
  extreme and dangerous conditions, and the ranked scheme implies a
  cliff in skill requirement at the top of each band.
- Table 2 (p.547): skill-level caps on wave height are discrete;
  exceeding them by a wide margin sits outside the validated design
  envelope of the scheme.

*Caveat.* The 1.5x multiplier itself is not in the paper. It is an
engineering safety margin and should be tuned on labeled data in
Issue #29, not defended as a literature value.

## What the score does NOT capture

Scarfe et al. (2009) identify four core surfing-wave parameters on p.544:

1. Breaking wave height H_B  (captured as `wave_score`)
2. Wave peel angle alpha     (not captured: needs bathymetric modelling)
3. Breaking intensity B_I    (not captured: needs sea-bed gradient)
4. Section length S_L        (not captured: needs oblique video or reef data)

The paper also highlights additional factors the formula ignores:

- Tide state, which changes the orthogonal gradient and therefore the
  breaker intensity (p.549).
- Beach state in the Wright and Short (1984) sense: intermediate states
  are flagged as more likely to create surfing waves (p.549).
- Relative angle of wind to the wave crest, as noted under `wind_penalty`
  and `offshore_bonus`.
- Spot geomorphology (headland, beach break, river bar, reef, ledge),
  which changes which parameters dominate and at what magnitudes
  (pp.547-548).

## Forward-looking note for the ML evaluation (Issues #29, #31)

The gaps above are where the gradient-boosted model has room to
outperform the rule-based baseline:

- Non-monotonic period response beyond the 14 s saturation anchor.
- Wind-wave direction interaction captured by the existing
  `wind_wave_interaction = wind_speed * cos(wind_dir - swell_dir)`
  engineered feature.
- Spot-conditioned wave-height sweet spots, where each spot learns
  its own band rather than inheriting a global skill threshold.
- Offshore-magnitude interaction with skill, which the flat +10 bonus
  cannot express.

When writing up Issue #31, attribute ML-over-baseline wins to these
specific gaps rather than to a generic "ML is better" narrative. That
keeps the evaluation defensible and makes the feature-importance and
SHAP plots legible to a thesis reader who has read Scarfe et al. (2009).
