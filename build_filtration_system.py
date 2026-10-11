#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
DOMESTIC SEWAGE FILTRATION SYSTEM  -  PARAMETRIC BLENDER BUILD SCRIPT
================================================================================
Source document : "Domestic Sewage Filtration System (Black & White).pdf"
                  (12 slides, scanned, no text layer; images read at 110 dpi)

WHAT THE SOURCE DOCUMENT ACTUALLY SPECIFIES
-------------------------------------------
Documented (qualitative only, NO numbers anywhere in the source):
  Stage 01  Iron Mesh Filtration
            - "heavy-duty rust-resistant iron wire mesh"
            - retains polythenes, plastic packaging, bulk waste
            - "iron mesh screen" is the first barrier the sewage meets
  Stage 02  Mud & Sediment Filtration
            - settling of fine sand, silt, dense mud
            - secondary filter = multi-grade gravel + fine-pore media
            - reduces turbidity, prepares water for polishing
  Stage 03  Fabric Polishing System
            - "high-tensile porous synthetic fabric filter"
            - captures micro-particulates / residual cloudiness
            - produces polished water
  Automation  Conveyor System
            - "motorized belt conveyor with scraper blades"
            - continuous or sensor-triggered rotation
            - lifts/shifts debris from the chambers into "secure disposal bins"
  Final Output
            - a "final output valve" discharging the polished water
  Cross-cutting: "gravity-assisted flow", "modular design", "low power footprint",
            "IoT sensors for automated sludge level detection" (future scope)

WHAT THE SOURCE DOCUMENT DOES **NOT** SPECIFY (everything below is provisional)
-----------------------------------------------------------------------------
  No dimensions, no flow rates, no mesh aperture, no material grades,
  no motor/gearbox rating, no hydraulic performance, no treatment efficiency,
  no structural load ratings. This script therefore defines ONE central
  PARAMETERS block of clearly-labelled PROVISIONAL engineering values which the
  user is expected to edit. Nothing here is certified or source-derived.

DISTINCTION DOCUMENTED vs PROPOSED
-----------------------------------
  [DOC]  = feature explicitly named in the source PDF
  [PROP] = mechanical addition invented by this design to make the documented
           feature buildable, serviceable and safe. Flagged on the object as a
           custom property "design_status" and listed in component_inventory.csv.

Units
-----
  All parameters are in MILLIMETRES (design reference unit).
  Blender works in METRES; MM is the conversion factor (1 BU = 1 m).
  X = process flow direction (inlet -> outlet), Y = machine width,
  Z = up, Z=0 is the ground/floor plane.

Run
---
  blender --background --python build_filtration_system.py
  blender --background --python build_filtration_system.py -- --no-anim
  blender --background --python build_filtration_system.py -- --quick   (low res)

Outputs
-------
  domestic_sewage_filtration_system.blend
  assembly_overview.png, exploded_assembly.png, sectional_view.png,
  front_view.png, side_view.png, top_view.png
  component_inventory.csv, design_parameters.json, README.md
  exports/  (stl/, obj, glb, stl per component)
================================================================================
"""

import bpy
import bmesh
import math
import os
import sys
import json
import csv
from mathutils import Vector

# ==============================================================================
# 0.  ARGUMENTS + PATHS
# ==============================================================================

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DO_ANIM_SETUP = "--no-anim" not in ARGV
QUICK = "--quick" in ARGV

MM = 0.001  # millimetre -> blender unit (metre)
S2 = math.sqrt(2.0) / 2.0

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = HERE
EXPORT_DIR = os.path.join(HERE, "exports")
STL_DIR = os.path.join(EXPORT_DIR, "stl")

RES_X, RES_Y = (960, 540) if QUICK else (1920, 1080)
SAMPLES = 16 if QUICK else 96


# ==============================================================================
# 1.  ══════════════════════════════════════════════════════════════════════════
#     DESIGN PARAMETERS  --  ALL PROVISIONAL, EDIT HERE
#     Every value below is a PROPOSED prototype-scale starting point, NOT a
#     value taken from the source document and NOT construction-certified.
#     =================================================================═════════
# ==============================================================================

P = {
    # ---------------------------------------------------------------- overall
    "units": "mm (provisional design reference unit)",
    "overall_length": 3400.0,          # X  (skid footprint incl. bin & outlet)
    "overall_width": 1400.0,           # Y
    "overall_height": 1750.0,          # Z above floor

    # ------------------------------------------------------------------ frame
    "frame_rhs": 60.0,                 # rectangular hollow section outer size
    "frame_rhs_wall": 4.0,
    "frame_deck_z": 150.0,             # top of skid frame (tanks stand on this)
    "frame_post_inset": 80.0,          # post centre inset from skid edge
    "frame_cross_member_count": 4,     # longitudinal cross members per bay

    # --------------------------------------------------------- 01 inlet+screen
    "inlet_chamber_len": 620.0,        # X
    "inlet_chamber_wid": 620.0,        # Y
    "inlet_chamber_ztop": 1400.0,
    "inlet_chamber_zbot": 880.0,
    "inlet_chamber_wall": 8.0,
    "inlet_pipe_dia": 150.0,           # DN150 raw sewage inlet
    "inlet_pipe_z": 1330.0,
    "screen_tilt_deg": 58.0,           # inclined bar/mesh screen
    "screen_x_bottom": 250.0,
    "screen_clear_h": 460.0,           # clear opening height of the screen
    "screen_clear_w": 560.0,
    "mesh_pitch": 25.0,                # [PROVISIONAL] wire mesh clear aperture
    "mesh_wire_dia": 4.0,
    "screen_frame_bar": 40.0,          # screen carrier frame bar size
    "screen_lift_clearance": 250.0,    # vertical lift needed to withdraw screen
    "weir_crest_z": 1300.0,

    # -------------------------------------------------------- 02 settling tank
    "settling_x0": 760.0,
    "settling_len": 1180.0,            # X
    "settling_wid": 900.0,             # Y
    "settling_rim_z": 1400.0,
    "settling_floor_z": 620.0,         # top of hopper = tank inner floor
    "settling_wall": 8.0,
    "settling_support_h": 220.0,       # pedestal height floor->deck
    "hopper_depth": 200.0,
    "hopper_angle_deg": 55.0,          # [PROVISIONAL] side slope
    "hopper_drain_dia": 80.0,          # DN80 sludge drain
    "settling_water_level_z": 1230.0,
    "settling_inlet_z": 1180.0,
    "settling_draw_off_z": 660.0,      # clarified water draw-off above hopper
    "lid_thk": 10.0,

    # ------------------------------------------- 02b gravel secondary filter
    "gravel_x0": 1500.0,               # occupies downstream end of tank only
    "gravel_len": 410.0,
    "gravel_wid": 820.0,
    "gravel_z0": 640.0,
    "gravel_layers": 3,                # multi-grade layers (documented "multi-grade")
    "gravel_layer_thk": 55.0,
    "gravel_underdrain_h": 40.0,

    # ------------------------------------------------------- 03 fabric chamber
    "fabric_x0": 2050.0,
    "fabric_len": 660.0,
    "fabric_wid": 780.0,
    "fabric_rim_z": 1230.0,
    "fabric_floor_z": 420.0,
    "fabric_wall": 8.0,
    "fabric_support_h": 270.0,
    "fabric_water_level_z": 1030.0,
    "fabric_inlet_z": 660.0,
    "fabric_outlet_z": 520.0,
    "filter_media_thk": 8.0,           # cloth thickness
    "filter_frame_bar": 30.0,
    "filter_lift_clearance": 450.0,    # space above chamber for filter lift-out
    "cover_lip_overhang": 25.0,
    "cover_handle_dia": 20.0,

    # ------------------------------------------------------------- 04 conveyor
    "conv_tail": (360.0, -640.0, 470.0),    # tail (lower) drum centre
    "conv_head": (2760.0, -640.0, 1160.0),  # head (drive) drum centre
    "conv_belt_width": 500.0,
    "conv_roller_dia": 100.0,
    "conv_belt_thk": 8.0,
    "conv_side_rail": 70.0,
    "conv_idler_count": 3,
    "conv_leg_positions": (1000.0, 1700.0, 2450.0),
    "motor_len": 300.0,                # envelope only - rating NOT specified
    "motor_dia": 180.0,
    "gearbox_len": 190.0,
    "gearbox_wid": 170.0,
    "gearbox_hgt": 220.0,
    "guard_thk": 4.0,
    "tensioner_stroke": 60.0,
    "scraper_blade_len": 480.0,
    "scraper_blade_thk": 12.0,

    # --------------------------------------------------------- 05 collection bin
    "bin_len": 700.0,
    "bin_wid": 470.0,
    "bin_hgt": 600.0,
    "bin_x0": 2280.0,
    "bin_y0": -800.0,
    "bin_floor_z": 150.0,              # sits on deck
    "bin_wall": 5.0,
    "bin_divider_x": 2560.0,           # solids bay | sludge bay
    "bin_drag_handle": 260.0,

    # ---------------------------------------------------------------- piping
    "transfer_pipe_dia": 150.0,        # inlet chamber -> settling tank
    "filtered_pipe_dia": 125.0,        # settling tank -> fabric chamber
    "outlet_pipe_dia": 100.0,          # PIPE_OUTLET (polished water)
    "sludge_pipe_dia": 80.0,           # sludge drain
    "sludge_valve_z": 300.0,
    "pipe_bend_radius_factor": 1.1,    # x pipe radius
    "flange_thk": 14.0,
    "flange_boss": 26.0,               # flange dia = pipe dia + 2*boss

    # ------------------------------------------------------------ fasteners
    "bolt_hex_af": 16.0,
    "bolt_head_h": 10.0,
    "bolt_count_lid": 10,
    "guard_gap": 12.0,
}


# ==============================================================================
# 2.  UTILITY FUNCTIONS
# ==============================================================================

def M(v):
    """millimetres -> blender metres (scalar or sequence)"""
    if hasattr(v, "__len__"):
        return tuple(x * MM for x in v)
    return v * MM


def wipe_scene():
    """Hard reset so the script is fully reproducible/idempotent."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                 bpy.data.objects, bpy.data.collections, bpy.data.cameras,
                 bpy.data.lights, bpy.data.images, bpy.data.actions):
        for db in list(coll):
            try:
                coll.remove(db)
            except Exception:
                pass


COLLECTIONS = {}


def make_collections():
    root = bpy.context.scene.collection
    names = [
        ("00_FRAME",        "00_Frame_and_Skid"),
        ("01_SCREEN",       "01_Inlet_and_Iron_Mesh_Screen"),
        ("02_SETTLING",     "02_Sedimentation_Chamber"),
        ("03_FABRIC",       "03_Fabric_Polishing_Chamber"),
        ("04_CONVEYOR",     "04_Conveyor_and_Waste_Handling"),
        ("05_PIPING",       "05_Piping_and_Outlet"),
        ("06_BIN",          "06_Sludge_and_Waste_Bin"),
        ("07_FLOW",         "07_Flow_Indicators"),
        ("08_ANNOT",        "08_Annotations"),
        ("09_RIG",          "09_Cameras_and_Lights"),
    ]
    for key, name in names:
        c = bpy.data.collections.new(name)
        root.children.link(c)
        COLLECTIONS[key] = c


def link_to(obj, coll_key):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    COLLECTIONS[coll_key].objects.link(obj)
    return obj


# ------------------------------------------------------------------------------
# Materials
# ------------------------------------------------------------------------------
MATS = {}


def make_material(name, color, metallic=0.0, roughness=0.5, alpha=1.0,
                  transmission=0.0, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
        for key, val in (("Metallic", metallic), ("Roughness", roughness),
                         ("Alpha", alpha)):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = val
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
        if emission is not None:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (
                    emission[0], emission[1], emission[2], 1.0)
                bsdf.inputs["Emission Strength"].default_value = emission[3]
    if alpha < 1.0:
        # Blender 4.2+ / 5.x EEVEE Next
        for attr, val in (("surface_render_method", "BLENDED"),
                          ("blend_method", "BLEND")):
            try:
                setattr(mat, attr, val)
            except Exception:
                pass
        mat.use_backface_culling = False
    MATS[name] = mat
    return mat


def build_materials():
    # restrained industrial palette
    make_material("MAT_Steel_Frame",    (0.32, 0.34, 0.37), 0.90, 0.42)
    make_material("MAT_Steel_Painted",  (0.26, 0.31, 0.36), 0.35, 0.50)
    make_material("MAT_Stainless_Tank", (0.70, 0.72, 0.74), 0.85, 0.28)
    make_material("MAT_Iron_Mesh",      (0.20, 0.17, 0.15), 0.80, 0.68)
    make_material("MAT_Gravel",         (0.50, 0.46, 0.41), 0.00, 0.90)
    make_material("MAT_Fabric_Filter",  (0.88, 0.87, 0.82), 0.00, 0.92)
    make_material("MAT_Rubber_Belt",    (0.055, 0.055, 0.06), 0.00, 0.85)
    make_material("MAT_Pipe_Polymer",   (0.18, 0.24, 0.32), 0.10, 0.45)
    make_material("MAT_Pipe_Clean",     (0.10, 0.40, 0.58), 0.20, 0.35)
    make_material("MAT_Pipe_Sludge",    (0.30, 0.26, 0.16), 0.10, 0.60)
    make_material("MAT_Water_Raw",      (0.30, 0.26, 0.17), 0.00, 0.10, 0.55)
    make_material("MAT_Water_Polished", (0.20, 0.52, 0.74), 0.00, 0.08, 0.45)
    make_material("MAT_Sludge",         (0.13, 0.10, 0.07), 0.00, 0.92)
    make_material("MAT_Motor_Blue",     (0.13, 0.20, 0.32), 0.40, 0.45)
    make_material("MAT_Rubber_Black",   (0.09, 0.09, 0.09), 0.00, 0.75)
    make_material("MAT_Safety_Orange",  (0.80, 0.36, 0.04), 0.00, 0.55)
    make_material("MAT_Concrete_Pad",   (0.52, 0.51, 0.49), 0.00, 0.85)
    make_material("MAT_Label",          (0.05, 0.06, 0.08), 0.00, 0.70)
    make_material("MAT_Flow_Raw",       (0.85, 0.55, 0.10), 0.00, 0.35,
                  emission=(0.85, 0.45, 0.05, 1.2))
    make_material("MAT_Flow_Clean",     (0.15, 0.70, 0.95), 0.00, 0.35,
                  emission=(0.10, 0.55, 0.95, 1.4))
    make_material("MAT_Flow_Sludge",    (0.55, 0.40, 0.12), 0.00, 0.45,
                  emission=(0.45, 0.30, 0.05, 0.8))


def assign(obj, mat):
    if mat is None:
        return obj
    m = MATS[mat] if isinstance(mat, str) else mat
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return obj


# ------------------------------------------------------------------------------
# Component inventory registry
# ------------------------------------------------------------------------------
INVENTORY = []


def tag(obj, subsystem, material_note, note="", status="[PROP]", qty=None):
    obj["design_status"] = status
    obj["subsystem"] = subsystem
    rec = {
        "component": obj.name,
        "subsystem": subsystem,
        "material_provisional": material_note,
        "status_vs_source": status,
        "notes": note,
    }
    INVENTORY.append(rec)
    obj["_inventory"] = rec
    return obj


def tag_many(objs, subsystem, material_note, note="", status="[PROP]"):
    for o in objs:
        tag(o, subsystem, material_note, note, status)


# ------------------------------------------------------------------------------
# Primitive builders (all dimensions in mm)
# ------------------------------------------------------------------------------
def box(name, size, loc, mat=None, coll="00_FRAME", rot=(0, 0, 0)):
    """size = (sx, sy, sz) mm, loc = centre in mm, rot = degrees."""
    bpy.ops.mesh.primitive_cube_add(size=1.0,
                                    location=M(loc),
                                    rotation=[math.radians(a) for a in rot])
    o = bpy.context.object
    o.name = name
    o.scale = M(size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, mat)
    link_to(o, coll)
    return o


def cyl(name, dia, height, loc, mat=None, coll="00_FRAME",
        rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=M(dia) / 2.0,
                                        depth=M(height),
                                        location=M(loc),
                                        rotation=[math.radians(a) for a in rot],
                                        vertices=verts)
    o = bpy.context.object
    o.name = name
    assign(o, mat)
    link_to(o, coll)
    return o


def tube(name, od, idia, height, loc, mat=None, coll="00_FRAME",
         rot=(0, 0, 0), verts=32):
    """Hollow pipe section (used for drums, sleeves, flanges)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=M(od) / 2.0, depth=M(height),
                                        location=M(loc),
                                        rotation=[math.radians(a) for a in rot],
                                        vertices=verts)
    o = bpy.context.object
    o.name = name
    if idia > 0:
        cutter = cyl("_cut", idia, height * 3, loc, None, coll, rot, verts)
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_add(type="BOOLEAN")
        mod = o.modifiers[-1]
        mod.object = cutter
        mod.operation = "DIFFERENCE"
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    assign(o, mat)
    link_to(o, coll)
    return o


def frustum_box(name, lx0, ly0, lx1, ly1, h, loc, mat=None,
                coll="00_FRAME", inner_scale=1.0):
    """Solid rectangular frustum with explicit top/bottom footprints (mm).

    Vertices are authored in millimetres and converted here, exactly as the
    primitive builders do.
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    tx, ty = M(lx0 / 2.0), M(ly0 / 2.0)
    bx, by = M(lx1 / 2.0), M(ly1 / 2.0)
    hh = M(h)
    v = [bm.verts.new((-bx, -by, 0)), bm.verts.new((bx, -by, 0)),
         bm.verts.new((bx, by, 0)), bm.verts.new((-bx, by, 0)),
         bm.verts.new((-tx, -ty, hh)), bm.verts.new((tx, -ty, hh)),
         bm.verts.new((tx, ty, hh)), bm.verts.new((-tx, ty, hh))]
    bm.faces.new(v[0:4][::-1])
    bm.faces.new(v[4:8])
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new([v[i], v[j], v[j + 4], v[i + 4]])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = M(loc)
    assign(o, mat)
    link_to(o, coll)
    return o


def boolean_diff(obj, cutter, op="DIFFERENCE", apply=True):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type="BOOLEAN")
    mod = obj.modifiers[-1]
    mod.object = cutter
    mod.operation = op
    mod.solver = "EXACT"
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def bevel(obj, width_mm=2.0, segments=2):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = M(width_mm)
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(40)
    mod.harden_normals = False
    return obj


