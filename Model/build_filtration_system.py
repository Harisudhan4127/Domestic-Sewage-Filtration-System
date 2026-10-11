#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 DOMESTIC SEWAGE FILTRATION SYSTEM  -  low-poly parametric Blender build script
================================================================================
 Run:
     blender --background --python build_filtration_system.py

 Produces (in the directory holding this script):
     domestic_sewage_filtration_system.blend
     assembly_overview.png      orthographic isometric, fully assembled
     exploded_view.png         orthographic isometric, components pulled apart
     section_view.png          orthographic front cut-away (near-clip section)

--------------------------------------------------------------------------------
 WHAT THE SOURCE DOCUMENT ACTUALLY SPECIFIES
--------------------------------------------------------------------------------
 "Domestic Sewage Filtration System (Black & White).pdf" - 12 scanned slides with
 no text layer, read page by page. The document is *qualitative only*: it names
 the process stages and the intent of each stage, but gives **no dimensions,
 no flow rates, no materials grades and no performance data whatsoever**.

   Stage 01 - IRON MESH FILTRATION
       "first encounter a heavy-duty iron mesh screen"
       material  : heavy-duty rust-resistant iron wire mesh
       retains   : bulk plastics, polythenes, plastic packaging, wrappers
   Stage 02 - MUD & SEDIMENT FILTRATION
       "settles and extracts fine sand, silt and dense mud particles"
       secondary filter : multi-grade gravel + fine-pore media
       outcome : dramatically reduced turbidity, water ready for polishing
   Stage 03 - FABRIC POLISHING SYSTEM
       material : "high-tensile porous synthetic fabric filter"
       result   : "polished water free from floating impurities"
   AUTOMATION - CONVEYOR SYSTEM
       "motorized belt conveyor with scraper blades"
       "continuous or sensor-triggered rotation"
       lifts/shifts collected debris from the chambers into "secure disposal bins"
   FINAL OUTPUT
       "final output valve" -> clear low-turbidity water channelled to streams
   CROSS-CUTTING CLAIMS
       gravity-assisted flow, low power footprint, modular design,
       IoT sensors for sludge level detection (stated as future scope)

--------------------------------------------------------------------------------
 DOCUMENTED vs PROPOSED
--------------------------------------------------------------------------------
   [DOC]  = named in the source PDF
   [PROP] = mechanical addition invented here so the documented feature is
            buildable/serviceable. Tagged on the object as custom property
            "design_status" and listed in the in-file README text block.

--------------------------------------------------------------------------------
 UNITS
--------------------------------------------------------------------------------
   All provisional dimensions below are in MILLIMETRES (design reference unit).
   Blender works in metres; MM converts. Axes:
       X = process flow direction (inlet -> outlet)
       Y = machine width (negative Y = service side / conveyor)
       Z = up, Z = 0 is the floor plane
================================================================================
"""

import math
import os
import sys
import bpy
from mathutils import Matrix, Vector

# ==============================================================================
# 1. PROVISIONAL PARAMETERS  (edit these - nothing below is source-derived)
# ==============================================================================

MM = 0.001                      # millimetre -> metre

# ---- base frame ---------------------------------------------------------------
FRAME_TOP_Z        = 700.0      # top face of the support frame (tank datum)
FRAME_BEAM         = 120.0      # square beam section
FRAME_X0, FRAME_X1 = -3100.0, 2800.0
FRAME_Y0, FRAME_Y1 = -1600.0, 1000.0
FRAME_LEG_COUNT    = 4          # legs per long side

# ---- shell / wall -------------------------------------------------------------
WALL_T             = 20.0       # tank wall thickness (provisional)

# ---- stage 01 : iron mesh screen chamber --------------------------------------
S1_CX              = -2000.0    # centre X
S1_L, S1_W, S1_H   = 800.0, 1000.0, 900.0
SCREEN_TILT        = 55.0       # deg, screen inclination from horizontal
SCREEN_BARS        = 9          # bars each way (thin bars arranged as a grid)
SCREEN_BAR_T       = 18.0
SCREEN_FRAME_BAR   = 45.0       # heavier perimeter frame of the screen panel
SCREEN_GAP         = 120.0      # clearance between screen top edge and chamber rim

# ---- stage 02 : sedimentation tank --------------------------------------------
S2_CX              = -800.0
S2_L, S2_W, S2_H   = 1400.0, 1400.0, 1000.0
S2_WATER_DEPTH     = 780.0      # water depth inside the tank
S2_SLUDGE_DEPTH    = 170.0      # settled sludge layer on the floor
S2_BAFFLE_X        = -500.0     # internal flow-damping baffle
S2_BAFFLE_H        = 620.0
S2_MEDIA_BED       = True       # [PROP] multi-grade media bed before the weir
S2_MEDIA_DEPTH     = 220.0

# ---- stage 03 : fabric filter chamber -----------------------------------------
S3_CX              = 700.0
S3_L, S3_W, S3_H   = 1200.0, 1000.0, 900.0
S3_WATER_DEPTH     = 520.0
CLOTH_TILT         = 20.0       # deg from vertical, cloth panel lean
CLOTH_T            = 12.0       # cloth panel thickness

# ---- piping -------------------------------------------------------------------
INLET_X0, INLET_X1 = -3020.0, -2400.0
INLET_D            = 200.0
INLET_Z            = 1250.0
OUTLET_X0, OUTLET_X1 = 1300.0, 2620.0
OUTLET_D           = 180.0
OUTLET_Z           = 1180.0
VALVE_X            = 1980.0     # clean-water outlet valve
SLUDGE_DRAIN_D     = 120.0
VALVE_BODY_R       = 190.0      # valve body radius
VALVE_HANDLE_R     = 26.0

# ---- conveyor (beside the solids collection area) ----------------------------
CONV_Y             = -1150.0    # belt centre line (service side)
CONV_X0, CONV_X1   = -900.0, 900.0
CONV_BELT_W        = 520.0
CONV_BELT_T        = 26.0
CONV_ROLLER_R      = 95.0
CONV_BELT_Z        = 780.0      # top belt run height
CONV_LEG_W         = 70.0
SCRAPER_COUNT      = 5          # scraper blades on the belt (per source doc)
MOTOR_SX, MOTOR_SY, MOTOR_SZ = 420.0, 260.0, 260.0

# ---- waste bin ----------------------------------------------------------------
BIN_X, BIN_Y       = 1330.0, CONV_Y
BIN_SX, BIN_SY, BIN_SZ = 700.0, 700.0, 560.0
BIN_WALL_T         = 30.0
BIN_FILL_H         = 300.0

# ---- labels / annotations -----------------------------------------------------
LBL_SIZE           = 90.0       # default label height, millimetres

# ---- render -------------------------------------------------------------------
RES_X, RES_Y       = 1920, 1080
SAMPLES             = 64
CAM_DIST           = 14.0
CAM_CENTER         = Vector((-150.0, -300.0, 900.0)) * MM

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- explode offsets (metres, per collection) ---------------------------------
EXPLODE = {
    "02_Inlet":            Vector((-1.30,  0.00,  0.55)),
    "03_Screen_Chamber":   Vector((-0.45,  0.00,  1.15)),
    "04_Sedimentation":    Vector(( 0.00,  0.00,  1.15)),
    "05_Fabric_Filter":    Vector(( 0.55,  0.00,  1.15)),
    "06_Outlet":           Vector(( 1.30,  0.00,  0.55)),
    "07_Conveyor":         Vector(( 0.00, -1.10,  0.15)),
    "01_Base_Frame":       Vector(( 0.00,  0.00, -0.30)),
}


# ==============================================================================
# 2. SCENE / COLLECTION / MATERIAL HELPERS
# ==============================================================================

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    return scene


def make_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def mat(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
    """Create (or fetch) a simple Principled BSDF material."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    rgba = (color[0], color[1], color[2], alpha)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    m.diffuse_color = rgba
    return m


