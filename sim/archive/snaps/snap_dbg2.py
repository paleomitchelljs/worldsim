"""
Zero-player civilization simulator on world.gpkg.

Full documentation: sim/docs/README.md (rules, traits, startup, data).

Peoples (a roster module, --peoples) start as founding bands and grow,
migrate, farm, found cities, form polities, trade, raid, conquer, clear
land, rebel, and collapse on the 0.5-degree world grid. Nobody plays it;
you watch what the map does.

Three layers, each driving the next:

  people     population, people and lineage per land cell. Peoples never
             mix: a cell holds one people or none. Each people starts as
             several founding groups; each group is a lineage with its own
             slightly different traits and its own technology. Lineages
             split (secession, colonies on new land) with small mutations,
             learn technology from lineages they touch, and are absorbed
             into the ruling lineage of their own people over time. A people can move into
             empty land, or into land another people has lost (raided out,
             cleared by conquest, emptied by famine or plague).
  cities     a cell becomes a city when it is dense and locally central
             (river, coast, ore, trade). Each city rules the land nearest
             to it by travel cost, out to its people's administrative reach.
  polities   a set of cities under one capital, ruled by a lineage.
             Tolerant neighbours trade, ally and may fuse into one state,
             the threshold rising with how unlike they are (kin easily,
             other peoples only if both are highly tolerant). Polities make
             war on
             neighbours (land or, for sailors, sea), take cities, absorb or
             clear conquered foreigners, trade with partners, and fragment
             when cohesion (asabiya) runs down and provinces lie far from
             the capital.

One tick is DT years. The world file is opened read-only.

Run:  ~/.venvs/worldsim/bin/python worldsim.py --seed 1 --years 4000
Out:  sim/runs/seed<N>/  (history.gif, final.png, legacy.png,
      population.png, events.txt, cities.csv, polities.csv, timeseries.csv)
"""
import argparse
import importlib
import csv
import json
import math
import os
import sqlite3
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, signal, sparse
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from peoples import PEOPLES  # noqa: E402

GPKG = os.path.join(HERE, "..", "gis", "world.gpkg")
NY, NX = 360, 720
R_EARTH = 6371.0
BIOMES = ["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra"]

# ---- assumptions ---------------------------------------------------------
DT = 5                      # years per tick
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

# ---- structural mechanics (draft, 2026-10-29; docs/rules/*.md) -----------
# Each can be switched off with --off NAME[,NAME...]; with all of them off,
# the model is the pre-structural one, draw for draw.
FEATURES = ["costs", "fiscal", "unrest", "succession", "vassals", "balance",
            "pastoral", "land", "climate", "supply", "minority",
            "acculturation", "immunity", "diagnostics", "roads",
            "improvements", "dragons", "separation", "hierarchy",
            "patience", "conformity", "proselytism", "dispersal", "fishing",
            "dominance", "ore_trade", "food_units", "shuffle", "dynasty",
            "logistics", "domestication", "craft", "resources", "guarded",
            "trade_assets", "war_motive", "salinity", "war_goals",
            "scale", "development", "density_cap", "experience",
            "mission", "dragon_hosts", "land_pressure", "war_v2",
            "raid_order", "sod", "two_sided", "ally_duty", "ally_lapse",
            "ally_balance", "betrayal", "trade_mean", "tol_path",
            "revolt_exp", "life_memory", "spiky", "rulers", "colonies",
            "trade_posts", "goods_value", "precious", "trade_floor",
            "trait_path", "devastation", "acc_cross"]
# Trait costs. Cohesion slows borrowing from outsiders; statecraft's
# extraction raises unrest when the state is underfed; violence raises the
# chance of a succession crisis; expansion leaves thin frontier cells more
# exposed to raids.
COST_COH = 0.5              # borrowing x (1 - COST_COH * cohesion)
COST_STATE = 2.0            # unrest x (1 + COST_STATE * statecraft * hunger)
COST_EXPN = 0.8             # raid damage x (1 + COST_EXPN * expn * thinness)
# Fiscal: a state's strength and reach follow its fed population, not its
# head count. fed = sum(pop * min(1, K/pop)) / sum(pop), smoothed.
FISC_EMA = 0.2              # weight of this tick in the smoothed value
# Structural-demographic unrest (Goldstone, Turchin). Elites grow when the
# land is crowded (cheap labour, high rents) and shrink otherwise; political
# stress = crowding x elite load, and multiplies the revolt hazard.
ELITE_G = 0.004             # per year, elite growth per unit crowding excess
ELITE_CROWD = 0.75          # crowding at which elites neither grow nor shrink
UNREST = 3.0                # revolt hazard x (1 + UNREST * stress)
# Succession: per-generation chance of a crisis in states of 3+ cities.
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
ABRUPT_RATE = 1 / 2000      # abrupt dry events per year (8.2/4.2/3.2 ka-like)
ABRUPT_YEARS, ABRUPT_AMP = (150, 400), (1.5, 2.5)   # length, depth in sd
ABRUPT_RAMP = (25, 75)      # years to set in, years to lift
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
# kept, but use lapses after SUPPLY_GRACE ticks without supply. Without
# cities, administration and metallurgy decay.
SUPPLY_GRACE = 4
DECAY_ADMIN, DECAY_METAL = 0.002, 0.0004   # per year, scaled by city loss
# Minorities: one secondary people per cell, up to MIN_CAP of the cell's K.
MIN_CAP = 0.2
MIN_GARRISON = 0.04         # of the city, settled by a conqueror
MIN_MERCHANT = 0.03         # of a city, x tie, from a trade partner people
MIN_EXPEL = 0.01            # per year x ruler separation x (1 - tolerance)
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
# once it is taken the war ends with chance WAR_DONE per tick. Before each
# round a weaker defender cedes the goal city (no sack) with chance
# WAR_CEDE x clip(attacker / defender - 1, 0, 1) per tick; rule goals are
# not ceded.
WAR_DONE, WAR_CEDE = 0.8, 0.3
# Two-sided wars (`two_sided`, U 2026-10-30; form and numbers C): each tick
# of a war the defender strikes back with chance COUNTER_K x R^2 / (1 +
# R^2), R = defender strength / attacker strength; it then lays as many
# sieges as its logistics allow at the attacker's cities, first those it
# lost in this war, nearest its capital first. Odds as for the attacker,
# with the attacker's allies, lord, vassals, terrain and walls defending.
# An attacker that has lost more cities than it took ends the war at
# WAR_DONE per tick ("repulsed").
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
PATH_PIVOT, PATH_PW, PATH_MIN = 0.5, 0.1, 0.3
# `devastation` (U 2026-11-01; numbers C): each siege lays waste, with
# chance WASTE_P, the besieged city's cell or a neighbouring cell its
# holder owns. A wasted cell's capacity drops to 0 and recovers linearly
# over WASTE_YEARS.
WASTE_P, WASTE_YEARS = 0.03, 100.0      # 0.03: U 2026-11-01
# Rulers (`rulers`, U 2026-10-30; forms and numbers C). Each state of 3+
# cities has a ruler; reigns last exponential(SUCC_GEN x lifespan) years
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
# Density cap (`density_cap`, U 2026-10-29: a hard limit per cell whatever
# the technology; numbers C): capacity at most DENS_MAX food-equivalents
# per km2, DENS_MAX_CITY in city cells.
DENS_MAX, DENS_MAX_CITY = 150.0, 500.0
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
#   trade       + EXP_TRADE/2 v       - EXP_UNUSED (1 - v1)
#   violence    + EXP_WAR s + EXP_RAID r   - EXP_TRADE_V v + EXP_PEACE (1 - m)
#   cohesion    + EXP_WAR/2 s         - EXP_LUX v1 + EXP_CALM (1 - m)
#   hierarchy   + EXP_WAR/2 s         - EXP_CALM (1 - m)
#   conformity  + EXP_WAR/2 s + EXP_HARD q  - EXP_TRADE/2 v1 + EXP_LOOSE safety
# and administration invention x (1 + EXP_ADMIN s).
EXP_TRADE, EXP_WAR, EXP_HARD, EXP_PEACE = 0.0005, 0.001, 0.005, 0.0002
EXP_UNUSED, EXP_LUX, EXP_CALM, EXP_LOOSE = 0.00005, 0.0001, 0.00005, 0.0002
# Raids count as experience (U, 2026-10-30): r = share of a lineage's
# people in cells that raided or were raided since the last tick. The
# peace and trade pulls on violence were halved at the same time (C), and
# restored after raid3 (U agreed).
EXP_RAID, EXP_TRADE_V = 0.01, 0.00025
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
# While at war each side's people lose WAR_COST per tick. Trade tie
# growth x (1.25 - 0.5 x the pair's mean dominance): the domineering take,
# the others trade.
WAR_BASE, WAR_EPS, DET_K = 0.12, 0.004, 1.0
ENM_K, IRR_K, WAR_COST = 1.5, 1.5, 0.005
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
SKILL_DOWN = 0.25
SKILLS = ("innovation", "seafaring", "statecraft")
# Plague: a host people; other peoples take PLAGUE_CROSS of the deaths and
# pass it on less readily. Immunity per cell after exposure, decaying
# IMM_DECAY per year; large cities hold endemic immunity IMM_ENDEMIC.
PLAGUE_CROSS = 0.3
IMM_HIT, IMM_DECAY, IMM_ENDEMIC = 0.8, 0.012, 0.5
IMM_PROTECT = 0.8           # mortality x (1 - IMM_PROTECT * immunity)
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


def unit_xyz(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo),
                     np.sin(la)], -1)


def gc_km(xyz, i, j):
    """Great-circle km between cell i and cells j."""
    ch = np.linalg.norm(xyz[j] - xyz[i], axis=-1)
    return 2 * R_EARTH * np.arcsin(np.clip(ch / 2, 0, 1))


TRAITS = ["violence", "expansion", "separation", "cohesion", "statecraft",
          "innovation", "seafaring", "trade", "tolerance"]
TI = {t: k for k, t in enumerate(TRAITS)}
# Traits added 2026-10-29, kept apart from TRAITS (their own array and
# random stream) so runs with them off are unchanged draw for draw. They
# enter acculturation and the Price decomposition, not similarity.
XTRAITS = ["hierarchy", "patience", "conformity", "proselytism", "dominance",
           "craftsmanship"]
TRAIT_ATTR = dict(violence="viol", expansion="expn", separation="sep",
                  cohesion="coh", statecraft="state", innovation="innov",
                  seafaring="seaf", trade="trade", tolerance="tol")
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


def vary_peoples(peoples, seed, amount):
    """Jitter every people's cultural traits for one run, on the logit
    scale by N(0, amount), so archetypes bend without all collapsing to the
    middle. Intrinsic traits (r, biome affinity, size) are left as given."""
    if amount <= 0:
        return [dict(p) for p in peoples]
    rng = np.random.default_rng(10_000 + seed)
    out = []
    for p in peoples:
        q = dict(p)
        for t in TRAITS:
            x = np.clip(p.get(t, 0.5), 0.02, 0.98)
            z = math.log(x / (1 - x)) + rng.normal(0, 2.5 * amount)
            q[t] = round(float(1 / (1 + math.exp(-z))), 2)
        out.append(q)
    xr = np.random.default_rng(20_000 + seed)
    for p, q in zip(peoples, out):
        for t in XTRAITS:
            x = np.clip(p.get(t, 0.5), 0.02, 0.98)
            z = math.log(x / (1 - x)) + xr.normal(0, 2.5 * amount)
            q[t] = round(float(1 / (1 + math.exp(-z))), 2)
    return out


# ---- world ---------------------------------------------------------------
class World:
    def __init__(self, gpkg=GPKG):
        con = sqlite3.connect(f"file:{os.path.abspath(gpkg)}?mode=ro",
                              uri=True)
        cols = ["row", "col", "lon", "lat", "area_km2", "fic_land",
                "fic_elev_km", "fic_biome", "fic_soil_bar_value",
                "syn_relief_km", "syn_discharge_m3s", "syn_river",
                "syn_lake", "syn_reach_productivity", "syn_dist_copper_km",
                "syn_dist_tin_km", "syn_dist_iron_km", "syn_surface_lith",
                "syn_alluvial_fill", "syn_runoff_m_yr", "fid",
                "syn_flow_to", "syn_basin_id", "syn_wetness",
                "fic_dist_coast_km"]
        rows = con.execute(f"select {','.join(cols)} from cells").fetchall()
        con.close()
        d = {c: [r[k] for r in rows] for k, c in enumerate(cols)}

        def num(c, fill=0.0):
            a = np.array([fill if v is None else v for v in d[c]], float)
            return np.where(np.isfinite(a), a, fill)

        row = num("row").astype(int)
        col = num("col").astype(int)
        land2 = np.zeros((NY, NX), bool)
        land2[row, col] = num("fic_land") > 0
        prod2 = np.zeros((NY, NX))
        prod2[row, col] = num("syn_reach_productivity")
        self.land2 = land2

        L = num("fic_land") > 0
        self.row, self.col = row[L], col[L]
        self.lon, self.lat = num("lon")[L], num("lat")[L]
        self.area = num("area_km2")[L]
        self.elev = num("fic_elev_km")[L]
        self.relief = num("syn_relief_km")[L]
        # swamp layer (derive_world.swamp_wetness): 0-1
        self.wet = num("syn_wetness")[L]
        self.Q = num("syn_discharge_m3s")[L]
        self.river = num("syn_river")[L] > 0
        # river network: downstream land cell (or -1) and upstream river
        # cells, for travel along rivers; basin ids for river trade
        fid = num("fid").astype(np.int64)
        fl = num("syn_flow_to", -1).astype(np.int64)
        lidx = {int(f) - 1: k for k, f in enumerate(fid[L])}  # flow_to is
        # a 0-based cell index (fid - 1)
        down = np.array([lidx.get(int(t), -1) for t in fl[L]])
        # full drainage network (every land cell), for routing discharge
        # and for rivers that change course
        self.flow = down.copy()
        self.runoff = num("syn_runoff_m_yr", 0.4)[L]
        self.alluvial = num("syn_alluvial_fill")[L] > 0
        self.basin = num("syn_basin_id", -1).astype(np.int64)[L]
        self.lake = num("syn_lake")[L] > 0
        self.d_cu = num("syn_dist_copper_km", 9e9)[L]
        self.d_sn = num("syn_dist_tin_km", 9e9)[L]
        self.d_fe = num("syn_dist_iron_km", 9e9)[L]
        soil = num("fic_soil_bar_value", np.nan)[L]
        biome = np.array(d["fic_biome"], object)[L]
        lith = np.array(d["syn_surface_lith"], object)[L]
        self.biome = np.array([BIOMES.index(b) if b in BIOMES else 4
                               for b in biome])
        self.N = N = L.sum()
        self.xyz = unit_xyz(self.lon, self.lat)
        self.yield_ = self.runoff * self.area * 1e6 / 3.156e7   # m3/s
        self.route()

        idx = -np.ones((NY, NX), int)
        idx[self.row, self.col] = np.arange(N)
        self.idx2 = idx
        offs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1),
                (1, 0), (1, 1)]
        nb = -np.ones((N, 8), int)
        nd = np.zeros((N, 8))
        coastal = np.zeros(N, bool)
        coast_prod = np.zeros(N)
        for k, (dr, dc) in enumerate(offs):
            r2 = self.row + dr
            c2 = (self.col + dc) % NX
            ok = (r2 >= 0) & (r2 < NY)
            r2c = np.clip(r2, 0, NY - 1)
            nb[:, k] = np.where(ok, idx[r2c, c2], -1)
            sea = ok & ~land2[r2c, c2]
            coastal |= sea
            coast_prod = np.maximum(coast_prod,
                                    np.where(sea, prod2[r2c, c2], 0))
            dy = 0.5 * 111.2 * dr
            dx = 0.5 * 111.2 * np.cos(np.radians(self.lat)) * dc
            nd[:, k] = np.maximum(np.hypot(dx, dy), 1.0)
        self.nb, self.coastal = nb, coastal
        self.nd = nd
        self.defence = np.array([TERRAIN_DEF[b] for b in BIOMES])[self.biome] \
            * (1 + DEF_RELIEF * np.clip(self.relief, 0, 1.5)) * \
            (1 + DEF_WET * self.wet)
        self.colonize = np.exp(-np.clip(self.relief, 0, None) / COL_RELIEF) \
            * (1 - COL_WET * self.wet)

        # undirected edge list (each land pair once)
        e1, e2, ek = [], [], []
        for k in (2, 4, 6, 7):          # NE, E, S, SE
            j = nb[:, k]
            m = j >= 0
            e1.append(np.nonzero(m)[0]); e2.append(j[m])
            ek.append(np.full(int(m.sum()), k))
        self.E1, self.E2 = np.concatenate(e1), np.concatenate(e2)
        self.EK = np.concatenate(ek)

        # short sea crossings between coastal cells
        ci = np.nonzero(coastal)[0]
        self.coast_idx = ci
        self.coast_tree = cKDTree(self.xyz[ci])
        pairs = np.array(sorted(self.coast_tree.query_pairs(
            2 * math.sin(STRAIT_KM / R_EARTH / 2))), int)
        if len(pairs):
            a, b = ci[pairs[:, 0]], ci[pairs[:, 1]]
            dkm = 2 * R_EARTH * np.arcsin(np.clip(np.linalg.norm(
                self.xyz[a] - self.xyz[b], axis=1) / 2, 0, 1))
            far = dkm > 90          # not already a land neighbour
            sa, sb, sw = a[far], b[far], 2.0 * dkm[far]
        else:
            sa = sb = sw = np.array([], int)
        self.sea_links = (sa, sb, sw)

        # landmasses (for logging first landings)
        lab, nlab = ndimage.label(land2, structure=np.ones((3, 3)))
        self.landmass = lab[self.row, self.col]
        self.landmass_area = np.bincount(self.landmass, weights=self.area)

        # ---- carrying capacity (people/km2) before people-specific terms
        # (the parts that do not depend on rivers; derive_rivers does the
        # rest, and runs again whenever a river changes course)
        self.fert = np.where(np.isfinite(soil), np.clip((soil + 3.75) / 5.5,
                                                        0, 1), 0.3)
        b = self.biome
        self.pn = np.clip((coast_prod - 0.0003) / 0.0006, 0, 1)
        self.elevpen = np.clip(1 - (self.elev - 1.5) / 1.5, 0.2, 1) / \
            (1 + 0.5 * np.clip(self.relief, 0, 2))
        alluv = np.array([l == "alluvium" for l in lith])
        self.wetf = np.where(alluv, 1.3, 1.0) * np.where(self.lake, 1.2, 1.0)
        # structural layers: steppe farming (rain-fed part cut far inland on
        # grassland and desert), herding density, dryness
        self.dcoast = num("fic_dist_coast_km", 0.0)[L]
        steppe = np.clip((self.dcoast - STEPPE_KM[0]) /
                         (STEPPE_KM[1] - STEPPE_KM[0]), 0, 1) * \
            np.isin(b, [BIOMES.index("Grassland"), BIOMES.index("Desert")])
        self.steppe = steppe
        self.herd = np.array([HERD[x] for x in BIOMES])[b] * \
            np.clip(1 - (self.elev - 2.5) / 1.5, 0.2, 1) * \
            (1 + 0.5 * steppe)
        self.dryness = np.clip(1 - self.runoff / 0.5, 0, 1)
        self.ecotones(land2)
        self.derive_rivers()

        # rendering base
        base = np.zeros((NY, NX, 3), np.uint8)
        base[:] = (28, 48, 78)
        bcol = np.array([(62, 96, 58), (176, 160, 118), (128, 138, 84),
                         (84, 112, 72), (176, 182, 184)], np.uint8)
        base[self.row, self.col] = bcol[b]
        shade = np.clip(1 - 0.25 * np.clip(self.relief, 0, 1.5), 0.6, 1)
        base[self.row, self.col] = (base[self.row, self.col] *
                                    shade[:, None]).astype(np.uint8)
        self.base = base
        rows_land = np.nonzero(land2.sum(1) > 40)[0]
        self.r0 = max(0, rows_land.min() - 8)
        self.r1 = min(NY, rows_land.max() + 4)


    # ---- rivers
    def route(self):
        """Topological levels of the drainage network: a cell's level is
        one more than the highest level draining into it."""
        N, down = self.N, self.flow
        deg = np.bincount(down[down >= 0], minlength=N)
        level = np.zeros(N, int)
        front = list(np.nonzero(deg == 0)[0])
        order = []
        while front:
            nxt = []
            for i in front:
                order.append(i)
                j = down[i]
                if j >= 0:
                    level[j] = max(level[j], level[i] + 1)
                    deg[j] -= 1
                    if deg[j] == 0:
                        nxt.append(j)
            front = nxt
        self.order = np.array(order)
        self.levels = [np.nonzero((level == lv) & (down >= 0))[0]
                       for lv in range(level.max() + 1)]

    def accumulate(self, v):
        """Sum v over each cell and everything upstream of it."""
        acc = v.astype(float).copy()
        for c in self.levels:
            np.add.at(acc, self.flow[c], acc[c])
        return acc

    def derive_rivers(self):
        """Everything that depends on where the rivers run: river links,
        foraging and irrigation, city locus and travel costs."""
        N, b = self.N, self.biome
        coastal, pn = self.coastal, self.pn
        self.down = np.where(self.river, self.flow, -1)
        self.down[self.down >= 0] = np.where(
            self.river[self.down[self.down >= 0]], self.down[self.down >= 0],
            -1)
        self.up = [[] for _ in range(N)]
        for k in np.nonzero(self.down >= 0)[0]:
            self.up[self.down[k]].append(int(k))
        near_river = self.river | (self.Q > 50)
        forage = np.array([FORAGE[x] for x in BIOMES])[b] * \
            (1 + 2.0 * coastal * pn) * (1 + 0.8 * near_river)
        farm = FARM_MAX_DENS * self.fert ** 1.3 * \
            np.array([FARM[x] for x in BIOMES])[b] * self.elevpen
        irr = IRRIG_MAX_DENS * np.sqrt(np.clip(self.Q / 3000, 0, 1)) * \
            np.array([IRRIG[x] for x in BIOMES])[b] * self.river
        wetf = self.wetf
        rain = farm
        farm = (rain + irr) * wetf + 1.0 * coastal * pn
        self.forage, self.farm = forage, farm
        steppe = self.steppe
        self.farm_steppe = (rain * (1 - (1 - STEPPE_MIN) * steppe) + irr) * \
            wetf + 1.0 * coastal * pn
        self.irr_share = np.clip(irr * wetf / np.maximum(farm, 1e-9), 0, 1)
        # the same, in parts, for the climate to scale separately
        self.rain_w = rain * wetf
        self.rain_ws = rain * (1 - (1 - STEPPE_MIN) * steppe) * wetf
        self.irr_w = irr * wetf
        self.fish = 1.0 * coastal * pn
        # waterside: coasts (more where the sea is rich), rivers, lakes
        self.water = np.maximum.reduce([coastal * (0.5 + 0.5 * pn),
                                        self.river * 1.0, self.lake * 1.0,
                                        (self.Q > 50) * 0.5])
        self.locus = (1 + 0.6 * self.river + 0.4 * coastal +
                      0.3 * (np.minimum(self.d_cu, self.d_sn) < 150) +
                      0.2 * (self.d_fe < 100))
        self.travel()

    def travel(self, road=None):
        """Travel cost per cell (biome, relief, rivers, and roads if
        given as a 0-1 cost multiplier), then per edge, and the graph."""
        N, nb, nd = self.N, self.nb, self.nd
        if road is None:
            road = getattr(self, "road", None)
        tc = (1 + 1.5 * np.clip(self.relief, 0, 2)) * \
            np.array([MOVE[b] for b in BIOMES])[self.biome]
        tc = np.where(self.river, 0.7 * tc, tc)
        if road is not None:
            tc = tc * road
        ec = np.zeros((N, 8))
        for k in range(8):
            j = nb[:, k]
            ec[:, k] = np.where(j >= 0, nd[:, k] * 0.5 *
                                (tc + tc[np.maximum(j, 0)]), np.inf)
        self.edgecost = ec
        EW = ec[self.E1, self.EK]
        sa, sb, sw = self.sea_links
        I = np.concatenate([self.E1, self.E2, sa, sb])
        J = np.concatenate([self.E2, self.E1, sb, sa])
        Wt = np.concatenate([EW, EW, sw, sw])
        self.G = sparse.csr_matrix((Wt, (I, J)), shape=(N, N))

    def reroute(self, i, j):
        """Cell i now drains to j (-1: straight to the sea). Discharge,
        rivers, basins and everything derived from them are recomputed."""
        self.flow[i] = j
        self.route()
        self.Q = self.accumulate(self.yield_)
        darea = self.accumulate(self.area)
        self.river = (self.Q > 300) & (darea > 30000) & ~self.lake
        basin = np.arange(self.N)
        for k in self.order[::-1]:
            if self.flow[k] >= 0:
                basin[k] = basin[self.flow[k]]
        self.basin = basin
        self.derive_rivers()

    def ecotones(self, land2):
        """For each cell, the biome a drier or a wetter climate would push
        it toward, and how close that biome is (1 next door, falling off
        over a few cells)."""
        dist = {}
        for k, nm in enumerate(BIOMES):
            g = np.ones((NY, NX), bool)
            g[self.row[self.biome == k], self.col[self.biome == k]] = False
            dist[nm] = ndimage.distance_transform_edt(g)[self.row, self.col]
        drier = {"Jungle": ["Grassland"], "Temperate forest": ["Grassland"],
                 "Grassland": ["Desert"]}
        wetter = {"Desert": ["Grassland"],
                  "Grassland": ["Temperate forest", "Jungle"]}
        for nm, table in (("dry", drier), ("wet", wetter)):
            tgt = -np.ones(self.N, int)
            prox = np.zeros(self.N)
            for k, b in enumerate(BIOMES):
                m = self.biome == k
                for t in table.get(b, []):
                    d = dist[t]
                    p = np.exp(-(np.maximum(d, 1) - 1) / 2.0)
                    better = m & (p > prox)
                    tgt[better] = BIOMES.index(t)
                    prox[better] = p[better]
            setattr(self, f"eco_{nm}", tgt)
            setattr(self, f"eco_{nm}_prox", prox)


# ---- simulation ----------------------------------------------------------
def dsig(x):
    """Logistic, for arrays."""
    return 1 / (1 + np.exp(-np.clip(x, -50, 50)))


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-50.0, min(50.0, x))))


def logistic(p, k, r):
    """Population after one tick of logistic growth at rate r toward
    capacity k. Where r < 0 (a dragon's toll above a people's growth
    rate) the people decline at that rate, and never above k: the closed
    form with r < 0 makes k a repeller, and cells above it ran off to
    huge or negative numbers for a tick (bug found 2026-11-01)."""
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        e = np.exp(-r * DT)
        up = k * p / (p + (k - p) * e)
        return np.where(r >= 0, up, np.minimum(p * np.exp(r * DT), k))


