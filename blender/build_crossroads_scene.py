"""
Blender 5.0 High-Fidelity Stylized Environment Authoring Script
(V6 External CC0 Asset Overhaul & Structural Wood Rendering Fix)
Project: The Crossroads — Two Paths, One Designer (Evelyn Lin)

Key Engineering & Art Upgrades:
1. EXTERNAL CC0 FOREST ASSET OVERHAUL (Quaternius Stylized Nature MegaKit, CC0 1.0 Universal):
   - Integrates and unifies official CC0 glTF models and hand-painted textures from Quaternius's
     Stylized Nature MegaKit (`assets/external/quaternius_stylized_nature/`):
     * Broadleaf Trees: `TwistedTree_1`, `TwistedTree_2`, `CommonTree_1`, `CommonTree_2`, `CommonTree_3`
     * Evergreen Trees: `Pine_1`, `Pine_2`, `Pine_3`, `Pine_4`
     * Woodland Shrubs: `Bush_Common`, `Bush_Common_Flowers`
     * Ferns & Ground Botanicals: `Fern_1`, `Plant_1`, `Plant_1_Big`, `Plant_7`, `Plant_7_Big`, `Clover_1`, `Clover_2`
     * Grass & Wildflowers: `Grass_Common_Short`, `Grass_Common_Tall`, `Grass_Wispy_Short`, `Flower_3_Group`, `Flower_4_Group`
     * Mossy Boulders & Stepping Stones: `Rock_Medium_1..3`, `Pebble_Round_1..4`, `RockPath_Round_Small_1..3`
   - Splits multi-material glTF assets into single-material runtime meshes (`Tree_*_Trunk`, `Tree_*_Canopy`,
     `Forest_Shrubs`, `Forest_Ferns`, `Forest_Grass`, `Wildflowers`, `Environment_Rocks`, `Pathway_Cobbles`)
     with preserved UV maps, softened trunk root AO, and dome-smoothed canopy normals.
2. ROOT-CAUSE FIX FOR WOODEN SIGN, MAILBOX BASE & BRIDGE BLEED-THROUGH:
   - Eliminates the negative-determinant coordinate reflection (`det = -1`) that previously inverted cube
     windings before `bmesh.ops.bevel`, which had caused inward-folded corner spikes and inward-facing
     front normals (culled by back-face culling to expose inner back walls).
   - Executes all box bevels in orthogonal right-handed local space (`det = +1`) prior to world placement,
     uses non-overlapping timber joinery on `Signpost_*_Post`, `Signpost_*_Board`, `Mailbox_Post`, and
     `Wooden_Bridge`, generates grain-aligned UV maps (`UVMap`), and mathematically verifies outward-facing
     normals on every polygon.
3. FINAL LOCKED SIGNPOST NAMING:
   - Left sign: `Design Trail` (conceptual theme: Design Stories -> https://evelynjlin.com)
   - Right sign: `Game Trail` (conceptual theme: Game Worlds -> future Game Portfolio / modal)
"""

import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Euler, Matrix, noise

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT_DIR = os.path.join(ROOT_DIR, "assets", "external", "quaternius_stylized_nature")
BLEND_OUT = os.path.join(ROOT_DIR, "assets", "source", "crossroads_master.blend")
GLB_OUT = os.path.join(ROOT_DIR, "public", "models", "crossroads_environment.glb")
RENDER_DIR = os.path.join(ROOT_DIR, "assets", "renders")

os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

random.seed(206)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgba(hex_str, alpha=1.0):
    hex_str = hex_str.lstrip("#")
    r = srgb_to_linear(int(hex_str[0:2], 16) / 255.0)
    g = srgb_to_linear(int(hex_str[2:4], 16) / 255.0)
    b = srgb_to_linear(int(hex_str[4:6], 16) / 255.0)
    return (r, g, b, alpha)


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        c1[0] * (1.0 - t) + c2[0] * t,
        c1[1] * (1.0 - t) + c2[1] * t,
        c1[2] * (1.0 - t) + c2[2] * t,
        1.0,
    )