PALETTE = {}


def build_materials():
    PALETTE["frame"]   = mat("M_Frame_SteelGrey",   (0.36, 0.39, 0.43), 0.75, 0.45)
    PALETTE["tank"]    = mat("M_Tank_LightGrey",     (0.62, 0.65, 0.67), 0.10, 0.55)
    PALETTE["pipe"]    = mat("M_Pipe_Blue",          (0.08, 0.32, 0.64), 0.25, 0.40)
    PALETTE["clean"]   = mat("M_Pipe_CleanWater",    (0.10, 0.58, 0.80), 0.15, 0.30)
    PALETTE["water"]   = mat("M_Water_Turbid",       (0.20, 0.45, 0.42), 0.00, 0.15, 0.40)
    PALETTE["sludge"]  = mat("M_Sludge_Brown",       (0.32, 0.19, 0.09), 0.00, 0.80)
    PALETTE["fabric"]  = mat("M_Fabric_Filter",      (0.90, 0.88, 0.80), 0.00, 0.85)
    PALETTE["clothfr"] = mat("M_Fabric_Frame",       (0.48, 0.50, 0.53), 0.60, 0.40)
    PALETTE["belt"]    = mat("M_Belt_DarkGrey",      (0.14, 0.14, 0.16), 0.00, 0.75)
    PALETTE["roller"]  = mat("M_Roller_Metal",       (0.55, 0.57, 0.60), 0.80, 0.30)
    PALETTE["motor"]   = mat("M_Motor_Blue",         (0.14, 0.26, 0.46), 0.30, 0.45)
    PALETTE["bin"]     = mat("M_Bin_Grey",           (0.44, 0.47, 0.49), 0.20, 0.60)
    PALETTE["waste"]   = mat("M_Captured_Waste",     (0.28, 0.28, 0.24), 0.00, 0.90)
    PALETTE["media"]   = mat("M_Filter_Media_Gravel",(0.58, 0.54, 0.45), 0.00, 0.85)
    PALETTE["arrow"]   = mat("M_Flow_Arrow_Blue",    (0.04, 0.38, 0.76), 0.00, 0.40)
    PALETTE["text"]    = mat("M_Label_Text",         (0.07, 0.08, 0.10), 0.00, 0.60)
    PALETTE["ground"]  = mat("M_Ground_LightGrey",   (0.80, 0.81, 0.82), 0.00, 0.75)


def link(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def tag(obj, status, note):
    """Record DOC / PROP provenance on the object itself."""
    obj["design_status"] = status
    obj["design_note"] = note
    return obj


def shade_smooth_off(obj):
    if obj.type == 'MESH':
        for p in obj.data.polygons:
            p.use_smooth = False


# ==============================================================================
# 3. PRIMITIVE BUILDERS  (all dimensions in millimetres unless noted)
# ==============================================================================

def box(name, size, loc, col, material, rot=(0, 0, 0), status="[DOC]", note=""):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=Vector(loc) * MM)
    o = bpy.context.active_object
    o.name = name
    o.scale = Vector(size) * MM
    o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    link(o, col)
    o.data.materials.append(material)
    shade_smooth_off(o)
    return tag(o, status, note)


def cyl(name, radius, depth, loc, col, material, rot=(0, 0, 0), verts=24,
        status="[DOC]", note=""):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius * MM, depth=depth * MM,
                                         vertices=verts, location=Vector(loc) * MM)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = rot
    link(o, col)
    o.data.materials.append(material)
    shade_smooth_off(o)
    return tag(o, status, note)