def shade_smooth(obj, angle_deg=35.0):
    """Smooth shading with an angle threshold (auto-smooth, version safe)."""
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        prev = bpy.context.view_layer
        obj.data.use_auto_smooth = True      # <=4.0
        obj.data.auto_smooth_angle = math.radians(angle_deg)
    except Exception:
        mod = obj.modifiers.new("EdgeSplit", "EDGE_SPLIT")
        mod.split_angle = math.radians(angle_deg)
    return obj


# ------------------------------------------------------------------------------
# Fastener instancing (shared mesh data = cheap)
# ------------------------------------------------------------------------------
_BOLT_MESH = None


def bolt(name, loc, size=None, coll="00_FRAME", rot=(0, 0, 0)):
    """Hex-head bolt, instanced (shared mesh data) for cheap repetition."""
    global _BOLT_MESH
    af = size or P["bolt_hex_af"]
    if _BOLT_MESH is None:
        tmp = cyl("_boltproto", af, P["bolt_head_h"], (0, 0, 0), None, coll,
                  verts=6)
        _BOLT_MESH = tmp.data
        bpy.data.objects.remove(tmp, do_unlink=True)
    o = bpy.data.objects.new(name, _BOLT_MESH)
    COLLECTIONS[coll].objects.link(o)
    o.location = M(loc)
    o.rotation_euler = [math.radians(a) for a in rot]
    assign(o, "MAT_Steel_Frame")
    return o


def bolt_ring(name, cx, cy, z, count, radius, coll="00_FRAME", phase=0.0):
    out = []
    for i in range(count):
        a = phase + 2.0 * math.pi * i / count
        out.append(bolt("%s_%02d" % (name, i),
                        (cx + radius * math.cos(a),
                         cy + radius * math.sin(a), z), coll=coll))
    return out


# ------------------------------------------------------------------------------
# Pipe routing: rounded polyline swept with a bevel -> real elbows
# ------------------------------------------------------------------------------
def rounded_path(points, radius, seg=8):
    """Round the interior corners of a 3D polyline (mm)."""
    if len(points) < 3:
        return list(points)
    out = [tuple(points[0])]
    for i in range(1, len(points) - 1):
        p, c, n = points[i - 1], points[i], points[i + 1]
        v1 = Vector((p[0] - c[0], p[1] - c[1], p[2] - c[2]))
        v2 = Vector((n[0] - c[0], n[1] - c[1], n[2] - c[2]))
        l1, l2 = v1.length, v2.length
        if l1 < 1e-6 or l2 < 1e-6:
            continue
        u1, u2 = v1 / l1, v2 / l2
        cosang = max(-1.0, min(1.0, u1.dot(u2)))
        ang = math.acos(cosang)
        if ang > math.radians(178) or ang < 1e-3:
            out.append(tuple(c))
            continue
        t = min(radius / math.tan(ang / 2.0), l1 * 0.48, l2 * 0.48)
        a = Vector(c) + u1 * t
        b = Vector(c) + u2 * t
        bis = (u1 + u2).normalized()
        d = t / math.cos(ang / 2.0)          # centre->corner distance
        centre = Vector(c) + bis * d
        va, vb = a - centre, b - centre
        axis = va.cross(vb)
        if axis.length < 1e-9:
            out.append(tuple(c))
            continue
        axis.normalize()
        total = va.angle(vb)
        # build arc with Rodrigues rotation about the corner axis
        arc = []
        for k in range(seg + 1):
            ang_k = total * k / seg
            v = va * math.cos(ang_k) + axis.cross(va) * math.sin(ang_k) \
                + axis * (axis.dot(va)) * (1 - math.cos(ang_k))
            arc.append(tuple(centre + v))
        out.extend(arc)
    out.append(tuple(points[-1]))
    # strip any accidental Nones / duplicates
    clean = []
    for q in out:
        if q is None:
            continue
        if not clean or (Vector(q) - Vector(clean[-1])).length > 0.05:
            clean.append(tuple(q))
    return clean


def pipe(name, dia, points, mat="MAT_Pipe_Polymer", coll="05_PIPING",
         bend_factor=1.1, status="[PROP]", note="", subsystem="Piping"):
    """Sweep a round profile along a filleted polyline (mm)."""
    r = dia / 2.0
    path = rounded_path(points, r * bend_factor * 2.0)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = M(r)
    cu.bevel_resolution = 6
    cu.resolution_u = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(path) - 1)
    for i, q in enumerate(path):
        sp.points[i].co = (M(q[0]), M(q[1]), M(q[2]), 1.0)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    assign(o, mat)
    link_to(o, coll)
    tag(o, subsystem, "provisional polymer/steel pipe DN%d" % int(dia),
        note or "routed pipe run with swept elbows", status)
    return o


def flange(name, dia, loc, axis="Z", coll="05_PIPING", mat="MAT_Steel_Frame",
           bolts=6):
    """Bolted pipe flange ring at a connection (mm)."""
    od = dia + 2.0 * P["flange_boss"]
    rot = {"Z": (0, 0, 0), "X": (0, 90, 0), "Y": (90, 0, 0)}[axis]
    f = tube(name, od, dia, P["flange_thk"], loc, mat, coll, rot=rot, verts=32)
    r = (od / 2.0) * 0.78
    for i in range(bolts):
        a = 2.0 * math.pi * i / bolts
        if axis == "Z":
            d = (loc[0] + r * math.cos(a), loc[1] + r * math.sin(a), loc[2])
        elif axis == "X":
            d = (loc[0], loc[1] + r * math.cos(a), loc[2] + r * math.sin(a))
        else:
            d = (loc[0] + r * math.cos(a), loc[1], loc[2] + r * math.sin(a))
        bolt(name + "_B%02d" % i, d, size=10.0, coll=coll)
    return f


def gate_valve(name, dia, loc, axis="X", coll="05_PIPING",
               mat="MAT_Pipe_Polymer"):
    """Simplified gate valve: body + bonnet + handwheel (mm)."""
    rot = {"Z": (0, 0, 0), "X": (0, 90, 0), "Y": (90, 0, 0)}[axis]
    body = cyl(name + "_BODY", dia * 1.55, dia * 1.5, loc, mat, coll, rot)
    up = 90 if axis != "Z" else 0
    stem_off = dia * 0.95
    if axis == "Z":
        stem_loc = (loc[0], loc[1], loc[2] + stem_off)
    else:
        stem_loc = (loc[0], loc[1], loc[2] + stem_off)
    cyl(name + "_BONNET", dia * 0.55, stem_off * 1.2, stem_loc, mat, coll)
    cyl(name + "_STEM", dia * 0.16, stem_off * 1.5,
        (stem_loc[0], stem_loc[1], stem_loc[2] + stem_off * 0.9),
        "MAT_Steel_Frame", coll)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=M(dia * 1.05), minor_radius=M(dia * 0.11),
        location=M((stem_loc[0], stem_loc[1],
                    stem_loc[2] + stem_off * 1.8)),
        major_segments=24, minor_segments=10)
    hw = bpy.context.object
    hw.name = name + "_HANDWHEEL"
    assign(hw, "MAT_Safety_Orange")
    link_to(hw, coll)
    g = [body, hw]
    tag_many(g, "Valves", "provisional cast body / steel handwheel",
             "isolation valve", "[PROP]")
    return g


# ------------------------------------------------------------------------------
# Text / annotation helpers
# ------------------------------------------------------------------------------
def text(name, body, loc, size=40.0, rot=(90, 0, 0), mat="MAT_Label",
         coll="08_ANNOT", align="CENTER", bold=False):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = M(size)
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = 0.0
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.location = M(loc)
    o.rotation_euler = [math.radians(a) for a in rot]
    assign(o, mat)
    link_to(o, coll)
    return o


def dim_line(name, p1, p2, offset_axis, offset, body, size=34.0,
             tick=60.0, mat="MAT_Label"):
    """Simple 3D dimension line with end ticks and a centred label.

    p1 / p2 may be given as (x, y) or (x, y, z); they are promoted to 3D so a
    plan-view dimension line works without supplying a z.
    """
    def v3(p):
        if len(p) == 2:
            return Vector((p[0], p[1], 0.0))
        return Vector((p[0], p[1], p[2]))

    a, b = v3(p1), v3(p2)
    axis = v3(offset_axis)
    if axis.length < 1e-9:
        axis = Vector((0, 0, 1))
    d = axis.normalized() * offset
    a2, b2 = a + d, b + d
    pa, pb = tuple(a), tuple(b)
    objs = []
    objs.append(box(name + "_EXT1", (3, 3, 3), pa, mat, "08_ANNOT"))
    objs.append(box(name + "_EXT2", (3, 3, 3), pb, mat, "08_ANNOT"))
    mid = (a2 + b2) / 2.0
    L = (b2 - a2).length
    ang = math.degrees(math.atan2((b2 - a2).z, (b2 - a2).x))
    # orient the thin bar along the measured direction
    if abs((b2 - a2).z) > abs((b2 - a2).x):
        objs.append(box(name + "_BAR", (tick, 3.0, L), tuple(mid), mat,
                        "08_ANNOT"))
        t_loc = tuple(mid + Vector((tick * 0.6, 0, 0)))
    else:
        objs.append(box(name + "_BAR", (L, 3.0, tick), tuple(mid), mat,
                        "08_ANNOT"))
        t_loc = tuple(mid + Vector((0, tick * 0.6, 0)))
    objs.append(box(name + "_T1", (3, 3, tick), tuple(a2), mat, "08_ANNOT"))
    objs.append(box(name + "_T2", (3, 3, tick), tuple(b2), mat, "08_ANNOT"))
    t = text(name + "_TXT", body, t_loc, size, rot=(90, 0, 0), mat=mat)
    objs.append(t)
    return objs


# ==============================================================================
# 3.  ASSEMBLY 00  -  STRUCTURAL SKID FRAME   [PROP]
# ==============================================================================
# The source PDF never mentions a support structure; "modular design" implies a
# transportable unit, so a bolted RHS skid is a proposed design detail.

def build_frame():
    L = P["overall_length"]
    W = P["overall_width"]
    s = P["frame_rhs"]
    wall = P["frame_rhs_wall"]
    dz = P["frame_deck_z"]
    ins = P["frame_post_inset"]

    x0, x1 = 0.0, L
    y0, y1 = -W / 2.0, W / 2.0
    px0, px1 = x0 + ins, x1 - ins
    py0, py1 = y0 + ins, y1 - ins

    objs = []
    # ---- perimeter rails (two per side: deck level + lower tie level)
    for yy, nm in ((py0, "FRONT"), (py1, "REAR")):
        objs.append(box("FRAME_RAIL_%s_TOP" % nm, (px1 - px0 + s, s, s),
                        ((px0 + px1) / 2.0, yy, dz - s / 2.0),
                        "MAT_Steel_Painted", "00_FRAME"))
        objs.append(box("FRAME_RAIL_%s_TIE" % nm, (px1 - px0, s * 0.8, s * 0.8),
                        ((px0 + px1) / 2.0, yy, 60.0),
                        "MAT_Steel_Painted", "00_FRAME"))
    for xx, nm in ((px0, "IN"), (px1, "OUT")):
        objs.append(box("FRAME_RAIL_%s_TOP" % nm, (s, py1 - py0, s),
                        (xx, (py0 + py1) / 2.0, dz - s / 2.0),
                        "MAT_Steel_Painted", "00_FRAME"))
        objs.append(box("FRAME_RAIL_%s_TIE" % nm, (s * 0.8, py1 - py0, s * 0.8),
                        (xx, (py0 + py1) / 2.0, 60.0),
                        "MAT_Steel_Painted", "00_FRAME"))

    # ---- corner posts + intermediate posts
    posts = [(px0, py0), (px1, py0), (px0, py1), (px1, py1)]
    n_bays = 5
    for i in range(1, n_bays):
        xx = px0 + (px1 - px0) * i / n_bays
        posts.append((xx, py0))
        posts.append((xx, py1))
    for i, (xx, yy) in enumerate(posts):
        objs.append(box("FRAME_POST_%02d" % i, (s, s, dz),
                        (xx, yy, dz / 2.0), "MAT_Steel_Painted", "00_FRAME"))
        # levelling foot + base plate
        objs.append(box("FRAME_FOOTPLATE_%02d" % i, (140, 140, 12),
                        (xx, yy, 6), "MAT_Steel_Frame", "00_FRAME"))
        objs.append(cyl("FRAME_LEVELSCREW_%02d" % i, 26, 46,
                        (xx, yy, 35), "MAT_Steel_Frame", "00_FRAME", verts=16))
        for k in range(2):
            a = 45 + 90 * k
            bolt("FRAME_FOOTBOLT_%02d_%d" % (i, k),
                 (xx + 45 * math.cos(math.radians(a)),
                  yy + 45 * math.sin(math.radians(a)), 16),
                 size=12.0, coll="00_FRAME")

    # ---- longitudinal cross members carrying the tank pedestals
    xs = [px0 + (px1 - px0) * i / 6.0 for i in range(1, 6)]
    for i, xx in enumerate(xs):
        objs.append(box("FRAME_CROSSMEM_%02d" % i, (s * 0.8, py1 - py0,
                                                    s * 0.8),
                        (xx, (py0 + py1) / 2.0, dz - s / 2.0),
                        "MAT_Steel_Painted", "00_FRAME"))

    # ---- removable checker plate deck panels between the rails
    for i in range(5):
        xa = px0 + (px1 - px0) * i / 5.0 + 30
        xb = px0 + (px1 - px0) * (i + 1) / 5.0 - 30
        objs.append(box("FRAME_DECKPANEL_%02d" % i, (xb - xa, py1 - py0 - 60,
                                                      6),
                        ((xa + xb) / 2.0, (py0 + py1) / 2.0, dz - 3),
                        "MAT_Steel_Frame", "00_FRAME"))

    # ---- gusset plates at the corners
    for i, (xx, yy) in enumerate(posts[:4]):
        objs.append(box("FRAME_GUSSET_%02d" % i, (10, 150, 150),
                        (xx + (0 if xx < L / 2 else -0), yy, dz - 90),
                        "MAT_Steel_Frame", "00_FRAME"))

    tag_many(objs, "Structural Frame",
             "provisional mild-steel RHS %dx%dx%d mm" % (s, s, wall),
             "bolted transportable skid; no load rating claimed - "
             "requires structural calculation", "[PROP]")
    return objs