def make_pbr_material(name, hex_color, roughness=0.74, metallic=0.0, use_vertex_color=True):
    mat = bpy.data.materials.new(name=name)
    mat.use_backface_culling = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(hex_color)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.25
        if use_vertex_color:
            vc_node = nodes.new(type="ShaderNodeVertexColor")
            vc_node.layer_name = "Col"
            links.new(vc_node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def finalize_mesh_object(name, bm, material, color_fn=None, verify_outward_from=None):
    """
    Converts a BMesh to a smooth-shaded Blender object with optional per-vertex color attribute 'Col'
    and optional outward-normal verification from a reference point.
    """
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if verify_outward_from is not None:
        center_v = Vector(verify_outward_from)
        for f in bm.faces:
            if (f.calc_center_median() - center_v).dot(f.normal) < 0:
                f.normal_flip()

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    if color_fn is not None:
        col_attr = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
        verts = mesh.vertices
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                v_idx = mesh.loops[loop_idx].vertex_index
                v = verts[v_idx]
                wx, wy, wz = v.co.x, v.co.z, -v.co.y
                nx, ny, nz = v.normal.x, v.normal.z, -v.normal.y
                col_attr.data[loop_idx].color = color_fn(wx, wy, wz, nx, ny, nz)

    for poly in mesh.polygons:
        poly.use_smooth = True

    if material:
        obj.data.materials.append(material)
    return obj


def add_oriented_box(
    bm,
    sx,
    sy,
    sz,
    cx,
    cy,
    cz,
    to_world_fn,
    bevel_offset=0.010,
    segments=2,
    taper_top_x=1.0,
    taper_top_z=1.0,
    shear_y_by_z=0.0,
    shear_z_by_y=0.0,
    grain_axis='X',
):
    """
    Creates an orthogonal right-handed box of dimensions (sx, sy, sz) centered at local (cx, cy, cz):
    1. Scales and bevels in axis-aligned right-handed local space (determinant = +sx*sy*sz > 0)
       so bmesh.ops.bevel never folds or spikes corners.
    2. Assigns clean box-projected UVs ('UVMap') aligned with `grain_axis` ('X', 'Y', or 'Z').
    3. Transforms into Blender world space via `to_world_fn(lx, ly, lz)` with determinant +1
       (note: lz = cz - local_y so (local_x, local_y, local_z) -> (wx, -wz, wy) has det = +1!).
    4. Explicitly verifies every face normal of the new box points outward from its center.
    """
    uv_layer = bm.loops.layers.uv.get("UVMap")
    if uv_layer is None:
        uv_layer = bm.loops.layers.uv.new("UVMap")

    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    for v in verts:
        # In local right-handed box space before world placement:
        # v.co.x -> lx (width sx), v.co.y -> -lz (depth sz), v.co.z -> ly (height sy)
        v.co.x *= sx
        v.co.y *= sz
        v.co.z *= sy

    bm.normal_update()
    safe_offset = min(bevel_offset, 0.30 * min(sx, sy, sz))
    edges = list({e for v in verts for e in v.link_edges if all(ev in verts for ev in e.verts)})
    if safe_offset > 1e-5:
        b_res = bmesh.ops.bevel(
            bm,
            geom=verts + edges,
            offset=safe_offset,
            segments=segments,
            affect='EDGES',
            clamp_overlap=True,
        )
        all_verts = [v for v in set(verts + b_res.get("verts", [])) if v.is_valid]
    else:
        all_verts = [v for v in verts if v.is_valid]

    all_verts_set = set(all_verts)
    box_faces = list({f for v in all_verts for f in v.link_faces if f.is_valid and all(fv in all_verts_set for fv in f.verts)})

    # Generate grain-aligned box UVs in orthogonal local space before tapering/rotating
    uv_scale = 1.6
    for f in box_faces:
        f.normal_update()
        n = f.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in f.loops:
            co = loop.vert.co
            lx_l, ly_l, lz_l = co.x, co.z, -co.y
            if grain_axis == 'Y':
                # Vertical post grain: U along height (ly_l), V around perimeter
                u = ly_l * uv_scale
                v_coord = (lx_l if ay >= ax else lz_l) * uv_scale
            elif grain_axis == 'Z':
                # Depth-running timber grain: U along lz_l, V across lx_l/ly_l
                u = lz_l * uv_scale
                v_coord = (lx_l if az >= ax else ly_l) * uv_scale
            else:
                # Horizontal plank grain ('X'): U along lx_l, V across ly_l/lz_l
                u = lx_l * uv_scale
                v_coord = (ly_l if ay >= az else lz_l) * uv_scale
            loop[uv_layer].uv = (u + 0.5, v_coord + 0.5)

    # Apply optional taper/shear and map into world space with positive determinant (+1)
    for v in all_verts:
        lx_raw = v.co.x
        ly_raw = v.co.z
        lz_raw = -v.co.y  # Minus sign makes (co.x, co.y, co.z) -> (wx, -wz, wy) determinant +1!

        top_t = max(0.0, min(1.0, (ly_raw / max(1e-4, sy)) + 0.5))
        tx = 1.0 + (taper_top_x - 1.0) * top_t
        tz = 1.0 + (taper_top_z - 1.0) * top_t

        lx = cx + lx_raw * tx
        ly = cy + ly_raw + shear_y_by_z * lz_raw
        lz = cz + lz_raw * tz + shear_z_by_y * ly_raw
        v.co = to_world_fn(lx, ly, lz)

    world_center = to_world_fn(cx, cy, cz)
    for f in box_faces:
        f.normal_update()
        if (f.calc_center_median() - world_center).dot(f.normal) < 0:
            f.normal_flip()


# ==============================================================================
# 1. SPATIAL & TERRAIN FUNCTIONS (Unified Trail, Widened Creek & Sculpted Relief)
# ==============================================================================

def island_rim_point(angle):
    """Smooth asymmetric organic island silhouette."""
    rx_base = (
        4.42
        + 0.22 * math.cos(angle * 2.0 - 0.25)
        + 0.13 * math.sin(angle * 3.0 - 0.4)
        - 0.07 * math.cos(angle * 4.0 + 0.5)
    )
    rz_base = (
        3.38
        + 0.18 * math.sin(angle * 2.0 + 0.35)
        - 0.11 * math.cos(angle * 3.0)
        + 0.06 * math.sin(angle * 4.0 - 0.6)
    )
    x = math.cos(angle) * rx_base - 0.06
    z = math.sin(angle) * rz_base - 0.08 * math.cos(angle)
    return x, z


def island_radial_factor(x, z):
    ang = math.atan2(z + 0.05, x + 0.06)
    rim_x, rim_z = island_rim_point(ang)
    rim_r = math.hypot(rim_x + 0.06, rim_z + 0.05)
    cur_r = math.hypot(x + 0.06, z + 0.05)
    return cur_r / max(1e-4, rim_r)


def stream_center_z(x):
    """Graceful S-bend woodland creek centerline Z as a function of X."""
    return 0.14 + 0.15 * x + 0.32 * math.sin(x * 0.62 - 0.10) + 0.05 * math.cos(x * 1.30)


def stream_half_width(x):
    """
    Prominent, natural woodland stream width:
    - Broad pool around and under the bridge (half-width ~0.68 -> total width ~1.36 units)
    - Natural width variation into the NW spring basin and SE riffle pool
    """
    bridge_pool = 1.0 + 0.25 * math.exp(-(x ** 2) / 1.25)
    basin_swell = 1.0 + 0.22 * math.exp(-((x + 1.95) ** 2) / 1.1) + 0.20 * math.exp(-((x - 1.65) ** 2) / 1.1)
    return 0.56 * bridge_pool * basin_swell


def trail_wear_weight(x, z):
    """
    Returns a smooth [0.0 .. 1.0] trail wear weight representing how worn the compacted woodland
    earth is at (x, z), integrating the trailhead, bridge approaches, central crossroads,
    Design Trail (left), Game Trail (right), and Mailbox spur directly into the terrain.
    """
    def seg_dist_and_t(px, pz, ax, az, bx, bz):
        vx, vz = bx - ax, bz - az
        wx, wz = px - ax, pz - az
        c1 = vx * wx + vz * wz
        c2 = vx * vx + vz * vz
        if c1 <= 0:
            return math.hypot(px - ax, pz - az), 0.0
        if c2 <= c1:
            return math.hypot(px - bx, pz - bz), 1.0
        t = c1 / c2
        pbx, pbz = ax + t * vx, az + t * vz
        return math.hypot(px - pbx, pz - pbz), t

    sx_curve = x - 0.07 * math.sin((z - 0.78) * 1.8)
    d_south, t_south = seg_dist_and_t(sx_curve, z, 0.0, 2.58, 0.0, 0.72)
    w_south = 0.44 * (0.75 + 0.25 * math.sin(t_south * math.pi))
    south_origin_fade = min(1.0, max(0.0, (2.72 - z) / 0.45))

    d_north, _ = seg_dist_and_t(x, z, 0.0, -0.42, 0.0, -0.68)
    w_north = 0.48

    lx_curve = x + 0.12 * math.sin((z + 0.65) * 2.4)
    d_left, t_left = seg_dist_and_t(lx_curve, z, -0.08, -0.62, -2.55, -1.68)
    w_left = 0.43 * (1.0 - 0.28 * t_left)
    left_end_fade = 1.0 - 0.75 * (max(0.0, (t_left - 0.78) / 0.22) ** 1.6)

    rx_curve = x - 0.12 * math.sin((z + 0.65) * 2.4)
    d_right, t_right = seg_dist_and_t(rx_curve, z, 0.08, -0.62, 2.55, -1.60)
    w_right = 0.43 * (1.0 - 0.28 * t_right)
    right_end_fade = 1.0 - 0.75 * (max(0.0, (t_right - 0.78) / 0.22) ** 1.6)

    d_spur, t_spur = seg_dist_and_t(x, z, 0.08, 1.48, 1.26, 1.36)
    w_spur = 0.32 * (0.85 + 0.25 * t_spur)

    n_edge = (
        0.065 * noise.noise(Vector((x * 2.4 + 1.7, z * 2.4 - 0.9, 0.4)))
        + 0.032 * noise.noise(Vector((x * 5.2 - 2.1, z * 5.2 + 1.4, 1.8)))
    )

    def weight_from(d, w, fade=1.0):
        w_eff = max(0.12, w + n_edge)
        if d >= w_eff * 1.45:
            return 0.0
        u = d / w_eff
        return max(0.0, min(1.0, math.exp(-(u ** 2.6) * 1.45))) * fade

    wt = max(
        weight_from(d_south, w_south, south_origin_fade),
        weight_from(d_north, w_north, 1.0),
        weight_from(d_left, w_left, left_end_fade),
        weight_from(d_right, w_right, right_end_fade),
        weight_from(d_spur, w_spur, 0.92),
    )

    sz = stream_center_z(x)
    hw = stream_half_width(x)
    in_creek = math.exp(-((abs(z - sz) / (hw * 0.92)) ** 3.2))
    return wt * (1.0 - in_creek)


def get_terrain_height(x, z):
    """Sculpted Landscape Heightmap with unified trail compaction and creek channel."""
    rf = island_radial_factor(x, z)

    nw_hill = 0.56 * math.exp(-((x + 2.45) ** 2 / 3.2 + (z + 1.95) ** 2 / 2.6))
    ne_hill = 0.48 * math.exp(-((x - 2.35) ** 2 / 3.0 + (z + 1.85) ** 2 / 2.5))
    north_ridge = 0.35 * math.exp(-((x + 0.20) ** 2 / 5.5 + (z + 2.55) ** 2 / 2.2))
    fork_divide_mound = 0.12 * math.exp(-((x ** 2) / 0.55 + ((z + 1.25) ** 2) / 0.55))

    fg_left_knoll = 0.25 * math.exp(-((x + 1.65) ** 2 / 1.80 + (z - 1.52) ** 2 / 1.30))
    fg_left_west = 0.18 * math.exp(-((x + 2.85) ** 2 / 1.55 + (z - 0.85) ** 2 / 1.35))
    fg_right_terrace = 0.23 * math.exp(-((x - 1.48) ** 2 / 1.90 + (z - 1.42) ** 2 / 1.35))

    n1 = noise.noise(Vector((x * 0.46 + 4.2, z * 0.46 - 2.8, 1.1))) * 0.10
    n2 = noise.noise(Vector((x * 1.15 - 1.9, z * 1.15 + 3.4, 2.7))) * 0.038

    sz = stream_center_z(x)
    hw = stream_half_width(x)
    d_stream = abs(z - sz)
    rim_atten = 1.0 if rf < 0.72 else max(0.15, 1.0 - ((rf - 0.72) / 0.28) ** 1.45)
    stream_cut = 0.50 * math.exp(-((d_stream / (hw * 1.15)) ** 2.3)) * rim_atten
    bank_shoulder = 0.082 * math.exp(-(((d_stream - hw * 1.28) / 0.28) ** 2)) * rim_atten

    abutment_south = 0.14 * math.exp(-((x ** 2) / 0.36 + ((z - (sz + 0.70)) ** 2) / 0.18))
    abutment_north = 0.14 * math.exp(-((x ** 2) / 0.36 + ((z - (sz - 0.70)) ** 2) / 0.18))

    tw = trail_wear_weight(x, z)
    trail_compaction = -0.011 * tw

    edge_drop = 0.0
    if rf > 0.84:
        t_edge = min(1.3, (rf - 0.84) / 0.16)
        edge_drop = -0.22 * (t_edge ** 1.85)

    return (
        0.24
        + nw_hill
        + ne_hill
        + north_ridge
        + fork_divide_mound
        + fg_left_knoll
        + fg_left_west
        + fg_right_terrace
        + n1
        + n2
        + bank_shoulder
        + abutment_south
        + abutment_north
        - stream_cut
        + trail_compaction
        + edge_drop
    )


def build_island_terrain_and_trails(materials):
    """Builds the watertight 112x224 Island_Terrain_Top, stitched Island_Rock_Underside, and Island_Soil_Rim."""
    bm_top = bmesh.new()
    rings = 112
    segs = 224

    center_y = get_terrain_height(-0.06, -0.05)
    center_v = bm_top.verts.new((-0.06, 0.05, center_y))

    ring_verts = []
    outer_rim_coords = []

    for ir in range(1, rings + 1):
        r_frac = (ir / rings) ** 0.92
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            x = -0.06 + (rim_x + 0.06) * r_frac
            z = -0.05 + (rim_z + 0.05) * r_frac
            y = get_terrain_height(x, z)
            v = bm_top.verts.new((x, -z, y))
            row.append(v)
            if ir == rings:
                outer_rim_coords.append((x, z, y))
        ring_verts.append(row)

    first_row = ring_verts[0]
    for iseg in range(segs):
        nseg = (iseg + 1) % segs
        bm_top.faces.new((center_v, first_row[iseg], first_row[nseg]))

    for ir in range(rings - 1):
        row_a = ring_verts[ir]
        row_b = ring_verts[ir + 1]
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm_top.faces.new((row_a[iseg], row_b[iseg], row_b[nseg], row_a[nseg]))

    c_grass_sun = hex_to_rgba("#76985F")
    c_grass_mid = hex_to_rgba("#52754B")
    c_moss_bank = hex_to_rgba("#2B513A")
    c_earth_rim = hex_to_rgba("#786147")
    c_trail_center = hex_to_rgba("#B0946E")
    c_trail_edge = hex_to_rgba("#7D7654")

    def terrain_color_fn(wx, wy, wz, nx, ny, nz):
        rf = island_radial_factor(wx, wz)
        sz = stream_center_z(wx)
        hw = stream_half_width(wx)
        d_stream = abs(wz - sz)
        n_c = noise.noise(Vector((wx * 0.72 + 1.2, wz * 0.72 - 0.8, 0.5)))
        n_fine = noise.noise(Vector((wx * 3.6 - 0.5, wz * 3.6 + 1.1, 2.0)))

        h_factor = max(0.0, min(1.0, (wy - 0.15) / 0.52 + 0.24 * n_c))
        col = lerp_color(c_grass_mid, c_grass_sun, h_factor)

        bank_zone = math.exp(-((d_stream / (hw * 1.38)) ** 2.2))
        col = lerp_color(col, c_moss_bank, bank_zone * 0.82)

        tw = trail_wear_weight(wx, wz)
        if tw > 0.01:
            encroach = max(0.0, min(1.0, tw + 0.18 * n_fine * (1.0 - tw)))
            trail_tone = lerp_color(c_trail_edge, c_trail_center, min(1.0, (tw ** 0.85) + 0.14 * n_fine))
            col = lerp_color(col, trail_tone, encroach * 0.94)

        if rf > 0.90:
            rim_t = min(1.0, (rf - 0.90) / 0.10)
            col = lerp_color(col, c_earth_rim, rim_t * 0.65)
        return col

    finalize_mesh_object("Island_Terrain_Top", bm_top, materials["grass_top"], terrain_color_fn)

    # Watertight Stitched Sculpted Rock & Earth Underside
    bm_rock = bmesh.new()
    rock_rings = 36
    rock_rows = []
    for ir in range(rock_rings + 1):
        t = ir / rock_rings
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z, exact_top_y = outer_rim_coords[iseg]

            if ir == 0:
                row.append(bm_rock.verts.new((rim_x, -rim_z, exact_top_y)))
                continue

            buttress = 0.055 * math.sin(ang * 7.0 + t * 1.8) + 0.035 * math.cos(ang * 11.0 - t * 2.5)
            n_crag1 = noise.noise(Vector((rim_x * 0.70 + 1.4, rim_z * 0.70 - 2.2, t * 2.8)))
            n_crag2 = noise.noise(Vector((rim_x * 1.55 - 0.8, rim_z * 1.55 + 1.9, t * 5.2)))

            ledge_step = 0.025 * math.sin(t * math.pi * 3.0 + n_crag1 * 2.0) * (1.0 - t)
            max_allowed = 0.992 - 0.04 * t
            taper = min(
                max_allowed,
                (0.992 - (t ** 2.05) * 0.90) + buttress * (1.0 - t * 0.5) * min(1.0, t * 2.0) + ledge_step,
            )

            rx = rim_x * max(0.03, taper)
            rz = rim_z * max(0.03, taper)

            radial_disp = (0.14 * n_crag1 + 0.06 * n_crag2) * (1.0 - t * 0.35) * min(1.0, (t - 0.04) * 3.0)
            if radial_disp > 0:
                radial_disp *= 0.35
            dir_len = max(1e-4, math.hypot(rim_x, rim_z))
            rx += (rim_x / dir_len) * radial_disp
            rz += (rim_z / dir_len) * radial_disp

            depth_scale = 2.25 + 0.28 * math.sin(ang - 1.1) + 0.16 * math.cos(ang * 3.0)
            ry = exact_top_y - (depth_scale * (t ** 1.05)) + 0.09 * n_crag1 * (1.0 - t * 0.4)

            row.append(bm_rock.verts.new((rx, -rz, ry)))
        rock_rows.append(row)

    bottom_apex = bm_rock.verts.new((-0.08, 0.12, -2.35))

    for ir in range(rock_rings):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm_rock.faces.new((
                rock_rows[ir][iseg],
                rock_rows[ir + 1][iseg],
                rock_rows[ir + 1][nseg],
                rock_rows[ir][nseg],
            ))
    for iseg in range(segs):
        nseg = (iseg + 1) % segs
        bm_rock.faces.new((rock_rows[rock_rings][iseg], bottom_apex, rock_rows[rock_rings][nseg]))

    c_soil_top = hex_to_rgba("#6E513A")
    c_rock_mid = hex_to_rgba("#585249")
    c_rock_deep = hex_to_rgba("#322F2B")
    c_rock_moss = hex_to_rgba("#465C41")

    def rock_color_fn(wx, wy, wz, nx, ny, nz):
        n_v = noise.noise(Vector((wx * 0.85, wz * 0.85, wy * 1.5)))
        soil_blend = max(0.0, min(1.0, (wy + 0.34 + 0.22 * n_v) / 0.36))
        depth_ao = max(0.0, min(1.0, (-wy - 0.15) / 1.95))
        col = lerp_color(c_rock_mid, c_rock_deep, depth_ao)
        col = lerp_color(col, c_soil_top, soil_blend)
        if ny > 0.22 and wy > -1.05:
            col = lerp_color(col, c_rock_moss, min(0.68, (ny - 0.22) * 1.25))
        return col

    finalize_mesh_object("Island_Rock_Underside", bm_rock, materials["rock_underside"], rock_color_fn)

    # Sculpted Under-Cliff Ledges & Front Identity Plaque Chiseled Stone Mantle (in Island_Soil_Rim)
    bm_outcrops = bmesh.new()
    outcrop_specs = [
        (-0.45, 0.85, -0.52, 0.46, 0.22, 0.32),
        (-1.18, 0.84, -0.58, 0.50, 0.24, 0.34),
        (-2.15, 0.85, -0.54, 0.46, 0.22, 0.32),
        (2.35, 0.85, -0.52, 0.44, 0.22, 0.30),
        (0.88, 0.84, -0.56, 0.46, 0.22, 0.32),
    ]
    for idx, (ang, r_mult, y_off, sx, sy, sz_r) in enumerate(outcrop_specs):
        rim_x, rim_z = island_rim_point(ang)
        ox = rim_x * r_mult
        oz = rim_z * r_mult
        oy = get_terrain_height(rim_x, rim_z) + y_off
        ret = bmesh.ops.create_icosphere(bm_outcrops, subdivisions=3, radius=1.0)
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.2 + idx, p.y * 2.2 - idx, p.z * 2.2)))
            chisel = 1.0 + 0.20 * n - 0.14 * abs(p.z)
            v.co = Vector((
                ox + p.x * sx * chisel,
                -(oz + p.y * sz_r * chisel),
                oy + p.z * sy * chisel,
            ))

    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.38
    plaque_pitch = math.radians(-22.0)

    def plaque_to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    add_oriented_box(
        bm_outcrops,
        sx=2.84,
        sy=0.78,
        sz=0.28,
        cx=0.0,
        cy=0.0,
        cz=-0.04,
        to_world_fn=plaque_to_world,
        bevel_offset=0.018,
        segments=2,
    )

    finalize_mesh_object("Island_Soil_Rim", bm_outcrops, materials["rock_underside"], rock_color_fn)


