"""Constants and switches."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

GPKG = os.path.join(HERE, "..", "gis", "world.gpkg")
NY, NX = 360, 720
R_EARTH = 6371.0
BIOMES = ["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra"]

# ---- assumptions ---------------------------------------------------------
DT = 5                      # years per tick
# Rates (WP5 stage C, 2026-11-18). A chance of an event, or a share lost or
# gained by compounding, that the model once wrote per 5-year tick is now
# quoted per SPAN years and applied over a step of any length by over();
# at DT = SPAN each is what it was. Rates linear in time are written per
# year and multiplied by the step, as before.
SPAN = 5.0


def over(p, years=None, span=SPAN):
    """The chance over `years` (default DT) of an event with chance p per
    `span` years at a constant hazard; equally the share lost over `years`
    at p per span. p is clipped to 0-1."""
    years = DT if years is None else years
    return 1.0 - (1.0 - min(1.0, max(0.0, p))) ** (years / span)


# Forager density (people/km2) by biome.
FORAGE = {"Jungle": 0.25, "Temperate forest": 0.18, "Grassland": 0.15,
          "Desert": 0.02, "Tundra": 0.03}
# Rain-fed farming suitability by biome (multiplies soil fertility).
FARM = {"Jungle": 0.45, "Temperate forest": 0.75, "Grassland": 1.0,
        "Desert": 0.04, "Tundra": 0.03}
# Floodplain irrigation response by biome: dry climates gain the most.
IRRIG = {"Jungle": 0.4, "Temperate forest": 0.6, "Grassland": 0.9,
         "Desert": 1.0, "Tundra": 0.05}
FARM_MAX_DENS = 1.8         # people/km2 on the best rain-fed soil
IRRIG_MAX_DENS = 9.0        # people/km2 added on a big floodplain
# `floodplain` (WP8 stage C): irrigation on the floodplain's area, not the
# whole cell. Floodplain width (km) = FP_W0 x sqrt(Q / 1000 m3/s), x FP_ALLUV
# on alluvium (surface alluvium or alluvial fill), x exp(-relief /
# FP_RELIEF); a delta (river cell at the coast on alluvium) at least
# FP_DELTA_KM. Irrigable area = valley
# length in the cell x width, capped at the cell's area.
FP_W0 = 5.0                 # km at 1,000 m3/s
FP_ALLUV = 3.0
FP_RELIEF = 0.5             # km
FP_DELTA_KM = 40.0
IRRIG_FP_DENS = 20.0        # people/km2 on irrigated land (~10 x FARM_MAX_DENS)
# Travel cost multiplier by biome (cost-km per km).
MOVE = {"Jungle": 1.7, "Temperate forest": 1.25, "Grassland": 1.0,
        "Desert": 1.5, "Tundra": 1.8}
STRAIT_KM = 160.0           # coastal cells this close link across water
# Biome preference: habitability = best * (affinity / best) ** k. k starts at
# BIOME_K and falls toward BIOME_K * (1 - BIOME_ADAPT) = 1 (the roster's own
# numbers) as farming and metallurgy let a lineage live off its home biome.
BIOME_K = 2.5
BIOME_ADAPT = 0.6
# Sea dispersal: voyage targets are weighted by exp(-d / D),
# D = SAIL_D0 + SAIL_D1 * sail ** 1.5 (km). No minimum range.
SAIL_D0, SAIL_D1 = 40.0, 2500.0
# Military multiplier from metal: 1 + bronze + iron + 1.5 * steel
METAL_MIL = (1.0, 1.0, 1.5)
# Farm yield from tools: 1 + iron + steel terms
TOOLS = (0.25, 0.25)
# Terrain. Defence: a siege defender's strength is multiplied by
# TERRAIN_DEF[biome] * (1 + DEF_RELIEF * relief_km[<=1.5]) * (1 + DEF_WET * wet)
TERRAIN_DEF = {"Grassland": 1.0, "Temperate forest": 1.1, "Tundra": 1.3,
               "Desert": 1.6, "Jungle": 1.7}
DEF_RELIEF, DEF_WET = 0.6, 0.6
# Colonization: settling a cell is weighted by
# exp(-relief_km / COL_RELIEF) * (1 - COL_WET * wet)
COL_RELIEF, COL_WET = 0.7, 0.5
# Wetland peoples (roster key `wet`, 0-1; default 0, 2026-10-29): a cell's
# capacity for them x (1 + WET_K x wet x wetness), and the settling
# penalty for wet ground (COL_WET) falls away in proportion to `wet`.
WET_K = 2.0
# Rivers. Dispersal: a pioneer leaving a river cell follows the river (up or
# downstream) with probability RIV_LEAP, up to RIV_STEPS[0] + RIV_STEPS[1] *
# sail cells; budding from a river cell to a river cell is favoured by
# (1 + RIV_BUD). Trade: tie growth x (1 + RIV_TRADE * mean share of the two
# states' cities on rivers) x (1 + BASIN_TRADE if they share a river basin).
RIV_LEAP, RIV_STEPS, RIV_BUD = 0.6, (6, 30), 1.0
RIV_TRADE, BASIN_TRADE = 1.0, 0.5
FOUND_MIN = 10.0            # smallest band that can claim an empty cell
CITY_POP = 6000.0           # food-equivalent cell population for a city
CITY_KEEP = 0.35            # a city is abandoned below this x its threshold
# Optional city size cap (food-equivalent people in the city cell), set by
# the ruling lineage's administration: CITY_POP * (CITY_CAP0 + CITY_CAP1 *
# admin**2). Off by default since 2026-10-29 (U); --city-cap 3 40 restores it.
CITY_CAP = False
CITY_CAP0, CITY_CAP1 = 3.0, 40.0
REACH0, REACH1 = 120.0, 900.0   # admin reach (cost-km) = REACH0 + REACH1*admin

# ---- switches ------------------------------------------------------------
# On unless named in --off NAME[,NAME...]. The 2026-11-02 streamlining made
# the rest permanent (docs/switch-inventory.md); these remain because they
# are rebuilt at the city level or are experimental.
FEATURES = ["acculturation", "acc_cross", "mission", "conformity",
            "proselytism", "experience", "spiky", "life_memory",
            "revolt_exp", "rulers", "ruler_traits", "turmoil",
            "revolt_viol", "fortress", "diagnostics", "city_culture",
            "city_admin", "city_history", "rule_weak", "city_trade",
            "trade_local", "city_influence", "adm_reach", "dominion",
            "food_flow", "war_terms", "urban_city", "trade_debit",
            "war_odds", "site_defence", "ruler_mil", "pol_step",
            "army", "camps", "epidemic", "upkeep", "shared_cells",
            "displacement", "climate_fields"]
# Switches off unless named in --on (WP4 stage B, 2026-11-17). Kept apart
# from FEATURES so that "--off all" and old states are unchanged. Empty
# since `trade_debit` became a default (WP4 D, U 2026-11-18).
OPTIONAL = ["floodplain"]
# Trait costs. Cohesion slows borrowing from outsiders; statecraft's
# extraction raises unrest when the state is underfed; violence raises the
# chance of a succession crisis; expansion leaves thin frontier cells more
# exposed to raids.
COST_COH = 0.5              # borrowing x (1 - COST_COH * cohesion)
COST_STATE = 2.0            # unrest x (1 + COST_STATE * statecraft * hunger)
COST_EXPN = 0.8             # raid damage x (1 + COST_EXPN * expn * thinness)
# Fiscal: a state's strength and reach follow its fed population, not its
# head count. fed = sum(pop * min(1, K/pop)) / sum(pop), smoothed.
FISC_EMA = 0.2              # weight of the last SPAN years, via over()
# Structural-demographic unrest (Goldstone, Turchin). Elites grow when the
# land is crowded (cheap labour, high rents) and shrink otherwise; political
# stress = crowding x elite load, and multiplies the revolt hazard.
ELITE_G = 0.004             # per year, elite growth per unit crowding excess
ELITE_CROWD = 0.75          # crowding at which elites neither grow nor shrink
UNREST = 3.0                # revolt hazard x (1 + UNREST * stress)
# Succession: per-generation chance of a crisis in states of
# SUCC_MIN_CITIES or more cities (3 until 2026-11-18; U: small states
# too, so that a talented ruler can arise in one).
SUCC_MIN_CITIES = 1
SUCC_GEN = 25.0             # years per reign, on average
SUCC_P = 0.12               # crisis chance per reign x (0.5 + violence)
                            # x (1.3 - 0.6 statecraft)
# Vassals: a much weaker side may submit instead of being besieged.
VASSAL_RATIO = 3.0          # projected strength ratio that invites submission
VASSAL_TRIB = 0.25          # share of a vassal's strength paid to its lord
VASSAL_DEFECT = 0.01        # per year, x vassal/lord strength x (1.5 - lord S)
# Balancing: a common strong neighbour pushes two states into alliance,
# across cultural lines.
BALANCE = 4.0
# Pastoralism. Herding density (people/km2) by biome; herding needs farming
# >= HERD_AGRI (domestic animals). Herders count MOUNT x in war and raids and
# project force further; they seldom found cities.
HERD = {"Grassland": 0.45, "Desert": 0.08, "Tundra": 0.06,
        "Temperate forest": 0.12, "Jungle": 0.02}
HERD_AGRI = (0.35, 0.75)    # herding ramps from 0 to full over this agri
MOUNT = 1.6
# Steppe proxy: the world file has one runoff value per biome, so dryness
# within a biome is taken from distance to the coast. Rain-fed farming on
# grassland and desert falls to STEPPE_MIN far inland.
STEPPE_KM = (400.0, 1600.0)
STEPPE_MIN = 0.35
# `climate_fields` (WP8 stage B): on a world with climate fields
# (world_v2.gpkg), dryness and the steppe come from the aridity index
# (P/PET), and farming and herding get a gradient within each biome from
# growing-degree days and aridity, normalised to an area-weighted mean of 1
# in each biome so each biome's total is kept. The steppe's cut on rain-fed
# farming is dropped there (the farming gradient carries aridity already).
CLIM_STEPPE_AI = (0.65, 0.2)  # steppe 0 at this aridity, 1 at this (UNEP bounds)
CLIM_DRY_AI = 1.0           # dryness = clip(1 - aridity / this)
CLIM_FARM = (2000.0, 0.65)  # farming term full at these GDD and aridity
CLIM_HERD = (800.0, 0.2)    # herding term full at these
CLIM_RATIO_MAX = 3.0        # cap on a cell's term relative to its biome's mean
# Land condition (0.3-1) multiplies farm density. It falls with farming
# intensity (irrigation x LAND_IRR faster: salinization) and recovers when
# land is lightly used.
LAND_DEG = 0.0003           # per year at full intensity, rain-fed
LAND_IRR = 3.0
LAND_REC = 0.004            # per year x (1 - condition) x (1 - intensity)
LAND_MIN = 0.3
# Climate (`climate`; replaces the random droughts when on). A moisture
# anomaly m per cell (sd about 1): fixed large-scale patterns, each with its
# own time series, plus a local field drawn fresh each tick, plus rare
# abrupt dry events. Each series mixes broad spectral peaks, not cycles:
CLIM_PARTS = [              # (kind, period yrs, damping yrs, variance share)
    ("white", 0, 0, 0.30),          # interannual-decadal (ENSO-like, 5-yr means)
    ("osc", 60, 60, 0.15),          # multidecadal
    ("osc", 200, 250, 0.20),        # centennial (solar-like)
    ("osc", 1500, 1500, 0.20),      # millennial (Bond-like; contested)
    ("red", 0, 400, 0.15)]          # slow background
CLIM_W = dict(world=0.35, latitude=0.25, inland=0.25, regional=0.35,
              local=0.45)           # weights of the patterns (normalized)
CLIM_REGIONAL, CLIM_REG_SIGMA, CLIM_LOCAL_SIGMA = 4, 20, 6   # fields, cells
CLIM_LOCAL_COARSE = 1       # >1: local field drawn on every k-th row and
                            # column, sigma in fine cells kept, interpolated
                            # to the land cells (speed). 1 (the full grid)
                            # since 2026-11-17 (U): 2 may have lowered
                            # population (open-questions.md)
ABRUPT_RATE = 1 / 2000      # abrupt dry events per year (8.2/4.2/3.2 ka-like)
ABRUPT_YEARS, ABRUPT_AMP = (150, 400), (1.5, 2.5)   # length, depth in sd
ABRUPT_RAMP = (25, 75)      # years to set in, years to lift
# The climate history (series and abrupt events) is drawn for CLIM_YEARS
# (or the run, if longer) whatever --years says, so a shorter run of a
# seed has the same climate as the start of a longer one (C, 2026-11-07;
# before, the draws depended on the run's length).
CLIM_YEARS = 20000
PREC_SD = (0.10, 0.12)      # precipitation anomaly sd = a + b x dryness
RUNOFF_EL = 1.5             # runoff responds 1.5x to precipitation
ECO_W = 0.35                # biome blend per sd of anomaly beyond 0.5 sd
ECO_MAX = 0.7
STORE_YEARS = 15.0          # granaries: state cells feel climate smoothed
                            # over STORE_YEARS x administration years
FAMINE_MOVE, FAMINE_RANGE, FAMINE_MAX = 0.5, 8, 600  # share of excess,
                            # cells, sources per tick
HUNGER_WAR, HUNGER_RAID = 2.0, 1.5
# Rivers change course (avulsion) on big rivers over alluvial lowland:
# per prone cell per year AVULSE_RATE x (discharge ratio)^2; the new course
# runs to a neighbour no more than AVULSE_TOL km higher.
AVULSE_RATE, AVULSE_TOL = 2.5e-4, 0.03
# Supply: a metal stage needs its ores in hand to stay in use; knowledge is
# kept, but use lapses after SUPPLY_GRACE years without supply. Without
# cities, administration and metallurgy decay.
SUPPLY_GRACE = 20           # years (was 4 ticks)
DECAY_ADMIN, DECAY_METAL = 0.002, 0.0004   # per year, scaled by city loss
# Growth (WP6, C): frontier fecundity multiplies the rate by up to
# 1 + FRONT_K where a cell is empty, falling to 1 at FRONT_END x K.
# R_SCALE multiplies every lineage's growth rate; R_MAX caps the
# effective yearly rate (after farming and frontier; 0 = no cap).
# Adopted 2026-11-18 (U->C, D7): R_SCALE 0.5, R_MAX 0.03; before WP6 B
# they were 1.0 and 0 (no cap).
FRONT_K, FRONT_END = 1.5, 0.5
R_SCALE, R_MAX = 0.5, 0.03
# Minorities: one secondary people per cell, up to MIN_CAP of the cell's K.
MIN_CAP = 0.2
MIN_GARRISON = 0.04         # of the city, settled by a conqueror
MIN_MERCHANT = 0.03         # of a city, x tie, from a trade partner people
MIN_EXPEL = 0.01            # per year x ruler separation x (1 - tolerance)
# Dominion (`dominion`, 2026-11-06; numbers C). Extraction: a state takes
# EXT_SUBJ x (0.5 + hierarchy) of the capacity of every people in it other
# than the ruling people, EXT_CITY times more in city cells, at most
# EXT_MAX; EXT_EFF of the food taken reaches the ruling people in the
# state's cities (by their share), smoothed at FISC_EMA. A subject city's
# revolt hazard x (1 + EXT_REVOLT x its rate).
EXT_SUBJ, EXT_CITY, EXT_MAX = 0.15, 1.5, 0.5
EXT_EFF = 0.6
EXT_REVOLT = 2.0
# Shared cells: a minority (other than a merchant quarter) shares the
# cell's land with the majority. Each side's capacity falls by
# SHARE_ALPHA x (w_other / w_own) x the other's food. Weight
# w = (1 + SH_TECH x tech) x (1 + SH_STATE x est), tech = mean of farming,
# bronze, iron and steel; est = administration x (0.5 + statecraft) of
# the ruling lineage, for the state's ruling people only.
SHARE_ALPHA = 0.9
SH_TECH, SH_STATE = 1.0, 3.0
# Settlers: cells of a state's ruling people above SET_PRESS of their
# capacity send SET_FRAC of their people per tick (at most half the room)
# into the best neighbouring cell of the same state held by another people.
SET_PRESS, SET_FRAC = 0.7, 0.02
# Shared cells (`shared_cells`, WP7 C, C): a row crowded past its
# migration threshold sends INF_FRAC x expansion x the excess of its people
# per tick into the neighbouring cell held by another people with most
# room, at most half that room; resistance INF_RES x (1 - holders'
# tolerance) x min(1, holders' weight / movers' weight).
INF_FRAC, INF_RES = 0.1, 0.9
# Flight (`displacement`, WP7 D): refugees go up to FLEE_RINGS cells (C).
FLEE_RINGS = 3
# Food flows (`food_flow`, 2026-11-09; U: rent from a state's own people,
# the state's take to its capital first, water carriage, trade as a
# per-city volume; numbers C). Needs `dominion`. Every rural cell under a
# city pays rent, FF_RENT x (0.5 + hierarchy) x the local carriage share,
# to that city; the state's own people also pay tax, FF_TAX x (0.5 +
# hierarchy), and subjects EXT_SUBJ as before; the total is capped at
# EXT_MAX. Peasants eat first: a cell yields FF_FORCE of its nominal take
# whatever the harvest, the rest only from what is left after its own
# people eat. Tax reaches the capital x exp(-food distance / FF_KM); the
# rest is spent in the cell's own city. Food distance runs over land as
# travel cost, along river channels at FF_RIVER and across water at FF_SEA
# per km (Diocletian's edict: sea 1, river ~5, land ~30-50). A vassal sends
# FF_VASSAL of its capital's tax to its lord's capital, by the same
# carriage. Trade brings FF_TRADE x sum over partners of tie x
# sqrt(FE_a x FE_b) (a gravity form) into a state's cities by size x
# (0.5 + 0.5 x waterside). The city-cell boost keeps its 1.5 base (gardens,
# manure, labour around the town) and loses the trade term. Trade is the
# one flow that adds food (gains from exchange) rather than moving it.
FF_RENT, FF_TAX, FF_FORCE = 0.12, 0.05, 0.5
FF_KM, FF_RIVER, FF_SEA = 250.0, 0.15, 0.04
# FF_RENT and FF_TRADE set after a test (seed 101, 6000 yrs): at 0.08 and
# 0.01 trade was 75% of the food reaching cities and fed non-capital ports
# into the top ranks; at 0.12 and 0.003 rent and the state's take are
# half, the largest cities are capitals, urban share 0.11 (was 0.17).
FF_VASSAL, FF_TRADE = 0.3, 0.003
# `trade_debit` (WP4 stage B, C): the share of a cell's marketable surplus
# (raw capacity beyond what its people eat and the state takes) that its
# farmers will sell
TRADE_SURPLUS = 0.5
FF_LIMIT = 4.0              # food distance searched, x FF_CAP_KM
# Capital levers (2026-11-09, U: try them; C). FF_CAP_KM: e-fold of the
# capital's take over the food graph (a state's carriage of tax grain may
# reach further than a landlord's cart); default FF_KM. FF_ABS: share of
# the ruling people's rent that goes to the capital, carried like tax
# (absentee landlords); default 0.
FF_CAP_KM = 250.0
FF_ABS = 0.0
# Urban population (records only, 2026-11-09, U: 2A): the people a city
# cell holds beyond what its own land feeds (at the 1.5 base boost), in
# food-equivalents; it replaces 0.08 x cell + 0.04 x hinterland as the
# city's size. A city below URBAN_MIN would be a village (counted, not
# acted on).
URBAN_MIN = 2000.0
# Cities as urban places (`urban_city`, 2026-11-09; U: 2B; numbers C). A
# city whose urban population stays below URBAN_MIN for URBAN_YEARS ends
# ("abandoned"), once it is URBAN_GRACE years old; its cell's farmers stay.
# No city is founded in a cell in famine (people above 1.05 x capacity,
# famine's own trigger) nor within 2 cells of a city abandoned less than
# URBAN_REFOUND years ago. The capital, a pretender's city and the size
# terms of city culture read urban population instead of the city cell's.
URBAN_YEARS, URBAN_GRACE, URBAN_REFOUND = 50, 100, 100
# Terms after a won siege (`war_terms`, 2026-11-09; U: built now; form and
# numbers C). The winner annexes the city, takes the defender as a
# tributary, or sacks the city and leaves. Weights: annex gov x (0.5 +
# dominance); tributary (1 - gov) x (0.5 + dominance), only if the
# defender is no one's vassal; sack TERMS_SACK x violence x (1.5 -
# dominance). gov = exp(-power distance / (1.5 x reach)), as projected
# strength. The war's goal multiplies its own outcome by TERMS_GOAL: land,
# resource and irredentism the annexation, prey the sack, rule annexation
# and tribute.
TERMS_SACK, TERMS_GOAL = 0.5, 2.0
# Turnover levers, named 2026-11-06 for the stability sweep (values as the
# literals they replace): cohesion decay per year (x size and age terms),
# provincial revolt base hazard per year, war end chance at the first tick
# (+0.03 per tick after), chance a state shatters into city-states when its
# capital falls. (WAR_DECLARE, named here too, fed only the pre-war_v2
# declaration rule, whose result war_chance overwrote: scaling it did
# nothing. Removed 2026-11-07; the declaration rate is WAR_BASE.)
COH_DECAY = 0.004
REVOLT_BASE = 0.0009
# War ending (per SPAN years, via over()): WAR_END0 + WAR_END_K x the
# war's age in years (was 0.03 per tick of age).
WAR_END0, WAR_END_K = 0.12, 0.006
SHATTER_P = 0.4
# Acculturation: cultural traits move toward contacts' traits, weighted by
# contact and prestige (sqrt population), at ACC x tolerance per year.
# Slow in general (U, 2026-10-29: was 0.004); fast under foreign rule: a
# lineage living under a ruler of another people moves toward the ruler's
# traits at ACC_CONQ x the share of it so ruled per year. Skill
# dispositions (innovation, seafaring, statecraft) can fall but are
# treated differently (U): a pull downward runs at SKILL_DOWN x the rate
# of a pull upward (C).
ACC = 0.001
# Dispersal (U, 2026-10-29): seafaring merges into expansion. Sea voyages
# run on expansion x (0.1 + sailing), as river leaps already did; sailing
# is invented from fishing and coastal share, and starts at SAIL_START.
SAIL_START = 0.025
# Fishing (U, 2026-10-29; numbers C): rivers, lakes and coasts feed more
# people, and a fishing technology raises the bonus. Capacity x (1 +
# (FISH0 + FISH1 x fishing) x water), water 0-1 per cell.
FISH0, FISH1 = 0.25, 0.75
FISH_START = 0.1
# Dominance (U, 2026-10-29; forms and numbers C): the wish to rule
# others. War chance x (0.5 + d) x (1 + DOM_PRIZE x d x min(2, their
# people / ours)); losses on capture x (1 - DOM_SPARE x d); clearance
# chance x (1 - d); the weaker side's chance to submit x (0.5 + d).
DOM_PRIZE = 0.5
# Ore trade (U, 2026-10-29): copper and tin move along trade ties. A state
# whose territory holds a worked deposit supplies every state joined to it
# by a chain of ties of at least ORE_TIE; lineages living in those states
# have the ore in hand.
ORE_TIE = 0.3
# Food units (`food_units`): founding groups, the dragon finding constant,
# prestige in acculturation, the population-size factor in invention, the
# plague trigger, recorded city sizes and Price weights count
# food-equivalents (heads x food per head), not heads.
FOUND_FOOD = 400.0
# Shuffle (`shuffle`): war declarations are checked in random order of
# pairs and of sides.
# Dynasty (`dynasty`, U 2026-10-29): the age in cohesion decay runs from
# the current dynasty, reset when the ruling lineage changes or a
# succession is disputed.
# Logistics (`logistics`, U 2026-10-29: "logistics win wars, size wins
# battles"; forms and numbers C). A state's logistics G = admin x (0.5 +
# statecraft). Sieges per war per tick 1 + floor(LOG_SIEGE x G); the war's
# ending chance x (1 - LOG_END x G / 1.5); projected strength falls with
# distance over 1.5 x reach x (1 + LOG_REACH x G); a failed siege costs
# cohesion 0.02 x (1.5 - G / 1.5).
LOG_SIEGE, LOG_END, LOG_REACH = 2.0, 0.6, 1.0
# Economy (U, 2026-10-29; forms and numbers C). Sites (unique resources
# and domestication hearths) come from sites.json (make_sites.py), or are
# re-drawn from the run seed with --shuffle-sites.
# Domestication (`domestication`): crop and animal packages, each from a
# hearth in one biome. A lineage with people within HEARTH_KM of a hearth
# develops it at DOM_INV x innovation x (1 - level) per year; others
# borrow it at DOM_BORROW like a technology, x (0.3 + 0.7 x share of the
# lineage's people in the package's biome). A package counts fully in its
# own biome and DOM_OFF in others. Farm yield x (DOM_FLOOR + (1 -
# DOM_FLOOR) x crop level); herd density x (DOM_HFLOOR + (1 - DOM_HFLOOR)
# x animal level).
HEARTH_KM, DOM_INV, DOM_BORROW, DOM_OFF = 300.0, 0.002, 0.003, 0.3
DOM_FLOOR, DOM_HFLOOR = 0.5, 0.3
# Craft (`craft`): a technology, 0-1. Invented at CRAFT_INV x
# craftsmanship x (0.5 + patience) x sqrt(min(1, cities / 3)) x (1 -
# craft); borrowed at CRAFT_BORROW; `supply`: lost at CRAFT_DECAY x idle
# share x craft. A crafting lineage counts x (1 + craft) in prestige.
CRAFT_INV, CRAFT_BORROW, CRAFT_DECAY = 0.0006, 0.001, 0.001
# Resources (`resources`): a state whose territory holds a site (cell
# settled) holds that kind; each kind adds RES_VOLUME to its trade volume.
RES_VOLUME = 0.3
# Guarded techniques (`guarded`): a lineage ruling a state of
# GUARD_CITIES+ cities with craft >= GUARD_CRAFT develops one with chance
# GUARD_P per year (at most GUARD_MAX in the world). It leaks to a contact
# at GUARD_LEAK x contact x (1.5 - cohesion) x (1.5 - conformity) of the
# holder per year, and passes to a conqueror taking a holder's city with
# chance GUARD_TAKE (x 2 at its capital).
GUARD_P, GUARD_MAX, GUARD_CRAFT, GUARD_CITIES = 1 / 3000, 6, 0.6, 3
GUARD_LEAK, GUARD_TAKE = 0.0003, 0.25
# Assets of a state: kinds of resource held, ores in hand (ORE_VALUE
# each), craft level and guarded techniques of its ruler. What a offers b:
# kinds b lacks + ORE_VALUE x ores b lacks + max(0, craft_a - craft_b) +
# techniques b lacks. Exchange value X = sqrt(offer(a, b) x offer(b, a)).
ORE_VALUE = 0.3
# Trade (`trade_assets`): ties grow at TRADE_RATE2 (was 0.03) with the
# tolerance need TOL_TRADE2 (was (0.4, 0.15)); acceptance a becomes a +
# (1 - a) x min(1, X / ASSET_X0); growth x (1 + X).
TRADE_RATE2, TOL_TRADE2, ASSET_X0 = 0.045, (0.3, 0.15), 1.0
ASSET_XMAX = 2.0            # growth x (1 + min(X, ASSET_XMAX))
# War (`war_motive`): the old declaration chance (without the dominance
# and hunger terms) x WAR_IDLE, plus a motivated chance DT x 0.012 x
# WAR_GAIN x (0.5 + violence) x S x strength term x (1 - tie) x gain,
# gain = dominance x min(2, their people / ours) + 2 x (1 - fed)
# [climate] + what the target offers the attacker (assets above).
WAR_IDLE, WAR_GAIN = 0.5, 3.0
WAR_GAIN_CAP = 2.0          # the summed motive saturates: g / (1 + g / cap)
# Salinity (`salinity`, U 2026-10-29: realistic depletion; numbers C).
# Salt (0-1) builds on worked irrigated land at SALT_GAIN x intensity x
# irrigated share x (1.5 - patience) x (1 - salt) per year and leaches out
# at SALT_REC x (1 - intensity) x salt. Farm yield x (1 - SALT_MAX x salt
# x irrigated share).
SALT_GAIN, SALT_REC, SALT_MAX = 0.002, 0.003, 0.7
# War goals (`war_goals`, U 2026-10-29; with `war_motive`; numbers C). A
# war is motivated with chance (motivated part) / (whole chance); its goal
# is the largest motive: a resource (the target's city ruling a site of a
# kind the attacker lacks, else its capital), rule (the capital), or land
# (the city nearest the attacker's capital). Sieges go for the goal city;
# once it is taken the war ends with chance WAR_DONE per SPAN years. Before each
# round a weaker defender cedes the goal city (no sack) with chance
# WAR_CEDE x clip(attacker / defender - 1, 0, 1) per SPAN years; rule goals are
# not ceded.
WAR_DONE, WAR_CEDE = 0.8, 0.3
# Two-sided wars (`two_sided`, U 2026-10-30; form and numbers C): in
# each SPAN years of a war the defender strikes back with chance COUNTER_K x R^2 / (1 +
# R^2), R = defender strength / attacker strength; it then lays as many
# sieges as its logistics allow at the attacker's cities, first those it
# lost in this war, nearest its capital first. Odds as for the attacker,
# with the attacker's allies, lord, vassals, terrain and walls defending.
# An attacker that has lost more cities than it took ends the war at
# WAR_DONE per SPAN years ("repulsed").
COUNTER_K = 0.5
# Alliances (U 2026-10-30; forms and numbers C).
# `ally_duty`: when a state is attacked each ally (not allied to the
# attacker) is called; it joins with chance ALLY_J0 + (1 - ALLY_J0) x
# min(1, (ally + defender strength) / attacker strength), else refuses and
# the alliance ends. Only allies who joined help defend; they count as at
# war (experience, war cost) while the war lasts.
# `ally_lapse`: any alliance lapses at ALLY_LAPSE per year.
# `ally_balance`: an alliance formed against a common threat ends at
# ALLY_GONE per year once no common neighbour outweighs the pair; any
# alliance ends at ALLY_OUTGROW x min(1, (ratio - 3) / 3) per year when
# one ally is more than 3 times as strong as the other.
# `betrayal`: allies may attack each other, at BETRAY_K x the usual war
# chance; the alliance ends.
ALLY_J0, ALLY_LAPSE, ALLY_GONE, ALLY_OUTGROW, BETRAY_K = \
    0.3, 0.002, 0.02, 0.01, 0.15
# Experience revisions (U 2026-10-30; forms and numbers C).
# `trade_mean`: the trade a lineage lives with is its state's mean tie
# strength over its neighbouring states, not the sum.
# `tol_path`: contact softens tolerant cultures and hardens intolerant
# ones: of the trade push EXP_TRADE x v, the share phi = sigmoid((tol -
# TOL_PIVOT) / TOL_PW) raises tolerance and 1 - phi lowers it.
# `revolt_exp`: lineages in a state that lost cities to revolt this tick
# (rebels included; share u) harden like raids: violence + EXP_REVOLT x u,
# tolerance - EXP_REVOLT / 2 x u, conformity and separation + EXP_REVOLT
# / 2 x u (separation falls back at EXP_CALM x (1 - war memory)).
# `life_memory`: memory spans x lifespan x (0.5 + patience): experience
# (EXP_MEM), churn (MIS_MEM) and grievance (a lost city counts for
# irredentism for IRR_MEM years x the same factor).
# `spiky`: steady experience change x EXP_BG; at each generation turnover
# (every GEN_LEN x lifespan years) a lineage takes GEN_YEARS years of
# experience change at once, and SPIKE_EVENT years for each major event
# touching its state that tick (war begun, capital lost, revolt,
# disputed succession, plague).
# phi has a floor PHI_MIN (U 2026-10-30: even intolerant societies trade):
# phi = PHI_MIN + (1 - PHI_MIN) x sigmoid. Pivot 0.2 (U, between low and
# middle).
# `trade_floor` (U; number C): trade acceptance = TRADE_FLOOR + (1 -
# TRADE_FLOOR) x the usual acceptance.
TOL_PIVOT, TOL_PW, EXP_REVOLT, IRR_MEM = 0.2, 0.08, 0.01, 150.0
PHI_MIN, TRADE_FLOOR = 0.3, 0.2
EXP_BG, GEN_LEN, GEN_YEARS, SPIKE_EVENT = 0.5, 25.0, 12.5, 10.0
SPIKE_REVOLT = 0.2           # a revolt is a major event if it takes this
                             # share of the state's cities
TRADE_MEAN_K = 3.0           # trade_mean: v = min(1.5, K x mean tie)
# `trait_path` (U 2026-11-01; form and numbers C): experience moves a
# culture less when it runs against what the culture already is. For every
# experience-driven trait, with g = sigmoid((x - pivot) / PATH_PW), pushes
# up are scaled by 2 (PATH_MIN + (1 - PATH_MIN) g) / (1 + PATH_MIN) and
# pushes down by the same with 1 - g: 1 at the pivot, from 0.46 to 1.54
# away from it. Pivot PATH_PIVOT, but TOL_PIVOT for tolerance.
PATH_PIVOT, PATH_PW, PATH_MIN = 0.5, 0.1, 0.6   # PATH_MIN 0.3 ran traits
                                                # to the bounds (cau runs)
# All experience pushes x EXP_SCALE (U 2026-11-01: slow experience so
# inheritance carries more; to be tuned with PATH_MIN).
EXP_SCALE = 0.5
PATH_TOL = 1.0               # 1: tolerance in trait_path too; 0: not
# `devastation` (U 2026-11-01; numbers C): each siege lays waste, with
# chance WASTE_P, the besieged city's cell or a neighbouring cell its
# holder owns. A wasted cell's capacity drops to 0 and recovers linearly
# over WASTE_YEARS.
WASTE_P, WASTE_YEARS = 0.03, 100.0      # 0.03: U 2026-11-01
# Rulers (`rulers`, U 2026-10-30; forms and numbers C). Each state of
# SUCC_MIN_CITIES+ cities (3+ until 2026-11-18) has a succession of
# rulers; reigns last exponential(SUCC_GEN x lifespan) years
# (lifespan: biological roster trait, U). A ruler's death:
# - partition (U): with chance partibility x min(1, cities / PART_N) the
#   realm is split among 2-4 heirs, each taking the cities nearest his
#   seat (partibility: a drifting cultural trait, starting PART0, U);
# - else a disputed succession as before (`succession`), its chance x (1 +
#   LONG_K x max(0, reign / expected reign - 1));
# - provinces test the new ruler: revolt chance x (1 + ACC_K) for
#   ACC_YEARS; neighbours' war chance against the state x (1 + OPP_K x
#   their dominance) for the same years;
# - each alliance lapses with chance ALLY_RENEW x (1 - trade tie);
# - each vassal defects with chance VASSAL_ACC (x 1.5 if foreign);
# - union of crowns: with chance UNION_CROWN x accept(TOL_FUSE) the realm
#   joins one ally under one ruler.
PART0, PART_N, LONG_K, ACC_YEARS, ACC_K, OPP_K = \
    0.1, 6.0, 0.3, 10.0, 1.0, 1.0
ALLY_RENEW, VASSAL_ACC, UNION_CROWN = 0.3, 0.2, 0.01   # U cut, 2026-11-01
# Ruler traits (`ruler_traits`, with `rulers`; U 2026-11-02, forms and
# numbers C). A ruler draws violence, dominance, expansion and statecraft
# in trait units, Student-t (RT_DF) x RT_SD x (1.5 - conformity), reflected
# into [0.01, 0.99] as drift is (U 2026-11-02: trait units, not logit):
# around the culture's mean (population-weighted over the state's lineages
# of his people) when a dynasty begins, else around his predecessor's. A
# disputed succession or pretender ends a dynasty; a state founded by
# revolt starts its own; partition heirs carry it on. Cohesion ages from
# the dynasty's start (was `dynasty`). State decisions read culture + w x
# (ruler - culture) (culture: the ruling lineage), w = min(1, hierarchy x
# (1.5 - conformity)). The state's lineages of his people move toward him
# at RT_PULL x hierarchy x administration per year. Own-people provinces
# revolt x (1 + RT_REVOLT x conformity x gap), gap the RMS distance
# between ruler and the city's lineage. Administration falls by RT_ADMIN
# x his statecraft shortfall per year. RT_SD 0.125 and RT_REVOLT 4 are the
# logit forms' 0.5 and 1 carried over at mid-scale (slope 1/4).
RT_TRAITS = ("viol", "dom", "expn", "state")
RT_DF, RT_SD, RT_PULL, RT_REVOLT, RT_ADMIN = 3.0, 0.125, 0.03, 4.0, 0.004
# Turmoil (`turmoil`, U 2026-11-02; numbers C): the ruling lineage's
# administration x (1 - ADM_LOSS x share) for the share of the state's
# cities lost to war, cession or revolt, and x (1 - ADM_RAID x share of the
# state's cells raided) per tick.
ADM_LOSS, ADM_RAID = 0.5, 0.05
# `revolt_viol` (U 2026-11-02; form C): provincial revolt chance x (0.5 +
# the city lineage's violence).
# Road engineering (`road_tech`, U 2026-11-02; numbers C): a technology
# (0-1), invented at ROADT_INV x innovation x share in a state x (1 -
# level) per year, borrowed at ROADT_BORROW, idle decay as administration.
# A road cell keeps the quality it was built at, ROAD_Q0 + (1 - ROAD_Q0) x
# engineering x (0.8 + 0.2 x administration), blended by stock; travel
# cost x (1 - ROAD_EFFECT x stock x quality).
ROADT_INV, ROADT_BORROW, ROAD_Q0 = 0.001, 0.002, 0.15
# City culture (`city_culture`, U 2026-11-02: cities a nested unit of
# culture; forms and numbers C; docs/open-questions.md). Rates per year.
#   CITY_RURAL    commons toward the residents' lineages x (0.5 + their
#                 conformity) (rural inflow)
#   CITY_NEAR     commons toward nearby similar cities, weights
#                 exp(-km / CITY_NEAR_KM) x similarity x sqrt(size),
#                 saturating at total weight CITY_NEAR_W
#   CITY_TRADE    commons toward trade partners' capitals' commons x trade
#                 volume (<= 1) x (0.5 + 0.5 port or river)
#                 (both x openness (0.5 + tolerance) x (1.5 - conformity))
#   CITY_RULE     a subject city's elite toward its capital's x hierarchy
#   CITY_NOISE    random drift, sd per sqrt(year), commons and elite
#   CITY_DOWN     a lineage toward the commons of its cities x their
#                 people / the lineage's
#   CITY_REVOLT   internal revolt chance x conformity x (gap/CITY_GAP0)^2,
#                 gap the RMS elite-commons distance; the elite keeps
#                 CITY_REVOLT_KEEP of its difference; a subject city then
#                 breaks away with chance CITY_REVOLT_SECEDE
#   CITY_SPEC     RMS commons-home lineage distance that founds a lineage
#   CITY_MOTHER_KM  a new city outside its people's state takes the
#                 culture of the nearest city of its lineage within this
# history.npz (the offline renderer, figures.py war and trade maps, the
# GIS export): a map snapshot every HIST_EVERY ticks, apart from the
# rendered frames (C, WP3 stage A: 5 ticks = 25 years; was 20 = 100
# years). worldsim.py --hist-every overrides it.
HIST_EVERY = 5
# Output is written while the run goes (output.Stream): every FLUSH_EVERY
# ticks (C: 100 ticks = 500 years) and at the end, so a killed run keeps
# its tables up to the last flush. Records only.
FLUSH_EVERY = 100
CITY_MAX = 20000
# U 2026-11-02 (option c): weaker cohesion between cities and weaker
# feedback into lineages, so cities diverge on their own histories and
# city life changes cities more than the countryside. Was CITY_RURAL
# 0.01 (~100-yr pull), CITY_NEAR 0.005, CITY_DOWN 0.01 (C).
CITY_RURAL, CITY_NEAR, CITY_NEAR_KM, CITY_NEAR_W = 0.0033, 0.0025, 300.0, 3.0
CITY_TRADE, CITY_RULE, CITY_NOISE, CITY_DOWN = 0.01, 0.01, 0.002, 0.003
CITY_REVOLT, CITY_GAP0, CITY_REVOLT_KEEP = 0.002, 0.1, 0.25
CITY_REVOLT_SECEDE, CITY_SPEC = 0.5, 0.2
CITY_MOTHER_KM = 600.0
# City life (U 2026-11-02: city-dwelling itself raises tolerance and
# lowers conformity and violence; scaling C). Per year on the commons,
# as experience pushes: tolerance up URB_TOL x diversity (1 - the largest
# lineage's share of the residents); conformity down URB_CONF x size;
# violence down URB_VIOL x size x the state's administration. Size =
# clip(log10(pop / the people's city threshold), 0, 1).
URB_TOL, URB_CONF, URB_VIOL = 0.004, 0.004, 0.004
# Lineage fusion (`lineage_fusion`, U 2026-11-02: fusion is spatial and
# slow, in the zone where two lineages of a people live side by side under
# one state; cultural distance slows it but never bars it; partial
# absorption of a minority zone into the local lineage; numbers C).
#   FUSE_EVERY  years between checks
#   FUSE_K      chance per year at full age, before the modifiers
#   FUSE_T      years under one rule to reach full chance (linear ramp)
#   FUSE_D      RMS distance at which the chance falls by 1/e
#   FUSE_KM     reach of the contact zone from the other lineage's cells
#   FUSE_SHARE  zone share under which the minority is absorbed, not fused
FUSE_EVERY, FUSE_K, FUSE_T, FUSE_D = 50, 0.004, 400.0, 0.15
FUSE_KM, FUSE_SHARE = 300.0, 0.25
# City history (`city_history`, U 2026-11-02: a city remembers what it
# lived through, so it can drift from its lineage on its own history;
# form and numbers C). Experience pushes go into an offset H that decays
# over CITY_HIST years; the rural, neighbour and trade pulls move the
# commons toward their targets + H, so they no longer erase it. H resets
# when the city founds its own lineage. Noise is unchanged (not in H).
CITY_HIST = 500.0
# `city_trade` (U 2026-11-02: per-city exposure; form C): a city's trade
# exposure (its hinterland's states' trade, remembered over EXP_MEM) x
# (0.5 + 0.5 x coastal or river), as CITY_TRADE already weights ports.
# `trade_local` (U 2026-11-03: each city trades most with the foreign
# cities nearest it, so a frontier city can take on its neighbour's ways
# while the heartland does not; form and number C). CITY_TRADE pulls a city
# toward the cities of each partner state, not its capital: partner q
# weighs tie x exp(-km to q's nearest city / CITY_TRADE_KM) and offers the
# mean commons of its cities weighted exp(-km / CITY_TRADE_KM) x
# sqrt(size); volume = min(1, sum of those weights). Off: every city of a
# state is pulled toward the partner capitals at the full tie. Recorded as
# trade_near in citygaps.csv.
CITY_TRADE_KM = 500.0
# `city_influence` (U 2026-11-04: states do not impose their culture;
# each city sways each other by trade volume, trade asymmetry, distance,
# administration and influence, in one pull; forms and numbers C).
# Replaces CITY_NEAR, CITY_TRADE (and trade_local) and CITY_RULE, and the
# ruler pulls only his capital's elite. Weight of j on i =
# sqrt(pop_j) x (contact + CITY_INF_TRADE x trade x asymmetry +
# CITY_INF_ADM x admin):
#   contact   exp(-km / CITY_NEAR_KM) x similarity
#   trade     tie of the two states (CITY_TIE_IN inside one state) x
#             exp(-km / CITY_TRADE_KM) x port_i x port_j
#   asymmetry 2 x j's share of the pair's market reach (sum over partners
#             of trade x sqrt(pop)); 1 for equals
#   admin     i's own capital only: its administration x
#             exp(-km / CITY_ADM_KM)
# Commons move toward the weighted mean of others' commons, elites toward
# others' elites, each at CITY_INF x min(1, total weight / CITY_INF_W) x
# its own openness (0.5 + tolerance) x (1.5 - conformity). CITY_INF is the
# old commons maximum (CITY_NEAR + CITY_TRADE, 0.0025 + 0.01).
CITY_INF, CITY_INF_W, CITY_INF_TRADE, CITY_INF_ADM = 0.0125, 3.0, 1.0, 2.0
CITY_TIE_IN, CITY_ADM_KM = 1.0, 1000.0
# `adm_reach` (U 2026-11-04: administration should expand a capital's
# influence, in reach as well as weight; reach is not a fixed distance:
# roads and sailing extend it, as for maritime empires; numbers C). The
# admin term becomes administration x exp(-d / (ADM_REACH_F x reach)) at
# weight ADM_REACH_W (was CITY_INF_ADM 2 over a fixed CITY_ADM_KM 1000).
# d is the state's travel distance to the city (power_dist: roads cut
# land cost, sailing cuts sea crossings from a coastal seat, provincial
# seats relay); reach is the state's administrative reach (REACH0 +
# REACH1 x administration, cut when underfed, longer with mounted herders
# and allied dragons). At administration 0.75 (the ci median), well fed,
# reach ~800 cost-km, so the scale is ~1600.
ADM_REACH_F, ADM_REACH_W = 2.0, 6.0
# City administration (`city_admin`, needs `city_culture`; U 2026-11-02:
# administration arises in cities, a state inherits from the pool of its
# cities, starting from the capital's and rising quickly toward its
# best-run city at a rate set by hierarchy, resisted by conformity;
# numbers C). Per year: invention ADM_INV x the city's statecraft x (1 -
# level) x sqrt(min(1, state's cities / 5)); borrowing ADM_BORROW x the
# largest gap to a city of another state (x exp(-km / CITY_NEAR_KM)) or a
# trade partner's capital (x tie) x (0.3 + innovation) x (1 - COST_COH x
# cohesion); within a state ADM_UP x hierarchy x (1.5 - conformity)
# toward its best city. A new city starts at its mother's level if the
# mother is in its state, else 0. Losing cities loses their offices, so
# `turmoil` does nothing under `city_admin`.
ADM_INV, ADM_BORROW, ADM_UP = 0.0008, 0.002, 0.02
# Fortresses (`fortress`, U 2026-11-02: Dwarves live in underground
# fortresses and make attackers pay; numbers C). The roster's `fortress`
# (default 0): raiders of its cells lose 0.01 x (1 + FORT_RAID x f) of
# their people instead of 0.01; a state besieging one of its cities loses
# FORT_SIEGE x f x the city's people, taken across its cells.
FORT_RAID, FORT_SIEGE = 4.0, 0.1
# Colonies (`colonies`, U 2026-10-30; form and numbers C): sea settlers
# may also land on thinly held coast (natives < COL_THIN food-
# equivalents) when no empty coast is in reach, with chance COL_OCC per
# voyage, weighted x exp(-natives / COL_THIN); where the
# natives are fewer than the settlers they are pushed out, otherwise the
# settlers become the cell's minority. A colony sent from inside a state
# to another landmass founds a lineage tied to that state (one per state
# and landmass): a city it founds joins the state (chance as for a city
# of the ruler's people).
# Trading posts (`trade_posts`, U 2026-10-30; form and numbers C): each
# tick a state with a coastal city plants a post with chance DT x POST_K
# x trade x sailing: a merchant minority (MIN_POST of the city) in a
# foreign coastal city within 4 x its sailing range that is not a
# neighbour, weighted by city size x exp(-distance / (2 x sailing
# range)). The two states can then trade as if neighbours while the
# merchants stay.
COL_THIN, POST_K, MIN_POST, COL_OCC = 3000.0, 0.02, 0.02, 0.2
# Value of goods (`goods_value`, U 2026-10-30; forms and numbers C). Each
# lineage values each kind of resource at (0.5 + craftsmanship) x its
# preference. Preferences: drawn per people at the start, lognormal
# (median 1, sigma PREF_SD), times a starting bias by kind group (U):
# favoured x PREF_FAV, disdained x PREF_DIS; inherited by lineages with
# drift; each tick lineages under a ruler of another lineage move
# PREF_RULE toward the ruler's, and the rulers of trading states toward
# each other at PREF_TRADE x tie. A kind a state lacks is worth its value
# in trade and as a war prize (in place of 1 each).
# Precious metals (`precious`, U; numbers C; needs sites_v2.json): gold
# and silver sites stack. Each holds a reserve (1 at the start); worked
# while held by a state (lode gold and silver need bronze), it yields
# output = reserve and runs down at MINE_RATE per year (placer gold at
# 2 x MINE_RATE). A state's output O: trade offer + value x O / (1 +
# partner's O) per metal; war prize + value x O; strength x (1 + PREC_STR
# x min(1, O)).
PREF_SD, PREF_FAV, PREF_DIS, PREF_RULE, PREF_TRADE = \
    0.5, 2.0, 0.25, 0.01, 0.01
MINE_RATE, PREC_STR = 1 / 600, 0.3
PREF_GROUPS = dict(
    plant={"incense", "spice", "fragrant timber", "dark hardwood",
           "fine fibre", "cotton fibre"},
    gem={"lapis", "jade", "obsidian", "pearls"},
    metal={"electrum", "placer gold", "lode gold", "silver"},
    animal={"ivory", "purple dye", "pearls"},
    amber={"amber"}, ivory={"ivory"})
PREF_BIAS = dict(                    # U, 2026-10-30
    Elf=dict(fav={"plant", "gem"}),
    Liz=dict(fav={"amber"}),
    Dwf=dict(fav={"gem", "metal"}),
    Gob=dict(fav={"gem", "animal"}, dis={"plant"}),
    Frg=dict(fav={"gem", "animal"}, dis={"plant"}),
    Gnt=dict(fav={"ivory", "metal", "gem"}),
    Ogr=dict(fav={"ivory", "metal", "gem"}),
    Trl=dict(fav={"ivory", "metal", "gem"}))
# Scale (`scale`, U 2026-10-29: big realms develop faster; forms and
# numbers C). Invention of every technology x F = clip((pool /
# SCALE_P0)^SCALE_EXP, SCALE_MIN, SCALE_MAX) x (1 + SCALE_DIV x (D - 1)).
# pool (food-equivalents): the lineage's own people, or for a ruling
# lineage its state's people if more, plus SCALE_TIE x tie x each trade partner's people.
# D: distinct biomes (>= 5% of the cells) of the state it rules (else of
# its own cells) + resource kinds held + landmasses reached - 1. F
# replaces the population-size factor of farming.
SCALE_P0, SCALE_EXP, SCALE_MIN, SCALE_MAX = 1e5, 0.3, 0.3, 5.0
SCALE_TIE, SCALE_DIV = 0.25, 0.05
# Development (`development`, U 2026-10-29: the general gains of
# technology not modelled one by one: building, engineering, canals,
# ports; forms and numbers C). A lineage's development (0-1) = mean of its
# normalized technologies: (farming - 0.25) / 0.75, metallurgy / 3.5,
# sailing, (fishing - 0.1) / 0.9, administration, and with their switches
# craft and its best domestication package. Capacity x (1 + DEV_K x dev);
# city-cell boost x (1 + DEV_CITY x dev of the ruler); a besieged city's
# defence x (1 + DEV_WALL x dev of the defender); trade tie growth x (1 +
# DEV_TRADE x the pair's mean dev).
DEV_K, DEV_CITY, DEV_WALL, DEV_TRADE = 0.25, 0.25, 0.5, 0.5
# Experience (`experience`, U 2026-10-29: trade breeds tolerance, war
# breeds violence and intolerance; 2026-10-30, U: every pushed trait has
# forces both ways, and conformity no longer slows experience; forms and
# numbers C). Per year, for each lineage: s = share of its people in
# states at war; v = the trade volume of the states its people live in
# (people-weighted, at most 1.5), v1 = min(1, v); q = its people's
# hardship this tick (plague, famine); m, h = s and q smoothed over
# EXP_MEM years (war and hardship memory); safety = (1 - m)(1 - h). A rise
# of trait x at rate r is r (1 - x), a fall r x.
#   tolerance   + EXP_TRADE v         - EXP_WAR s + EXP_HARD q + EXP_RAID/2 r
#   trade       + EXP_TRADE/2 v       - 0.00005 (1 - v1)
#   violence    + EXP_WAR s + EXP_RAID r   - EXP_TRADE_V v + EXP_PEACE (1 - m)
#   cohesion    + EXP_WAR/2 s         - EXP_LUX v1 + EXP_CALM (1 - m)
#   hierarchy   + EXP_WAR/2 s         - EXP_CALM (1 - m)
#   conformity  + EXP_WAR/2 s + EXP_HARD q  - EXP_TRADE/2 v1 + EXP_LOOSE safety
# and administration invention x (1 + EXP_ADMIN s).
EXP_TRADE, EXP_WAR, EXP_HARD, EXP_PEACE = 0.0005, 0.001, 0.005, 0.0002
EXP_LUX, EXP_CALM, EXP_LOOSE = 0.0001, 0.00005, 0.0002
# Raids count as experience (U, 2026-10-30): r = share of a lineage's
# people in cells that raided or were raided since the last tick. The
# peace and trade pulls on violence were halved at the same time (C), and
# restored after raid3 (U agreed).
EXP_RAID, EXP_TRADE_V = 0.01, 0.00025
# `causal_exp` (U 2026-11-01: no secular directionality in culture; a
# trait moves only when something causes it, plus random noise; forms
# and numbers C). The terms that ran without a cause are tied to one:
#   violence    peace pull x order (EXP_PEACE (1 - m) only inside an
#               ordered state: order = share in a state x the ruler's
#               administration; stateless peace no longer pacifies)
#   cohesion    calm pull x order
#   conformity  safety pull x order
#   hierarchy   falls with stateless life (EXP_CALM x (1 - in-state
#               share)) instead of with peace
#   separation  falls with trade (EXP_CALM x v1) instead of with peace
#   trade       falls with war and raids (EXP_DISRUPT x (s + r)) instead
#               of when unused
#   superiority no slow fall (EXP_SUP_CALM dropped)
# (The rows above that causal_exp replaced, and EXP_UNUSED and
# EXP_SUP_CALM, were removed from the code 2026-11-17.)
EXP_DISRUPT = 0.0005
# `kin_raids` (U 2026-11-01: raids happen within peoples too; numbers C):
# neighbouring cells of different lineages of one people raid each other
# at KIN_RAID x (0.5 + 0.5 (1 - their similarity)) x the usual chance
# (so 0.05-0.1 of a raid between peoples); `raid_order` (administration,
# borders, peace) applies as to any raid.
# `flat_drift` (U 2026-11-01: no causeless bias, so drift at lineage
# splits adds noise in trait units rather than on the logit scale, which
# leaned toward 0.5; numbers C): trait + N(0, DRIFT_UNIT x sd), reflected
# into [0.01, 0.99]. DRIFT_UNIT 0.625 = the old logit spread (2.5 sd) at
# 0.5. Goods preferences: x exp(e - var/2), mean 1 (was exp(e), mean
# above 1).
DRIFT_UNIT = 0.625
# `goods_appetite` (U 2026-11-01: demand for goods is driven up by craft,
# technology, administration, violence and trade, not by drift; form and
# numbers C). Each lineage's appetite moves (experience memory span)
# toward APP0 + APP_K x the mean of its craft level, development,
# administration, violence and min(1, trade volume); it falls when those
# fall. Value of a kind of goods x appetite.
APP0, APP_K = 0.5, 1.5
# `feuding` (U 2026-11-02: violence carries an internal cost, so that
# stateless peoples can stay violent but vary; form and numbers C). Each
# tick a cell loses DT x FEUD_K x f x (1 - order) of its people, where
# f = clip((violence - FEUD_PIVOT) / (1 - FEUD_PIVOT), 0, 1) and order =
# in a state x the ruler's administration. At violence 0.99 outside a
# state this lowers the settled density to about 0.65-0.8 of capacity
# (growth 0.012-0.02); at 0.8 to about 0.85-0.9. More violent lineages
# lose more, so selection can act on violence within a people.
FEUD_K, FEUD_PIVOT = 0.004, 0.6
# `travel_reach` (U 2026-11-02: roads extend reach, and maritime empires
# must be possible; form and numbers C). A state's hold on a city (revolt
# risk) and its strength there (war) fall with the travel distance from
# its seat(s) of power, not the straight-line distance from the capital.
# Land: cheapest route on the travel graph (relief, biome, rivers, roads,
# straits) / PROV_CR, the median cost per km of unroaded land (measured
# 2026-11-02), so on average a route counts as its length in km and a
# road (travel cost x 0.5 at full stock) halves it. Sea: between coastal
# cells, km x (SEA_F0 - SEA_F1 x the ruler's sailing), 1.5 with no
# sailing, 0.3 at full sailing (ships move 3-5x the pace of armies on
# foot). Unreachable: km x 1.5. Recomputed whenever the seats, the travel
# graph or (for a coastal seat) the ruler's sailing change (2026-11-07;
# was every PROV_EVERY = 2 ticks or when the seats changed, so a state's
# distances could be a tick stale and depended on when they were last
# asked for).
PROV_CR, SEA_F0, SEA_F1 = 2.34, 1.5, 1.2
# `provinces` (U 2026-11-02: provincial reach; form and numbers C).
# Every ROAD_EVERY years a state of 4+ cities names int(PROV_N x admin x
# sqrt(cities)) provincial seats: cities it has held PROV_HOLD+ years,
# chosen greedily for distance from the capital and other seats x
# sqrt(population). Distance to a city = the least, over the capital and
# seats, of PROV_LINK x (capital to seat) + (seat to city). Roads are
# built out from seats as from the capital. A seat that revolts takes
# with it (each with chance 0.6) the cities of its people nearer to it
# than to the capital or any other seat.
PROV_N, PROV_HOLD, PROV_LINK = 0.5, 100, 0.3
# `war_hardy` (U 2026-11-02: a biological trait, Trolls take much less
# from losing fights and wars; number U->C). The roster's `hardy` (default
# 1) scales a people's own losses from raids, war levies, sieges, sacks
# and clearances. Trolls 0.3.
KIN_RAID = 0.1                # 0.5 drove every people to violence ~0.95 by yr 2000 (C)
# Raid order (`raid_order`, U 2026-10-30: raids governed by states and
# peace rather than by a lower experience rate; numbers C). A raid from or
# into a cell inside a state is x (1 - RAID_ADMIN x the ruler's
# administration), each side; across a border between two states, x (1 -
# trade tie), and x RAID_PEACE if they are allied or in truce.
RAID_ADMIN, RAID_PEACE = 0.6, 0.3
# Sod (`sod`, U 2026-10-30: grasslands were herders' country until the
# plough could break the sod; farms clung to rivers and coasts; numbers
# C, the bronze step U): rain-fed farming on grassland x SOD0 before
# bronze, SOD_BR with bronze in use, full with iron. Irrigation untouched.
SOD0, SOD_BR = 0.35, 0.6
EXP_MEM, EXP_ADMIN = 50.0, 1.0
# Mission (`mission`, U 2026-10-30: mixing toward similar cultures; border
# mixing low next to trade and conquest, driven one way by the source's
# proselytism; cultural change breeds unrest; difference and proselytism
# breed war; forms and numbers C). Replaces the contact pull of
# acculturation (foreign rule unchanged). Per year, lineage i moves toward
# each contact j by
#   [MIS_BORDER x Cb_ij x pros_j x S'_ij + MIS_TRADE x Ct_ij x tol_i x S_ij]
#   x (T_j - T_i) / max(1, sum_j (Cb_ij + Ct_ij))  (x (1.5 - conformity))
# Cb: shared borders and minorities; Ct: trade and rule; S: similarity;
# S' = S + MIS_REACH x pros_j x (1 - S). Churn: the summed size of a
# lineage's trait change from mixing and foreign rule, per century,
# smoothed over MIS_MEM years; a state's political stress + MIS_UNREST x
# its people's churn. War motive "faith" = (1 - similarity) x (MIS_HOLY x
# own proselytism + MIS_BACKLASH x target's proselytism x (1 - own
# tolerance)); its goal is the target's capital.
MIS_BORDER, MIS_TRADE, MIS_REACH = 0.0005, 0.002, 0.5
# `rule_weak` (U 2026-11-02: weaken the pull that makes a state's cities
# alike; number C): rule contact (subject lineage <-> ruling lineage) is
# split from trade ties in Ct and moves customs at MIS_RULE instead of
# MIS_TRADE. Off, rule counts as trade (MIS_TRADE). Contact for borrowing
# technology is unchanged.
MIS_RULE = 0.0005
MIS_MEM, MIS_UNREST = 25.0, 10.0
MIS_HOLY, MIS_BACKLASH = 1.0, 1.0
# Land pressure (`land_pressure`, U 2026-10-30: a territory near capacity
# must spread or collapse; dominance sets how full a land must be before
# pressure turns to war; strong states next to much weaker ones are drawn
# to attack, by dominance, fullness and the strength gap; forms and
# numbers C). Room = settleable empty cells (capacity x food per head >
# 200 for the cell's lineage) touching a state's settled cells, / (LP_ROOM
# x its cells), at most 1. Threshold th = LP_HI - LP_SPAN x dominance;
# pressure = clip((crowding - th) / (1 - th), 0, 1) x (1 - room). War
# motives: land + LP_K x pressure; prey = PREY_K x dominance x min(1.2,
# crowding) x clip((strength ratio - 1) / (PREY_R - 1), 0, 1). Both aim at
# the target's city nearest the attacker's capital.
LP_ROOM, LP_HI, LP_SPAN, LP_K = 0.1, 1.0, 0.35, 1.5
PREY_K, PREY_R = 1.5, 3.0
# War, second form (`war_v2`, U 2026-10-30; forms and numbers C). Replaces
# the split into unmotivated and motivated parts of `war_motive`. Chance
# per tick that A declares on B:
#   DT x WAR_BASE x S x (0.5 + violence) x (1 - tie) x deterrence
#      x sat(WAR_EPS + sum of motives),   sat(x) = x / (1 + x / 2)
# deterrence = min(1, 2 R^2 / (1 + R^2))^DET_K (twice the odds of taking
# the city, so an even siege does not deter), R = A's strength projected
# to B's city
# nearest A's capital over B's there (with its allies, x 1.4 x terrain
# defence x walls), as in a siege. Motives:
#   land       (hunger + land pressure) x land value (B's capacity per km2
#              over A's, clipped to [0.5, 2])
#   prey       PREY_K x dominance x min(1.2, crowding) x gap(R)
#   rule       dominance x min(2, B's people / A's)
#   resource   what conquest would give A: B's resource kinds A lacks,
#              ORE_VALUE x ores B works in its territory A lacks, craft
#              gap, guarded techniques A lacks; x (0.5 + dominance)
#   enmity     ENM_K x (1 - similarity) x hostility
#   faith      as under `mission`
#   irredentism  IRR_K x min(1, cities B holds that A once held / 2)
# While at war each side's people lose WAR_COST per year (was 0.005 a
# tick). The chance of declaring is capped at WAR_P_CAP per year (was 0.5
# a tick). Trade tie
# growth x (1.25 - 0.5 x the pair's mean dominance): the domineering take,
# the others trade.
WAR_BASE, WAR_EPS, DET_K = 0.12, 0.004, 1.0
ENM_K, IRR_K, WAR_COST = 1.5, 1.5, 0.001
WAR_P_CAP = 0.1
# Clocks in years (WP5 stage C; values as they were in ticks). A war ended
# by peace, cession, submission or abandonment leaves a truce of
# TRUCE_WAR years; a vassal that breaks away, TRUCE_VASSAL; heirs of a
# partition, TRUCE_HEIRS. Trade ties between states not trading decay by
# TIE_DECAY per SPAN years. Sea adjacency is recomputed every
# SEA_ADJ_EVERY years. A siege kills SIEGE_TOLL of the city's people and a
# failed one costs the besieger SIEGE_COH x (1.5 - logistics / 1.5) of its
# cohesion; both are per siege, not per time.
TRUCE_WAR, TRUCE_VASSAL, TRUCE_HEIRS = 30, 10, 20
TIE_DECAY, SEA_ADJ_EVERY = 0.1, 20
SIEGE_TOLL, SIEGE_COH = 0.03, 0.02
# Yearly political step (`pol_step`, WP5 stage D, 2026-11-18; U: build it,
# sieges with a length; numbers C). Diplomacy, war and rebellion run every
# DT_POL years inside the tick. A siege lasts L = ceil(exponential(
# SIEGE_YEARS x the city's defence)) years, 1 to SIEGE_MAX, the defence
# being terrain x site x walls x 1.25 at a capital (1.4-3 at most
# cities, so a mean of about 2-4 years). The city loses SIEGE_TOLL over
# the whole siege, spread over its years; the siege is decided at its end
# on the odds then. Logistics sets how many sieges a side runs at once
# (1 + floor(LOG_SIEGE x G), as before). Without the switch a siege is
# decided when it is laid, as before.
DT_POL, SIEGE_YEARS, SIEGE_MAX = 1.0, 1.0, 8
# Field armies (`army`, WP5 stage E, 2026-11-18; forms from the review,
# numbers C). A state at war (or helping an ally at war) raises toward
# ARMY_SHARE of its people: each year it closes 1 / ARMY_RAISE of the
# gap, taking the heads from its own people's cells. Out of peace it
# sends all the survivors home. Its field share f = army / (ARMY_SHARE x
# people), 0-1, multiplies the strength it brings to its sieges, and its
# defence of a city by ARMY_GARRISON + (1 - ARMY_GARRISON) x f (walls and
# townsmen hold without a field army). A decided siege costs the side
# that lost it ARMY_LOST and the side that won ARMY_WON of its army. The
# army eats from its own people's harvest: their capacity falls by the
# army's heads / their capacity (at most ARMY_X_MAX), the ledger line
# `taken_army`. Exhaustion: the war's ending chance (per 5 years) is
# WAR_END0 + EXH_K x the larger side's soldiers lost / its people,
# instead of rising with the war's age. Replaces WAR_COST.
ARMY_SHARE, ARMY_RAISE, ARMY_GARRISON = 0.04, 2.0, 0.5
ARMY_WON, ARMY_LOST, ARMY_X_MAX, EXH_K = 0.05, 0.2, 0.5, 25.0
# Camp polities (`camps`, WP5 stage F, 2026-11-18; U: build as camps kept
# outside the city table; a defeated camp scatters or becomes a vassal;
# numbers C; docs/upgrade/WP5F-camps-design.md). Every CAMP_EVERY years
# each lineage's stateless cells within CAMP_R km of its densest
# stateless cell are scored: heads x cohesion trait x (0.5 + hierarchy);
# at CAMP_N or more, with chance CAMP_P, the cells within a new camp's
# reach (cohesion 0.6) are scored again, and at CAMP_N a camp polity
# forms there (first form, 500 km alone: three in four camps dispersed
# at the next check, their land being smaller than the area scored). Its seat
# moves every CAMP_MOVE years to the densest cell of its lineage in its
# land. Reach = CAMP_REACH x cohesion x (1 + CAMP_HERD x herding share)
# (CAMP_REACH: about a one-city state's reach, 120 + 900 x admin 0.2; the
# design note's REACH0 gave one cell). A
# camp takes no rent, tax or tribute (no city to receive it). It cannot
# be besieged: an attacker fights a battle at the seat each year, the
# camp's strength x CAMP_EVADE; a won battle makes it a vassal with
# chance (0.5 + dominance) / 2, else scatters it. It ends "dispersed"
# when its own lineage's score in its land falls under CAMP_N x
# CAMP_END. Taking or founding a city makes it an ordinary state.
# CAMP_N: set from wp5d_seed101's state at year 5,000, where the median
# one-city state's own lineage scores 2.1e4 in its land (run-log.md).
CAMP_EVERY, CAMP_MOVE, CAMP_R, CAMP_P = 25, 10, 500.0, 0.2
CAMP_N, CAMP_END, CAMP_HERD, CAMP_EVADE = 2.1e4, 1 / 3, 1.5, 1.5
CAMP_REACH = 300.0
# Odds-gated war (`war_odds`, WP5 stage B, 2026-11-18; U: build it; forms
# from the review, numbers C). Declaring: the deterrence factor becomes
# floor + (1 - floor) x logistic((ln R - ln ODDS_MID) / ODDS_W), with
# floor = ODDS_FLOOR x min(1, R / ODDS_MID) x min(1, (1 - fed) + enmity +
# faith motives): the hungry, the hating and the zealous still attack at
# long odds, less the longer they are. (A flat floor, first tried, was
# looser than the old 2R^2 / (1 + R^2) below R = 0.16: 13-14% of wars were
# declared at a whole-state strength ratio under 0.5, against 1%.)
# Besieging: a side lays a siege only at win probability >= SIEGE_MIN;
# below it the attacker ravages the target city's hinterland with chance
# = its violence (RAVAGE_K x violence of the people there die, and as
# many improvements fall as in a raid), else it sits. A war with no siege
# for WAR_STALL years ends "abandoned". A defender facing odds >=
# SUBMIT_ODDS sues for terms before the siege with chance SUBMIT_K x
# clip((p - SUBMIT_ODDS) / (1 - SUBMIT_ODDS), 0, 1) x (1.2 - cohesion) x
# (0.5 + the attacker's dominance), and never cedes its last city.
ODDS_MID, ODDS_W, ODDS_FLOOR = 0.7, 0.35, 0.05
SIEGE_MIN, RAVAGE_K, WAR_STALL = 0.15, 0.1, 15.0
SUBMIT_ODDS, SUBMIT_K = 0.6, 1.0
# Site defence (`site_defence`, U 2026-11-18: a random per-city boost for
# whatever in its ground makes it easier or harder to take than terrain
# says; most alike, a few vulnerable, a few very hard; numbers C). Each
# cell draws m = exp(SITE_DEF_SD x t) once, t Student-t with SITE_DEF_DF
# degrees of freedom, clipped to SITE_DEF_LIM; m multiplies the terrain
# defence of a city there wherever a siege, cession or deterrence reads
# it. SITE_DEF_SD was 0.12 until 2026-11-18 (U: widen it a bit). With
# 0.18 half of sites lie within 0.87-1.15 and 9 in 10 within 0.65-1.53;
# 1 in 18 is above 1.5, 1 in 65 above 2.0 and 1 in 230 at the cap of 3;
# 1 in 65 is held at the floor of 0.5.
SITE_DEF_SD, SITE_DEF_DF, SITE_DEF_LIM = 0.18, 3, (0.5, 3.0)
# Ruler generalship (`ruler_mil`, U 2026-11-18: some rulers are better at
# offense; it does not change the chance of war, but at war their state
# punches above its weight, and the edge fades over later reigns; numbers
# C). Each ruler draws a talent g ~ exponential(RULER_MIL_MEAN), capped
# at RULER_MIL_CAP. A state's offense = 1 + g + legacy; at each
# succession legacy becomes RULER_MIL_DECAY x (legacy + the old ruler's
# g). It multiplies the strength the state brings when it besieges
# (attacker's sieges, counter-offensives) and when it presses a cession,
# not its defence nor its deterrence (so not the chance of declaring).
# Half of rulers have g < 0.07; 1 in 20 over 0.3; 1 in 140 over 0.5.
RULER_MIL_MEAN, RULER_MIL_CAP, RULER_MIL_DECAY = 0.1, 1.0, 0.5
# Dragon hosts (`dragon_hosts`, U 2026-10-30): peoples flagged
# dragon_host in the roster never ward off a dragon: their cells are never
# warded (no confrontation), are always hunted (g(n) = n / (n + n0)), and
# never block a dragon's nesting or retreat; young and driven-off dragons
# settle only where every settled cell in reach is of a host people (U,
# 2026-10-30: a refuge only where Frogloks live). A wild dragon whose territory
# holds settled host cells inside a state may still ally with that state:
# chance per year CONFRONT, then the usual tolerance test.
GUARD_NAMES = ["silk", "porcelain", "glass", "lacquer", "fine steel",
               "true dye"]
# Loss by disuse (`supply`, U 2026-10-29: farming, fishing and sailing can
# be lost too): per year, rate x share of the lineage not using it x
# (level - floor). Not using: farming, people in herding cells or below
# AGRI_THIN of capacity; fishing, away from water (1 - waterside share);
# sailing, away from coasts (1 - coastal share).
DECAY_AGRI, DECAY_FISH, DECAY_SAIL = 0.001, 0.001, 0.001
AGRI_THIN = 0.1
DOM_SPARE = 0.5
ACC_CONQ = 0.01
# `acc_cross` (U 2026-11-01: slow mixing between peoples, especially
# between neighbours; very low for 3-4 generations under foreign rule;
# numbers C). Contact acculturation between lineages of different peoples
# x ACC_CROSS. Under a ruler of another people, a cell's pull toward the
# ruler's customs x ACC_RULE0 + (1 - ACC_RULE0) x sigmoid((g - ACC_GENS)
# / 0.5), g = generations the cell has been so ruled (GEN_LEN x the
# subject people's lifespan years each); the clock restarts when the
# ruling or the subject people changes.
ACC_CROSS, ACC_RULE0, ACC_GENS = 0.1, 0.05, 3.5
# `superiority` (U 2026-11-01; form and numbers C): a cultural trait (0-1)
# for how far a culture rejects influence from other peoples. Every pull
# on a lineage from lineages of another people (contact and foreign rule)
# x (1 - its superiority). It drifts at lineage splits (own stream) and
# moves toward the superiority of contacts of the same people only.
# Roster: SUP0 unless set (U: high across the board, Humans and
# Lizardfolk lower; Elves loath to adapt).
SUP0 = 0.75
# `sup_exp` (U 2026-11-01: asymmetries move superiority; rates C). Per
# tick, for the lineages of a state (by population share): + EXP_SUP_WAR
# x the share of its cities it gained from states of another people (a
# vassal's cities / its own when one submits), - EXP_SUP_WAR x the share
# of its cities it lost to them (all when it submits); + EXP_SUP_TRADE x
# adv, adv = min(1, 3 x mean over its trade partners of another people
# of tie x (max(0, dev - partner dev) + max(0, craft - partner craft))),
# and - EXP_SUP_TRADE x the same with the partner ahead (symmetric, U
# 2026-11-01) (dev: technology level 0-1); a slow fall EXP_SUP_CALM
# 0.00005 was dropped under causal_exp.
# Pushes as other experience (spiky, trait_path with pivot 0.5).
EXP_SUP_WAR, EXP_SUP_TRADE = 0.01, 0.0005
SKILL_DOWN = 0.25
SKILLS = ("innovation", "statecraft")
# Plague: a host people; other peoples take PLAGUE_CROSS of the deaths and
# pass it on less readily. Immunity per cell after exposure, decaying
# IMM_DECAY per year; large cities hold endemic immunity IMM_ENDEMIC.
PLAGUE_CROSS = 0.3
# Plague onset: chance PLAGUE_P per year x min(1, urban people / 3M), at
# most once every PLAGUE_GAP years (was 0.04 a tick, 10 ticks). Drought
# relief: each SPAN years the drought factor recovers DROUGHT_REC of its
# gap to 1.
PLAGUE_P, PLAGUE_GAP, DROUGHT_REC = 0.008, 50, 0.35
IMM_HIT, IMM_DECAY, IMM_ENDEMIC = 0.8, 0.012, 0.5
IMM_PROTECT = 0.8           # mortality x (1 - IMM_PROTECT * immunity)
# Epidemics (`epidemic`, WP6 C, all C). Onset: per city per year
# PL_EMERGE x min(1, its people in fe / PL_CCS, a critical community size)
# x (1 + PL_LINK x its state's trade ties, up to 1). Spread per tick: up to
# PL_STEPS rings over land and short sea crossings; chance per infected
# neighbour PL_BETA x d / (d + PL_D0), d people per km2; trade jumps
# PL_JUMP x tie per tick. Mortality drawn from PL_MORT per epidemic (the
# range of the old burst). An epidemic ends when it reaches no new cell,
# or after PL_MAXT years. PLAGUE_P and PLAGUE_GAP serve the old burst
# only (`epidemic` off).
PL_EMERGE, PL_CCS, PL_LINK = 5e-5, 3e4, 1.0
PL_STEPS, PL_BETA, PL_D0, PL_JUMP = 60, 0.9, 1.0, 0.3
PL_MORT, PL_MAXT = (0.15, 0.35), 100
PRICE_EVERY = 100           # years between Price-equation snapshots
# Roads (`roads`): every ROAD_EVERY years each state of 2+ cities builds
# along the cheapest routes from its capital to its cities. A cell's road
# stock (0-1) cuts its travel cost by up to ROAD_EFFECT. Roads last
# ROAD_LIFE years with upkeep (inside a state) and ROAD_LIFE_WILD without.
ROAD_EVERY, ROAD_BUILD, ROAD_EFFECT = 50, 0.6, 0.5   # build x admin per round
ROAD_LIFE, ROAD_LIFE_WILD = 1500.0, 300.0
# Improvements (`improvements`): cleared fields, terraces and canals (0-1).
# Built by farming (faster under capable states), silting away when unused,
# wrecked by sacks and raids. Irrigation reaches IMP_IRR0 of its potential
# without canals; rain-fed farming gains up to IMP_RAIN; settlers prefer
# improved land (x up to 1 + IMP_SETTLE).
IMP_BUILD, IMP_DECAY = 0.003, 1 / 400   # per year
IMP_IRR0, IMP_RAIN, IMP_SETTLE = 0.4, 0.3, 2.0
IMP_SACK = 0.6              # a sack wrecks up to this share, x violence
# Upkeep (`upkeep`, WP6 C, C): works fall in without the hands to keep
# them. Where a cell's people fall below IMP_HANDS of their mean over the
# last IMP_MEM years (exponential), extra decay IMP_LAPSE per year x the
# shortfall ((IMP_HANDS x mean - pop) / (IMP_HANDS x mean)); an emptied
# cell has shortfall 1 (works gone in about a decade).
IMP_HANDS, IMP_LAPSE, IMP_MEM = 0.7, 0.1, 50.0
# Separation as spacing (`separation`, 2026-10-29; U: a separated people
# may be tolerant and trade freely, yet live at low density). A lineage
# fills a cell only to SEP_PREF = 1 - SEP_DENS x separation^2 of its
# capacity (city cells excepted), and moves on or buds off past that. The
# hostile effects separation used to carry (avoiding foreign neighbours,
# raids, war on foreigners, clearance, expulsion) move to (1 - tolerance).
SEP_DENS = 0.8
# Hierarchy (`hierarchy`, C): how steep a society is. Elites grow
# ELITE_G x (0.5 + h); the unrest of a hungry state scales with hierarchy
# (it used statecraft); strength x (HIER_MIL0 + HIER_MIL1 x h), a levy
# raised on command.
HIER_MIL0, HIER_MIL1 = 0.85, 0.3
# Patience (`patience`, C): investment for the long term. Improvements and
# roads are built x (0.5 + p); granaries smooth over STORE_YEARS x admin x
# (0.5 + p) years; land wears x (1.5 - p) (fallowing, care).
# Conformity (`conformity`, C): fidelity of transmission. Drift at lineage
# splits x (1.5 - c); acculturation x (1.5 - c).
# Proselytism (`proselytism`, C): pushing one's customs and identity on
# others. Peoples are near-species here, so it spreads customs and lineage
# identity, not people: in acculturation a contact's pull is weighted
# x (0.5 + p) and adds PROS_PUSH x its proselytism to the receiver's
# openness (tolerance); a ruling lineage absorbs kin lineages x (0.5 + p).
PROS_PUSH = 0.5
# Dragons (`dragons`, 2026-10-29). Large predators, each holding a territory
# (the cells within DRAGON_TERR_KM of its home); homes of wild dragons stay
# DRAGON_SPACE_KM apart. Abundant at the start (U). A wild dragon
# (second form, 2026-10-29, U) cuts the growth rate of a cell's people by
# DRAGON_PEN x g(n) per year, summed over the dragons whose territories
# cover it (U: the same cut for everyone; only fast breeders stay above
# zero; overlap raises it sharply), where
#   g(n) = n / (n + DRAGON_FIND) / (1 + (n / ward) ** 4)
# small bands are seldom found, groups of about `ward` or more are left
# alone (U). ward = WARD0 / (body size x metal x (1 + WARD_STATE x admin
# inside a state)) heads (U: strength, technology, resources). Each warded
# cell in a wild dragon's territory brings a confrontation at CONFRONT per
# year (U: slain, pushed out or allied): alliance needs tolerance >=
# DRAGON_TOL and a state (U: only very tolerant societies), with chance
# (tol - DRAGON_TOL) / (1 - DRAGON_TOL); otherwise slain with chance
# DRAGON_SLAY0 + DRAGON_SLAY1 x violence, else pushed out to a free site
# (lost if none). An allied dragon guards its territory against wild ones
# (U: lower local deaths), lengthens its state's reach (U: administration)
# and multiplies its strength (U: wars): x (1 + k sqrt(dragons)).
# Dragons live to DRAGON_LIFE (U), breed slowly (U) into free sites.
DRAGON_TERR_KM, DRAGON_SPACE_KM = 80.0, 110.0
DRAGON_START = 0.625        # share of free sites held at year 0 (U: high,
                            # not overpowering; 0.8, then 0.5, then 25%
                            # more)
DRAGON_LIFE = 3000.0        # (U) years
DRAGON_MORT = 1 / 10000     # per year, other deaths of wild dragons
DRAGON_ADULT, DRAGON_BREED = 300.0, 1 / 1200  # breeding age; per year
                            # (U: slow, so people can grow in dragon-free
                            # land; 1/500, then 1/1500, then slightly
                            # higher)
DRAGON_GROW = 300.0         # (U) years to full size: a dragon's strength
                            # x min(1, age / DRAGON_GROW), at least 0.05;
                            # small bands can drive off or kill the young
DRAGON_NEST = 0.05          # (U: young need very sparse land) a young
                            # dragon settles only where no cell in reach
                            # holds this share of its (full-size) ward
DRAGON_DISP_KM = 300.0      # scale of offspring and push-out moves
DRAGON_PEN = 0.036          # cut in yearly growth rate per unit of hazard
                            # at the worst group size (U→C: r 0.06 - 0.036
                            # = 0.024, the human rate, under one dragon)
DRAGON_SHUN = 0.0           # if > 0, dragons do not settle (breed or move)
                            # where a cell in reach holds this share of its
                            # ward size or more (C; off by default)
DRAGON_FIND = 150.0         # heads: a band this size is found half as often
WARD0, WARD_STATE = 3000.0, 1.0   # heads that ward off a dragon (human, no
                            # metal, stateless); / (1 + admin) in a state
CONFRONT = 0.01             # per year per warded cell in the territory
DRAGON_FIGHT = 0.02         # share of the cell's people lost in a fight
DRAGON_TOL = 0.75           # tolerance needed for alliance (U: very high)
DRAGON_SLAY0, DRAGON_SLAY1 = 0.3, 0.5
DRAGON_GUARD = 0.9          # share of wild-dragon hazard an ally keeps off
DRAGON_WAR, DRAGON_ADMIN = 1.0, 0.3
# Dragons vary (U), heritably (C). Tolerance and violence are logit-normal
# around their means, strength log-normal around 1; young take after their
# parent with DRAGON_DRIFT (logit / log scale). A dragon's hunting weight is
# strength x (0.5 + violence) x (1.3 - 0.6 tolerance); the ward size
# against it x strength; the odds of slaying it x (0.5 + violence) /
# strength (it stands and fights, but a strong one survives); alliance
# needs the mean of the lineage's and the dragon's tolerance >= DRAGON_TOL;
# an ally's boons scale with the allied dragons' summed strength.
DRAGON_TOL_MEAN, DRAGON_VIOL_MEAN = 0.4, 0.5
DRAGON_TRAIT_SD, DRAGON_STR_SD, DRAGON_DRIFT = 1.0, 0.3, 0.15
# Ward size divides by body size ** WARD_SIZE_EXP (was 1 in the first
# draft; 0.75 makes the ward the same in food-equivalents for every body
# size, so individual strength still counts per head but not per mouth).
WARD_SIZE_EXP = 0.75
# City histories (bookkeeping only; no effect on the model)
CITY_TS_EVERY = 25          # years between rows of city_sizes.csv
SHOCK_WINDOW = 50           # years before a city's end searched for a cause



# seafaring was dropped 2026-11-02 (inert since `dispersal`: expansion
# drives voyages, fishing drives sailing)
TRAITS = ["violence", "expansion", "separation", "cohesion", "statecraft",
          "innovation", "trade", "tolerance"]
TI = {t: k for k, t in enumerate(TRAITS)}
# Traits added 2026-10-29, kept apart from TRAITS (their own array and
# random stream) so runs with them off are unchanged draw for draw. They
# enter acculturation and the Price decomposition, not similarity.
XTRAITS = ["hierarchy", "patience", "conformity", "proselytism", "dominance",
           "craftsmanship"]
XATTR = ("hier", "pati", "conf", "pros", "dom", "crafts")   # XTRAITS order
TRAIT_ATTR = dict(violence="viol", expansion="expn", separation="sep",
                  cohesion="coh", statecraft="state", innovation="innov",
                  trade="trade", tolerance="tol")
MAXL = 60000                # lineage table size
BLOCK = 10                  # settlement regions are BLOCK x BLOCK cells (5 deg)
# Similarity between two lineages: within a people exp(-d/SIM_SAME_SCALE)
# of their trait distance d; between peoples a + b*exp(-d/0.8), capped low.
SIM_SAME_SCALE = 0.8
SIM_OTHER = (0.15, 0.35)
# (share of dissimilarity each side's tolerance must cover, softness)
TOL_TRADE = (0.4, 0.15)
TOL_ALLY = (0.8, 0.08)
TOL_FUSE = (1.0, 0.06)