def build_pad():
    L = P["overall_length"]
    W = P["overall_width"]
    pad = box("GROUND_PAD", (L + 600, W + 600, 60),
              (L / 2.0, 0, -30), "MAT_Concrete_Pad", "00_FRAME")
    tag(pad, "Structural Frame", "provisional concrete pad",
        "visual datum plane for the skid, not a foundation design",
        "[PROP]")
    return pad


def pedestal(name, cx, cy, w, l, h, coll, top_mat="MAT_Steel_Frame"):
    """Short fabricated pedestal that lifts a tank off the skid deck (mm)."""
    parts = []
    parts.append(box(name + "_PLINTH", (l, w, 12), (cx, cy, h / 2.0 - 6),
                     top_mat, coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("%s_WEB_%d%d" % (name, sx, sy), (10, w * 0.9, h),
                             (cx + sx * (l / 2.0 - 5), cy, h / 2.0),
                             top_mat, coll))
    parts.append(box(name + "_TOPPLATE", (l + 30, w + 30, 14),
                     (cx, cy, h - 7), top_mat, coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bolt(name + "_HOLD_DOWN_%d%d" % (sx, sy),
                 (cx + sx * (l / 2.0 - 20), cy + sy * (w / 2.0 - 20), h + 4),
                 size=12.0, coll=coll)
    return parts


# ==============================================================================
# 4.  ASSEMBLY 01  -  INLET CHAMBER + IRON MESH SCREEN
# ==============================================================================
# [DOC] "heavy-duty rust-resistant iron wire mesh" first barrier; retains
#       polythenes / plastic packaging / bulk waste.
# [PROP] everything else: chamber, tilt, lifting handle, rails, brackets, weir.

def build_inlet_chamber():
    objs = []
    ln = P["inlet_chamber_len"]
    wd = P["inlet_chamber_wid"]
    zt = P["inlet_chamber_ztop"]
    zb = P["inlet_chamber_zbot"]
    w = P["inlet_chamber_wall"]
    cx = ln / 2.0

    x0, x1 = 0.0, ln
    y0, y1 = -wd / 2.0, wd / 2.0
    ix0, ix1 = x0 + w, x1 - w
    iy0, iy1 = y0 + w, y1 - w

    def panel(nm, sx, sy, sz, lx):
        return box("INLET_CHAMBER_" + nm, (sx, sy, sz),
                   (lx[0], lx[1], lx[2]), "MAT_Stainless_Tank", "01_SCREEN")

    objs.append(panel("FLOOR", ln, wd, w, (cx, 0, zb + w / 2.0)))
    objs.append(panel("WALL_W", w, wd, zt - zb, (x0 + w / 2.0, 0,
                                                 (zt + zb) / 2.0)))
    objs.append(panel("WALL_E", w, wd, zt - zb, (x1 - w / 2.0, 0,
                                                 (zt + zb) / 2.0)))
    objs.append(panel("WALL_S", ln - 2 * w, w, zt - zb,
                      (cx, y0 + w / 2.0, (zt + zb) / 2.0)))
    objs.append(panel("WALL_N", ln - 2 * w, w, zt - zb,
                      (cx, y1 - w / 2.0, (zt + zb) / 2.0)))
    # top rim flange (open - the cover is a separate removable part)
    for nm, sx, sy, lx in (
            ("RIM_W", w + 30, wd, (x0, 0, zt)),
            ("RIM_E", w + 30, wd, (x1, 0, zt)),
            ("RIM_S", ln, w + 30, (cx, y0, zt)),
            ("RIM_N", ln, w + 30, (cx, y1, zt))):
        objs.append(box("INLET_CHAMBER_" + nm, (sx, sy, 14),
                        (lx[0], lx[1], zt + 7), "MAT_Stainless_Tank",
                        "01_SCREEN"))

    tag_many(objs, "Inlet Chamber",
             "provisional %g mm stainless plate" % w,
             "water-tight inlet well upstream of the iron mesh screen "
             "[PROP]", "[PROP]")

    # ---- raw sewage body in front of the screen
    water = box("INLET_WATER_RAW", (ix1 - ix0, iy1 - iy0, 400),
                ((ix0 + ix1) / 2.0, 0, P["weir_crest_z"] - 200),
                "MAT_Water_Raw", "01_SCREEN")
    tag(water, "Flow Visuals", "translucent water proxy",
        "visual water level indicator only - colour does NOT indicate "
        "water quality", "[PROP]")
    return objs


def build_screen():
    """Inclined, removable iron mesh screen on a rigid carrier frame."""
    objs = []
    tilt = P["screen_tilt_deg"]
    h = P["screen_clear_h"]
    wid = P["screen_clear_w"]
    bar = P["screen_frame_bar"]
    pitch = P["mesh_pitch"]
    wire = P["mesh_wire_dia"]

    sx = P["screen_x_bottom"]
    zb = P["inlet_chamber_zbot"] + 40
    # screen local frame: centre of the clear aperture
    cx = sx + math.cos(math.radians(tilt)) * h / 2.0
    cz = zb + math.sin(math.radians(tilt)) * h / 2.0

    # ---- carrier frame: 4 bars forming a rigid removable cassette
    rot = (0, 90.0 - tilt, 0)
    for nm, sy, sz, oy, oz in (("BOTTOM", wid + 2 * bar, bar, 0,
                                -h / 2.0 - bar / 2.0),
                               ("TOP", wid + 2 * bar, bar, 0,
                                h / 2.0 + bar / 2.0),
                               ("SIDE_L", bar, h + 2 * bar,
                                -wid / 2.0 - bar / 2.0, 0),
                               ("SIDE_R", bar, h + 2 * bar,
                                wid / 2.0 + bar / 2.0, 0)):
        objs.append(box("SCREEN_01_CARRIER_%s" % nm, (bar, sy, sz),
                        (cx, oy, cz + oz), "MAT_Steel_Frame", "01_SCREEN",
                        rot=rot))

    # ---- the mesh itself: real wires, arrayed along X then Y
    n_v = max(2, int(wid / pitch))
    n_h = max(2, int(h / pitch))
    vert = cyl("SCREEN_01_MESH_WIRE_V", wire, wid, (0, 0, 0),
               "MAT_Iron_Mesh", "01_SCREEN", verts=6)
    av = vert.modifiers.new("Array_V", "ARRAY")
    av.count = n_v
    av.use_relative_offset = False
    av.use_constant_offset = True
    av.constant_offset_displace = (M(pitch) * math.cos(math.radians(tilt)),
                                   0.0, M(pitch) * math.sin(math.radians(tilt)))
    hori = cyl("SCREEN_01_MESH_WIRE_H", wire, h, (0, 0, 0),
               "MAT_Iron_Mesh", "01_SCREEN", rot=(90, 0, 0), verts=6)
    ah = hori.modifiers.new("Array_H", "ARRAY")
    ah.count = n_h
    ah.use_relative_offset = False
    ah.use_constant_offset = True
    ah.constant_offset_displace = (0.0, M(pitch), 0.0)
    for o in (vert, hori):
        o.location = M((cx, -wid / 2.0, cz - h / 2.0))
        o.rotation_euler = [math.radians(a) for a in rot]
        bevel(o, 0.4, 1)
    objs += [vert, hori]

    tag(vert, "Iron Mesh Screen [DOC]",
        "provisional rust-resistant iron wire, %g mm aperture" % pitch,
        "wastewater passes THROUGH this screen; large debris is retained",
        "[DOC]")
    tag(hori, "Iron Mesh Screen [DOC]",
        "provisional rust-resistant iron wire, %g mm aperture" % pitch,
        "horizontal wire array of the mesh cassette", "[DOC]")

    # ---- lift handle + guide rails so the screen can be withdrawn vertically
    hbx = cx - math.cos(math.radians(tilt)) * (h / 2.0 + 90)
    hbz = cz + math.sin(math.radians(tilt)) * (h / 2.0 + 90)
    hb = box("SCREEN_01_HANDLE_BAR", (40, 420, 40), (0, 0, 0),
             "MAT_Steel_Frame", "01_SCREEN")
    hb.location = M((hbx, 0.0, hbz))
    hb.rotation_euler = [math.radians(90 - tilt), 0, 0]
    objs.append(hb)
    for sy in (-1, 1):
        leg = box("SCREEN_01_HANDLE_LEG_%d" % sy, (40, 40, 110), (0, 0, 0),
                  "MAT_Steel_Frame", "01_SCREEN")
        leg.location = M((hbx + math.sin(math.radians(tilt)) * 55,
                          sy * 190,
                          hbz - math.cos(math.radians(tilt)) * 55))
        leg.rotation_euler = [math.radians(tilt), 0, 0]
        objs.append(leg)

    for sy in (-1, 1):
        rail = box("SCREEN_01_GUIDE_RAIL_%s" % ("L" if sy < 0 else "R"),
                   (bar * 0.8, bar, P["inlet_chamber_ztop"] - zb + 200),
                   (cx, sy * (wid / 2.0 + bar * 1.2),
                    (zb + P["inlet_chamber_ztop"] + 200) / 2.0),
                   "MAT_Steel_Frame", "01_SCREEN", rot=(0, 90 - tilt, 0))
        objs.append(rail)

    # ---- clamping brackets that lock the screen in its rails (4 off)
    for sy in (-1, 1):
        for zz in (cz - h / 2.0, cz + h / 2.0):
            objs.append(box("SCREEN_01_CLAMP_%d_%d" % (sy, int(zz)),
                            (90, bar * 1.4, 26),
                            (cx, sy * (wid / 2.0 + bar * 1.4), zz),
                            "MAT_Steel_Frame", "01_SCREEN",
                            rot=(0, 90 - tilt, 0)))
            bolt("SCREEN_01_CLAMP_BOLT_%d_%d" % (sy, int(zz)),
                 (cx, sy * (wid / 2.0 + bar * 2.0), zz), size=10.0,
                 coll="01_SCREEN")

    # ---- lifting clearance annotation object (also documents service access)
    tag_many(objs, "Iron Mesh Screen",
             "provisional mild-steel carrier + iron wire mesh",
             "screen withdraws vertically; clearance required above the "
             "chamber = %g mm (see design_parameters.json)" %
             P["screen_lift_clearance"], "[PROP]")
    return objs


def build_inlet_pipe():
    d = P["inlet_pipe_dia"]
    z = P["inlet_pipe_z"]
    ln = P["inlet_chamber_len"]
    objs = []
    p = pipe("PIPE_INLET_RAW", d,
             [(-420, 0, z), (-60, 0, z), (60, 0, z)],
             "MAT_Pipe_Polymer", "05_PIPING",
             note="raw sewage DN150 inlet into the iron mesh screen chamber")
    objs.append(p)
    objs.append(flange("FLANGE_INLET", d, (-160, 0, z), "X"))
    objs.append(flange("FLANGE_SCREEN_IN", d, (0, 0, z), "X"))
    objs += gate_valve("VALVE_INLET_ISOLATION", d, (-300, 0, z), "X")
    objs.append(box("PIPE_INLET_SUPPORT_BRKT", (60, 200, 120),
                    (-160, 0, z - d / 2.0 - 60), "MAT_Steel_Frame", "05_PIPING"))
    return objs


# ==============================================================================
# 5.  ASSEMBLY 02  -  SEDIMENTATION CHAMBER  (TANK_01_SETTLING)
# ==============================================================================
# [DOC] settling of sand/silt/mud; multi-grade gravel secondary filter.
# [PROP] hopper, drain, valve, lid, support pedestal, baffle.

def build_settling_tank():
    objs = []
    x0 = P["settling_x0"]
    ln = P["settling_len"]
    wd = P["settling_wid"]
    rim = P["settling_rim_z"]
    flr = P["settling_floor_z"]
    w = P["settling_wall"]
    hp = P["hopper_depth"]
    cx = x0 + ln / 2.0

    # ---------------- hopper (sloped bottom collecting settled sludge)
    hop_top = ln - 2 * w
    hop_wid = wd - 2 * w
    hop_bot = P["hopper_drain_dia"] * 2.6
    outer = frustum_box("TANK_01_HOPPER_OUTER", hop_top, hop_wid,
                        hop_bot, hop_bot * 0.8, hp,
                        (cx, 0, flr - hp), "MAT_Stainless_Tank", "02_SETTLING")
    inner = frustum_box("_hopper_inner", hop_top - 2 * w, hop_wid - 2 * w,
                        hop_bot * 0.45, hop_bot * 0.36, hp + 2,
                        (cx, 0, flr - hp - 1), None, "02_SETTLING")
    boolean_diff(outer, inner)
    bpy.data.objects.remove(inner, do_unlink=True)
    objs.append(outer)

    # sludge blanket sitting in the hopper (static, illustrative)
    sludge = frustum_box("TANK_01_SLUDGE_BLANKET", hop_top - 2 * w - 10,
                         hop_wid - 2 * w - 10, hop_bot * 0.7, hop_bot * 0.55,
                         hp * 0.45, (cx, 0, flr - hp + 4),
                         "MAT_Sludge", "02_SETTLING")
    objs.append(sludge)

    # ---------------- four side walls (real thickness, assembled from panels)
    walls = [
        ("WALL_WEST", (w, wd, rim - flr), (x0 + w / 2.0, 0,
                                            (rim + flr) / 2.0)),
        ("WALL_EAST", (w, wd, rim - flr), (x0 + ln - w / 2.0, 0,
                                            (rim + flr) / 2.0)),
        ("WALL_SOUTH", (ln - 2 * w, w, rim - flr),
         (cx, -wd / 2.0 + w / 2.0, (rim + flr) / 2.0)),
        ("WALL_NORTH", (ln - 2 * w, w, rim - flr),
         (cx, wd / 2.0 - w / 2.0, (rim + flr) / 2.0)),
    ]
    for nm, sz, lx in walls:
        o = box("TANK_01_" + nm, sz, lx, "MAT_Stainless_Tank", "02_SETTLING")
        bevel(o, 3.0, 2)
        objs.append(o)

    # ---------------- top rim flange + bolted removable inspection lid
    for nm, sz, lx in (
            ("RIM_W", (w + 30, wd, 16), (x0, 0, rim + 8)),
            ("RIM_E", (w + 30, wd, 16), (x0 + ln, 0, rim + 8)),
            ("RIM_S", (ln, w + 30, 16), (cx, -wd / 2.0, rim + 8)),
            ("RIM_N", (ln, w + 30, 16), (cx, wd / 2.0, rim + 8))):
        objs.append(box("TANK_01_" + nm, sz, lx, "MAT_Stainless_Tank",
                        "02_SETTLING"))
    lid = box("TANK_01_INSPECTION_LID", (ln - 2 * w - 10, wd - 2 * w - 10,
                                         P["lid_thk"]),
              (cx, 0, rim + 16 + P["lid_thk"] / 2.0),
              "MAT_Stainless_Tank", "02_SETTLING")
    bevel(lid, 2.0, 2)
    objs.append(lid)
    lid_gz = rim + 16 + P["lid_thk"] + 6
    bc = P["bolt_count_lid"]
    for i in range(bc):
        a = 2 * math.pi * i / bc
        bolt("TANK_01_LID_BOLT_%02d" % i,
             (cx + (ln / 2 - 55) * math.cos(a), (wd / 2 - 55) * math.sin(a),
              lid_gz), size=12.0, coll="02_SETTLING")
    # lid lifting eyes
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=M(26), minor_radius=M(8),
            location=M((cx, sy * 200, lid_gz + 26)),
            rotation=(math.radians(90), 0, 0),
            major_segments=20, minor_segments=8)
        e = bpy.context.object
        e.name = "TANK_01_LID_LIFT_EYE_%d" % sy
        assign(e, "MAT_Steel_Frame")
        link_to(e, "02_SETTLING")
        objs.append(e)

    # ---------------- inlet baffle (inlet / outlet stilling)
    baffle = box("TANK_01_INLET_BAFFLE", (12, wd - 2 * w - 20, 240),
               (x0 + 300, 0, P["settling_inlet_z"] + 90),
               "MAT_Stainless_Tank", "02_SETTLING")
    objs.append(baffle)

    # ---------------- water body at the provisional operating level
    wl = P["settling_water_level_z"]
    water = box("TANK_01_WATER_BODY", (ln - 2 * w - 6, wd - 2 * w - 6,
                                       wl - (flr + 90)),
                (cx, 0, (flr + 90 + wl) / 2.0), "MAT_Water_Raw", "02_SETTLING")
    objs.append(water)

    objs += pedestal("TANK_01_PEDESTAL", cx, 0, wd + 120, ln - 160,
                     P["settling_support_h"], "02_SETTLING")

    tag_many([o for o in objs if o.name.startswith("TANK_01_W")],
             "Flow Visuals", "translucent water proxy",
             "settling zone water level - visual only", "[PROP]")
    for o in objs:
        if o.name.startswith("TANK_01_"):
            tag(o, "Sedimentation Chamber",
                "provisional %g mm stainless plate / mild steel" % w,
                "sloped hopper collects settled sludge; freeboard and "
                "level are provisional", "[PROP]")
    tag(outer, "Sedimentation Chamber",
        "provisional stainless plate",
        "hopper side slope = %g deg from horizontal (typical repose range "
        "for drained sand is 35-45 deg; 55 deg is a provisional "
        "self-cleaning assumption requiring geotechnical check)" %
        P["hopper_angle_deg"], "[PROP]")
    tag(sludge, "Sludge Accumulation", "provisional settled solids",
        "illustrative sludge blanket - not a volume or mass calculation",
        "[PROP]")
    tag(lid, "Maintenance Access", "provisional stainless plate",
        "bolted removable inspection lid, %d fasteners" % bc, "[PROP]")
    return objs


def build_gravel_bed():
    """[DOC] multi-grade gravel secondary filter inside the settling tank.
    Placed only in the downstream third so it does not obstruct settling."""
    objs = []
    gx = P["gravel_x0"]
    gl = P["gravel_len"]
    gw = P["gravel_wid"]
    gz = P["gravel_z0"]
    thk = P["gravel_layer_thk"]
    n = P["gravel_layers"]
    cz = gx + gl / 2.0

    objs.append(box("MEDIA_02_UNDERDRAIN_PAN", (gl, gw, P["gravel_underdrain_h"]),
                    (cz, 0, gz - P["gravel_underdrain_h"] / 2.0),
                    "MAT_Stainless_Tank", "02_SETTLING"))
    for i in range(n):
        # coarse at the bottom, fine on top = classic multi-grade bed
        t = gz + i * thk
        o = box("MEDIA_02_GRAVEL_L%d" % (i + 1), (gl, gw, thk - 2),
                (cz, 0, t + thk / 2.0), "MAT_Gravel", "02_SETTLING")
        bevel(o, 8.0, 2)
        objs.append(o)
        tag(o, "Gravel / Secondary Media [DOC]",
            "provisional multi-grade gravel layer %d of %d" % (i + 1, n),
            "graded gravel/sand bed - grain size distribution NOT specified "
            "in the source document", "[DOC]")
    tag(objs[0], "Gravel / Secondary Media [DOC]",
        "provisional stainless plate",
        "underdrain pan supporting the multi-grade bed and collecting the "
        "clarified water draw-off", "[PROP]")

    # retaining walls of the media cell
    for nm, sz, lx in (
            ("MEDIA_02_CELL_W", (10, gw + 20, n * thk + 40),
             (gx - 5, 0, gz + (n * thk + 40) / 2.0)),
            ("MEDIA_02_CELL_E", (10, gw + 20, n * thk + 40),
             (gx + gl + 5, 0, gz + (n * thk + 40) / 2.0))):
        o = box(nm, sz, lx, "MAT_Stainless_Tank", "02_SETTLING")
        tag(o, "Gravel / Secondary Media [DOC]", "provisional stainless plate",
            "media cell retaining wall", "[PROP]")
        objs.append(o)
    return objs


# ==============================================================================
# 6.  ASSEMBLY 03  -  FABRIC POLISHING CHAMBER  (FILTER_02_FABRIC)
# ==============================================================================
# [DOC] "high-tensile porous synthetic fabric filter", removes micro solids.
# [PROP] cartridge/bag frame, top cover, support, lifting frame, sealing flange.

def build_fabric_chamber():
    objs = []
    x0 = P["fabric_x0"]
    ln = P["fabric_len"]
    wd = P["fabric_wid"]
    rim = P["fabric_rim_z"]
    flr = P["fabric_floor_z"]
    w = P["fabric_wall"]
    cx = x0 + ln / 2.0

    objs.append(box("FILTER_02_FLOOR", (ln, wd, w),
                    (cx, 0, flr + w / 2.0), "MAT_Stainless_Tank", "03_FABRIC"))
    for nm, sz, lx in (
            ("WALL_W", (w, wd, rim - flr), (x0 + w / 2.0, 0,
                                            (rim + flr) / 2.0)),
            ("WALL_E", (w, wd, rim - flr), (x0 + ln - w / 2.0, 0,
                                            (rim + flr) / 2.0)),
            ("WALL_S", (ln - 2 * w, w, rim - flr),
             (cx, -wd / 2.0 + w / 2.0, (rim + flr) / 2.0)),
            ("WALL_N", (ln - 2 * w, w, rim - flr),
             (cx, wd / 2.0 - w / 2.0, (rim + flr) / 2.0))):
        o = box("FILTER_02_" + nm, sz, lx, "MAT_Stainless_Tank", "03_FABRIC")
        bevel(o, 3.0, 2)
        objs.append(o)
    # top flange that the removable cover bolts onto
    for nm, sz, lx in (
            ("FLANGE_W", (w + 30, wd, 16), (x0, 0, rim + 8)),
            ("FLANGE_E", (w + 30, wd, 16), (x0 + ln, 0, rim + 8)),
            ("FLANGE_S", (ln, w + 30, 16), (cx, -wd / 2.0, rim + 8)),
            ("FLANGE_N", (ln, w + 30, 16), (cx, wd / 2.0, rim + 8))):
        objs.append(box("FILTER_02_" + nm, sz, lx, "MAT_Stainless_Tank",
                        "03_FABRIC"))
    # cover sealing gasket (thin dark ring)
    objs.append(box("FILTER_02_COVER_GASKET", (ln - 2 * w - 60, wd - 2 * w - 60,
                                               4),
                    (cx, 0, rim + 17), "MAT_Rubber_Black", "03_FABRIC"))
    water = box("FILTER_02_WATER_BODY",
                (ln - 2 * w - 6, wd - 2 * w - 6,
                 P["fabric_water_level_z"] - (flr + 60)),
                (cx, 0, (flr + 60 + P["fabric_water_level_z"]) / 2.0),
                "MAT_Water_Polished", "03_FABRIC")
    objs.append(water)

    objs += pedestal("FILTER_02_PEDESTAL", cx, 0, wd + 100, ln - 140,
                     P["fabric_support_h"], "03_FABRIC")

    for o in objs:
        if o.name.startswith("FILTER_02_") and "WATER" not in o.name:
            tag(o, "Fabric Polishing Chamber",
                "provisional %g mm stainless plate" % w,
                "water-tight polishing chamber; volume and residence time "
                "NOT calculated", "[PROP]")
    return objs


def build_fabric_element():
    """Removable framed fabric filter element - lifts straight out of the top."""
    objs = []
    x0 = P["fabric_x0"]
    ln = P["fabric_len"]
    wd = P["fabric_wid"]
    rim = P["fabric_rim_z"]
    flr = P["fabric_floor_z"]
    bar = P["filter_frame_bar"]
    thk = P["filter_media_thk"]
    cx = x0 + ln / 2.0
    ew = wd - 2 * P["fabric_wall"] - 120      # element width
    el = ln - 2 * P["fabric_wall"] - 200      # element length
    eh = 520.0
    ez = flr + 120

    # ---- rigid support grid: top and bottom spreader frames + vertical posts
    for zz, nm in ((ez + eh / 2.0, "TOP"), (ez - eh / 2.0, "BOT")):
        for sy in (-1, 1):
            objs.append(box("FILTER_02_FRAME_%s_Y%d" % (nm, sy),
                            (el + 2 * bar, bar, bar),
                            (cx, sy * (ew / 2.0 + bar / 2.0), zz),
                            "MAT_Steel_Frame", "03_FABRIC"))
        for sx in (-1, 1):
            objs.append(box("FILTER_02_FRAME_%s_X%d" % (nm, sx),
                            (bar, ew + 2 * bar, bar),
                            (cx + sx * (el / 2.0 + bar / 2.0), 0, zz),
                            "MAT_Steel_Frame", "03_FABRIC"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box("FILTER_02_FRAME_POST_%d%d" % (sx, sy),
                            (bar * 0.8, bar * 0.8, eh),
                            (cx + sx * (el / 2.0 + bar / 2.0),
                             sy * (ew / 2.0 + bar / 2.0), ez),
                            "MAT_Steel_Frame", "03_FABRIC"))

    # ---- the cloth itself: two cloth bags, dirty side facing the inlet
    for i, sx in enumerate((-1, 1)):
        cloth = box("FILTER_02_CLOTH_MEDIA_%d" % (i + 1), (thk, ew, eh),
                    (cx + sx * 90, 0, ez), "MAT_Fabric_Filter", "03_FABRIC")
        objs.append(cloth)
        tag(cloth, "Fabric Filter [DOC]",
            "provisional high-tensile porous synthetic cloth",
            "documented cloth polishing element; pore size / areal weight / "
            "flow rate NOT specified in the source", "[DOC]")
        # sewn seam battens give the cloth a believable formed shape
        for sy in (-1, 1):
            objs.append(box("FILTER_02_CLOTH_SEAM_%d%d" % (i + 1, sy),
                            (thk * 1.8, 26, eh - 20),
                            (cx + sx * 90, sy * (ew / 2.0 - 20), ez),
                            "MAT_Fabric_Filter", "03_FABRIC"))
    # hanging loops so the element can be lifted out
    for sx in (-1, 1):
        for sy in (-1, 1):
            bpy.ops.mesh.primitive_torus_add(
                major_radius=M(22), minor_radius=M(6),
                location=M((cx + sx * (el / 2.0), sy * 200,
                            ez + eh / 2.0 + bar + 22)),
                rotation=(0, math.radians(90), 0),
                major_segments=16, minor_segments=8)
            t = bpy.context.object
            t.name = "FILTER_02_LIFT_LOOP_%d%d" % (sx, sy)
            assign(t, "MAT_Steel_Frame")
            link_to(t, "03_FABRIC")
            objs.append(t)

    # ---- top cover: removable, bolted, with lifting handle
    cov = box("FILTER_02_TOP_COVER", (ln, wd, P["lid_thk"]),
              (cx, 0, rim + 24 + P["lid_thk"] / 2.0),
              "MAT_Stainless_Tank", "03_FABRIC")
    bevel(cov, 2.0, 2)
    objs.append(cov)
    ov = P["cover_lip_overhang"]
    for nm, sz, lx in (
            ("COVER_LIP_W", (ov, wd, 40), (x0 - ov / 2.0, 0, rim + 4)),
            ("COVER_LIP_E", (ov, wd, 40), (x0 + ln + ov / 2.0, 0, rim + 4)),
            ("COVER_LIP_S", (ln, ov, 40), (cx, -wd / 2.0 - ov / 2.0, rim + 4)),
            ("COVER_LIP_N", (ln, ov, 40), (cx, wd / 2.0 + ov / 2.0, rim + 4))):
        objs.append(box("FILTER_02_" + nm, sz, lx, "MAT_Stainless_Tank",
                        "03_FABRIC"))
    for sy in (-1, 1):
        objs.append(cyl("FILTER_02_COVER_HANDLE_POST_%d" % sy, 18, 130,
                        (cx, sy * 200, rim + 24 + P["lid_thk"] + 65),
                        "MAT_Steel_Frame", "03_FABRIC", verts=12))
    objs.append(cyl("FILTER_02_COVER_HANDLE_BAR",
                    P["cover_handle_dia"], 400,
                    (cx, 0, rim + 24 + P["lid_thk"] + 130),
                    "MAT_Steel_Frame", "03_FABRIC", rot=(90, 0, 0), verts=12))
    for i in range(8):
        a = 2 * math.pi * i / 8
        bolt("FILTER_02_COVER_BOLT_%02d" % i,
             (cx + (ln / 2 - 45) * math.cos(a), (wd / 2 - 45) * math.sin(a),
              rim + 24 + P["lid_thk"] + 8), size=10.0, coll="03_FABRIC")

    tag(cov, "Maintenance Access", "provisional stainless plate",
        "bolted removable top cover - clear vertical lift space above the "
        "chamber must be >= %g mm for filter replacement" %
        P["filter_lift_clearance"], "[PROP]")
    for o in objs:
        if o.name.startswith("FILTER_02_FRAME"):
            tag(o, "Fabric Filter [DOC]", "provisional mild-steel support grid",
                "spreader frame carrying and sealing the cloth element",
                "[PROP]")
    return objs


# ==============================================================================
# 7.  ASSEMBLY 04  -  BELT CONVEYOR  (CONVEYOR_01_*)   [DOC]
# ==============================================================================
# [DOC] "motorized belt conveyor with scraper blades", continuous or sensor
#       triggered, moving debris from the chambers into a disposal bin.
# [PROP] drive/tail roller bearings, belt-tensioning screws, side rails,
#        gearbox, guard, legs, discharge chute. Belt WIDTH / speed / motor
#        POWER are NOT specified by the source.

def belt_profile(c1, c2, r, seg=18):
    """Stadium profile (mm) of a belt loop wrapping two equal-radius rollers.
    c1 = tail roller centre (x,z), c2 = head roller centre (x,z)."""
    c1 = Vector((c1[0], c1[1]))
    c2 = Vector((c2[0], c2[1]))
    d = (c2 - c1)
    L = d.length
    d.normalize()
    p = Vector((-d.y, d.x))
    if p.y < 0:
        p = -p
    a1 = c1 + p * r
    a2 = c2 + p * r
    pts = [tuple(a1), tuple(a2)]
    # wrap around the head roller (through the forward direction d)
    a_start = math.atan2(p.y, p.x)
    a_end = a_start - 2 * math.pi
    for k in range(1, seg):
        a = a_start + (a_end - a_start) * k / seg
        pts.append((c2.x + r * math.cos(a), c2.y + r * math.sin(a)))
    b2 = c2 - p * r
    b1 = c1 - p * r
    pts.append(tuple(b2))
    pts.append(tuple(b1))
    # wrap around the tail roller (through -d)
    a_start = math.atan2(b1.y - c1.y, b1.x - c1.x)
    for k in range(1, seg):
        a = a_start - 2 * math.pi * k / seg
        pts.append((c1.x + r * math.cos(a), c1.y + r * math.sin(a)))
    return pts


def build_conveyor():
    objs = []
    tx, ty, tz = P["conv_tail"]
    hx, hy, hz = P["conv_head"]
    rd = P["conv_roller_dia"]
    rr = rd / 2.0
    bw = P["conv_belt_width"]
    bthk = P["conv_belt_thk"]
    rail = P["conv_side_rail"]

    ang = math.degrees(math.atan2(hz - tz, hx - tx))
    mid = Vector(((tx + hx) / 2.0, (ty + hy) / 2.0, (tz + hz) / 2.0))
    run = math.hypot(hx - tx, hz - tz)

    # ------------------------------------------------------------- belt loop
    prof = belt_profile((tx, tz), (hx, hz), rr + bthk)
    me = bpy.data.meshes.new("CONVEYOR_01_BELT")
    bm = bmesh.new()
    rows = []
    for (px, pz) in prof:
        rows.append([bm.verts.new((M(px), M(-bw / 2.0), M(pz))),
                     bm.verts.new((M(px), M(bw / 2.0), M(pz)))])
    n = len(rows)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([rows[i][0], rows[i][1], rows[j][1], rows[j][0]])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    belt = bpy.data.objects.new("CONVEYOR_01_BELT", me)
    bpy.context.scene.collection.objects.link(belt)
    sol = belt.modifiers.new("Belt_Thickness", "SOLIDIFY")
    sol.thickness = M(bthk)
    sol.offset = 0.0
    assign(belt, "MAT_Rubber_Belt")
    shade_smooth(belt)
    link_to(belt, "04_CONVEYOR")
    tag(belt, "Conveyor [DOC]", "provisional rubber belt, %g mm wide" % bw,
        "documented conveyor belt; belt speed / throughput NOT specified",
        "[DOC]")
    objs.append(belt)

    # cleats on the carrying strand (visualises movement in the animation)
    for i in range(10):
        f = (i + 0.5) / 10.0
        cxl = tx + (hx - tx) * f
        czl = tz + (hz - tz) * f
        objs.append(box("CONVEYOR_01_CLEAT_%02d" % i,
                        (26, bw - 40, 34),
                        (cxl, ty, czl + rr + bthk + 17),
                        "MAT_Rubber_Belt", "04_CONVEYOR", rot=(0, -ang, 0)))

    # ------------------------------------------------- drive + tail rollers
    drv = tube("CONVEYOR_01_DRIVE_ROLLER", rd, 0, bw,
               (hx, ty, hz), "MAT_Steel_Frame", "04_CONVEYOR",
               rot=(90, 0, 0), verts=32)
    tail = tube("CONVEYOR_01_TAIL_ROLLER", rd, 0, bw,
                (tx, ty, tz), "MAT_Steel_Frame", "04_CONVEYOR",
                rot=(90, 0, 0), verts=32)
    shade_smooth(drv)
    shade_smooth(tail)
    tag(drv, "Conveyor [DOC]", "provisional steel roller, dia %g mm" % rd,
        "motor-driven head roller", "[DOC]")
    tag(tail, "Conveyor [PROP]", "provisional steel roller, dia %g mm" % rd,
        "tail roller on tensioning slides", "[PROP]")
    objs += [drv, tail]

    # bearing pillow blocks (4 off) + tensioning screws at the tail
    for (rx, rz, nm) in ((hx, hz, "HEAD"), (tx, tz, "TAIL")):
        for sy in (-1, 1):
            px = rx + sy * (bw / 2.0 + 55) * (1 if rx == hx else -1)
            objs.append(box("CONVEYOR_01_BEARING_%s_%d" % (nm, sy),
                            (150, 90, 150),
                            (rx + sy * (bw / 2.0 + 55), ty, rz),
                            "MAT_Steel_Painted", "04_CONVEYOR",
                            rot=(0, 0, 0)))
            cyl("CONVEYOR_01_BEARING_SHAFT_%s_%d" % (nm, sy), 40,
                bw + 240, (rx, ty, rz), "MAT_Steel_Frame", "04_CONVEYOR",
                rot=(90, 0, 0), verts=16)
            if nm == "TAIL":
                # belt tension adjuster: threaded screw + hand nut
                cyl("CONVEYOR_01_TENSION_SCREW_%d" % sy, 18, 170,
                    (rx - sy * 130, ty, rz), "MAT_Steel_Frame", "04_CONVEYOR",
                    rot=(0, 90, 0), verts=12)
                objs.append(box("CONVEYOR_01_TENSION_NUT_%d" % sy, (46, 46, 46),
                                (rx - sy * 200, ty, rz), "MAT_Steel_Frame",
                                "04_CONVEYOR"))
    tag(objs[-1], "Conveyor [PROP]", "provisional mild steel",
        "take-up screws give %g mm of belt tension adjustment" %
        P["tensioner_stroke"], "[PROP]")

    # -------------------------------------------------------------- idlers
    for i in range(P["conv_idler_count"]):
        f = (i + 1) / (P["conv_idler_count"] + 1.0)
        ix = tx + (hx - tx) * f
        iz = tz + (hz - tz) * f
        idl = tube("CONVEYOR_01_IDLER_%02d" % i, rd * 0.8, 0, bw - 30,
                   (ix, ty, iz), "MAT_Steel_Frame", "04_CONVEYOR",
                   rot=(90, 0, 0), verts=24)
        shade_smooth(idl)
        objs.append(idl)
        for sy in (-1, 1):
            objs.append(box("CONVEYOR_01_IDLER_MOUNT_%02d_%d" % (i, sy),
                            (70, 30, 90), (ix, ty + sy * (bw / 2.0 - 20), iz),
                            "MAT_Steel_Painted", "04_CONVEYOR",
                            rot=(0, 0, 0)))

    # ------------------------------------------------------------ side rails
    for sy in (-1, 1):
        rail_c = box("CONVEYOR_01_SIDE_RAIL_%s" % ("L" if sy < 0 else "R"),
                     (run + 300, rail, 180),
                     (mid.x, ty + sy * (bw / 2.0 + 45), mid.z),
                     "MAT_Steel_Painted", "04_CONVEYOR", rot=(0, -ang, 0))
        objs.append(rail_c)
        # skirt boards close the gap between belt and rail (contain spillage)
        objs.append(box("CONVEYOR_01_SKIRT_%s" % ("L" if sy < 0 else "R"),
                        (run + 200, 14, 120),
                        (mid.x, ty + sy * (bw / 2.0 + 14), mid.z + 26),
                        "MAT_Steel_Painted", "04_CONVEYOR", rot=(0, -ang, 0)))

    # ------------------------------------------------- scraper blade [DOC]
    sc_l = P["scraper_blade_len"]
    sc_t = P["scraper_blade_thk"]
    scx = hx - 190
    scz = tz + (hz - tz) * ((scx - tx) / (hx - tx)) - rr - bthk - 40
    blade = box("CONVEYOR_01_SCRAPER_BLADE", (sc_t, sc_l, 90),
                (scx, ty, scz), "MAT_Steel_Frame", "04_CONVEYOR",
                rot=(0, -ang, 0))
    objs.append(blade)
    tag(blade, "Conveyor [DOC]", "provisional hardened steel / polymer blade",
        "documented scraper blade wiping the return strand and discharging "
        "solids into the bin", "[DOC]")
    for sy in (-1, 1):
        objs.append(box("CONVEYOR_01_SCRAPER_ARM_%d" % sy,
                        (40, 60, 300),
                        (scx, ty + sy * (bw / 2.0 + 70), scz - 170),
                        "MAT_Steel_Painted", "04_CONVEYOR", rot=(0, -ang, 0)))
        objs.append(box("CONVEYOR_01_SCRAPER_TIE_%d" % sy,
                        (240, 30, 30),
                        (scx - 60, ty + sy * (bw / 2.0 + 70), scz - 20),
                        "MAT_Steel_Painted", "04_CONVEYOR", rot=(0, -ang, 0)))

    # ----------------------------------------- motor + gearbox [PROP envelope]
    gl = P["gearbox_len"]
    gw = P["gearbox_wid"]
    gh = P["gearbox_hgt"]
    gbx = hx + 150
    objs.append(box("CONVEYOR_01_GEARBOX_HOUSING", (gl, gw, gh),
                    (gbx, ty, hz + 30), "MAT_Motor_Blue", "04_CONVEYOR"))
    objs.append(box("CONVEYOR_01_GEARBOX_MOUNT", (gl + 40, gw + 40, 20),
                    (gbx, ty, hz - gh / 2.0 - 2), "MAT_Steel_Frame",
                    "04_CONVEYOR"))
    cyl("CONVEYOR_01_MOTOR_BODY", P["motor_dia"], P["motor_len"],
        (gbx + gl / 2.0 + P["motor_len"] / 2.0, ty, hz + 30),
        "MAT_Motor_Blue", "04_CONVEYOR", rot=(0, 90, 0), verts=24)
    objs.append(box("CONVEYOR_01_MOTOR_TERMINAL_BOX", (90, 90, 70),
                    (gbx + gl / 2.0 + P["motor_len"] / 2.0, ty, hz + 30 + 110),
                    "MAT_Motor_Blue", "04_CONVEYOR"))
    objs.append(box("CONVEYOR_01_MOTOR_TERMINAL_FAN_COWL", (70, P["motor_dia"],
                                                            P["motor_dia"]),
                    (gbx + gl / 2.0 + P["motor_len"] + 35, ty, hz + 30),
                    "MAT_Motor_Blue", "04_CONVEYOR"))
    for o in objs[-4:]:
        tag(o, "Conveyor Drive [DOC]", "provisional gearmotor envelope",
            "the PDF states only 'motorized'; motor power, ratio, speed and "
            "gear type are NOT specified - envelope shown is a placeholder",
            "[PROP]")

    # ------------------------------------------------------- drive guard
    gd = P["guard_thk"]
    for sy in (-1, 1):
        objs.append(box("CONVEYOR_01_GUARD_PLATE_%d" % sy,
                        (gl + 260, gd, 420),
                        (gbx, ty + sy * (gw / 2.0 + 60), hz + 30),
                        "MAT_Safety_Orange", "04_CONVEYOR"))
    objs.append(box("CONVEYOR_01_GUARD_TOP", (gl + 260, gw + 130, gd),
                    (gbx, ty, hz + 240), "MAT_Safety_Orange", "04_CONVEYOR"))
    for o in objs[-3:]:
        tag(o, "Safety [PROP]", "provisional perforated steel guard",
            "guard added around the nip point - not mentioned in the source",
            "[PROP]")

    # ------------------------------------------------------------ support legs
    for i, lx in enumerate(P["conv_leg_positions"]):
        f = (lx - tx) / (hx - tx)
        lz = tz + (hz - tz) * f
        top = lz - 90
        for sy in (-1, 1):
            objs.append(box("CONVEYOR_01_LEG_%02d_%d" % (i, sy),
                            (70, 70, top - P["frame_deck_z"]),
                            (lx, ty + sy * (bw / 2.0 + 45),
                             (top + P["frame_deck_z"]) / 2.0),
                            "MAT_Steel_Painted", "04_CONVEYOR"))
            objs.append(box("CONVEYOR_01_LEG_FOOT_%02d_%d" % (i, sy),
                            (160, 160, 12),
                            (lx, ty + sy * (bw / 2.0 + 45),
                             P["frame_deck_z"] + 6),
                            "MAT_Steel_Frame", "04_CONVEYOR"))
        objs.append(box("CONVEYOR_01_LEG_CROSS_%02d" % i,
                        (60, bw + 160, 60),
                        (lx, ty, P["frame_deck_z"] + 120),
                        "MAT_Steel_Painted", "04_CONVEYOR"))
        objs.append(box("CONVEYOR_01_LEG_TOPPLATE_%02d" % i,
                        (140, bw + 180, 14), (lx, ty, top - 7),
                        "MAT_Steel_Frame", "04_CONVEYOR"))
        objs.append(box("CONVEYOR_01_KNEE_BRACE_%02d" % i,
                        (500, 50, 50), (lx - 150, ty + bw / 2.0 + 45,
                                        top - 300),
                        "MAT_Steel_Painted", "04_CONVEYOR", rot=(0, 45, 0)))

    for o in objs:
        if not o.get("design_status") and o.name.startswith("CONVEYOR_"):
            tag(o, "Conveyor Structure [PROP]",
                "provisional mild steel",
                "conveyor structural / supporting component", "[PROP]")

    # ---- discharge chute delivering into the bin (closes the solids path)
    objs.append(build_discharge_chute(hx, ty, hz, ang))
    return objs


def build_discharge_chute(hx, ty, hz, ang):
    parts = []
    top_z = hz - 40
    bx = P["bin_x0"] + 240
    by = P["bin_y0"] + P["bin_wid"] / 2.0
    parts.append(box("CONVEYOR_01_DISCHARGE_CHUTE",
                     (700, P["conv_belt_width"] - 40, 10),
                     ((hx + bx) / 2.0 + 60, ty, (top_z + 700) / 2.0),
                     "MAT_Steel_Frame", "04_CONVEYOR",
                     rot=(0, math.degrees(math.atan2(top_z - 700,
                                                    bx - hx + 120)), 0)))
    for sy in (-1, 1):
        parts.append(box("CONVEYOR_01_CHUTE_SIDE_%d" % sy,
                         (760, 10, 220),
                         ((hx + bx) / 2.0 + 60,
                          ty + sy * ((P["conv_belt_width"] - 40) / 2.0),
                          (top_z + 700) / 2.0 + 100),
                         "MAT_Steel_Frame", "04_CONVEYOR",
                         rot=(0, math.degrees(math.atan2(top_z - 700,
                                                        bx - hx + 120)), 0)))
    parts.append(box("CONVEYOR_01_CHUTE_MOUNT_ARM", (60, 60, 900),
                     (hx + 420, ty, (top_z + 700) / 2.0 - 60),
                     "MAT_Steel_Painted", "04_CONVEYOR",
                     rot=(0, 20, 0)))
    tag_many(parts, "Conveyor [PROP]", "provisional mild steel",
             "discharge chute - proposed mechanism connecting the conveyor to "
             "the waste bin; NOT specified in the source document", "[PROP]")
    return parts


# ==============================================================================
# 8.  ASSEMBLY 06  -  SLUDGE / SOLID WASTE COLLECTION BIN   [PROP]
# ==============================================================================
def build_bin():
    objs = []
    bl = P["bin_len"]
    bw = P["bin_wid"]
    bh = P["bin_hgt"]
    x0 = P["bin_x0"]
    y0 = P["bin_y0"]
    z0 = P["bin_floor_z"]
    w = P["bin_wall"]
    cx = x0 + bl / 2.0
    cy = y0 + bw / 2.0

    objs.append(box("BIN_01_FLOOR", (bl, bw, w), (cx, cy, z0 + w / 2.0),
                    "MAT_Steel_Painted", "06_BIN"))
    for nm, sz, lx in (
            ("WALL_W", (w, bw, bh), (x0 + w / 2.0, cy, z0 + bh / 2.0)),
            ("WALL_E", (w, bw, bh), (x0 + bl - w / 2.0, cy, z0 + bh / 2.0)),
            ("WALL_S", (bl - 2 * w, w, bh), (cx, y0 + w / 2.0,
                                             z0 + bh / 2.0)),
            ("WALL_N", (bl - 2 * w, w, bh), (cx, y0 + bw - w / 2.0,
                                             z0 + bh / 2.0))):
        objs.append(box("BIN_01_" + nm, sz, lx, "MAT_Steel_Painted", "06_BIN"))
    # internal divider -> solids bay | sludge bay
    objs.append(box("BIN_01_DIVIDER", (10, bw - 2 * w, bh - 20),
                    (P["bin_divider_x"], cy, z0 + bh / 2.0),
                    "MAT_Steel_Painted", "06_BIN"))
    # rim, fork pockets and drag handle
    for nm, sz, lx in (
            ("RIM_W", (w + 30, bw, 20), (x0, cy, z0 + bh + 10)),
            ("RIM_E", (w + 30, bw, 20), (x0 + bl, cy, z0 + bh + 10)),
            ("RIM_S", (bl, w + 30, 20), (cx, y0, z0 + bh + 10)),
            ("RIM_N", (bl, w + 30, 20), (cx, y0 + bw, z0 + bh + 10))):
        objs.append(box("BIN_01_" + nm, sz, lx, "MAT_Steel_Frame", "06_BIN"))
    for sy in (-1, 1):
        objs.append(box("BIN_01_FORK_POCKET_%d" % sy,
                        (300, 110, 70),
                        (x0 + bl / 2.0, cy + sy * (bw - 40),
                         z0 + bh - 90), "MAT_Rubber_Black", "06_BIN"))
    cyl("BIN_01_DRAG_HANDLE", 22, P["bin_drag_handle"],
        (x0 + bl - 40, cy, z0 + 60), "MAT_Steel_Frame", "06_BIN",
        rot=(0, 90, 0), verts=12)
    for sy in (-1, 1):
        objs.append(box("BIN_01_HANDLE_LEG_%d" % sy, (40, 40, 90),
                        (x0 + bl - 40, cy + sy * (P["bin_drag_handle"] / 2 - 20),
                         z0 + 30), "MAT_Steel_Frame", "06_BIN"))

    # illustrative contents: retained plastics (left bay) and sludge (right bay)
    objs.append(box("BIN_01_RETAINED_SOLIDS", (P["bin_divider_x"] - x0 - 60,
                                               bw - 2 * w - 20, 200),
                    ((x0 + P["bin_divider_x"]) / 2.0, cy, z0 + 100),
                    "MAT_Sludge", "06_BIN"))
    objs.append(box("BIN_01_SLUDGE_CONTENTS",
                    (x0 + bl - P["bin_divider_x"] - 60, bw - 2 * w - 20, 240),
                    ((P["bin_divider_x"] + x0 + bl) / 2.0, cy, z0 + 120),
                    "MAT_Sludge", "06_BIN"))

    tag_many(objs, "Waste Collection Bin [DOC]",
             "provisional mild steel, fork-pocket / drag-handle bin",
             "documented 'secure disposal bins'; split bay is a PROPOSED "
             "arrangement separating screened solids from drained sludge",
             "[DOC]")
    return objs


# ==============================================================================
# 9.  ASSEMBLY 05  -  INTERCONNECTING PIPING & OUTLET
# ==============================================================================
# Process order: inlet -> iron mesh -> settling/gravel -> fabric filter ->
# clean-water outlet.  Sludge branch is deliberately a different colour and a
# different route so the two are never confused.

def build_piping():
    objs = []
    dt = P["transfer_pipe_dia"]
    df = P["filtered_pipe_dia"]
    do = P["outlet_pipe_dia"]
    ds = P["sludge_pipe_dia"]

    # ---- inlet chamber -> settling tank (transfer, raw)
    z = P["settling_inlet_z"]
    objs.append(pipe("PIPE_01_TRANSFER_RAW", dt,
                     [(P["inlet_chamber_len"] - 40, 0, P["weir_crest_z"] - 90),
                      (P["inlet_chamber_len"] + 90, 0,
                       P["weir_crest_z"] - 90),
                      (P["inlet_chamber_len"] + 90, 0, z),
                      (P["settling_x0"] + 40, 0, z)],
                     "MAT_Pipe_Polymer", "05_PIPING",
                     note="weir overflow from the screen chamber into the "
                          "settling tank"))
    objs.append(flange("FLANGE_TRANSFER_IN", dt,
                       (P["settling_x0"] - 10, 0, z), "X"))
    objs.append(box("PIPE_01_TRANSFER_WALL_BRKT", (30, 260, 40),
                    (P["settling_x0"] - 40, 0, z - dt / 2 - 20),
                    "MAT_Steel_Frame", "05_PIPING"))

    # ---- settling tank -> fabric chamber (clarified, filtered water)
    zf = P["fabric_inlet_z"]
    objs.append(pipe("PIPE_02_SETTLING_TO_FABRIC", df,
                     [(P["gravel_x0"] + P["gravel_len"] / 2.0, -260,
                       P["settling_draw_off_z"]),
                      (P["fabric_x0"] - 130, -260, P["settling_draw_off_z"]),
                      (P["fabric_x0"] - 130, -260, zf),
                      (P["fabric_x0"] - 10, -260, zf)],
                     "MAT_Pipe_Polymer", "05_PIPING",
                     note="clarified water draw-off taken from UNDER the "
                          "multi-grade gravel bed"))
    objs.append(flange("FLANGE_FABRIC_IN", df, (P["fabric_x0"] - 10, -260, zf),
                       "X"))
    objs += gate_valve("VALVE_FABRIC_IN", df,
                       (P["fabric_x0"] - 230, -260, zf), "X")
    objs.append(box("PIPE_02_SUPPORT_BRKT", (40, 260, 40),
                    (P["fabric_x0"] - 130, -260, zf - df / 2 - 20),
                    "MAT_Steel_Frame", "05_PIPING"))

    # ---- fabric chamber -> CLEAN WATER OUTLET  [DOC: "final output valve"]
    zo = P["fabric_outlet_z"]
    L = P["overall_length"]
    objs.append(pipe("PIPE_OUTLET", do,
                     [(P["fabric_x0"] + P["fabric_len"] / 2.0, 200, zo),
                      (L - 180, 200, zo),
                      (L - 180, 200, 1250),
                      (L + 160, 200, 1250)],
                     "MAT_Pipe_Clean", "05_PIPING",
                     note="CLEAN-WATER OUTLET - distinct blue polymer, "
                          "separate route, labelled valve"))
    objs.append(flange("FLANGE_OUTLET", do, (L + 40, 200, 1250), "X"))
    objs += gate_valve("VALVE_FINAL_OUTPUT", do, (L - 60, 200, 1250), "X")
    objs.append(box("PIPE_OUTLET_SUPPORT_POST", (60, 60, 1250 - P["frame_deck_z"]),
                    (L - 180, 200 + 120, (1250 + P["frame_deck_z"]) / 2.0),
                    "MAT_Steel_Painted", "05_PIPING"))
    objs.append(box("PIPE_OUTLET_SUPPORT_CLAMP", (60, 200, 40),
                    (L - 180, 200 + 90, 1250 - 60), "MAT_Steel_Frame",
                    "05_PIPING"))

    # ---- SLUDGE branch: clearly different colour + route, into the bin
    hs = P["settling_floor_z"] - P["hopper_depth"]
    objs.append(pipe("PIPE_SLUDGE_DRAIN", ds,
                     [(P["settling_x0"] + P["settling_len"] / 2.0, 0, hs - 40),
                      (P["settling_x0"] + P["settling_len"] / 2.0, 0,
                       P["sludge_valve_z"]),
                      (P["bin_x0"] + 250, 0, P["sludge_valve_z"]),
                      (P["bin_x0"] + 250, P["bin_y0"] + 120,
                       P["sludge_valve_z"] + 60),
                      (P["bin_x0"] + 250, P["bin_y0"] + 120,
                       P["bin_floor_z"] + 340)],
                     "MAT_Pipe_Sludge", "05_PIPING",
                     note="SLUDGE DRAIN - olive/dark route, discharges into "
                          "the sludge bay of the waste bin"))
    objs += gate_valve("VALVE_SLUDGE_DRAIN", ds,
                       (P["settling_x0"] + P["settling_len"] / 2.0 + 190, 0,
                        P["sludge_valve_z"]), "X")
    objs.append(flange("FLANGE_SLUDGE_DRAIN", ds,
                       (P["settling_x0"] + P["settling_len"] / 2.0, 0,
                        hs - 20), "Z"))
    objs.append(box("PIPE_SLUDGE_SUPPORT_BRKT", (60, 220, 40),
                    (P["settling_x0"] + P["settling_len"] / 2.0 + 320, 0,
                     P["sludge_valve_z"] - ds / 2 - 20),
                    "MAT_Steel_Frame", "05_PIPING"))
    tag_many([o for o in objs if "SLUDGE" in o.name],
             "Sludge Line", "provisional polymer/steel pipe DN%d" % int(ds),
             "sludge removal branch - deliberately separated from the "
             "clean-water outlet", "[PROP]")
    return objs


# ==============================================================================
# 10.  FLOW INDICATORS  (visualisation only, NOT a quality claim)
# ==============================================================================
def flow_arrow(name, start, end, mat, coll="07_FLOW", shaft=26.0, head=70.0):
    a, b = Vector(start), Vector(end)
    d = b - a
    L = d.length
    if L < 1:
        return None
    dn = d.normalized()
    hl = min(head, L * 0.4)
    sh = box(name + "_SHAFT", (shaft, shaft, L - hl),
             tuple(a + dn * ((L - hl) / 2.0)), mat, coll)
    sh.rotation_euler = dn.to_track_quat("Z", "Y").to_euler()
    bpy.ops.mesh.primitive_cone_add(
        radius1=M(head / 2.0), radius2=0.0, depth=M(hl),
        location=M(tuple(b - dn * (hl / 2.0))), vertices=20)
    h = bpy.context.object
    h.name = name + "_HEAD"
    h.rotation_euler = dn.to_track_quat("Z", "Y").to_euler()
    assign(h, mat)
    link_to(h, coll)
    for o in (sh, h):
        tag(o, "Flow Indicator", "n/a - schematic",
            "direction-of-flow marker only; water colour does NOT indicate "
            "water quality", "[PROP]")
    return [sh, h]


def build_flow_indicators():
    objs = []
    zi = P["inlet_pipe_z"]
    objs += flow_arrow("FLOW_01_INLET", (-380, 0, zi), (60, 0, zi),
                       "MAT_Flow_Raw")
    objs += flow_arrow("FLOW_02_TRANSFER",
                       (P["inlet_chamber_len"] + 40, 0,
                        P["settling_inlet_z"] + 160),
                       (P["settling_x0"] + 240, 0,
                        P["settling_inlet_z"] + 160), "MAT_Flow_Raw")
    # through the settling zone
    objs += flow_arrow("FLOW_03_SETTLING",
                       (P["settling_x0"] + 420, -300, 1150),
                       (P["settling_x0"] + 1150, -300, 1150), "MAT_Flow_Raw")
    # settling arrow pointing DOWN into the hopper
    objs += flow_arrow("FLOW_04_SETTLING_DOWN",
                       (P["settling_x0"] + 620, 200, 900),
                       (P["settling_x0"] + 620, 200, 690), "MAT_Flow_Sludge")
    objs += flow_arrow("FLOW_05_TO_FABRIC",
                       (P["fabric_x0"] - 190, -260, 900),
                       (P["fabric_x0"] + 260, -260, 900), "MAT_Flow_Clean")
    objs += flow_arrow("FLOW_06_THROUGH_FABRIC",
                       (P["fabric_x0"] - 60, 0, 900),
                       (P["fabric_x0"] + 60, 0, 900), "MAT_Flow_Clean")
    objs += flow_arrow("FLOW_07_OUTLET",
                       (P["fabric_x0"] + 380, 200, 1000),
                       (P["overall_length"] + 130, 200, 1250),
                       "MAT_Flow_Clean")
    objs += flow_arrow("FLOW_08_CONVEYOR_SOLIDS",
                       (600, P["conv_tail"][1], P["conv_tail"][2] + 130),
                       (2300, P["conv_tail"][1], 1000), "MAT_Flow_Sludge")
    return [o for o in objs if o]


# ==============================================================================
# 11.  CAMERAS / LIGHTS / RENDER SETUP
# ==============================================================================
def setup_render(res_x=RES_X, res_y=RES_Y, samples=SAMPLES):
    sc = bpy.context.scene
    engine_ok = False
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            sc.render.engine = eng
            engine_ok = True
            break
        except Exception:
            continue
    if not engine_ok:
        sc.render.engine = "BLENDER_EEVEE"
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
    else:
        try:
            sc.eevee.taa_render_samples = samples
            sc.eevee.use_raytracing = True
        except Exception:
            try:
                sc.eevee.use_ssr = True
                sc.eevee.use_ssr_refraction = True
            except Exception:
                pass
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass

    world = bpy.data.worlds.new("World_Studio")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.045, 0.055, 0.075, 1.0)
        bg.inputs[1].default_value = 0.35
    sc.world = world
    return sc


def add_area_light(name, loc, energy, size, rot=(0, 0, 0),
                   color=(1, 1, 1)):
    la = bpy.data.lights.new(name, "AREA")
    la.energy = energy
    la.size = M(size)
    la.color = color
    o = bpy.data.objects.new(name, la)
    bpy.context.scene.collection.objects.link(o)
    o.location = M(loc)
    o.rotation_euler = [math.radians(a) for a in rot]
    link_to(o, "09_RIG")
    return o


def add_sun(name, energy, rot):
    la = bpy.data.lights.new(name, "SUN")
    la.energy = energy
    la.angle = math.radians(3.0)
    o = bpy.data.objects.new(name, la)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = [math.radians(a) for a in rot]
    link_to(o, "09_RIG")
    return o


def build_lighting():
    """Soft studio setup. Energies are in Watts and sized for a ~4 m subject;
    these were tuned down hard after a first pass blew the render out."""
    objs = []
    # key sun - defines form
    objs.append(add_sun("LIGHT_KEY_SUN", 1.6, (52, 0, 38)))
    # cool fill from behind, lifts the shadow side without flattening
    objs.append(add_sun("LIGHT_FILL_SUN", 0.45, (62, 0, 145)))
    # broad soft top light
    objs.append(add_area_light("LIGHT_TOP_SOFT", (1700, 0, 3800), 6000,
                               4000, rot=(0, 0, 0), color=(0.92, 0.95, 1.0)))
    # warm key from the viewer's left front
    objs.append(add_area_light("LIGHT_KEY_SIDE", (700, -2600, 1700), 3200,
                               2500, rot=(62, 0, 42),
                               color=(1.0, 0.96, 0.90)))
    # rim from behind-right to separate the silhouette from the background
    objs.append(add_area_light("LIGHT_RIM", (3600, 1800, 2000), 2600, 2000,
                               rot=(66, 0, 130), color=(0.80, 0.88, 1.0)))
    # low bounce so undersides are not black
    objs.append(add_area_light("LIGHT_BOUNCE", (1700, -900, 200), 1400,
                               3000, rot=(0, 0, 0), color=(1.0, 0.94, 0.86)))
    return objs


def add_camera(name, loc, look_at, ortho=None, lens=50.0, shift=(0.0, 0.0)):
    cam = bpy.data.cameras.new(name)
    if ortho is not None:
        cam.type = "ORTHO"
        cam.ortho_scale = M(ortho)
    else:
        cam.type = "PERSP"
        cam.lens = lens
    cam.clip_start = 1.0
    cam.clip_end = 200.0
    cam.shift_x, cam.shift_y = shift
    o = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(o)
    o.location = M(loc)
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    link_to(o, "09_RIG")
    return o


def model_centre():
    return (P["overall_length"] / 2.0, 0.0, 700.0)


def fit_camera(cam, objs, margin=1.14):
    """Aim + set ortho/persp framing so every object fits the render."""
    pts = []
    deps = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type not in {"MESH", "CURVE", "FONT"}:
            continue
        oe = o.evaluated_get(deps)
        try:
            for c in oe.bound_box:
                pts.append(oe.matrix_world @ Vector(c))
        except Exception:
            continue
    if not pts:
        return
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts),
                 min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts),
                 max(p.z for p in pts)))
    ctr = (mn + mx) / 2.0
    rad = max((mx - mn).length / 2.0, 0.3)
    cam.location = (ctr + Vector(cam.location) * 0.0) + \
        (Vector(cam.location) - ctr).normalized() * \
        max(rad * 3.2, 2.5)
    d = ctr - Vector(cam.location)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if cam.data.type == "ORTHO":
        aspect = (bpy.context.scene.render.resolution_x /
                  max(bpy.context.scene.render.resolution_y, 1))
        ext = max((mx.x - mn.x), (mx.y - mn.y) * aspect, (mx.z - mn.z))
        cam.data.ortho_scale = M(max(ext * margin, 0.5))