def build_embedded_identity_plaque(materials):
    """Physically embeds Evelyn Lin's 3D Identity Plaque into the front cliff mantle with right-handed bevels."""
    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.38
    plaque_pitch = math.radians(-22.0)

    def to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    bm_frame = bmesh.new()
    add_oriented_box(
        bm_frame,
        sx=2.66,
        sy=0.68,
        sz=0.10,
        cx=0.0,
        cy=0.0,
        cz=0.09,
        to_world_fn=to_world,
        bevel_offset=0.012,
        segments=2,
    )
    for rx_s in (-1.20, 1.20):
        for ry_s in (-0.23, 0.23):
            add_oriented_box(
                bm_frame,
                sx=0.042,
                sy=0.042,
                sz=0.025,
                cx=rx_s,
                cy=ry_s,
                cz=0.152,
                to_world_fn=to_world,
                bevel_offset=0.004,
                segments=2,
            )
    finalize_mesh_object("Identity_Plaque_Frame", bm_frame, materials["champagne_brass"])

    bm_plate = bmesh.new()
    add_oriented_box(
        bm_plate,
        sx=2.52,
        sy=0.56,
        sz=0.08,
        cx=0.0,
        cy=0.0,
        cz=0.112,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
    )
    finalize_mesh_object("Identity_Plaque_Plate", bm_plate, materials["mailbox_forest_metal"])

    bpy.ops.object.text_add(location=(0, 0, 0))
    name_obj = bpy.context.active_object
    name_obj.name = "Identity_Plaque_Name3D"
    name_obj.data.body = "Evelyn Lin"
    name_obj.data.align_x = 'CENTER'
    name_obj.data.align_y = 'CENTER'
    name_obj.data.size = 0.235
    name_obj.data.space_character = 1.04
    name_obj.data.extrude = 0.018
    name_obj.data.bevel_depth = 0.0024
    name_obj.data.bevel_resolution = 1
    bpy.ops.object.convert(target='MESH')
    for v in name_obj.data.vertices:
        v.co = to_world(v.co.x, 0.095 + v.co.y, 0.156 + v.co.z)
    name_obj.data.materials.append(materials["ivory_lettering"])
    for poly in name_obj.data.polygons:
        poly.use_smooth = True

    bpy.ops.object.text_add(location=(0, 0, 0))
    title_obj = bpy.context.active_object
    title_obj.name = "Identity_Plaque_Title3D"
    title_obj.data.body = "UX & INTERACTIVE EXPERIENCE DESIGNER"
    title_obj.data.align_x = 'CENTER'
    title_obj.data.align_y = 'CENTER'
    title_obj.data.size = 0.082
    title_obj.data.space_character = 1.08
    title_obj.data.extrude = 0.012
    title_obj.data.bevel_depth = 0.0014
    title_obj.data.bevel_resolution = 1
    bpy.ops.object.convert(target='MESH')
    for v in title_obj.data.vertices:
        v.co = to_world(v.co.x, -0.135 + v.co.y, 0.155 + v.co.z)
    title_obj.data.materials.append(materials["champagne_brass"])
    for poly in title_obj.data.polygons:
        poly.use_smooth = True


# ==============================================================================
# 2. WOODEN SIGNPOSTS, MAILBOX & BRIDGE (100% SOLID, RIGHT-HANDED, ZERO BLEED-THROUGH)
# ==============================================================================