def pipe_between(name, p0, p1, diameter, col, material, verts=20,
                 status="[DOC]", note=""):
    """Cylinder spanning two world points (millimetres)."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    mid = (a + b) * 0.5
    q = d.to_track_quat('Z', 'Y')
    o = cyl(name, diameter * 0.5, d.length, mid, col, material,
            rot=q.to_euler(), verts=verts, status=status, note=note)
    return o


def join_objects(objects, name, col):
    """Join a list of meshes into the first one and re-centre its origin.

    Re-centring matters: several parts are built flat around the origin and are
    only rotated into place *after* the join, so the object's origin has to sit
    in the middle of the joined geometry. World position is preserved.
    """
    objects = [o for o in objects if o]
    if not objects:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name

    me = o.data
    if len(me.vertices):
        mn = Vector((min(v.co[i] for v in me.vertices) for i in range(3)))
        mx = Vector((max(v.co[i] for v in me.vertices) for i in range(3)))
        centre = (mn + mx) * 0.5
        me.transform(Matrix.Translation(-centre))
        o.location = o.location + centre

    o["design_status"] = "[DOC]"
    return o


# In this isometric view the world direction (1, -1, 0) projects exactly onto the
# screen's horizontal axis, so rotating flat text by -45 deg about Z makes every
# label read perfectly horizontally. Labels can then be spaced along that axis.
LABEL_ROT = (0.0, 0.0, math.radians(-45.0))


def text_label(name, body, loc, col, size=LBL_SIZE, rot=LABEL_ROT,
               align='CENTER', status="[DOC]", note="", home=None):
    """Flat text object, aligned to the isometric screen-horizontal axis."""
    bpy.ops.object.text_add(location=Vector(loc) * MM, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.body = body
    o.data.size = size * MM
    o.data.align_x = align
    o.data.align_y = 'CENTER'
    o.data.extrude = 0.0
    link(o, col)
    o.data.materials.append(PALETTE["text"])
    if home:
        # so the label travels with its component in the exploded view
        o["explode_home"] = home
    return tag(o, status, note)


def flow_arrow(name, p0, p1, col, shaft_r=42.0, head_r=95.0, head_len=210.0,
               status="[DOC]", note=""):
    """Simple cone+shaft arrow showing the intended flow direction."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    length = d.length
    q = d.to_track_quat('Z', 'Y')
    shaft_len = max(length - head_len, 1.0)
    shaft_mid = a + d * (shaft_len * 0.5 / length)
    s = cyl(name + "_Shaft", shaft_r, shaft_len, shaft_mid, col,
            PALETTE["arrow"], rot=q.to_euler(), verts=14, status=status, note=note)
    bpy.ops.mesh.primitive_cone_add(radius1=head_r * MM, radius2=6.0 * MM,
                                    depth=head_len * MM, vertices=16,
                                    location=(b - d * (head_len * 0.5 / length)) * MM)
    h = bpy.context.active_object
    h.name = name + "_Head"
    h.rotation_euler = q.to_euler()
    link(h, col)
    h.data.materials.append(PALETTE["arrow"])
    shade_smooth_off(h)
    h["design_status"] = status
    # arrows describe the assembled flow path, so they are hidden when exploded
    for o in (s, h):
        o["hide_in_explode"] = True
    return s


# ==============================================================================
# 4. COMPONENT BUILDERS
# ==============================================================================

def open_tank(name, cx, cy, bottom_z, L, W, H, col, t=WALL_T):
    """A rectangular tank built from 5 slabs (floor + 4 walls) - simple & editable."""
    zc = bottom_z + H * 0.5
    parts = [
        box(name + "_Floor", (L, W, t), (cx, cy, bottom_z + t * 0.5), col, PALETTE["tank"]),
        box(name + "_Wall_XL", (t, W, H), (cx - L * 0.5 + t * 0.5, cy, zc), col, PALETTE["tank"]),
        box(name + "_Wall_XR", (t, W, H), (cx + L * 0.5 - t * 0.5, cy, zc), col, PALETTE["tank"]),
        box(name + "_Wall_YB", (L - 2 * t, t, H), (cx, cy - W * 0.5 + t * 0.5, zc), col, PALETTE["tank"]),
        box(name + "_Wall_YT", (L - 2 * t, t, H), (cx, cy + W * 0.5 - t * 0.5, zc), col, PALETTE["tank"]),
    ]
    return join_objects(parts, name, col)


def build_base_frame(col):
    """[PROP] Simple base frame - the source only claims 'modular design'."""
    n = "Frame"
    bx, by = FRAME_BEAM, FRAME_BEAM
    cx = (FRAME_X0 + FRAME_X1) * 0.5
    cy = (FRAME_Y0 + FRAME_Y1) * 0.5
    Lx = FRAME_X1 - FRAME_X0
    Ly = FRAME_Y1 - FRAME_Y0

    parts = []
    zc = FRAME_TOP_Z - bx * 0.5
    # top rails (tanks sit on these)
    parts.append(box(n + "_TopRail_Y0", (Lx, by, bx), (cx, FRAME_Y0 + by * 0.5, zc), col, PALETTE["frame"]))
    parts.append(box(n + "_TopRail_Y1", (Lx, by, bx), (cx, FRAME_Y1 - by * 0.5, zc), col, PALETTE["frame"]))
    # bottom rails
    parts.append(box(n + "_BotRail_Y0", (Lx, by, bx), (cx, FRAME_Y0 + by * 0.5, bx * 0.5), col, PALETTE["frame"]))
    parts.append(box(n + "_BotRail_Y1", (Lx, by, bx), (cx, FRAME_Y1 - by * 0.5, bx * 0.5), col, PALETTE["frame"]))
    # cross members
    for i in range(FRAME_LEG_COUNT + 1):
        x = FRAME_X0 + Lx * i / FRAME_LEG_COUNT
        parts.append(box(f"{n}_Cross_{i}", (bx, Ly, bx), (x, cy, zc), col, PALETTE["frame"]))
    # legs
    for i in range(FRAME_LEG_COUNT + 1):
        x = FRAME_X0 + Lx * i / FRAME_LEG_COUNT
        for j, y in enumerate((FRAME_Y0 + by * 0.5, FRAME_Y1 - by * 0.5)):
            parts.append(box(f"{n}_Leg_{i}_{j}", (bx, bx, FRAME_TOP_Z - bx),
                             (x, y, (FRAME_TOP_Z - bx) * 0.5), col, PALETTE["frame"]))
    return join_objects(parts, "Base_Frame", col)


def build_inlet(col):
    """[DOC] Wastewater inlet - first thing the sewage meets."""
    parts = []
    parts.append(pipe_between("Inlet_Pipe", (INLET_X0, 0, INLET_Z), (INLET_X1, 0, INLET_Z),
                              INLET_D, col, PALETTE["pipe"]))
    parts.append(pipe_between("Inlet_Elbow_Down", (INLET_X1, 0, INLET_Z), (INLET_X1, 0, FRAME_TOP_Z + 500),
                              INLET_D, col, PALETTE["pipe"]))
    parts.append(box("Inlet_Housing", (260.0, 320.0, 260.0),
                     (INLET_X1, 0, FRAME_TOP_Z + 500.0), col, PALETTE["pipe"]))
    return join_objects(parts, "Stage01_Inlet", col)