# ==============================================================================
# 12.  ANNOTATIONS  (dimensions, labels, flow arrows on drawings)
# ==============================================================================
ANNOT_STATE = []


def _track(o):
    if isinstance(o, (list, tuple)):
        for x in o:
            _track(x)
    elif o is not None:
        ANNOT_STATE.append((o, o.location.copy(), o.rotation_euler.copy()))
    return o


def add_stage_labels():
    """Numbered component callouts used on the orthographic / sectional views."""
    L = P["overall_length"]
    items = [
        ("01  INLET + IRON MESH SCREEN  [DOC]", (300, -720, 1500)),
        ("02  TANK_01_SETTLING + GRAVEL BED  [DOC]", (1300, -520, 1560)),
        ("03  FILTER_02_FABRIC POLISHER  [DOC]", (2380, -460, 1400)),
        ("04  CONVEYOR_01_BELT + SCRAPER  [DOC]", (1500, -1000, 1330)),
        ("05  BIN_01 SLUDGE / SOLID WASTE  [DOC]", (2600, -1050, 900)),
        ("06  STRUCTURAL SKID FRAME  [PROP]", (600, 760, 320)),
    ]
    for body, loc in items:
        _track(text("LABEL_STAGE_" + body[:2], body, loc, size=46,
                    rot=(90, 0, 0)))
    _track(text("LABEL_TITLE",
                "DOMESTIC SEWAGE FILTRATION SYSTEM  -  PROVISIONAL "
                "PROTOTYPE DIMENSIONS", (L / 2.0, -1250, 2000), size=64,
                rot=(90, 0, 0)))
    _track(text("LABEL_SUBTITLE",
                "ALL DIMENSIONS ARE PROVISIONAL DESIGN VALUES - NOT "
                "SOURCE-DOCUMENT SPECIFIED, NOT CONSTRUCTION CERTIFIED",
                (L / 2.0, -1250, 1880), size=40, rot=(90, 0, 0)))