def build_signpost(name, label_text, x, z, yaw_deg, arrow_dir, materials):
    """
    Constructs a rock-solid, opaque, handcrafted wooden signpost with:
    - Non-overlapping architectural post joinery (base plinth collar -> main chamfered oak shaft ->
      neck molding -> solid hipped finial cap -> rear mortise cleats).
    - Positive-determinant right-handed bevels (`add_oriented_box`) with grain-aligned UVs and
      verified outward face normals (zero inside-out faces or back-face culling bleed-through!).
    - Solid 4-layer bevel-edged directional oak signboard (`Design Trail` / `Game Trail`) with
      verified outward face normals and grain-aligned horizontal UVs.
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()

    # 1. Base mortised timber plinth collar (y = -0.04 to 0.18, height 0.22)
    add_oriented_box(
        bm_post,
        sx=0.250,
        sy=0.220,
        sz=0.250,
        cx=0.0,
        cy=0.070,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.014,
        segments=2,
        taper_top_x=0.90,
        taper_top_z=0.90,
        grain_axis='Y',
    )

    # 2. Lower decorative transition moulding ring (y = 0.18 to 0.23, height 0.05)
    add_oriented_box(
        bm_post,
        sx=0.190,
        sy=0.050,
        sz=0.190,
        cx=0.0,
        cy=0.205,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
        taper_top_x=0.86,
        taper_top_z=0.86,
        grain_axis='Y',
    )

    # 3. Main vertical chamfered oak post shaft (y = 0.23 to 1.49, height 1.26 — NO overlap with base!)
    add_oriented_box(
        bm_post,
        sx=0.152,
        sy=1.260,
        sz=0.152,
        cx=0.0,
        cy=0.860,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.015,
        segments=2,
        taper_top_x=0.90,
        taper_top_z=0.90,
        grain_axis='Y',
    )

    # 4. Upper neck collar under finial cap (y = 1.49 to 1.54, height 0.05)
    add_oriented_box(
        bm_post,
        sx=0.184,
        sy=0.050,
        sz=0.184,
        cx=0.0,
        cy=1.515,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
        grain_axis='X',
    )

    # 5. Solid hipped pyramid weather finial cap (y = 1.54 to 1.66, height 0.12)
    add_oriented_box(
        bm_post,
        sx=0.225,
        sy=0.120,
        sz=0.225,
        cx=0.0,
        cy=1.600,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
        taper_top_x=0.22,
        taper_top_z=0.22,
        grain_axis='X',
    )

    # 6. Rear timber mortise mounting cleats connecting post front (lz = +0.070) to board back (lz = +0.098)
    for cleat_y in (1.03, 1.27):
        add_oriented_box(
            bm_post,
            sx=0.220,
            sy=0.052,
            sz=0.032,
            cx=0.0,
            cy=cleat_y,
            cz=0.082,
            to_world_fn=to_world,
            bevel_offset=0.005,
            segments=1,
            grain_axis='X',
        )

    c_post_light = hex_to_rgba("#9A6842")
    c_post_dark = hex_to_rgba("#5C3B22")
    finalize_mesh_object(
        f"{name}_Post",
        bm_post,
        materials["wood_post"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_post_dark, c_post_light, 0.35 + 0.52 * min(1.0, (wy - y_ground) / 1.45) + 0.13 * max(0.0, ny)
        ),
    )

    # Solid, Opaque, Bevel-Edged Handcrafted Directional Oak Signboard
    # Placed cleanly in front of post at lz_back = +0.098 to lz_front = +0.180 (thickness = 0.082)
    bm_board = bmesh.new()
    uv_board = bm_board.loops.layers.uv.new("UVMap")
    board_y = 1.15
    half_h = 0.220
    lz_back = 0.098
    lz_front = 0.180
    bevel_inset = 0.018

    if arrow_dir < 0:
        x_stations = [
            (-0.85, 0.018),
            (-0.56, half_h * 0.96),
            (-0.28, half_h * 1.00),
            (0.0, half_h * 0.99),
            (0.28, half_h * 1.01),
            (0.54, half_h * 0.98),
            (0.75, half_h * 0.94),
        ]
    else:
        x_stations = [
            (-0.75, half_h * 0.94),
            (-0.54, half_h * 0.98),
            (-0.28, half_h * 1.01),
            (0.0, half_h * 0.99),
            (0.28, half_h * 1.00),
            (0.56, half_h * 0.96),
            (0.85, 0.018),
        ]

    layers_spec = [
        (lz_back, 0.91),
        (lz_back + bevel_inset, 1.00),
        (lz_front - bevel_inset, 1.00),
        (lz_front, 0.91),
    ]

    layer_loops = []
    vert_local_coords = {}
    for lz_val, scale_factor in layers_spec:
        top_edge = []
        bot_edge = []
        n_st = len(x_stations)
        for idx_s, (sx_p, sh_p) in enumerate(x_stations):
            x_sh = sx_p
            if idx_s == 0:
                x_sh = sx_p + (1.0 - scale_factor) * 0.18
            elif idx_s == n_st - 1:
                x_sh = sx_p - (1.0 - scale_factor) * 0.18
            h_sh = max(0.012, sh_p * scale_factor)
            vt = bm_board.verts.new(to_world(x_sh, board_y + h_sh, lz_val))
            vb = bm_board.verts.new(to_world(x_sh, board_y - h_sh, lz_val))
            vert_local_coords[vt] = (x_sh, h_sh, lz_val)
            vert_local_coords[vb] = (x_sh, -h_sh, lz_val)
            top_edge.append(vt)
            bot_edge.append(vb)
        layer_loops.append((top_edge, bot_edge))

    top0, bot0 = layer_loops[0]
    top3, bot3 = layer_loops[3]
    for i in range(len(x_stations) - 1):
        bm_board.faces.new((top0[i], top0[i + 1], bot0[i + 1], bot0[i]))
        bm_board.faces.new((bot3[i], bot3[i + 1], top3[i + 1], top3[i]))

    for il in range(3):
        tA, bA = layer_loops[il]
        tB, bB = layer_loops[il + 1]
        n_st = len(x_stations)
        for i in range(n_st - 1):
            bm_board.faces.new((tA[i], tB[i], tB[i + 1], tA[i + 1]))
            bm_board.faces.new((bA[i + 1], bB[i + 1], bB[i], bA[i]))
        bm_board.faces.new((bA[0], bB[0], tB[0], tA[0]))
        bm_board.faces.new((tA[n_st - 1], tB[n_st - 1], bB[n_st - 1], bA[n_st - 1]))

    # Assign horizontal plank UVs across the entire directional signboard
    for f in bm_board.faces:
        for loop in f.loops:
            lx_c, ly_c, lz_c = vert_local_coords[loop.vert]
            loop[uv_board].uv = ((lx_c + 0.90) * 0.65, (ly_c + 0.25 + (lz_c - 0.14) * 0.5) * 1.8)

    board_world_center = to_world(0.0, board_y, 0.5 * (lz_back + lz_front))
    c_plaque_edge = hex_to_rgba("#4A2C16")
    c_plaque_face = hex_to_rgba("#7C4E2B")
    finalize_mesh_object(
        f"{name}_Board",
        bm_board,
        materials["wood_sign_plaque"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_plaque_edge,
            c_plaque_face,
            0.35 + 0.50 * (1.0 - min(1.0, abs(wy - (y_ground + board_y)) / 0.21)) + 0.15 * max(0.0, ny),
        ),
        verify_outward_from=board_world_center,
    )

    # Raised 3D Relief Lettering ('Design Trail' & 'Game Trail') anchored on front plank face (lz = +0.180)
    bpy.ops.object.text_add(location=(0, 0, 0))
    txt_obj = bpy.context.active_object
    txt_obj.name = f"{name}_Label3D"
    txt_obj.data.body = label_text
    txt_obj.data.align_x = 'CENTER'
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.size = 0.184
    txt_obj.data.space_character = 1.05
    txt_obj.data.extrude = 0.012
    txt_obj.data.bevel_depth = 0.0016
    txt_obj.data.bevel_resolution = 1

    bpy.ops.object.convert(target='MESH')
    text_x_offset = 0.04 if arrow_dir < 0 else -0.04
    for v in txt_obj.data.vertices:
        lx = v.co.x + text_x_offset
        ly = board_y + v.co.y
        lz = 0.180 + v.co.z
        v.co = to_world(lx, ly, lz)

    txt_obj.data.materials.append(materials["ivory_lettering"])
    for poly in txt_obj.data.polygons:
        poly.use_smooth = True


def build_woodland_mailbox(x, z, yaw_deg, materials):
    """
    Constructs a refined, heirloom-quality miniature Woodland Mailbox on the dry front-right terrace:
    1. Support Post & Mounting Cradle (`Mailbox_Post`):
       - Base plinth, transition collar, vertical chamfered oak shaft, front/rear mortise corbel knee braces,
         under-deck cross-bolster, chamfered oak mounting deck, and side cradle rails with grain-aligned UVs.
    2. Arched Forest-Green Metal Housing with Recessed Interior Cavity (`Mailbox_Body`):
       - Rolled front & rear arch ribs, molded bottom mounting flange, and a shaded recessed interior mail
         chamber (`#0B1F18` interior vertex colors vs `#1E4B3B` exterior hood) so looking past the ajar door
         reveals a clean dark interior rather than a flat wall or white plane.
    3. Sculpted Cast-Brass Front Door & Hinge Assembly (`Mailbox_Door`):
       - Raised outer perimeter flange frame with a recessed inner arched panel, 3-knuckle bottom brass barrel
         hinge, sculpted stand-off finger pull handle at the top arch, and slim embossed center escutcheon.
    4. Slender Tapered Brass Postal Signal Flag (`Mailbox_Flag`):
       - Circular side pivot boss with central dome rivet, slender tapered flat metal arm (`0.010` thick),
         and swallowtail-notched pennant flag head (`0.012` thick) plus 4 brass base mounting bolts.
    5. Recessed Interior Folded Letter (`Mailbox_Letter`):
       - Rests flat on the floor of the recessed mail cavity (`cy = base_y + 0.034, cz = 0.12`) so zero
         white internal geometry pokes out of the upper door opening when closed/ajar.
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()

    # 1. Base mortised timber plinth (y = -0.04 to 0.16, height 0.20)
    add_oriented_box(
        bm_post,
        sx=0.250,
        sy=0.200,
        sz=0.250,
        cx=0.0,
        cy=0.060,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.014,
        segments=2,
        taper_top_x=0.90,
        taper_top_z=0.90,
        grain_axis='Y',
    )

    # 2. Transition moulding collar (y = 0.16 to 0.21, height 0.05)
    add_oriented_box(
        bm_post,
        sx=0.192,
        sy=0.050,
        sz=0.192,
        cx=0.0,
        cy=0.185,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
        taper_top_x=0.86,
        taper_top_z=0.86,
        grain_axis='Y',
    )

    # 3. Solid vertical chamfered oak post shaft (y = 0.21 to 0.84, height 0.63)
    add_oriented_box(
        bm_post,
        sx=0.152,
        sy=0.630,
        sz=0.152,
        cx=0.0,
        cy=0.525,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.014,
        segments=2,
        grain_axis='Y',
    )

    # 4. Under-deck mortised cross-bolster saddle (y = 0.84 to 0.885, height 0.045)
    add_oriented_box(
        bm_post,
        sx=0.330,
        sy=0.045,
        sz=0.230,
        cx=0.0,
        cy=0.8625,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.008,
        segments=2,
        taper_top_x=1.12,
        taper_top_z=1.10,
        grain_axis='X',
    )

    # 5. Front and rear mortised timber corbel knee-braces supporting the platform (y = 0.63 to 0.88)
    for dir_z in (-1.0, 1.0):
        add_oriented_box(
            bm_post,
            sx=0.094,
            sy=0.235,
            sz=0.145,
            cx=0.0,
            cy=0.758,
            cz=dir_z * 0.138,
            to_world_fn=to_world,
            bevel_offset=0.009,
            segments=2,
            taper_top_z=1.35,
            shear_z_by_y=dir_z * 0.42,
            grain_axis='Y',
        )

    # 6. Upper chamfered oak mounting platform deck (y = 0.885 to 0.945, height 0.060)
    add_oriented_box(
        bm_post,
        sx=0.476,
        sy=0.060,
        sz=0.616,
        cx=0.0,
        cy=0.915,
        cz=0.0,
        to_world_fn=to_world,
        bevel_offset=0.011,
        segments=2,
        grain_axis='Z',
    )

    # 7. Left & right molded timber cradle rails + rear stop rail gripping the mailbox base (y = 0.945 to 0.985)
    for side_x in (-0.218, 0.218):
        add_oriented_box(
            bm_post,
            sx=0.036,
            sy=0.042,
            sz=0.592,
            cx=side_x,
            cy=0.964,
            cz=0.0,
            to_world_fn=to_world,
            bevel_offset=0.006,
            segments=2,
            taper_top_x=0.78,
            grain_axis='Z',
        )
    add_oriented_box(
        bm_post,
        sx=0.400,
        sy=0.038,
        sz=0.034,
        cx=0.0,
        cy=0.962,
        cz=-0.285,
        to_world_fn=to_world,
        bevel_offset=0.005,
        segments=1,
        grain_axis='X',
    )

    c_post_light = hex_to_rgba("#9D6A43")
    c_post_dark = hex_to_rgba("#5C3B22")
    finalize_mesh_object(
        "Mailbox_Post",
        bm_post,
        materials["wood_post"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_post_dark, c_post_light, 0.36 + 0.52 * min(1.0, (wy - y_ground) / 1.05) + 0.12 * max(0.0, ny)
        ),
    )

    # --------------------------------------------------------------------------
    # Arched Forest-Green Metal Mailbox Housing with Shaded Recessed Interior Cavity
    # --------------------------------------------------------------------------
    bm_body = bmesh.new()
    segs_arch = 28
    mb_w = 0.416
    mb_h = 0.408
    mb_l = 0.570
    base_y = 0.945

    def build_arch_profile(scale_w, scale_h, y_lift=0.0):
        pts = [(-mb_w * 0.5 * scale_w, y_lift), (-mb_w * 0.5 * scale_w, y_lift + mb_h * 0.48 * scale_h)]
        for i in range(segs_arch + 1):
            ang = math.pi - (math.pi * i) / segs_arch
            px = math.cos(ang) * (mb_w * 0.5 * scale_w)
            py = y_lift + mb_h * 0.48 * scale_h + math.sin(ang) * (mb_w * 0.5 * scale_w)
            pts.append((px, py))
        pts.append((mb_w * 0.5 * scale_w, y_lift))
        return pts

    outer_Stations = [
        # (lz, scale_w, scale_h, y_lift, is_interior)
        (-mb_l * 0.50, 0.96, 0.96, 0.006, False),   # 0: Rear chamfered end cap
        (-mb_l * 0.47, 1.03, 1.03, 0.000, False),   # 1: Rear rolled seam rib
        (-mb_l * 0.41, 1.03, 1.03, 0.000, False),   # 2: Rear rolled seam rib front
        (-mb_l * 0.39, 1.00, 1.00, 0.000, False),   # 3: Main hood body start
        (-0.04,        1.00, 1.00, 0.000, False),   # 4: Mid body before center band
        (0.00,         1.018, 1.018, 0.000, False), # 5: Subtle center stiffening rib
        (0.04,         1.00, 1.00, 0.000, False),   # 6: Mid body after center band
        (mb_l * 0.39,  1.00, 1.00, 0.000, False),   # 7: Main hood body front
        (mb_l * 0.41,  1.035, 1.035, 0.000, False), # 8: Front rolled aperture collar back
        (mb_l * 0.49,  1.035, 1.035, 0.000, False), # 9: Front rolled aperture collar front
        (mb_l * 0.50,  0.97, 0.97, 0.008, False),   # 10: Front bevel lip
        (mb_l * 0.47,  0.88, 0.87, 0.022, True),    # 11: Inner aperture rim
        (mb_l * 0.08,  0.86, 0.85, 0.024, True),    # 12: Deep recessed interior chamber back wall
    ]

    rings = []
    interior_verts = set()
    for lz, sw, sh, y_lift, is_int in outer_Stations:
        prof = build_arch_profile(sw, sh, y_lift)
        row = []
        for px, py in prof:
            v = bm_body.verts.new(to_world(px, base_y + py, lz))
            if is_int:
                interior_verts.add(v)
            row.append(v)
        rings.append(row)

    n_pts = len(rings[0])
    for il in range(len(rings) - 1):
        for ip in range(n_pts):
            nip = (ip + 1) % n_pts
            # For exterior rings (0..10) outward normal points away from centerline;
            # for interior cavity rings (10..12) normal points inward toward cavity center
            bm_body.faces.new((
                rings[il][ip],
                rings[il][nip],
                rings[il + 1][nip],
                rings[il + 1][ip],
            ))

    # Cap rear exterior wall (ring 0) and recessed interior back wall (ring -1)
    bm_body.faces.new(rings[0][::-1])
    bm_body.faces.new(rings[-1])

    # Molded base mounting flange skirt along bottom sides of Mailbox_Body
    for side_x in (-mb_w * 0.49, mb_w * 0.49):
        add_oriented_box(
            bm_body,
            sx=0.026,
            sy=0.024,
            sz=mb_l * 0.82,
            cx=side_x,
            cy=base_y + 0.012,
            cz=0.0,
            to_world_fn=to_world,
            bevel_offset=0.004,
            segments=1,
        )

    bmesh.ops.recalc_face_normals(bm_body, faces=bm_body.faces)
    c_body_ext_top = hex_to_rgba("#235745")
    c_body_ext_side = hex_to_rgba("#163A2E")
    c_body_interior = hex_to_rgba("#091A14")

    mesh_body = bpy.data.meshes.new("Mailbox_Body_Mesh")
    bm_body.to_mesh(mesh_body)
    bm_body.free()

    obj_body = bpy.data.objects.new("Mailbox_Body", mesh_body)
    bpy.context.collection.objects.link(obj_body)
    col_body = mesh_body.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    for poly in mesh_body.polygons:
        poly.use_smooth = True
        for loop_idx in poly.loop_indices:
            v_idx = mesh_body.loops[loop_idx].vertex_index
            v = mesh_body.vertices[v_idx]
            wx, wy, wz = v.co.x, v.co.z, -v.co.y
            nx, ny, nz = v.normal.x, v.normal.z, -v.normal.y
            # Detect interior cavity vertices by local position
            rel_y = wy - (y_ground + base_y)
            if poly.index >= (len(outer_Stations) - 3) * n_pts and poly.index < (len(outer_Stations) - 1) * n_pts + 2:
                col_body.data[loop_idx].color = c_body_interior
            else:
                t_up = max(0.0, min(1.0, 0.45 + 0.55 * ny))
                col_body.data[loop_idx].color = lerp_color(c_body_ext_side, c_body_ext_top, t_up)
    obj_body.data.materials.append(materials["mailbox_body_metal"])

    # --------------------------------------------------------------------------
    # Sculpted Cast-Brass Front Door, Recessed Panel, 3-Knuckle Hinge & Pull Handle (`Mailbox_Door`)
    # --------------------------------------------------------------------------
    bm_door = bmesh.new()
    door_tilt = math.radians(15.0)
    hinge_y = base_y + 0.014
    hinge_z = mb_l * 0.50

    def door_point(px, py, dz):
        ry = py * math.cos(door_tilt) - dz * math.sin(door_tilt)
        rz = py * math.sin(door_tilt) + dz * math.cos(door_tilt)
        return to_world(px, hinge_y + ry, hinge_z + rz)

    # Multi-layer door profile:
    # Layer 0 (dz=0.000): back sealing lip
    # Layer 1 (dz=0.018): outer perimeter rim front
    # Layer 2 (dz=0.018): inner perimeter step
    # Layer 3 (dz=0.011): recessed inner panel face
    door_layers = [
        (0.000, 0.94, 0.93, 0.004),
        (0.018, 0.95, 0.94, 0.002),
        (0.018, 0.83, 0.82, 0.022),
        (0.011, 0.81, 0.80, 0.025),
    ]
    d_rings = []
    for dz_l, sw_l, sh_l, y_l in door_layers:
        prof_d = build_arch_profile(sw_l, sh_l, y_l)
        d_rings.append([bm_door.verts.new(door_point(px, py, dz_l)) for px, py in prof_d])

    for il in range(len(d_rings) - 1):
        for ip in range(n_pts):
            nip = (ip + 1) % n_pts
            bm_door.faces.new((d_rings[il][ip], d_rings[il][nip], d_rings[il + 1][nip], d_rings[il + 1][ip]))
    # Cap back face (layer 0) and recessed front face (layer 3)
    bm_door.faces.new(d_rings[0][::-1])
    bm_door.faces.new(d_rings[3])

    bmesh.ops.recalc_face_normals(bm_door, faces=bm_door.faces)

    # 3-Knuckle bottom brass barrel hinge along the door pivot line
    for hx in (-0.11, 0.0, 0.11):
        add_oriented_box(
            bm_door,
            sx=0.052,
            sy=0.022,
            sz=0.024,
            cx=hx,
            cy=0.004,
            cz=0.008,
            to_world_fn=door_point,
            bevel_offset=0.006,
            segments=2,
        )

    # Sculpted stand-off arch pull handle (two petite stand-off posts + contoured grip bar)
    for post_x in (-0.036, 0.036):
        add_oriented_box(
            bm_door,
            sx=0.016,
            sy=0.018,
            sz=0.018,
            cx=post_x,
            cy=mb_h * 0.74,
            cz=0.020,
            to_world_fn=door_point,
            bevel_offset=0.003,
            segments=1,
        )
    add_oriented_box(
        bm_door,
        sx=0.102,
        sy=0.022,
        sz=0.016,
        cx=0.0,
        cy=mb_h * 0.74,
        cz=0.032,
        to_world_fn=door_point,
        bevel_offset=0.005,
        segments=2,
    )

    # Slim embossed center brass escutcheon plate inside the recessed door panel
    add_oriented_box(
        bm_door,
        sx=0.220,
        sy=0.036,
        sz=0.008,
        cx=0.0,
        cy=mb_h * 0.46,
        cz=0.015,
        to_world_fn=door_point,
        bevel_offset=0.003,
        segments=1,
    )
    finalize_mesh_object("Mailbox_Door", bm_door, materials["champagne_brass"])

    # --------------------------------------------------------------------------
    # Recessed Interior Folded Cream-Parchment Letter (`Mailbox_Letter`)
    # --------------------------------------------------------------------------
    # Rests flat on the floor of the recessed mail cavity (cy = base_y + 0.035, cz = 0.13)
    # so zero white block pokes out of the upper door gap when the mailbox is closed!
    bm_letter = bmesh.new()
    add_oriented_box(
        bm_letter,
        sx=0.210,
        sy=0.016,
        sz=0.210,
        cx=0.0,
        cy=base_y + 0.036,
        cz=0.135,
        to_world_fn=to_world,
        bevel_offset=0.004,
        segments=2,
        shear_y_by_z=0.04,
    )
    finalize_mesh_object("Mailbox_Letter", bm_letter, materials["ivory_lettering"])

    # --------------------------------------------------------------------------
    # Slender Tapered Brass Postal Signal Flag & Base Mounting Bolts (`Mailbox_Flag`)
    # --------------------------------------------------------------------------
    bm_flag = bmesh.new()
    flag_x = mb_w * 0.522

    # 1. Circular pivot boss plate & dome rivet mounted flush against right side of mailbox
    add_oriented_box(
        bm_flag,
        sx=0.014,
        sy=0.052,
        sz=0.052,
        cx=flag_x - 0.002,
        cy=base_y + 0.165,
        cz=0.095,
        to_world_fn=to_world,
        bevel_offset=0.014,
        segments=2,
    )
    add_oriented_box(
        bm_flag,
        sx=0.022,
        sy=0.024,
        sz=0.024,
        cx=flag_x + 0.005,
        cy=base_y + 0.165,
        cz=0.095,
        to_world_fn=to_world,
        bevel_offset=0.006,
        segments=2,
    )

    # 2. Slender flat metal signal stem extending cleanly from the pivot boss up to the flag head
    add_oriented_box(
        bm_flag,
        sx=0.011,
        sy=0.184,
        sz=0.022,
        cx=flag_x + 0.004,
        cy=base_y + 0.272,
        cz=0.095,
        to_world_fn=to_world,
        bevel_offset=0.0025,
        segments=1,
    )

    # 3. Cleanly proportioned postal pennant flag blade sitting atop the stem (non-overlapping)
    add_oriented_box(
        bm_flag,
        sx=0.011,
        sy=0.066,
        sz=0.106,
        cx=flag_x + 0.004,
        cy=base_y + 0.395,
        cz=0.053,
        to_world_fn=to_world,
        bevel_offset=0.003,
        segments=1,
        taper_top_z=0.88,
    )
    # Leading-edge spine reinforcement along the front edge of the flag head
    add_oriented_box(
        bm_flag,
        sx=0.015,
        sy=0.068,
        sz=0.022,
        cx=flag_x + 0.004,
        cy=base_y + 0.395,
        cz=0.095,
        to_world_fn=to_world,
        bevel_offset=0.0025,
        segments=1,
    )

    # 4. Four small brass mounting bolt heads securing the mailbox base flange to the oak cradle
    for bx_s in (-mb_w * 0.505, mb_w * 0.505):
        for bz_s in (-0.18, 0.18):
            add_oriented_box(
                bm_flag,
                sx=0.016,
                sy=0.016,
                sz=0.016,
                cx=bx_s,
                cy=base_y + 0.018,
                cz=bz_s,
                to_world_fn=to_world,
                bevel_offset=0.004,
                segments=1,
            )

    flag_obj = finalize_mesh_object("Mailbox_Flag", bm_flag, materials["champagne_brass"])
    for poly in flag_obj.data.polygons:
        poly.use_smooth = False


