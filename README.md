# Domestic Sewage Filtration System - 3D Mechanical Model

Parametric Blender model of a **domestic sewage filtration system**, built from
the workflow described in
`Domestic Sewage Filtration System (Black & White).pdf`.

---

## 1. READ THIS FIRST - scope and honesty statement

The source PDF is a **12-slide concept presentation**. It names the process
stages and the filtration media, but it contains **no dimensions, no flow
rates, no material grades, no motor specification and no performance data**.

Therefore:

* Every number in `design_parameters.json` and in the `P = {...}` block of
  `build_filtration_system.py` is a **PROVISIONAL prototype-scale value chosen
  by the modeller**. It is **not** source-specified and it is **not**
  construction-certified.
* No structural load rating, no hydraulic capacity and no treatment
  efficiency is claimed anywhere in this project.
* The translucent blue/brown volumes and the animated arrows are **visual
  flow indicators only**. Water colour does **not** indicate water quality.
* No microbiological or biological purification is modelled or implied. This
  is a purely **mechanical** (screening / settling / cloth polishing) train.
* The hopper slope, mesh aperture, filter cloth specification, motor power and
  conveyor speed all need engineering verification before any build.

### Documented vs proposed

| Status | Meaning |
|---|---|
| `[DOC]` | Feature explicitly named in the source PDF. |
| `[PROP]` | Mechanical addition made by this design so the documented feature is buildable, serviceable and safe. Not in the source. |

Every object carries a custom property `design_status` with one of these two
values, so you can filter the outliner and the CSV by provenance.

---

## 2. What the source document specifies (and what it does not)

**Documented, qualitative only:**

1. **Stage 1 - Iron Mesh Filtration** - "heavy-duty rust-resistant iron wire
   mesh"; retains polythenes, plastic packaging and bulk waste; it is the
   first barrier the sewage meets.
2. **Stage 2 - Mud & Sediment Filtration** - settling of fine sand, silt and
   dense mud; secondary filter is **multi-grade gravel + fine-pore media**;
   reduces turbidity to prepare the water for polishing.
3. **Stage 3 - Fabric Polishing System** - **high-tensile porous synthetic
   fabric**; captures micro-particulates and residual cloudiness; produces
   polished water.
4. **Conveyor system** - "motorized belt conveyor with scraper blades",
   continuous or sensor-triggered rotation; lifts and shifts collected debris
   from the chambers into **secure disposal bins**.
5. **Final output** - a **final output valve** on the polished water line.
6. Cross-cutting intent - gravity-assisted flow, modular design, low power
   footprint, and (future scope) IoT sludge level sensing.

**NOT specified by the source - filled here with provisional parameters:**
every dimension, mesh aperture, wall thickness, gravel grading, cloth spec,
pipe size, roller diameter, motor power, belt speed, hopper angle, drain size
and service clearance.

---

## 3. Process flow implemented in the model

```
 raw sewage
     |
     v
 PIPE_INLET_RAW (DN150)
     |
 [ INLET CHAMBER ]  -- SCREEN_01 (inclined iron mesh cassette, lift-out)
     |                    \  retained plastics -> CONVEYOR_01_BELT
     | weir overflow  (weir crest z=1300 mm)
     v
 [ TANK_01_SETTLING ]   sloped hopper -> sludge blanket -> BIN_01 sludge bay
     |                     (via PIPE_SLUDGE_DRAIN DN80 + isolation valve)
     | clarified draw-off from UNDER the gravel bed
     v
 [ MEDIA_02_GRAVEL_L1..L3 ]  multi-grade secondary bed [DOC]
     |
 [ FILTER_02_FABRIC ]  framed cloth element, removable through the top cover
     |
 PIPE_OUTLET (DN100, distinct blue) -- VALVE_FINAL_OUTPUT --> discharge
```

**Solids path:** screen-retained plastics drop onto `CONVEYOR_01_BELT` ->
`CONVEYOR_01_SCRAPER_BLADE` -> `CONVEYOR_01_DISCHARGE_CHUTE` ->
`BIN_01` solids bay. Drained sludge travels the separate `PIPE_SLUDGE_DRAIN`
into the `BIN_01` sludge bay. The two are kept visually and spatially
distinct on purpose.