class Sim:
    def __init__(self, world, seed=1, years=6000, frame_every=10, out=None,
                 homelands="continents", peoples=None, start_pool=0.0,
                 starts=3, start_vary=0.05, drift=0.06, cluster_km=0.0,
                 settle_drift=0.03, size_food="kleiber", start_mode="wander",
                 wander_steps=2000, off=(), shuffle_sites=False,
                 sites="sites.json"):
        self.W = W = world
        self.on = set(FEATURES) - set(off)
        # under dispersal, seafaring is no longer a trait that counts
        self.simmask = np.array([t != "seafaring" for t in TRAITS], float)
        self.homelands = homelands
        self.start_pool = start_pool
        self.starts = starts
        self.start_vary = start_vary
        self.drift = drift
        self.cluster_km = cluster_km
        self.settle_drift = settle_drift
        self.start_mode = start_mode
        self.wander_steps = wander_steps
        self.shuffle_sites = shuffle_sites
        self.sites_file = sites
        self.size_food = size_food
        self.vary = 0.0
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.years = years
        self.frame_every = frame_every
        self.out = out
        P = self.P = peoples
        self.nP = nP = len(P)
        self.keys = [p["key"] for p in P]
        self.colors = np.array([p["color"] for p in P], np.uint8)
        self.pT = np.array([[p.get(t, 0.5) for t in TRAITS] for p in P])
        self.pr = np.array([p["r"] for p in P], float)
        self.paff = np.array([[p["affinity"].get(b, 1.0) for b in BIOMES]
                              for p in P])
        # body size: combat worth per head relative to a human. With
        # size_food="kleiber" each head also eats size**0.75 humans' food,
        # so the land carries fewer large bodies.
        self.psize = np.array([p.get("size", 1.0) for p in P], float)
        self.pwet = np.array([p.get("wet", 0.0) for p in P], float)
        self.phost = np.array([bool(p.get("dragon_host", False))
                               for p in P])
        # city threshold per people, in heads: CITY_POP food-equivalents,
        # times the roster's optional `city` factor (>1 = founds fewer)
        self.pcity = None
        self.peat = np.array([p.get("eat", p.get("size", 1.0) ** 0.75
                                    if size_food == "kleiber" else 1.0)
                              for p in P], float)

        # lineages: one row each; traits and technology live here
        nT = len(TRAITS)
        self.LT = np.zeros((MAXL, nT))
        self.Lr = np.zeros(MAXL)
        self.Laff = np.ones((MAXL, len(BIOMES)))
        self.Lbest = np.ones(MAXL)       # best biome affinity (cached)
        self.Lpeople = -np.ones(MAXL, int)
        self.Lparent = -np.ones(MAXL, int)
        self.Lfounded = np.zeros(MAXL, int)
        self.Lended = -np.ones(MAXL, int)
        self.Lhow = []
        self.Lcol = np.zeros((MAXL, 3), np.uint8)
        self.Lpeak = np.zeros(MAXL)
        self.Lseen = {}
        self.Pblk = [set() for _ in P]   # regions each people has held
        self.agri = np.zeros(MAXL)
        self.metal = np.zeros(MAXL)
        self.sail = np.zeros(MAXL)
        self.fishing = np.zeros(MAXL)
        self.craft = np.zeros(MAXL)
        self.ore_has = np.zeros((MAXL, 3), bool)
        self.admin = np.zeros(MAXL)
        self.bronze = np.zeros(MAXL, bool)
        self.iron = np.zeros(MAXL, bool)
        self.steel = np.zeros(MAXL, bool)
        # supply: stages known (kept for good) and ticks each in-use stage
        # has gone without its ores or cities
        self.known = np.zeros((MAXL, 3), bool)
        self.lack = np.zeros((MAXL, 3), int)
        self.nL = 0
        for t, k in TI.items():           # column views, kept in sync
            setattr(self, TRAIT_ATTR[t], self.LT[:, k])
        self.pX = np.array([[p.get(t, 0.5) for t in XTRAITS] for p in P])
        self.pvar = np.array([p.get("variance", 1.0) for p in P])
        self.plife = np.array([p.get("lifespan", 1.0) for p in P])
        self.LX = np.full((MAXL, len(XTRAITS)), 0.5)
        self.hier, self.pati = self.LX[:, 0], self.LX[:, 1]
        self.conf, self.pros = self.LX[:, 2], self.LX[:, 3]
        self.dom = self.LX[:, 4]
        self.crafts = self.LX[:, 5]
        self.xrng = np.random.default_rng(80_000 + seed)
        self.prng = np.random.default_rng(85_000 + seed)
        self.Lpart = np.full(MAXL, PART0)   # partibility (rulers)
        self.p_output = {}                  # pid -> precious output
        self.Lcolony = -np.ones(MAXL, int)  # state that sent a colony
        self.colony_lin = {}                # (state, landmass) -> lineage
        self.posts = {}                     # (lo, hi) -> (owner, city, yr)
        self.waste = np.ones(world.N)       # devastation: capacity share
        self.rule_key = -np.ones(world.N, int)  # acc_cross: ruler, subject
        self.rule_since = np.zeros(world.N)     # acc_cross: since (year)
        self.ruler_log = []
        self.n_ruler = 0

        N = W.N
        self.pcity = CITY_POP * np.array([p.get("city", 1.0) for p in P]) / \
            self.peat
        self.Kcap = np.full(N, np.inf)    # city size caps (food-equivalent)
        self.blk = (W.row // BLOCK) * (NX // BLOCK + 1) + W.col // BLOCK
        self.pop = np.zeros(N)
        self.cul = -np.ones(N, int)       # people per cell
        self.lin = -np.ones(N, int)       # lineage per cell
        self.drought = np.ones(N)
        self.Kcell = np.ones(N)
        # structural state
        self.land = np.ones(N)            # land condition (farm multiplier)
        self.herding = np.zeros(N, bool)  # cell lives by herding
        self.moist = np.zeros(N)          # climate moisture anomaly (sd)
        self.cm = np.ones((4, N))         # climate multipliers: rain-fed
                                          # farming, irrigation, forage, herd
        self.eco_tgt = -np.ones(N, int)   # biome a cell is shifting toward
        self.eco_f = np.zeros(N)
        self.events_abrupt = []
        self.n_avulsions = 0
        self.famine_movers = 0.0
        self._great_dry = -9999
        self.mcul = -np.ones(N, int)      # minority people per cell
        self.mlin = -np.ones(N, int)
        self.mpop = np.zeros(N)
        self.imm = np.zeros(N)            # plague immunity
        self.road = np.zeros(N)           # road stock 0-1
        self.imp = np.zeros(N)            # improvements 0-1
        self.salt = np.zeros(N)           # salt on irrigated land 0-1
        self.hard = np.zeros(N)           # hardship this tick (0/1)
        self.raided = np.zeros(N)         # raided or raiding this tick
        self.revolted = np.zeros(N)       # state lost cities to revolt
        self.pevent = {}                  # pid -> spike years this tick
        self.Lgen_next = np.zeros(MAXL)   # year of next generation turnover
        self.Lraidm = np.zeros(MAXL)      # raid memory per lineage
        self.Lwarm = np.zeros(MAXL)       # war memory per lineage
        self.Lhardm = np.zeros(MAXL)      # hardship memory per lineage
        self.Ltradem = np.zeros(MAXL)     # trade volume, smoothed
        self.Lchurn = np.zeros(MAXL)      # cultural churn per century
        # trait change from experience since the last Price snapshot
        self.Lexp = np.zeros((MAXL, len(TRAITS) + len(XTRAITS)))
        self.vassal = {}                  # vassal pid -> overlord pid
        self.price_rows = []
        self.price_snap = None
        self.n_revolts = 0
        self.cnt = {}                     # event counts this tick
        self._pretender = False
        # climate has its own random stream: the same seed gives the same
        # climate history whatever else is switched on
        self.crng = np.random.default_rng(50_000 + seed)
        if "climate" in self.on:
            self.climate_setup()
        # dragons have their own random stream too
        self.drng = np.random.default_rng(70_000 + seed)
        self.d_by_pid = {}
        self.dragon_kills = np.zeros(nP)
        if "dragons" in self.on:
            self.dragon_setup()
        self.sites_setup()
        self.tick = 0
        self.year = 0
        self.events = []
        self.firsts = set()
        self.p_seen = np.zeros(nP, bool)
        self.p_extinct = np.zeros(nP, bool)
        self.contact_seen = np.zeros((nP, nP), bool)
        self.trade_seen = np.zeros((nP, nP), bool)

        self.cities = {}            # cell -> record (active)
        self.city_hist = []         # all records
        self.city_years = np.zeros(N)
        self.city_peak = np.zeros(N)
        self.polities = {}          # pid -> record
        self.next_pid = 1
        self.wars = {}              # (lo, hi) -> record
        self.truce = {}             # (lo, hi) -> tick until
        self.ties = {}              # (lo, hi) -> trade strength 0..1
        self.allies = {}            # (lo, hi) -> year formed
        self.ally_kind = {}         # (lo, hi) -> "affinity" | "balance"
        self.adj = set()
        self.cell_pol = -np.ones(N, int)
        self.cell_city = -np.ones(N, int)
        self.city_size = {}
        self.city_ts = []           # (year, id, cell, status, size, ...)
        self.ruins = {}             # cell -> record of the city that ended
        self.ts = []
        self.frames = []
        self.rel = []               # relations.csv rows (on frame ticks)
        self.war_log = []           # wars.csv (records only)
        self.siege_log = []         # sieges.csv
        self.revolt_log = []        # revolts.csv
        self._sim = {}
        self.start_sites()

    # ---- helpers
    def log(self, kind, text):
        self.events.append((self.year, kind, text))

    def pname(self, pid):
        p = self.polities.get(pid)
        return f"P{pid}({self.keys[p['culture']]})" if p else f"P{pid}"

    def lname(self, L):
        return f"L{L}({self.keys[self.Lpeople[L]]})"

    def place(self, i):
        return f"{self.W.lon[i]:+.1f},{self.W.lat[i]:+.1f}"

    def shock(self, cells, kind):
        """Note a blow to the cities among `cells`, for attributing their
        end later. Bookkeeping only."""
        for c in np.atleast_1d(cells):
            rec = self.cities.get(int(c))
            if rec is not None:
                sh = rec["shocks"]
                if not sh or sh[-1] != (self.year, kind):
                    sh.append((self.year, kind))
                    if len(sh) > 40:
                        del sh[:10]

    def end_cause(self, rec):
        """Why a city ended: the latest blow within SHOCK_WINDOW years,
        else the state of its land at the end."""
        recent = [k for y, k in rec["shocks"]
                  if self.year - y <= SHOCK_WINDOW]
        if recent:
            order = ["clearance", "sack", "raid takeover", "river lost",
                     "plague", "drought", "dragon", "raid", "siege"]
            return min(recent, key=lambda k: order.index(k)
                       if k in order else 99)
        c = rec["cell"]
        if self.salt[c] > 0.5:
            return "salted land"
        if self.land[c] < 0.6:
            return "worn land"
        if self.moist[c] < -1.0:
            return "dry climate"
        return "decline"

    def devastate(self, t, holder):
        """A siege at city t may lay waste one cell (`devastation`)."""
        if "devastation" not in self.on or self.rng.random() >= WASTE_P:
            return
        c = [t] + [int(x) for x in self.W.nb[t]
                   if x >= 0 and self.cell_pol[x] == holder]
        x = c[int(self.rng.integers(len(c)))]
        self.waste[x] = 0.0
        self.count("devastation")
        if x in self.cities:
            self.count("devastation_city")
            P = self.polities.get(self.cities[x]["polity"])
            if P is not None and len(P["cities"]) >= 8:
                self.log("war", f"the land around the city at "
                         f"{self.place(x)} in {self.pname(P['id'])} is "
                         f"laid waste")

    def count(self, key, n=1):
        self.cnt[key] = self.cnt.get(key, 0) + n

    def first(self, key, kind, text):
        if key not in self.firsts:
            self.firsts.add(key)
            self.log(kind, text)

    # ---- lineages
    def new_lineage(self, people, parent, how, sd=0.0):
        """A new lineage: a founding group of a people, or a daughter of an
        existing lineage (secession, settlers, colony). Intrinsic traits
        (growth rate, biome affinity) and technology pass on unchanged;
        cultural traits mutate by `sd` on the logit scale."""
        if self.nL >= MAXL:
            return parent if parent >= 0 else 0
        L = self.nL
        self.nL += 1
        rng = self.rng
        sd = sd * self.pvar[people]       # a people's own variability
        if "conformity" in self.on and sd > 0:
            # faithful transmission: conformist parents pass customs on
            # nearly unchanged
            c0 = self.conf[parent] if parent >= 0 else \
                self.pX[people, XTRAITS.index("conformity")]
            sd = sd * (1.5 - c0)
        if parent >= 0:
            self.LX[L] = self.LX[parent]
            self.Lpart[L] = self.Lpart[parent]
        else:
            self.LX[L] = self.pX[people]
            self.Lpart[L] = PART0
        if hasattr(self, "Lpref"):
            self.Lpref[L] = self.Lpref[parent] if parent >= 0 else \
                self.ppref[people]
            if sd > 0 and "goods_value" in self.on:
                self.Lpref[L] = self.Lpref[L] * np.exp(
                    self.prng.normal(0, sd, self.Lpref.shape[1]))
        if sd > 0 and "rulers" in self.on:
            x = min(max(self.Lpart[L], 0.02), 0.98)
            self.Lpart[L] = 1 / (1 + math.exp(-(math.log(x / (1 - x)) +
                                                self.prng.normal(0, 2.5 * sd))))
        if sd > 0:
            x = np.clip(self.LX[L], 0.02, 0.98)
            self.LX[L] = 1 / (1 + np.exp(-(np.log(x / (1 - x)) +
                                           self.xrng.normal(0, 2.5 * sd,
                                                            len(XTRAITS)))))
        if parent >= 0:
            T, r, aff = self.LT[parent], self.Lr[parent], self.Laff[parent]
            for a in ("agri", "metal", "sail", "fishing", "admin", "bronze", "iron",
                      "steel", "known", "lack", "craft", "domlv", "guard",
                      "Lwarm", "Lhardm", "Ltradem", "Lexp", "Lchurn",
                      "Lraidm"):
                getattr(self, a)[L] = getattr(self, a)[parent]
        else:
            T, r, aff = self.pT[people], self.pr[people], self.paff[people]
            self.agri[L] = 0.25
            self.fishing[L] = FISH_START
        if sd > 0:
            x = np.clip(T, 0.02, 0.98)
            T = 1 / (1 + np.exp(-(np.log(x / (1 - x)) +
                                  rng.normal(0, 2.5 * sd, len(T)))))
        self.LT[L], self.Lr[L], self.Laff[L] = T, r, aff
        self.Lbest[L] = aff.max()
        if parent < 0:
            self.sail[L] = SAIL_START if "dispersal" in self.on else \
                0.05 * self.seaf[L]
        self.Lpeople[L] = people
        self.Lparent[L] = parent
        self.Lfounded[L] = self.year
        self.Lhow.append(how)
        base = self.colors[people].astype(float)
        self.Lcol[L] = np.clip(base * rng.uniform(0.6, 1.2) +
                               rng.uniform(-30, 30, 3), 15, 245)
        self.Lseen[L] = set(self.Lseen.get(parent, set()))
        return L

    def similarity(self, a, b):
        """1 for identical lineages; within a people it falls with trait
        distance; between peoples it is capped low (SIM_OTHER)."""
        if a == b:
            return 1.0
        key = (a, b) if a < b else (b, a)
        s = self._sim.get(key)
        if s is None:
            dv = self.LT[a] - self.LT[b]
            if "dispersal" in self.on:
                dv = dv * self.simmask
            d = float(np.linalg.norm(dv) + 0.3 *
                      np.linalg.norm(np.log(self.Laff[a]) -
                                     np.log(self.Laff[b])))
            if self.Lpeople[a] == self.Lpeople[b]:
                s = math.exp(-d / SIM_SAME_SCALE)
            else:
                s = SIM_OTHER[0] + SIM_OTHER[1] * math.exp(-d / 0.8)
            self._sim[key] = s
        return s

    def sim_matrix(self, A):
        """Similarity between all pairs of lineages A (as similarity())."""
        X = self.LT[A] * (self.simmask if "dispersal" in self.on else 1)
        sq = (X ** 2).sum(1)
        d = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * X @ X.T, 0))
        F = np.log(self.Laff[A])
        sf = (F ** 2).sum(1)
        d = d + 0.3 * np.sqrt(np.maximum(sf[:, None] + sf[None, :] -
                                         2 * F @ F.T, 0))
        same = self.Lpeople[A][:, None] == self.Lpeople[A][None, :]
        e = np.exp(-d / SIM_SAME_SCALE)
        return np.where(same, e, SIM_OTHER[0] + SIM_OTHER[1] *
                        np.exp(-d / 0.8))

    def accept(self, a, b, level):
        """Both sides must tolerate `level` x their dissimilarity."""
        need, width = level
        need = need * (1 - self.similarity(a, b))
        return sigmoid((self.tol[a] - need) / width) * \
            sigmoid((self.tol[b] - need) / width)

    # ---- capacity
    def prepare_capacity(self):
        self.Kcell = self.drought.copy()
        if "climate" in self.on:
            self.climate()
        self.Kcap[:] = np.inf
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            boost = np.array([1.5 + 2.0 * min(1.5, self.polities[
                self.cities[c]["polity"]]["trade"])
                if self.cities[c]["polity"] in self.polities else 1.5
                for c in cc])
            if "development" in self.on:
                rl = np.array([self.polities[self.cities[c]["polity"]]["lin"]
                               if self.cities[c]["polity"] in self.polities
                               else max(self.lin[c], 0) for c in cc])
                boost = boost * (1 + DEV_CITY * self.dev(rl))
            self.Kcell[cc] *= boost
            adm = np.array([self.admin[self.polities[
                self.cities[c]["polity"]]["lin"]]
                if self.cities[c]["polity"] in self.polities
                else self.admin[max(self.lin[c], 0)] for c in cc])
            if CITY_CAP:
                self.Kcap[cc] = CITY_POP * (CITY_CAP0 + CITY_CAP1 * adm ** 2)
        if "devastation" in self.on:
            self.waste = np.minimum(1.0, self.waste + DT / WASTE_YEARS)
            self.Kcell *= self.waste

    def dev(self, L):
        """Development (0-1) of lineages L: their technologies' mean."""
        parts = [np.clip((self.agri[L] - 0.25) / 0.75, 0, 1),
                 np.clip(self.metal[L] / 3.5, 0, 1), self.sail[L],
                 np.clip((self.fishing[L] - FISH_START) / (1 - FISH_START),
                         0, 1), self.admin[L]]
        if "craft" in self.on:
            parts.append(self.craft[L])
        if "domestication" in self.on and len(self.h_cell):
            parts.append(self.domlv[L].max(-1))
        return sum(parts) / len(parts)

    def adapt(self, L):
        """0..1: how far farming and metallurgy free a lineage from its
        preferred biomes."""
        return 0.5 * np.clip((self.agri[L] - 0.25) / 0.75, 0, 1) + \
            0.5 * np.clip(self.metal[L] / 2.6, 0, 1)

    def biome_fit(self, L, b):
        """Effective biome affinity of lineages L in biomes b."""
        best = self.Lbest[L]
        k = BIOME_K * (1 - BIOME_ADAPT * self.adapt(L))
        return best * (self.Laff[L, b] / best) ** k

    def Kf(self, L, j):
        """Carrying capacity of cells j for lineages L (broadcast): the
        better of farming (blended with foraging) and, if on, herding."""
        Kc, Kh = self.K2(L, j)
        return Kc if Kh is None else np.maximum(Kc, Kh)

    def K2(self, L, j):
        """(farming K, herding K or None) of cells j for lineages L."""
        W = self.W
        a = self.agri[L]
        tools = 1 + TOOLS[0] * self.iron[L] + TOOLS[1] * self.steel[L]
        if "climate" in self.on:
            cm = self.cm
            rain = W.rain_ws[j] if "pastoral" in self.on else W.rain_w[j]
            farm = rain * cm[0, j] + W.irr_w[j] * cm[1, j] + W.fish[j]
            rainc = rain * cm[0, j]
            forage = W.forage[j] * cm[2, j]
            herd = W.herd[j] * cm[3, j]
        elif "improvements" in self.on:
            rain = W.rain_ws[j] if "pastoral" in self.on else W.rain_w[j]
            farm = rain + W.irr_w[j] + W.fish[j]
            rainc = rain
            forage, herd = W.forage[j], W.herd[j]
        else:
            farm = W.farm_steppe[j] if "pastoral" in self.on else W.farm[j]
            rainc = W.rain_ws[j] if "pastoral" in self.on else W.rain_w[j]
            forage, herd = W.forage[j], W.herd[j]
        if "improvements" in self.on:
            # canals carry irrigation; clearance and terraces help rain-fed
            if "climate" not in self.on:
                cm0 = cm1 = 1.0
            else:
                cm0, cm1 = cm[0, j], cm[1, j]
            imp = self.imp[j]
            farm = rain * cm0 * (1 + IMP_RAIN * imp) + \
                W.irr_w[j] * cm1 * (IMP_IRR0 + (1 - IMP_IRR0) * imp) + \
                W.fish[j]
            rainc = rain * cm0 * (1 + IMP_RAIN * imp)
        if "sod" in self.on:
            # grassland sod resists the plough until bronze, then iron
            sf = np.where(self.iron[L], 1.0,
                          np.where(self.bronze[L], SOD_BR, SOD0))
            grass = W.biome[j] == BIOMES.index("Grassland")
            farm = farm - grass * (1 - sf) * rainc
        if "land" in self.on:
            farm = farm * self.land[j]
        if "salinity" in self.on:
            farm = farm * (1 - SALT_MAX * self.salt[j] * W.irr_share[j])
        if "domestication" in self.on:
            # what there is to farm and herd: the packages a lineage holds
            b = W.biome[j]
            lv = self.domlv[L]
            cr = (lv * np.moveaxis(self.h_wc[:, b], 0, -1)).max(-1)
            an = (lv * np.moveaxis(self.h_wa[:, b], 0, -1)).max(-1)
            farm = farm * (DOM_FLOOR + (1 - DOM_FLOOR) * cr)
            herd = herd * (DOM_HFLOOR + (1 - DOM_HFLOOR) * an)
        dens = forage * (1 - a) + farm * a * tools
        eat = self.peat[self.Lpeople[L]]
        fit = self.biome_fit(L, W.biome[j])
        if "climate" in self.on:
            # near a biome edge, a dry or wet spell moves the edge
            f = self.eco_f[j]
            fit = fit + f * (self.biome_fit(L, np.maximum(self.eco_tgt[j], 0))
                             - fit)
        if "fishing" in self.on:
            coast = 1 + (FISH0 + FISH1 * self.fishing[L]) * W.water[j]
        else:
            coast = 1 + 0.5 * self.seaf[L] * W.coastal[j]
        if self.pwet.any():
            fit = fit * (1 + WET_K * self.pwet[self.Lpeople[L]] * W.wet[j])
        cap = self.Kcap[j] / eat
        if "development" in self.on:
            coast = coast * (1 + DEV_K * self.dev(L))
        if "density_cap" in self.on:
            dm = np.where(self.cell_city[j] == j, DENS_MAX_CITY, DENS_MAX)
            cap = np.minimum(cap, dm * W.area[j] / eat)
        Kc = np.minimum(W.area[j] * dens * fit * self.Kcell[j] * coast / eat,
                        cap)
        if "pastoral" not in self.on:
            return Kc, None
        h = np.clip((a - HERD_AGRI[0]) / (HERD_AGRI[1] - HERD_AGRI[0]), 0, 1)
        # herders forage too; animals make the difference
        hd = forage * (1 - h) + herd * h
        Kh = np.minimum(W.area[j] * hd * fit * self.Kcell[j] * coast / eat,
                        cap)
        return Kc, Kh

    def climate_setup(self):
        """Fixed patterns, their time series for the whole run, and the
        abrupt events, all from the climate's own random stream."""
        W, rng = self.W, self.crng
        nt = self.years // DT + 2

        def series():
            out = np.zeros(nt)
            for kind, P, tau, share in CLIM_PARTS:
                burn = int(3 * max(tau, P, 50) / DT) + 10
                e = rng.normal(size=nt + burn)
                if kind == "white":
                    x = e
                elif kind == "red":
                    x = signal.lfilter([1], [1, -math.exp(-DT / tau)], e)
                else:
                    r = math.exp(-DT / tau)
                    x = signal.lfilter([1], [1, -2 * r * math.cos(
                        2 * math.pi * DT / P), r * r], e)
                x = x[burn:]
                out += math.sqrt(share) * x / x.std()
            return out / out.std()

        def std(v):
            return (v - v.mean()) / max(v.std(), 1e-9)

        def field(sigma):
            g = ndimage.gaussian_filter(rng.normal(size=(NY, NX)), sigma,
                                        mode="wrap")
            return std(g[W.row, W.col])

        pats = [np.ones(W.N), std(np.cos(4 * np.radians(W.lat))),
                std(W.dcoast)] + [field(CLIM_REG_SIGMA)
                                  for _ in range(CLIM_REGIONAL)]
        w = np.array([CLIM_W["world"], CLIM_W["latitude"], CLIM_W["inland"]]
                     + [CLIM_W["regional"]] * CLIM_REGIONAL)
        norm = math.sqrt((w ** 2).sum() + CLIM_W["local"] ** 2)
        self.clim_pat = np.array(pats) * (w / norm)[:, None]
        self.clim_loc = CLIM_W["local"] / norm
        self.clim_ser = np.array([series() for _ in pats])
        # abrupt dry events: a smooth regional footprint (or, one time in
        # four, the whole world), setting in fast and lifting slowly
        t = rng.exponential(1 / ABRUPT_RATE)
        while t < self.years:
            if rng.random() < 0.25:
                fp, where = np.ones(W.N), "the whole world"
            else:
                g = np.clip(field(25), 0, None)
                fp = g / max(g.max(), 1e-9)
                k = int(np.argmax(fp))
                where = f"lands around {W.lon[k]:+.0f},{W.lat[k]:+.0f}"
            self.events_abrupt.append(dict(
                start=t, years=rng.uniform(*ABRUPT_YEARS),
                amp=rng.uniform(*ABRUPT_AMP), fp=fp, where=where,
                logged=False, ended=False))
            t += rng.exponential(1 / ABRUPT_RATE)

    def climate(self):
        """This tick's moisture anomaly and what it does: rain-fed yields,
        foraging and herding, river discharge (from the whole catchment),
        biome edges, granaries, and rivers changing course."""
        W, rng = self.W, self.crng
        tick = min(self.tick, self.clim_ser.shape[1] - 1)
        m = self.clim_pat.T @ self.clim_ser[:, tick]
        g = ndimage.gaussian_filter(rng.normal(size=(NY, NX)),
                                    CLIM_LOCAL_SIGMA, mode="wrap")
        g = g[W.row, W.col]
        m += self.clim_loc * g / max(g.std(), 1e-9)
        for ev in self.events_abrupt:
            dt = self.year - ev["start"]
            if dt < 0 or ev["ended"]:
                continue
            if dt > ev["years"] + ABRUPT_RAMP[1]:
                ev["ended"] = True
                self.log("climate", f"the long dry spell over {ev['where']}"
                         " lifts")
                continue
            env = min(1, dt / ABRUPT_RAMP[0]) if dt <= ev["years"] else \
                1 - (dt - ev["years"]) / ABRUPT_RAMP[1]
            m -= ev["amp"] * env * ev["fp"]
            if not ev["logged"]:
                ev["logged"] = True
                self.log("climate", f"a long dry spell sets in over "
                         f"{ev['where']} (~{ev['years']:.0f} yrs)")
        self.moist = m
        pa = np.clip((PREC_SD[0] + PREC_SD[1] * W.dryness) * m, -0.7, 0.7)
        el = 1 + W.dryness
        rain = np.clip(1 + el * pa, 0.1, 1.6)
        forage = np.clip(1 + 0.8 * el * pa, 0.2, 1.5)
        Qt = W.accumulate(W.yield_ * np.clip(1 + RUNOFF_EL * pa, 0.05, None))
        ratio = Qt / np.maximum(W.Q, 1e-9)
        irr = np.sqrt(np.clip(ratio, 0.2, 2.0))
        # biome edges move: blend toward the drier or wetter neighbour biome
        dry = m < 0
        tgt = np.where(dry, W.eco_dry, W.eco_wet)
        f = np.clip(ECO_W * (np.abs(m) - 0.5), 0, ECO_MAX) * \
            np.where(dry, W.eco_dry_prox, W.eco_wet_prox) * (tgt >= 0)
        self.eco_tgt, self.eco_f = tgt, f
        b, t2 = W.biome, np.maximum(tgt, 0)
        mix = []
        for table in (FARM, FORAGE, HERD):
            v = np.array([table[x] for x in BIOMES])
            mix.append(1 - f + f * v[t2] / v[b])
        raw = np.array([rain * mix[0], irr, forage * mix[1], forage * mix[2]])
        # granaries: states smooth short swings, more so with good offices
        pl = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                pl[pid] = p["lin"]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        tau = np.where(rl >= 0, STORE_YEARS * self.admin[np.maximum(rl, 0)],
                       0)
        if "patience" in self.on:
            tau = tau * (0.5 + self.pati[np.maximum(rl, 0)])
        alpha = DT / (DT + tau)
        self.cm += alpha * (raw - self.cm)
        # a great drought, for the log
        # (about 2% of people are that dry in an ordinary year)
        dry_pop = self.pop[m < -2].sum()
        if dry_pop > 0.08 * max(self.pop.sum(), 1) and dry_pop > 1e6 and \
                self.year - self._great_dry >= 50:
            self._great_dry = self.year
            k = int(np.argmin(np.where(self.pop > 0, m, 9)))
            self.log("drought", f"great drought, worst near {self.place(k)}"
                     f" ({dry_pop / 1e6:.1f}M people under severe drought)")
        # rivers change course, mostly in high water
        prone = np.nonzero(W.river & W.alluvial & (W.relief < 0.3) &
                           (W.elev < 0.3) & (W.Q > 1000))[0]
        if len(prone):
            pr = DT * AVULSE_RATE * np.clip(ratio[prone], 0.3, 3) ** 2
            for i in prone[rng.random(len(prone)) < pr][:3]:
                if W.river[i]:
                    self.avulse(int(i))

    def avulse(self, i):
        """The river at cell i breaks its banks and takes a new course to a
        lower (or nearly as low) neighbour, or straight to the sea."""
        W, rng = self.W, self.crng
        old = int(W.flow[i])
        cand, el = [], []
        for k in range(8):
            j = int(W.nb[i, k])
            if j < 0 or j == old or W.flow[j] == i or W.lake[j] or \
                    W.elev[j] > W.elev[i] + AVULSE_TOL:
                continue
            x, ok = j, True
            for _ in range(5000):           # no loops back through i
                if x == i:
                    ok = False
                    break
                x = int(W.flow[x])
                if x < 0:
                    break
            if ok:
                cand.append(j)
                el.append(W.elev[j])
        if W.coastal[i] and old >= 0:
            cand.append(-1)
            el.append(0.0)
        if not cand:
            return
        el = np.array(el)
        wt = np.exp(-(el - el.min()) / 0.01)
        j = int(cand[rng.choice(len(cand), p=wt / wt.sum())])
        before = W.river.copy()
        W.reroute(i, j)
        self.n_avulsions += 1
        lost = np.nonzero(before & ~W.river)[0]
        hit = [c for c in lost if c in self.cities]
        self.shock(hit, "river lost")
        if hit or len(lost) >= 5:
            names = ", ".join(self.place(c) for c in hit[:4])
            self.log("river", f"the river at {self.place(i)} changes course"
                     f" ({len(lost)} cells lose it"
                     + (f"; cities left dry: {names}" if hit else "") + ")")

    # ---- economy
    def sites_setup(self):
        """Unique resources and domestication hearths (sites.json, or
        drawn from the run seed with --shuffle-sites)."""
        W = self.W
        if self.shuffle_sites:
            from make_sites import place_sites, place_sites_v2
            S = place_sites(W, 90_000 + self.seed)
            if self.sites_file != "sites.json":
                S = place_sites_v2(W, 90_000 + self.seed, S["hearths"])
        else:
            with open(os.path.join(HERE, self.sites_file)) as fh:
                S = json.load(fh)
        self.sites = S
        R, H = S["resources"], S["hearths"]
        self.res_cell = np.array([W.idx2[x["row"], x["col"]] for x in R],
                                 int)
        self.res_kinds = sorted({x["kind"] for x in R})
        self.res_kind = np.array([self.res_kinds.index(x["kind"])
                                  for x in R], int)
        nk = len(self.res_kinds)
        self.res_prec = np.array([bool(x.get("precious")) for x in R], bool)
        self.res_lode = np.array([x["kind"] in ("lode gold", "silver")
                                  for x in R], bool)
        self.res_reserve = np.ones(len(R))
        self.kind_prec = np.array([any(self.res_prec[self.res_kind == k])
                                   for k in range(nk)], bool)
        grng = np.random.default_rng(87_000 + self.seed)
        self.ppref = np.exp(grng.normal(0, PREF_SD, (self.nP, nk)))
        for c, key in enumerate(self.keys):
            b = PREF_BIAS.get(key, {})
            for k, kind in enumerate(self.res_kinds):
                grp = {g for g, kinds in PREF_GROUPS.items() if kind in kinds}
                if grp & b.get("fav", set()):
                    self.ppref[c, k] *= PREF_FAV
                elif grp & b.get("dis", set()):
                    self.ppref[c, k] *= PREF_DIS
        self.Lpref = np.ones((MAXL, nk))
        for L in range(self.nL):
            self.Lpref[L] = self.ppref[self.Lpeople[L]]
        self.h_cell = np.array([W.idx2[x["row"], x["col"]] for x in H], int)
        self.h_crop = np.array([x["kind"] == "crop" for x in H], bool)
        self.h_biome = np.array([BIOMES.index(x["biome"]) for x in H], int)
        self.h_name = [f"{x['biome'].lower()} {x['kind']}s" for x in H]
        nh, nb = len(H), len(BIOMES)
        # weight of each package in each biome: 1 at home, DOM_OFF elsewhere
        own = self.h_biome[:, None] == np.arange(nb)[None, :]
        w = np.where(own, 1.0, DOM_OFF)
        self.h_wc = np.where(self.h_crop[:, None], w, 0.0)
        self.h_wa = np.where(~self.h_crop[:, None], w, 0.0)
        self.h_near = [np.nonzero(gc_km(W.xyz, c, np.arange(W.N)) <
                                  HEARTH_KM)[0] for c in self.h_cell]
        self.domlv = np.zeros((MAXL, nh))
        self.guard = np.zeros((MAXL, GUARD_MAX), bool)
        self.n_guard = 0
        self.passets = {}

    def state_assets(self):
        """Kinds of resource, ores, craft and guarded techniques of each
        living state."""
        kinds = {}
        if "resources" in self.on and len(self.res_cell):
            rc = self.res_cell
            pol = self.cell_pol[rc]
            ok = (pol >= 0) & (self.lin[rc] >= 0)
            for pid, k in zip(pol[ok], self.res_kind[ok]):
                kinds.setdefault(int(pid), set()).add(int(k))
            if "precious" in self.on and self.res_prec.any():
                outp = {}
                for i in np.nonzero(ok & self.res_prec)[0]:
                    pid = int(pol[i])
                    Lr = self.polities[pid]["lin"] \
                        if pid in self.polities else -1
                    if self.res_lode[i] and (Lr < 0 or not self.bronze[Lr]):
                        continue
                    o = outp.setdefault(pid, np.zeros(len(self.res_kinds)))
                    o[self.res_kind[i]] += self.res_reserve[i]
                    rate = MINE_RATE * (1 if self.res_lode[i] else 2)
                    self.res_reserve[i] = max(0.0, self.res_reserve[i] -
                                              DT * rate)
                self.p_output = outp
        terr = {}
        W = self.W
        for i, d in enumerate((W.d_cu, W.d_sn, W.d_fe)):
            near = (self.lin >= 0) & (self.cell_pol >= 0) & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            for pid in np.unique(self.cell_pol[near]):
                terr.setdefault(int(pid), set()).add(i)
        out = {}
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            L = p["lin"]
            out[pid] = dict(
                ores_terr=terr.get(pid, set()),
                kinds=kinds.get(pid, set()),
                ores={i for i in range(3) if self.ore_has[L, i]},
                craft=float(self.craft[L]) if "craft" in self.on else 0.0,
                tech=set(np.nonzero(self.guard[L])[0].tolist())
                if "guarded" in self.on else set())
            p["n_kinds"] = len(out[pid]["kinds"])
        self.passets = out

    def war_prize(self, b, a):
        """What conquering state b would give state a."""
        x, y = self.passets.get(b), self.passets.get(a)
        if x is None or y is None:
            return 0.0
        if "goods_value" in self.on:
            return self.goods_worth(b, a, prize=True) + \
                ORE_VALUE * len(x["ores_terr"] - y["ores"]) + \
                max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])
        return len(x["kinds"] - y["kinds"]) + \
            ORE_VALUE * len(x["ores_terr"] - y["ores"]) + \
            max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])

    def deter(self, A, B, allies):
        """Strength A projects to B's city nearest A's capital over B's
        defence there (with allies, terrain and walls); and that city."""
        cc = list(B["cities"])
        t = cc[int(np.argmin(gc_km(self.W.xyz, A["capital"], np.array(cc))))]
        PA = self.projected(A, t)
        PB = self.projected(B, t)
        for q in allies.get(B["id"], ()):
            Q = self.polities.get(q)
            if q != A["id"] and Q and Q["ended"] is None:
                PB += 0.35 * self.projected(Q, t)
        PB *= 1.4 * self.W.defence[t] * (1.25 if t == B["capital"] else 1)
        if "development" in self.on:
            PB *= 1 + DEV_WALL * self.dev(B["lin"])
        return PA / max(PB, 1e-9), t

    def kind_value(self, pid):
        """Value of each kind of resource to the ruling lineage of pid."""
        L = self.polities[pid]["lin"]
        return (0.5 + self.crafts[L]) * self.Lpref[L]

    def goods_worth(self, a, b, prize=False):
        """Worth to state b of what state a holds and b lacks (valued by
        b's culture), plus precious-metal output (`precious`)."""
        x, y = self.passets[a], self.passets[b]
        v = self.kind_value(b)
        out = sum(v[k] for k in x["kinds"] - y["kinds"]
                  if not (self.kind_prec[k] and "precious" in self.on))
        if "precious" in self.on:
            oa = self.p_output.get(a)
            if oa is not None:
                ob = self.p_output.get(b, np.zeros(len(oa)))
                out += float((v * (oa if prize else oa / (1 + ob))).sum())
        return out

    def offer(self, a, b):
        """What state a has that state b lacks."""
        x, y = self.passets.get(a), self.passets.get(b)
        if x is None or y is None:
            return 0.0
        if "goods_value" in self.on:
            return self.goods_worth(a, b) + \
                ORE_VALUE * len(x["ores"] - y["ores"]) + \
                max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])
        return len(x["kinds"] - y["kinds"]) + \
            ORE_VALUE * len(x["ores"] - y["ores"]) + \
            max(0.0, x["craft"] - y["craft"]) + len(x["tech"] - y["tech"])

    # ---- setup
    def start_sites(self):
        """Place founding groups. A people's `head` (years) is its head
        start: groups of the people with the largest head start found at
        year 0, the rest arrive `max_head - head` years later, each on an
        empty site."""
        W = self.W
        dens = W.forage[None] * 0.5 + W.farm[None] * 0.5
        # founders settle only in their people's best biome(s)
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        fit = np.where(self.paff >= 0.9 * best, fit, 0)
        self.site_score = W.area[None] * dens * fit[:, W.biome]
        groups = [(c, k) for c in range(self.nP)
                  for k in range(self.P[c].get("starts", self.starts))]
        groups = [groups[i] for i in self.rng.permutation(len(groups))]
        self.chosen, self.first_site = [], {}
        self.sep0 = float(np.clip(3500 / math.sqrt(len(groups)), 500, 1800))
        H = max(p.get("head", 0) for p in self.P)
        self.arrivals = sorted(
            ((H - self.P[c].get("head", 0), c, k) for c, k in groups),
            key=lambda x: x[0])
        if self.start_mode == "wander":
            self.wander_setup(groups)
        self.place_arrivals()

    # ---- wandering founders
    def wander_setup(self, groups):
        """Before the run, each founding group is dropped at a random
        habitable cell and wanders: every step it stays with probability
        min(0.95, suitability / the people's 95th-percentile suitability),
        otherwise it moves to a neighbouring cell chosen in proportion to
        the square of the surrounding land's suitability (biome preference
        x productivity, smoothed over ~3 cells), so groups can sense better
        land beyond their immediate neighbours."""
        W = self.W
        best = self.paff.max(1, keepdims=True)
        fit = best * (self.paff / best) ** BIOME_K
        dens = 0.75 * W.forage + 0.25 * W.farm
        if "fishing" in self.on:
            wb = (1 + (FISH0 + FISH1 * FISH_START) * W.water)[None]
        else:
            wb = 1 + 0.5 * self.pT[:, TI["seafaring"]][:, None] * \
                W.coastal[None]
        suit = W.area[None] * dens[None] * fit[:, W.biome] * wb
        if self.homelands == "continents":
            big = 15e6 if self.nP <= 5 else 4e6
            small = W.landmass_area[W.landmass] < big
            for c, p in enumerate(self.P):
                if not p.get("anywhere"):
                    suit[c, small] = 0
        # regional starts (roster key `region`): founders start and wander
        # only within their people's homeland
        for c, p in enumerate(self.P):
            if p.get("region"):
                suit[c, ~self.region_mask(p["region"])] = 0
        ref = np.array([np.percentile(s[s > 0], 95) for s in suit])
        self.suit = suit
        look = np.zeros_like(suit)
        g = np.zeros((NY, NX))
        for c in range(self.nP):
            g[:] = 0
            g[W.row, W.col] = suit[c] / ref[c]
            look[c] = ndimage.gaussian_filter(g, 3, mode="wrap")[W.row, W.col]
        self.look = (look + 1e-6) ** 2
        self.pstay = np.minimum(0.95, suit / ref[:, None])
        self.wpos, self.wfrom = {}, {}
        for c, k in groups:
            ok = np.nonzero(suit[c] > 0)[0]
            self.wpos[(c, k)] = self.wfrom[(c, k)] = int(self.rng.choice(ok))
        self.wander(groups, self.wander_steps, avoid=False)

    def region_mask(self, region):
        """Cells of a homeland: a list of parts, each the landmass at a
        point (lon, lat), optionally only within radius_km of it."""
        W = self.W
        m = np.zeros(W.N, bool)
        for part in region:
            lon, lat = part["at"]
            i = int(np.argmin(np.linalg.norm(
                W.xyz - unit_xyz(np.array(lon), np.array(lat)), axis=1)))
            mm = W.landmass == W.landmass[i]
            if part.get("radius_km"):
                mm &= gc_km(W.xyz, i, np.arange(W.N)) <= part["radius_km"]
            m |= mm
        return m

    def wander(self, groups, steps, avoid):
        if not groups:
            return
        W = self.W
        cs = np.array([c for c, _ in groups])
        pos = np.array([self.wpos[g] for g in groups])
        for _ in range(steps):
            q = self.pstay[cs, pos]
            if avoid:
                q = np.where(self.lin[pos] >= 0, 0, q)
            move = self.rng.random(len(pos)) >= q
            if not move.any():
                continue
            nb = W.nb[pos[move]]
            w = np.where(nb >= 0, self.look[cs[move][:, None],
                                            np.maximum(nb, 0)], 0)
            if avoid:
                w = np.where((nb >= 0) & (self.lin[np.maximum(nb, 0)] < 0),
                             w, 0)
            w = np.where(w.sum(1, keepdims=True) > 0, w,
                         (nb >= 0).astype(float))
            tot = w.sum(1)
            pick = (w.cumsum(1) < (self.rng.random(len(nb)) * tot)[:, None]
                    ).sum(1)
            pick = np.minimum(pick, 7)
            new = nb[np.arange(len(nb)), pick]
            idx = np.nonzero(move)[0]
            good = (new >= 0) & (tot > 0)
            pos[idx[good]] = new[good]
        for g, p in zip(groups, pos):
            self.wpos[g] = int(p)

    def place_arrivals(self):
        while self.arrivals and self.arrivals[0][0] <= self.year:
            _, c, k = self.arrivals.pop(0)
            self.found_group(c, k)
        if self.start_mode == "wander" and self.arrivals:
            # groups not yet arrived keep wandering, avoiding settled land
            self.wander([(c, k) for _, c, k in self.arrivals], 3, avoid=True)

    def empty_near(self, i, c, rings=8):
        """Best empty cell within `rings` steps of i, or -1."""
        W = self.W
        seen, front = {i}, [i]
        for _ in range(rings):
            nxt = []
            for x in front:
                for j in W.nb[x]:
                    if j >= 0 and j not in seen:
                        seen.add(int(j))
                        nxt.append(int(j))
            front = nxt
            cand = [j for j in front if self.lin[j] < 0 and
                    self.suit[c, j] > 0]
            if cand:
                return max(cand, key=lambda j: self.suit[c, j])
        return -1

    def found_group(self, c, k):
        W = self.W
        p = self.P[c]
        i = -1
        if self.start_mode == "wander" and not (p.get("start") and k == 0):
            i = self.wpos[(c, k)]
            if self.lin[i] >= 0:
                i = self.empty_near(i, c)
        if i >= 0:
            pass
        elif p.get("start") and k == 0:
            lon, lat = p["start"]
            i = int(np.argmin(np.linalg.norm(
                W.xyz - unit_xyz(np.array(lon), np.array(lat)), axis=1)))
        else:
            s0 = self.site_score[c].copy()
            s0[self.lin >= 0] = 0
            if self.homelands == "continents":
                big = 15e6 if self.nP <= 5 else 4e6
                s0[W.landmass_area[W.landmass] < big] = 0
            if p["seafaring"] < 0.5 and "dispersal" not in self.on:
                s0[W.coastal] *= 0.5
            if self.cluster_km > 0 and c in self.first_site:
                s0[gc_km(W.xyz, self.first_site[c], np.arange(W.N)) >
                   self.cluster_km] = 0
            sep_km = self.sep0
            while True:
                s = s0.copy()
                for j in self.chosen:
                    s[gc_km(W.xyz, j, np.arange(W.N)) < sep_km] = 0
                pos = np.nonzero(s > 0)[0]
                if len(pos) or sep_km < 100:
                    break
                sep_km *= 0.7
            if not len(pos):
                pos = np.nonzero(s0 > 0)[0]
                s = s0
            if not len(pos):
                self.log("origin", f"{p['label']} group {k + 1} finds no "
                         "empty land and never arrives")
                return
            n = max(60, int(self.start_pool * len(pos)))
            top = pos[np.argsort(s[pos])[-n:]]
            i = int(self.rng.choice(top, p=s[top] / s[top].sum()))
        self.first_site.setdefault(c, i)
        self.chosen.append(i)
        L = self.new_lineage(c, -1, "start", sd=self.start_vary)
        self.Lseen[L] = {W.landmass[i]}
        self.Pblk[c].add(int(self.blk[i]))
        self.cul[i], self.lin[i], self.pop[i] = c, L, \
            FOUND_FOOD / self.peat[c] if "food_units" in self.on else 400.0
        moved = ""
        if (c, k) in getattr(self, "wfrom", {}):
            d = gc_km(W.xyz, self.wfrom[(c, k)], np.array([i]))[0]
            moved = f", after wandering from {self.place(self.wfrom[(c, k)])}" \
                f" ({d:.0f} km)"
        self.log("origin", f"{p['label']} group {k + 1} {self.lname(L)} "
                 f"founded at {self.place(i)} [{BIOMES[W.biome[i]]}]{moved}")

    # ---- step pieces
    def grow(self):
        occ = np.nonzero(self.lin >= 0)[0]
        L = self.lin[occ]
        k = np.maximum(self.Kf(L, occ), 1e-3)
        if "minority" in self.on:
            # a minority eats from the same land
            mo = occ[self.mlin[occ] >= 0]
            if len(mo):
                Lm = self.mlin[mo]
                km = np.maximum(MIN_CAP * self.Kf(Lm, mo), 1e-3)
                pm = self.mpop[mo]
                rm = self.Lr[Lm]
                if "dragons" in self.on:
                    rm = rm - self.dragon_pen(mo)
                self.mpop[mo] = logistic(pm, km, rm * (0.6 + 0.4 *
                                                       self.agri[Lm]))
                food = np.zeros(self.W.N)
                food[mo] = self.mpop[mo] * self.peat[self.mcul[mo]]
                k = np.maximum(k - food[occ] / self.peat[self.cul[occ]], 1e-3)
        if "separation" in self.on:
            k = k * self.pref(L, occ)
        p = self.pop[occ]
        # frontier fecundity: thinly settled land grows fastest
        front = 1 + 1.5 * np.clip(1 - 2 * p / k, 0, 1)
        r = self.Lr[L] * (0.6 + 0.4 * self.agri[L]) * front
        if "dragons" in self.on:
            # dragons: a cut in the growth rate, the same for everyone;
            # only fast breeders stay above zero under a dragon
            pen = self.dragon_pen(occ)
            rb = self.Lr[L] - pen
            r_d = rb * (0.6 + 0.4 * self.agri[L]) * np.where(rb > 0, front, 1)
            e0 = np.exp(-r * DT)
            p0 = k * p / (p + (k - p) * e0)
            r = r_d
        self.pop[occ] = logistic(p, k, r)
        if "dragons" in self.on:
            lost = np.maximum(p0 - self.pop[occ], 0)
            self.dragon_kills = np.bincount(self.cul[occ], weights=lost,
                                            minlength=self.nP)
            if self.cities:
                hc = occ[lost > 0.05 * np.maximum(p0, 1)]
                self.shock(hc[np.isin(hc, list(self.cities))], "dragon")
        self.land_use(occ, L)

    def colon(self, j, L=None):
        """How readily settlers of lineages L take cells j: terrain, and
        (with `improvements`) land others have already cleared and worked.
        Wetland peoples do not mind wet ground."""
        c = self.W.colonize[j]
        if L is not None and self.pwet.any():
            w = self.pwet[self.Lpeople[L]]
            wt = self.W.wet[j]
            c = c * (1 - COL_WET * wt * (1 - w)) / (1 - COL_WET * wt)
        if "improvements" in self.on:
            return np.minimum(1, c * (1 + IMP_SETTLE * self.imp[j]))
        return c

    def hostile(self, L):
        """What used to be separation's hostile side: separation itself, or
        (1 - tolerance) with `separation` on."""
        return 1 - self.tol[L] if "separation" in self.on else self.sep[L]

    def tolf(self, L, k):
        """The separate tolerance term (1 - k x tolerance) of raids, war,
        clearance and expulsion; 1 with `separation` on, where hostility
        is already 1 - tolerance."""
        return 1.0 if "separation" in self.on else 1 - k * self.tol[L]

    def pref(self, L, j):
        """Share of capacity lineages L choose to fill in cells j
        (`separation`); 1 in cities and with the switch off."""
        if "separation" not in self.on:
            return 1.0
        p = 1 - SEP_DENS * self.sep[L] ** 2
        return np.where(self.cell_city[j] >= 0, 1.0, p)

    def famine(self):
        """When a cell holds more people than its land now feeds, part of
        the surplus leaves: up to FAMINE_RANGE cells away, to empty land
        or kin with room. The rest dies back as the land allows."""
        W, rng = self.W, self.rng
        occ = np.nonzero(self.lin >= 0)[0]
        K = self.Kf(self.lin[occ], occ)
        ex = self.pop[occ] - 1.05 * K
        h = ex > np.maximum(FOUND_MIN, 0.05 * K)
        src, ex = occ[h], ex[h]
        self.famine_movers = 0.0
        if not len(src):
            return
        o = np.argsort(-ex)[:FAMINE_MAX]
        src, ex = src[o], ex[o]
        n, R = len(src), FAMINE_RANGE
        dr = rng.integers(-R, R + 1, (n, 16))
        dc = rng.integers(-R, R + 1, (n, 16))
        r2 = W.row[src][:, None] + dr
        ok = (r2 >= 0) & (r2 < NY)
        t = W.idx2[np.clip(r2, 0, NY - 1), (W.col[src][:, None] + dc) % NX]
        ok &= t >= 0
        t = np.where(ok, t, src[:, None])
        L = self.lin[src][:, None] * np.ones((1, 16), int)
        ok &= W.landmass[t] == W.landmass[src][:, None]
        ok &= (self.lin[t] < 0) | (self.lin[t] == L)
        Kt = self.Kf(L, t)
        room = np.where(ok, Kt - self.pop[t], 0) * \
            np.where(self.lin[t] < 0, self.colon(t, L), 1)
        k = np.argmax(room, 1)
        best = t[np.arange(n), k]
        rb = room[np.arange(n), k]
        go = rb > FOUND_MIN
        src, best, ex, rb = src[go], best[go], ex[go], rb[go]
        _, first = np.unique(best, return_index=True)   # one band per target
        src, best = src[first], best[first]
        mv = np.minimum(FAMINE_MOVE * ex[first], rb[first])
        self.pop[src] -= mv
        new = self.lin[best] < 0
        self.lin[best[new]] = self.lin[src[new]]
        self.cul[best[new]] = self.cul[src[new]]
        self.pop[best] += mv
        self.famine_movers = float(mv.sum())
        self.hard[src] = 1

    # ---- dragons
    D_ARR = ("dhome", "dage", "dally", "did", "dtol", "dviol", "dstr")

    def dragon_setup(self):
        """Neighbour lists for territories and spacing, and the year-0
        dragons: a random packing of homes DRAGON_SPACE_KM apart, of which
        DRAGON_START are held. Each dragon has its own tolerance, violence
        and strength."""
        W, rng = self.W, self.drng
        self.d_tree = cKDTree(W.xyz)

        def csr(km):
            nb = self.d_tree.query_ball_point(
                W.xyz, 2 * math.sin(km / (2 * R_EARTH)))
            ptr = np.zeros(W.N + 1, int)
            ptr[1:] = np.cumsum([len(x) for x in nb])
            return ptr, np.concatenate([np.asarray(x, int) for x in nb])
        self.d_tptr, self.d_tidx = csr(DRAGON_TERR_KM)
        self.d_sptr, self.d_sidx = csr(DRAGON_SPACE_KM)
        blocked = np.zeros(W.N, bool)
        homes = []
        for c in rng.permutation(W.N):
            if not blocked[c]:
                homes.append(c)
                blocked[self.d_sidx[self.d_sptr[c]:self.d_sptr[c + 1]]] = True
        homes = np.array(homes)
        homes = homes[rng.random(len(homes)) < DRAGON_START]
        n = len(homes)
        self.dhome = homes
        self.dage = rng.uniform(0, DRAGON_LIFE, n)
        self.dally = -np.ones(n, int)
        self.did = np.arange(n)
        lg = lambda p: math.log(p / (1 - p))
        self.dtol = dsig(lg(DRAGON_TOL_MEAN) +
                            DRAGON_TRAIT_SD * rng.standard_normal(n))
        self.dviol = dsig(lg(DRAGON_VIOL_MEAN) +
                             DRAGON_TRAIT_SD * rng.standard_normal(n))
        self.dstr = np.exp(DRAGON_STR_SD * rng.standard_normal(n))
        self.dhaz = np.zeros(W.N)
        self.dsmean = np.ones(W.N)
        self.dragon_hist = []
        for i in range(n):
            self.d_hist_add(i, None, homes[i], self.dtol[i], self.dviol[i],
                            self.dstr[i])

    def d_hist_add(self, i, born, home, tol, viol, strength, parent=None):
        self.dragon_hist.append(dict(
            id=i, born=born, parent=parent, home0=int(home),
            tolerance=round(float(tol), 3), violence=round(float(viol), 3),
            strength=round(float(strength), 3), ended=None, fate=None,
            ally=None, ally_people=None, ally_year=None, moves=0))

    def dseff(self, idx=slice(None)):
        """Strength as grown: x min(1, age / DRAGON_GROW), at least 0.05."""
        return self.dstr[idx] * np.clip(self.dage[idx] / DRAGON_GROW,
                                        0.05, 1)

    def d_keep(self, keep):
        for a in self.D_ARR:
            setattr(self, a, getattr(self, a)[keep])

    def terr(self, homes):
        """(cells, owner index) of the territories of homes."""
        a, b = self.d_tptr[homes], self.d_tptr[homes + 1]
        n = b - a
        own = np.repeat(np.arange(len(homes)), n)
        off = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        return self.d_tidx[np.repeat(a, n) + off], own

    def ward(self, j):
        """Heads that ward off a dragon of strength 1 in cells j: fewer for
        big bodies, metal, and the organization of a state."""
        L = np.maximum(self.lin[j], 0)
        mil = 1 + METAL_MIL[0] * self.bronze[L] + \
            METAL_MIL[1] * self.iron[L] + METAL_MIL[2] * self.steel[L]
        org = 1 + WARD_STATE * self.admin[L] * (self.cell_pol[j] >= 0)
        body = self.psize[np.maximum(self.cul[j], 0)] ** WARD_SIZE_EXP
        wd = WARD0 / (body * mil * org)
        if "dragon_hosts" in self.on and self.phost.any():
            host = self.phost[np.maximum(self.cul[j], 0)] & (self.cul[j] >= 0)
            wd = np.where(host, np.inf, wd)
        return wd

    def dragon_pen(self, j):
        """Cut in the yearly growth rate of cells j from the wild dragons
        hunting there: DRAGON_PEN x hazard x g(n)."""
        haz = self.dhaz[j]
        out = np.zeros(len(j))
        k = haz > 0
        if k.any():
            jj = j[k]
            n = self.pop[jj] + self.mpop[jj]
            wd = self.ward(jj) * self.dsmean[jj]
            find = DRAGON_FIND
            if "food_units" in self.on:
                find = DRAGON_FIND / self.peat[np.maximum(self.cul[jj], 0)]
            g = n / (n + find) / (1 + (n / wd) ** 4)
            out[k] = DRAGON_PEN * haz[k] * g
        return out

    def dragon_site(self, c0, warded, taken):
        """A free home for a dragon leaving c0: no other home within
        DRAGON_SPACE_KM, no warded cell in reach. -1 if none found."""
        W, rng = self.W, self.drng
        la1, lo1 = math.radians(W.lat[c0]), math.radians(W.lon[c0])
        for _ in range(12):
            dk = DRAGON_SPACE_KM + DRAGON_DISP_KM * rng.exponential()
            dl, th = dk / R_EARTH, rng.uniform(0, 2 * math.pi)
            la2 = math.asin(math.sin(la1) * math.cos(dl) +
                            math.cos(la1) * math.sin(dl) * math.cos(th))
            lo2 = lo1 + math.atan2(math.sin(th) * math.sin(dl) *
                                   math.cos(la1),
                                   math.cos(dl) - math.sin(la1) *
                                   math.sin(la2))
            c = int(self.d_tree.query(unit_xyz(math.degrees(lo2),
                                               math.degrees(la2)))[1])
            if taken[self.d_sidx[self.d_sptr[c]:self.d_sptr[c + 1]]].any():
                continue
            if warded[self.d_tidx[self.d_tptr[c]:self.d_tptr[c + 1]]].any():
                continue
            return c
        return -1

    def dragons(self):
        """Dragons hunt, age, breed, and are slain, driven off or taken as
        allies where people have grown too many for them."""
        W, rng, N = self.W, self.drng, self.W.N
        # ageing and other deaths (allied dragons are kept from the latter)
        self.dage += DT
        old = self.dage >= DRAGON_LIFE
        other = (rng.random(len(self.dage)) < DRAGON_MORT * DT) & \
            (self.dally < 0)
        self.count("dragon_died", int((old | other).sum()))
        for d in np.nonzero(old | other)[0]:
            h = self.dragon_hist[self.did[d]]
            h["ended"] = self.year
            h["fate"] = "old age" if old[d] else "died"
        self.d_keep(~old & ~other)
        # allies follow their state, or go wild when it falls
        for d in np.nonzero(self.dally >= 0)[0]:
            P = self.polities.get(int(self.dally[d]))
            if P is None or P["ended"] is not None:
                self.dally[d] = -1
                self.count("dragon_freed")
            elif self.cell_pol[self.dhome[d]] != P["id"]:
                self.dhome[d] = P["capital"]
                self.dragon_hist[self.did[d]]["moves"] += 1
        wild = np.nonzero(self.dally < 0)[0]
        # hunting: each wild dragon covering a cell adds its hunting weight
        # (strength x (0.5 + violence) x (1.3 - 0.6 tolerance)); the ward
        # size scales with the mean strength of the dragons there
        cw, own = self.terr(self.dhome[wild])
        se = self.dseff(wild)
        hw = se * (0.5 + self.dviol[wild]) * \
            (1.3 - 0.6 * self.dtol[wild])
        haz = np.bincount(cw, weights=hw[own], minlength=N)
        sw = np.bincount(cw, weights=(hw * se)[own],
                         minlength=N)
        smean = np.where(haz > 0, sw / np.maximum(haz, 1e-9), 1.0)
        if (self.dally >= 0).any():
            ca, _ = self.terr(self.dhome[self.dally >= 0])
            haz[ca] *= 1 - DRAGON_GUARD
        # the hazard and mean strength feed this tick's growth (grow)
        self.dhaz, self.dsmean = haz, smean
        occ = np.nonzero(self.lin >= 0)[0]
        wd = self.ward(occ) * smean[occ]
        n = self.pop[occ] + self.mpop[occ]
        warded = np.zeros(N, bool)
        warded[occ] = n >= wd
        self.d_warded = warded
        nest = warded.copy()
        nest[occ] |= n >= DRAGON_NEST * wd
        avoid = warded
        if DRAGON_SHUN > 0:
            avoid = warded.copy()
            avoid[occ] |= n >= DRAGON_SHUN * wd
        if "dragon_hosts" in self.on and self.phost.any():
            # the refuge is only where the hosts live: young and driven-off
            # dragons settle among host peoples or in empty land, never
            # within reach of anyone else's settled cells
            other = np.zeros(N, bool)
            other[occ] = ~self.phost[self.cul[occ]]
            nest = nest | other
            avoid = avoid | other
        # confrontations, one per warded cell per 1/CONFRONT years; a
        # stronger dragon counts a cell as warded only past its own ward
        base = np.zeros(N)
        base[occ] = n / self.ward(occ)
        wi = np.nonzero(self.dally < 0)[0]
        cells, own = self.terr(self.dhome[wi])
        sew = self.dseff(wi)
        nw = np.bincount(own, weights=base[cells] >= sew[own],
                         minlength=len(wi))
        hit = wi[rng.random(len(wi)) < 1 - np.exp(-CONFRONT * DT * nw)]
        keep = np.ones(len(self.dhome), bool)
        taken = np.zeros(N, bool)
        taken[self.dhome] = True
        for d in hit:
            tc, _ = self.terr(self.dhome[d:d + 1])
            sd_ = float(self.dseff(d))
            tc = tc[base[tc] >= sd_]
            c = int(tc[np.argmax(self.pop[tc])])
            L, pid = self.lin[c], int(self.cell_pol[c])
            s, v, dt = sd_, self.dviol[d], self.dtol[d]
            self.pop[c] *= 1 - min(0.5, DRAGON_FIGHT * s * (0.5 + v))
            joint = (self.tol[L] + dt) / 2
            h = self.dragon_hist[self.did[d]]
            who = self.pname(pid) if pid >= 0 else self.lname(L)
            if pid >= 0 and joint >= DRAGON_TOL and rng.random() < \
                    (joint - DRAGON_TOL) / (1 - DRAGON_TOL):
                self.dally[d] = pid
                taken[self.dhome[d]] = False
                self.dhome[d] = c
                taken[c] = True
                h["ally"], h["ally_year"] = pid, self.year
                h["ally_people"] = self.keys[self.cul[c]]
                self.count("dragon_ally")
                self.first(("dragon_ally", self.cul[c]), "dragon",
                           f"{who} takes a dragon as ally at {self.place(c)}")
            elif rng.random() < min(0.95, (DRAGON_SLAY0 + DRAGON_SLAY1 *
                                           self.viol[L]) *
                                    (0.5 + v) / s):
                # a violent dragon stands and fights; a strong one survives
                keep[d] = False
                h["ended"], h["fate"] = self.year, "slain"
                self.count("dragon_slain")
                self.first(("dragon_slain", self.cul[c]), "dragon",
                           f"{who} slays a dragon at {self.place(c)}")
            else:
                taken[self.dhome[d]] = False
                site = self.dragon_site(self.dhome[d], avoid, taken)
                if site < 0:
                    keep[d] = False
                    self.count("dragon_lost")
                    h["ended"], h["fate"] = self.year, "driven off, no land"
                else:
                    self.dhome[d] = site
                    taken[site] = True
                    h["moves"] += 1
                    self.count("dragon_pushed")
        self.d_keep(keep)
        if "dragon_hosts" in self.on and self.phost.any():
            self.host_alliances(taken)
        # breeding into free sites; young take after their parent
        ad = np.nonzero((self.dage >= DRAGON_ADULT) &
                        (rng.random(len(self.dage)) < DRAGON_BREED * DT))[0]
        new, par = [], []
        for d in ad:
            site = self.dragon_site(self.dhome[d], nest, taken)
            if site >= 0:
                taken[site] = True
                new.append(site)
                par.append(d)
        if new:
            m, par = len(new), np.array(par)
            z = rng.standard_normal((3, m)) * DRAGON_DRIFT
            lt = lambda p: np.log(p / (1 - p))
            tol = dsig(lt(self.dtol[par]) + z[0])
            viol = dsig(lt(self.dviol[par]) + z[1])
            st = self.dstr[par] * np.exp(z[2])
            ids = np.arange(len(self.dragon_hist), len(self.dragon_hist) + m)
            for i in range(m):
                self.d_hist_add(int(ids[i]), self.year, new[i], tol[i],
                                viol[i], st[i],
                                parent=int(self.did[par[i]]))
            for a, x in (("dhome", new), ("dage", np.zeros(m)),
                         ("dally", -np.ones(m, int)), ("did", ids),
                         ("dtol", tol), ("dviol", viol), ("dstr", st)):
                setattr(self, a, np.concatenate([getattr(self, a), x]))
            self.count("dragon_born", m)
        self.d_by_pid = {}
        for d in np.nonzero(self.dally >= 0)[0]:
            pid = int(self.dally[d])
            self.d_by_pid[pid] = self.d_by_pid.get(pid, 0) + \
                float(self.dseff(d))

    def host_alliances(self, taken):
        """Wild dragons among dragon-host peoples inside a state may be
        taken as allies (no fight)."""
        rng = self.drng
        hostc = (self.lin >= 0) & (self.cell_pol >= 0) & \
            self.phost[np.maximum(self.cul, 0)]
        wi = np.nonzero(self.dally < 0)[0]
        if not len(wi) or not hostc.any():
            return
        cells, own = self.terr(self.dhome[wi])
        nh = np.bincount(own, weights=hostc[cells], minlength=len(wi))
        for d in wi[(nh > 0) & (rng.random(len(wi)) < CONFRONT * DT)]:
            tc, _ = self.terr(self.dhome[d:d + 1])
            tc = tc[hostc[tc]]
            c = int(tc[np.argmax(self.pop[tc])])
            L, pid = self.lin[c], int(self.cell_pol[c])
            joint = (self.tol[L] + self.dtol[d]) / 2
            if joint >= DRAGON_TOL and rng.random() < \
                    (joint - DRAGON_TOL) / (1 - DRAGON_TOL):
                h = self.dragon_hist[self.did[d]]
                self.dally[d] = pid
                taken[self.dhome[d]] = False
                self.dhome[d] = c
                taken[c] = True
                h["ally"], h["ally_year"] = pid, self.year
                h["ally_people"] = self.keys[self.cul[c]]
                self.count("dragon_ally")
                self.first(("dragon_ally", self.cul[c]), "dragon",
                           f"{self.pname(pid)} takes a dragon as ally at "
                           f"{self.place(c)}")

    def dragon_record(self):
        al = self.dally >= 0
        occ = self.lin >= 0
        fd = np.zeros(self.W.N)
        fd[occ] = self.pop[occ] * self.peat[self.cul[occ]] / \
            self.W.area[occ]
        wl = ~al
        st = dict(dragons_wild=int(wl.sum()), dragons_allied=int(al.sum()),
                  dragon_kills=round(float(self.dragon_kills.sum())),
                  dragon_land=round(float((self.dhaz > 0).mean()), 3),
                  warded_cells=int(self.d_warded.sum()),
                  near_empty=round(float((fd < 0.02).mean()), 3),
                  dragon_tol=round(float(self.dtol[wl].mean()), 3)
                  if wl.any() else None,
                  dragon_viol=round(float(self.dviol[wl].mean()), 3)
                  if wl.any() else None,
                  dragon_str=round(float(self.dstr[wl].mean()), 3)
                  if wl.any() else None)
        apc = np.zeros(self.nP, int)
        for d in np.nonzero(al)[0]:
            P = self.polities.get(int(self.dally[d]))
            if P:
                apc[P["culture"]] += 1
        for i, k in enumerate(self.keys):
            st[f"dragon_kills_{k}"] = round(float(self.dragon_kills[i]))
            st[f"dragons_allied_{k}"] = int(apc[i])
        return st

    def land_use(self, occ, L):
        """Herding or farming per cell, and the land condition that farming
        wears down (salinization fastest on irrigated land)."""
        W = self.W
        if self.on & {"pastoral", "land", "improvements", "salinity"}:
            Kc, Kh = self.K2(L, occ)
        if "pastoral" in self.on:
            h = np.clip((self.agri[L] - HERD_AGRI[0]) /
                        (HERD_AGRI[1] - HERD_AGRI[0]), 0, 1)
            self.herding[:] = False
            self.herding[occ] = (Kh > Kc) & (h > 0)
        if "land" in self.on:
            inten = np.zeros(W.N)
            farmed = ~self.herding[occ]
            inten[occ] = farmed * self.agri[L] * \
                np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
            # wear is proportional to what is left; recovery (fallow,
            # flushing) runs regardless, so each cell settles at
            # REC / (REC + DEG x intensity x (1 + IRR x irrigated))
            deg = LAND_DEG * inten * (1 + LAND_IRR * W.irr_share) * self.land
            if "patience" in self.on:
                deg[occ] *= 1.5 - self.pati[L]
            rec = LAND_REC * (1 - self.land)
            self.land = np.clip(self.land + DT * (rec - deg), LAND_MIN, 1)
        if "salinity" in self.on:
            # irrigation brings salt up; fallow and abandonment leach it
            it = np.zeros(W.N)
            it[occ] = ~self.herding[occ] * self.agri[L] * \
                np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
            gain = SALT_GAIN * it * W.irr_share * (1 - self.salt)
            if "patience" in self.on:
                gain[occ] *= 1.5 - self.pati[L]
            self.salt = np.clip(self.salt + DT * (
                gain - SALT_REC * (1 - it) * self.salt), 0, 1)
        if "improvements" in self.on:
            # farmers build; capable states build faster; unused works
            # silt up and fall in
            pl = np.full(self.next_pid, -1)
            for pid, p in self.polities.items():
                if p["ended"] is None:
                    pl[pid] = p["lin"]
            rl = pl[np.maximum(self.cell_pol[occ], 0)]
            adm = np.where((self.cell_pol[occ] >= 0) & (rl >= 0),
                           self.admin[np.maximum(rl, 0)], 0)
            use = np.zeros(W.N)
            use[occ] = ~self.herding[occ] * self.agri[L] * \
                np.clip(self.pop[occ] / np.maximum(Kc, 1e-3), 0, 1)
            build = np.zeros(W.N)
            build[occ] = IMP_BUILD * use[occ] * (0.5 + adm)
            if "patience" in self.on:
                build[occ] *= 0.5 + self.pati[L]
            self.imp += DT * (build * (1 - self.imp) -
                              IMP_DECAY * (1 - use) * self.imp)
            np.clip(self.imp, 0, 1, out=self.imp)

    def adjacency_by_people(self):
        W = self.W
        adj = np.zeros((self.nP, W.N), bool)
        for k in range(8):
            j = W.nb[:, k]
            cn = np.where(j >= 0, self.cul[np.maximum(j, 0)], -1)
            for c in range(self.nP):
                adj[c] |= cn == c
        return adj

    def migrate(self):
        """Within a lineage, people drift toward room; empty land is taken
        by budding, pioneer leaps and voyages."""
        W, N = self.W, self.W.N
        ar = np.arange(N)
        occ = self.lin >= 0
        was = occ.copy()
        L = np.where(occ, self.lin, 0)
        c = self.Lpeople[L]
        press = self.pop / np.maximum(self.Kf(L, ar) * self.pref(L, ar),
                                      1e-3)
        adj = self.adjacency_by_people()
        nadj = adj.sum(0)
        expn, sep = self.expn[L], self.sep[L]
        if "separation" in self.on:
            sep = 1 - self.tol[L]       # keeping apart is intolerance now
        thr = 0.9 - 0.6 * expn
        frac = 0.04 + 0.3 * expn * np.clip(press - thr, 0, 1.5)
        E = np.where(occ, self.pop * frac, 0)
        w = np.zeros((N, 8))
        for k in range(8):
            j = W.nb[:, k]
            jj = np.maximum(j, 0)
            ok = occ & (j >= 0) & (self.lin[jj] == L)
            Kt = np.maximum(self.Kf(L, jj), 1e-3)
            room = np.clip(1 - self.pop[jj] / (Kt * self.pref(L, jj)), 0, 1)
            foreign = (nadj[jj] - adj[c, jj]) > 0
            w[:, k] = ok * room * np.sqrt(Kt) / W.edgecost[:, k] * \
                (1 - 0.9 * sep * foreign)
        Wsum = w.sum(1)
        go = Wsum > 0
        E = np.where(go, E, 0)
        self.pop -= E
        F = (E[:, None] * w / np.where(go, Wsum, 1)[:, None]).ravel()
        tgt = W.nb.ravel()
        m = (tgt >= 0) & (F > 0)
        np.add.at(self.pop, tgt[m], F[m])
        for _ in range(2):
            occ = self.lin >= 0
            L = np.where(occ, self.lin, 0)
            press = self.pop / np.maximum(self.Kf(L, ar) *
                                          self.pref(L, ar), 1e-3)
            adj = self.adjacency_by_people()
            self.settle(*self.budding(press, adj, adj.sum(0), L, occ))
        self.pioneers(press)
        self.voyages(press)
        self.settler_lineages(np.nonzero((self.lin >= 0) & ~was)[0])

    def settler_lineages(self, new):
        """Settlers entering a region (BLOCK x BLOCK cells) their people
        has never held found a daughter lineage: the parent's traits with a
        small mutation."""
        if not len(new) or self.settle_drift <= 0:
            return
        new = new[self.Lfounded[self.lin[new]] != self.year]
        for L, cells in self.by_lineage(new):
            seen = self.Pblk[self.Lpeople[L]]
            b = self.blk[cells]
            for bb in np.unique(b):
                if int(bb) in seen:
                    continue
                seen.add(int(bb))
                D = self.new_lineage(self.Lpeople[L], L, "settler",
                                     sd=self.settle_drift)
                self.lin[cells[b == bb]] = D

    def budding(self, press, adj, nadj, L, occ):
        """A crowded cell splits off one band toward its best empty
        neighbour. Expansive lineages split before they are full."""
        W, N = self.W, self.W.N
        c = self.Lpeople[L]
        thr = 0.45 - 0.35 * self.expn[L]
        can = occ & (press > thr) & (self.pop > 2 * FOUND_MIN)
        best = np.zeros(N)
        tgt = -np.ones(N, int)
        noise = self.rng.uniform(0.6, 1.4, (N, 8))
        for k in range(8):
            j = W.nb[:, k]
            jj = np.maximum(j, 0)
            ok = can & (j >= 0) & (self.lin[jj] < 0)
            Kt = self.Kf(L, jj)
            foreign = (nadj[jj] - adj[c, jj]) > 0
            s = ok * np.sqrt(np.maximum(Kt, 0)) / W.edgecost[:, k] * \
                self.colon(jj, L) * (1 + RIV_BUD * (W.river & W.river[jj])) * \
                (1 - 0.95 * self.hostile(L) * foreign) * noise[:, k] * \
                (Kt > 2 * FOUND_MIN)
            better = s > best
            best = np.where(better, s, best)
            tgt = np.where(better, j, tgt)
        src = np.nonzero(tgt >= 0)[0]
        Ls = L[src]
        band = np.maximum(FOUND_MIN, (0.2 + 0.25 * self.expn[Ls]) *
                          self.pop[src])
        band = np.minimum(np.maximum(band, 0.15 * self.Kf(Ls, tgt[src])),
                          0.5 * self.pop[src])
        self.pop[src] -= band
        return src, tgt[src], band, Ls

    def settle(self, src, tgt, band, bl):
        """Bands claim empty cells; the largest claimant wins, the rest
        go home."""
        if not len(src):
            return
        order = np.lexsort((-band, tgt))
        src, tgt, band, bl = src[order], tgt[order], band[order], bl[order]
        first = np.ones(len(tgt), bool)
        first[1:] = tgt[1:] != tgt[:-1]
        win = first & (self.lin[tgt] < 0)
        self.lin[tgt[win]] = bl[win]
        self.cul[tgt[win]] = self.Lpeople[bl[win]]
        self.pop[tgt[win]] = band[win]
        np.add.at(self.pop, src[~win], band[~win])

    def by_lineage(self, cells):
        """Group cell indices by lineage: yields (L, cells of L)."""
        if not len(cells):
            return
        Ls = self.lin[cells]
        o = np.argsort(Ls, kind="stable")
        cells, Ls = cells[o], Ls[o]
        u, start = np.unique(Ls, return_index=True)
        ends = list(start[1:]) + [len(cells)]
        for L, a, b in zip(u, start, ends):
            yield int(L), cells[a:b]

    def pioneers(self, press):
        """Bands leap past the frontier into empty land 2-6 cells away."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & (self.pop * eat > 300))[0]
        for L, cells in self.by_lineage(cand):
            lam = 3.0 * self.expn[L] ** 2 * (1 + math.log10(1 + len(cells)))
            n = self.rng.poisson(lam)
            if not n:
                continue
            wts = self.pop[cells] * np.clip(press[cells], 0.05, 2)
            for s in self.rng.choice(cells, n, p=wts / wts.sum()):
                if W.river[s] and self.rng.random() < RIV_LEAP:
                    self.river_leap(L, s)
                    continue
                dr, dc = self.rng.integers(-6, 7, 2)
                if max(abs(dr), abs(dc)) < 2:
                    continue
                r2, c2 = W.row[s] + dr, (W.col[s] + dc) % NX
                if not (0 <= r2 < NY):
                    continue
                t = W.idx2[r2, c2]
                if t < 0 or self.lin[t] >= 0 or \
                        self.rng.random() > self.colon(t, L) or \
                        W.landmass[t] != W.landmass[s] or \
                        self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
                    continue
                mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def river_leap(self, L, s):
        """A band travels along the river network from s and settles an
        empty cell on the way."""
        W = self.W
        n = int(RIV_STEPS[0] + RIV_STEPS[1] * self.sail[L])
        downstream = self.rng.random() < 0.5
        x, path = s, []
        for _ in range(n):
            if downstream:
                x = int(W.down[x])
            else:
                ups = W.up[x]
                if not ups:
                    break
                q = W.Q[ups] + 1
                x = int(self.rng.choice(ups, p=q / q.sum()))
            if x < 0:
                break
            path.append(x)
        cand = [t for t in path[1:] if self.lin[t] < 0]
        if not cand:
            return
        t = int(self.rng.choice(cand))
        if self.rng.random() > self.colon(t, L) or \
                self.Kf(L, t) * self.peat[self.Lpeople[L]] < 200:
            return
        mv = min(120.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
        self.pop[s] -= mv
        self.lin[t], self.cul[t], self.pop[t] = L, self.Lpeople[L], mv

    def sail_km(self, L):
        """Typical voyage distance (km) of lineage L."""
        return SAIL_D0 + SAIL_D1 * self.sail[L] ** 1.5

    def voyages(self, press):
        """Sea colonization from crowded coasts to empty coasts. Targets
        are weighted by exp(-distance / sail_km), so sailing sets how far
        colonists usually go rather than whether they can go at all.
        A colony on a landmass new to its lineage founds a daughter
        lineage (founder effect)."""
        W = self.W
        eat = self.peat[np.maximum(self.cul, 0)]
        cand = np.nonzero((self.lin >= 0) & W.coastal & (self.pop * eat > 400) &
                          (press > 0.5))[0]
        col = "colonies" in self.on
        for L, src in self.by_lineage(cand):
            D = self.sail_km(L)
            sea = self.expn[L] if "dispersal" in self.on else self.seaf[L]
            lam = 2.5 * sea * (0.1 + self.sail[L]) * \
                math.sqrt(len(src))
            n = self.rng.poisson(lam)
            for s in self.rng.choice(src, min(n, 6)):
                ids = W.coast_tree.query_ball_point(
                    W.xyz[s], 2 * math.sin(min(4 * D, 9000) / R_EARTH / 2))
                cnd = W.coast_idx[ids]
                if col:
                    nat = self.pop[cnd] * eat[cnd] * (self.lin[cnd] >= 0)
                    keep = (self.lin[cnd] < 0) | (
                        (self.cul[cnd] != self.Lpeople[L]) &
                        (self.cell_city[cnd] != cnd) & (nat < COL_THIN))
                    cnd, nat = cnd[keep], nat[keep]
                else:
                    cnd = cnd[self.lin[cnd] < 0]
                if not len(cnd):
                    continue
                wt = self.Kf(L, cnd)
                ok = wt * self.peat[self.Lpeople[L]] > 300
                cnd, wt = cnd[ok], wt[ok]
                if col:
                    nat = nat[ok]
                if not len(cnd):
                    continue
                wt = wt * np.exp(-gc_km(W.xyz, s, cnd) / D) * self.colon(cnd, L)
                if col:
                    wt = np.where(np.isfinite(wt), wt, 0.0)
                    empty = (nat <= 0) & (wt > 0)
                    if empty.any():
                        # settlers take empty coast where they can
                        wt = np.where(empty, wt, 0.0)
                    else:
                        if self.rng.random() >= COL_OCC:
                            continue
                        wt = wt * np.exp(-nat / COL_THIN)
                if wt.sum() <= 0:
                    continue
                t = int(self.rng.choice(cnd, p=wt / wt.sum()))
                mv = min(200.0 / self.peat[self.Lpeople[L]], 0.2 * self.pop[s])
                self.pop[s] -= mv
                lm = W.landmass[t]
                Lt = L
                sp = int(self.cell_pol[s]) if col else -1
                if sp >= 0 and self.cell_pol[t] != sp and \
                        lm != W.landmass[s]:
                    Lc = self.colony_lin.get((sp, int(lm)), -1)
                    if Lc < 0 or self.Lended[Lc] >= 0:
                        Lc = self.new_lineage(self.Lpeople[L], L, "colony",
                                              sd=self.drift)
                        self.Lcolony[Lc] = sp
                        self.Lseen[Lc] = set(self.Lseen.get(L, set())) | {lm}
                        self.colony_lin[(sp, int(lm))] = Lc
                        self.count("colony_state")
                    Lt = Lc
                if col and self.lin[t] >= 0:
                    fe_n = self.pop[t] * eat[t]
                    if fe_n < mv * self.peat[self.Lpeople[L]]:
                        # thin natives pushed out
                        self.count("colony_displace")
                        self.lin[t], self.cul[t], self.pop[t] = \
                            Lt, self.Lpeople[Lt], mv
                    else:
                        self.count("colony_minority")
                        self.add_minority([t], int(self.Lpeople[Lt]), Lt, mv)
                    continue
                if Lt == L and lm not in self.Lseen[L]:
                    self.Lseen[L].add(lm)
                    if W.landmass_area[lm] > 2e5:
                        Lt = self.new_lineage(self.Lpeople[L], L, "colony",
                                              sd=self.drift)
                        self.Lseen[Lt] = {lm}
                        self.log("voyage", f"{self.lname(L)} sailors land "
                                 f"on a new landmass at {self.place(t)} "
                                 f"({W.landmass_area[lm]/1e6:.1f}M km2), "
                                 f"founding {self.lname(Lt)}")
                self.lin[t], self.cul[t], self.pop[t] = \
                    Lt, self.Lpeople[Lt], mv

    def raids(self):
        """Cell-scale violence where peoples touch outside state control."""
        W = self.W
        a, b = W.E1, W.E2
        ca, cb = self.cul[a], self.cul[b]
        mix = (ca >= 0) & (cb >= 0) & (ca != cb)
        a, b, ca, cb = a[mix], b[mix], ca[mix], cb[mix]
        if not len(a):
            return
        for x, y in set(zip(ca.tolist(), cb.tolist())):
            if not self.contact_seen[x, y]:
                self.contact_seen[x, y] = self.contact_seen[y, x] = True
                self.log("contact", f"first contact: {self.keys[x]} meets "
                         f"{self.keys[y]}")
        for att, dfn in ((a, b), (b, a)):
            La, Ld = self.lin[att], self.lin[dfn]
            pa = self.pop[att] / np.maximum(self.Kf(La, att), 1e-3)
            same_state = (self.cell_pol[att] >= 0) & \
                (self.cell_pol[att] == self.cell_pol[dfn])
            p = DT * 0.02 * self.viol[La] * (0.5 + pa) * \
                (1 + self.hostile(La)) * self.tolf(La, 0.5) * \
                np.where(same_state, 0.2, 1)
            if "raid_order" in self.on:
                p = p * self.raid_order(att, dfn, same_state)
            if "pastoral" in self.on:
                # mounted herders raid more often
                p = p * np.where(self.herding[att], 1.5, 1)
            if "climate" in self.on:
                # and so do the hungry
                p = p * (1 + HUNGER_RAID * np.clip(pa - 1, 0, 1))
            hit = self.rng.random(len(att)) < np.clip(p, 0, 0.9)
            self.count("raid", int(hit.sum()))
            rel = np.sqrt(self.psize[self.cul[att]] / self.psize[self.cul[dfn]])
            dmg = 0.12 * self.viol[La] * rel / W.defence[dfn]
            if "pastoral" in self.on:
                dmg = dmg * np.where(self.herding[att], MOUNT, 1)
            if "costs" in self.on:
                # expansive peoples leave thin, exposed frontier cells
                pdn = self.pop[dfn] / np.maximum(self.Kf(Ld, dfn), 1e-3)
                dmg = dmg * (1 + COST_EXPN * self.expn[Ld] *
                             np.clip(1 - 2 * pdn, 0, 1))
            loss = 1 - np.clip(dmg[hit], 0, 0.6)
            self.pop[dfn[hit]] *= loss
            if "improvements" in self.on:
                self.imp[dfn[hit]] *= 1 - 0.3 * (1 - loss)
            if self.cities:
                self.shock(dfn[hit][np.isin(dfn[hit], list(self.cities))],
                           "raid")
            self.mpop[dfn[hit]] *= loss
            self.raided[dfn[hit]] = 1
            self.raided[att[hit]] = 1
            self.pop[att[hit]] *= 0.99
            pd = self.pop[dfn] / np.maximum(self.Kf(Ld, dfn), 1e-3)
            take = hit & (pd < 0.15) & (pa > 0.6) & \
                (self.rng.random(len(att)) < self.viol[La])
            ti, first = np.unique(dfn[take], return_index=True)
            if self.cities:
                self.shock(ti[np.isin(ti, list(self.cities))],
                           "raid takeover")
            si = att[take][first]
            mv = 0.25 * self.pop[si]
            self.pop[si] -= mv
            if "minority" in self.on:
                # the old people stays on as an underclass
                self.mcul[ti], self.mlin[ti] = self.cul[ti], self.lin[ti]
                self.mpop[ti] = 0.5 * self.pop[ti]
            self.lin[ti] = self.lin[si]
            self.cul[ti] = self.cul[si]
            self.pop[ti] = mv

    def raid_order(self, att, dfn, same_state):
        """How far states and peace hold raids back on these edges."""
        pl = np.full(self.next_pid, -1)
        for pid, P in self.polities.items():
            if P["ended"] is None:
                pl[pid] = P["lin"]
        f = np.ones(len(att))
        for c in (att, dfn):
            pc = self.cell_pol[c]
            L = pl[np.maximum(pc, 0)]
            ok = (pc >= 0) & (L >= 0)
            f = f * np.where(ok, 1 - RAID_ADMIN *
                             self.admin[np.maximum(L, 0)], 1)
        pa, pb = self.cell_pol[att], self.cell_pol[dfn]
        two = (pa >= 0) & (pb >= 0) & (pa != pb)
        if two.any():
            lo, hi = np.minimum(pa[two], pb[two]), np.maximum(pa[two], pb[two])
            keys = lo.astype(np.int64) * 10_000_000 + hi
            uk, inv = np.unique(keys, return_inverse=True)
            g = np.ones(len(uk))
            for i, kk in enumerate(uk):
                k = (int(kk // 10_000_000), int(kk % 10_000_000))
                g[i] = 1 - self.ties.get(k, 0.0)
                if k in self.allies or self.truce.get(k, -1) > self.tick:
                    g[i] *= RAID_PEACE
            f[two] = f[two] * g[inv]
        return f

    def tidy(self):
        if "minority" in self.on:
            self.tidy_minorities()
        dead = (self.pop < 5) & (self.lin >= 0)
        self.pop[dead] = 0
        self.cul[dead] = -1
        self.lin[dead] = -1

    def tidy_minorities(self):
        """A minority that outnumbers the majority (in food terms) becomes
        the majority; a minority of the majority's own people merges into
        it; tiny minorities vanish."""
        m = self.mlin >= 0
        gone = m & ((self.mpop < 5) | (self.lin < 0) & (self.mpop < 20))
        merge = m & ~gone & (self.mcul == self.cul)
        self.pop[merge] += self.mpop[merge]
        swap = m & ~gone & ~merge & \
            (self.mpop * self.peat[np.maximum(self.mcul, 0)] >
             self.pop * self.peat[np.maximum(self.cul, 0)])
        s = np.nonzero(swap)[0]
        if len(s):
            c0, l0, p0 = self.cul[s].copy(), self.lin[s].copy(), \
                self.pop[s].copy()
            self.cul[s], self.lin[s], self.pop[s] = \
                self.mcul[s], self.mlin[s], self.mpop[s]
            self.mcul[s], self.mlin[s], self.mpop[s] = c0, l0, p0
            for x, old in zip(s, c0):
                if x in self.cities and old >= 0:
                    # the city carries on under its new majority
                    self.cities[x]["culture"] = int(self.cul[x])
                    self.cities[x]["flips"] = \
                        self.cities[x].get("flips", 0) + 1
                    self.log("minority", f"{self.keys[self.cul[x]]} come to "
                             f"outnumber {self.keys[old]} in the city at "
                             f"{self.place(x)}")
        clear = gone | merge | (self.mcul < 0)
        self.mcul[clear], self.mlin[clear], self.mpop[clear] = -1, -1, 0

    def add_minority(self, cells, c, L, amount):
        """Settle `amount` (per cell) of people c, lineage L, as the
        minority of cells, unless another minority is already there."""
        cells = np.asarray(cells, int)
        ok = (self.cul[cells] != c) & ((self.mcul[cells] < 0) |
                                       (self.mcul[cells] == c))
        cells, amount = cells[ok], np.broadcast_to(amount, ok.shape)[ok]
        new = self.mcul[cells] < 0
        self.mcul[cells], self.mlin[cells] = c, np.where(new, L,
                                                         self.mlin[cells])
        self.mpop[cells] += amount

    # ---- cities and polities
    def new_polity(self, L, capital, cohesion=0.6, parent=None):
        pid = self.next_pid
        self.next_pid += 1
        c = int(self.Lpeople[L])
        self.polities[pid] = dict(id=pid, culture=c, lin=int(L),
                                  capital=capital, founded=self.year,
                                  ended=None, cohesion=cohesion, trade=0.0,
                                  fed=1.0, crowd=0.5, elite=1.0, stress=0.0,
                                  herd=0.0, vassal_years=0,
                                  next_succ=self.year + SUCC_GEN * (
                                      self.plife[c] if "rulers" in self.on
                                      else 1),
                                  cities={capital}, peak_cells=0,
                                  peak_year=self.year, peak_cities=1,
                                  peak_pop=0, peak_mask=None, peoples=set(),
                                  parent=parent, n_cells=0, strength=0,
                                  pop=0, col=self.polity_color(c))
        return pid

    def polity_color(self, c):
        base = self.colors[c].astype(float)
        wide = self.nP <= 5
        j = self.rng.uniform(0.55, 1.25) if wide else \
            self.rng.uniform(0.7, 1.15)
        h = self.rng.uniform(-28, 28, 3) if wide else \
            self.rng.uniform(-15, 15, 3)
        return np.clip(base * j + h, 20, 245).astype(np.uint8)

    def end_city(self, cell, why):
        rec = self.cities.pop(cell)
        rec["ended"] = self.year
        rec["end_reason"] = why
        rec["cause"] = self.end_cause(rec)
        rec["end_pop"] = float(self.pop[cell])
        self.ruins[cell] = rec
        p = self.polities.get(rec["polity"])
        if p:
            p["cities"].discard(cell)
            if p["capital"] == cell:
                self.recapital(p)

    def recapital(self, p):
        if not p["cities"]:
            self.kill_polity(p["id"], "lost its last city")
            return
        p["capital"] = max(p["cities"], key=lambda x: self.pop[x])

    def kill_polity(self, pid, why):
        p = self.polities.get(pid)
        if p is None or p["ended"] is not None:
            return
        p["ended"] = self.year
        self.vassal.pop(pid, None)
        for v in [v for v, o in self.vassal.items() if o == pid]:
            del self.vassal[v]
            self.count("vassal_freed")
        if p["peak_cities"] >= 3 or p["peak_cells"] >= 150:
            self.log("fall", f"{self.pname(pid)} falls ({why}); "
                     f"{self.year - p['founded']} yrs, peak "
                     f"{p['peak_cities']} cities / {p['peak_cells']} cells")
        for key in [k for k in self.wars if pid in k]:
            w = self.wars.pop(key)
            side = "defender" if w.get("dfn") == pid else "attacker"
            self.war_close(w, f"{side} fell ({why})")
        for d in (self.ties, self.allies):
            for key in [k for k in d if pid in k]:
                del d[key]
        for c in list(p["cities"]):
            self.cities.get(c, {}).update(polity=-1)
        p["cities"] = set()

    def update_cities(self):
        W = self.W
        for cell in list(self.cities):
            rec = self.cities[cell]
            if self.cul[cell] != rec["culture"]:
                self.end_city(cell, "people replaced")
            elif self.pop[cell] < CITY_KEEP * self.pcity[rec["culture"]]:
                self.end_city(cell, "depopulated")
        pot2 = np.zeros((NY, NX))
        occ = self.lin >= 0
        fpop = np.where(occ, self.pop * self.peat[np.maximum(self.cul, 0)], 0)
        pot = fpop * W.locus
        if "pastoral" in self.on:
            # herders rarely found cities: their camps move
            fpop = np.where(self.herding, 0.3 * fpop, fpop)
            pot = fpop * W.locus
        pot2[W.row, W.col] = pot
        mx = ndimage.maximum_filter(pot2, size=5, mode="wrap")
        taken = np.zeros((NY, NX), bool)
        if self.cities:
            cc = np.fromiter(self.cities.keys(), int)
            taken[W.row[cc], W.col[cc]] = True
            taken = ndimage.binary_dilation(taken, np.ones((5, 5)))
        settled = np.where(self.herding, 0.3, 1.0) * self.pop
        cand = np.nonzero(occ & (settled > self.pcity[np.maximum(
            self.cul, 0)]) &
                          (pot >= mx[W.row, W.col]) &
                          ~taken[W.row, W.col])[0]
        for cell in cand:
            c, L = int(self.cul[cell]), int(self.lin[cell])
            owner = int(self.cell_pol[cell])
            op = self.polities.get(owner)
            join = False
            if op is not None and op["ended"] is None:
                if op["culture"] == c:
                    join = self.rng.random() < \
                        0.3 + 0.7 * self.state[op["lin"]]
                else:
                    join = self.rng.random() < 0.7
            elif "colonies" in self.on and self.Lcolony[L] >= 0:
                op = self.polities.get(int(self.Lcolony[L]))
                if op is not None and op["ended"] is None and \
                        op["culture"] == c:
                    owner = op["id"]
                    join = self.rng.random() < \
                        0.3 + 0.7 * self.state[op["lin"]]
                    if join:
                        self.count("colony_city")
            rec = dict(cell=int(cell), culture=c, founded=self.year,
                       ended=None, end_reason="", peak=0.0, polity=-1,
                       lon=float(W.lon[cell]), lat=float(W.lat[cell]),
                       owners=[], id=len(self.city_hist), shocks=[],
                       peak_year=self.year, cause="", end_pop=0.0,
                       refounded=None, successor=None, ruin_empty=0,
                       ruin_years=0, n_sacks=0, prev=None)
            # a city founded near a ruin ends that ruin
            r0, c0 = W.row[cell], W.col[cell]
            for rc in [x for x in self.ruins
                       if abs(int(W.row[x]) - r0) <= 2 and
                       min(abs(int(W.col[x]) - c0),
                           NX - abs(int(W.col[x]) - c0)) <= 2]:
                old = self.ruins.pop(rc)
                old["refounded"] = self.year
                old["successor"] = rec["id"]
                if rec["prev"] is None:
                    rec["prev"] = old["id"]
            self.cities[cell] = rec
            self.city_hist.append(rec)
            if join:
                rec["polity"] = owner
                op["cities"].add(cell)
            else:
                rec["polity"] = self.new_polity(L, cell)
            rec["owners"].append(rec["polity"])
            self.first(("city", c), "city", f"first city of {self.keys[c]} "
                       f"at {self.place(cell)}")

    def territory(self):
        W = self.W
        self.cell_pol[:] = -1
        self.cell_city[:] = -1
        if not self.cities:
            return
        cc = np.fromiter(self.cities.keys(), int)
        creach = np.zeros(W.N)
        creach[cc] = [self.reach(self.polities[self.cities[c]["polity"]])
                      if self.cities[c]["polity"] in self.polities else REACH0
                      for c in cc]
        dist, _, src = dijkstra(W.G, indices=cc, min_only=True,
                                return_predecessors=True,
                                limit=max(1.5 * (REACH0 + REACH1),
                                          creach.max()) + 1)
        ok = src >= 0
        si = np.where(ok, src, 0)
        cpol = np.full(W.N, -1)
        cpol[cc] = [self.cities[c]["polity"] for c in cc]
        ok &= dist <= creach[si]
        self.cell_city[ok] = src[ok]
        self.cell_pol[ok] = cpol[src[ok]]

    def polity_stats(self):
        W = self.W
        n = self.next_pid
        pol = self.cell_pol
        m = pol >= 0
        Lpop = np.bincount(self.lin[self.lin >= 0],
                           weights=self.pop[self.lin >= 0], minlength=self.nL)
        pc = np.full(n, -1)
        pl = np.zeros(n, int)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                # a ruling lineage that has died out passes to the capital's
                cap = p["capital"]
                if Lpop[p["lin"]] <= 0 and self.lin[cap] >= 0:
                    p["lin"] = int(self.lin[cap])
                    p["dyn"] = self.year
                    p["culture"] = int(self.cul[cap])
                pc[pid], pl[pid] = p["culture"], p["lin"]
        own = m & (self.cul == pc[np.maximum(pol, 0)])
        # records: share of each state's people (food-equivalents) not of
        # its ruler's people, as majorities or minorities
        fe = self.pop * self.peat[np.maximum(self.cul, 0)] * (self.lin >= 0)
        mfe = self.mpop * self.peat[np.maximum(self.mcul, 0)] * \
            (self.mlin >= 0)
        pcm = pc[np.maximum(pol, 0)]
        tot_fe = np.bincount(pol[m], weights=(fe + mfe)[m], minlength=n)
        for_fe = np.bincount(pol[m], weights=(fe * (self.cul != pcm) +
                                              mfe * (self.mcul != pcm))[m],
                             minlength=n)
        foreign = for_fe / np.maximum(tot_fe, 1e-9)
        tolp = self.tol[pl[np.maximum(pol, 0)]]
        popw = np.where(own, self.pop, (0.4 + 0.5 * tolp) * self.pop) * \
            self.psize[np.maximum(self.cul, 0)]
        if "pastoral" in self.on:
            popw = popw * np.where(self.herding, MOUNT, 1)
        if "minority" in self.on:
            mown = self.mcul == pc[np.maximum(pol, 0)]
            popw = popw + (self.mlin >= 0) * self.mpop * \
                self.psize[np.maximum(self.mcul, 0)] * \
                np.where(mown, 1, 0.4 + 0.5 * tolp)
        pop_by = np.bincount(pol[m], weights=self.pop[m], minlength=n)
        str_by = np.bincount(pol[m], weights=popw[m], minlength=n)
        if self.on & {"fiscal", "unrest", "pastoral", "climate"}:
            # fed share and crowding of each state's people, and its
            # herding share
            mo = np.nonzero(m & (self.lin >= 0))[0]
            K = np.maximum(self.Kf(self.lin[mo], mo), 1e-3)
            pw = self.pop[mo]
            fed_by = np.bincount(pol[mo], weights=np.minimum(pw, K),
                                 minlength=n) / np.maximum(pop_by, 1)
            crowd_by = np.bincount(pol[mo], weights=pw * pw / K,
                                   minlength=n) / np.maximum(pop_by, 1)
            herd_by = np.bincount(pol[mo], weights=pw * self.herding[mo],
                                  minlength=n) / np.maximum(pop_by, 1)
            kd_by = np.bincount(pol[mo], weights=K * self.peat[
                self.cul[mo]], minlength=n) / np.maximum(
                np.bincount(pol[mo], weights=W.area[mo], minlength=n), 1)
            churn_by = np.bincount(pol[mo], weights=pw *
                                   self.Lchurn[self.lin[mo]],
                                   minlength=n) / np.maximum(pop_by, 1)
        cells_by = np.bincount(pol[m], minlength=n)
        area_by = np.bincount(pol[m], weights=W.area[m], minlength=n)
        # assimilation: kin under a ruling lineage slowly take it on
        rl = pl[np.maximum(pol, 0)]
        kin = m & own & (self.lin >= 0) & (self.lin != rl)
        pk = (0.5 + self.pros[rl]) if "proselytism" in self.on else 1.0
        conv = kin & (self.rng.random(W.N) <
                      DT * 0.008 * (0.5 + self.state[rl]) * pk)
        self.lin[conv] = rl[conv]
        # borders
        pa, pb = pol[W.E1], pol[W.E2]
        frontier = np.zeros(n)
        border = np.zeros(n)
        for x, y, ex, ey in ((pa, pb, W.E1, W.E2), (pb, pa, W.E2, W.E1)):
            cy = self.cul[ey]
            b = (x >= 0) & (x != y)
            np.add.at(border, x[b], 1)
            f = b & (cy >= 0) & (cy != pc[np.maximum(x, 0)])
            if "pastoral" in self.on:
                # the steppe-sown border is a frontier too
                f |= b & (cy >= 0) & (self.herding[ex] != self.herding[ey])
            np.add.at(frontier, x[f], 1)
        adjm = (pa >= 0) & (pb >= 0) & (pa != pb)
        lo, hi = np.minimum(pa[adjm], pb[adjm]), np.maximum(pa[adjm],
                                                           pb[adjm])
        keys = np.unique(lo.astype(np.int64) * 10_000_000 + hi)
        self.adj = {(int(k // 10_000_000), int(k % 10_000_000))
                    for k in keys}
        self.adj |= self.sea_adjacency()
        if "land_pressure" in self.on:
            self.state_room(n)
        for pid, p in self.polities.items():
            if p["ended"] is not None:
                continue
            L = p["lin"]
            mil = (0.5 + self.viol[L]) * (1 + METAL_MIL[0] * self.bronze[L] +
                                         METAL_MIL[1] * self.iron[L] +
                                         METAL_MIL[2] * self.steel[L])
            p["pop"] = pop_by[pid]
            p["n_cells"] = int(cells_by[pid])
            p["km2"] = float(area_by[pid])
            p["strength"] = str_by[pid] * mil * (0.3 + 0.7 * p["cohesion"])
            if "precious" in self.on and pid in self.p_output:
                # gold and silver pay soldiers
                p["strength"] *= 1 + PREC_STR * min(
                    1.0, float(self.p_output[pid].sum()))
            if self.on & {"fiscal", "unrest", "pastoral", "climate"} and \
                    pop_by[pid] > 0:
                p["fed"] += FISC_EMA * (fed_by[pid] - p["fed"])
                p["crowd"] += FISC_EMA * (crowd_by[pid] - p["crowd"])
                p["herd"] = float(herd_by[pid])
                p["kdens"] = float(kd_by[pid])
            if "fiscal" in self.on:
                # armies are paid from the harvest, not from head count
                p["strength"] *= 0.4 + 0.6 * p["fed"]
            nd = self.d_by_pid.get(pid, 0)
            if "hierarchy" in self.on:
                p["strength"] *= HIER_MIL0 + HIER_MIL1 * self.hier[L]
            if nd:
                # allied dragons fight for the state
                p["strength"] *= 1 + DRAGON_WAR * math.sqrt(nd)
            if "unrest" in self.on:
                # elites multiply when land is crowded (cheap labour, high
                # rents) and thin out otherwise; stress = crowding x elite
                # load, worse when an extractive state goes hungry
                e = p["elite"]
                eg = ELITE_G * (0.5 + self.hier[L]) \
                    if "hierarchy" in self.on else ELITE_G
                p["elite"] = float(np.clip(
                    e + DT * eg * e * (p["crowd"] - ELITE_CROWD) /
                    (1 - ELITE_CROWD), 0.3, 4))
                hunger = 1 - p["fed"]
                ext = self.hier[L] if "hierarchy" in self.on \
                    else self.state[L]
                cost = 1 + COST_STATE * ext * hunger \
                    if "costs" in self.on else 1
                p["stress"] = max(0.0, p["crowd"] ** 2 * p["elite"] - 0.6) * \
                    cost * (1 + 4 * hunger)
                if "mission" in self.on:
                    # customs changing fast unsettle a state
                    p["churn"] = float(churn_by[pid])
                    p["stress"] += MIS_UNREST * p["churn"]
            ff = frontier[pid] / max(border[pid], 1)
            S = p["cohesion"]
            nc = len(p["cities"])
            age = self.year - p.get("dyn", p["founded"]) \
                if "dynasty" in self.on else self.year - p["founded"]
            dS = 0.04 * self.coh[L] * S * (1 - S) * (0.3 + ff) - \
                0.004 * S * (1 + 0.5 * math.log1p(nc)) * (1 + age / 600)
            p["cohesion"] = float(np.clip(S + DT * dS, 0.02, 1))
            if p["n_cells"] > p["peak_cells"]:
                p["peak_cells"] = p["n_cells"]
                p["peak_year"] = self.year
                if p["n_cells"] >= 120:
                    p["peak_mask"] = np.nonzero(pol == pid)[0]
            p["peak_cities"] = max(p["peak_cities"], nc)
            p["peak_pop"] = max(p["peak_pop"], p["pop"])
            p["peak_foreign"] = max(p.get("peak_foreign", 0.0),
                                    float(foreign[pid]))
            for x in p["cities"]:
                p["peoples"].add(self.cities[x]["culture"])
        if self.on & {"resources", "trade_assets", "war_motive"}:
            self.state_assets()
        if "vassals" in self.on:
            # tribute: a share of each vassal's strength serves its lord
            for v, o in list(self.vassal.items()):
                V, O = self.polities.get(v), self.polities.get(o)
                if not V or not O or V["ended"] is not None or \
                        O["ended"] is not None:
                    self.vassal.pop(v, None)
                    continue
                t = VASSAL_TRIB * V["strength"]
                V["strength"] -= t
                O["strength"] += t
                V["vassal_years"] += DT

    def state_room(self, n):
        """Room of each state: settleable empty cells along its edge."""
        W, pol = self.W, self.cell_pol
        P, Cc, Lc = [], [], []
        for x, y in ((W.E1, W.E2), (W.E2, W.E1)):
            m = (pol[x] >= 0) & (self.lin[x] >= 0) & (self.lin[y] < 0)
            P.append(pol[x][m])
            Cc.append(y[m])
            Lc.append(self.lin[x][m])
        P, Cc, Lc = np.concatenate(P), np.concatenate(Cc), np.concatenate(Lc)
        empty = np.zeros(n)
        if len(P):
            _, ix = np.unique(P.astype(np.int64) * W.N + Cc, return_index=True)
            P, Cc, Lc = P[ix], Cc[ix], Lc[ix]
            ok = self.Kf(Lc, Cc) * self.peat[self.Lpeople[Lc]] > 200
            empty = np.bincount(P[ok], minlength=n).astype(float)
        cells = np.bincount(pol[pol >= 0], minlength=n)
        room = np.clip(empty / np.maximum(LP_ROOM * cells, 1), 0, 1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                p["room"] = float(room[pid])

    def pressure(self, P):
        """Land pressure of state P (0-1)."""
        d = self.dom[P["lin"]] if "dominance" in self.on else 0.5
        th = LP_HI - LP_SPAN * d
        return float(np.clip((P["crowd"] - th) / (1 - th), 0, 1)) * \
            (1 - P.get("room", 0.0))

    def sea_adjacency(self):
        """Polities whose coastal cities lie within a sailor's range."""
        W = self.W
        if self.tick % 4 and hasattr(self, "_sea_adj"):
            return {k for k in self._sea_adj
                    if all(self.polities.get(x, {}).get("ended", 1) is None
                           for x in k)}
        out = set()
        cc = [c for c in self.cities if W.coastal[c] and
              self.cities[c]["polity"] in self.polities]
        if len(cc) > 1:
            cc = np.array(cc)
            tree = cKDTree(W.xyz[cc])
            for c in cc:
                pid = self.cities[c]["polity"]
                rng_km = 2 * self.sail_km(self.polities[pid]["lin"])
                for j in tree.query_ball_point(
                        W.xyz[c], 2 * math.sin(rng_km / R_EARTH / 2)):
                    q = self.cities[cc[j]]["polity"]
                    if q != pid and q in self.polities:
                        out.add((min(pid, q), max(pid, q)))
        self._sea_adj = out
        return out

    def live(self, k):
        a, b = self.polities.get(k[0]), self.polities.get(k[1])
        if not a or not b or a["ended"] is not None or b["ended"] is not None:
            return None
        return a, b

    def pref_spread(self):
        """Tastes spread: subjects toward their ruler, trading rulers
        toward each other (`goods_value`)."""
        rl = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                rl[pid] = p["lin"]
        m = (self.lin >= 0) & (self.cell_pol >= 0)
        key = np.unique(self.cell_pol[m].astype(np.int64) * MAXL +
                        self.lin[m])
        pol, lin = key // MAXL, key % MAXL
        ru = rl[pol]
        ok = (ru >= 0) & (ru != lin)
        lin, ru = lin[ok], ru[ok]
        if len(lin):
            d = PREF_RULE * (self.Lpref[ru] - self.Lpref[lin])
            np.add.at(self.Lpref, lin, d)
        for (x, y), t in self.ties.items():
            a, b = rl[x], rl[y]
            if a >= 0 and b >= 0 and a != b:
                d = PREF_TRADE * t * (self.Lpref[b] - self.Lpref[a])
                self.Lpref[a] += d
                self.Lpref[b] -= d

    def trade_posts(self):
        """Merchant states plant posts in distant foreign ports
        (`trade_posts`); posts lapse when their merchants are gone."""
        W, rng = self.W, self.rng
        for k, (o, c, y) in list(self.posts.items()):
            h = k[1] if k[0] == o else k[0]
            rec = self.cities.get(c)
            O = self.polities.get(o)
            if rec is None or rec["polity"] != h or O is None or \
                    O["ended"] is not None or self.mcul[c] != O["culture"]:
                del self.posts[k]
        cc = [c for c in self.cities if W.coastal[c] and
              self.cities[c]["polity"] in self.polities and
              self.polities[self.cities[c]["polity"]]["ended"] is None]
        if len(cc) < 2:
            return
        cc = np.array(cc)
        cpol = np.array([self.cities[c]["polity"] for c in cc])
        for pid in sorted(set(cpol.tolist())):
            P = self.polities[pid]
            L = P["lin"]
            if rng.random() >= DT * POST_K * self.trade[L] * self.sail[L]:
                continue
            D = self.sail_km(L)
            src = cc[cpol == pid]
            d = np.min([gc_km(W.xyz, x, cc) for x in src], 0)
            ok = (cpol != pid) & (d < 4 * D)
            ok &= np.array([(min(pid, q), max(pid, q)) not in self.adj
                            for q in cpol])
            ok &= self.cul[cc] != P["culture"]
            if not ok.any():
                continue
            fe = self.pop[cc] * self.peat[np.maximum(self.cul[cc], 0)]
            wt = np.where(ok, fe * np.exp(-d / (2 * D)), 0)
            if wt.sum() <= 0:
                continue
            i = int(rng.choice(len(cc), p=wt / wt.sum()))
            c, h = int(cc[i]), int(cpol[i])
            self.add_minority([c], P["culture"], L, MIN_POST * self.pop[c] *
                              self.peat[self.cul[c]] / self.peat[P["culture"]])
            if self.mcul[c] == P["culture"]:
                k = (min(pid, h), max(pid, h))
                if k not in self.posts:
                    self.count("trade_post")
                    if len(P["cities"]) + len(self.polities[h]["cities"]) \
                            >= 8:
                        self.log("trade", f"{self.pname(pid)} plants a "
                                 f"trading post at {self.place(c)} in "
                                 f"{self.pname(h)}")
                self.posts[k] = (pid, c, self.year)

    def trade_ties(self):
        """Trade grows with both sides' trade drive and tolerance, gated by
        whether each tolerates the other's difference."""
        pairs = self.adj
        if "trade_posts" in self.on and self.posts:
            pairs = self.adj | set(self.posts)
        for k in list(self.ties):
            if k not in pairs or k in self.wars or not self.live(k):
                self.ties[k] *= 0.9
                if self.ties[k] < 0.02:
                    del self.ties[k]
        W = self.W
        riv = {}
        for pid, p in self.polities.items():
            if p["ended"] is None and p["cities"]:
                cc = np.fromiter(p["cities"], int)
                rc = cc[W.river[cc]]
                riv[pid] = (len(rc) / len(cc), set(W.basin[rc].tolist()))
        for k in (sorted(pairs) if pairs is not self.adj else self.adj):
            if k in self.wars:
                continue
            ab = self.live(k)
            if not ab:
                continue
            La, Lb = ab[0]["lin"], ab[1]["lin"]
            ra, ba = riv.get(k[0], (0.0, set()))
            rb, bb = riv.get(k[1], (0.0, set()))
            if "trade_assets" in self.on:
                # goods one side has and the other wants can carry trade
                # past intolerance
                X = math.sqrt(self.offer(k[0], k[1]) * self.offer(k[1], k[0]))
                acc = self.accept(La, Lb, TOL_TRADE2)
                if "trade_floor" in self.on:
                    acc = TRADE_FLOOR + (1 - TRADE_FLOOR) * acc
                acc = acc + (1 - acc) * min(1.0, X / ASSET_X0)
                rate, xb = TRADE_RATE2, 1 + min(X, ASSET_XMAX)
            else:
                acc, rate, xb = self.accept(La, Lb, TOL_TRADE), 0.03, 1.0
            g = self.trade[La] * self.trade[Lb] * \
                (0.4 + 0.3 * (self.tol[La] + self.tol[Lb])) * acc * \
                (1 + RIV_TRADE * (ra + rb) / 2) * \
                (1 + BASIN_TRADE * bool(ba & bb)) * xb
            if "development" in self.on:
                g *= 1 + DEV_TRADE * (self.dev(La) + self.dev(Lb)) / 2
            if "war_v2" in self.on and "dominance" in self.on:
                g *= 1.25 - 0.25 * (self.dom[La] + self.dom[Lb])
            t = self.ties.get(k, 0.0)
            if "trade_assets" in self.on:
                # exact over the tick, so a tie never passes 1
                self.ties[k] = 1 - (1 - t) * math.exp(-DT * rate * g)
            else:
                self.ties[k] = t + DT * rate * g * (1 - t)
        for (x, y), t in self.ties.items():
            cx, cy = self.polities[x]["culture"], self.polities[y]["culture"]
            if cx != cy and t > 0.5 and not self.trade_seen[cx, cy]:
                self.trade_seen[cx, cy] = self.trade_seen[cy, cx] = True
                self.log("trade", f"lasting trade between {self.keys[cx]} "
                         f"and {self.keys[cy]}: {self.pname(x)} and "
                         f"{self.pname(y)}")
        tot = {}
        for (x, y), t in self.ties.items():
            tot[x] = tot.get(x, 0) + t
            tot[y] = tot.get(y, 0) + t
        for pid, p in self.polities.items():
            p["trade"] = tot.get(pid, 0.0)
            if "resources" in self.on:
                p["trade"] += RES_VOLUME * p.get("n_kinds", 0)

    def minorities(self):
        """Merchant quarters along lasting trade between peoples; expulsion
        of foreign minorities by intolerant, separatist rulers."""
        rng = self.rng
        for (x, y), t in self.ties.items():
            if t < 0.5:
                continue
            X, Y = self.polities[x], self.polities[y]
            if X["culture"] == Y["culture"]:
                continue
            for host, guest in ((X, Y), (Y, X)):
                if rng.random() < DT * 0.01 * t:
                    cap, gc = host["capital"], guest["culture"]
                    self.add_minority([cap], gc, guest["lin"],
                                      MIN_MERCHANT * t * self.pop[cap] *
                                      self.peat[host["culture"]] /
                                      self.peat[gc])
        m = np.nonzero((self.mlin >= 0) & (self.cell_pol >= 0))[0]
        if not len(m):
            return
        pl = np.full(self.next_pid, -1)
        pc = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                pl[pid], pc[pid] = p["lin"], p["culture"]
        L = pl[self.cell_pol[m]]
        foreign = (L >= 0) & (self.mcul[m] != pc[self.cell_pol[m]])
        pr = DT * MIN_EXPEL * self.hostile(L) * self.tolf(L, 1.0)
        out = m[foreign & (rng.random(len(m)) < pr)]
        self.mcul[out], self.mlin[out], self.mpop[out] = -1, -1, 0

    def diplomacy(self):
        """Alliances form between neighbours who tolerate each other; long
        alliances can fuse into one state. Within a people moderate
        tolerance suffices; across peoples both must be highly tolerant."""
        rng = self.rng
        if "vassals" in self.on:
            self.vassal_politics()
        threat = self.threats() if "balance" in self.on else {}
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or k in self.wars:
                self.allies.pop(k, None)
                continue
            La, Lb = ab[0]["lin"], ab[1]["lin"]
            if rng.random() < DT * 0.004 * (1 - self.accept(La, Lb,
                                                              TOL_ALLY)) * \
                    (1 - threat.get(k, 0.0)):
                self.allies.pop(k, None)
                self.ally_kind.pop(k, None)
                self.count("ally_break")
                continue
            if "ally_lapse" in self.on and rng.random() < DT * ALLY_LAPSE:
                self.allies.pop(k, None)
                self.ally_kind.pop(k, None)
                self.count("ally_lapse")
                continue
            if "ally_balance" in self.on:
                sa, sb = ab[0]["strength"], ab[1]["strength"]
                ratio = max(sa, sb) / max(min(sa, sb), 1e-9)
                pb = ALLY_OUTGROW * min(1.0, max(0.0, (ratio - 3) / 3))
                if self.ally_kind.get(k) == "balance" and \
                        threat.get(k, 0.0) <= 0:
                    pb += ALLY_GONE
                if pb > 0 and rng.random() < DT * pb:
                    self.allies.pop(k, None)
                    self.ally_kind.pop(k, None)
                    self.count("ally_outgrown")
        for k in self.adj:
            if k in self.wars or k in self.allies or self.is_vassal_pair(k):
                continue
            ab = self.live(k)
            if not ab:
                continue
            a, b = ab
            La, Lb = a["lin"], b["lin"]
            p = DT * 0.005 * self.accept(La, Lb, TOL_ALLY) * \
                (0.3 + self.ties.get(k, 0.0))
            p_aff = p
            th = threat.get(k, 0.0)
            if th > 0:
                # a common strong neighbour makes allies of the unlike
                p += DT * 0.005 * BALANCE * th * \
                    self.accept(La, Lb, TOL_TRADE)
            r = rng.random()
            if r < p:
                self.allies[k] = self.year
                self.ally_kind[k] = "balance" if r >= p_aff else "affinity"
                cross = a["culture"] != b["culture"]
                self.count(f"ally_{'cross' if cross else 'same'}")
                if r >= p_aff:
                    self.count("ally_balance")
                if cross or len(a["cities"]) + len(b["cities"]) >= 8:
                    self.log("alliance", f"{self.pname(k[0])} and "
                             f"{self.pname(k[1])} ally")
        for k in list(self.allies):
            ab = self.live(k)
            if not ab or self.ties.get(k, 0) < 0.3:
                continue
            a, b = ab
            La, Lb = a["lin"], b["lin"]
            p = DT * 0.0025 * self.accept(La, Lb, TOL_FUSE) * \
                0.5 * (self.state[La] + self.state[Lb])
            if rng.random() < p:
                self.count("fusion" if a["culture"] != b["culture"]
                           else "union")
                self.fuse(a, b)

    def is_vassal_pair(self, k):
        return self.vassal.get(k[0]) == k[1] or self.vassal.get(k[1]) == k[0]

    def threats(self):
        """For each neighbouring pair: 0-1, how far a neighbour of both
        outweighs the two together (1 at three times their strength)."""
        nbrs = {}
        for x, y in self.adj:
            nbrs.setdefault(x, set()).add(y)
            nbrs.setdefault(y, set()).add(x)
        out = {}
        for k in self.adj:
            ab = self.live(k)
            if not ab:
                continue
            common = (nbrs.get(k[0], set()) & nbrs.get(k[1], set()))
            both = ab[0]["strength"] + ab[1]["strength"] + 1
            worst = 0.0
            for c in common:
                C = self.polities.get(c)
                if C is None or C["ended"] is not None:
                    continue
                worst = max(worst, C["strength"] / both)
            if worst > 1:
                out[k] = min(1.0, (worst - 1) / 2)
        return out

    def vassal_politics(self):
        """Vassals throw off weak lords; lords annex small kin vassals."""
        rng = self.rng
        for v, o in list(self.vassal.items()):
            V, O = self.polities.get(v), self.polities.get(o)
            if not V or not O or V["ended"] is not None or \
                    O["ended"] is not None:
                self.vassal.pop(v, None)
                continue
            rel = min(2.0, 2 * V["strength"] / max(O["strength"], 1))
            alien = 1.5 if V["culture"] != O["culture"] else 1.0
            if rng.random() < DT * VASSAL_DEFECT * rel * \
                    (1.5 - O["cohesion"]) * alien:
                del self.vassal[v]
                self.count("vassal_defect")
                k = (min(v, o), max(v, o))
                self.truce[k] = self.tick + 2
                if len(V["cities"]) + len(O["cities"]) >= 6:
                    self.log("vassal", f"{self.pname(v)} throws off "
                             f"{self.pname(o)}")
            elif V["culture"] == O["culture"] and len(V["cities"]) <= 3 \
                    and V["vassal_years"] >= 50 and rng.random() < \
                    DT * 0.004 * (0.5 + self.state[O["lin"]]):
                for c in list(V["cities"]):
                    self.cities[c]["polity"] = o
                    self.cities[c]["owners"].append(o)
                    O["cities"].add(c)
                V["cities"] = set()
                self.count("vassal_annex")
                self.kill_polity(v, f"annexed by its lord {self.pname(o)}")

    def submit(self, v, o):
        """State v becomes the tributary vassal of state o."""
        for key in [k for k in self.allies if v in k]:
            del self.allies[key]
        self.vassal[v] = o
        self.count("vassal_submit_" + ("same" if self.polities[v]["culture"]
                                       == self.polities[o]["culture"]
                                       else "cross"))
        self.polities[v]["vassal_years"] = 0
        V, O = self.polities[v], self.polities[o]
        if len(V["cities"]) + len(O["cities"]) >= 6:
            self.log("vassal", f"{self.pname(v)} submits to "
                     f"{self.pname(o)} and pays tribute")

    def fuse(self, a, b):
        big, small = (a, b) if a["pop"] >= b["pop"] else (b, a)
        for x in small["cities"]:
            self.cities[x]["polity"] = big["id"]
            self.cities[x]["owners"].append(big["id"])
        big["cities"] |= small["cities"]
        big["peoples"] |= small["peoples"]
        small["cities"] = set()
        big["cohesion"] = max(big["cohesion"], small["cohesion"])
        cross = a["culture"] != b["culture"]
        self.blend(big, small)
        if cross:
            self.log("fusion", f"{self.pname(small['id'])} and "
                     f"{self.pname(big['id'])} fuse into one state "
                     f"({self.keys[small['culture']]} + "
                     f"{self.keys[big['culture']]}) under "
                     f"{self.lname(big['lin'])}")
        elif len(big["cities"]) >= 5:
            self.log("union", f"{self.pname(small['id'])} joins "
                     f"{self.pname(big['id'])} by treaty")
        self.kill_polity(small["id"], f"{'fusion' if cross else 'union'} "
                         f"with {self.pname(big['id'])}")

    def blend(self, big, small):
        """A merged state takes one culture: its ruling lineages are
        replaced, inside its territory, by new lineages whose cultural
        traits are the population-weighted average of the two (technology:
        the better of the two). Growth rate, biome fit and body size stay
        with each people."""
        La, Lb = big["lin"], small["lin"]
        if La == Lb:
            return
        ids = (big["id"], small["id"])
        cells = np.nonzero(np.isin(self.cell_pol, ids) &
                           np.isin(self.lin, (La, Lb)))[0]
        wa = self.pop[cells][self.lin[cells] == La].sum() + 1
        wb = self.pop[cells][self.lin[cells] == Lb].sum() + 1
        T = (wa * self.LT[La] + wb * self.LT[Lb]) / (wa + wb)
        X = (wa * self.LX[La] + wb * self.LX[Lb]) / (wa + wb)
        how = "fusion" if big["culture"] != small["culture"] else "union"
        new = {}
        for Lo in (La, Lb):
            c = int(self.Lpeople[Lo])
            if c in new:
                continue
            D = self.new_lineage(c, Lo, how)
            if D == Lo:
                return
            self.LT[D] = T
            self.LX[D] = X
            for t in ("agri", "metal", "sail", "fishing", "admin", "craft"):
                v = getattr(self, t)
                v[D] = max(v[La], v[Lb])
            self.domlv[D] = np.maximum(self.domlv[La], self.domlv[Lb])
            self.guard[D] = self.guard[La] | self.guard[Lb]
            for t in ("bronze", "iron", "steel"):
                v = getattr(self, t)
                v[D] = v[La] or v[Lb]
            self.known[D] = self.known[La] | self.known[Lb]
            self.lack[D] = np.minimum(self.lack[La], self.lack[Lb])
            self.Lseen[D] = self.Lseen[La] | self.Lseen[Lb]
            new[c] = D
        for Lo in (La, Lb):
            self.lin[cells[self.lin[cells] == Lo]] = new[int(self.Lpeople[Lo])]
        big["lin"] = new[int(big["culture"])]
        big["dyn"] = self.year

    def city_dist(self, a, b):
        return float(gc_km(self.W.xyz, a, np.array([b]))[0])

    def roads(self):
        """States build roads along the cheapest routes from capital to
        each of their cities; roads decay, slowly where a state keeps them
        up. Travel costs and the travel graph are then rebuilt."""
        W = self.W
        kept = self.cell_pol >= 0
        life = np.where(kept, ROAD_LIFE, ROAD_LIFE_WILD)
        self.road *= np.exp(-ROAD_EVERY / life)
        for pid, p in self.polities.items():
            if p["ended"] is not None or len(p["cities"]) < 2:
                continue
            cap = p["capital"]
            others = [c for c in p["cities"] if c != cap]
            dist, pred = dijkstra(W.G, indices=cap, return_predecessors=True,
                                  limit=1.5 * self.reach(p))
            add = ROAD_BUILD * self.admin[p["lin"]]
            if "patience" in self.on:
                add *= 0.5 + self.pati[p["lin"]]
            if add <= 0:
                continue
            path = set()
            for c in others:
                x = c
                if pred[x] < 0:
                    continue
                while x >= 0 and x != cap and x not in path:
                    path.add(x)
                    x = pred[x]
            if path:
                idx = np.fromiter(path, int)
                self.road[idx] += add * (1 - self.road[idx])
                self.road[cap] += add * (1 - self.road[cap])
        W.road = 1 - ROAD_EFFECT * self.road
        W.travel()

    def reach(self, P):
        """Administrative reach (cost-km) of a state: its lineage's
        administration, cut when the state is underfed (fiscal) and
        lengthened by a mounted herding population (pastoral)."""
        r = REACH0 + REACH1 * self.admin[P["lin"]]
        if "fiscal" in self.on:
            r *= 0.6 + 0.4 * P["fed"]
        if "pastoral" in self.on:
            r *= 1 + 0.5 * P["herd"]
        nd = self.d_by_pid.get(P["id"], 0)
        if nd:
            # allied dragons carry word and enforce it
            r *= 1 + DRAGON_ADMIN * math.sqrt(nd)
        return r

    def projected(self, P, t):
        reach = self.reach(P)
        if "logistics" in self.on:
            reach *= 1 + LOG_REACH * self.logi(P)
        return P["strength"] * math.exp(-self.city_dist(P["capital"], t) /
                                        (1.5 * reach))

    def logi(self, P):
        """Logistics of a state: administration x (0.5 + statecraft)."""
        L = P["lin"]
        return self.admin[L] * (0.5 + self.state[L])

    def war_chance(self, A, B, k, allies):
        """Chance per tick that A declares war on B (`war_v2`), and its
        motives with the motivated share."""
        La, Lb = A["lin"], B["lin"]
        if not A["cities"] or not B["cities"]:
            return 0.0, None
        R, _ = self.deter(A, B, allies)
        d = self.dom[La] if "dominance" in self.on else 0.5
        crowd = A.get("crowd", 0.5)
        g = {}
        land = 0.0
        if "climate" in self.on:
            land += HUNGER_WAR * (1 - A["fed"])
        if "land_pressure" in self.on:
            land += LP_K * self.pressure(A)
        lv = min(2.0, max(0.5, B.get("kdens", 1) / max(A.get("kdens", 1),
                                                       1e-9)))
        g["land"] = land * lv
        g["prey"] = PREY_K * d * min(1.2, crowd) * \
            min(1.0, max(0.0, (R - 1) / (PREY_R - 1)))
        g["rule"] = d * min(2.0, B["pop"] / max(A["pop"], 1)) \
            if "dominance" in self.on else 0.0
        g["resource"] = self.war_prize(B["id"], A["id"]) * (0.5 + d)
        sim = self.similarity(La, Lb)
        g["enmity"] = ENM_K * (1 - sim) * self.hostile(La)
        if "mission" in self.on:
            g["faith"] = (1 - sim) * (MIS_HOLY * self.pros[La] +
                                      MIS_BACKLASH * self.pros[Lb] *
                                      (1 - self.tol[La]))
        lost = [c for c in B["cities"] if A["id"] in
                self.cities[c]["owners"][:-1]]
        if "life_memory" in self.on:
            # a grievance fades with the generations that remember it
            span = IRR_MEM * self.memf(np.array([La]))[0]
            lost = [c for c in lost if self.year - self.cities[c].get(
                "lost", {}).get(A["id"], -1e9) < span]
        g["irredentism"] = IRR_K * min(1.0, len(lost) / 2)
        m = sum(g.values())
        x = WAR_EPS + m
        opp = 1 + OPP_K * d if B.get("acc_until", -1) > self.year else 1.0
        p = DT * WAR_BASE * A["cohesion"] * (0.5 + self.viol[La]) * \
            (1 - self.ties.get(k, 0.0)) * \
            min(1.0, 2 * R * R / (1 + R * R)) ** DET_K * \
            x / (1 + x / WAR_GAIN_CAP) * opp
        return p, (g, m / x)

    def wars_step(self):
        rng = self.rng
        pairs = self.adj
        allies = {}
        if "war_v2" in self.on:
            for x, y in self.allies:
                allies.setdefault(x, []).append(y)
                allies.setdefault(y, []).append(x)
            # war is costly: levies, lost harvests
            at = {x for kk in self.wars for x in kk}
            if "ally_duty" in self.on:
                at |= {q for w in self.wars.values()
                       for q in w.get("joined", ())}
            if at:
                self.pop[np.isin(self.cell_pol, list(at))] *= 1 - WAR_COST
        if "shuffle" in self.on:
            pairs = sorted(pairs)
            pairs = [pairs[i] for i in rng.permutation(len(pairs))]
        betray = "betrayal" in self.on
        for k in pairs:
            if k in self.wars or (k in self.allies and not betray) or \
                    self.truce.get(k, -1) > self.tick or \
                    self.is_vassal_pair(k):
                continue
            ab = self.live(k)
            if not ab:
                continue
            sides = (k, k[::-1])
            if "shuffle" in self.on and rng.random() < 0.5:
                sides = sides[::-1]
            for att, dfn in sides:
                A, B = self.polities[att], self.polities[dfn]
                La, Lb = A["lin"], B["lin"]
                ratio = A["strength"] / max(B["strength"], 1)
                rf = min(3.0, ratio) ** 1.2 / 2
                xeno = 0.5 + (1 - self.similarity(La, Lb)) * \
                    (1 + 1.5 * self.hostile(La))
                p = DT * 0.012 * self.viol[La] * A["cohesion"] * rf * xeno * \
                    (1 - self.ties.get(k, 0.0)) * self.tolf(La, 0.4)
                motive = None
                if "war_v2" in self.on:
                    p, motive = self.war_chance(A, B, k, allies)
                elif "war_motive" in self.on:
                    # idle wars rarer; wars for something more common
                    gains = dict(resource=self.offer(dfn, att), rule=0.0,
                                 land=0.0)
                    if "dominance" in self.on:
                        gains["rule"] = self.dom[La] * min(
                            2.0, B["pop"] / max(A["pop"], 1))
                    if "climate" in self.on:
                        gains["land"] = HUNGER_WAR * (1 - A["fed"])
                    if "land_pressure" in self.on:
                        # a full land must spread; the strong eye the weak
                        gains["land"] = gains.get("land", 0.0) + \
                            LP_K * self.pressure(A)
                        d = self.dom[La] if "dominance" in self.on else 0.5
                        gains["prey"] = PREY_K * d * min(1.2, A["crowd"]) * \
                            min(1.0, max(0.0, (ratio - 1) / (PREY_R - 1)))
                    if "mission" in self.on:
                        diff = 1 - self.similarity(La, Lb)
                        gains["faith"] = diff * (
                            MIS_HOLY * self.pros[La] + MIS_BACKLASH *
                            self.pros[Lb] * (1 - self.tol[La]))
                    gs = sum(gains.values())
                    gs = gs / (1 + gs / WAR_GAIN_CAP)
                    pm = DT * 0.012 * WAR_GAIN * (0.5 + self.viol[La]) * \
                        A["cohesion"] * rf * (1 - self.ties.get(k, 0.0)) * gs
                    p = WAR_IDLE * p + pm
                    motive = (gains, pm / max(p, 1e-12))
                else:
                    if "dominance" in self.on:
                        # the ambitious go after peoples worth ruling
                        d = self.dom[La]
                        p *= (0.5 + d) * (1 + DOM_PRIZE * d * min(
                            2.0, B["pop"] / max(A["pop"], 1)))
                    if "climate" in self.on:
                        # hungry states go looking for land and grain
                        p *= 1 + HUNGER_WAR * (1 - A["fed"])
                if betray and k in self.allies:
                    p *= BETRAY_K
                if rng.random() < min(p, 0.5):
                    if k in self.allies:
                        self.allies.pop(k, None)
                        self.ally_kind.pop(k, None)
                        self.count("ally_betray")
                        if len(A["cities"]) + len(B["cities"]) >= 8:
                            self.log("alliance", f"{self.pname(att)} "
                                     f"betrays its ally {self.pname(dfn)}")
                    self.count("war_" + ("same" if A["culture"] ==
                                         B["culture"] else "cross"))
                    self.wars[k] = dict(att=att, dfn=dfn, start=self.tick,
                                        caps=0, goal=None, kind="idle",
                                        done=False)
                    if "war_goals" in self.on and motive is not None and \
                            rng.random() < motive[1]:
                        self.set_goal(self.wars[k], A, B, motive[0])
                    self.war_open(self.wars[k], A, B)
                    self.spike(att)
                    self.spike(dfn)
                    if "ally_duty" in self.on:
                        self.call_allies(self.wars[k], A, B)
                    self.ties.pop(k, None)
                    if len(A["cities"]) + len(B["cities"]) >= 8:
                        self.log("war", f"{self.pname(att)} attacks "
                                 f"{self.pname(dfn)}")
                    break
        for k in list(self.wars):
            w = self.wars.get(k)
            if w is None:
                continue
            A, B = self.polities.get(w["att"]), self.polities.get(w["dfn"])
            if not A or not B or A["ended"] is not None or \
                    B["ended"] is not None or not B["cities"] \
                    or not A["cities"]:
                self.war_close(self.wars.pop(k, None), "side ended")
                continue
            if "war_goals" in self.on and w["goal"] is not None and \
                    not w["done"] and w["kind"] in (
                        "land", "prey", "resource", "irredentism") and \
                    w["goal"] in B["cities"]:
                # a weaker defender may cede the goal rather than fight
                g = w["goal"]
                ra = self.projected(A, g) / max(1.4 * self.W.defence[g] *
                                               self.projected(B, g), 1e-9)
                if rng.random() < WAR_CEDE * min(1.0, max(0.0, ra - 1)):
                    w["moved"] = w.get("moved", 0.0) + self.city_fe(g)
                    self.cede(w["att"], w["dfn"], g)
                    self.war_close(self.wars.pop(k, None), "ceded")
                    self.truce[k] = self.tick + 6
                    continue
            # logistics: a well-run state keeps more sieges going at once
            ns = 1 + int(LOG_SIEGE * self.logi(A)) \
                if "logistics" in self.on else 1
            for _ in range(ns):
                if not B["cities"] or B["ended"] is not None or \
                        k not in self.wars:
                    break
                targets = list(B["cities"])
                dists = gc_km(self.W.xyz, A["capital"], np.array(targets))
                t = targets[int(np.argmin(dists))]
                if w.get("goal") in B["cities"] and not w.get("done"):
                    t = w["goal"]
                PA = self.projected(A, t)
                PB = self.projected(B, t)
                # defensive allies send help (not against their own allies)
                for kk in self.allies:
                    if w["dfn"] in kk:
                        q = kk[1] if kk[0] == w["dfn"] else kk[0]
                        Q = self.polities.get(q)
                        if q != w["att"] and Q and Q["ended"] is None and \
                                (min(q, w["att"]), max(q, w["att"])) \
                                not in self.allies and \
                                ("ally_duty" not in self.on or
                                 q in w.get("joined", ())):
                            PB += 0.35 * self.projected(Q, t)
                            w.setdefault("helpers", set()).add(q)
                if "vassals" in self.on:
                    # a lord defends its vassals; vassals send levies to a lord
                    o = self.vassal.get(w["dfn"])
                    if o is not None and o != w["att"] and o in self.polities:
                        PB += 0.5 * self.projected(self.polities[o], t)
                    for v, lord in self.vassal.items():
                        if lord == w["dfn"] and v != w["att"] and \
                                v in self.polities:
                            PB += 0.35 * self.projected(self.polities[v], t)
                PB *= 1.4 * self.W.defence[t] * \
                    (1.25 if t == B["capital"] else 1)
                if "development" in self.on:
                    # walls and works
                    PB *= 1 + DEV_WALL * self.dev(B["lin"])
                if "vassals" in self.on and w["dfn"] not in self.vassal and \
                        PA > VASSAL_RATIO * PB and \
                        rng.random() < 0.5 * (1.2 - B["cohesion"]) * \
                        ((0.5 + self.dom[A["lin"]]) if "dominance" in self.on
                         else 1):
                    # the weaker side submits rather than be besieged
                    self.submit(w["dfn"], w["att"])
                    self.war_close(self.wars.pop(k, None), "submitted")
                    self.truce[k] = self.tick + 6
                    w["submitted"] = True
                    break
                pw = PA ** 2 / (PA ** 2 + PB ** 2 + 1e-9)
                self.pop[t] *= 0.97
                self.shock(t, "siege")
                self.devastate(t, w["dfn"])
                fe = self.city_fe(t)
                cap_t = t == B["capital"]
                won = rng.random() < pw
                w["sieges"] = w.get("sieges", 0) + 1
                self.siege_log.append((
                    self.year, w.get("id", -1), "att", int(t), round(fe),
                    int(cap_t), w["att"], w["dfn"], round(PA, 1),
                    round(PB, 1), round(pw, 4), int(won)))
                if won:
                    w["moved"] = w.get("moved", 0.0) + fe
                    w["caps"] += 1
                    if t == w.get("goal"):
                        w["done"] = True
                        self.count("war_goal_met")
                    self.capture(w["att"], w["dfn"], t)
                else:
                    A["cohesion"] *= 1 - 0.02 * (
                        1.5 - self.logi(A) / 1.5 if "logistics" in self.on
                        else 1)
            if w.get("submitted"):
                continue
            if "two_sided" in self.on and k in self.wars and \
                    A["ended"] is None and B["ended"] is None and \
                    A["cities"] and B["cities"]:
                self.counteroffensive(k, w, A, B)
                if k not in self.wars:
                    continue
            dur = self.tick - w["start"]
            pend = 0.12 + 0.03 * dur
            if "logistics" in self.on:
                # supply lines let a campaign go on
                pend *= 1 - LOG_END * self.logi(A) / 1.5
            if w.get("done"):
                pend = max(pend, WAR_DONE)
            rep = w.get("recaps", 0) > w["caps"]
            if rep:
                pend = max(pend, WAR_DONE)
            if rng.random() < pend or \
                    self.polities[w["dfn"]]["ended"] is not None:
                self.war_close(self.wars.pop(k, None),
                               "defender fell" if self.polities[w["dfn"]][
                                   "ended"] is not None else
                               "goal met" if w.get("done") else
                               "repulsed" if rep else "peace")
                self.truce[k] = self.tick + 6

    def call_allies(self, w, A, B):
        """Defender B's allies are called against attacker A: each joins
        or refuses (and the alliance ends)."""
        b, a = B["id"], A["id"]
        w["joined"] = set()
        for kk in [kk for kk in self.allies if b in kk]:
            q = kk[1] if kk[0] == b else kk[0]
            Q = self.polities.get(q)
            if q == a or not Q or Q["ended"] is not None or \
                    (min(q, a), max(q, a)) in self.allies:
                continue
            j = ALLY_J0 + (1 - ALLY_J0) * min(
                1.0, (Q["strength"] + B["strength"]) /
                max(A["strength"], 1e-9))
            if self.rng.random() < j:
                w["joined"].add(q)
                self.count("ally_join")
            else:
                self.allies.pop(kk, None)
                self.ally_kind.pop(kk, None)
                self.count("ally_refuse")
                if len(Q["cities"]) + len(B["cities"]) >= 8:
                    self.log("alliance", f"{self.pname(q)} refuses the "
                             f"call of {self.pname(b)}; the alliance ends")

    def defence_at(self, D, O, t):
        """What state D brings to bear holding its city t against O:
        its own projected strength, allies not allied to O, lord and
        vassals, times terrain, capital and walls."""
        PD = self.projected(D, t)
        d, o = D["id"], O["id"]
        for kk in self.allies:
            if d in kk:
                q = kk[1] if kk[0] == d else kk[0]
                Q = self.polities.get(q)
                if q != o and Q and Q["ended"] is None and \
                        (min(q, o), max(q, o)) not in self.allies and \
                        "ally_duty" not in self.on:
                    PD += 0.35 * self.projected(Q, t)
        if "vassals" in self.on:
            lord = self.vassal.get(d)
            if lord is not None and lord != o and lord in self.polities:
                PD += 0.5 * self.projected(self.polities[lord], t)
            for v, lo in self.vassal.items():
                if lo == d and v != o and v in self.polities:
                    PD += 0.35 * self.projected(self.polities[v], t)
        PD *= 1.4 * self.W.defence[t] * (1.25 if t == D["capital"] else 1)
        if "development" in self.on:
            PD *= 1 + DEV_WALL * self.dev(D["lin"])
        return PD

    def counteroffensive(self, k, w, A, B):
        """The defender B strikes back at the attacker A (two_sided)."""
        rng = self.rng
        R = B.get("strength", 0.0) / max(A.get("strength", 0.0), 1e-9)
        if rng.random() >= COUNTER_K * R * R / (1 + R * R):
            return
        ns = 1 + int(LOG_SIEGE * self.logi(B)) \
            if "logistics" in self.on else 1
        for _ in range(ns):
            if not A["cities"] or A["ended"] is not None or \
                    k not in self.wars:
                break
            lost = [c for c in A["cities"]
                    if w["dfn"] in self.cities[c]["owners"][:-1]]
            pool = lost or list(A["cities"])
            t = pool[int(np.argmin(gc_km(self.W.xyz, B["capital"],
                                         np.array(pool))))]
            PB = self.projected(B, t)
            PA = self.defence_at(A, B, t)
            pw = PB ** 2 / (PB ** 2 + PA ** 2 + 1e-9)
            self.pop[t] *= 0.97
            self.shock(t, "siege")
            self.devastate(t, w["att"])
            fe = self.city_fe(t)
            won = rng.random() < pw
            w["sieges"] = w.get("sieges", 0) + 1
            self.siege_log.append((
                self.year, w.get("id", -1), "dfn", int(t), round(fe),
                int(t == A["capital"]), w["dfn"], w["att"], round(PB, 1),
                round(PA, 1), round(pw, 4), int(won)))
            if won:
                w["moved_back"] = w.get("moved_back", 0.0) + fe
                w["recaps"] = w.get("recaps", 0) + 1
                self.count("war_counter_capture")
                self.capture(w["dfn"], w["att"], t)
                if k not in self.wars:
                    break
            else:
                B["cohesion"] *= 1 - 0.02 * (
                    1.5 - self.logi(B) / 1.5 if "logistics" in self.on
                    else 1)

    def spike(self, pid):
        """A major event touches state pid (spiky cultural change); at
        most one spike per state per tick."""
        self.pevent[pid] = SPIKE_EVENT

    def city_fe(self, c):
        """Food-equivalents in a city cell (records)."""
        return float(self.pop[c] * self.peat[max(int(self.cul[c]), 0)])

    def war_open(self, w, A, B):
        """Start a war's record (wars.csv; no draws)."""
        w["id"] = len(self.war_log)
        w["rec"] = dict(
            id=w["id"], start=self.year, att=A["id"], dfn=B["id"],
            people_att=self.keys[A["culture"]],
            people_dfn=self.keys[B["culture"]],
            landmass_att=int(self.W.landmass[A["capital"]]),
            landmass_dfn=int(self.W.landmass[B["capital"]]),
            cities_att=len(A["cities"]), cities_dfn=len(B["cities"]),
            strength_att=round(A.get("strength", 0.0), 1),
            strength_dfn=round(B.get("strength", 0.0), 1))
        self.war_log.append(w["rec"])

    def war_close(self, w, why):
        """Finish a war's record."""
        if not w or "rec" not in w:
            return
        r = w["rec"]
        r.update(end=self.year, years=self.year - r["start"], why=why,
                 goal=w.get("kind") if w.get("goal") is not None else "",
                 goal_city=w.get("goal", ""), goal_met=int(bool(w.get("done"))),
                 sieges=w.get("sieges", 0), captures=w.get("caps", 0),
                 recaptures=w.get("recaps", 0),
                 moved=round(w.get("moved", 0.0)),
                 moved_back=round(w.get("moved_back", 0.0)),
                 helpers=" ".join(str(x) for x in
                                  sorted(w.get("helpers", ()))))

    def set_goal(self, w, A, B, gains):
        """The goal of a motivated war: its largest motive."""
        kind = max(gains, key=gains.get)
        goal = B["capital"]
        if kind == "irredentism":
            lost = [c for c in B["cities"] if A["id"] in
                    self.cities[c]["owners"][:-1]]
            if lost:
                goal = lost[0]
        elif kind in ("land", "prey", "enmity"):
            cc = list(B["cities"])
            goal = cc[int(np.argmin(gc_km(self.W.xyz, A["capital"],
                                          np.array(cc))))]
        elif kind == "resource" and "resources" in self.on:
            have = self.passets.get(A["id"], {}).get("kinds", set())
            for c, kd in zip(self.res_cell, self.res_kind):
                cc = int(self.cell_city[c])
                if kd not in have and self.cell_pol[c] == B["id"] and \
                        cc in B["cities"]:
                    goal = cc
                    break
        w["goal"], w["kind"] = int(goal), kind
        self.count(f"war_goal_{kind}")

    def cede(self, att, dfn, t):
        """State dfn hands city t to state att to end a war."""
        A, B = self.polities[att], self.polities[dfn]
        rec = self.cities[t]
        rec.setdefault("lost", {})[dfn] = self.year
        B["cities"].discard(t)
        A["cities"].add(t)
        rec["polity"] = att
        rec["owners"].append(att)
        self.count("war_ceded")
        if len(A["cities"]) + len(B["cities"]) >= 6:
            self.log("war", f"{self.pname(dfn)} cedes the city at "
                     f"{self.place(t)} to {self.pname(att)}")
        if not B["cities"]:
            self.kill_polity(dfn, f"ceded its last city to "
                             f"{self.pname(att)}")
        elif B["capital"] == t:
            self.recapital(B)

    def capture(self, att, dfn, t):
        A, B = self.polities[att], self.polities[dfn]
        ca, La = A["culture"], A["lin"]
        rec = self.cities[t]
        was_cap = B["capital"] == t
        rec.setdefault("lost", {})[dfn] = self.year
        self.count("capture_" + ("same" if rec["culture"] == ca else "cross"))
        self.shock(t, "sack")
        rec["n_sacks"] = rec.get("n_sacks", 0) + 1
        if "improvements" in self.on:
            # the canals and fields of the city and its land are wrecked
            hint = self.cell_city == t
            self.imp[hint] *= 1 - 0.5 * IMP_SACK * self.viol[La]
            self.imp[t] *= 1 - IMP_SACK * self.viol[La]
        if "guarded" in self.on:
            # a conqueror may carry off the secret
            take = self.guard[B["lin"]] & ~self.guard[La]
            for g in np.nonzero(take)[0]:
                if self.rng.random() < GUARD_TAKE * (2 if was_cap else 1):
                    self.guard[La, g] = True
                    self.log("craft", f"{self.pname(att)} takes the secret "
                             f"of {GUARD_NAMES[g]} from {self.pname(dfn)}")
        B["cities"].discard(t)
        A["cities"].add(t)
        rec["polity"] = att
        rec["owners"].append(att)
        spare = 1 - DOM_SPARE * self.dom[La] if "dominance" in self.on \
            else 1
        self.pop[t] *= 1 - (0.1 + 0.4 * self.viol[La]) * spare
        self.mpop[t] *= 1 - (0.1 + 0.4 * self.viol[La]) * spare
        A["cohesion"] = min(1, A["cohesion"] + 0.03)
        if rec["culture"] != ca and self.rng.random() < \
                self.hostile(La) * self.viol[La] * self.tolf(La, 1.0) * \
                ((1 - self.dom[La]) if "dominance" in self.on else 1):
            hint = (self.cell_city == t) & (self.cul == rec["culture"])
            self.pop[hint] *= 0.15
            self.pop[t] *= 0.3
            self.shock(t, "clearance")
            if "improvements" in self.on:
                self.imp[hint] *= 0.5
            if len(A["cities"]) + len(B["cities"]) >= 5:
                self.log("clearance", f"{self.pname(att)} clears "
                         f"{self.keys[rec['culture']]} from the city at "
                         f"{self.place(t)}")
        if "minority" in self.on and rec["culture"] != ca:
            # a garrison and settlers of the conqueror's people stay on
            self.add_minority([t], ca, La, MIN_GARRISON * self.pop[t] *
                              self.peat[rec["culture"]] / self.peat[ca])
        if was_cap:
            B["cohesion"] *= 0.6
            self.spike(dfn)
            if len(B["cities"]) + 1 >= 4:
                self.log("conquest", f"{self.pname(att)} takes the capital "
                         f"of {self.pname(dfn)} at {self.place(t)}")
            if not B["cities"]:
                self.kill_polity(dfn, f"conquered by {self.pname(att)}")
            elif B["culture"] == ca and len(B["cities"]) <= 3:
                for c in list(B["cities"]):
                    self.cities[c]["polity"] = att
                    self.cities[c]["owners"].append(att)
                    A["cities"].add(c)
                B["cities"] = set()
                self.kill_polity(dfn, f"absorbed by {self.pname(att)}")
            elif self.rng.random() < 0.4:
                rest = list(B["cities"])
                B["cities"] = set()
                self.kill_polity(dfn, "shattered after its capital fell")
                for c in rest:
                    Lc = self.lin[c] if self.lin[c] >= 0 else B["lin"]
                    self.cities[c]["polity"] = self.new_polity(
                        Lc, c, 0.5, parent=dfn)
                    self.cities[c]["owners"].append(self.cities[c]["polity"])
            else:
                self.recapital(B)

    def rebellions(self):
        rng = self.rng
        for pid in list(self.polities):
            p = self.polities[pid]
            if p["ended"] is not None or len(p["cities"]) < 2:
                continue
            L = p["lin"]
            reach = self.reach(p)
            cities = [x for x in p["cities"] if x != p["capital"]]
            d = gc_km(self.W.xyz, p["capital"], np.array(cities))
            nc = len(p["cities"])
            for x, dx in zip(cities, d):
                if x not in p["cities"] or self.lin[x] < 0:
                    continue
                Lx = int(self.lin[x])
                alien = 1 + 3 * (1 - self.similarity(L, Lx)) * \
                    (1 - 0.6 * self.tol[L])
                pr = DT * 0.0009 * (dx / reach) ** 2 * \
                    (1.5 - p["cohesion"]) * alien * (1 + 0.2 * math.log(nc))
                if "unrest" in self.on:
                    pr *= 1 + UNREST * p["stress"]
                if p.get("acc_until", -1) > self.year:
                    pr *= 1 + ACC_K
                if rng.random() < pr:
                    self.revolt(pid, x)
                    if "unrest" in self.on:
                        # a revolt thins the elite
                        p["elite"] = max(0.3, 0.8 * p["elite"])
            if "succession" in self.on and nc >= 3 and \
                    self.year >= p["next_succ"] and p["ended"] is None:
                self.succession(pid, p)

    def succession(self, pid, p):
        """A reign ends. Violent peoples and weak administrations risk a
        disputed succession: cohesion falls, and a pretender may take the
        largest provincial city out of the state."""
        if "rulers" in self.on:
            return self.reign_end(pid, p)
        rng = self.rng
        p["next_succ"] = self.year + max(DT, rng.exponential(SUCC_GEN))
        L = p["lin"]
        q = SUCC_P * (1.3 - 0.6 * self.state[L])
        if "costs" in self.on:
            q *= 0.5 + self.viol[L]
        if rng.random() >= q:
            return
        self.disputed(pid, p)

    def reign_end(self, pid, p):
        """A ruler dies (`rulers`): inheritance, the new ruler's testing
        time, alliances and vassals up for renewal, union of crowns."""
        rng = self.rng
        L = p["lin"]
        exp_reign = SUCC_GEN * self.plife[self.Lpeople[L]]
        r = p.get("ruler") or dict(id=-1, start=p["founded"])
        reign = self.year - r["start"]
        p["next_succ"] = self.year + max(DT, rng.exponential(exp_reign))
        nc = len(p["cities"])
        outcome = "peaceful"
        if nc >= 4 and rng.random() < self.Lpart[L] * min(1.0, nc / PART_N):
            outcome = f"partition {self.partition(pid, p)}"
        else:
            q = SUCC_P * (1.3 - 0.6 * self.state[L])
            if "costs" in self.on:
                q *= 0.5 + self.viol[L]
            q *= 1 + LONG_K * max(0.0, reign / exp_reign - 1)
            if rng.random() < q:
                n0 = len(p["cities"])
                self.disputed(pid, p)
                outcome = "disputed" if len(p["cities"]) == n0 \
                    else "pretender"
        p["acc_until"] = self.year + ACC_YEARS
        for kk in [kk for kk in self.allies if pid in kk]:
            if rng.random() < ALLY_RENEW * (1 - self.ties.get(kk, 0.0)):
                self.allies.pop(kk, None)
                self.ally_kind.pop(kk, None)
                self.count("ally_lapse_death")
        for v in [v for v, o in self.vassal.items() if o == pid]:
            V = self.polities.get(v)
            alien = 1.5 if V and V["culture"] != p["culture"] else 1.0
            if rng.random() < VASSAL_ACC * alien:
                del self.vassal[v]
                self.count("vassal_defect")
                self.truce[(min(v, pid), max(v, pid))] = self.tick + 2
        if p["ended"] is None and p["cities"]:
            for kk in [kk for kk in self.allies if pid in kk]:
                ab = self.live(kk)
                if not ab:
                    continue
                if rng.random() < UNION_CROWN * self.accept(
                        ab[0]["lin"], ab[1]["lin"], TOL_FUSE):
                    self.count("union_crowns")
                    other = ab[1] if ab[0]["id"] == pid else ab[0]
                    if nc + len(other["cities"]) >= 6:
                        self.log("succession", f"union of crowns: "
                                 f"{self.pname(pid)} and "
                                 f"{self.pname(other['id'])} pass to one "
                                 "ruler")
                    outcome += " union"
                    self.fuse(ab[0], ab[1])
                    break
        self.ruler_log.append((r["id"], pid, self.keys[p["culture"]],
                               r["start"], self.year, reign, nc, outcome))
        self.n_ruler += 1
        p["ruler"] = dict(id=self.n_ruler, start=self.year)

    def partition(self, pid, p):
        """The realm is divided among heirs: 2-4 seats (the capital and the
        largest cities far from the others); every city goes to the
        nearest seat; each seat but the capital becomes a state of the
        same lineage. Returns the number of heirs."""
        rng = self.rng
        cc = list(p["cities"])
        nh = int(min(2 + rng.integers(0, 3), max(2, len(cc) // 2)))
        seats = [p["capital"]]
        xyz = self.W.xyz
        while len(seats) < nh:
            rest = [c for c in cc if c not in seats]
            if not rest:
                break
            d = np.min([gc_km(xyz, s, np.array(rest)) for s in seats], 0)
            score = d * np.sqrt(np.maximum(self.pop[rest], 1))
            seats.append(rest[int(np.argmax(score))])
        D = np.array([gc_km(xyz, s, np.array(cc)) for s in seats])
        near = D.argmin(0)
        heirs = [pid]
        for i, s in enumerate(seats[1:], 1):
            group = [c for c, j in zip(cc, near) if j == i]
            new = self.new_polity(p["lin"], s, p["cohesion"], parent=pid)
            for c in group:
                p["cities"].discard(c)
                self.cities[c]["polity"] = new
                self.cities[c]["owners"].append(new)
                self.cities[c].setdefault("lost", {})[pid] = self.year
                self.polities[new]["cities"].add(c)
            heirs.append(new)
        for a in heirs:
            self.spike(a)
            for b in heirs:
                if a < b:
                    self.truce[(a, b)] = self.tick + 4
        self.count("partition")
        if len(cc) >= 6:
            self.log("succession", f"partition: {self.pname(pid)} is "
                     f"divided among {len(heirs)} heirs (" + ", ".join(
                         f"{self.pname(h)} {len(self.polities[h]['cities'])}"
                         for h in heirs) + " cities)")
        return len(heirs)

    def disputed(self, pid, p):
        """A disputed succession."""
        rng = self.rng
        p["cohesion"] *= 0.8
        p["elite"] = max(0.3, 0.85 * p["elite"])
        p["dyn"] = self.year
        self.spike(pid)
        civil = rng.random() < min(0.9, 0.3 + 0.3 * p["stress"])
        rest = [x for x in p["cities"] if x != p["capital"] and
                self.lin[x] >= 0]
        if civil and rest:
            x = max(rest, key=lambda c: self.pop[c])
            if len(p["cities"]) >= 5:
                self.log("succession", f"disputed succession in "
                         f"{self.pname(pid)}: a pretender holds "
                         f"{self.place(x)}")
            self._pretender = True
            self.revolt(pid, x)
            self._pretender = False
        elif len(p["cities"]) >= 8:
            self.log("succession", f"disputed succession weakens "
                     f"{self.pname(pid)}")

    def revolt(self, pid, x):
        """A province breaks away. Rebels of the ruling lineage found a
        daughter lineage (they drift apart from here); rebels of another
        lineage or people restore their own."""
        p = self.polities[pid]
        self.n_revolts += 1
        cx, Lx = self.cities[x]["culture"], int(self.lin[x])
        same = Lx == p["lin"]
        Lnew = self.new_lineage(cx, Lx, "secession", sd=self.drift) \
            if same else Lx
        new = self.new_polity(Lnew, x, 0.75, parent=pid)
        self.cities[x].setdefault("lost", {})[pid] = self.year
        p["cities"].discard(x)
        self.cities[x]["polity"] = new
        self.cities[x]["owners"].append(new)
        group = [x]
        others = [y for y in p["cities"] if y != p["capital"] and
                  self.cities[y]["culture"] == cx]
        if others:
            dn = gc_km(self.W.xyz, x, np.array(others))
            dc = gc_km(self.W.xyz, p["capital"], np.array(others))
            for y, a, b in zip(others, dn, dc):
                if a < 400 and a < b and self.rng.random() < 0.6:
                    self.cities[y].setdefault("lost", {})[pid] = self.year
                    p["cities"].discard(y)
                    self.cities[y]["polity"] = new
                    self.cities[y]["owners"].append(new)
                    self.polities[new]["cities"].add(y)
                    group.append(y)
        if same:
            hint = np.isin(self.cell_city, group) & (self.lin == Lx)
            self.lin[hint] = Lnew
        taken = len(group)
        kind = ("ethnic revolt" if cx != p["culture"] else
                "secession" if same else "kin revolt")
        key = "pretender" if self._pretender else kind.split()[0]
        share = taken / max(taken + len(p["cities"]), 1)
        if share >= SPIKE_REVOLT:
            self.spike(pid)
            self.spike(new)
        if "revolt_exp" in self.on:
            # weighted by the share of the state's cities lost this tick
            m = self.cell_pol == pid
            self.revolted[m] = np.minimum(1.0, self.revolted[m] + share)
            for c in group:
                hc = self.cell_city == c
                self.revolted[hc] = np.minimum(1.0, self.revolted[hc] + share)
        self.revolt_log.append((
            self.year, pid, new, self.keys[p["culture"]], self.keys[cx], key,
            taken, len(p["cities"]), int(self.W.landmass[x]),
            round(float(self.W.lon[x]), 2), round(float(self.W.lat[x]), 2)))
        self.count(f"revolt_{key}")
        self.count(f"revolt_{key}_cities", taken)
        if taken >= 3 or (taken >= 2 and len(p["cities"]) >= 6):
            extra = f", new lineage {self.lname(Lnew)}" if same else ""
            self.log("revolt", f"{kind}: {self.pname(new)} breaks from "
                     f"{self.pname(pid)} at {self.place(x)} "
                     f"with {taken} cities{extra}")
        p["cohesion"] *= 0.9

    # ---- technology
    def technology(self):
        """Per-lineage invention, plus borrowing from the most advanced
        lineage each one touches (borders, trade, rule)."""
        W, nL = self.W, self.nL
        occ = self.lin >= 0
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        self.Lpeak[:nL] = np.maximum(self.Lpeak[:nL], Lpop)
        dead = (Lpop <= 0) & (self.Lended[:nL] < 0) & (self.Lpeak[:nL] > 0)
        self.Lended[:nL][dead] = self.year
        A = np.nonzero(Lpop > 0)[0]
        if not len(A):
            return
        nA = len(A)
        amap = -np.ones(nL, int)
        amap[A] = np.arange(nA)
        ncity = np.zeros(nL)
        for cell in self.cities:
            if self.lin[cell] >= 0:
                ncity[self.lin[cell]] += 1
        coastal = np.bincount(self.lin[occ], weights=(self.pop * W.coastal)
                              [occ], minlength=nL) / np.maximum(Lpop, 1)
        waterside = np.bincount(self.lin[occ], weights=(self.pop * W.water)
                                [occ], minlength=nL) / np.maximum(Lpop, 1)
        # contact between lineages
        M = np.zeros((nA, nA))
        la, lb = self.lin[W.E1], self.lin[W.E2]
        m = (la >= 0) & (lb >= 0) & (la != lb)
        np.add.at(M, (amap[la[m]], amap[lb[m]]), 1)
        Mb = M.copy()
        pl = np.full(self.next_pid, -1)
        for pid, p in self.polities.items():
            if p["ended"] is None:
                pl[pid] = p["lin"]
        rl = np.where(self.cell_pol >= 0, pl[np.maximum(self.cell_pol, 0)],
                      -1)
        m = occ & (rl >= 0) & (rl != self.lin)
        m &= amap[np.maximum(rl, 0)] >= 0
        np.add.at(M, (amap[self.lin[m]], amap[rl[m]]), 0.5)
        if "minority" in self.on:
            # a minority lives among its hosts
            m = occ & (self.mlin >= 0) & (self.mlin != self.lin)
            m &= amap[np.maximum(self.mlin, 0)] >= 0
            np.add.at(M, (amap[self.lin[m]], amap[self.mlin[m]]), 2.0)
            np.add.at(Mb, (amap[self.lin[m]], amap[self.mlin[m]]), 2.0)
        M = M + M.T
        Mb = Mb + Mb.T
        for (x, y), t in self.ties.items():
            a, b = pl[x], pl[y]
            if a >= 0 and b >= 0 and a != b and amap[a] >= 0 and amap[b] >= 0:
                M[amap[a], amap[b]] += 30 * t
                M[amap[b], amap[a]] += 30 * t
        C = np.clip(M / 60, 0, 1)
        Cb = np.clip(Mb / 60, 0, 1)
        Ct = np.clip((M - Mb) / 60, 0, 1)
        inn = self.innov[A]
        # closed, cohesive societies borrow less from outsiders
        openness = 1 - COST_COH * self.coh[A] if "costs" in self.on else 1

        def diffuse(v, rate):
            gap = np.clip(v[None, :] - v[:, None], 0, None)
            return rate * (C * gap).max(1) * (0.3 + inn) * openness

        LpopF = Lpop * self.peat[np.maximum(self.Lpeople[:nL], 0)] \
            if "food_units" in self.on else Lpop
        g = 0.5 + 0.5 * np.clip(np.log10(1 + LpopF[A]) / 6, 0, 1)
        F = 1.0
        if "scale" in self.on:
            # big, connected, varied realms invent faster
            F = self.scale_factor(A, LpopF, occ)
            g = F
        ag, mt, sl, ad = (self.agri[A], self.metal[A], self.sail[A],
                          self.admin[A])
        nc = ncity[A]
        ag2 = ag + DT * (0.0009 * inn * g * (1 - ag) + diffuse(ag, 0.004))
        mt2 = mt + DT * (0.0005 * F * inn ** 2 * (ag > 0.5) *
                         (1 + np.log1p(nc) / 3) + diffuse(mt, 0.0008))
        if "fishing" in self.on:
            # fishing grows with innovation where there is water to fish
            fs = self.fishing[A]
            fs2 = fs + DT * (0.001 * F * inn * (waterside[A] + 0.05) *
                             (1 - fs) +
                             diffuse(fs, 0.002))
            self.fishing[A] = np.clip(fs2, 0, 1)
        sea = (inn * (0.5 + self.fishing[A]) if "fishing" in self.on
               else inn) if "dispersal" in self.on else self.seaf[A]
        sl2 = sl + DT * (0.0012 * F * sea * (coastal[A] + 0.1) *
                         (1 - sl) + diffuse(sl, 0.001))
        ex = self.exposure(occ, Lpop, A) if "experience" in self.on else None
        Fad = F * (1 + EXP_ADMIN * ex[0]) if ex is not None else F
        ad2 = ad + DT * (0.0008 * Fad * self.state[A] * (1 - ad) *
                         np.sqrt(np.clip(nc / 5, 0, 1)) + diffuse(ad, 0.002))
        sup = "supply" in self.on
        kb, ki = (self.known[A, 0], self.known[A, 1]) if sup else \
            (self.bronze[A], self.iron[A])
        cap = np.where(~kb, 1.2, np.where(~ki, 2.0, 3.5))
        if sup:
            # outside any state, offices and workshops lapse
            ruled = np.bincount(self.lin[occ], weights=(self.pop * (
                self.cell_pol >= 0))[occ], minlength=nL)[A]
            idle = 1 - ruled / np.maximum(Lpop[A], 1)
            ad2 = ad2 - DT * DECAY_ADMIN * idle
            mt2 = mt2 - DT * DECAY_METAL * idle
            # farming, fishing and sailing lapse where they are not used
            Kocc = np.maximum(self.Kf(self.lin[occ], np.nonzero(occ)[0]),
                              1e-3)
            unused = self.herding[occ] | (self.pop[occ] < AGRI_THIN * Kocc)
            nofarm = (np.bincount(self.lin[occ], weights=self.pop[occ] *
                                  unused, minlength=nL) /
                      np.maximum(Lpop, 1))[A]
            ag2 = ag2 - DT * DECAY_AGRI * nofarm * np.maximum(ag2 - 0.25, 0)
            sl2 = sl2 - DT * DECAY_SAIL * (1 - coastal[A]) * \
                np.maximum(sl2 - SAIL_START, 0)
            if "fishing" in self.on:
                fs2 = self.fishing[A]
                self.fishing[A] = fs2 - DT * DECAY_FISH * \
                    (1 - waterside[A]) * np.maximum(fs2 - FISH_START, 0)
        self.agri[A] = np.clip(ag2, 0, 1)
        self.metal[A] = np.minimum(mt2, cap)
        if sup:
            self.metal[A] = np.maximum(self.metal[A], 0)
            ad2 = np.clip(ad2, 0, 1)
        self.sail[A], self.admin[A] = sl2, ad2
        if "craft" in self.on:
            # settled specialists make prized goods
            cr = self.craft[A]
            cr2 = cr + DT * (CRAFT_INV * F * self.crafts[A] *
                             (0.5 + self.pati[A]) *
                             np.sqrt(np.clip(nc / 3, 0, 1)) * (1 - cr) +
                             diffuse(cr, CRAFT_BORROW))
            if sup:
                cr2 = cr2 - DT * CRAFT_DECAY * idle * cr2
            self.craft[A] = np.clip(cr2, 0, 1)
        if "domestication" in self.on:
            self.domesticate(A, occ, Lpop, inn * F, diffuse)
        if "guarded" in self.on:
            self.guarded(A, C, nc)
        # ore access: own land near ores, or close contact with a holder
        has = {}
        for nm, d in (("cu", W.d_cu), ("sn", W.d_sn), ("fe", W.d_fe)):
            near = occ & (d < 120) & \
                (self.pop * self.peat[np.maximum(self.cul, 0)] > 1000)
            h = (np.bincount(self.lin[near], minlength=nL) > 0)[A]
            has[nm] = h | ((C * h[None, :]).max(1) > 0.4)
            if "ore_trade" in self.on and nm in ("cu", "sn"):
                has[nm] = has[nm] | self.ore_by_trade(near, nL)[A]
        self.ore_has[A] = np.stack([has["cu"], has["sn"], has["fe"]], 1)
        # a stage needs the lineage's own metallurgy plus the ore in hand
        if sup:
            # ...and stays in use only while the ore (and, for steel, the
            # cities) remain; knowledge is kept, use lapses after a grace
            mtA = self.metal[A]
            okb = (mtA >= 1.0) & has["cu"] & has["sn"]
            oki = (mtA >= 1.8) & has["fe"] & (self.known[A, 0] | okb)
            oks = oki & (mtA >= 2.6) & (nc >= 6)
            stages = []
            for s, (arr, ok) in enumerate(((self.bronze, okb),
                                           (self.iron, oki),
                                           (self.steel, oks))):
                self.known[A, s] |= ok
                self.lack[A, s] = np.where(ok, 0, self.lack[A, s] + 1)
                stages.append(ok | (arr[A] & (self.lack[A, s] <= SUPPLY_GRACE)))
            br, fe, st = stages
            lost = self.bronze[A] & ~br & (Lpop[A] > 3e5)
            for L in A[lost]:
                self.log("tech", f"{self.lname(L)} can no longer get tin and "
                         "copper: bronze goes out of use")
        else:
            br = self.bronze[A] | ((self.metal[A] >= 1.0) & has["cu"] &
                                   has["sn"])
            fe = self.iron[A] | (br & (self.metal[A] >= 1.8) & has["fe"])
            st = self.steel[A] | (fe & (self.metal[A] >= 2.6) & (nc >= 6))
        for arr, new, nm in ((self.bronze, br, "cast bronze"),
                             (self.iron, fe, "work iron"),
                             (self.steel, st, "forge steel")):
            for L in A[new & ~arr[A]]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")
            arr[A] = new
        if "acculturation" in self.on:
            # customs drift toward those of contacts, weighted by contact and
            # prestige (sqrt population), faster in tolerant lineages
            sk = [TI[t] for t in SKILLS]
            # under dispersal seafaring does nothing and is left alone
            frz = [TI["seafaring"]] if "dispersal" in self.on else []
            churn = np.zeros(nL)
            Wm = C * np.sqrt(LpopF[A])[None, :]
            if "acc_cross" in self.on:
                pa = self.Lpeople[A]
                xp = np.where(pa[:, None] == pa[None, :], 1.0, ACC_CROSS)
                # the pull's strength falls with the foreign share of
                # contact, not only its direction
                xs = (Wm * xp).sum(1) / np.maximum(Wm.sum(1), 1e-12)
                Wm = Wm * xp
            if "craft" in self.on:
                Wm = Wm * (1 + self.craft[A])[None, :]
            if "proselytism" in self.on:
                Wm = Wm * (0.5 + self.pros[A])[None, :]
            np.fill_diagonal(Wm, 0)
            tot = Wm.sum(1)
            has_c = tot > 0
            nT = len(TRAITS)
            if "mission" in self.on:
                # proselytizers push their neighbours; trade and rule carry
                # customs both ways; like cultures move each other most
                has_c[:] = False
                S = self.sim_matrix(A)
                pj = self.pros[A]
                Sb = S + MIS_REACH * pj[None, :] * (1 - S)
                Wx = MIS_BORDER * Cb * pj[None, :] * Sb + \
                    MIS_TRADE * Ct * self.tol[A][:, None] * S
                if "acc_cross" in self.on:
                    Wx = Wx * xp
                np.fill_diagonal(Wx, 0)
                T = np.hstack([self.LT[A], self.LX[A]])
                norm = np.maximum(1, (Cb + Ct).sum(1) - np.diag(Cb + Ct))
                dT = DT * (Wx @ T - Wx.sum(1)[:, None] * T) / norm[:, None]
                if "conformity" in self.on:
                    dT = dT * (1.5 - self.conf[A])[:, None]
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                dT[:, frz] = 0
                self.LT[A] += dT[:, :nT]
                self.LX[A] += dT[:, nT:]
                churn[A] += np.abs(dT).sum(1)
            if has_c.any():
                T = np.hstack([self.LT[A], self.LX[A]])
                target = (Wm @ T) / np.maximum(tot, 1e-9)[:, None]
                open_ = self.tol[A]
                if "proselytism" in self.on:
                    open_ = open_ + PROS_PUSH * (Wm @ self.pros[A]) / \
                        np.maximum(tot, 1e-9)
                rate = DT * ACC * open_ * np.minimum(1, C.sum(1))
                if "acc_cross" in self.on:
                    rate = rate * xs
                if "conformity" in self.on:
                    rate = rate * (1.5 - self.conf[A])
                dT = rate[:, None] * (target - T)
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                dT[:, frz] = 0
                self.LT[A[has_c]] += dT[has_c, :nT]
                self.LX[A[has_c]] += dT[has_c, nT:]
            # under foreign rule, customs move fast toward the ruler's
            fr = occ & (rl >= 0) & (self.cul != self.Lpeople[np.maximum(rl, 0)])
            if "acc_cross" in self.on:
                key = np.where(fr, self.Lpeople[np.maximum(rl, 0)] * 1000 +
                               np.maximum(self.cul, 0), -1)
                new = fr & (key != self.rule_key)
                self.rule_since[new] = self.year
                self.rule_key = key
            if fr.any():
                sub, ru, w = self.lin[fr], rl[fr], self.pop[fr]
                if "acc_cross" in self.on:
                    g = (self.year - self.rule_since[fr]) / (
                        GEN_LEN * self.plife[self.cul[fr]])
                    w = w * (ACC_RULE0 + (1 - ACC_RULE0) /
                             (1 + np.exp(-(g - ACC_GENS) / 0.5)))
                wsum = np.bincount(sub, weights=w, minlength=nL)
                tg = np.zeros((nL, nT + len(XTRAITS)))
                np.add.at(tg, sub, w[:, None] *
                          np.hstack([self.LT[ru], self.LX[ru]]))
                ok = wsum[A] > 0
                Ak = A[ok]
                tgt = tg[Ak] / wsum[Ak][:, None]
                rc = DT * ACC_CONQ * wsum[Ak] / np.maximum(Lpop[Ak], 1)
                if "conformity" in self.on:
                    rc = rc * (1.5 - self.conf[Ak])
                dT = rc[:, None] * (tgt - np.hstack([self.LT[Ak],
                                                     self.LX[Ak]]))
                dT[:, sk] = np.where(dT[:, sk] < 0, SKILL_DOWN, 1) * dT[:, sk]
                dT[:, frz] = 0
                self.LT[Ak] += dT[:, :nT]
                self.LX[Ak] += dT[:, nT:]
                churn[Ak] += np.abs(dT).sum(1)
            if "mission" in self.on:
                a = np.minimum(1.0, DT / (MIS_MEM * self.memf(A)))
                self.Lchurn[A] += a * (100 * churn[A] / DT - self.Lchurn[A])
        if ex is not None:
            self.experience(A, *ex)
        for nm, v, lv in (("adopt farming", self.agri, 0.5),
                          ("adopt open-sea sailing", self.sail, 0.4),
                          ("adopt net and weir fishing", self.fishing, 0.5),
                          ("adopt bureaucracy", self.admin, 0.5)):
            for L in A[v[A] >= lv]:
                c = self.Lpeople[L]
                self.first((nm, c), "tech", f"{self.keys[c]} {nm} "
                           f"(first: {self.lname(L)})")

    def exposure(self, occ, Lpop, A):
        """Per living lineage: share of its people in states at war, the
        trade volume of the states they live in, and their hardship."""
        nL = self.nL
        atwar = np.zeros(self.next_pid, bool)
        vol = np.zeros(self.next_pid)
        for k in self.wars:
            atwar[list(k)] = True
        if "ally_duty" in self.on:
            for w in self.wars.values():
                for q in w.get("joined", ()):
                    if q < len(atwar):
                        atwar[q] = True
        if "trade_mean" in self.on:
            tsum = np.zeros(self.next_pid)
            nn = np.zeros(self.next_pid)
            for x, y in self.adj:
                t = self.ties.get((x, y), 0.0)
                tsum[x] += t
                tsum[y] += t
                nn[x] += 1
                nn[y] += 1
            vol = np.minimum(1.5, TRADE_MEAN_K * tsum / np.maximum(nn, 1))
        else:
            for pid, p in self.polities.items():
                if p["ended"] is None:
                    vol[pid] = min(1.5, p["trade"])
        pol = np.maximum(self.cell_pol, 0)
        inst = occ & (self.cell_pol >= 0)
        w = self.pop * inst
        L = self.lin[occ]
        den = np.maximum(Lpop, 1)
        s = np.bincount(L, weights=(w * atwar[pol])[occ], minlength=nL) / den
        v = np.bincount(L, weights=(w * vol[pol])[occ], minlength=nL) / den
        q = np.bincount(L, weights=(self.pop * self.hard)[occ],
                        minlength=nL) / den
        r = np.bincount(L, weights=(self.pop * self.raided)[occ],
                        minlength=nL) / den
        u = np.bincount(L, weights=(self.pop * self.revolted)[occ],
                        minlength=nL) / den
        ev = np.zeros(self.next_pid)
        for pid, y in self.pevent.items():
            if pid < len(ev):
                ev[pid] = y
        yev = np.bincount(L, weights=(w * ev[pol])[occ], minlength=nL) / den
        self.hard[:] = 0
        self.raided[:] = 0
        self.revolted[:] = 0
        self.pevent = {}
        return s[A], v[A], q[A], r[A], u[A], yev[A]

    def memf(self, A):
        """Memory span factor of lineages A: lifespan x (0.5 + patience)
        with `life_memory`, else 1."""
        if "life_memory" not in self.on:
            return 1.0
        return self.plife[self.Lpeople[A]] * (0.5 + self.pati[A])

    def experience(self, A, s, v, q, r, u=0.0, yev=0.0):
        """Traits shaped by what a lineage lives through."""
        a = np.minimum(1.0, DT / (EXP_MEM * self.memf(A)))
        self.Lwarm[A] += a * (s - self.Lwarm[A])
        self.Lhardm[A] += a * (q - self.Lhardm[A])
        self.Ltradem[A] += a * (v - self.Ltradem[A])
        self.Lraidm[A] += a * (r - self.Lraidm[A])
        m, h = self.Lwarm[A], self.Lhardm[A]
        v1 = np.minimum(v, 1)
        safe = (1 - m) * (1 - h)
        nT = len(TRAITS)
        mult = 1.0
        if "spiky" in self.on:
            gen = GEN_LEN * self.plife[self.Lpeople[A]]
            nxt = self.Lgen_next[A]
            unset = nxt <= 0
            nxt[unset] = self.year + ((A[unset] * 7919) % 1000) / 1000 * \
                gen[unset]
            due = self.year >= nxt
            nxt[due] += gen[due]
            self.Lgen_next[A] = nxt
            mult = EXP_BG + (GEN_YEARS * due + yev) / DT
        rv = "revolt_exp" in self.on
        tp = "trait_path" in self.on

        def push(arr, col, up, down, piv=PATH_PIVOT):
            x = arr[A]
            if tp:
                g = 1 / (1 + np.exp(-(x - piv) / PATH_PW))
                up = up * 2 * (PATH_MIN + (1 - PATH_MIN) * g) / (1 + PATH_MIN)
                down = down * 2 * (PATH_MIN + (1 - PATH_MIN) * (1 - g)) / \
                    (1 + PATH_MIN)
            d = DT * mult * (up * (1 - x) - down * x)
            if "spiky" in self.on:
                # no overshoot past the balance point
                d = d / np.maximum(1, DT * mult * (up + down) / 0.5)
            new = np.clip(x + d, 0.01, 0.99)
            self.Lexp[A, col] += new - x
            arr[A] = new
        if "tol_path" in self.on:
            phi = PHI_MIN + (1 - PHI_MIN) / (
                1 + np.exp(-(self.tol[A] - TOL_PIVOT) / TOL_PW))
            push(self.tol, TI["tolerance"], EXP_TRADE * v * phi,
                 EXP_WAR * s + EXP_HARD * q + EXP_RAID / 2 * r +
                 EXP_TRADE * v * (1 - phi) + rv * EXP_REVOLT / 2 * u,
                 TOL_PIVOT)
        else:
            push(self.tol, TI["tolerance"], EXP_TRADE * v,
                 EXP_WAR * s + EXP_HARD * q + EXP_RAID / 2 * r +
                 rv * EXP_REVOLT / 2 * u, TOL_PIVOT)
        push(self.trade, TI["trade"], EXP_TRADE / 2 * v,
             EXP_UNUSED * (1 - v1))
        # wars and frontier raids harden; trade and peace soften
        push(self.viol, TI["violence"], EXP_WAR * s + EXP_RAID * r +
             rv * EXP_REVOLT * u, EXP_TRADE_V * v + EXP_PEACE * (1 - m))
        if rv:
            push(self.sep, TI["separation"], EXP_REVOLT / 2 * u,
                 EXP_CALM * (1 - m))
        # war binds a people; wealth and long peace loosen the bond
        push(self.coh, TI["cohesion"], EXP_WAR / 2 * s,
             EXP_LUX * v1 + EXP_CALM * (1 - m))
        push(self.hier, nT + XTRAITS.index("hierarchy"), EXP_WAR / 2 * s,
             EXP_CALM * (1 - m))
        # threat tightens norms; trade and safety loosen them
        push(self.conf, nT + XTRAITS.index("conformity"),
             EXP_WAR / 2 * s + EXP_HARD * q + rv * EXP_REVOLT / 2 * u,
             EXP_TRADE / 2 * v1 + EXP_LOOSE * safe)

    def scale_factor(self, A, LpopF, occ):
        """Invention multiplier F of living lineages A (see SCALE_*)."""
        W, nL = self.W, self.nL
        pool = LpopF[:nL].astype(float).copy()
        fe = self.pop * self.peat[np.maximum(self.cul, 0)]
        m = occ & (self.cell_pol >= 0)
        spop = np.bincount(self.cell_pol[m], weights=fe[m],
                           minlength=self.next_pid)
        nb = len(BIOMES)
        sb = np.zeros((self.next_pid, nb))
        np.add.at(sb, (self.cell_pol[m], W.biome[m]), 1)
        lb = np.zeros((nL, nb))
        np.add.at(lb, (self.lin[occ], W.biome[occ]), 1)
        D = (lb / np.maximum(lb.sum(1, keepdims=True), 1) >= 0.05).sum(1)
        D = D.astype(float)
        for pid, p in self.polities.items():
            L = p["lin"]
            if p["ended"] is not None or L >= nL:
                continue
            # the state's people (its ruling lineage's own among them)
            pool[L] = max(pool[L], spop[pid])
            sh = sb[pid] / max(sb[pid].sum(), 1)
            D[L] = max(D[L], float((sh >= 0.05).sum()) +
                       p.get("n_kinds", 0))
        for (x, y), t in self.ties.items():
            for a, b in ((x, y), (y, x)):
                P = self.polities.get(a)
                if P is not None and P["ended"] is None and P["lin"] < nL:
                    pool[P["lin"]] += SCALE_TIE * t * spop[b]
        for L in A:
            D[L] += len(self.Lseen.get(int(L), ())) - 1
        F = np.clip((np.maximum(pool[A], 0) / SCALE_P0) ** SCALE_EXP,
                    SCALE_MIN, SCALE_MAX)
        return F * (1 + SCALE_DIV * np.maximum(D[A] - 1, 0))

    def domesticate(self, A, occ, Lpop, inn, diffuse):
        """Crop and animal packages: developed near their hearths,
        borrowed elsewhere, most readily into their own biome."""
        W, nL = self.W, self.nL
        nh = len(self.h_cell)
        lv = self.domlv[A]
        inv = np.zeros_like(lv)
        for k in range(nh):
            c = self.h_near[k]
            c = c[(self.lin[c] >= 0) & (self.pop[c] * self.peat[
                np.maximum(self.cul[c], 0)] > 300)]
            if len(c):
                near = np.zeros(nL, bool)
                near[self.lin[c]] = True
                inv[:, k] = DOM_INV * inn * near[A]
        bs = np.zeros((nL, len(BIOMES)))
        np.add.at(bs, (self.lin[occ], W.biome[occ]), self.pop[occ])
        bs = bs[A] / np.maximum(Lpop[A], 1)[:, None]
        suit = 0.3 + 0.7 * bs[:, self.h_biome]
        bor = np.stack([diffuse(lv[:, k], DOM_BORROW) for k in range(nh)], 1)
        new = np.clip(lv + DT * (inv * (1 - lv) + bor * suit), 0, 1)
        self.domlv[A] = new
        for k in range(nh):
            got = (new[:, k] >= 0.5) & (lv[:, k] < 0.5)
            for L in A[got][:1]:
                self.first(("domesticate", k), "tech",
                           f"{self.lname(L)} domesticates {self.h_name[k]}"
                           f" (hearth at {self.place(self.h_cell[k])})")

    def guarded(self, A, C, nc):
        """Guarded techniques: invented by skilled rulers of large states,
        leaking slowly to contacts."""
        rng = self.rng
        G = self.guard[A]
        if G.any():
            hw = (1.5 - self.coh[A]) * (1.5 - self.conf[A])
            P = DT * GUARD_LEAK * C * hw[None, :]
            for g in np.nonzero(G.any(0))[0]:
                h = G[:, g]
                pr = 1 - np.prod(1 - P[:, h], axis=1)
                got = ~h & (rng.random(len(A)) < pr)
                self.guard[A[got], g] = True
                for L in A[got][:1]:
                    self.log("craft", f"the secret of {GUARD_NAMES[g]} "
                             f"reaches {self.lname(L)}")
        if self.n_guard >= GUARD_MAX:
            return
        for pid, p in self.polities.items():
            L = p["lin"]
            if p["ended"] is not None or len(p["cities"]) < GUARD_CITIES or \
                    self.craft[L] < GUARD_CRAFT:
                continue
            if rng.random() < DT * GUARD_P:
                g = self.n_guard
                self.n_guard += 1
                self.guard[L, g] = True
                self.log("craft", f"{self.pname(pid)} ({self.lname(L)}) "
                         f"masters {GUARD_NAMES[g]} and guards the secret")
                if self.n_guard >= GUARD_MAX:
                    return

    def ore_by_trade(self, near, nL):
        """Lineages that get an ore by trade: those living in a state
        joined, by a chain of ties >= ORE_TIE, to a state whose territory
        holds a worked deposit (`near`)."""
        pol = self.cell_pol
        src = set(np.unique(pol[near & (pol >= 0)]).tolist())
        out = np.zeros(nL, bool)
        if not src:
            return out
        nbr = {}
        for (x, y), t in self.ties.items():
            if t >= ORE_TIE:
                nbr.setdefault(x, []).append(y)
                nbr.setdefault(y, []).append(x)
        reach, front = set(src), list(src)
        while front:
            x = front.pop()
            for y in nbr.get(x, ()):
                if y not in reach:
                    reach.add(y)
                    front.append(y)
        occ = (self.lin >= 0) & (pol >= 0)
        inr = np.zeros(self.next_pid, bool)
        inr[list(reach)] = True
        m = occ & inr[np.maximum(pol, 0)]
        out[np.unique(self.lin[m])] = True
        return out

    # ---- disasters
    def disasters(self):
        W, rng = self.W, self.rng
        self.drought += (1 - self.drought) * 0.35
        no_drought = "climate" in self.on   # the climate has its own
        if "immunity" in self.on:
            self.imm *= math.exp(-IMM_DECAY * DT)
            if self.cities:
                cc = np.fromiter(self.cities.keys(), int)
                big = cc[self.pop[cc] > 5 * self.pcity[np.maximum(
                    self.cul[cc], 0)]]
                self.imm[big] = np.maximum(self.imm[big], IMM_ENDEMIC)
        if not no_drought and rng.random() < 0.08:
            i = int(rng.integers(W.N))
            rad = rng.uniform(400, 1500)
            sev = rng.uniform(0.35, 0.7)
            d = gc_km(W.xyz, i, np.arange(W.N))
            f = np.clip(1 - d / rad, 0, 1)
            self.drought = np.minimum(self.drought, 1 - sev * f)
            if self.cities:
                cc = np.fromiter(self.cities.keys(), int)
                self.shock(cc[f[cc] > 0.3], "drought")
            hit = (self.pop * (f > 0.3)).sum()
            if hit > 1e6:
                self.log("drought", f"great drought centred {self.place(i)} "
                         f"({hit/1e6:.1f}M people affected)")
        urban = sum(self.pop[c] * (self.peat[self.cul[c]] if "food_units"
                                   in self.on and self.cul[c] >= 0 else 1)
                    for c in self.cities)
        if self.cities and self.tick >= getattr(self, "_plague_next", 0) \
                and rng.random() < 0.04 * min(1, urban / 3e6):
            self._plague_next = self.tick + 10
            cc = np.fromiter(self.cities.keys(), int)
            wt = self.pop[cc]
            o = int(rng.choice(cc, p=wt / wt.sum()))
            start = self.cities[o]["polity"]
            if start not in self.polities:
                return
            imm_on = "immunity" in self.on
            host = int(self.cul[o])
            hit = {start}
            frontier = [start]
            for _ in range(4):
                nxt = []
                for x in frontier:
                    for k in self.adj:
                        if x in k:
                            y = k[1] if k[0] == x else k[0]
                            if y in hit:
                                continue
                            pr = 0.25 + 0.6 * self.ties.get(k, 0)
                            if imm_on and self.polities[y]["culture"] != host:
                                pr *= PLAGUE_CROSS + 0.4
                            if rng.random() < pr:
                                hit.add(y)
                                nxt.append(y)
                frontier = nxt
            mort = rng.uniform(0.15, 0.35)
            mask = np.isin(self.cell_pol, list(hit))
            self.hard[mask] = 1
            for x in hit:
                self.shock(list(self.polities[x]["cities"]), "plague")
                self.spike(x)
            if imm_on:
                # the host people dies at full rate, others at a fraction;
                # survivors of a recent plague, and the people of large
                # cities where it is endemic, are partly immune
                f = mort * (1 - IMM_PROTECT * self.imm) * mask
                fm = f * np.where(self.mcul == host, 1, PLAGUE_CROSS)
                f = f * np.where(self.cul == host, 1, PLAGUE_CROSS)
                dead = (self.pop * f).sum() + (self.mpop * fm).sum()
                self.pop *= 1 - f
                self.mpop *= 1 - fm
                for x in hit:
                    for c in self.polities[x]["cities"]:
                        self.pop[c] *= 1 - 0.3 * f[c]
                self.imm[mask] = np.maximum(self.imm[mask], IMM_HIT)
            else:
                dead = (self.pop * mask).sum() * mort
                self.pop[mask] *= 1 - mort
                for x in hit:
                    for c in self.polities[x]["cities"]:
                        self.pop[c] *= 1 - 0.3 * mort
            if dead > 2e5:
                self.log("plague", f"plague from {self.place(o)} through "
                         f"{len(hit)} states, ~{dead/1e6:.2f}M dead"
                         + (f" (host: {self.keys[host]})" if imm_on else ""))

    # ---- bookkeeping
    def people_summary(self):
        """Per people: population, living lineages, best tech stage, best
        farming level."""
        nP, nL = self.nP, self.nL
        occ = self.lin >= 0
        popc = np.bincount(self.cul[occ], weights=self.pop[occ], minlength=nP)
        Lpop = np.bincount(self.lin[occ], weights=self.pop[occ], minlength=nL)
        out = []
        for c in range(nP):
            Ls = np.nonzero((self.Lpeople[:nL] == c) & (Lpop > 0))[0]
            stage = ("St" if self.steel[Ls].any() else
                     "Fe" if self.iron[Ls].any() else
                     "Br" if self.bronze[Ls].any() else "")
            out.append(dict(pop=popc[c], nlin=len(Ls), stage=stage,
                            agri=float(self.agri[Ls].max()) if len(Ls) else 0,
                            metal=float(self.metal[Ls].max())
                            if len(Ls) else 0))
        return out

    def record(self):
        nP = self.nP
        occ = self.cul >= 0
        cells = np.bincount(self.cul[occ], minlength=nP)
        ncity = np.zeros(nP, int)
        for r in self.cities.values():
            ncity[r["culture"]] += 1
        live = [p for p in self.polities.values() if p["ended"] is None]
        big = max((p["n_cells"] for p in live), default=0)
        bigkm = max((p.get("km2", 0) for p in live), default=0)
        ps = self.people_summary()
        for c in range(nP):
            if ps[c]["pop"] > 0:
                self.p_seen[c] = True
            elif self.p_seen[c] and not self.p_extinct[c]:
                self.p_extinct[c] = True
                self.log("extinction", f"the last {self.P[c]['label']} are "
                         "gone")
        # population-weighted mean traits, world and per people
        o = np.nonzero(self.lin >= 0)[0]
        w, Lo, co = self.pop[o], self.lin[o], self.cul[o]
        tr = {}
        ZX = np.hstack([self.LT, self.LX])
        for t in ("violence", "tolerance", "expansion", "cohesion",
                  "conformity", "hierarchy", "trade"):
            v = ZX[Lo, (TRAITS + XTRAITS).index(t)]
            tr[f"{t}_world"] = float((w * v).sum() / max(w.sum(), 1))
            s = np.bincount(co, weights=w * v, minlength=nP)
            n = np.bincount(co, weights=w, minlength=nP)
            for i, k in enumerate(self.keys):
                tr[f"{t}_{k}"] = float(s[i] / n[i]) if n[i] > 0 else None
        # structural measures
        live2 = [p for p in live if len(p["cities"]) >= 2]
        at_war = {x for k in self.wars for x in k}
        farmed = occ & ~self.herding
        st = dict(
            at_war_share=round(sum(p["id"] in at_war for p in live2) /
                               max(len(live2), 1), 3),
            revolts=self.n_revolts,
            vassals=len(self.vassal),
            herd_share=round(float((self.pop * self.herding).sum() /
                                   max(self.pop.sum(), 1)), 3),
            land_mean=round(float((self.land * self.pop * farmed).sum() /
                                  max((self.pop * farmed).sum(), 1)), 3),
            moisture=round(float((self.moist * self.pop).sum() /
                                 max(self.pop.sum(), 1)), 3),
            dry_pop_share=round(float(self.pop[self.moist < -1.5].sum() /
                                      max(self.pop.sum(), 1)), 3),
            famine_movers=round(self.famine_movers),
            avulsions=self.n_avulsions,
            road_cells=int((self.road > 0.3).sum()),
            improvements=round(float((self.imp * self.pop).sum() /
                                     max(self.pop.sum(), 1)), 3),
            minority_pop=float(self.mpop.sum()),
            stress_mean=round(float(np.mean([p["stress"] for p in live2]))
                              if live2 else 0.0, 3),
            bronze_users=int(self.bronze[:self.nL].sum()),
            cities_mixed_share=round(float(np.mean([
                r.get("min_share", 0.0) > 0.1 for r in self.cities.values()]))
                if self.cities else 0.0, 3))
        if "land_pressure" in self.on:
            # the same columns every tick, empty before there are states
            st["crowd_mean"] = round(float(np.mean([p["crowd"]
                                                    for p in live2])), 3) \
                if live2 else None
            st["room_mean"] = round(float(np.mean([p.get("room", 0)
                                                   for p in live2])), 3) \
                if live2 else None
            st["pressured_share"] = round(float(np.mean(
                [self.pressure(p) > 0 for p in live2])), 3) \
                if live2 else None
        if "mission" in self.on:
            o3 = self.lin >= 0
            st["churn_mean"] = round(float(
                (self.Lchurn[self.lin[o3]] * self.pop[o3]).sum() /
                max(self.pop[o3].sum(), 1)), 4)
        if "salinity" in self.on:
            irr = (self.lin >= 0) & (self.W.irr_share > 0.3)
            st["salt_irrigated"] = round(float(
                (self.salt * self.pop)[irr].sum() /
                max(self.pop[irr].sum(), 1)), 3)
        if self.on & {"craft", "domestication", "resources", "guarded"}:
            o2 = np.nonzero(self.lin >= 0)[0]
            w2 = self.pop[o2] / max(self.pop[o2].sum(), 1)
            L2 = self.lin[o2]
            st.update(
                craft_mean=round(float(w2 @ self.craft[L2]), 3),
                guarded=int(self.n_guard),
                res_held=int(sum(len(a["kinds"])
                                 for a in self.passets.values())),
                dev_mean=round(float(w2 @ self.dev(L2)), 3),
                dom_mean=round(float(w2 @ self.domlv[L2].max(1)), 3)
                if len(self.h_cell) else 0.0,
                ties_cross=int(sum(1 for (x, y), t in self.ties.items()
                                   if t > 0.3 and self.polities[x]["culture"]
                                   != self.polities[y]["culture"])))
        if "dragons" in self.on:
            st.update(self.dragon_record())
        self.n_revolts = 0
        CNT = ["ally_same", "ally_cross", "ally_balance", "ally_break",
               "union", "fusion", "vassal_submit_same", "vassal_submit_cross",
               "vassal_defect", "vassal_annex", "vassal_freed", "war_same",
               "war_cross", "capture_same", "capture_cross", "war_goal_met",
               "war_goal_resource", "war_goal_rule", "war_goal_land",
               "war_ceded", "war_goal_faith", "war_goal_prey",
               "war_goal_enmity", "war_goal_irredentism", "raid",
               "war_counter_capture", "ally_join", "ally_refuse",
               "ally_lapse", "ally_outgrown", "ally_betray",
               "ally_lapse_death", "partition", "union_crowns",
               "colony_state", "colony_displace", "colony_minority",
               "colony_city", "trade_post", "devastation",
               "devastation_city"] + \
            [f"revolt_{k}{c}" for k in ("secession", "kin", "ethnic",
                                         "pretender")
             for c in ("", "_cities")] + \
            [f"dragon_{k}" for k in ("slain", "pushed", "lost", "ally",
                                     "freed", "born", "died")]
        st.update({f"n_{k}": self.cnt.get(k, 0) for k in CNT})
        self.cnt = {}
        st["city_years"] = len(self.cities) * DT
        # within-people structure: states, cities per state, and cultural
        # spread of lineages (pop-weighted mean distance from the people's
        # mean traits)
        nst = np.zeros(nP)
        ncs = np.zeros(nP)
        for p in live:
            nst[p["culture"]] += 1
            ncs[p["culture"]] += len(p["cities"])
        Lp = np.bincount(Lo, weights=w, minlength=self.nL)
        Ls = np.nonzero(Lp > 0)[0]
        for i, k in enumerate(self.keys):
            st[f"states_{k}"] = int(nst[i])
            st[f"cities_per_state_{k}"] = round(ncs[i] / nst[i], 2) \
                if nst[i] else None
            g = Ls[self.Lpeople[Ls] == i]
            if len(g):
                pw = Lp[g] / Lp[g].sum()
                mu = pw @ self.LT[g]
                st[f"spread_{k}"] = round(float(
                    pw @ np.linalg.norm(self.LT[g] - mu, axis=1)), 4)
            else:
                st[f"spread_{k}"] = None
        if "diagnostics" in self.on and self.year % PRICE_EVERY == 0:
            self.price()
        self.ts.append(dict(year=self.year, **st, **tr, **{
            f"pop_{k}": float(ps[i]["pop"]) for i, k in enumerate(self.keys)},
            **{f"cells_{k}": int(cells[i]) for i, k in enumerate(self.keys)},
            **{f"cities_{k}": int(ncity[i]) for i, k in enumerate(self.keys)},
            **{f"lineages_{k}": ps[i]["nlin"] for i, k in
               enumerate(self.keys)},
            n_polities=len(live), largest_polity_cells=int(big),
            largest_polity_Mkm2=round(bigkm / 1e6, 3),
            wars=len(self.wars), alliances=len(self.allies),
            multi_people_states=sum(1 for p in live
                                    if len(p["peoples"]) > 1),
            **{f"agri_{k}": ps[i]["agri"] for i, k in enumerate(self.keys)},
            **{f"metal_{k}": ps[i]["metal"] for i, k in
               enumerate(self.keys)}))
        for cell in self.cities:
            hinter = self.pop[self.cell_city == cell].sum()
            rec = self.cities[cell]
            ms = 0.0
            if self.mlin[cell] >= 0:
                a = self.pop[cell] * self.peat[self.cul[cell]]
                b = self.mpop[cell] * self.peat[self.mcul[cell]]
                ms = b / max(a + b, 1e-9)
                rec.setdefault("min_peoples", set()).add(int(self.mcul[cell]))
            rec["min_share"] = ms
            rec["min_peak"] = max(rec.get("min_peak", 0.0), ms)
            if ms > 0.1:
                rec["min_years"] = rec.get("min_years", 0) + DT
            size = 0.08 * self.pop[cell] + 0.04 * hinter
            if "food_units" in self.on:
                size *= self.peat[self.cities[cell]["culture"]]
            self.city_size[cell] = size
            rec = self.cities[cell]
            if size > rec["peak"]:
                rec["peak"], rec["peak_year"] = size, self.year
            self.city_years[cell] += DT
            self.city_peak[cell] = max(self.city_peak[cell], size)
        for cell, rec in self.ruins.items():
            rec["ruin_years"] += DT
            rec["ruin_empty"] += DT * (self.lin[cell] < 0)
        if self.year % CITY_TS_EVERY == 0:
            for cell, rec in self.cities.items():
                self.city_ts.append((
                    self.year, rec["id"], cell, "city",
                    round(self.city_size.get(cell, 0.0)),
                    round(float(self.pop[cell])), self.keys[rec["culture"]],
                    rec["polity"],
                    self.keys[self.mcul[cell]] if self.mlin[cell] >= 0
                    else "", round(rec.get("min_share", 0.0), 3)))
            for cell, rec in self.ruins.items():
                c = self.cul[cell]
                self.city_ts.append((
                    self.year, rec["id"], cell,
                    "ruin, empty" if c < 0 else "ruin, settled", 0,
                    round(float(self.pop[cell])),
                    self.keys[c] if c >= 0 else "", -1, "", 0))

    def price(self):
        """Price-equation decomposition of the change in each cultural
        trait over the last PRICE_EVERY years, per people and for the
        world, with the lineages alive at the last snapshot as units.
        A lineage's offspring are its own cells now plus those of its
        descendant lineages; cells assimilated into it count as its
        offspring too, since that is how a culture reproduces here.
            wbar dzbar = Cov(w, z) + E(w dz)     (weights: ancestor pop)
        selection = Cov/wbar, transmission = E(w dz)/wbar."""
        nL = self.nL
        occ = self.lin >= 0
        wts = self.pop[occ] * (self.peat[self.cul[occ]] if "food_units" in
                               self.on else 1)
        Lpop = np.bincount(self.lin[occ], weights=wts, minlength=nL)
        alive = np.nonzero(Lpop > 0)[0]
        snap = self.price_snap
        ZT = np.hstack([self.LT, self.LX])
        EX = self.Lexp.copy()
        self.Lexp[:] = 0
        self.price_snap = dict(L=alive, pop=Lpop[alive],
                               T=ZT[alive].copy(), year=self.year)
        if snap is None:
            return
        S = snap["L"]
        pos = -np.ones(nL, int)
        pos[S] = np.arange(len(S))
        # nearest ancestor in the snapshot, for every lineage alive now
        anc = -np.ones(nL, int)
        for j in alive:
            x = j
            while x >= 0 and pos[x] < 0:
                x = self.Lparent[x]
            anc[j] = pos[x] if x >= 0 else -1
        a = anc[alive]
        ok = a >= 0
        names = TRAITS + XTRAITS
        nS, nT = len(S), len(names)
        off = np.bincount(a[ok], weights=Lpop[alive][ok], minlength=nS)
        zoff = np.zeros((nS, nT))
        for k in range(nT):
            zoff[:, k] = np.bincount(a[ok], weights=(Lpop[alive] *
                                     ZT[alive, k])[ok], minlength=nS)
        z = snap["T"]
        zp = np.where(off[:, None] > 0, zoff / np.maximum(off, 1e-9)[:, None],
                      z)
        # the experience-driven part of each offspring group's change
        eoff = np.zeros((nS, nT))
        for k in range(nT):
            eoff[:, k] = np.bincount(a[ok], weights=(Lpop[alive] *
                                     EX[alive, k])[ok], minlength=nS)
        ze = np.where(off[:, None] > 0, eoff / np.maximum(off, 1e-9)[:, None],
                      0)
        p0 = snap["pop"]
        w = off / np.maximum(p0, 1e-9)
        peo = self.Lpeople[S]
        immig = Lpop[alive][~ok].sum() / max(Lpop.sum(), 1)
        groups = [(self.keys[c], peo == c) for c in range(self.nP)] + \
            [("ALL", np.ones(nS, bool))]
        for name, g in groups:
            if g.sum() < 2 or p0[g].sum() <= 0:
                continue
            pw = p0[g] / p0[g].sum()
            wg, zg, zpg, zeg = w[g], z[g], zp[g], ze[g]
            wbar = float(pw @ wg)
            if wbar <= 0:
                continue
            zbar = pw @ zg
            cov = pw @ ((wg - wbar)[:, None] * (zg - zbar))
            trans = pw @ (wg[:, None] * (zpg - zg))
            expc = pw @ (wg[:, None] * zeg)
            for k, t in enumerate(names):
                if t == "seafaring" and "dispersal" in self.on:
                    continue
                self.price_rows.append(dict(
                    year=self.year, people=name, trait=t,
                    zbar=round(float(zbar[k]), 4),
                    dz=round(float((cov[k] + trans[k]) / wbar), 5),
                    selection=round(float(cov[k] / wbar), 5),
                    transmission=round(float(trans[k] / wbar), 5),
                    experience=round(float(expc[k] / wbar), 5),
                    wbar=round(wbar, 4), n_lineages=int(g.sum()),
                    immigrant_share=round(float(immig), 4)))

    def step(self):
        self._sim = {}
        self.place_arrivals()
        self.technology()
        self.prepare_capacity()
        if "climate" in self.on:
            self.famine()
        if "dragons" in self.on:
            self.dragons()
        self.grow()
        self.migrate()
        self.raids()
        self.tidy()
        self.update_cities()
        self.territory()
        if "roads" in self.on and self.year % ROAD_EVERY == 0:
            self.roads()
        self.polity_stats()
        if "trade_posts" in self.on:
            self.trade_posts()
        self.trade_ties()
        if "goods_value" in self.on:
            self.pref_spread()
        if "minority" in self.on:
            self.minorities()
        self.diplomacy()
        self.wars_step()
        self.rebellions()
        self.disasters()
        self.tidy()
        self.record()
        self.tick += 1
        self.year += DT

    def relations(self):
        """Snapshot of every pair of neighbouring live states (by land or
        sea): similarity, each side's enmity and faith motives, trade tie,
        war, alliance, truce. Reads state only (no draws)."""
        W = self.W
        for k in sorted(self.adj | set(self.posts)):
            ab = self.live(k)
            if not ab:
                continue
            A, B = ab
            La, Lb = A["lin"], B["lin"]
            sim = self.similarity(La, Lb)
            fa = fb = 0.0
            if "mission" in self.on:
                fa = (1 - sim) * (MIS_HOLY * self.pros[La] + MIS_BACKLASH *
                                  self.pros[Lb] * (1 - self.tol[La]))
                fb = (1 - sim) * (MIS_HOLY * self.pros[Lb] + MIS_BACKLASH *
                                  self.pros[La] * (1 - self.tol[Lb]))
            self.rel.append((
                self.year, k[0], k[1], self.keys[A["culture"]],
                self.keys[B["culture"]], int(W.landmass[A["capital"]]),
                int(W.landmass[B["capital"]]), len(A["cities"]),
                len(B["cities"]), round(sim, 4),
                round(ENM_K * (1 - sim) * self.hostile(La), 4),
                round(ENM_K * (1 - sim) * self.hostile(Lb), 4),
                round(fa, 4), round(fb, 4), round(self.ties.get(k, 0.0), 4),
                int(k in self.wars), int(k in self.allies),
                int(self.truce.get(k, -1) > self.tick)))

    def run(self, verbose=True):
        t0 = time.time()
        nt = self.years // DT
        for _ in range(nt):
            self.step()
            if self.tick % self.frame_every == 0 or self.tick == nt:
                self.frames.append(render(self))
                self.relations()
            if verbose and self.tick % 50 == 0:
                s = self.ts[-1]
                tot = sum(s[f"pop_{k}"] for k in self.keys)
                nlin = sum(s[f"lineages_{k}"] for k in self.keys)
                print(f"yr {self.year:5d}  pop {tot/1e6:7.2f}M  cities "
                      f"{len(self.cities):4d}  states {s['n_polities']:4d}"
                      f"  lineages {nlin:4d}  allies {len(self.allies):3d}"
                      f"  wars {len(self.wars):3d}  "
                      f"[{time.time()-t0:5.0f}s]", flush=True)


# ---- rendering -----------------------------------------------------------
def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def borders_mask(lab2):
    b = np.zeros(lab2.shape, bool)
    b[:, :-1] |= lab2[:, :-1] != lab2[:, 1:]
    b[:-1, :] |= lab2[:-1, :] != lab2[1:, :]
    return b


def render(sim, scale=2):
    W = sim.W
    r0, r1 = W.r0, W.r1
    occ = sim.cul >= 0
    dens = np.where(occ, sim.pop / W.area, 0)
    a = np.clip(np.log10(1 + dens) / np.log10(1 + 60), 0.4, 1)

    # political map
    pol = W.base.astype(float).copy()
    pid = sim.cell_pol
    pc = np.zeros((sim.next_pid, 3))
    for k, p in sim.polities.items():
        pc[k] = p["col"]
    m = pid >= 0
    rr, cc = W.row, W.col
    tribal = occ & ~m
    col_t = sim.colors[np.maximum(sim.cul, 0)].astype(float)
    pol[rr[tribal], cc[tribal]] = 0.6 * pol[rr[tribal], cc[tribal]] + \
        0.4 * col_t[tribal]
    pol[rr[m], cc[m]] = 0.15 * pol[rr[m], cc[m]] + 0.85 * pc[pid[m]]
    lab = -np.ones((NY, NX), int)
    lab[rr, cc] = np.where(m, pid, -2)
    lab[~W.land2] = -3
    bm = borders_mask(lab) & W.land2 & (lab >= 0)
    pol[bm] = pol[bm] * 0.25

    # peoples map
    eth = W.base.astype(float).copy()
    eth[rr[occ], cc[occ]] = (1 - a[occ, None]) * eth[rr[occ], cc[occ]] + \
        a[occ, None] * col_t[occ]

    def panel(img):
        im = img[r0:r1].clip(0, 255).astype(np.uint8)
        im = np.repeat(np.repeat(im, scale, 0), scale, 1)
        return Image.fromarray(im)

    P1, P2 = panel(pol), panel(eth)
    for P, dots in ((P1, True), (P2, True)):
        d = ImageDraw.Draw(P)
        for cell, rec in sim.cities.items():
            s = sim.city_size.get(cell, 0)
            rad = 1 + 1.2 * math.log10(1 + s / 2000)
            x = (W.col[cell] + 0.5) * scale
            y = (W.row[cell] - r0 + 0.5) * scale
            p = sim.polities.get(rec["polity"])
            cap = p is not None and p["capital"] == cell
            d.ellipse([x - rad, y - rad, x + rad, y + rad],
                      fill=(255, 255, 255) if cap else (235, 230, 215),
                      outline=(0, 0, 0))
            if cap and p["n_cells"] > 250:
                d.ellipse([x - rad - 3, y - rad - 3, x + rad + 3, y + rad + 3],
                          outline=(255, 255, 255), width=2)
    if "dragons" in sim.on:
        d = ImageDraw.Draw(P2)
        for h, al in zip(sim.dhome, sim.dally):
            x = (W.col[h] + 0.5) * scale
            y = (W.row[h] - r0 + 0.5) * scale
            d.rectangle([x - 1, y - 1, x + 1, y + 1],
                        fill=(255, 215, 0) if al >= 0 else (120, 0, 0))
    d = ImageDraw.Draw(P1)
    f = font(13)
    live = sorted([p for p in sim.polities.values() if p["ended"] is None],
                  key=lambda p: -p["n_cells"])[:10]
    for p in live:
        if p["n_cells"] < 150:
            break
        c = p["capital"]
        x = (W.col[c] + 0.5) * scale + 6
        y = (W.row[c] - r0 + 0.5) * scale - 6
        d.text((x, y), sim.pname(p["id"]), fill=(255, 255, 255), font=f,
               stroke_width=2, stroke_fill=(0, 0, 0))

    w, h = P1.size
    rows = (sim.nP + 4) // 5
    hdr = 14 + 38 * rows
    out = Image.new("RGB", (w, 2 * h + hdr + 6), (16, 18, 24))
    out.paste(P1, (0, hdr))
    out.paste(P2, (0, hdr + h + 6))
    d = ImageDraw.Draw(out)
    d.text((12, 8), f"Year {sim.year}", fill=(240, 240, 240), font=font(24))
    ps = sim.people_summary()
    for i, k in enumerate(sim.keys):
        x = 150 + 225 * (i % 5)
        y0 = 38 * (i // 5)
        d.rectangle([x, 12 + y0, x + 14, 26 + y0], fill=tuple(sim.colors[i]))
        d.text((x + 20, 8 + y0), f"{sim.P[i]['label']}",
               fill=(230, 230, 230), font=font(13))
        d.text((x + 20, 26 + y0), f"{ps[i]['pop']/1e6:5.2f}M "
               f"{ps[i]['nlin']} lin {ps[i]['stage']}",
               fill=(170, 170, 170), font=font(12))
    nl = sum(1 for p in sim.polities.values() if p["ended"] is None)
    d.text((12, 40), f"states {nl}", fill=(230, 230, 230), font=font(13))
    d.text((12, 58), f"wars {len(sim.wars)}", fill=(230, 230, 230),
           font=font(13))
    return out


def legacy_map(sim, scale=2):
    """Where cities stood and how far the great states once reached."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float) * 0.55
    im = Image.fromarray(np.repeat(np.repeat(
        img[r0:r1].astype(np.uint8), scale, 0), scale, 1))
    d = ImageDraw.Draw(im, "RGBA")
    greats = sorted([p for p in sim.polities.values()
                     if p["peak_mask"] is not None],
                    key=lambda p: -p["peak_cells"])[:14]
    f = font(13)
    for p in greats:
        msk = np.zeros((NY, NX), bool)
        msk[W.row[p["peak_mask"]], W.col[p["peak_mask"]]] = True
        edge = msk & ~ndimage.binary_erosion(msk)
        col = tuple(int(v) for v in sim.colors[p["culture"]])
        ys, xs = np.nonzero(msk[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (38,))
        ys, xs = np.nonzero(edge[r0:r1])
        for y, x in zip(ys, xs):
            d.rectangle([x * scale, y * scale, x * scale + scale - 1,
                         y * scale + scale - 1], fill=col + (230,))
    order = np.argsort(sim.city_years)
    for cell in order[sim.city_years[order] > 0]:
        yrs = sim.city_years[cell]
        rad = 1 + 1.3 * math.log10(1 + sim.city_peak[cell] / 2000)
        al = int(np.clip(70 + yrs / 8, 70, 255))
        x = (W.col[cell] + 0.5) * scale
        y = (W.row[cell] - r0 + 0.5) * scale
        rc = [r for r in sim.city_hist if r["cell"] == cell]
        c = sim.colors[rc[-1]["culture"]] if rc else (255, 255, 255)
        d.ellipse([x - rad, y - rad, x + rad, y + rad],
                  fill=tuple(int(v) for v in c) + (al,),
                  outline=(255, 255, 255, al))
    placed = []
    for p in greats:
        msk_cells = p["peak_mask"]
        cy = (np.median(W.row[msk_cells]) - r0) * scale
        cx = np.median(W.col[msk_cells]) * scale
        if any(abs(cx - x) < 150 and abs(cy - y) < 18 for x, y in placed):
            continue
        placed.append((cx, cy))
        end = p["ended"] if p["ended"] is not None else "now"
        d.text((cx, cy),
               f"{sim.pname(p['id'])} {p['founded']}-{end}",
               fill=(255, 255, 255, 255), font=f, stroke_width=2,
               stroke_fill=(0, 0, 0, 255))
    hdr = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    hdr.paste(im, (0, 40))
    dd = ImageDraw.Draw(hdr)
    dd.text((12, 8), f"Legacy after {sim.year} years: cities (size = peak, "
            f"opacity = years inhabited) and the peak extent of the "
            f"{len(greats)} largest states", fill=(235, 235, 235),
            font=font(16))
    return hdr


def population_plot(sim, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = [s["year"] for s in sim.ts]
    fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    ys = [[s[f"pop_{k}"] / 1e6 for s in sim.ts] for k in sim.keys]
    cols = sim.colors / 255
    ax[0].stackplot(yrs, ys, colors=cols,
                    labels=[f"{k} {p['label']}" for k, p in
                            zip(sim.keys, sim.P)])
    ax[0].set_ylabel("population (M)")
    ax[0].legend(loc="upper left", fontsize=8, frameon=False)
    for i, k in enumerate(sim.keys):
        ax[1].plot(yrs, [s[f"cities_{k}"] for s in sim.ts], color=cols[i])
    ax[1].set_ylabel("cities")
    ax[2].plot(yrs, [s["n_polities"] for s in sim.ts], color="k",
               label="states")
    ax2 = ax[2].twinx()
    ax2.plot(yrs, [s["largest_polity_Mkm2"] for s in sim.ts],
             color="tab:red", label="largest state")
    ax[2].set_ylabel("number of states")
    ax2.set_ylabel("largest state (M km2)", color="tab:red")
    ax[2].set_xlabel("year")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def trait_plot(sim, path, traits=("violence", "tolerance")):
    """Population-weighted mean of each trait over time: world (black)
    and per people."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = np.array([s["year"] for s in sim.ts])
    cols = sim.colors / 255
    fig, ax = plt.subplots(len(traits), 1, figsize=(11, 4 * len(traits)),
                           sharex=True)
    for a, t in zip(np.atleast_1d(ax), traits):
        for i, k in enumerate(sim.keys):
            y = np.array([np.nan if s[f"{t}_{k}"] is None else s[f"{t}_{k}"]
                          for s in sim.ts])
            a.plot(yrs, y, color=cols[i], lw=1.2, label=sim.P[i]["label"])
        a.plot(yrs, [s[f"{t}_world"] for s in sim.ts], color="k", lw=2.6,
               label="world")
        a.set_ylabel(f"mean {t}")
        a.set_ylim(0, 1)
        a.spines[["top", "right"]].set_visible(False)
    np.atleast_1d(ax)[0].legend(loc="upper left", fontsize=8, ncol=6,
                                frameon=False)
    np.atleast_1d(ax)[-1].set_xlabel("year")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def lineage_map(sim, scale=2):
    """Final map of living lineages: hue = people, shade = lineage; thin
    lines separate lineages, thick lines separate peoples."""
    W = sim.W
    r0, r1 = W.r0, W.r1
    img = W.base.astype(float).copy()
    occ = sim.lin >= 0
    rr, cc = W.row[occ], W.col[occ]
    img[rr, cc] = 0.2 * img[rr, cc] + 0.8 * sim.Lcol[sim.lin[occ]]
    lab = -np.ones((NY, NX), int)
    lab[W.row, W.col] = sim.lin
    peo = -np.ones((NY, NX), int)
    peo[W.row, W.col] = sim.cul
    bl = borders_mask(lab) & (lab >= 0)
    bp = borders_mask(peo) & (peo >= 0)
    img[bl] *= 0.6
    img[bp] *= 0.15
    im = img[r0:r1].clip(0, 255).astype(np.uint8)
    im = Image.fromarray(np.repeat(np.repeat(im, scale, 0), scale, 1))
    d = ImageDraw.Draw(im)
    occi = np.nonzero(occ)[0]
    Lpop = np.bincount(sim.lin[occi], weights=sim.pop[occi], minlength=sim.nL)
    for L in np.argsort(Lpop)[::-1][:40]:
        if Lpop[L] < 5e5:
            break
        cells = occi[sim.lin[occi] == L]
        y = (np.median(W.row[cells]) - r0) * scale
        x = np.median(W.col[cells]) * scale
        d.text((x, y), sim.lname(L), fill=(255, 255, 255), font=font(12),
               stroke_width=2, stroke_fill=(0, 0, 0))
    out = Image.new("RGB", (im.size[0], im.size[1] + 40), (16, 18, 24))
    out.paste(im, (0, 40))
    ImageDraw.Draw(out).text(
        (12, 8), f"Lineages in year {sim.year} ({int((Lpop > 0).sum())} "
        f"living): hue = people, shade = lineage", fill=(235, 235, 235),
        font=font(16))
    return out


def write_checks(sim, path):
    """Compare a run with rough historical regularities. The references
    are orders of magnitude, not targets (docs/diagnostics.md)."""
    P = [p for p in sim.polities.values() if p["peak_cities"] >= 3]
    L = []
    for p in P:
        end = p["ended"] if p["ended"] is not None else sim.year
        if p["ended"] is not None:          # finished lives only
            L.append(end - p["founded"])
    L = np.array(L, float)
    lines = ["Stylized-fact checks (references are rough; see "
             "docs/diagnostics.md)", ""]
    if len(L):
        lines += [f"State lifespans (states that held 3+ cities and ended; "
                  f"n={len(L)}):",
                  f"  mean {L.mean():.0f} yrs, median {np.median(L):.0f}, "
                  f"CV {L.std() / max(L.mean(), 1):.2f}",
                  "  reference: mean ~200-250 yrs, roughly exponential "
                  "(CV ~1) [Arbesman 2011]", ""]
    sz = np.array(sorted((p["peak_cells"] for p in P), reverse=True), float)
    if len(sz) >= 10:
        lg = np.log(sz[sz > 0])
        sk = float(((lg - lg.mean()) ** 3).mean() / max(lg.std(), 1e-9) ** 3)
        lines += [f"State sizes at peak (cells, states with 3+ cities; "
                  f"n={len(sz)}):",
                  f"  largest {sz[0]:.0f}, 10th {sz[9]:.0f}, median "
                  f"{np.median(sz):.0f}; skew of log size {sk:+.2f}",
                  "  reference: heavy-tailed, roughly log-normal (skew of "
                  "log size near 0) [Taagepera 1978-97]", ""]
    cs = np.array(sorted(sim.city_size.values(), reverse=True), float)
    cs = cs[cs > 0][:200]
    if len(cs) >= 20:
        slope = np.polyfit(np.log(np.arange(1, len(cs) + 1)), np.log(cs), 1)[0]
        lines += [f"City rank-size (top {len(cs)} at the end): slope "
                  f"{slope:.2f}",
                  "  reference: about -1 (Zipf); pre-modern systems often "
                  "flatter, -0.6 to -1", ""]
    ws = [r["at_war_share"] for r in sim.ts if "at_war_share" in r]
    if ws:
        lines += [f"Share of states (2+ cities) at war, mean over run: "
                  f"{np.mean(ws):.2f}",
                  "  reference: high in pre-modern state systems; great "
                  "powers at war in most years [Levy 1983]. Uncertain.", ""]
    if sim.price_rows:
        lines += ["Price decomposition, summed over the run (ALL = world, "
                  "lineages as units):",
                  f"  {'trait':12s} {'dz':>8s} {'selection':>10s} "
                  f"{'transmission':>13s}"]
        for t in TRAITS:
            rows = [r for r in sim.price_rows
                    if r["people"] == "ALL" and r["trait"] == t]
            s = sum(r["selection"] for r in rows)
            tr = sum(r["transmission"] for r in rows)
            lines.append(f"  {t:12s} {s + tr:+8.3f} {s:+10.3f} {tr:+13.3f}")
        lines += ["", "  within peoples (mean over peoples of the summed "
                  "terms; selection | transmission):"]
        for t in TRAITS:
            ss, tt = [], []
            for k in sim.keys:
                rows = [r for r in sim.price_rows
                        if r["people"] == k and r["trait"] == t]
                if rows:
                    ss.append(sum(r["selection"] for r in rows))
                    tt.append(sum(r["transmission"] for r in rows))
            if ss:
                lines.append(f"  {t:12s} {np.mean(ss):+.3f} | "
                             f"{np.mean(tt):+.3f}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_outputs(sim, out):
    os.makedirs(out, exist_ok=True)
    fr = sim.frames
    if fr:
        small = [f.resize((f.size[0] * 3 // 4, f.size[1] * 3 // 4),
                          Image.LANCZOS) for f in fr]
        pal = [f.quantize(colors=200, method=Image.Quantize.MEDIANCUT)
               for f in small]
        pal[0].save(os.path.join(out, "history.gif"), save_all=True,
                    append_images=pal[1:], duration=140, loop=0,
                    optimize=False)
        fr[-1].save(os.path.join(out, "final_maps.png"))
    WCOL = ["id", "start", "end", "years", "att", "dfn", "people_att",
            "people_dfn", "landmass_att", "landmass_dfn", "cities_att",
            "cities_dfn", "strength_att", "strength_dfn", "goal", "goal_city",
            "goal_met", "why", "sieges", "captures", "recaptures", "moved",
            "moved_back", "helpers"]
    if sim.war_log:
        with open(os.path.join(out, "wars.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(WCOL)
            for r in sim.war_log:
                w.writerow([r.get(c, "ongoing" if c == "why" else "")
                            for c in WCOL])
    if sim.siege_log:
        with open(os.path.join(out, "sieges.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["year", "war", "side", "city", "city_fe", "capital",
                        "besieger", "holder", "P_besieger", "P_holder",
                        "odds", "taken"])
            w.writerows(sim.siege_log)
    if sim.revolt_log:
        with open(os.path.join(out, "revolts.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["year", "state", "new_state", "people_ruler",
                        "people_rebels", "kind", "cities_taken",
                        "cities_left", "landmass", "lon", "lat"])
            w.writerows(sim.revolt_log)
    if sim.ruler_log:
        with open(os.path.join(out, "rulers.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ruler", "state", "people", "start", "end", "years",
                        "cities", "succession"])
            w.writerows(sim.ruler_log)
    if sim.rel:
        with open(os.path.join(out, "relations.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["year", "a", "b", "people_a", "people_b",
                        "landmass_a", "landmass_b", "cities_a", "cities_b",
                        "similarity", "enmity_ab", "enmity_ba", "faith_ab",
                        "faith_ba", "tie", "war", "allied", "truce"])
            w.writerows(sim.rel)
        fdir = os.path.join(out, "frames")
        os.makedirs(fdir, exist_ok=True)
        for k, f in enumerate(fr):
            f.save(os.path.join(fdir, f"f{k:04d}.png"))
    legacy_map(sim).save(os.path.join(out, "legacy.png"))
    lineage_map(sim).save(os.path.join(out, "lineages.png"))
    population_plot(sim, os.path.join(out, "population.png"))
    trait_plot(sim, os.path.join(out, "violence.png"))
    with open(os.path.join(out, "traits.txt"), "w") as fh:
        fh.write(f"seed {sim.seed}, people variation {sim.vary}, start-group "
                 f"variation {sim.start_vary}, lineage drift {sim.drift}\n\n")
        for c, p in enumerate(sim.P):
            fh.write(f"{p['key']} {p['label']}\n  r={p['r']:.4f}  " +
                     "  ".join(f"{t}={p.get(t, 0.5):.2f}" for t in TRAITS) +
                     "\n  affinity " + "  ".join(
                         f"{b}={v:.2f}" for b, v in p["affinity"].items()) +
                     (f"\n  head start {p['head']} yrs" if p.get("head")
                      else "") +
                     f"\n  size {sim.psize[c]:g}  food/head {sim.peat[c]:.2f}"
                     + "\n")
            for L in range(sim.nL):
                if sim.Lpeople[L] == c and sim.Lhow[L] == "start":
                    fh.write(f"    start {sim.lname(L)} r={sim.Lr[L]:.4f}  " +
                             "  ".join(f"{t[:4]}={sim.LT[L, k]:.2f}"
                                       for k, t in enumerate(TRAITS)) + "\n")
            fh.write("\n")
    with open(os.path.join(out, "lineages.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "parent", "how", "founded", "ended",
                    "peak_pop", "stage", "agri", "metal", "sail", "fishing",
                    "war_mem", "trade_mem", "hard_mem", "raid_mem", "admin",
                    "r"] + TRAITS + XTRAITS)
        for L in range(sim.nL):
            stage = ("steel" if sim.steel[L] else "iron" if sim.iron[L] else
                     "bronze" if sim.bronze[L] else "")
            w.writerow([L, sim.keys[sim.Lpeople[L]], sim.Lparent[L],
                        sim.Lhow[L], sim.Lfounded[L],
                        sim.Lended[L] if sim.Lended[L] >= 0 else "",
                        int(sim.Lpeak[L]), stage, round(sim.agri[L], 3),
                        round(sim.metal[L], 3), round(sim.sail[L], 3),
                        round(sim.fishing[L], 3), round(sim.Lwarm[L], 4),
                        round(sim.Ltradem[L], 4), round(sim.Lhardm[L], 4),
                        round(sim.Lraidm[L], 4),
                        round(sim.admin[L], 3), round(sim.Lr[L], 4)] +
                       [round(v, 3) for v in sim.LT[L]] +
                       [round(v, 3) for v in sim.LX[L]])
    with open(os.path.join(out, "events.txt"), "w") as fh:
        for y, k, t in sim.events:
            fh.write(f"{y:5d}  {k:10s} {t}\n")
    import re
    great = {p["id"] for p in sorted(sim.polities.values(),
                                     key=lambda p: -p["peak_cells"])[:15]}
    always = {"origin", "contact", "trade", "tech", "voyage", "city",
              "fusion", "extinction"}
    with open(os.path.join(out, "chronicle.txt"), "w") as fh:
        fh.write("Major events only: world-firsts, great plagues and "
                 "droughts, and events touching the 15 largest states.\n\n")
        for y, k, t in sim.events:
            ids = {int(x) for x in re.findall(r"P(\d+)\(", t)}
            if k in always or (ids & great) or \
                    (k in ("plague", "drought") and "M" in t and
                     float(re.findall(r"([\d.]+)M", t)[0]) >= 2):
                fh.write(f"{y:5d}  {k:10s} {t}\n")
    with open(os.path.join(out, "cities.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "cell", "lon", "lat", "people", "founded", "ended",
                    "end_reason", "cause", "years", "peak_size", "peak_year",
                    "n_sacks", "n_rulers", "prev_city", "refounded",
                    "ruin_years", "ruin_empty_years", "successor", "rulers",
                    "minority_peoples", "minority_peak_share",
                    "minority_years", "majority_changes"])
        for r in sim.city_hist:
            end = r["ended"] if r["ended"] is not None else sim.year
            w.writerow([r["id"], r["cell"], f"{r['lon']:.2f}",
                        f"{r['lat']:.2f}", sim.keys[r["culture"]],
                        r["founded"], r["ended"], r["end_reason"],
                        r["cause"], end - r["founded"], int(r["peak"]),
                        r["peak_year"], r["n_sacks"], len(set(r["owners"])),
                        "" if r["prev"] is None else r["prev"],
                        "" if r["refounded"] is None else r["refounded"],
                        r["ruin_years"] if r["ended"] is not None else "",
                        r["ruin_empty"] if r["ended"] is not None else "",
                        "" if r["successor"] is None else r["successor"],
                        " ".join(f"P{x}" for x in dict.fromkeys(r["owners"])),
                        " ".join(sim.keys[c] for c in
                                 sorted(r.get("min_peoples", ()))),
                        round(r.get("min_peak", 0.0), 3),
                        r.get("min_years", 0), r.get("flips", 0)])
    with open(os.path.join(out, "city_sizes.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "city_id", "cell", "status", "size", "cell_pop",
                    "people", "polity", "minority", "minority_share"])
        w.writerows(sim.city_ts)
    with open(os.path.join(out, "polities.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "people", "lineage", "peoples_ruled", "founded",
                    "ended", "years", "parent", "peak_cells", "peak_km2",
                    "peak_year", "peak_cities", "peak_pop", "capital_lon",
                    "capital_lat", "peak_foreign_share"])
        for p in sim.polities.values():
            end = p["ended"] if p["ended"] is not None else sim.year
            cap = p["capital"]
            km2 = sim.W.area[p["peak_mask"]].sum() if p["peak_mask"] \
                is not None else ""
            w.writerow([p["id"], sim.keys[p["culture"]], f"L{p['lin']}",
                        " ".join(sim.keys[c] for c in sorted(p["peoples"])),
                        p["founded"],
                        p["ended"], end - p["founded"], p["parent"],
                        p["peak_cells"], km2 and int(km2), p["peak_year"],
                        p["peak_cities"], int(p["peak_pop"]),
                        f"{sim.W.lon[cap]:.2f}", f"{sim.W.lat[cap]:.2f}",
                        round(p.get("peak_foreign", 0.0), 3)])
    with open(os.path.join(out, "timeseries.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sim.ts[0]))
        w.writeheader()
        w.writerows(sim.ts)
    if sim.price_rows:
        with open(os.path.join(out, "price.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(sim.price_rows[0]))
            w.writeheader()
            w.writerows(sim.price_rows)
    if "diagnostics" in sim.on:
        write_checks(sim, os.path.join(out, "checks.txt"))
    np.savez_compressed(os.path.join(out, "final_state.npz"),
                        row=sim.W.row, col=sim.W.col, pop=sim.pop,
                        people=sim.cul, lineage=sim.lin, polity=sim.cell_pol,
                        city_years=sim.city_years, city_peak=sim.city_peak,
                        road=sim.road, improvements=sim.imp, land=sim.land,
                        minority_people=sim.mcul, minority_lineage=sim.mlin,
                        minority_pop=sim.mpop, waste=sim.waste,
                        salt=sim.salt,
                        river=sim.W.river, flow_to=sim.W.flow,
                        **({} if "dragons" not in sim.on else dict(
                            dragon_home=sim.dhome, dragon_ally=sim.dally,
                            dragon_age=sim.dage, dragon_tol=sim.dtol,
                            dragon_viol=sim.dviol, dragon_str=sim.dstr)))
    if "dragons" in sim.on:
        rows = sim.dragon_hist
        with open(os.path.join(out, "dragons.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(out, "run.json"), "w") as fh:
        json.dump(dict(seed=sim.seed, years=sim.years, dt=DT,
                       overrides=getattr(sim, "overrides", []),
                       peoples=sim.P, vary=sim.vary, starts=sim.starts,
                       start_vary=sim.start_vary, drift=sim.drift,
                       start_pool=sim.start_pool,
                       cluster_km=sim.cluster_km,
                       settle_drift=sim.settle_drift,
                       size_food=sim.size_food, city_pop=CITY_POP,
                       start_mode=sim.start_mode,
                       wander_steps=sim.wander_steps,
                       city_cap=(CITY_CAP0, CITY_CAP1) if CITY_CAP else None,
                       dragon_penalty=DRAGON_PEN, dragon_shun=DRAGON_SHUN,
                       features=sorted(sim.on)), fh, indent=1,
                  default=str)
    with open(os.path.join(out, "posts.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["planter", "host", "city", "lon", "lat", "year",
                    "people_planter", "people_host"])
        for k, (o, c, y) in sorted(sim.posts.items()):
            h = k[1] if k[0] == o else k[0]
            if o not in sim.polities or h not in sim.polities:
                continue
            w.writerow([o, h, c, f"{sim.W.lon[c]:.2f}", f"{sim.W.lat[c]:.2f}",
                        y, sim.keys[sim.polities[o]["culture"]],
                        sim.keys[sim.polities[h]["culture"]]])
    if fr:
        # 2x2 final.png and wars.png (figures.py); a failure there must
        # not lose the run's other outputs
        try:
            import figures
            figures.compose(out)
        except Exception as e:  # noqa: BLE001
            print(f"figures.py failed ({e!r}); final_maps.png kept")


def main():
    global CITY_POP, CITY_CAP, CITY_CAP0, CITY_CAP1, DRAGON_PEN, DRAGON_SHUN
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=6000)
    ap.add_argument("--frame-every", type=int, default=20,
                    help="ticks between animation frames")
    ap.add_argument("--homelands", choices=["continents", "anywhere"],
                    default="continents",
                    help="continents: founders start on the two large "
                    "landmasses so peoples meet; anywhere: any good site")
    ap.add_argument("--vary", type=float, default=0.0,
                    help="per-run trait jitter (0 = peoples.py as written; "
                    "0.3 = strong)")
    ap.add_argument("--peoples", default="peoples",
                    help="module in sim/ defining PEOPLES "
                    "(e.g. peoples_fantasy)")
    ap.add_argument("--start-pool", type=float, default=0.02,
                    help="share of habitable cells founders may start in "
                    "(0 = only the best ~60 sites; 0.3 = wide)")
    ap.add_argument("--starts", type=int, default=3,
                    help="founding groups per people (a roster entry's "
                    "'starts' overrides)")
    ap.add_argument("--start-vary", type=float, default=0.05,
                    help="trait jitter between a people's founding groups")
    ap.add_argument("--drift", type=float, default=0.06,
                    help="trait mutation when a daughter lineage splits off")
    ap.add_argument("--cluster-km", type=float, default=0,
                    help="if >0, a people's later groups start within this "
                    "distance of its first; 0 = anywhere")
    ap.add_argument("--settle-drift", type=float, default=0.03,
                    help="trait mutation when a lineage settles a new 5-deg "
                    "region (founds a daughter lineage); 0 = off")
    ap.add_argument("--size-food", choices=["none", "kleiber"],
                    default="kleiber",
                    help="kleiber: each head eats size**0.75 humans' food, "
                    "so large peoples live sparser")
    ap.add_argument("--city-pop", type=float, default=CITY_POP,
                    help="food-equivalent cell population that founds a "
                    "city (a roster `city` factor scales it per people)")
    ap.add_argument("--city-cap", type=float, nargs=2, default=None,
                    metavar=("CAP0", "CAP1"),
                    help="turn on the city size cap = city-pop * (CAP0 + "
                    "CAP1 * admin^2); off by default (the old runs used 3 40)")
    ap.add_argument("--start-mode", choices=["wander", "score"],
                    default="wander",
                    help="wander: founders random-walk toward suitable land "
                    "before the run; score: pick sites by suitability")
    ap.add_argument("--wander-steps", type=int, default=2000)
    ap.add_argument("--dragon-shun", type=float, default=DRAGON_SHUN,
                    help="dragons do not settle near cells holding this "
                    "share of their ward size (0 = off)")
    ap.add_argument("--dragon-penalty", type=float, default=DRAGON_PEN,
                    help="cut in the yearly growth rate per unit of dragon "
                    "hazard at the worst group size (dragons feature)")
    ap.add_argument("--off", default="",
                    help="structural mechanics to switch off, comma-"
                    "separated, or 'all': " + ",".join(FEATURES))
    ap.add_argument("--set", action="append", default=[],
                    metavar="NAME=VALUE",
                    help="override a numeric constant (repeatable)")
    ap.add_argument("--shuffle-sites", action="store_true",
                    help="draw resource sites and hearths from the run seed "
                    "instead of sites.json")
    ap.add_argument("--sites", default="sites.json",
                    help="site file (sites_v2.json: landmass quotas, more "
                    "kinds, precious metals)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    for kv in a.set:
        k, v = kv.split("=", 1)
        if k not in globals() or not isinstance(globals()[k], (int, float)):
            ap.error(f"--set: no numeric constant {k}")
        globals()[k] = type(globals()[k])(float(v)) \
            if isinstance(globals()[k], float) else int(v)
    off = FEATURES if a.off == "all" else \
        [x for x in a.off.split(",") if x]
    bad = set(off) - set(FEATURES)
    if bad:
        ap.error(f"unknown feature(s): {', '.join(sorted(bad))}")
    CITY_POP = a.city_pop
    DRAGON_PEN = a.dragon_penalty
    DRAGON_SHUN = a.dragon_shun
    if a.city_cap is not None:
        CITY_CAP = True
        CITY_CAP0, CITY_CAP1 = a.city_cap
    out = a.out or os.path.join(HERE, "runs", f"seed{a.seed}")
    t0 = time.time()
    world = World()
    print(f"world: {world.N} land cells, loaded in {time.time()-t0:.1f}s")
    sim = Sim(world, seed=a.seed, years=a.years,
              frame_every=a.frame_every, out=out, homelands=a.homelands,
              peoples=vary_peoples(importlib.import_module(
                  a.peoples).PEOPLES, a.seed, a.vary),
              start_pool=a.start_pool, starts=a.starts,
              start_vary=a.start_vary, drift=a.drift,
              cluster_km=a.cluster_km, settle_drift=a.settle_drift,
              size_food=a.size_food, start_mode=a.start_mode,
              wander_steps=a.wander_steps, off=off,
              shuffle_sites=a.shuffle_sites, sites=a.sites)
    sim.vary = a.vary
    sim.overrides = a.set
    for p in sim.P:
        print(f"  {p['key']} {p['label']:16s} r={p['r']:.4f} " +
              " ".join(f"{t[:4]}={p.get(t, 0.5):.2f}" for t in TRAITS))
    sim.run()
    write_outputs(sim, out)
    print(f"done in {time.time()-t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
