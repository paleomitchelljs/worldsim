# Sensitivity screen (WP9 stage B, 2026-11-21)

**The screen.** A Morris screen of 30 parameters against the 28 measured
patterns of [patterns.md](patterns.md).
- Asked by U (2026-11-20): "Go ahead and launch"; keep summaries only.
- Code of `wp8j`, with `clearing` on.
- Tool: `docs/upgrade/tools/wp9_screen.py`.
- Full tables: `docs/upgrade/baseline/wp9b_effects.md`, from
  `wp9_analyze.py`.

**What it is for.** To find which parameters matter at all, and which
patterns respond to which dials. **It does not choose values**, and none
is changed here. Held-out patterns stay held out: knowing which dial
moves them is not leave to turn it.

## Design

- **Points.** 8 trajectories of 31 points (SALib 1.6.0, 4 levels): 248
  runs of 8,000 years, all on seed 101. A further point at the defaults
  ran on seed 105. All 249 runs ended normally; about 12 hours, 8 at a
  time.
- **Ranges.** Each parameter runs from half its default to double it, on
  a log scale. Three are linear:
  - PATH_MIN 0.3-0.9;
  - BUD_PRESS 0.3-0.6;
  - ODDS_MID 0.5-1.0.
- **Elementary effect (EE).** The change in a pattern when one parameter
  steps 2/3 of its range, rescaled to the whole range. So **mu (the mean
  EE) is roughly the change from the bottom to the top of the range.**
- **Seed noise.** The pattern's sd over six seeds at the defaults: `wp8j`
  seeds 101-104 and 106, plus seed 105 here. One parameter step changes
  the run's path as much as a new seed does, so an EE carries noise
  √2 × sd / (2/3).
- **Two tests.**
  - mu\* (mean |EE|) over that noise. This is weak: noise alone gives
    about 0.8.
  - **A clear direction:** |mu| / (noise / √n) ≥ 3, with n = 8. By chance
    about 2 of the 840 parameter-pattern pairs would pass. Only this one
    is used below.

## Results

**Parameters with a clear direction on each pattern.** The sign is the
effect of raising the parameter. The size is mu, against the pattern's
mean and seed sd at the defaults.

| Pattern | Mean (seed sd) | Clear dials (mu over the range) |
|---|---|---|
| P1 population at 8000 (M) | 48 (13) | R_SCALE +61, ADM_INV +37, EXP_SCALE −28 |
| P2 first city (yr) | 681 (200) | R_SCALE −740 |
| P2b year of 10M | 2,678 (184) | R_SCALE −4,340; BUD_PRESS +831, FEUD_K +776, EXP_SCALE +497, AGRI_INV −450 |
| P2c first bronze (yr) | 4,917 (1,100) | METAL_INV −3,250 |
| P3 growth, 6000-7000 | 0.011 (0.016) %/yr | none |
| P4 largest 100-yr fall after 3000 | −0.12 (0.06) | none |
| P5 urban share at the end | 0.040 (0.009) | FF_RENT +0.048, ADM_INV +0.047, R_SCALE +0.038, FF_TAX +0.028 |
| C1 rank-size slope, top 200 | −0.98 (0.27) | R_SCALE +0.82 |
| C2 largest city, share of world | 0.0010 (0.0002) | ADM_INV +0.0009, FF_RENT +0.0008, FF_TAX +0.0007, PL_EMERGE −0.0004; also EXT_SUBJ +, WAR_BASE +, TRADE_RATE2 − |
| C3 city food from trade | 0.030 (0.011) | FF_TRADE +0.058, R_SCALE +0.041, ADM_INV +0.035 |
| C4 cities ended, share | 0.89 (0.03) | FF_RENT −0.16, ADM_INV −0.16, FF_TAX −0.10, R_SCALE −0.10, DEV_K −0.07 |
| C5 spacing vs density (held out) | −0.46 (0.08) | R_SCALE +0.22 |
| C6 large third on coast or river (held out) | 0.96 (0.04) | none |
| S1 state lifespan median (yr) | 563 (241) | EXT_SUBJ +876, EXP_SCALE +625 |
| S2 largest state, share of land | 0.010 (0.005) | R_SCALE +0.040, ADM_INV +0.029, EXP_SCALE −0.015, REVOLT_BASE −0.013, KIN_RAID −0.013 |
| S3 skew of log state peak size | −0.01 (0.28) | ADM_INV +1.2, R_SCALE +0.88, TRADE_RATE2 −0.83, ODDS_MID +0.73 |
| S4 state slope, ranks 11-100 (held out) | −0.55 (0.07) | ADM_INV −0.26 (EXP_SCALE +0.16 below the cut) |
| S5 never above one city | 0.91 (0.03) | ADM_INV −0.12, R_SCALE −0.11, FF_RENT −0.10 |
| S6 rule spells, p90 (held out) | 458 (37) yr | FF_RENT +155, FF_TAX +145 |
| S7 largest state, land pieces | 3.8 (2.5) | R_SCALE +10, EXT_SUBJ −8, ADM_INV +7, BUD_PRESS +7, SUCC_P −6 |
| W1 wars | 1,137 (612) | R_SCALE +8,310; EXP_SCALE −4,510; ADM_INV +3,360; RAID_RATE −2,690; ODDS_MID −2,330; and 7 more |
| W2 sieges taken | 0.44 (0.01) | ADM_INV +0.13, R_SCALE +0.09, ODDS_MID +0.06, R_MAX +0.05, COH_DECAY −0.04, METAL_INV −0.04, EXP_SCALE −0.04; and 3 more |
| W3 peer wars (held out) | 19 (18) | R_SCALE +181, ODDS_MID −127, EXP_SCALE −119, ADM_INV +69, RAID_RATE −69; and 6 more |
| L1 population on rivers | 0.40 (0.03) | none |
| L2 population at \|lat\| 0-15 | 0.71 (0.04) | none |
| L4 population in a state | 0.56 (0.11) | ADM_INV +0.44, R_SCALE +0.34 |
| K3 traits between a lineage's cities (held out) | 0.012 (0.002) | FF_KM −0.007, FEUD_K −0.006, WAR_BASE +0.004; also KIN_RAID +, UNREST +, AGRI_INV +, PATH_MIN − |
| K4 people changed, 7500-8000 | 0.019 (0.003) | R_SCALE +0.028, ADM_INV +0.019, EXT_SUBJ +0.012, CLIM_AMP +0.010, DEV_K +0.008, EXP_SCALE −0.008, RAID_RATE −0.007 |