---

## 4. Files in this folder

| File | What it is |
|---|---|
| `domestic_sewage_filtration_system.blend` | The editable Blender project. |
| `build_filtration_system.py` | The full reproducible build script. |
| `assembly_overview.png` | Isometric presentation render. |
| `exploded_assembly.png` | Exploded assembly render. |
| `sectional_view.png` | Cutaway of the tank and filtration internals. |
| `front_view.png` / `side_view.png` / `top_view.png` | Orthographic engineering views with dimensions and labels. |
| `component_inventory.csv` | Component name, subsystem, qty, provisional material, source status, notes. |
| `design_parameters.json` | Every editable provisional dimension plus the derived values. |
| `README.md` | This file. |
| `exports/stl/*.stl` | Per-component STL for individual parts. |
| `exports/*.obj`, `exports/*.glb` | Whole-assembly interchange formats. |

---

## 5. How to run

```bash
# full build: geometry + renders + reports + exports
"/path/to/blender" --background --python build_filtration_system.py

# fast preview (half resolution, low samples)
"/path/to/blender" --background --python build_filtration_system.py -- --quick

# skip the animation setup
"/path/to/blender" --background --python build_filtration_system.py -- --no-anim

# or, interactively:
#   open Blender > Scripting > open build_filtration_system.py > Run Script
```

Blender version used for the committed renders: **5.2.2 LTS**.

---

## 6. How to edit the design

Every dimension lives in **one** block near the top of
`build_filtration_system.py`:

```python
P = {
    "overall_length": 3400.0,
    "settling_len": 1180.0,
    "mesh_pitch": 25.0,
    ...
}
```

* Units are **millimetres**; `MM = 0.001` converts to Blender units.
* Change a tank size and the dependent geometry (walls, rim, lid, water body,
  supports, gravel cell) follows, because the builders read the same keys.
* Rerun the script. It performs a `read_factory_settings(use_empty=True)` at the
  start, so the rebuild is deterministic and idempotent - there is no
  duplicated-geometry accumulation.
* To keep a .blend you have edited by hand, **do not** rerun the script over
  it; copy it first.

### Collections

```
00_Frame_and_Skid                    structural skid, posts, feet, deck
01_Inlet_and_Iron_Mesh_Screen         inlet chamber, screen cassette, rails
02_Sedimentation_Chamber              TANK_01 walls, hopper, lid, sludge
                                      MEDIA_02 gravel layers (documented)
03_Fabric_Polishing_Chamber           FILTER_02 chamber, cloth, cover, frame
04_Conveyor_and_Waste_Handling        belt, rollers, scraper, motor, guards
05_Piping_and_Outlet                  inlet / transfer / fabric / outlet /
                                      sludge runs, flanges, valves
06_Sludge_and_Waste_Bin               BIN_01 solids bay + sludge bay
07_Flow_Indicators                    schematic direction arrows
08_Annotations                        dimensions and labels (view-specific)
09_Cameras_and_Lights                 cameras, sun and area lights
```

Removable / moving parts (screen cassette, inspection lid, cloth element,
top cover, belt, cleats, scraper blade, bin) are **separate objects**, so each
can be selected, animated or exported on its own.

---

## 7. Maintenance access built into the model

| Service task | Access provided | Clearance parameter |
|---|---|---|
| Remove and clean the iron mesh screen | Vertical lift out of guide rails; clamping brackets release; lift handle | `screen_lift_clearance` = 250 mm |
| Inspect / clean the settling chamber | Bolted removable top inspection lid (10 fasteners, 2 lifting eyes) | lid `(ln)x(wd)x(thk)` = `settling_len/wid/lid_thk` |
| Drain the sludge hopper | DN80 bottom drain + gate valve to the bin sludge bay | `hopper_drain_dia` = 80 mm |
| Replace the cloth filter element | Top cover unbolts; element lifts vertically on 4 loops | `filter_lift_clearance` = 450 mm |
| Tension the conveyor belt | Two take-up screws with lock nuts at the tail roller | `tensioner_stroke` = 60 mm |
| Empty the waste bin | Fork pockets + drag handle, bin lifts off the deck | `bin_len/bin_wid/bin_hgt` |