def build_screen_chamber(col):
    """[DOC] Stage 01 - heavy-duty rust-resistant iron wire mesh screen."""
    cx, cy, bz = S1_CX, 0.0, FRAME_TOP_Z
    tank = open_tank("Screen_Chamber", cx, cy, bz, S1_L, S1_W, S1_H, col)
    tank["design_note"] = "Stage 01 chamber holding the iron mesh screen"

    # ---- inclined mesh panel: thin bars in a grid, built flat then tilted -----
    pw, ph = S1_W - 2 * WALL_T - 60.0, S1_H - 2 * WALL_T - 40.0
    parts = []
    inner_w = pw - 2 * SCREEN_FRAME_BAR
    inner_h = ph - 2 * SCREEN_FRAME_BAR
    span_w = inner_w
    span_h = inner_h * math.cos(math.radians(SCREEN_TILT))
    for i in range(SCREEN_BARS):                       # bars across the width
        x = -inner_w * 0.5 + inner_w * i / max(SCREEN_BARS - 1, 1)
        parts.append(box(f"_Bar_{i}", (SCREEN_BAR_T, span_h, SCREEN_BAR_T),
                         (x, 0, 0), col, PALETTE["frame"]))
    for j in range(SCREEN_BARS):                       # bars up the slope
        y = -span_h * 0.5 + span_h * j / max(SCREEN_BARS - 1, 1)
        parts.append(box(f"_Rib_{j}", (span_w, SCREEN_BAR_T, SCREEN_BAR_T),
                         (0, y, 0), col, PALETTE["frame"]))
    parts.append(box("_Fb", (SCREEN_FRAME_BAR, ph, SCREEN_FRAME_BAR),
                     (-pw * 0.5 + SCREEN_FRAME_BAR * 0.5, 0, 0), col, PALETTE["frame"]))
    parts.append(box("_Ft", (SCREEN_FRAME_BAR, ph, SCREEN_FRAME_BAR),
                     (pw * 0.5 - SCREEN_FRAME_BAR * 0.5, 0, 0), col, PALETTE["frame"]))
    parts.append(box("_Fb2", (pw, SCREEN_FRAME_BAR, SCREEN_FRAME_BAR),
                     (0, -span_h * 0.5, 0), col, PALETTE["frame"]))
    parts.append(box("_Ft2", (pw, SCREEN_FRAME_BAR, SCREEN_FRAME_BAR),
                     (0, span_h * 0.5, 0), col, PALETTE["frame"]))
    screen = join_objects(parts, "Iron_Mesh_Screen", col)
    screen.rotation_euler = (math.radians(SCREEN_TILT - 90.0), 0, 0)
    # sit the top edge just under the chamber rim so the screen stays readable
    screen.location = Vector((cx - 40.0, cy,
                              bz + S1_H - SCREEN_GAP - inner_h * 0.5)) * MM
    screen["design_status"] = "[DOC]"
    screen["design_note"] = "Stage 01: rust-resistant iron wire mesh, %d x %d bars" % (
        SCREEN_BARS, SCREEN_BARS)

    # retained solids sitting on the screen (bulk plastics / packaging)
    debris = []
    for i in range(5):
        dx = cx - 230.0 + i * 95.0
        debris.append(box(f"_Debris_{i}", (160.0, 140.0, 90.0),
                          (dx, -180.0 + i * 70.0, bz + S1_H - SCREEN_GAP + 40.0),
                          col, PALETTE["waste"], rot=(0, 0, math.radians(i * 23))))
    deb = join_objects(debris, "Retained_Plastics", col)
    deb["design_note"] = "Plastics / packaging held back by the mesh screen"
    return tank


def build_sedimentation(col):
    """[DOC] Stage 02 - mud & sediment settling, multi-grade media filter."""
    cx, cy, bz = S2_CX, 0.0, FRAME_TOP_Z
    tank = open_tank("Sedimentation_Tank", cx, cy, bz, S2_L, S2_W, S2_H, col)
    tank["design_note"] = "Stage 02: gravity settling of fine sand, silt and dense mud"

    water = box("Sedimentation_Water", (S2_L - 2 * WALL_T - 20, S2_W - 2 * WALL_T - 20, S2_WATER_DEPTH),
                (cx, cy, bz + S2_SLUDGE_DEPTH + S2_WATER_DEPTH * 0.5), col, PALETTE["water"])
    water["design_note"] = "Turbid water after the mesh screen"

    sludge = box("Sludge_Layer", (S2_L - 2 * WALL_T - 20, S2_W - 2 * WALL_T - 20, S2_SLUDGE_DEPTH),
                 (cx, cy, bz + S2_SLUDGE_DEPTH * 0.5), col, PALETTE["sludge"])
    sludge["design_note"] = "Settled sand / silt / mud on the tank floor"

    baffle = box("Flow_Baffle", (WALL_T, S2_W - 2 * WALL_T, S2_BAFFLE_H),
                 (S2_BAFFLE_X, cy, bz + S2_H * 0.5), col, PALETTE["tank"],
                 status="[PROP]", note="Flow-damping baffle (adds residence time, slows velocity)")
    baffle["design_status"] = "[PROP]"
    baffle["design_note"] = "PROPOSED: flow-damping baffle to slow the flow for settling"

    if S2_MEDIA_BED:
        media = box("Filter_Media_Bed", (300.0, S2_W - 2 * WALL_T - 20, S2_MEDIA_DEPTH),
                    (cx + S2_L * 0.5 - 200.0, cy, bz + WALL_T + S2_MEDIA_DEPTH * 0.5), col, PALETTE["media"],
                    status="[PROP]", note="Multi-grade gravel / fine-pore media bed")
        media["design_status"] = "[PROP]"
        media["design_note"] = "PROPOSED: multi-grade gravel + fine-pore media bed over the outlet weir"

    # sludge drain from the tank floor  [PROP] - the document mentions sludge
    # level sensors, but shows no drain pipe.
    drain = pipe_between("Sludge_Drain_Pipe",
                         (cx + 250.0, cy, bz + 60.0),
                         (cx + 250.0, cy, 150.0), SLUDGE_DRAIN_D, col, PALETTE["sludge"])
    drain["design_status"] = "[PROP]"
    drain["design_note"] = "PROPOSED: sludge drain from the tank floor"
    d2 = pipe_between("Sludge_Drain_Out",
                      (cx + 250.0, cy, 150.0), (cx + 250.0, FRAME_Y0 - 500.0, 150.0),
                      SLUDGE_DRAIN_D, col, PALETTE["sludge"])
    d2["design_status"] = "[PROP]"
    d2["design_note"] = "PROPOSED: sludge drain from the tank floor"
    return tank