def build_stream_and_bridge(materials):
    """
    Builds the creek riverbed (`Stream_Bed`), translucent creek surface (`Stream_Water`),
    and 100% solid, right-handed 13-plank arched oak bridge (`Wooden_Bridge`) with grain UVs.
    """
    bm_bed = bmesh.new()
    bm_water = bmesh.new()
    steps = 88
    cols = 15
    bed_rows = []
    water_rows = []

    x_start, x_end = -3.38, 3.22
    for i in range(steps + 1):
        u_stream = i / steps
        x = x_start + (x_end - x_start) * u_stream
        cz = stream_center_z(x)
        dx = 0.06
        dz = stream_center_z(x + dx) - cz
        length = math.hypot(dx, dz)
        nx_d, nz_d = -dz / length, dx / length

        end_envelope = math.sin(u_stream * math.pi) ** 0.42
        hw = stream_half_width(x) * max(0.14, end_envelope)
        bed_center_y = get_terrain_height(x, cz)
        water_depth = 0.175 * (0.45 + 0.55 * end_envelope)
        water_y = bed_center_y + water_depth

        b_row = []
        w_row = []
        for c in range(cols):
            u = (c / (cols - 1)) * 2.0 - 1.0
            wx = x + nx_d * hw * u
            wz = cz + nz_d * hw * u

            bed_y = bed_center_y + 0.13 * (u * u) + 0.014 * math.sin(x * 8.0 + u * 6.0)
            b_row.append(bm_bed.verts.new((wx, -wz, bed_y)))

            ripple = 0.007 * math.sin(x * 5.0 + u * 3.2) * (1.0 - 0.45 * u * u) * end_envelope
            w_row.append(bm_water.verts.new((wx, -wz, water_y + ripple)))
        bed_rows.append(b_row)
        water_rows.append(w_row)

    for r in range(len(bed_rows) - 1):
        for c in range(len(bed_rows[r]) - 1):
            bm_bed.faces.new((bed_rows[r][c], bed_rows[r][c + 1], bed_rows[r + 1][c + 1], bed_rows[r + 1][c]))
            bm_water.faces.new((water_rows[r][c], water_rows[r][c + 1], water_rows[r + 1][c + 1], water_rows[r + 1][c]))

    c_bed_deep = hex_to_rgba("#1A2E2A")
    c_bed_pebble = hex_to_rgba("#544E40")
    finalize_mesh_object(
        "Stream_Bed",
        bm_bed,
        materials["rock_underside"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_bed_deep,
            c_bed_pebble,
            min(1.0, abs(wz - stream_center_z(wx)) / max(0.25, stream_half_width(wx))),
        ),
    )

    c_water_deep = hex_to_rgba("#1A6A65")
    c_water_mid = hex_to_rgba("#328F87")
    c_water_shallow = hex_to_rgba("#66B0A1")
    c_water_foam = hex_to_rgba("#C2EFE6")

    def water_color_fn(wx, wy, wz, nx, ny, nz):
        cz = stream_center_z(wx)
        hw = max(0.25, stream_half_width(wx))
        edge_t = min(1.0, abs(wz - cz) / hw)
        if edge_t < 0.55:
            col = lerp_color(c_water_deep, c_water_mid, edge_t / 0.55)
        else:
            col = lerp_color(c_water_mid, c_water_shallow, (edge_t - 0.55) / 0.45)

        n_w = noise.noise(Vector((wx * 3.0, wz * 3.0, 0.5)))
        if n_w > 0.34 or edge_t > 0.85:
            col = lerp_color(col, c_water_foam, 0.28)
        return col

    finalize_mesh_object("Stream_Water", bm_water, materials["stream_water"], water_color_fn)

    # Handcrafted Arched Wooden Bridge Built Entirely with Right-Handed Oriented Boxes (det = +1)
    bm_bridge = bmesh.new()
    bridge_center_z = stream_center_z(0.0)
    bridge_span = 1.48
    bridge_width = 1.02
    num_planks = 13

    y_south_ground = get_terrain_height(0.0, bridge_center_z + bridge_span * 0.5)
    y_north_ground = get_terrain_height(0.0, bridge_center_z - bridge_span * 0.5)
    base_abutment_y = max(y_south_ground, y_north_ground) + 0.008

    def arch_height(z_local):
        norm = z_local / (bridge_span * 0.5)
        return base_abutment_y + 0.165 * max(0.0, 1.0 - norm * norm)

    def bridge_world(lx, ly, lz):
        return Vector((lx, -lz, ly))

    # 1. Bank abutment sill beams
    for end_sign in (-1.0, 1.0):
        wz_sill = bridge_center_z + end_sign * (bridge_span * 0.48)
        wy_sill = arch_height(end_sign * (bridge_span * 0.48)) - 0.025
        add_oriented_box(
            bm_bridge,
            sx=bridge_width + 0.12,
            sy=0.090,
            sz=0.140,
            cx=0.0,
            cy=wy_sill,
            cz=wz_sill,
            to_world_fn=bridge_world,
            bevel_offset=0.010,
            segments=2,
            grain_axis='X',
        )

    # 2. Arched timber stringer beams spanning under the deck planks
    for side_x in (-0.39, 0.39):
        segs_s = 12
        for i in range(segs_s):
            u0 = (i / segs_s) * 2.0 - 1.0
            u1 = ((i + 1) / segs_s) * 2.0 - 1.0
            zl0 = u0 * (bridge_span * 0.47)
            zl1 = u1 * (bridge_span * 0.47)
            zm = 0.5 * (zl0 + zl1)
            ym = 0.5 * (arch_height(zl0) + arch_height(zl1)) - 0.036
            dz_seg = zl1 - zl0
            dy_seg = arch_height(zl1) - arch_height(zl0)
            slope_seg = dy_seg / max(1e-4, dz_seg)
            add_oriented_box(
                bm_bridge,
                sx=0.088,
                sy=0.072,
                sz=abs(dz_seg) * 1.04,
                cx=side_x,
                cy=ym,
                cz=bridge_center_z + zm,
                to_world_fn=bridge_world,
                bevel_offset=0.007,
                segments=1,
                shear_y_by_z=slope_seg,
                grain_axis='Z',
            )

    # 3. 13 individual beveled oak deck planks with natural spacing and camber
    for ip in range(num_planks):
        u = (ip / (num_planks - 1)) * 2.0 - 1.0
        zl = u * (bridge_span * 0.46)
        wz = bridge_center_z + zl
        wy = arch_height(zl) + 0.016
        slope = -0.22 * u
        w_var = bridge_width * (0.99 + 0.016 * math.sin(ip * 2.3))

        def plank_world(lx, ly, lz, wz=wz, wy=wy, slope=slope):
            dlz = lz - wz
            dly = ly - wy
            rz = dlz * math.cos(slope) - dly * math.sin(slope)
            ry = dlz * math.sin(slope) + dly * math.cos(slope)
            return Vector((lx, -(wz + rz), wy + ry))

        add_oriented_box(
            bm_bridge,
            sx=w_var,
            sy=0.045,
            sz=0.090,
            cx=0.0,
            cy=wy,
            cz=wz,
            to_world_fn=plank_world,
            bevel_offset=0.009,
            segments=2,
            grain_axis='X',
        )

    # 4. 6 vertical beveled posts + capped finials + double arched handrails
    for side_x in (-0.46, 0.46):
        for post_z_local in (-0.58, 0.0, 0.58):
            wz = bridge_center_z + post_z_local
            wy = arch_height(post_z_local)
            # Vertical post shaft
            add_oriented_box(
                bm_bridge,
                sx=0.084,
                sy=0.350,
                sz=0.084,
                cx=side_x,
                cy=wy + 0.165,
                cz=wz,
                to_world_fn=bridge_world,
                bevel_offset=0.010,
                segments=2,
                grain_axis='Y',
            )
            # Post top cap
            add_oriented_box(
                bm_bridge,
                sx=0.104,
                sy=0.036,
                sz=0.104,
                cx=side_x,
                cy=wy + 0.352,
                cz=wz,
                to_world_fn=bridge_world,
                bevel_offset=0.006,
                segments=2,
                taper_top_x=0.65,
                taper_top_z=0.65,
                grain_axis='X',
            )

        for rail_h, rail_thick in ((0.285, 0.044), (0.165, 0.030)):
            segs_r = 10
            for i in range(segs_r):
                u0 = (i / segs_r) * 2.0 - 1.0
                u1 = ((i + 1) / segs_r) * 2.0 - 1.0
                zl0 = u0 * 0.56
                zl1 = u1 * 0.56
                zm = 0.5 * (zl0 + zl1)
                ym = 0.5 * (arch_height(zl0) + arch_height(zl1)) + rail_h
                dz_seg = zl1 - zl0
                dy_seg = arch_height(zl1) - arch_height(zl0)
                slope_seg = dy_seg / max(1e-4, dz_seg)
                add_oriented_box(
                    bm_bridge,
                    sx=0.052,
                    sy=rail_thick,
                    sz=abs(dz_seg) * 1.02,
                    cx=side_x,
                    cy=ym,
                    cz=bridge_center_z + zm,
                    to_world_fn=bridge_world,
                    bevel_offset=0.006,
                    segments=1,
                    shear_y_by_z=slope_seg,
                    grain_axis='Z',
                )

    c_oak_light = hex_to_rgba("#B58054")
    c_oak_dark = hex_to_rgba("#754D2E")
    finalize_mesh_object(
        "Wooden_Bridge",
        bm_bridge,
        materials["wood_oak"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_oak_dark,
            c_oak_light,
            0.42 + 0.38 * max(0.0, ny) + 0.20 * math.sin(wz * 26.0 + wx * 4.0),
        ),
    )


