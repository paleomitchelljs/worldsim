# WP3: visualization

**Goal.** See what a run does: frames at any cadence without rerunning,
maps that do not distort area, state colours that show turnover, and a
format that carries more than a 16-frame GIF. No mechanic changes.

**Why.**
- The user judges dynamics by watching `history.gif`. Test runs make one
  frame per 500 years (`--frame-every 100`), 200 colours, at three-quarter
  size.
- `render()` is called inside the run loop and frames are held in memory,
  so a different view or cadence means another 14-minute run.
- Maps are the raw 0.5-degree grid (plate carrée). East-west distances
  are stretched by 1 / cos(latitude): 1.4x at 45°, 2x at 60°. Large
  northern and southern states look larger than they are.
- A state's colour is its people's colour with ±15 jitter
  (`states.polity_color`). In `arh_seed101` 75-85% of ruled cells changed
  state every 500 years, mostly to successors of the same people
  (`docs/open-questions.md`, 2026-11-06), and almost none of that shows.

Read first: `wsim/render.py`, `figures.py` (`flat_peoples`, `map_figure`,
`tradewars_gif`), `wsim/sim.py` (`snapshot`, `run`), `wsim/output.py`,
`docs/running.md` (outputs table).

## Stage A: snapshots

1. Make the snapshot cadence an option (`--hist-every`, in ticks). Default
   C: 5 (25 years), down from `HIST_EVERY` = 20.
2. Store per snapshot: people (int8), lineage (int32), polity (int32),
   minority people (int8), population as float16 of log1p (decode with
   expm1; check the round-trip error is under 1%), herding flag, and the
   per-snapshot tables already kept (live states, trade ties). Add the
   city table (cell, id, size, polity, capital flag) so a renderer needs
   nothing else.
3. These arrays change slowly, so `np.savez_compressed` should hold 320
   snapshots in a few tens of MB. Measure and report the size. If it
   passes about 60 MB, store polity and lineage as changes from the
   previous snapshot.
4. Snapshots read state only.

## Stage B: a separate renderer, with an equal-area projection

1. `render_run.py RUN --layer states|peoples|density|lineages
   --every N --proj mollweide|platecarree --format png|mp4|gif`.
   It reads `history.npz` and the cached world (WP0 stage E) and never
   imports the simulation step.
2. Move the drawing code out of `wsim/render.py` into functions that take
   a snapshot, so the live `render(sim)` (kept for `final_maps.png`) and
   the offline renderer share it.
3. Projection without new packages: for each output pixel compute the
   inverse projection to (lon, lat), then the source grid cell; store that
   index array once and every frame is a single fancy-index. Mollweide has
   a closed-form inverse:
   `theta = arcsin(y / (sqrt(2) R))`,
   `lat = arcsin((2 theta + sin 2 theta) / pi)`,
   `lon = lon0 + pi x / (2 sqrt(2) R cos theta)`;
   pixels outside the ellipse are background. City dots, labels and
   borders go through the forward projection (solve
   `2 theta + sin 2 theta = pi sin lat` by a few Newton steps).
4. Keep plate carrée as an option: the source maps in `art/` and the
   draft book maps are drawn that way, and overlays need to match.
5. Draw borders from the projected label image, at output resolution, so
   they stay one pixel wide.

## Stage C: state colours and layers of change

1. **Colours.** A state keeps one colour for life. Choose it at founding:
   the hue stays in the ruling people's family (so the peoples still
   read), while lightness and chroma vary widely; then adjust until it
   differs from every neighbouring state's colour by a minimum distance
   (greedy, over `self.adj` at render time). A successor state must not
   inherit its parent's colour. Do this in the renderer from polity ids,
   so old runs benefit and the simulation is untouched (`polity_color`
   draws from `self.rng`; do not change how many numbers it draws).
2. **Years since the cell last changed state**, and **years since it last
   changed people**: two layers computed from the snapshots. Young
   borders and contested regions show at a glance.
3. **Turnover strip.** Under the map, a strip chart per landmass group
   (`landmasses.py`) of the share of ruled cells that changed state in
   the last 100 years.
4. Label the ten largest states by id at their largest piece's centre,
   not only at the capital.

## Stage D: video and an optional viewer

1. MP4 through `ffmpeg` (installed): one frame per snapshot, about 8
   frames per second, H.264, `-pix_fmt yuv420p`. Keep a GIF option for
   places that cannot play video.
2. A two-layer video (states above, peoples below) to replace
   `history.gif`'s layout, and single-layer videos per landmass group at
   higher zoom.
3. **Optional (ask the user first).** One self-contained HTML page per
   run: a time slider, a layer switch, and a click on a city or state that
   lists its rows from `cities.csv` / `polities.csv` and its events from
   `events.jsonl`. The data is small enough to embed. This is the tool
   for reading a history rather than checking one; build it only if the
   user wants it.

## Checking

Look at the pictures. Put one before/after frame pair of the same
snapshot in the handoff.