def build_fabric_filter(col):
    """[DOC] Stage 03 - high-tensile porous synthetic fabric polishing filter."""
    cx, cy, bz = S3_CX, 0.0, FRAME_TOP_Z
    tank = open_tank("Fabric_Filter_Chamber", cx, cy, bz, S3_L, S3_W, S3_H, col)
    tank["design_note"] = "Stage 03: fabric polishing chamber"

    water = box("Fabric_Filter_Water", (S3_L - 2 * WALL_T - 20, S3_W - 2 * WALL_T - 20, S3_WATER_DEPTH),
                (cx, cy, bz + WALL_T + S3_WATER_DEPTH * 0.5), col, PALETTE["water"])
    water["design_note"] = "Low-turbidity water entering the cloth filter"

    # flat rectangular cloth panel, leaning slightly
    cloth = box("Fabric_Filter_Panel", (S3_L - 2 * WALL_T - 60, CLOTH_T, S3_H - 2 * WALL_T - 90),
                (cx, 0.0, bz + S3_H * 0.5 + 10.0), col, PALETTE["fabric"],
                rot=(math.radians(CLOTH_TILT), 0, 0))
    cloth["design_note"] = "High-tensile porous synthetic fabric filter medium"

    # supporting frame for the cloth  [PROP]
    fw, fh = S3_L - 2 * WALL_T - 40, S3_H - 2 * WALL_T - 60
    fparts = [
        box("_cf_a", (fw, 50.0, 50.0), (0, -fh * 0.5, 0), col, PALETTE["clothfr"]),
        box("_cf_b", (fw, 50.0, 50.0), (0, fh * 0.5, 0), col, PALETTE["clothfr"]),
        box("_cf_c", (50.0, fh, 50.0), (-fw * 0.5, 0, 0), col, PALETTE["clothfr"]),
        box("_cf_d", (50.0, fh, 50.0), (fw * 0.5, 0, 0), col, PALETTE["clothfr"]),
    ]
    frame = join_objects(fparts, "Cloth_Panel_Frame", col)
    frame.rotation_euler = (math.radians(CLOTH_TILT), 0, 0)
    frame.location = Vector((cx, 0.0, bz + S3_H * 0.5 + 10.0)) * MM
    frame["design_status"] = "[PROP]"
    frame["design_note"] = "PROPOSED: support frame that holds the cloth panel"
    return tank


def build_valve(name, x, y, z, col, material):
    """[PROP] Simple block-and-handle valve body on a pipe."""
    parts = [
        cyl(name + "_Body", VALVE_BODY_R, 260.0, (x, y, z), col, material, rot=(0, math.radians(90), 0)),
        cyl(name + "_Stem", VALVE_HANDLE_R, 320.0, (x, y, z + VALVE_BODY_R + 150.0), col, material),
        cyl(name + "_Handwheel", VALVE_HANDLE_R * 2.6, 40.0,
            (x, y, z + VALVE_BODY_R + 290.0), col, material),
    ]
    o = join_objects(parts, name, col)
    o["design_status"] = "[PROP]"
    o["design_note"] = "PROPOSED: valve body modelled for readability; source only states 'a final output valve'"
    return o


def build_outlet(col):
    """[DOC] Final output valve -> clear water to the stream."""
    parts = [
        pipe_between("Outlet_Pipe", (OUTLET_X0, 0, OUTLET_Z), (OUTLET_X1, 0, OUTLET_Z),
                     OUTLET_D, col, PALETTE["clean"]),
        pipe_between("Outlet_Elbow_Down", (OUTLET_X0, 0, OUTLET_Z), (OUTLET_X0, 0, FRAME_TOP_Z + 520.0),
                     OUTLET_D, col, PALETTE["clean"]),
    ]
    outlet = join_objects(parts, "Stage05_Outlet", col)
    outlet["design_note"] = "Clean, low-turbidity water leaving via the final output valve"
    build_valve("Outlet_Valve", VALVE_X, 0.0, OUTLET_Z, col, PALETTE["clean"])
    return outlet


def build_conveyor(col):
    """[DOC] Motorized belt conveyor with scraper blades."""
    y = CONV_Y
    z = CONV_BELT_Z
    parts = []
    # top run + bottom run of the belt loop
    parts.append(box("Belt_Top_Run", (CONV_X1 - CONV_X0, CONV_BELT_W, CONV_BELT_T),
                     ((CONV_X0 + CONV_X1) * 0.5, y, z), col, PALETTE["belt"]))
    parts.append(box("Belt_Bottom_Run", (CONV_X1 - CONV_X0, CONV_BELT_W, CONV_BELT_T),
                     ((CONV_X0 + CONV_X1) * 0.5, y, z - CONV_ROLLER_R * 2.0), col, PALETTE["belt"]))
    belt = join_objects(parts, "Conveyor_Belt", col)
    belt["design_note"] = "Belt loop carrying debris away from the chambers"

    # two cylindrical rollers at each end (belt drum + tail drum)
    rollers = []
    for i, x in enumerate((CONV_X0, CONV_X1)):
        rollers.append(cyl(f"Roller_{i}", CONV_ROLLER_R, CONV_BELT_W,
                           (x, y, z - CONV_ROLLER_R), col, PALETTE["roller"],
                           rot=(math.radians(90), 0, 0)))
    rol = join_objects(rollers, "Conveyor_Rollers", col)
    rol["design_note"] = "Drive / tail rollers"

    # side rails + legs
    sup = []
    for s in (-1, 1):
        sup.append(box(f"_Rail_{s}", (CONV_X1 - CONV_X0, 60.0, 160.0),
                       ((CONV_X0 + CONV_X1) * 0.5, y + s * (CONV_BELT_W * 0.5 + 30.0), z + 60.0),
                       col, PALETTE["frame"]))
        for i, x in enumerate((CONV_X0 + 200.0, CONV_X1 - 200.0)):
            sup.append(box(f"_Leg_{s}_{i}", (CONV_LEG_W, CONV_LEG_W, z - 60.0),
                           (x, y + s * (CONV_BELT_W * 0.5 + 30.0), (z - 60.0) * 0.5),
                           col, PALETTE["frame"]))
    supp = join_objects(sup, "Conveyor_Frame", col)
    supp["design_status"] = "[PROP]"
    supp["design_note"] = "PROPOSED: conveyor support rails and legs"

    # scraper blades  [DOC: "scraper blades"]
    blades = []
    for i in range(SCRAPER_COUNT):
        x = CONV_X0 + 300.0 + (CONV_X1 - CONV_X0 - 600.0) * i / max(SCRAPER_COUNT - 1, 1)
        blades.append(box(f"_Scraper_{i}", (60.0, CONV_BELT_W - 80.0, 70.0),
                          (x, y, z + CONV_BELT_T * 0.5 + 35.0), col, PALETTE["clothfr"]))
    scr = join_objects(blades, "Scraper_Blades", col)
    scr["design_note"] = "Scraper blades that push debris along the belt"

    # simple motor block  [PROP: the doc says 'motorized', no drive detail]
    motor = box("Conveyor_Motor", (MOTOR_SX, MOTOR_SY, MOTOR_SZ),
                (CONV_X1 + 190.0, y, z - CONV_ROLLER_R - 40.0), col, PALETTE["motor"],
                status="[PROP]", note="Motor block; source says only 'motorized belt conveyor'")
    motor["design_status"] = "[PROP]"
    motor["design_note"] = "PROPOSED: simplified motor block driving the head roller"
    return belt