def add_dimensions():
    """Overall + principal component dimensions for the orthographic views."""
    L = P["overall_length"]
    W = P["overall_width"]
    H = P["overall_height"]
    yf = -W / 2.0 - 260.0        # front dimension line
    xr = L + 300.0               # right dimension line
    yb = W / 2.0 + 260.0         # back dimension line

    # ---- plan (top view): overall length + widths of the three vessels
    _track(dim_line("DIM_OVERALL_LEN", (0, yb), (L, yb), (0, 1, 0), 0,
                    "%.0f  OVERALL LENGTH (provisional)" % L, size=44))
    _track(dim_line("DIM_VESSEL_LEN",
                    (P["settling_x0"], yb), (P["settling_x0"] +
                                             P["settling_len"], yb),
                    (0, 1, 0), 170,
                    "%.0f  TANK_01_SETTLING" % P["settling_len"], size=38))
    _track(dim_line("DIM_FABRIC_LEN",
                    (P["fabric_x0"], yb), (P["fabric_x0"] + P["fabric_len"],
                                           yb), (0, 1, 0), 170,
                    "%.0f  FILTER_02_FABRIC" % P["fabric_len"], size=38))
    _track(dim_line("DIM_SCREEN_CHAMBER_LEN", (0, yb),
                    (P["inlet_chamber_len"], yb), (0, 1, 0), 340,
                    "%.0f  SCREEN CHAMBER" % P["inlet_chamber_len"], size=38))
    _track(dim_line("DIM_OVERALL_WID", (xr, -W / 2.0), (xr, W / 2.0),
                    (-1, 0, 0), 0,
                    "%.0f  OVERALL WIDTH (provisional)" % W, size=44))

    # ---- elevation (front view): overall height + key levels
    _track(dim_line("DIM_OVERALL_HGT", (xr, 0, 0), (xr, 0, H), (-1, 0, 0), 0,
                    "%.0f  OVERALL HEIGHT" % H, size=44))
    _track(dim_line("DIM_TANK_HGT", (xr, 0, P["frame_deck_z"]),
                    (xr, 0, P["settling_rim_z"] + 40), (-1, 0, 0), 180,
                    "%.0f  TANK_01 RIM ABOVE DECK" %
                    (P["settling_rim_z"] + 40 - P["frame_deck_z"]), size=38))
    _track(dim_line("DIM_WATER_LEVEL", (xr, 0, P["settling_floor_z"]),
                    (xr, 0, P["settling_water_level_z"]), (-1, 0, 0), 330,
                    "%.0f  SETTLING DEPTH (provisional)" %
                    (P["settling_water_level_z"] - P["settling_floor_z"]),
                    size=38))
    _track(dim_line("DIM_MESH_APERTURE",
                    (P["inlet_chamber_len"] + 240, -340, 900),
                    (P["inlet_chamber_len"] + 240 + P["mesh_pitch"], -340, 900),
                    (0, 0, 1), -150,
                    "%.0f  MESH APERTURE (provisional)" % P["mesh_pitch"],
                    size=34))

    # ---- side view: conveyor geometry
    _track(dim_line("DIM_CONV_INCLINE",
                    (P["conv_tail"][0], -1400, P["conv_tail"][2]),
                    (P["conv_head"][0], -1400, P["conv_head"][2]),
                    (0, 1, 0), 0,
                    "CONVEYOR INCLINE %.1f deg (provisional)" %
                    math.degrees(math.atan2(P["conv_head"][2] -
                                            P["conv_tail"][2],
                                            P["conv_head"][0] -
                                            P["conv_tail"][0])),
                    size=38))
    _track(dim_line("DIM_CONV_LEN",
                    (P["conv_tail"][0], -1400, P["conv_tail"][2] - 150),
                    (P["conv_head"][0], -1400, P["conv_tail"][2] - 150),
                    (0, 0, 1), 0,
                    "%.0f  CONVEYOR CENTRE DISTANCE (provisional)" %
                    math.hypot(P["conv_head"][0] - P["conv_tail"][0],
                               P["conv_head"][2] - P["conv_tail"][2]),
                    size=38))