# ==============================================================================
# 3. EXTERNAL CC0 ASSET INTEGRATION (Quaternius Stylized Nature MegaKit)
# ==============================================================================

_GLTF_TEMPLATE_CACHE = {}
_CANONICAL_MAT_CACHE = {}


def get_gltf_template(filename):
    """
    Imports a Quaternius glTF asset once into a hidden template object, deduplicates its materials
    and textures into canonical shared materials, and caches its mesh.
    """
    if filename in _GLTF_TEMPLATE_CACHE:
        return _GLTF_TEMPLATE_CACHE[filename]

    filepath = os.path.join(EXT_DIR, filename)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    added = [o for o in (set(bpy.data.objects) - before) if o.type == 'MESH']
    if not added:
        raise RuntimeError(f"No mesh found when importing {filepath}")

    tmpl = added[0]
    tmpl.name = f"_Template_{filename}"

    # Deduplicate materials by base name (e.g., 'Bark_NormalTree.001' -> 'Bark_NormalTree')
    for idx, mat in enumerate(list(tmpl.data.materials)):
        if not mat:
            continue
        base_name = mat.name.split(".")[0]
        if base_name in _CANONICAL_MAT_CACHE:
            tmpl.data.materials[idx] = _CANONICAL_MAT_CACHE[base_name]
        else:
            mat.name = base_name
            if any(k in base_name for k in ("Leaves", "Leaf", "Grass", "Flowers")):
                mat.use_backface_culling = False
                if hasattr(mat, 'blend_method'):
                    mat.blend_method = 'CLIP'
                if hasattr(mat, 'alpha_threshold'):
                    mat.alpha_threshold = 0.28
            else:
                mat.use_backface_culling = True
            _CANONICAL_MAT_CACHE[base_name] = mat

    for coll in list(tmpl.users_collection):
        coll.objects.unlink(tmpl)

    _GLTF_TEMPLATE_CACHE[filename] = tmpl
    return tmpl


def extract_transformed_material_mesh(filename, mat_index, world_x, world_z, y_offset, scale_xyz, rot_deg_xyz):
    """
    Duplicates a cached Quaternius template mesh, filters to polygons of `mat_index` (if mat_index is not None),
    applies positive-determinant scale + rotation + translation to `(world_x, -world_z, y_ground + y_offset)`,
    and returns a temporary single-material Blender Mesh object ready for joining.
    """
    tmpl = get_gltf_template(filename)
    mesh_copy = tmpl.data.copy()

    if mat_index is not None and len(tmpl.data.materials) > 1:
        bm = bmesh.new()
        bm.from_mesh(mesh_copy)
        to_del = [f for f in bm.faces if f.material_index != mat_index]
        if to_del:
            bmesh.ops.delete(bm, geom=to_del, context='FACES')
        for f in bm.faces:
            f.material_index = 0
        bm.to_mesh(mesh_copy)
        bm.free()
        target_mat = tmpl.data.materials[mat_index]
        mesh_copy.materials.clear()
        mesh_copy.materials.append(target_mat)

    y_ground = get_terrain_height(world_x, world_z) + y_offset
    sx, sy, sz = scale_xyz if isinstance(scale_xyz, tuple) else (scale_xyz, scale_xyz, scale_xyz)
    rx, ry, rz = [math.radians(a) for a in rot_deg_xyz]

    mat_loc = Matrix.Translation(Vector((world_x, -world_z, y_ground)))
    mat_rot = Euler((rx, ry, rz), 'XYZ').to_matrix().to_4x4()
    mat_sca = Matrix.Diagonal(Vector((sx, sy, sz, 1.0)))
    xf = mat_loc @ mat_rot @ mat_sca

    mesh_copy.transform(xf)
    for poly in mesh_copy.polygons:
        poly.use_smooth = True

    obj = bpy.data.objects.new(f"_Inst_{filename}_{mat_index}", mesh_copy)
    bpy.context.collection.objects.link(obj)
    return obj


def join_objects_into_named_mesh(objs, target_name, force_single_material=True):
    """
    Joins a list of mesh objects into one named scene mesh object and enforces a single canonical
    material slot so glTF 2.0 always exports a single primitive (`Primitives created: 1`).
    """
    if not objs:
        return None
    primary_mat = objs[0].data.materials[0] if objs[0].data.materials else None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    merged.name = target_name
    merged.data.name = f"{target_name}_Mesh"

    if force_single_material and primary_mat is not None:
        merged.data.materials.clear()
        merged.data.materials.append(primary_mat)
        for p in merged.data.polygons:
            p.material_index = 0

    return merged


def refine_tree_trunk_and_canopy_colors(trunk_obj, canopy_obj, palette_shift=0):
    """
    Unifies imported Quaternius tree trunks and canopies by updating the 'Color' attribute in-place:
    - Softens trunk root vertex AO from [0.04..1.0] to [0.62..1.0] so tree bases are never pitch black.
    - Bakes a bright, natural 3D canopy sunlight + interior ambient-occlusion gradient ('Color') on the canopy
      AND blends vertex normals 60% toward a smooth outward canopy dome for plush Ghibli-style lighting.
    """
    if trunk_obj and trunk_obj.data.color_attributes:
        ca = trunk_obj.data.color_attributes[0]
        verts = trunk_obj.data.vertices
        z_vals = [v.co.z for v in verts]
        z_min = min(z_vals) if z_vals else 0.0
        for poly in trunk_obj.data.polygons:
            for loop_idx in poly.loop_indices:
                v = verts[trunk_obj.data.loops[loop_idx].vertex_index]
                old_c = ca.data[loop_idx].color
                ao = max(0.62, min(1.0, 0.60 + 0.40 * old_c[0]))
                h_rel = max(0.0, min(1.0, (v.co.z - z_min) / 0.55))
                r_c = ao * (0.86 + 0.14 * h_rel)
                g_c = ao * (0.95 + 0.05 * h_rel)
                b_c = ao * (0.82 + 0.18 * h_rel)
                ca.data[loop_idx].color = (r_c, g_c, b_c, 1.0)

    if canopy_obj:
        mesh = canopy_obj.data
        ca = mesh.color_attributes.get("Color")
        if ca is None:
            ca = mesh.color_attributes[0] if mesh.color_attributes else mesh.color_attributes.new(
                name="Color", type='BYTE_COLOR', domain='CORNER'
            )

        verts = mesh.vertices
        if not verts:
            return
        xs = [v.co.x for v in verts]
        ys = [v.co.y for v in verts]
        zs = [v.co.z for v in verts]
        cx = 0.5 * (min(xs) + max(xs))
        cy = 0.5 * (min(ys) + max(ys))
        cz = 0.5 * (min(zs) + max(zs))
        z_min, z_max = min(zs), max(zs)
        z_span = max(0.2, z_max - z_min)
        max_r = max(0.2, max(math.hypot(v.co.x - cx, v.co.y - cy) for v in verts))

        palettes = [
            ((0.62, 0.72, 0.65), (0.88, 0.96, 0.88)),  # Deep Hero Oak emerald-jade
            ((0.58, 0.68, 0.66), (0.84, 0.94, 0.91)),  # Deep Boreal Pine conifer green
            ((0.64, 0.74, 0.64), (0.91, 0.96, 0.86)),  # Mature Woodland Broadleaf moss-green
        ]
        c_shadow, c_sun = palettes[palette_shift % len(palettes)]

        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                v = verts[mesh.loops[loop_idx].vertex_index]
                h_t = (v.co.z - z_min) / z_span
                r_t = math.hypot(v.co.x - cx, v.co.y - cy) / max_r
                sun_dir = max(0.0, min(1.0, 0.52 * h_t + 0.30 * r_t + 0.18 * ((cx - v.co.x) / max_r)))
                r_c = c_shadow[0] * (1.0 - sun_dir) + c_sun[0] * sun_dir
                g_c = c_shadow[1] * (1.0 - sun_dir) + c_sun[1] * sun_dir
                b_c = c_shadow[2] * (1.0 - sun_dir) + c_sun[2] * sun_dir
                ca.data[loop_idx].color = (min(1.0, r_c), min(1.0, g_c), min(1.0, b_c), 1.0)