**How many patterns each parameter moves** (clear direction):

| Parameters | Patterns |
|---|---|
| R_SCALE | 17 |
| ADM_INV | 15 |
| EXP_SCALE | 7 |
| FF_RENT, FF_TAX | 6 each |
| TRADE_RATE2 | 5 |
| KIN_RAID, FEUD_K, ODDS_MID, EXT_SUBJ | 4 each |
| METAL_INV, AGRI_INV, REVOLT_BASE, RAID_RATE, WAR_BASE | 3 each |
| SUCC_P, BUD_PRESS, DEV_K | 2 each |
| R_MAX, FF_KM, CLIM_AMP, PATH_MIN, COH_DECAY, FF_TRADE, PL_EMERGE, UNREST | 1 each |
| SITE_DEF_SD, WAR_GAIN, WAR_IDLE, ACC | 0 |

## Conclusions

### 1. Inert parameters

Four parameters move no pattern at all over a factor of 4:
- **WAR_GAIN** and **WAR_IDLE**: not even mu\* is above noise.
  *Correction (WP13 A, 2026-11-21):* neither was read by the code
  (left from the old `war_motive` rule), so this says nothing about the
  war motive. Both were deleted in WP13 B.
- **ACC** (acculturation): not even mu\* is above noise.
- **SITE_DEF_SD**: mu\* above noise on 4 patterns, with no clear
  direction. Checked in WP15 (2026-11-22, `wp12f` seeds 101 and 103):
  site defence does reach the odds (`city_def` in every siege and
  defence path; `--set` reaches it). Hard sites are besieged about half
  as often (strongest quartile 5.8 and 7.2 sieges per 1,000 city-years,
  weakest 8.9 and 16.0), but the odds and outcomes of the sieges that
  happen do not vary with it (correlation -0.02 and 0.02): `war_odds`
  gates sieges on the odds, so it selects the sieges that are worth
  laying. No pattern measures siege frequency per site.

Their mechanisms run, but the measured patterns don't see them. Either
the mechanism is swamped by others (war onset by the odds and raid
paths), or what it shapes is not among the patterns (acculturation
shapes peoples' shares, which have no frozen pattern).

Seven more move one pattern each, and may be single-purpose or marginal:
- R_MAX, FF_KM, CLIM_AMP, PATH_MIN, COH_DECAY, PL_EMERGE, UNREST.
- **CLIM_AMP touches only turnover**, though the climate's swing drives
  famines. Volatility (P4) responds to nothing at all.

### 2. Patterns that respond to nothing

- **P3 late growth and P4 volatility.** Their seed sd is as large as
  their mean, or near it, so one seed per point cannot see an effect.
  They are noise-dominated, not proven insensitive.
- **L1 population on rivers, L2 population at low latitude, and C6 large
  cities by water.** All have small seed sd and still respond to nothing.
  **They are set by the map**: where the good land is. None of the 30
  dials moves them. Agreement here says the world file is doing the
  work, not the society model.

### 3. Patterns with a single dial

- **P2 first city** and **C1 rank-size slope**: R_SCALE alone. Its range
  moves C1 by 0.8, three seed sds, from about −1.4 to −0.6.
- **P2c first bronze**: METAL_INV alone (−3,250 years over its range).
- **C5 spacing (held out)**: R_SCALE alone.
- **S4 state slope, ranks 11-100 (held out)**: ADM_INV alone (EXP_SCALE
  just below the cut).
- **C3 trade food**: FF_TRADE leads (+0.058), with R_SCALE and ADM_INV.

### 4. Two master dials

**R_SCALE (growth) and ADM_INV (administration's invention rate) move
most of what is measured**: 17 and 15 of 28 patterns.
- Much of it is through scale: more people means more cities, states and
  wars. W1 (wars) and W3 (peer wars) are counts and scale with
  population.
- Patterns already spent by tuning another parameter (W1, by WAR_BASE)
  also respond to these two. The spent values are
  conditional on R_SCALE and ADM_INV as they stand.

### 5. Food flows and experience

- **FF_RENT and FF_TAX shape the city system**: urban share, largest
  city, how many cities die, and rule spells. They act together, always
  in the same direction.
- **EXP_SCALE (experience)** moves:
  - state size and lifespan;
  - wars, which it cuts;
  - population, which it lowers;
  - the timeline, which it slows.
  It is the third broadest dial.

## Caveats

- **One seed per point**, r = 8, and ranges of ×/÷2. Morris ranks effects
  and doesn't measure them well. mu is a mean over different contexts,
  and sigma (in the tables) is often as large as mu: interactions or
  curvature.
- **The seed sd is from six runs**, so the noise is itself uncertain
  by about ±30%. Pairs near z = 3 could go either way.
- **Only 30 parameters**: the screen's leading rates, not every constant.
  The map, the roster and switches are not screened.
- **Run on `wp8j`.** The clearing extensions (`clear_terrain`, `fire`)
  and any climate fix come later and could shift these effects.