def clear_annotations():
    for o, loc, rot in ANNOT_STATE:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
    del ANNOT_STATE[:]


# ==============================================================================
# 13.  RENDER PIPELINE
# ==============================================================================
def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    ok = os.path.isfile(path) and os.path.getsize(path) > 1024
    print("[RENDER] %-34s %s (%d bytes)" % (
        os.path.basename(path), "OK" if ok else "FAILED/EMPTY",
        os.path.getsize(path) if os.path.isfile(path) else 0))
    return ok


def all_renderable():
    skip = {"08_ANNOT", "09_RIG"}
    out = []
    for key, c in COLLECTIONS.items():
        if key in skip:
            continue
        out += [o for o in c.objects if o.type in {"MESH", "CURVE", "FONT"}]
    return out


def shot_overview():
    cx, cy, cz = model_centre()
    cam = add_camera("CAM_OVERVIEW", (cx - 3400, -4200, 2600),
                     (cx, cy, cz), lens=52.0)
    bpy.context.scene.camera = cam
    fit_camera(cam, all_renderable(), margin=1.10)
    return render_to(os.path.join(OUT_DIR, "assembly_overview.png"))


def _section_cutters():
    """Half-space cubes used to cut the vessels for the cutaway render."""
    cutters = []
    specs = [("CUTTER_TANKS", (3.2, 0.0, 0.0), (P["settling_x0"] +
                                                  P["settling_len"] / 2.0,
                                                  0.0, 900.0)),
             ("CUTTER_FABRIC", (3.2, 0.0, 0.0),
              (P["fabric_x0"] + P["fabric_len"] / 2.0, 0.0, 900.0)),
             ("CUTTER_SCREEN", (2.6, 0.0, 0.0), (300.0, 0.0, 1150.0))]
    for nm, sz, loc in specs:
        c = box(nm, sz, loc, None, "09_RIG")
        cutters.append(c)
    return cutters