---

## 8. Build validation actually performed

```
objects in file      : 395
mesh objects         : 385
triangles            : 13424
empty mesh objects   : 0
degenerate-face objs : 0

assembly presence:
   01 Inlet + iron mesh screen    OK
   02 Sedimentation chamber       OK
   02b Gravel secondary bed       OK
   03 Fabric polishing            OK
   04 Conveyor                    OK
   05 Piping                      OK
   06 Collection bin              OK
   07 Structure                   OK

assembly bbox (m)   : X 4.17  Y 2.05  Z 1.80
assembly bbox min    : (-0.47, -1.05, -0.06)
assembly bbox max    : (3.70, 1.00, 1.74)

collections:
   00_Frame_and_Skid                           83 objects
   01_Inlet_and_Iron_Mesh_Screen               29 objects
   02_Sedimentation_Chamber                    41 objects
   03_Fabric_Polishing_Chamber                 59 objects
   04_Conveyor_and_Waste_Handling              76 objects
   05_Piping_and_Outlet                        69 objects
   06_Sludge_and_Waste_Bin                     17 objects
   07_Flow_Indicators                          16 objects
   08_Annotations                               0 objects
   09_Cameras_and_Lights                        5 objects

ISSUES FOUND: 0 - all checks passed
```

* The script was executed head-less and exited with no Python error.
* The saved `.blend` was re-opened head-less and the collections/objects were
  counted and checked.
* Every deliverable file was checked for existence and non-zero size.
* The mesh was checked for non-manifold / loose geometry on the key vessels.

---

## 9. Known limitations and unresolved decisions

1. **No calculations.** Tank sizing, frame sizing and motor selection are
   *assumed*, not calculated. A real project needs a flow budget, a solids
   loading check, a head-loss check and a structural check.
2. **Hopper slope 55 deg** is aggressive for drained sand (typical drained
   repose is 35-45 deg). It was chosen for self-cleaning; it needs a
   geotechnical/handling check.
3. **No pumping.** The document implies gravity-assisted flow; this model has
   no pump. A domestic installation at this scale would very likely need one,
   and its duty point would change every elevation shown.
4. **No odour control.** A real chambered system needs a vent/odour control
   and a sealed lid seal (a gasket is modelled on the fabric chamber only).
5. **Conveyor duty.** Solids that pass a %(mesh)g mm aperture and settle in a
   tank hopper do not normally need a belt conveyor to reach a bin; the
   conveyor in the source document is presented as handling *screen-retained*
   plastics. That is how it is modelled here. If the intent was hydraulic
   sludge pumping instead, this assembly would need to be reconfigured.
6. **Fabric element** is modelled as two flat framed cloth panels for clarity
   and printability, not as a pleated cartridge or a rotating drum.
7. **No treatment performance is implied.** Filtering, screening and cloth
   polishing do not disinfect water and do not remove dissolved pollutants.
8. **Explode / section renders are presentation aids**; the cutaway uses
   temporary boolean modifiers that are removed again after rendering, so the
   saved `.blend` contains clean, unmodified geometry.

---

## 10. Where to go next for a real build

* Replace every value in `P` with project-true dimensions.
* Run a solids loading + settling velocity check on `TANK_01`
  (target surface overflow rate / horizontal velocity).
* Select the mesh aperture against the actual debris size distribution.
* Specify the cloth (areal weight, pore size, permeability, chemical
  compatibility) and add a backwash or replace-and-wash provision.
* Add a pump, an odour vent, a flow meter, the IoT sludge level sensor the
  document mentions in future scope, and an electrical enclosure with an
  interlocked guard.
* Have the frame, hoppers and conveyor supports structurally checked before
  fabrication.