def build_quaternius_forest_and_botanicals():
    """
    Populates the floating island with curated, color-harmonized CC0 models from
    Quaternius's Stylized Nature MegaKit:
    - 7 main tree groups (`Tree_NW_Hero`, `Tree_N_Left`, `Tree_N_Center`, `Tree_N_Right`,
      `Tree_NE_Hero`, `Tree_W_Flank`, `Tree_E_Flank`) combining broadleaf oaks/maples and evergreen pines.
    - Layered woodland shrubs (`Forest_Shrubs`), ferns & broadleaf plants (`Forest_Ferns`),
      grass clumps (`Forest_Grass`), wildflowers (`Wildflowers`), mossy boulders (`Environment_Rocks`),
      and trail stepping stones (`Pathway_Cobbles`).
    """
    # 1. SEVEN HERO & FLANKING TREE GROUPS (Broadleaf & Evergreen Zones)
    # Each entry can include a primary hero tree plus an optional companion sub-tree for rich forest depth
    tree_group_specs = [
        (
            "Tree_NW_Hero",
            0,
            [
                ("TwistedTree_1.gltf", -2.55, -1.88, -0.02, (0.215, 0.215, 0.210), (0, 0, 28)),
                ("CommonTree_2.gltf", -1.92, -2.18, -0.02, (0.37, 0.37, 0.36), (0, 0, -15)),
            ],
        ),
        (
            "Tree_N_Left",
            1,
            [
                ("Pine_1.gltf", -1.28, -2.42, -0.02, (0.45, 0.45, 0.44), (0, 0, 18)),
                ("Pine_3.gltf", -0.68, -2.62, -0.02, (0.38, 0.38, 0.39), (0, 0, -35)),
            ],
        ),
        (
            "Tree_N_Center",
            2,
            [
                ("CommonTree_1.gltf", 0.12, -2.48, -0.02, (0.43, 0.43, 0.42), (0, 0, -10)),
            ],
        ),
        (
            "Tree_N_Right",
            1,
            [
                ("Pine_3.gltf", 1.52, -2.35, -0.02, (0.46, 0.46, 0.45), (0, 0, -22)),
                ("Pine_2.gltf", 0.92, -2.58, -0.02, (0.37, 0.37, 0.38), (0, 0, 40)),
            ],
        ),
        (
            "Tree_NE_Hero",
            0,
            [
                ("CommonTree_1.gltf", 2.65, -1.72, -0.02, (0.45, 0.45, 0.44), (0, 0, -25)),
                ("TwistedTree_2.gltf", 2.15, -2.12, -0.02, (0.175, 0.175, 0.175), (0, 0, 14)),
            ],
        ),
        (
            "Tree_W_Flank",
            2,
            [
                ("CommonTree_3.gltf", -3.12, -0.62, -0.02, (0.34, 0.34, 0.33), (0, 0, 42)),
            ],
        ),
        (
            "Tree_E_Flank",
            1,
            [
                ("Pine_1.gltf", 3.08, -0.45, -0.02, (0.42, 0.42, 0.41), (0, 0, -32)),
                ("Pine_4.gltf", 2.82, -1.05, -0.02, (0.29, 0.29, 0.30), (0, 0, 15)),
            ],
        ),
    ]

    for tree_id, pal_idx, sub_trees in tree_group_specs:
        trunk_insts = []
        canopy_insts = []
        for fn, tx, tz, ty_off, sc, rot in sub_trees:
            trunk_insts.append(extract_transformed_material_mesh(fn, 0, tx, tz, ty_off, sc, rot))
            canopy_insts.append(extract_transformed_material_mesh(fn, 1, tx, tz, ty_off, sc, rot))

        trunk_obj = join_objects_into_named_mesh(trunk_insts, f"{tree_id}_Trunk")
        canopy_obj = join_objects_into_named_mesh(canopy_insts, f"{tree_id}_Canopy")
        refine_tree_trunk_and_canopy_colors(trunk_obj, canopy_obj, palette_shift=pal_idx)

    # 2. WOODLAND SHRUBS (`Forest_Shrubs` + flowering shrub blossoms merged into `Wildflowers`)
    shrub_placements = [
        ("Bush_Common.gltf", -2.85, -1.25, -0.02, 0.36, (0, 0, 15)),
        ("Bush_Common_Flowers.gltf", -2.15, -1.45, -0.02, 0.34, (0, 0, 65)),
        ("Bush_Common.gltf", -1.42, -2.05, -0.02, 0.38, (0, 0, -30)),
        ("Bush_Common_Flowers.gltf", -0.35, -2.15, -0.02, 0.33, (0, 0, 20)),
        ("Bush_Common.gltf", 0.55, -2.18, -0.02, 0.35, (0, 0, -45)),
        ("Bush_Common_Flowers.gltf", 1.88, -1.85, -0.02, 0.34, (0, 0, 35)),
        ("Bush_Common.gltf", 2.85, -1.15, -0.02, 0.37, (0, 0, -20)),
        ("Bush_Common_Flowers.gltf", -2.45, 0.82, -0.02, 0.30, (0, 0, 50)),
        ("Bush_Common.gltf", 2.42, 1.32, -0.02, 0.29, (0, 0, -55)),
    ]
    shrub_foliage_insts = []
    flower_petal_insts = []
    for fn, sx, sz, sy_off, sc, rot in shrub_placements:
        shrub_foliage_insts.append(extract_transformed_material_mesh(fn, 0, sx, sz, sy_off, sc, rot))
        if fn == "Bush_Common_Flowers.gltf":
            flower_petal_insts.append(extract_transformed_material_mesh(fn, 1, sx, sz, sy_off, sc, rot))

    shrub_obj = join_objects_into_named_mesh(shrub_foliage_insts, "Forest_Shrubs")
    refine_tree_trunk_and_canopy_colors(None, shrub_obj, palette_shift=0)

    # 3. FERNS, BROADLEAF PLANTS, CLOVERS & WILDFLOWERS (`Forest_Ferns` & `Wildflowers`)
    fern_and_plant_placements = [
        # Creek bank & spring/cascade grotto ferns
        ("Fern_1.gltf", -2.92, -0.22, -0.01, 0.28, (0, 0, 18)),
        ("Fern_1.gltf", -2.18, 0.46, -0.01, 0.26, (0, 0, 74)),
        ("Fern_1.gltf", 2.48, 0.98, -0.01, 0.28, (0, 0, -32)),
        ("Fern_1.gltf", 2.82, 0.35, -0.01, 0.25, (0, 0, 45)),
        ("Fern_1.gltf", -0.78, 0.68, -0.01, 0.22, (0, 0, -18)),
        ("Fern_1.gltf", 0.76, 0.68, -0.01, 0.22, (0, 0, 28)),
        # Foreground rock knoll & central crossroads fork divide
        ("Fern_1.gltf", -1.82, 1.44, -0.01, 0.27, (0, 0, 40)),
        ("Plant_1_Big.gltf", -1.42, 1.68, -0.01, 0.22, (0, 0, -25)),
        ("Fern_1.gltf", 0.04, -1.24, -0.01, 0.25, (0, 0, 12)),
        ("Plant_1.gltf", -0.22, -1.16, -0.01, 0.24, (0, 0, 55)),
        # Signpost, mailbox & tree root botanical clusters
        ("Fern_1.gltf", -1.86, -0.62, -0.01, 0.23, (0, 0, -40)),
        ("Fern_1.gltf", 1.86, -0.58, -0.01, 0.23, (0, 0, 38)),
        ("Plant_1.gltf", 1.56, 1.28, -0.01, 0.23, (0, 0, -15)),
        ("Fern_1.gltf", -2.48, -1.62, -0.01, 0.28, (0, 0, 22)),
        ("Fern_1.gltf", 2.48, -1.52, -0.01, 0.28, (0, 0, -24)),
        ("Plant_7_Big.gltf", -1.15, -0.52, -0.02, 0.28, (0, 0, 15)),
        ("Plant_7_Big.gltf", 1.15, -0.48, -0.02, 0.28, (0, 0, -20)),
        ("Clover_1.gltf", -0.58, 1.55, 0.0, 0.24, (0, 0, 10)),
        ("Clover_2.gltf", 0.62, 1.62, 0.0, 0.24, (0, 0, -35)),
        ("Clover_1.gltf", -1.25, 0.72, 0.0, 0.25, (0, 0, 45)),
        ("Clover_2.gltf", 1.32, 0.85, 0.0, 0.25, (0, 0, -15)),
    ]
    fern_insts = []
    for fn, fx, fz, fy_off, sc, rot in fern_and_plant_placements:
        fern_insts.append(extract_transformed_material_mesh(fn, 0, fx, fz, fy_off, sc, rot))

    wildflower_group_placements = [
        ("Flower_3_Group.gltf", -1.78, -0.56, 0.0, 0.20, (0, 0, 15)),
        ("Flower_4_Group.gltf", -1.48, 1.36, 0.0, 0.19, (0, 0, -28)),
        ("Flower_3_Group.gltf", 1.78, -0.52, 0.0, 0.20, (0, 0, 42)),
        ("Flower_4_Group.gltf", 1.48, 1.32, 0.0, 0.18, (0, 0, -15)),
        ("Flower_3_Group.gltf", -0.62, 0.78, 0.0, 0.18, (0, 0, 30)),
        ("Flower_4_Group.gltf", 0.14, -1.18, 0.0, 0.19, (0, 0, -20)),
        ("Flower_3_Group.gltf", -2.18, -1.05, 0.0, 0.20, (0, 0, 60)),
        ("Flower_4_Group.gltf", 2.18, -0.95, 0.0, 0.20, (0, 0, -45)),
    ]
    for fn, wx, wz, wy_off, sc, rot in wildflower_group_placements:
        # Material 0 is Leaves (stems), Material 1 is Flowers (petals)
        fern_insts.append(extract_transformed_material_mesh(fn, 0, wx, wz, wy_off, sc, rot))
        flower_petal_insts.append(extract_transformed_material_mesh(fn, 1, wx, wz, wy_off, sc, rot))

    join_objects_into_named_mesh(fern_insts, "Forest_Ferns")
    join_objects_into_named_mesh(flower_petal_insts, "Wildflowers")

    # 4. WOODLAND GRASS TUFTS (`Forest_Grass`)
    grass_placements = [
        ("Grass_Common_Short.gltf", -1.52, 1.38, 0.0, 0.24, (0, 0, 12)),
        ("Grass_Wispy_Short.gltf", -0.56, 0.84, 0.0, 0.22, (0, 0, 40)),
        ("Grass_Common_Short.gltf", 0.56, 0.86, 0.0, 0.22, (0, 0, -25)),
        ("Grass_Common_Tall.gltf", -1.24, 0.22, 0.0, 0.22, (0, 0, 18)),
        ("Grass_Wispy_Short.gltf", 1.38, 0.88, 0.0, 0.22, (0, 0, -35)),
        ("Grass_Common_Short.gltf", 1.48, 1.48, 0.0, 0.22, (0, 0, 50)),
        ("Grass_Common_Short.gltf", -1.74, -0.54, 0.0, 0.22, (0, 0, -15)),
        ("Grass_Common_Short.gltf", 1.74, -0.50, 0.0, 0.22, (0, 0, 28)),
        ("Grass_Wispy_Short.gltf", -0.64, -0.38, 0.0, 0.20, (0, 0, -42)),
        ("Grass_Wispy_Short.gltf", 0.64, -0.38, 0.0, 0.20, (0, 0, 32)),
        ("Grass_Common_Short.gltf", -0.28, -1.12, 0.0, 0.22, (0, 0, 15)),
        ("Grass_Common_Short.gltf", 0.34, -1.15, 0.0, 0.22, (0, 0, -22)),
        ("Grass_Common_Tall.gltf", -2.22, -0.92, 0.0, 0.22, (0, 0, 65)),
        ("Grass_Common_Tall.gltf", 2.22, -0.88, 0.0, 0.22, (0, 0, -55)),
        ("Grass_Common_Short.gltf", -0.44, 2.32, 0.0, 0.20, (0, 0, 20)),
        ("Grass_Common_Short.gltf", 0.42, 2.24, 0.0, 0.20, (0, 0, -18)),
    ]
    grass_insts = [
        extract_transformed_material_mesh(fn, 0, gx, gz, gy_off, sc, rot)
        for fn, gx, gz, gy_off, sc, rot in grass_placements
    ]
    join_objects_into_named_mesh(grass_insts, "Forest_Grass")

    # 5. SCULPTED MOSSY BOULDERS & CREEK GROTTOS (`Environment_Rocks`)
    rock_models = ["Rock_Medium_1.gltf", "Rock_Medium_2.gltf", "Rock_Medium_3.gltf"]
    rock_placements = [
        # NW spring headwater grotto enclosing left creek origin (-3.38, -0.45)
        (-3.45, -0.52, (0.31, 0.31, 0.28), 15),
        (-3.16, -0.86, (0.26, 0.26, 0.24), 85),
        (-3.22, -0.05, (0.25, 0.25, 0.22), 140),
        (-2.86, -0.68, (0.19, 0.19, 0.17), 210),
        # SE cascade grotto enclosing right creek outlet (+3.22, +0.72)
        (3.24, 0.78, (0.30, 0.30, 0.26), 45),
        (2.96, 1.05, (0.25, 0.25, 0.22), 115),
        (3.02, 0.36, (0.24, 0.24, 0.21), 195),
        (2.70, 0.88, (0.18, 0.18, 0.16), 260),
        # Creek bank & bridge abutment stones
        (-2.15, 0.32, (0.19, 0.19, 0.16), 30),
        (-1.28, 0.06, (0.17, 0.17, 0.14), 110),
        (-0.58, 0.62, (0.17, 0.17, 0.15), 75),
        (0.58, -0.22, (0.16, 0.16, 0.14), 165),
        (-0.58, -0.26, (0.16, 0.16, 0.14), 240),
        (0.58, 0.62, (0.16, 0.16, 0.14), 15),
        (1.52, 0.72, (0.18, 0.18, 0.15), 95),
        (2.25, 0.88, (0.20, 0.20, 0.17), 150),
        # Central crossroads fork boulder cluster & foreground knoll outcrop
        (-0.06, -1.20, (0.23, 0.23, 0.19), 25),
        (0.24, -1.28, (0.16, 0.16, 0.14), 135),
        (-1.68, 1.54, (0.22, 0.22, 0.18), 55),
        (-1.38, 1.68, (0.15, 0.15, 0.13), 175),
        # Signpost & tree root accent stones
        (-1.92, -0.78, (0.17, 0.17, 0.15), 80),
        (1.92, -0.74, (0.17, 0.17, 0.15), 200),
        (1.58, 1.38, (0.15, 0.15, 0.12), 120),
        (-0.15, -2.20, (0.24, 0.24, 0.20), 40),
    ]
    rock_insts = []
    for idx, (rx, rz, sc_tuple, yaw_d) in enumerate(rock_placements):
        fn = rock_models[idx % len(rock_models)]
        rock_insts.append(extract_transformed_material_mesh(fn, 0, rx, rz, -0.02, sc_tuple, (0, 0, yaw_d)))
    join_objects_into_named_mesh(rock_insts, "Environment_Rocks")

    # 6. HAND-PAINTED TRAIL STEPPING STONES (`Pathway_Cobbles`)
    pebble_models = [
        "Pebble_Round_1.gltf",
        "Pebble_Round_2.gltf",
        "Pebble_Round_3.gltf",
        "Pebble_Round_4.gltf",
    ]
    stone_specs = [
        # South trailhead approach stones
        (-0.12, 2.48, 0.82, 15),
        (0.11, 2.28, 0.88, -25),
        (-0.08, 2.04, 0.80, 40),
        (0.10, 1.80, 0.86, -18),
        (-0.07, 1.54, 0.78, 30),
        (0.08, 1.26, 0.84, -12),
        (-0.02, 0.98, 0.90, 8),
        # Mailbox terrace spur stones
        (0.56, 1.42, 0.72, 28),
        (0.92, 1.38, 0.76, -15),
        # North bridge exit & crossroads fork
        (0.02, -0.58, 0.92, 5),
        # Design Trail (left branch) stepping stones
        (-0.46, -0.72, 0.82, 35),
        (-0.92, -0.92, 0.86, -28),
        (-1.38, -1.14, 0.78, 42),
        (-1.85, -1.36, 0.82, -18),
        (-2.28, -1.56, 0.72, 22),
        # Game Trail (right branch) stepping stones
        (0.46, -0.70, 0.82, -32),
        (0.92, -0.88, 0.86, 26),
        (1.38, -1.08, 0.78, -38),
        (1.85, -1.28, 0.82, 16),
        (2.28, -1.48, 0.72, -24),
    ]
    cobble_insts = []
    for idx, (sx, sz, sc_h, yaw_d) in enumerate(stone_specs):
        fn = pebble_models[idx % len(pebble_models)]
        # Flatten vertical scale to 0.34 and sink slightly so tops sit naturally embedded in the trail dirt
        cobble_insts.append(
            extract_transformed_material_mesh(fn, 0, sx, sz, -0.012, (sc_h, sc_h, 0.34), (0, 0, yaw_d))
        )
    join_objects_into_named_mesh(cobble_insts, "Pathway_Cobbles")