def shot_sectional():
    """Cutaway through the vessels showing water passages + sludge collection."""
    cutters = _section_cutters()
    targets = []
    for key in ("01_SCREEN", "02_SETTLING", "03_FABRIC"):
        targets += [o for o in COLLECTIONS[key].objects
                    if o.type in {"MESH", "CURVE"}]
    n = 0
    for o in targets:
        for c in cutters:
            dx = (abs(o.location.x - c.location.x) / (c.dimensions.x / 2.0
                                                     if c.dimensions.x else 1))
            dy = (abs(o.location.y - c.location.y) / (c.dimensions.y / 2.0
                                                     if c.dimensions.y else 1))
            dz = (abs(o.location.z - c.location.z) / (c.dimensions.z / 2.0
                                                     if c.dimensions.z else 1))
            if max(dx, dy, dz) > 1.6:
                continue
            m = o.modifiers.new("SECTION_CUT", "BOOLEAN")
            m.object = c
            m.operation = "INTERSECT"
            m.solver = "EXACT"
            n += 1
            break
    add_stage_labels()
    cx, cy, cz = model_centre()
    cam = add_camera("CAM_SECTION", (cx + 2500, -3600, 1500),
                     (1500, 60, 800), lens=58.0)
    bpy.context.scene.camera = cam
    clear_annotations()
    fit_camera(cam, all_renderable(), margin=1.12)
    ok = render_to(os.path.join(OUT_DIR, "sectional_view.png"))
    for o in targets:
        for m in list(o.modifiers):
            if m.name.startswith("SECTION_CUT"):
                o.modifiers.remove(m)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    return ok


EXPLODE_OFFSETS = {
    "00_FRAME":   (0.0, 0.0, -420.0),
    "01_SCREEN":  (-620.0, 0.0, 1150.0),
    "02_SETTLING": (0.0, 0.0, 700.0),
    "03_FABRIC":  (760.0, 0.0, 300.0),
    "04_CONVEYOR": (0.0, -1150.0, -260.0),
    "06_BIN":     (1150.0, -950.0, -430.0),
    "05_PIPING":  (0.0, 0.0, 0.0),
    "07_FLOW":    (0.0, 0.0, 0.0),
}


def shot_exploded():
    saved = []
    for key, off in EXPLODE_OFFSETS.items():
        for o in COLLECTIONS.get(key, bpy.data.collections.new("_t")).objects:
            saved.append((o, o.location.copy()))
            o.location = o.location + Vector(tuple(v * MM for v in off))
    # explosion axis guide
    cx, cy, cz = model_centre()
    g = cyl("EXPLODE_GUIDE_AXIS", 14, P["overall_length"] + 2200,
            (cx, 60, 1300), "MAT_Safety_Orange", "08_ANNOT",
            rot=(0, 90, 0), verts=12)
    cam = add_camera("CAM_EXPLODED", (cx - 3000, -5200, 3900),
                     (cx, cy, 1250), lens=48.0)
    bpy.context.scene.camera = cam
    fit_camera(cam, all_renderable(), margin=1.08)
    ok = render_to(os.path.join(OUT_DIR, "exploded_assembly.png"))
    for o, loc in saved:
        o.location = loc
    try:
        bpy.data.objects.remove(g, do_unlink=True)
    except Exception:
        pass
    return ok


def shot_ortho():
    """Front / side / top orthographic engineering views with dimensions."""
    L = P["overall_length"]
    W = P["overall_width"]
    results = []
    add_stage_labels()
    add_dimensions()

    specs = [
        ("front_view.png", "CAM_FRONT", (L / 2.0, -6000.0, 800.0),
         (L / 2.0, 0.0, 800.0)),
        ("side_view.png", "CAM_SIDE", (-6000.0, 0.0, 800.0),
         (0.0, 0.0, 800.0)),
        ("top_view.png", "CAM_TOP", (L / 2.0, 0.0, 6000.0),
         (L / 2.0, 0.0, 0.0)),
    ]
    for fname, cname, loc, look in specs:
        cam = add_camera(cname, loc, look, ortho=1000.0)
        bpy.context.scene.camera = cam
        fit_camera(cam, all_renderable(), margin=1.22)
        results.append(render_to(os.path.join(OUT_DIR, fname)))
    clear_annotations()
    return all(results)


# ==============================================================================
# 14.  OPTIONAL ANIMATION  (operating-principle demonstration)
# ==============================================================================
def build_animation(frames=144, fps=24):
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames
    sc.render.fps = fps

    tx, ty, tz = P["conv_tail"]
    hx, hy, hz = P["conv_head"]
    rd = P["conv_roller_dia"]
    rr = rd / 2.0 + P["conv_belt_thk"]
    ang = math.atan2(hz - tz, hx - tx)
    run = math.hypot(hx - tx, hz - tz)

    # ---- rollers spin (proposed; the PDF gives no speed)
    for nm, cx, cz in (("CONVEYOR_01_DRIVE_ROLLER", hx, hz),
                       ("CONVEYOR_01_TAIL_ROLLER", tx, tz)):
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        for f, a in ((1, 0.0), (frames, 2 * math.pi * run / (2 * rr))):
            o.rotation_euler = (0.0, a, 0.0)
            o.keyframe_insert("rotation_euler", frame=f)
    for o in COLLECTIONS["04_CONVEYOR"].objects:
        if o.name.startswith("CONVEYOR_01_IDLER_") and "_MOUNT" not in o.name:
            for f, a in ((1, 0.0), (frames, 2 * math.pi * run / (2 * rr))):
                o.rotation_euler = (0.0, a, 0.0)
                o.keyframe_insert("rotation_euler", frame=f)

    # ---- cleats travel the carrying strand and fall into the bin
    cleats = [o for o in bpy.data.objects
              if o.name.startswith("CONVEYOR_01_CLEAT_")]
    cleats.sort(key=lambda o: o.name)
    total = run * 1.9
    for i, o in enumerate(cleats):
        f0 = i / max(len(cleats), 1)
        o.rotation_mode = "XYZ"
        for f in range(1, frames + 1, 3):
            t = (f0 + (f - 1) / frames * (total / run)) % 1.0
            s = t * run
            if s <= run:
                x = tx + math.cos(ang) * s
                z = tz + math.sin(ang) * s + rr + 17
                o.location = M((x, ty, z))
                o.rotation_euler = (0.0, -ang, 0.0)
            else:
                # discharged over the head roller into the chute
                k = (s - run) / max(total - run, 1.0)
                x = hx + 120 + 520 * k
                z = hz + 40 - 400 * k
                o.location = M((x, ty, z))
                o.rotation_euler = (0.0, -ang - 1.3 * k, 0.0)
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)

    # ---- sequential stage captions (engineering annotation, not a QA claim)
    caps = [
        (1, "STAGE 1  -  RAW SEWAGE ENTERS AND HITS THE IRON MESH SCREEN"),
        (29, "STAGE 2  -  MESH RETAINS PLASTICS / BULK WASTE"),
        (57, "STAGE 3  -  HEAVY PARTICLES SETTLE INTO THE HOPPER"),
        (85, "STAGE 4  -  WATER PASSES THE GRAVEL BED AND THE CLOTH FILTER"),
        (113, "STAGE 5  -  CONVEYOR MOVES SOLIDS TO THE WASTE BIN"),
        (141, "STAGE 6  -  POLISHED WATER EXITS THROUGH THE FINAL OUTLET VALVE"),
    ]
    for i, (f0, body) in enumerate(caps):
        t = text("ANIM_STAGE_CAPTION_%d" % i, body,
                 (P["overall_length"] / 2.0, -1450.0, 1750.0 + i * 190.0),
                 size=52, rot=(90, 0, 0))
        t.hide_render = True
        t.keyframe_insert("hide_render", frame=1)
        if f0 > 1:
            t.hide_render = True
            t.keyframe_insert("hide_render", frame=f0 - 1)
            t.hide_render = False
            t.keyframe_insert("hide_render", frame=f0)
    sc.frame_set(1)
    print("[ANIM] operating-principle animation set up: %d frames @ %d fps"
          % (frames, fps))


# ==============================================================================
# 15.  EXPORTS
# ==============================================================================
def _stl_export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
        return True
    except Exception:
        try:
            bpy.ops.export_mesh.stl(filepath=path, use_selection=True)
            return True
        except Exception as e:
            print("[STL] failed", obj.name, e)
            return False


