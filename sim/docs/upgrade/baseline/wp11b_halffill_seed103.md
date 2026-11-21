Seed 103, year 8000: population 72.8M main rows; 44206 occupied cells.

| Biome | area M km² | occupied | people/km2 | K/km2 | fill | best K/km2 | farm | forage | agri | tools | sod | steppe | clim_rain | crop | fit | Kcell | coast_dev | herd wins |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jungle | 29.4 | 1.00 | 1.75 | 3.05 | 0.573 | 5.28 | 0.94 | 0.404 | 0.917 | 1.14 | 1 | 1 | 0.978 | 0.908 | 1.26 | 1.02 | 1.73 | 0.119 |
| Desert | 9.5 | 0.99 | 0.18 | 0.31 | 0.581 | 0.567 | 0.123 | 0.0234 | 0.67 | 1.01 | 1 | 1 | 1.34 | 0.799 | 0.528 | 1 | 1.12 | 0.762 |
| Grassland | 37.9 | 1.00 | 0.25 | 0.635 | 0.393 | 1.65 | 0.444 | 0.175 | 0.701 | 1.01 | 0.373 | 1 | 0.951 | 0.729 | 0.752 | 1 | 1.19 | 0.702 |
| Temperate forest | 26.0 | 1.00 | 0.39 | 1.01 | 0.388 | 2.22 | 0.779 | 0.263 | 0.804 | 1.03 | 1 | 1 | 1 | 0.645 | 0.813 | 1 | 1.36 | 0.2 |
| Tundra | 19.2 | 0.34 | 0.044 | 0.0785 | 0.561 | 0.0903 | 0.104 | 0.036 | 0.73 | 1 | 1 | 1 | 1.05 | 0.526 | 0.686 | 1 | 1.14 | 0.673 |

Half-fill: main rows' people as a share of land capacity (raw K, no drought or devastation), and the gap split by step; each term is a share of land capacity, and fill + the terms = 1. `received` is negative (food sent in). `other rows' people` is for scale.

| Biome | land K/km² | fill (people/land K) | fill (stage A) | drought | devastation | rent+tax (own) | army food | rent+tribute (subjects) | trade sold | received | (state residual) | other rows eat | separation | below own k (lag) | other rows' people |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jungle | 3.048 | 0.573 | 0.573 | 0.000 | 0.000 | 0.076 | 0.006 | 0.009 | 0.004 | -0.064 | -0.000 | 0.012 | 0.016 | 0.368 | 0.014 |
| Desert | 0.310 | 0.581 | 0.581 | 0.000 | 0.000 | 0.067 | 0.001 | 0.000 | 0.003 | -0.048 | 0.000 | 0.006 | 0.047 | 0.344 | 0.008 |
| Grassland | 0.635 | 0.393 | 0.393 | 0.000 | 0.000 | 0.021 | 0.000 | 0.005 | 0.001 | -0.020 | -0.000 | 0.010 | 0.075 | 0.514 | 0.013 |
| Temperate forest | 1.005 | 0.388 | 0.388 | 0.000 | 0.000 | 0.033 | 0.004 | 0.002 | 0.002 | -0.024 | 0.000 | 0.006 | 0.034 | 0.555 | 0.009 |
| Tundra | 0.078 | 0.561 | 0.561 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.036 | 0.403 | 0.000 |
| All occupied | 1.312 | 0.509 | 0.509 | 0.000 | 0.000 | 0.058 | 0.005 | 0.007 | 0.003 | -0.049 | 0.000 | 0.010 | 0.030 | 0.426 | 0.013 |

Flows over the last 1005 years: heads by phase (change + deaths recorded in it; `grow` is natural increase) and deaths by cause, per century, as a share of the biome's heads at the window's start (all rows, soldiers away excluded).

| | Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|---|
| heads at start (M) | 31.45 | 0.81 | 7.41 | 7.50 | 0.25 |
| heads at end (M) | 52.58 | 1.71 | 9.74 | 10.34 | 0.29 |
| phase famine | +0.000 | -0.004 | -0.001 | +0.000 | -0.005 |
| phase grow | +0.389 | +0.528 | +0.466 | +0.410 | +0.369 |
| phase migrate | -0.003 | -0.012 | +0.008 | +0.007 | +0.001 |
| phase states | +0.002 | -0.000 | +0.000 | +0.001 | -0.000 |
| phase minorities | +0.011 | +0.003 | +0.002 | +0.008 | +0.000 |
| phase wars | -0.016 | -0.007 | -0.001 | -0.007 | -0.000 |
| deaths: feud | 0.094 | 0.161 | 0.271 | 0.193 | 0.259 |
| deaths: plague | 0.110 | 0.115 | 0.033 | 0.062 | 0.000 |
| deaths: raid | 0.070 | 0.089 | 0.117 | 0.098 | 0.076 |
| deaths: hunger | 0.018 | 0.026 | 0.015 | 0.012 | 0.014 |
| deaths: ravage | 0.010 | 0.003 | 0.001 | 0.009 | 0.000 |
| deaths: expelled | 0.008 | 0.001 | 0.002 | 0.004 | 0.000 |
| deaths: sack | 0.004 | 0.001 | 0.001 | 0.002 | 0.000 |
| deaths: siege | 0.002 | 0.000 | 0.000 | 0.001 | 0.000 |
| deaths: clearance | 0.001 | 0.000 | 0.001 | 0.000 | 0.000 |
| deaths: displaced | 0.000 | 0.001 | 0.001 | 0.000 | 0.000 |
| deaths: dwindled | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 |
| growth forgone under dragons (not deaths) | 0.123 | 0.074 | 0.337 | 0.306 | 0.047 |

Fill (main rows' people / raw K, as stage A) by year:

| Year | Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|---|
| 1000 | 0.18 | 0.15 | 0.20 | 0.23 | 0.52 |
| 2000 | 0.19 | 0.18 | 0.20 | 0.24 | 0.40 |
| 3000 | 0.20 | 0.20 | 0.23 | 0.26 | 0.55 |
| 4000 | 0.26 | 0.21 | 0.28 | 0.30 | 0.63 |
| 5000 | 0.32 | 0.22 | 0.31 | 0.34 | 0.66 |
| 6000 | 0.34 | 0.25 | 0.33 | 0.34 | 0.63 |
| 7000 | 0.44 | 0.34 | 0.32 | 0.36 | 0.66 |
| 7500 | 0.48 | 0.43 | 0.32 | 0.35 | 0.52 |
| 8000 | 0.57 | 0.58 | 0.39 | 0.39 | 0.56 |