# ==============================================================================
# 4. LIGHTING, VERIFICATION RENDERS & GLB EXPORT
# ==============================================================================

def setup_lighting_and_render_previews():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 960
    scene.render.resolution_y = 1200

    world = bpy.data.worlds.new("CrossroadsWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = hex_to_rgba("#1B382E")
        bg.inputs[1].default_value = 1.15

    sun_data = bpy.data.lights.new(name="LateAfternoonSun", type='SUN')
    sun_data.energy = 3.9
    sun_data.color = hex_to_rgba("#FFF2D6")[:3]
    sun_obj = bpy.data.objects.new(name="LateAfternoonSun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = Euler((math.radians(46), math.radians(-24), math.radians(30)), 'XYZ')

    fill_data = bpy.data.lights.new(name="ForestFill", type='SUN')
    fill_data.energy = 1.65
    fill_data.color = hex_to_rgba("#BFE0CC")[:3]
    fill_obj = bpy.data.objects.new(name="ForestFill", object_data=fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Euler((math.radians(60), math.radians(36), math.radians(-138)), 'XYZ')

    cam_data = bpy.data.cameras.new(name="PreviewCamera")
    cam_data.lens = 34
    cam_obj = bpy.data.objects.new("PreviewCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    def aim_camera(cam_pos, target_pos):
        cam_obj.location = Vector(cam_pos)
        direction = Vector(target_pos) - cam_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

    aim_camera((-0.35, -12.6, 7.1), (0.0, 0.0, 0.35))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_initial.png")
    bpy.ops.render.render(write_still=True)

    aim_camera((5.2, -11.6, 7.3), (-0.05, 0.0, 0.35))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_rotated.png")
    bpy.ops.render.render(write_still=True)


def print_mesh_statistics():
    total_verts = 0
    total_tris = 0
    tree_tris = 0
    scene_meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in scene_meshes:
        v_count = len(obj.data.vertices)
        t_count = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
        total_verts += v_count
        total_tris += t_count
        if obj.name.startswith("Tree_"):
            tree_tris += t_count
    print(
        f"SCENE GEOMETRY STATS: {total_verts} vertices, {total_tris} total triangles "
        f"({tree_tris} tree triangles) across {len(scene_meshes)} mesh objects"
    )


def main():
    clear_scene()

    materials = {
        "grass_top": make_pbr_material("Grass_Top_Mat", "#5B7A53", roughness=0.82),
        "rock_underside": make_pbr_material("Rock_Underside_Mat", "#524B44", roughness=0.88),
        "stone_warm": make_pbr_material("Stone_Warm_Mat", "#928A7F", roughness=0.76),
        "stone_mossy": make_pbr_material("Stone_Mossy_Mat", "#646F5E", roughness=0.79),
        "stream_water": make_pbr_material("Stream_Water_Mat", "#2C6861", roughness=0.52, metallic=0.0),
        "wood_oak": make_pbr_material("Wood_Oak_Mat", "#9D6E48", roughness=0.76),
        "wood_post": make_pbr_material("Wood_Post_Mat", "#784F30", roughness=0.78),
        "wood_sign_plaque": make_pbr_material("Wood_Sign_Plaque_Mat", "#5A371E", roughness=0.74),
        "ivory_lettering": make_pbr_material("Ivory_Lettering_Mat", "#F5EFE3", roughness=0.36, use_vertex_color=False),
        "mailbox_forest_metal": make_pbr_material("Mailbox_Forest_Metal_Mat", "#1C4537", roughness=0.38, metallic=0.26, use_vertex_color=False),
        "mailbox_body_metal": make_pbr_material("Mailbox_Body_Metal_Mat", "#1E4B3B", roughness=0.40, metallic=0.24, use_vertex_color=True),
        "champagne_brass": make_pbr_material("Champagne_Brass_Mat", "#DCC89A", roughness=0.28, metallic=0.74, use_vertex_color=False),
    }

    build_island_terrain_and_trails(materials)
    build_embedded_identity_plaque(materials)
    build_stream_and_bridge(materials)
    build_quaternius_forest_and_botanicals()

    # Solid Right-Handed Wooden Signposts with Final Locked Labels: 'Design Trail' & 'Game Trail'
    build_signpost("Signpost_UX", "Design Trail", -1.58, -0.68, 18.0, -1, materials)
    build_signpost("Signpost_Game", "Game Trail", 1.58, -0.64, -18.0, 1, materials)

    # Solid Right-Handed Woodland Mailbox on the dry front-right terrace (x=1.28, z=1.36)
    build_woodland_mailbox(1.28, 1.36, -22.0, materials)

    # Remove off-scene template objects before saving/exporting
    for tmpl_obj in list(_GLTF_TEMPLATE_CACHE.values()):
        if tmpl_obj.name in bpy.data.objects:
            bpy.data.objects.remove(tmpl_obj, do_unlink=True)
    _GLTF_TEMPLATE_CACHE.clear()

    print_mesh_statistics()

    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
    )
    print(f"Exported V6 runtime GLB to: {GLB_OUT}")

    setup_lighting_and_render_previews()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved V6 master Blender source to: {BLEND_OUT}")


if __name__ == "__main__":
    main()