def build_waste_bin(col):
    """[DOC] 'secure disposal bins' fed at the conveyor discharge end."""
    x, y = BIN_X, BIN_Y
    h = BIN_SZ
    z0 = 60.0
    t = BIN_WALL_T
    parts = [
        box("Bin_Floor", (BIN_SX, BIN_SY, t), (x, y, z0 + t * 0.5), col, PALETTE["bin"]),
        box("Bin_Wall_XL", (t, BIN_SY, h), (x - BIN_SX * 0.5 + t * 0.5, y, z0 + h * 0.5), col, PALETTE["bin"]),
        box("Bin_Wall_XR", (t, BIN_SY, h), (x + BIN_SX * 0.5 - t * 0.5, y, z0 + h * 0.5), col, PALETTE["bin"]),
        box("Bin_Wall_YB", (BIN_SX - 2 * t, t, h), (x, y - BIN_SY * 0.5 + t * 0.5, z0 + h * 0.5), col, PALETTE["bin"]),
        box("Bin_Wall_YT", (BIN_SX - 2 * t, t, h), (x, y + BIN_SY * 0.5 - t * 0.5, z0 + h * 0.5), col, PALETTE["bin"]),
    ]
    bin_o = join_objects(parts, "Waste_Bin", col)
    bin_o["design_note"] = "Secure disposal bin at the conveyor discharge"

    fill = box("Captured_Waste", (BIN_SX - 2 * t - 20, BIN_SY - 2 * t - 20, BIN_FILL_H),
               (x, y, z0 + t + BIN_FILL_H * 0.5), col, PALETTE["waste"])
    fill["design_note"] = "Captured plastics / debris / sludge cake"
    return bin_o


def build_ground(col):
    """Simple backdrop slab - gives the frame a contact shadow. Excluded from framing."""
    g = box("Ground_Backdrop", (60000.0, 60000.0, 40.0), (0.0, 0.0, -20.0), col, PALETTE["ground"],
            status="[PROP]", note="Backdrop slab for shadow catching only")
    g["design_status"] = "[PROP]"
    return g


def build_flow_arrows(col):
    """Flow indication: inlet -> screen -> settling -> fabric -> outlet."""
    top = 2050.0
    flow_arrow("Flow_Inlet", (INLET_X0 + 60, 0, INLET_Z), (INLET_X1 - 40, 0, INLET_Z), col)
    flow_arrow("Flow_1", (S1_CX + 380, 0, top), (S1_CX + 980, 0, top), col)
    flow_arrow("Flow_2", (S2_CX + 760, 0, top), (S2_CX + 1500, 0, top), col)
    flow_arrow("Flow_3", (S3_CX + 680, 0, top), (S3_CX + 1320, 0, top), col)
    flow_arrow("Flow_Outlet", (OUTLET_X0 + 40, 0, OUTLET_Z + 260.0), (OUTLET_X1 - 60, 0, OUTLET_Z + 260.0), col)
    # solids path, screen -> conveyor -> bin
    flow_arrow("Flow_Solids", (S2_CX + 200, -260, FRAME_TOP_Z + 1500),
               (S2_CX + 200, CONV_Y + 380, CONV_BELT_Z + 320), col)
    flow_arrow("Flow_Solids_2", (CONV_X1 - 60, CONV_Y, CONV_BELT_Z + 230),
               (BIN_X - BIN_SX * 0.5 + 20, CONV_Y, BIN_SZ + 140), col)
    flow_arrow("Flow_Sludge", (S2_CX + 250, FRAME_Y0 - 430, 150.0),
               (S2_CX + 250, FRAME_Y0 - 110, 150.0), col)


def build_labels(col):
    """Readable flat labels.

    Everything is laid out in two clear bands:
      * an upper annotation band floating above the machine,
      * a lower call-out band laid out on the open ground in front of it.
    Stage labels are spread along the (1, -1, 0) axis so they read horizontally
    and never overlap in the isometric projection.
    """
    # ---- upper band : title, flow legend, stage titles ----------------------
    text_label("Lbl_Title", "DOMESTIC SEWAGE FILTRATION SYSTEM", (-1900, 1900, 3950),
               col, size=185.0, status="[DOC]", note="Title")
    text_label("Lbl_Flow", ">>> WATER FLOW >>>", (1900, 900, 3950), col, size=145.0,
               status="[PROP]", note="Flow direction annotation")
    # the banner labels belong to the assembled machine, not to any one part,
    # so they are hidden while the model is pulled apart
    for nm in ("Lbl_Title", "Lbl_Flow"):
        bpy.data.objects[nm]["hide_in_explode"] = True

    zs = 3400.0
    text_label("Lbl_Stage1", "STAGE 01\nIRON MESH SCREEN", (-2100, 600, zs), col, size=150.0, home="03_Screen_Chamber")
    text_label("Lbl_Stage2", "STAGE 02\nSEDIMENTATION TANK", (-900, -200, zs), col, size=150.0, home="04_Sedimentation")
    text_label("Lbl_Stage3", "STAGE 03\nFABRIC POLISHING", (300, -1000, zs), col, size=150.0, home="05_Fabric_Filter")

    text_label("Lbl_Cloth", "FABRIC FILTER PANEL", (1500, 1500, 2200), col, size=130.0, home="05_Fabric_Filter")
    text_label("Lbl_Valve", "OUTPUT VALVE", (2700, -1700, 2200), col, size=130.0, home="06_Outlet")

    # ---- lower band : floor call-outs on the open ground --------------------
    yf = -2300.0
    text_label("Lbl_Inlet", "WASTEWATER\nINLET", (-2600, yf, 60), col, size=140.0, home="02_Inlet")
    text_label("Lbl_Conveyor", "CONVEYOR +\nSCRAPER BLADES", (-800, yf, 60), col, size=140.0, home="07_Conveyor")
    text_label("Lbl_Bin", "DISPOSAL\nBIN", (900, yf, 60), col, size=140.0, home="07_Conveyor")
    text_label("Lbl_Outlet", "CLEAN WATER\nOUTLET", (2500, yf, 60), col, size=140.0)
    text_label("Lbl_Sludge", "SLUDGE DRAIN", (-1600, yf - 800, 60), col, size=140.0, home="04_Sedimentation")


