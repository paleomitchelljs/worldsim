Seed 101, year 8000: population 63.1M main rows; 43453 occupied cells.

| Biome | area M km² | occupied | people/km2 | K/km2 | fill | best K/km2 | farm | forage | agri | tools | sod | steppe | clim_rain | crop | fit | Kcell | coast_dev | herd wins |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jungle | 29.4 | 1.00 | 1.27 | 2.41 | 0.525 | 4.93 | 0.845 | 0.386 | 0.891 | 1.12 | 1 | 1 | 0.913 | 0.767 | 1.27 | 1.01 | 1.67 | 0.11 |
| Desert | 9.5 | 0.99 | 0.139 | 0.29 | 0.477 | 0.516 | 0.119 | 0.0239 | 0.718 | 1.03 | 1 | 1 | 1.39 | 0.904 | 0.588 | 1 | 1.14 | 0.812 |
| Grassland | 37.9 | 1.00 | 0.253 | 0.603 | 0.42 | 1.65 | 0.401 | 0.166 | 0.679 | 1.01 | 0.376 | 1 | 0.887 | 0.716 | 0.751 | 1 | 1.18 | 0.749 |
| Temperate forest | 26.0 | 1.00 | 0.569 | 1.1 | 0.518 | 2.54 | 0.722 | 0.239 | 0.814 | 1.03 | 1 | 1 | 0.906 | 0.671 | 0.824 | 1.01 | 1.35 | 0.205 |
| Tundra | 19.2 | 0.30 | 0.0394 | 0.052 | 0.758 | 0.0995 | 0.101 | 0.0259 | 0.66 | 1 | 1 | 1 | 0.626 | 0.516 | 0.666 | 1 | 1.13 | 0.707 |

Half-fill: main rows' people as a share of land capacity (raw K, no drought or devastation), and the gap split by step; each term is a share of land capacity, and fill + the terms = 1. `received` is negative (food sent in). `other rows' people` is for scale.

| Biome | land K/km² | fill (people/land K) | fill (stage A) | drought | devastation | rent+tax (own) | army food | rent+tribute (subjects) | trade sold | received | (state residual) | other rows eat | separation | below own k (lag) | other rows' people |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jungle | 2.416 | 0.525 | 0.525 | 0.000 | 0.001 | 0.061 | 0.005 | 0.002 | 0.003 | -0.048 | -0.000 | 0.007 | 0.020 | 0.426 | 0.012 |
| Desert | 0.290 | 0.477 | 0.477 | 0.000 | 0.000 | 0.048 | 0.000 | 0.005 | 0.010 | -0.059 | -0.000 | 0.019 | 0.050 | 0.448 | 0.042 |
| Grassland | 0.603 | 0.420 | 0.420 | 0.000 | 0.000 | 0.023 | 0.000 | 0.002 | 0.001 | -0.018 | 0.000 | 0.005 | 0.073 | 0.494 | 0.007 |
| Temperate forest | 1.098 | 0.518 | 0.518 | 0.000 | 0.000 | 0.038 | 0.000 | 0.002 | 0.001 | -0.038 | 0.000 | 0.005 | 0.025 | 0.448 | 0.009 |
| Tundra | 0.052 | 0.758 | 0.758 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0.032 | 0.210 | 0.000 |
| All occupied | 1.157 | 0.504 | 0.504 | 0.000 | 0.000 | 0.049 | 0.003 | 0.002 | 0.002 | -0.041 | -0.000 | 0.007 | 0.031 | 0.443 | 0.011 |

Flows over the last 1005 years: heads by phase (change + deaths recorded in it; `grow` is natural increase) and deaths by cause, per century, as a share of the biome's heads at the window's start (all rows, soldiers away excluded).

| | Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|---|
| heads at start (M) | 24.31 | 0.53 | 9.05 | 12.29 | 0.22 |
| heads at end (M) | 38.12 | 1.41 | 9.71 | 15.00 | 0.23 |
| phase famine | -0.000 | -0.003 | -0.001 | +0.001 | -0.001 |
| phase grow | +0.436 | +0.832 | +0.367 | +0.310 | +0.330 |
| phase migrate | +0.001 | -0.024 | +0.001 | -0.002 | -0.000 |
| phase raids | -0.000 | +0.001 | +0.000 | +0.000 | -0.000 |
| phase states | +0.002 | +0.001 | +0.000 | +0.001 | +0.000 |
| phase minorities | +0.009 | +0.027 | +0.001 | +0.004 | +0.000 |
| phase wars | -0.010 | -0.004 | -0.001 | -0.006 | -0.000 |
| deaths: feud | 0.174 | 0.334 | 0.188 | 0.122 | 0.224 |
| deaths: raid | 0.112 | 0.212 | 0.100 | 0.084 | 0.081 |
| deaths: plague | 0.060 | 0.051 | 0.039 | 0.061 | 0.000 |
| deaths: hunger | 0.013 | 0.039 | 0.028 | 0.012 | 0.015 |
| deaths: ravage | 0.009 | 0.011 | 0.002 | 0.003 | 0.000 |
| deaths: expelled | 0.007 | 0.012 | 0.002 | 0.003 | 0.000 |
| deaths: sack | 0.003 | 0.000 | 0.001 | 0.001 | 0.000 |
| deaths: siege | 0.002 | 0.002 | 0.000 | 0.001 | 0.000 |
| deaths: clearance | 0.001 | 0.000 | 0.000 | 0.001 | 0.000 |
| deaths: displaced | 0.001 | 0.001 | 0.000 | 0.000 | 0.000 |
| deaths: dwindled | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 |
| growth forgone under dragons (not deaths) | 0.224 | 0.139 | 0.261 | 0.205 | 0.054 |

Fill (main rows' people / raw K, as stage A) by year:

| Year | Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|---|
| 1000 | 0.17 | 0.27 | 0.16 | 0.21 | 0.47 |
| 2000 | 0.18 | 0.20 | 0.24 | 0.26 | 0.56 |
| 3000 | 0.22 | 0.18 | 0.31 | 0.27 | 0.50 |
| 4000 | 0.32 | 0.25 | 0.39 | 0.38 | 0.59 |
| 5000 | 0.31 | 0.35 | 0.42 | 0.45 | 0.81 |
| 6000 | 0.39 | 0.38 | 0.42 | 0.45 | 0.79 |
| 7000 | 0.45 | 0.35 | 0.48 | 0.49 | 0.86 |
| 7500 | 0.45 | 0.38 | 0.41 | 0.46 | 0.65 |
| 8000 | 0.52 | 0.48 | 0.42 | 0.52 | 0.76 |