def export_all():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(STL_DIR, exist_ok=True)

    # ---- STL for the individually identifiable / printable components
    printable = []
    for pat in ("TANK_01_INSPECTION_LID", "TANK_01_WALL_", "SCREEN_01_CARRIER_",
                "SCREEN_01_MESH_WIRE", "FILTER_02_CLOTH_MEDIA",
                "FILTER_02_TOP_COVER", "FILTER_02_FRAME_",
                "CONVEYOR_01_SIDE_RAIL", "CONVEYOR_01_SCRAPER_BLADE",
                "CONVEYOR_01_BELT", "BIN_01_", "FRAME_POST_",
                "MEDIA_02_CELL_"):
        printable += [o for o in bpy.data.objects
                      if o.name.startswith(pat) and o.type == "MESH"]
    printable = sorted(set(printable), key=lambda o: o.name)
    ok_stl = 0
    for o in printable:
        if _stl_export(o, os.path.join(STL_DIR, o.name + ".stl")):
            ok_stl += 1
    print("[EXPORT] %d/%d STL component files written to %s"
          % (ok_stl, len(printable), STL_DIR))

    bpy.ops.object.select_all(action="SELECT")
    # ---- OBJ
    obj_path = os.path.join(EXPORT_DIR, "domestic_sewage_filtration_system.obj")
    done = False
    try:
        bpy.ops.wm.obj_export(filepath=obj_path,
                              export_selected_objects=True,
                              apply_modifiers=True)
        done = True
    except Exception:
        try:
            bpy.ops.export_scene.obj(filepath=obj_path, use_selection=True)
            done = True
        except Exception as e:
            print("[EXPORT] OBJ failed:", e)
    # ---- glTF / GLB
    glb_path = os.path.join(EXPORT_DIR, "domestic_sewage_filtration_system.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=glb_path,
                                  export_format="GLB",
                                  use_selection=True)
    except Exception as e:
        print("[EXPORT] glTF failed:", e)
    for p in (obj_path, glb_path):
        if os.path.isfile(p):
            print("[EXPORT] %s  (%d bytes)" % (os.path.basename(p),
                                               os.path.getsize(p)))
        else:
            print("[EXPORT] %s  NOT CREATED" % os.path.basename(p))
    bpy.ops.object.select_all(action="DESELECT")


# ==============================================================================
# 16.  REPORTS  (CSV / JSON / README)
# ==============================================================================
def write_inventory():
    path = os.path.join(OUT_DIR, "component_inventory.csv")
    rows = []
    for rec in INVENTORY:
        rows.append((rec["component"], rec["subsystem"],
                     1, rec["material_provisional"],
                     rec["status_vs_source"], rec["notes"]))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["component_name", "subsystem", "quantity",
                    "provisional_material", "status_vs_source_document",
                    "notes"])
        w.writerows(sorted(set(rows), key=lambda r: r[0]))
    print("[REPORT] component_inventory.csv  (%d rows)" % len(set(rows)))
    return path


def write_parameters():
    path = os.path.join(OUT_DIR, "design_parameters.json")
    doc = {
        "project": "Domestic Sewage Filtration System",
        "source_document": "Domestic Sewage Filtration System "
                           "(Black & White).pdf",
        "disclaimer": "EVERY numeric value below is a PROVISIONAL design "
                      "parameter chosen for a plausible prototype scale. The "
                      "source document specifies NO dimensions, flow rates, "
                      "material grades, motor ratings or treatment "
                      "performance. Nothing here is construction-certified "
                      "or source-verified.",
        "unit": "millimetre",
        "blender_conversion": "1 mm = 0.001 Blender units (metres)",
        "documented_features": [
            "Stage 1 iron mesh screen - rust-resistant iron wire",
            "Stage 2 mud/sediment settling + multi-grade gravel filter",
            "Stage 3 high-tensile porous synthetic fabric polisher",
            "Motorised belt conveyor with scraper blades",
            "Solid waste / sludge collection bin",
            "Final output valve on the polished water line",
        ],
        "proposed_design_additions": [
            "structural skid frame and pedestals",
            "sloped sludge hopper + DN80 drain with isolation valve",
            "screen carrier frame, guide rails, clamps and lift handle",
            "conveyor drive/tail rollers, take-up screws, gearbox, guards",
            "removable bolted inspection lid and top covers",
            "discharge chute from conveyor into the bin",
            "all pipe routing, flanges, brackets and supports",
        ],
        "parameters": {k: v for k, v in P.items()},
        "derived": {
            "conveyor_incline_deg": round(math.degrees(math.atan2(
                P["conv_head"][2] - P["conv_tail"][2],
                P["conv_head"][0] - P["conv_tail"][0])), 2),
            "conveyor_centre_distance_mm": round(math.hypot(
                P["conv_head"][0] - P["conv_tail"][0],
                P["conv_head"][2] - P["conv_tail"][2]), 1),
            "settling_plan_area_m2": round(
                (P["settling_len"] - 2 * P["settling_wall"]) *
                (P["settling_wid"] - 2 * P["settling_wall"]) / 1e6, 3),
            "settling_water_depth_mm": round(
                P["settling_water_level_z"] - P["settling_floor_z"], 1),
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print("[REPORT] design_parameters.json written")
    return path


def write_readme(qa):
    path = os.path.join(OUT_DIR, "README.md")
    derived = {
        "conveyor_incline_deg": round(math.degrees(math.atan2(
            P["conv_head"][2] - P["conv_tail"][2],
            P["conv_head"][0] - P["conv_tail"][0])), 2),
        "conveyor_centre_distance_mm": round(math.hypot(
            P["conv_head"][0] - P["conv_tail"][0],
            P["conv_head"][2] - P["conv_tail"][2]), 1),
        "settling_water_depth_mm": round(
            P["settling_water_level_z"] - P["settling_floor_z"], 1),
        "object_count": qa["objects"],
        "triangles_evaluated": qa["tris"],
    }
    txt = r"""# Domestic Sewage Filtration System - 3D Mechanical Model

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
     | weir overflow  (weir crest z=%(weir)g mm)
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

Blender version used for the committed renders: **%(blender)s**.

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
| Remove and clean the iron mesh screen | Vertical lift out of guide rails; clamping brackets release; lift handle | `screen_lift_clearance` = %(screenclr)g mm |
| Inspect / clean the settling chamber | Bolted removable top inspection lid (10 fasteners, 2 lifting eyes) | lid `(ln)x(wd)x(thk)` = `settling_len/wid/lid_thk` |
| Drain the sludge hopper | DN80 bottom drain + gate valve to the bin sludge bay | `hopper_drain_dia` = %(drain)g mm |
| Replace the cloth filter element | Top cover unbolts; element lifts vertically on 4 loops | `filter_lift_clearance` = %(filtclr)g mm |
| Tension the conveyor belt | Two take-up screws with lock nuts at the tail roller | `tensioner_stroke` = %(tens)g mm |
| Empty the waste bin | Fork pockets + drag handle, bin lifts off the deck | `bin_len/bin_wid/bin_hgt` |

---

## 8. Build validation actually performed

```
%(qa)s
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
2. **Hopper slope %(hop)g deg** is aggressive for drained sand (typical drained
   repose is 35-45 deg). It was chosen for self-cleaning; it needs a
   geotechnical/handling check.
3. **No pumping.** The document implies gravity-assisted flow; this model has
   no pump. A domestic installation at this scale would very likely need one,
   and its duty point would change every elevation shown.
4. **No odour control.** A real chambered system needs a vent/odour control
   and a sealed lid seal (a gasket is modelled on the fabric chamber only).
5. **Conveyor duty.** Solids that pass a %%(mesh)g mm aperture and settle in a
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
""" % {
        "weir": P["weir_crest_z"],
        "blender": bpy.app.version_string,
        "screenclr": P["screen_lift_clearance"],
        "drain": P["hopper_drain_dia"],
        "filtclr": P["filter_lift_clearance"],
        "tens": P["tensioner_stroke"],
        "hop": P["hopper_angle_deg"],
        "mesh": P["mesh_pitch"],
        "qa": qa["text"],
    }
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(txt)
    print("[REPORT] README.md written")
    return path


# ==============================================================================
# 17.  QUALITY ASSURANCE
# ==============================================================================
def qa_report():
    lines = []
    issues = []
    sc = bpy.context.scene

    objs = [o for o in bpy.data.objects]
    meshes = [o for o in objs if o.type == "MESH"]
    lines.append("objects in file      : %d" % len(objs))
    lines.append("mesh objects         : %d" % len(meshes))

    tris = 0
    loose = 0
    nonman = 0
    deps = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        me = o.data
        if len(me.polygons) == 0:
            loose += 1
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        if len(me.polygons) and not all(len(p.vertices) >= 3
                                         for p in me.polygons):
            nonman += 1
    lines.append("triangles            : %d" % tris)
    lines.append("empty mesh objects   : %d" % loose)
    lines.append("degenerate-face objs : %d" % nonman)
    if loose:
        issues.append("%d mesh objects have no faces" % loose)

    # required assemblies present
    required = {
        "01 Inlet + iron mesh screen":
            ["SCREEN_01_MESH_WIRE_V", "SCREEN_01_CARRIER_BOTTOM",
             "PIPE_INLET_RAW", "INLET_CHAMBER_WALL_W"],
        "02 Sedimentation chamber": ["TANK_01_HOPPER_OUTER", "TANK_01_WALL_WEST",
                                     "TANK_01_INSPECTION_LID",
                                     "PIPE_SLUDGE_DRAIN", "BIN_01_SLUDGE_CONTENTS"],
        "02b Gravel secondary bed": ["MEDIA_02_GRAVEL_L1", "MEDIA_02_GRAVEL_L2",
                                     "MEDIA_02_GRAVEL_L3",
                                     "MEDIA_02_UNDERDRAIN_PAN"],
        "03 Fabric polishing": ["FILTER_02_CLOTH_MEDIA_1", "FILTER_02_TOP_COVER",
                                "FILTER_02_COVER_GASKET",
                                "PIPE_OUTLET", "VALVE_FINAL_OUTPUT_BODY",
                                "VALVE_FINAL_OUTPUT_HANDWHEEL"],
        "04 Conveyor": ["CONVEYOR_01_BELT", "CONVEYOR_01_DRIVE_ROLLER",
                        "CONVEYOR_01_TAIL_ROLLER", "CONVEYOR_01_SCRAPER_BLADE",
                        "CONVEYOR_01_GEARBOX_HOUSING", "CONVEYOR_01_BELT" ],
        "05 Piping": ["PIPE_INLET_RAW", "PIPE_01_TRANSFER_RAW",
                      "PIPE_02_SETTLING_TO_FABRIC", "PIPE_OUTLET",
                      "PIPE_SLUDGE_DRAIN"],
        "06 Collection bin": ["BIN_01_FLOOR", "BIN_01_DIVIDER",
                              "CONVEYOR_01_DISCHARGE_CHUTE"],
        "07 Structure": ["FRAME_POST_00", "FRAME_RAIL_FRONT_TOP",
                         "GROUND_PAD"],
    }
    lines.append("")
    lines.append("assembly presence:")
    for grp, names in required.items():
        miss = [n for n in names if bpy.data.objects.get(n) is None]
        status = "OK" if not miss else "MISSING " + ",".join(miss)
        lines.append("   %-30s %s" % (grp, status))
        if miss:
            issues.append("%s missing %s" % (grp, miss))

    # bounding box sanity / stray geometry
    if meshes:
        mn = [1e9] * 3
        mx = [-1e9] * 3
        stray = []
        for o in meshes:
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                for i in range(3):
                    mn[i] = min(mn[i], w[i])
                    mx[i] = max(mx[i], w[i])
        span = [mx[i] - mn[i] for i in range(3)]
        lines.append("")
        lines.append("assembly bbox (m)   : X %.2f  Y %.2f  Z %.2f"
                     % (span[0], span[1], span[2]))
        lines.append("assembly bbox min    : (%.2f, %.2f, %.2f)"
                     % (mn[0], mn[1], mn[2]))
        lines.append("assembly bbox max    : (%.2f, %.2f, %.2f)"
                     % (mx[0], mx[1], mx[2]))
        if span[0] < 1.5 or span[1] < 0.4 or span[2] < 0.5:
            issues.append("assembly bounding box is implausibly small")
        if span[0] > 12 or span[1] > 6 or span[2] > 5:
            issues.append("assembly bounding box is implausibly large - "
                          "possible stray geometry")
        for o in meshes:
            c = o.matrix_world.translation
            if (c.x < -3.0 or c.x > P["overall_length"] / 1000.0 + 3.0
                    or abs(c.y) > 3.0 or c.z < -0.5 or c.z > 3.0):
                if not o.name.startswith(("PIPE_", "CUTTER_", "EXPLODE_")):
                    stray.append(o.name)
        if stray:
            lines.append("objects outside expected envelope: %s"
                         % ", ".join(stray[:12]))
            issues.append("%d stray objects outside the skid envelope"
                          % len(stray))

    # collections
    lines.append("")
    lines.append("collections:")
    for k, c in COLLECTIONS.items():
        lines.append("   %-42s %3d objects" % (c.name, len(c.objects)))

    lines.append("")
    if issues:
        lines.append("ISSUES FOUND: %d" % len(issues))
        for i in issues:
            lines.append("   ! " + i)
    else:
        lines.append("ISSUES FOUND: 0 - all checks passed")

    text = "\n".join("    " + l for l in lines)
    print("\n========== QA REPORT ==========")
    print(text)
    print("=============================\n")
    return {"objects": len(objs), "tris": tris, "issues": issues,
            "text": "\n".join(lines)}


def verify_deliverables():
    need = ["domestic_sewage_filtration_system.blend",
            "build_filtration_system.py",
            "assembly_overview.png", "exploded_assembly.png",
            "sectional_view.png", "front_view.png", "side_view.png",
            "top_view.png", "component_inventory.csv",
            "design_parameters.json", "README.md"]
    print("\n--- DELIVERABLE CHECK ---")
    bad = []
    for n in need:
        p = os.path.join(OUT_DIR, n)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            print("  OK      %-42s %10d bytes" % (n, os.path.getsize(p)))
        else:
            print("  MISSING %-42s" % n)
            bad.append(n)
    return bad


# ==============================================================================
# 18.  MAIN
# ==============================================================================
def main():
    print("\n" + "=" * 74)
    print("  DOMESTIC SEWAGE FILTRATION SYSTEM - PARAMETRIC BUILD")
    print("  Blender %s   quick=%s   anim=%s"
          % (bpy.app.version_string, QUICK, DO_ANIM_SETUP))
    print("=" * 74 + "\n")

    wipe_scene()
    make_collections()
    build_materials()
    setup_render()

    print("[BUILD] 00 frame")
    build_pad()
    build_frame()
    print("[BUILD] 01 inlet + iron mesh screen")
    build_inlet_chamber()
    build_screen()
    build_inlet_pipe()
    print("[BUILD] 02 sedimentation chamber + gravel bed")
    build_settling_tank()
    build_gravel_bed()
    print("[BUILD] 03 fabric polishing chamber")
    build_fabric_chamber()
    build_fabric_element()
    print("[BUILD] 04 conveyor")
    build_conveyor()
    print("[BUILD] 06 collection bin")
    build_bin()
    print("[BUILD] 05 piping + outlet")
    build_piping()
    print("[BUILD] 07 flow indicators")
    build_flow_indicators()
    build_lighting()

    if DO_ANIM_SETUP:
        build_animation()

    qa = qa_report()

    # ---------------------------------------------------------------- reports
    write_parameters()
    write_inventory()

    # ---------------------------------------------------------------- renders
    print("\n[RENDER] orthographic views")
    shot_ortho()
    print("[RENDER] isometric overview")
    shot_overview()
    print("[RENDER] exploded assembly")
    shot_exploded()
    print("[RENDER] sectional cutaway")
    shot_sectional()

    # --------------------------------------------------------------- exports
    print("\n[EXPORT] interchange files")
    export_all()

    # ------------------------------------------------------------ save .blend
    blend_path = os.path.join(OUT_DIR,
                              "domestic_sewage_filtration_system.blend")
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("\n[SAVE] %s (%d bytes)" % (blend_path,
                                      os.path.getsize(blend_path)))

    write_readme(qa)
    missing = verify_deliverables()
    print("\n" + "=" * 74)
    if missing:
        print("  BUILD COMPLETE WITH PROBLEMS: %d deliverables missing"
              % len(missing))
        print("  " + ", ".join(missing))
    else:
        print("  BUILD COMPLETE - all deliverables present")
    print("=" * 74 + "\n")


if __name__ == "__main__":
    main()