# ==============================================================================
# 5. STAGING : world, lights, cameras, render settings
# ==============================================================================

def setup_world(scene, ambient=0.42):
    """White studio background that does not blow out the model.

    A plain white world at full strength both clips the background to pure
    white AND floods the model with ambient light, which flattens everything.
    The Light Path / Is Camera Ray node separates the two: camera rays see pure
    white, while lighting rays see a dimmer grey. That gives a clean white
    backdrop with correctly contrasted, readable components.
    """
    world = bpy.data.worlds.new("World_White_Studio")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (400, 0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    path = nt.nodes.new("ShaderNodeLightPath")
    path.location = (-100, 250)

    bg_amb = nt.nodes.new("ShaderNodeBackground")       # what the lights see
    bg_amb.location = (0, -120)
    bg_amb.inputs[0].default_value = (ambient, ambient * 1.01, ambient * 1.03, 1.0)
    bg_amb.inputs[1].default_value = 1.0

    bg_cam = nt.nodes.new("ShaderNodeBackground")       # what the camera sees
    bg_cam.location = (0, 120)
    bg_cam.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg_cam.inputs[1].default_value = 1.0

    nt.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg_amb.outputs[0], mix.inputs[1])
    nt.links.new(bg_cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])

    scene.world = world


def setup_lights(col):
    bpy.ops.object.light_add(type='SUN', location=(6, -6, 10))
    sun = bpy.context.active_object
    sun.name = "Key_Sun"
    sun.data.energy = 2.4
    sun.data.angle = math.radians(18.0)
    sun.rotation_euler = (math.radians(48), math.radians(5), math.radians(-125))
    link(sun, col)

    bpy.ops.object.light_add(type='AREA', location=(2.0, 7.0, 7.0))
    fill = bpy.context.active_object
    fill.name = "Fill_Area"
    fill.data.energy = 200.0
    fill.data.size = 8.0
    fill.rotation_euler = (math.radians(55), 0.0, math.radians(150))
    link(fill, col)
    return sun


def iso_camera(col, name="Camera_Isometric", clip_start=None):
    """Orthographic isometric camera (45 deg azimuth, 35.26 deg elevation)."""
    bpy.ops.object.camera_add(location=(0, 0, 0))
    cam = bpy.context.active_object
    cam.name = name
    # viewed from (-X, -Y, +Z) so that the process reads left -> right in the image
    d = Vector((-1.0, -1.0, 0.8165)).normalized()
    cam.location = CAM_CENTER + d * CAM_DIST
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 9.4
    if clip_start is not None:
        cam.data.clip_start = clip_start
    link(cam, col)
    return cam


def front_camera(col, name="Camera_Section", cut_y=-430.0):
    """Orthographic front camera whose near clip plane cuts the model at cut_y.

    The section is a true near-clip cut: the camera looks along +Y and its
    near clip plane sits at y = cut_y. The default plane is just inside the
    front tank walls, so the walls are sliced away and the water, sludge and
    filter media inside each chamber become visible. Everything on the service
    side (conveyor, bin) is in front of the plane and is therefore cut away too.
    """
    cam_y = CAM_CENTER.y * MM - CAM_DIST
    bpy.ops.object.camera_add(location=(0, 0, 0))
    cam = bpy.context.active_object
    cam.name = name
    cam.location = (CAM_CENTER.x * MM, cam_y, CAM_CENTER.z * MM)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 9.4
    cam.data.clip_start = cut_y * MM - cam_y          # both in metres
    cam.data.clip_end = cam.data.clip_start + CAM_DIST
    link(cam, col)
    return cam


def fit_ortho_camera(cam, scene, margin=1.05, reposition=True, preserve_y=False,
                    include_text=True):
    """Set cam.data.ortho_scale (and optionally position) so everything fits.

    Bounds are taken from the evaluated depsgraph so that text objects, whose
    bound_box is only correct once the curve has been generated, are measured
    correctly and never get clipped by the frame.
    """
    deps = bpy.context.evaluated_depsgraph_get()
    rot = cam.matrix_world.to_quaternion()
    right = rot @ Vector((1.0, 0.0, 0.0))
    up = rot @ Vector((0.0, 1.0, 0.0))
    fwd = rot @ Vector((0.0, 0.0, 1.0))       # camera looks along -Z of its own axes

    xs, ys = [], []
    for ob in scene.objects:
        if ob.type not in {'MESH', 'FONT'}:
            continue
        # flat labels are seen edge-on by the section camera, so counting them
        # would only push the framing out for nothing
        if ob.type == 'FONT' and not include_text:
            continue
        if ob.name.startswith("Ground_"):
            continue                          # backdrop is excluded from auto-framing
        ev = ob.evaluated_get(deps)
        mw = ob.matrix_world
        for corner in ev.bound_box:
            pt = mw @ Vector(corner)
            xs.append(pt.dot(right))
            ys.append(pt.dot(up))
    if not xs:
        return
    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    w = (max(xs) - min(xs)) * margin
    h = (max(ys) - min(ys)) * margin
    aspect = scene.render.resolution_x / scene.render.resolution_y
    cam.data.ortho_scale = max(w, h * aspect)

    if reposition:
        centre = right * cx + up * cy
        # cam's local +Z points from the model back toward the camera
        loc = centre + fwd * CAM_DIST
        if preserve_y:
            # keep the standoff distance: for the section camera that distance
            # is what places the near clip plane on the cutting plane
            loc.y = cam.location.y
        cam.location = loc
    print("[fit] %s ortho_scale=%.2f  extent=%.2f x %.2f m"
          % (cam.name, cam.data.ortho_scale, w, h))


def setup_render(scene, camera):
    scene.camera = camera
    engines = {i.identifier for i in
               bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
    if 'BLENDER_EEVEE_NEXT' in engines:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    elif 'BLENDER_EEVEE' in engines:
        scene.render.engine = 'BLENDER_EEVEE'
    else:
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = SAMPLES
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    try:
        scene.eevee.taa_render_samples = SAMPLES
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0


def render_to(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[OK] rendered", path)


# ==============================================================================
# 6. ASSEMBLY / EXPLODE / SECTION
# ==============================================================================

def apply_explode(cols, factor=1.0):
    """Offset whole collections (and any label bound to them) for the exploded view."""
    for name, col in cols.items():
        off = EXPLODE.get(name)
        if not off:
            continue
        for o in col.objects:
            o.location = o.location + off * factor

    # labels and arrows live in the annotation collection, which is never offset
    # itself - instead every label that declares a home collection rides along
    # with the component it annotates.
    for name, col in cols.items():
        if EXPLODE.get(name):
            continue
        for o in col.objects:
            home = o.get("explode_home")
            if home and EXPLODE.get(home):
                o.location = o.location + EXPLODE[home] * factor


def main():
    scene = reset_scene()
    build_materials()

    # ---- named collections -------------------------------------------------
    cols = {
        "00_Staging":        make_collection("00_Staging"),
        "01_Base_Frame":     make_collection("01_Base_Frame"),
        "02_Inlet":          make_collection("02_Inlet"),
        "03_Screen_Chamber": make_collection("03_Screen_Chamber"),
        "04_Sedimentation":  make_collection("04_Sedimentation"),
        "05_Fabric_Filter":  make_collection("05_Fabric_Filter"),
        "06_Outlet":         make_collection("06_Outlet"),
        "07_Conveyor":       make_collection("07_Conveyor"),
        "08_Annotations":    make_collection("08_Annotations"),
    }

    # ---- build -------------------------------------------------------------
    build_base_frame(cols["01_Base_Frame"])
    build_inlet(cols["02_Inlet"])
    build_screen_chamber(cols["03_Screen_Chamber"])
    build_sedimentation(cols["04_Sedimentation"])
    build_fabric_filter(cols["05_Fabric_Filter"])
    build_outlet(cols["06_Outlet"])
    build_conveyor(cols["07_Conveyor"])
    build_waste_bin(cols["07_Conveyor"])
    build_flow_arrows(cols["08_Annotations"])
    build_labels(cols["08_Annotations"])
    build_ground(cols["00_Staging"])

    setup_world(scene)
    setup_lights(cols["00_Staging"])
    cam_iso = iso_camera(cols["00_Staging"])
    cam_sec = front_camera(cols["00_Staging"])
    setup_render(scene, cam_iso)

    # ---- README text block inside the .blend -------------------------------
    readme = bpy.data.texts.new("README_Domestic_Sewage_Filtration")
    readme.write(
        "DOMESTIC SEWAGE FILTRATION SYSTEM - low-poly visualization model\n"
        "==================================================================\n"
        "Source: 'Domestic Sewage Filtration System (Black & White).pdf'\n"
        "(12 scanned slides, no text layer). The source document is qualitative\n"
        "only. It names the stages but gives NO dimensions, flow rates, materials\n"
        "grades or performance data. Every dimension in build_filtration_system.py\n"
        "is therefore PROVISIONAL and meant to be edited.\n\n"
        "Process chain modelled:\n"
        "  Wastewater inlet -> Iron mesh screen -> Sedimentation tank\n"
        "  -> Fabric filter -> Output valve -> stream discharge\n"
        "  Solids: screen debris / sludge -> belt conveyor + scraper -> disposal bin\n\n"
        "[DOC]  = named in the source document.\n"
        "[PROP] = proposed addition made here so the documented feature is buildable\n"
        "         (base frame, pipe runs, valve bodies, support legs, media bed\n"
        "         representation, flow arrows).\n\n"
        "Collections are numbered in process order. Every object carries the custom\n"
        "properties 'design_status' and 'design_note'.\n"
    )

    # ---- render 1 : assembled isometric ------------------------------------
    fit_ortho_camera(cam_iso, scene)
    render_to(scene, os.path.join(OUT_DIR, "assembly_overview.png"))

    # ---- render 2 : exploded view ------------------------------------------
    apply_explode(cols, 1.0)
    global_banner = [o for o in cols["08_Annotations"].objects
                     if o.get("hide_in_explode")]
    for o in global_banner:
        o.hide_render = True
    fit_ortho_camera(cam_iso, scene)
    render_to(scene, os.path.join(OUT_DIR, "exploded_view.png"))
    for o in global_banner:
        o.hide_render = False
    apply_explode(cols, -1.0)

    # ---- render 3 : sectional (front orthographic cut at Y = 0) ------------
    backdrop = [o for o in cols["00_Staging"].objects if o.name.startswith("Ground_")]
    for o in backdrop:
        o.hide_render = True          # a horizontal backdrop would fill a side view
    fit_ortho_camera(cam_sec, scene, reposition=True, preserve_y=True,
                      include_text=False)
    scene.camera = cam_sec
    render_to(scene, os.path.join(OUT_DIR, "section_view.png"))
    for o in backdrop:
        o.hide_render = False

    # ---- back to the assembled state and save ------------------------------
    scene.camera = cam_iso
    fit_ortho_camera(cam_iso, scene)
    setup_render(scene, cam_iso)

    blend_path = os.path.join(OUT_DIR, "domestic_sewage_filtration_system.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("[OK] saved", blend_path)

    n_obj = sum(len(c.objects) for c in cols.values())
    print("[SUMMARY] collections=%d objects=%d" % (len(cols), n_obj))


if __name__ == "__main__":
    main()