"""
Blender 5.0 High-Fidelity Stylized Environment Authoring Script
(V5 Unified 3D Environment & Interaction Refinement)
Project: The Crossroads — Two Paths, One Designer (Evelyn Lin)

V5 Root-Cause Engineering & Art Upgrades:
1. STAGE 1 — High-Fidelity Tree Reconstruction:
   - Replaced voxel-smoothed marshmallow blobs and stacked conifer rings with a 3-tier botanical
     hierarchy: root-flared grooved trunks -> primary/secondary/tertiary branching -> faceted inner
     shadow cores, chiseled medium foliage pads, and hundreds of outer 3D individual leaf-fan sprays
     (Tree A: Gnarled Broadleaf Oak, Tree B: Slender Multi-Stem Birch, Tree C: Fibonacci-Spiral
     Drape-Bough Evergreen Spruce).
2. STAGE 2 — Wooden Signpost Geometry Repair & Final Locked Naming:
   - Eliminated overlapping trim boxes, penetrating post straps, and non-planar beveled cubes.
   - Built solid, watertight, manifold multi-segment directional oak signboards connected via rear-only
     wrought-iron mortise brackets, displaying final locked labels: 'Design Trail' (left) and 'Game Trail' (right).
3. STAGE 3 & 5 — Unified Terrain, Trail Naturalization & Watertight Island Rim:
   - Stitched Island_Rock_Underside top ring to the exact 3D vertex coordinates of Island_Terrain_Top's
     outer perimeter ring (eliminating all rim gaps, detached slivers, and rock bleed-through).
   - Integrated the woodland trails directly into the high-resolution unified terrain surface (112 rings x 224 segs)
     with organic noise-feathered dirt/moss/grass vertex splatting, natural trailhead flagstones above the
     front plaque, deeply embedded stepping stones, and a central mossy boulder fork dividing Design Trail & Game Trail.
4. STAGE 4 — Creek & Bridge Integration:
   - Widened the creek pool around and under the bridge, enclosed both stream ends inside sculpted spring/cascade
     boulder grottos (no cut water edges), and aligned the 13-plank arched oak bridge flush with stone-and-earth
     approach ramps.
5. STAGE 5 & 6 — Mailbox Dry-Terrace Placement, Purposeful Botanicals & Embedded 3D Identity Plaque.
"""

import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Euler, Matrix, noise

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND_OUT = os.path.join(ROOT_DIR, "assets", "source", "crossroads_master.blend")
GLB_OUT = os.path.join(ROOT_DIR, "public", "models", "crossroads_environment.glb")
RENDER_DIR = os.path.join(ROOT_DIR, "assets", "renders")

os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

random.seed(205)


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


def make_pbr_material(name, hex_color, roughness=0.72, metallic=0.0, use_vertex_color=True):
    mat = bpy.data.materials.new(name=name)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(hex_color)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.28
        if use_vertex_color:
            vc_node = nodes.new(type="ShaderNodeVertexColor")
            vc_node.layer_name = "Col"
            links.new(vc_node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def finalize_mesh_object(name, bm, material, color_fn=None):
    """Converts a BMesh to a smooth-shaded Blender object with optional per-vertex color attribute 'Col'."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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


def add_beveled_box(bm, transform_fn, bevel_offset=0.010, segments=2):
    ret = bmesh.ops.create_cube(bm, size=1.0)
    verts = ret["verts"]
    for v in verts:
        v.co = transform_fn(v.co)
    edges = list({e for v in verts for e in v.link_edges if all(ev in verts for ev in e.verts)})
    if bevel_offset > 0:
        bmesh.ops.bevel(
            bm,
            geom=verts + edges,
            offset=bevel_offset,
            segments=segments,
            affect='EDGES',
            clamp_overlap=True,
        )


# ==============================================================================
# SPATIAL & TERRAIN FUNCTIONS (Unified Trail, Widened Creek & Sculpted Relief)
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
    Design Trail (left), Game Trail (right), and Mailbox spur directly into the terrain!
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

    # 1. South trailhead approach: curves gently from trailhead terrace (0.04, 2.52) to south bridge ramp (0.0, 0.78)
    sx_curve = x - 0.07 * math.sin((z - 0.78) * 1.8)
    d_south, t_south = seg_dist_and_t(sx_curve, z, 0.0, 2.58, 0.0, 0.72)
    w_south = 0.44 * (0.75 + 0.25 * math.sin(t_south * math.pi))
    # Feather smoothly at the front trailhead origin so there is NO blunt pointed tip
    south_origin_fade = min(1.0, max(0.0, (2.72 - z) / 0.45))

    # 2. North bridge exit to central crossroads fork (0.0, -0.45) to (0.0, -0.68)
    d_north, _ = seg_dist_and_t(x, z, 0.0, -0.42, 0.0, -0.68)
    w_north = 0.48

    # 3. Left Branch (Design Trail): curves northwest past Design Trail sign (-1.58, -0.72) to (-2.65, -1.72)
    lx_curve = x + 0.12 * math.sin((z + 0.65) * 2.4)
    d_left, t_left = seg_dist_and_t(lx_curve, z, -0.08, -0.62, -2.55, -1.68)
    w_left = 0.43 * (1.0 - 0.28 * t_left)
    left_end_fade = 1.0 - 0.75 * (max(0.0, (t_left - 0.78) / 0.22) ** 1.6)

    # 4. Right Branch (Game Trail): curves northeast past Game Trail sign (+1.58, -0.68) to (+2.65, -1.62)
    rx_curve = x - 0.12 * math.sin((z + 0.65) * 2.4)
    d_right, t_right = seg_dist_and_t(rx_curve, z, 0.08, -0.62, 2.55, -1.60)
    w_right = 0.43 * (1.0 - 0.28 * t_right)
    right_end_fade = 1.0 - 0.75 * (max(0.0, (t_right - 0.78) / 0.22) ** 1.6)

    # 5. Mailbox dry-terrace spur from (0.05, 1.48) to mailbox footing (1.26, 1.36)
    d_spur, t_spur = seg_dist_and_t(x, z, 0.08, 1.48, 1.26, 1.36)
    w_spur = 0.32 * (0.85 + 0.25 * t_spur)

    # Organic edge irregularity noise so trail borders are never straight geometric lines
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

    # Suppress trail dirt inside the creek water channel itself
    sz = stream_center_z(x)
    hw = stream_half_width(x)
    in_creek = math.exp(-((abs(z - sz) / (hw * 0.92)) ** 3.2))
    return wt * (1.0 - in_creek)


def get_terrain_height(x, z):
    """
    V5 Sculpted Landscape Heightmap:
    - Elevated NW and NE background forest hills
    - Intentional foreground relief (front-left mossy knoll, front-right mailbox dry terrace,
      and subtle trailhead terrace above the front plaque)
    - Smoothly carved creek channel enclosed inside spring/cascade basins at both ends
    - Integrated earth-and-stone bridge approach ramps at x=0, z=sz ± 0.70
    - Subtle natural trail compaction (0.018 units) instead of a deep artificial trench
    """
    rf = island_radial_factor(x, z)

    # Background & flanking hills
    nw_hill = 0.56 * math.exp(-((x + 2.45) ** 2 / 3.2 + (z + 1.95) ** 2 / 2.6))
    ne_hill = 0.48 * math.exp(-((x - 2.35) ** 2 / 3.0 + (z + 1.85) ** 2 / 2.5))
    north_ridge = 0.35 * math.exp(-((x + 0.20) ** 2 / 5.5 + (z + 2.55) ** 2 / 2.2))

    # Central fork mound between Design Trail and Game Trail so the two paths visibly diverge around higher ground
    fork_divide_mound = 0.12 * math.exp(-((x ** 2) / 0.55 + ((z + 1.25) ** 2) / 0.55))

    # Intentional foreground sculpting (eliminates empty flat front patch)
    fg_left_knoll = 0.25 * math.exp(-((x + 1.65) ** 2 / 1.80 + (z - 1.52) ** 2 / 1.30))
    fg_left_west = 0.18 * math.exp(-((x + 2.85) ** 2 / 1.55 + (z - 0.85) ** 2 / 1.35))
    fg_right_terrace = 0.23 * math.exp(-((x - 1.48) ** 2 / 1.90 + (z - 1.42) ** 2 / 1.35))

    # Multi-octave organic terrain undulation
    n1 = noise.noise(Vector((x * 0.46 + 4.2, z * 0.46 - 2.8, 1.1))) * 0.10
    n2 = noise.noise(Vector((x * 1.15 - 1.9, z * 1.15 + 3.4, 2.7))) * 0.038

    # Creek channel carving with clear bank shoulders and smooth rim enclosure
    sz = stream_center_z(x)
    hw = stream_half_width(x)
    d_stream = abs(z - sz)
    rim_atten = 1.0 if rf < 0.72 else max(0.15, 1.0 - ((rf - 0.72) / 0.28) ** 1.45)
    stream_cut = 0.50 * math.exp(-((d_stream / (hw * 1.15)) ** 2.3)) * rim_atten
    bank_shoulder = 0.082 * math.exp(-(((d_stream - hw * 1.28) / 0.28) ** 2)) * rim_atten

    # Bridge approach earth ramps at x=0, z=sz ± 0.70 so trail meets bridge deck seamlessly
    abutment_south = 0.14 * math.exp(-((x ** 2) / 0.36 + ((z - (sz + 0.70)) ** 2) / 0.18))
    abutment_north = 0.14 * math.exp(-((x ** 2) / 0.36 + ((z - (sz - 0.70)) ** 2) / 0.18))

    # Gentle natural trail wear compaction (only 0.022 units deep, never a harsh trench!)
    tw = trail_wear_weight(x, z)
    trail_compaction = 0.022 * tw

    # Smooth, well-supported outer turf rim roll-off
    edge_roll = 0.0
    if rf > 0.78:
        t = min(1.05, (rf - 0.78) / 0.22)
        ang = math.atan2(z, x)
        cliff_var = 0.92 + 0.12 * math.sin(ang * 3.0 + 0.5)
        edge_roll = -0.28 * (t ** 1.95) * cliff_var

    return (
        0.21
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
        - trail_compaction
        + edge_roll
    )


# ==============================================================================
# 1. WATERTIGHT UNIFIED ISLAND TERRAIN, NATURALIZED TRAILS & EMBEDDED STEPPING STONES
# ==============================================================================

def build_island_terrain_and_trails(materials):
    """
    Builds a high-density unified upper terrain mesh (112 rings x 224 segments = 25,088 vertices)
    with the woodland trails organically vertex-splatted directly into the continuous surface,
    and stitches Island_Rock_Underside's top ring to the EXACT outer perimeter vertices of
    Island_Terrain_Top so there are ZERO rim gaps or rock bleed-through slivers!
    """
    bm_top = bmesh.new()
    rings = 112
    segs = 224

    center_y = get_terrain_height(0.0, 0.0)
    center_vert = bm_top.verts.new((0.0, 0.0, center_y))

    ring_verts = []
    outer_rim_coords = []

    for ir in range(1, rings + 1):
        u = ir / rings
        r_frac = math.sin(u * math.pi * 0.5) if u > 0.72 else u * (math.sin(0.72 * math.pi * 0.5) / 0.72)
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            wx = rim_x * r_frac
            wz = rim_z * r_frac
            wy = get_terrain_height(wx, wz)

            if ir >= rings - 3:
                lip_t = (ir - (rings - 3)) / 3.0
                drape_noise = noise.noise(Vector((wx * 0.85, wz * 0.85, 0.5)))
                drape_depth = 0.085 * (0.85 + 0.30 * drape_noise)
                wy -= drape_depth * (lip_t ** 1.45)

            v = bm_top.verts.new((wx, -wz, wy))
            row.append(v)
            if ir == rings:
                outer_rim_coords.append((wx, wz, wy))
        ring_verts.append(row)

    first_ring = ring_verts[0]
    for iseg in range(segs):
        nseg = (iseg + 1) % segs
        bm_top.faces.new((center_vert, first_ring[iseg], first_ring[nseg]))

    for ir in range(len(ring_verts) - 1):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm_top.faces.new((
                ring_verts[ir][iseg],
                ring_verts[ir][nseg],
                ring_verts[ir + 1][nseg],
                ring_verts[ir + 1][iseg],
            ))

    # Multi-layered vertex color terrain & trail splatting
    c_moss_bank = hex_to_rgba("#2D5337")
    c_grass_mid = hex_to_rgba("#55764E")
    c_grass_sun = hex_to_rgba("#7B9B67")
    c_trail_center = hex_to_rgba("#BA9C73")
    c_trail_edge = hex_to_rgba("#876E4E")
    c_earth_rim = hex_to_rgba("#6E533B")

    def terrain_color_fn(wx, wy, wz, nx, ny, nz):
        sz = stream_center_z(wx)
        hw = stream_half_width(wx)
        d_stream = abs(wz - sz)
        rf = island_radial_factor(wx, wz)
        n_c = noise.noise(Vector((wx * 0.85 + 1.3, wz * 0.85 - 2.1, wy)))
        n_fine = noise.noise(Vector((wx * 3.4 - 0.7, wz * 3.4 + 1.8, wy * 2.0)))

        # 1. Base meadow grass to sunlit ridge grass
        h_factor = max(0.0, min(1.0, (wy - 0.15) / 0.52 + 0.24 * n_c))
        col = lerp_color(c_grass_mid, c_grass_sun, h_factor)

        # 2. Lush dark moss & damp bank soil along the sculpted creek channel
        bank_zone = math.exp(-((d_stream / (hw * 1.38)) ** 2.2))
        col = lerp_color(col, c_moss_bank, bank_zone * 0.82)

        # 3. Naturalized Woodland Trail splatting with irregular grass encroachment & pebble mottling
        tw = trail_wear_weight(wx, wz)
        if tw > 0.01:
            # Grass encroachment patches along the trail margins
            encroach = max(0.0, min(1.0, tw + 0.18 * n_fine * (1.0 - tw)))
            trail_tone = lerp_color(c_trail_edge, c_trail_center, min(1.0, (tw ** 0.85) + 0.14 * n_fine))
            col = lerp_color(col, trail_tone, encroach * 0.94)

        # 4. Outer turf lip transition to warm earth
        if rf > 0.90:
            rim_t = min(1.0, (rf - 0.90) / 0.10)
            col = lerp_color(col, c_earth_rim, rim_t * 0.65)
        return col

    finalize_mesh_object("Island_Terrain_Top", bm_top, materials["grass_top"], terrain_color_fn)

    # Watertight Stitched Sculpted Rock & Earth Underside
    # Notice: ir == 0 uses the EXACT outer_rim_coords from Island_Terrain_Top so zero gap or bleed can occur!
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

            # Strictly <= 0.992 on ring 1..N so the rock underside never pokes outside the stitched top turf lip!
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
                radial_disp *= 0.35  # Prevent outward bulge past the grass lip
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
        # Strictly tucked deep underneath the cliff overhang (r_mult <= 0.86, y_off <= -0.46)
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

    # Front-center sculpted stone mantle housing the embedded 3D Identity Plaque at (0.0, -0.34, 3.38)
    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.38
    plaque_pitch = math.radians(-22.0)

    def plaque_to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    add_beveled_box(
        bm_outcrops,
        lambda co: plaque_to_world(co.x * 2.84, co.z * 0.78, -0.04 + co.y * 0.28),
        bevel_offset=0.016,
        segments=2,
    )

    finalize_mesh_object("Island_Soil_Rim", bm_outcrops, materials["rock_underside"], rock_color_fn)

    # Deeply Embedded Flat Sandstone Stepping Stones & Fine Trailside Gravel Pebbles
    bm_stones = bmesh.new()
    stone_specs = [
        # Trailhead flagstones above the front plaque (gradual origin)
        (-0.14, 2.52, 0.19, 0.13, 0.15), (0.12, 2.34, 0.22, 0.15, -0.22),
        (-0.08, 2.08, 0.18, 0.13, 0.08), (0.11, 1.82, 0.20, 0.14, -0.18),
        (-0.07, 1.54, 0.17, 0.12, 0.24), (0.08, 1.24, 0.19, 0.13, -0.12),
        (-0.03, 0.96, 0.21, 0.14, 0.05),
        # Mailbox dry-terrace flagstones at (1.28, 1.36)
        (0.58, 1.42, 0.15, 0.12, 0.30), (0.94, 1.38, 0.17, 0.13, -0.15),
        (1.28, 1.36, 0.28, 0.24, 0.10),
        # North bridge exit & crossroads fork
        (0.02, -0.58, 0.22, 0.16, 0.04),
        # Left route (Design Trail) embedded stones
        (-0.46, -0.72, 0.18, 0.13, 0.35), (-0.92, -0.92, 0.20, 0.14, -0.28),
        (-1.38, -1.14, 0.17, 0.12, 0.42), (-1.85, -1.36, 0.19, 0.13, -0.18),
        (-2.28, -1.56, 0.15, 0.11, 0.22),
        # Right route (Game Trail) embedded stones
        (0.46, -0.70, 0.18, 0.13, -0.32), (0.92, -0.88, 0.20, 0.14, 0.26),
        (1.38, -1.08, 0.17, 0.12, -0.38), (1.85, -1.28, 0.19, 0.13, 0.16),
        (2.28, -1.48, 0.15, 0.11, -0.24),
        # Small trail-margin gravel pebbles
        (-0.34, 2.22, 0.07, 0.06, 0.1), (0.32, 1.96, 0.08, 0.06, 0.5),
        (-0.32, 1.38, 0.07, 0.05, -0.4), (0.34, 1.12, 0.06, 0.05, 0.2),
        (-0.68, -0.58, 0.08, 0.06, 0.3), (0.68, -0.56, 0.08, 0.06, -0.3),
    ]
    for idx, (sx, sz, rx_s, rz_s, yaw_off) in enumerate(stone_specs):
        # Deeply embedded into the trail surface: top protrudes only ~0.012 units!
        sy = get_terrain_height(sx, sz) + 0.002
        ret = bmesh.ops.create_icosphere(bm_stones, subdivisions=3, radius=1.0)
        yaw = yaw_off + (idx * 0.65)
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.5 + sx, p.y * 2.5 + sz, p.z * 2.5)))
            lx = p.x * rx_s * (1.0 + 0.15 * n)
            lz = p.y * rz_s * (1.0 + 0.15 * n)
            wx = sx + lx * math.cos(yaw) - lz * math.sin(yaw)
            wz = sz + lx * math.sin(yaw) + lz * math.cos(yaw)
            # Flattened upper walking face, embedded lower root
            z_flat = p.z * 0.014 if p.z > 0 else p.z * 0.045
            wy = get_terrain_height(wx, wz) + 0.003 + z_flat
            v.co = Vector((wx, -wz, wy))

    c_stone_light = hex_to_rgba("#9D9486")
    c_stone_dark = hex_to_rgba("#6A635A")
    finalize_mesh_object(
        "Pathway_Cobbles",
        bm_stones,
        materials["stone_warm"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_stone_dark, c_stone_light, 0.48 + 0.38 * ny + 0.18 * noise.noise(Vector((wx * 3.2, wz * 3.2, wy)))
        ),
    )


def build_embedded_identity_plaque(materials):
    """
    Physically embeds Evelyn Lin's 3D Identity Plaque into the front cliff mantle of the floating island.
    """
    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.38
    plaque_pitch = math.radians(-22.0)

    def to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    bm_frame = bmesh.new()
    add_beveled_box(
        bm_frame,
        lambda co: to_world(co.x * 2.66, co.z * 0.68, 0.09 + co.y * 0.10),
        bevel_offset=0.010,
        segments=2,
    )
    for rx_s in (-1.20, 1.20):
        for ry_s in (-0.23, 0.23):
            add_beveled_box(
                bm_frame,
                lambda co, rxs=rx_s, rys=ry_s: to_world(
                    rxs + co.x * 0.042,
                    rys + co.z * 0.042,
                    0.152 + co.y * 0.025,
                ),
                bevel_offset=0.004,
                segments=2,
            )
    finalize_mesh_object("Identity_Plaque_Frame", bm_frame, materials["champagne_brass"])

    bm_plate = bmesh.new()
    add_beveled_box(
        bm_plate,
        lambda co: to_world(co.x * 2.52, co.z * 0.56, 0.112 + co.y * 0.08),
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
    name_obj.data.bevel_resolution = 2
    bpy.ops.object.convert(target='MESH')
    for v in name_obj.data.vertices:
        v.co = to_world(v.co.x, 0.075 + v.co.y, 0.156 + v.co.z)
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
    title_obj.data.space_character = 1.10
    title_obj.data.extrude = 0.014
    title_obj.data.bevel_depth = 0.0014
    title_obj.data.bevel_resolution = 1
    bpy.ops.object.convert(target='MESH')
    for v in title_obj.data.vertices:
        v.co = to_world(v.co.x, -0.138 + v.co.y, 0.154 + v.co.z)
    title_obj.data.materials.append(materials["champagne_brass"])
    for poly in title_obj.data.polygons:
        poly.use_smooth = True


# ==============================================================================
# 2. STAGE 1 — HIGH-FIDELITY TREE RECONSTRUCTION (MULTI-SCALE FOLIAGE & LEAF SPRAYS)
# ==============================================================================

def add_curved_branch_tube(bm, points_xyz_rad, segs=12, bark_groove_amp=0.04, is_trunk=False):
    rows = []
    n_pts = len(points_xyz_rad)
    for idx, (px, py, pz, rad) in enumerate(points_xyz_rad):
        t = idx / max(1, n_pts - 1)
        if idx < n_pts - 1:
            tx = points_xyz_rad[idx + 1][0] - px
            ty = points_xyz_rad[idx + 1][1] - py
            tz = points_xyz_rad[idx + 1][2] - pz
        else:
            tx = px - points_xyz_rad[idx - 1][0]
            ty = py - points_xyz_rad[idx - 1][1]
            tz = pz - points_xyz_rad[idx - 1][2]
        tangent = Vector((tx, ty, tz)).normalized()
        up_ref = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
        binorm = tangent.cross(up_ref).normalized()
        norm_v = binorm.cross(tangent).normalized()

        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            flair = 1.0 + (0.42 * max(0.0, 1.0 - t * 3.4) * math.cos(ang * 5.0 + px)) if is_trunk else 1.0
            groove = 1.0 + bark_groove_amp * math.sin(ang * 7.0 + t * 6.0)
            r_eff = rad * flair * groove
            offset = (binorm * math.cos(ang) + norm_v * math.sin(ang)) * r_eff
            wx = px + offset.x
            wy = py + offset.y
            wz = pz + offset.z
            row.append(bm.verts.new((wx, -wz, wy)))
        rows.append(row)

    for r in range(len(rows) - 1):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm.faces.new((rows[r][iseg], rows[r][nseg], rows[r + 1][nseg], rows[r + 1][iseg]))

    # Cap branch tip
    if len(rows) > 0:
        tip_px, tip_py, tip_pz, _ = points_xyz_rad[-1]
        tip_v = bm.verts.new((tip_px, -tip_pz, tip_py))
        last_row = rows[-1]
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm.faces.new((last_row[iseg], last_row[nseg], tip_v))


def add_sculpted_leaf_mass_with_sprays(
    bm, cx, cy, cz, rx, ry, rz, yaw, pitch, seed_val, num_leaf_fans=16, leaf_scale=0.16
):
    """
    Constructs a multi-scale botanical foliage bough using:
    1. A sculpted, multi-faceted inner foliage core volume
    2. Medium-scale overlapping leaf-clump sub-volumes
    3. Outer dimensional 3D leaf-spray tufts (manifold 3D teardrop leaf bundles oriented along growth directions,
       eliminating paper-thin flat triangles and harsh backface shadows while preserving rich leaf silhouettes!)
    """
    ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    cy_cos, cy_sin = math.cos(yaw), math.sin(yaw)
    cp_cos, cp_sin = math.cos(pitch), math.sin(pitch)

    def local_to_world(lx, ly, lz):
        ly_p = ly * cp_cos - lz * cp_sin
        lz_p = ly * cp_sin + lz * cp_cos
        wx = cx + lx * cy_cos + lz_p * cy_sin
        wz = cz - lx * cy_sin + lz_p * cy_cos
        wy = cy + ly_p
        return Vector((wx, -wz, wy))

    for v in ret["verts"]:
        p = v.co
        n1 = noise.noise(Vector((p.x * 2.0 + seed_val, p.y * 2.0 - seed_val, p.z * 2.0)))
        n2 = noise.noise(Vector((p.x * 4.2 - seed_val, p.y * 4.2 + seed_val, p.z * 4.2)))
        chisel = 1.0 + 0.20 * n1 + 0.10 * abs(n2) - 0.08 * abs(p.x * p.y)
        y_shape = 1.05 if p.z >= 0 else 0.60
        v.co = local_to_world(p.x * rx * chisel, p.z * ry * chisel * y_shape, p.y * rz * chisel)

    # Generate dimensional 3D leaf-spray tufts around the crown and perimeter
    golden_angle = 2.39996323
    for ifan in range(num_leaf_fans):
        t_h = -0.18 + 1.12 * (ifan / max(1, num_leaf_fans - 1))
        lat = math.asin(max(-0.80, min(0.96, t_h)))
        lon = ifan * golden_angle + seed_val * 1.3
        dir_x = math.cos(lat) * math.cos(lon)
        dir_z = math.cos(lat) * math.sin(lon)
        dir_y = math.sin(lat)

        anchor_lx = dir_x * rx * 0.78
        anchor_ly = dir_y * ry * (0.84 if dir_y >= 0 else 0.52)
        anchor_lz = dir_z * rz * 0.78

        # Create a smooth 3D sculpted leaf-cluster dome/spray (subdivisions=2 for smooth organic curves)
        ret_tuft = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        tx_d, tz_d = -math.sin(lon), math.cos(lon)
        tuft_len = leaf_scale * (1.05 + 0.25 * ((ifan % 3) * 0.5))
        tuft_wid = tuft_len * 0.82
        tuft_thick = tuft_len * 0.44

        for vt in ret_tuft["verts"]:
            pt = vt.co
            n_t = noise.noise(Vector((pt.x * 2.2 + ifan, pt.y * 2.2 - ifan, pt.z * 2.2)))
            forward = pt.x * 0.5 + 0.25
            fan_spread = (1.0 + 0.22 * forward) * (1.0 + 0.12 * n_t)
            arch_droop = -0.14 * (max(0.0, forward) ** 1.8) * tuft_len
            lx_t = (
                anchor_lx
                + dir_x * (forward * tuft_len)
                + tx_d * (pt.y * tuft_wid * fan_spread)
            )
            lz_t = (
                anchor_lz
                + dir_z * (forward * tuft_len)
                + tz_d * (pt.y * tuft_wid * fan_spread)
            )
            ly_t = (
                anchor_ly
                + dir_y * (forward * tuft_len * 0.60)
                + pt.z * tuft_thick * (1.08 if pt.z >= 0 else 0.65)
                + arch_droop
            )
            vt.co = local_to_world(lx_t, ly_t, lz_t)


def make_foliage_color_fn(tree_x, tree_y_base, tree_z, palette_mode):
    if palette_mode == 0:  # Rich Broadleaf Oak
        c_shadow = hex_to_rgba("#133024")
        c_mid = hex_to_rgba("#356343")
        c_sun = hex_to_rgba("#82A86A")
    elif palette_mode == 1:  # Sunlit Woodland Birch
        c_shadow = hex_to_rgba("#224230")
        c_mid = hex_to_rgba("#4F764A")
        c_sun = hex_to_rgba("#9CB876")
    else:  # Deep Alpine Evergreen Spruce
        c_shadow = hex_to_rgba("#112B23")
        c_mid = hex_to_rgba("#275241")
        c_sun = hex_to_rgba("#628B68")

    sun_dir = Vector((0.52, 0.74, 0.42)).normalized()

    def color_fn(wx, wy, wz, nx, ny, nz):
        norm = Vector((nx, ny, nz)).normalized()
        sun_dot = max(0.0, norm.dot(sun_dir))
        height_t = max(0.0, min(1.0, (wy - (tree_y_base + 0.95)) / 1.95))
        n_leaf = noise.noise(Vector((wx * 3.2, wy * 3.2, wz * 3.2)))

        radial_d = math.hypot(wx - tree_x, wz - tree_z)
        core_ao = max(0.0, min(1.0, (radial_d - 0.22) / 0.88))

        light_val = max(0.0, min(1.0, 0.34 * height_t + 0.48 * sun_dot + 0.18 * core_ao + 0.16 * n_leaf))
        if light_val < 0.46:
            return lerp_color(c_shadow, c_mid, light_val / 0.46)
        return lerp_color(c_mid, c_sun, (light_val - 0.46) / 0.54)

    return color_fn


def make_bark_color_fn(is_birch=False):
    if is_birch:
        c_base = hex_to_rgba("#A69988")
        c_dark = hex_to_rgba("#483F36")
        c_moss = hex_to_rgba("#466141")
    else:
        c_base = hex_to_rgba("#6C4D36")
        c_dark = hex_to_rgba("#3A281B")
        c_moss = hex_to_rgba("#425C3C")

    def color_fn(wx, wy, wz, nx, ny, nz):
        n_b = noise.noise(Vector((wx * 2.8, wy * 4.5, wz * 2.8)))
        col = lerp_color(c_dark, c_base, 0.42 + 0.48 * max(0.0, nx * 0.5 + ny * 0.5) + 0.22 * n_b)
        if is_birch:
            band = math.sin(wy * 24.0 + n_b * 4.2)
            if band > 0.70:
                col = lerp_color(col, c_dark, 0.72)
        if wy < 0.75:
            moss_t = max(0.0, (0.75 - wy) / 0.48) * (0.6 + 0.4 * n_b)
            col = lerp_color(col, c_moss, min(0.78, moss_t))
        return col

    return color_fn


def create_tree_archetype_oak(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Tree A — Main Broadleaf Hero Tree (Rebuilt V5):
    - Root-buttressed S-curved trunk, 5 primary boughs, 10 secondary limbs, and visible tertiary branches
    - Multi-scale foliage clusters with hundreds of outer 3D lanceolate leaf-fan sprays (NO marshmallow blobs!)
    """
    y0 = get_terrain_height(x, z) - 0.06
    bm_trunk = bmesh.new()

    trunk_pts = []
    steps = 12
    h = 1.62 * scale
    for i in range(steps + 1):
        t = i / steps
        rad = (0.26 * (1.0 - 0.54 * (t ** 0.75)) + 0.09 * math.exp(-t * 6.5)) * scale
        px = x + (lean_x * (t ** 1.3) + 0.08 * math.sin(t * math.pi * 1.4)) * scale
        pz = z + (lean_z * (t ** 1.3) - 0.05 * math.sin(t * math.pi)) * scale
        py = y0 + h * t
        trunk_pts.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, trunk_pts, segs=14, bark_groove_amp=0.06, is_trunk=True)

    # Surface root buttresses gripping the terrain
    for ir_root in range(4):
        ang_r = ir_root * (math.pi * 0.5) + 0.35
        r_pts = []
        for k in range(6):
            tk = k / 5.0
            rx_p = x + math.cos(ang_r) * (0.14 + 0.34 * tk) * scale
            rz_p = z + math.sin(ang_r) * (0.14 + 0.34 * tk) * scale
            ry_p = y0 + (0.28 * (1.0 - tk) ** 1.6 - 0.03 * tk) * scale
            r_pts.append((rx_p, ry_p, rz_p, 0.085 * (1.0 - 0.75 * tk) * scale))
        add_curved_branch_tube(bm_trunk, r_pts, segs=8, bark_groove_amp=0.03)

    # 5 Primary Boughs + 2 Secondary Forking Limbs per Bough
    bough_specs = [
        (-0.82, 0.58, 0.24, 0.115, 0.72),
        (0.78, 0.55, -0.20, 0.110, 0.75),
        (-0.32, 0.78, -0.62, 0.102, 0.80),
        (0.36, 0.74, 0.54, 0.098, 0.78),
        (0.05, 0.94, -0.10, 0.095, 0.88),
    ]
    foliage_anchors = []
    for b_idx, (bx_d, by_d, bz_d, b_rad, start_frac) in enumerate(bough_specs):
        p_idx = min(steps, int(start_frac * steps))
        sx, sy, sz, _ = trunk_pts[p_idx]
        b_pts = []
        for ib in range(8):
            tb = ib / 7.0
            r_b = b_rad * (1.0 - 0.65 * tb) * scale
            px = sx + (bx_d * (tb ** 1.08) + 0.05 * math.sin(tb * math.pi)) * scale
            py = sy + (by_d * (tb ** 0.82) + 0.06 * math.sin(tb * math.pi)) * scale
            pz = sz + (bz_d * (tb ** 1.08)) * scale
            b_pts.append((px, py, pz, r_b))
        add_curved_branch_tube(bm_trunk, b_pts, segs=10, bark_groove_amp=0.035)
        foliage_anchors.append((b_pts[-1][0], b_pts[-1][1], b_pts[-1][2], 1.0))

        # Secondary forked sub-branches off each primary bough
        mid_x, mid_y, mid_z, mid_r = b_pts[4]
        for s_sign in (-1.0, 1.0):
            s_pts = []
            for isub in range(6):
                ts = isub / 5.0
                s_pts.append((
                    mid_x + (bx_d * 0.42 + s_sign * 0.34 * (-bz_d)) * ts * scale,
                    mid_y + (0.28 + 0.10 * s_sign) * (ts ** 0.85) * scale,
                    mid_z + (bz_d * 0.42 + s_sign * 0.34 * bx_d) * ts * scale,
                    mid_r * 0.72 * (1.0 - 0.70 * ts),
                ))
            add_curved_branch_tube(bm_trunk, s_pts, segs=7, bark_groove_amp=0.02)
            foliage_anchors.append((s_pts[-1][0], s_pts[-1][1], s_pts[-1][2], 0.76))

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(False))

    # Multi-Scale Leaf Canopy Construction with 3D Leaf-Fan Sprays
    bm_canopy = bmesh.new()
    for a_idx, (ax, ay, az, a_scale) in enumerate(foliage_anchors):
        # Main bough foliage mass + 2 satellite leaf clusters with rich 3D leaf fans
        sub_clusters = [
            (0.0, 0.04, 0.0, 0.36 * a_scale, 0.23 * a_scale, 0.33 * a_scale, 15),
            (
                0.20 * math.cos(a_idx * 1.9) * a_scale,
                -0.04 * a_scale,
                0.20 * math.sin(a_idx * 1.9) * a_scale,
                0.27 * a_scale,
                0.18 * a_scale,
                0.25 * a_scale,
                11,
            ),
            (
                -0.16 * math.sin(a_idx * 2.3) * a_scale,
                0.14 * a_scale,
                0.16 * math.cos(a_idx * 2.3) * a_scale,
                0.25 * a_scale,
                0.17 * a_scale,
                0.23 * a_scale,
                10,
            ),
        ]
        for s_i, (dx, dy, dz, rx, ry, rz, n_fans) in enumerate(sub_clusters):
            add_sculpted_leaf_mass_with_sprays(
                bm_canopy,
                ax + dx * scale,
                ay + dy * scale,
                az + dz * scale,
                rx * scale,
                ry * scale,
                rz * scale,
                yaw=(a_idx * 0.7 + s_i * 1.1),
                pitch=0.08 * math.sin(a_idx + s_i),
                seed_val=a_idx * 3.1 + s_i * 1.7 + x,
                num_leaf_fans=n_fans,
                leaf_scale=0.165 * scale * a_scale,
            )

    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
    )


def create_tree_archetype_birch(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Tree B — Slender Woodland Tree (Multi-Stem Silver Birch / Alder):
    - Open, delicate branching silhouette with visible pale trunks and secondary twigs
    - Airy, pendulous leaf-fan bouquets with clear negative space between boughs
    """
    y0 = get_terrain_height(x, z) - 0.05
    bm_trunk = bmesh.new()

    h_main = 1.98 * scale
    pts_main = []
    for i in range(13):
        t = i / 12.0
        rad = (0.14 * (1.0 - 0.66 * (t ** 0.8)) + 0.04 * math.exp(-t * 7.0)) * scale
        px = x + (lean_x * (t ** 1.25) + 0.09 * math.sin(t * math.pi)) * scale
        pz = z + (lean_z * (t ** 1.25) + 0.04 * math.cos(t * math.pi)) * scale
        py = y0 + h_main * t
        pts_main.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts_main, segs=12, bark_groove_amp=0.025, is_trunk=True)

    h_sec = 1.48 * scale
    side_sign = -1.0 if lean_x >= 0 else 1.0
    pts_sec = []
    for i in range(10):
        t = i / 9.0
        rad = (0.10 * (1.0 - 0.68 * t)) * scale
        px = x + (side_sign * 0.54 * (t ** 1.15)) * scale
        pz = z + (0.26 * (t ** 1.1)) * scale
        py = y0 + h_sec * (t ** 0.92)
        pts_sec.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts_sec, segs=10, bark_groove_amp=0.02, is_trunk=True)

    branch_anchors = [
        (0.52, -0.50, 0.34, 0.20),
        (0.68, 0.48, 0.38, -0.22),
        (0.82, -0.32, 0.40, -0.28),
        (0.92, 0.26, 0.35, 0.18),
    ]
    sub_tips = [
        (pts_main[-1][0], pts_main[-1][1], pts_main[-1][2], 0.92),
        (pts_sec[-1][0], pts_sec[-1][1], pts_sec[-1][2], 0.84),
    ]
    for t_anchor, dx, dy, dz in branch_anchors:
        idx_a = int(t_anchor * 12)
        ax, ay, az, _ = pts_main[idx_a]
        b_pts = []
        for ib in range(7):
            tb = ib / 6.0
            b_pts.append((
                ax + dx * tb * scale,
                ay + dy * (tb ** 0.82) * scale,
                az + dz * tb * scale,
                0.055 * (1.0 - 0.72 * tb) * scale,
            ))
        add_curved_branch_tube(bm_trunk, b_pts, segs=8, bark_groove_amp=0.015)
        sub_tips.append((b_pts[-1][0], b_pts[-1][1], b_pts[-1][2], 0.78))

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(True))

    bm_canopy = bmesh.new()
    for t_idx, (tx, ty, tz, t_sc) in enumerate(sub_tips):
        bouquets = [
            (0.0, 0.03, 0.0, 0.30 * t_sc, 0.18 * t_sc, 0.28 * t_sc, 14),
            (
                0.18 * math.cos(t_idx * 2.1) * t_sc,
                -0.05 * t_sc,
                0.18 * math.sin(t_idx * 2.1) * t_sc,
                0.22 * t_sc,
                0.15 * t_sc,
                0.21 * t_sc,
                10,
            ),
        ]
        for b_i, (dx, dy, dz, rx, ry, rz, n_fans) in enumerate(bouquets):
            add_sculpted_leaf_mass_with_sprays(
                bm_canopy,
                tx + dx * scale,
                ty + dy * scale,
                tz + dz * scale,
                rx * scale,
                ry * scale,
                rz * scale,
                yaw=t_idx * 1.1 + b_i,
                pitch=0.10,
                seed_val=t_idx * 2.7 + b_i + x,
                num_leaf_fans=n_fans,
                leaf_scale=0.15 * scale * t_sc,
            )

    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
    )


def create_tree_archetype_cedar(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Tree C — Rebuilt Evergreen (Fibonacci-Spiral Drape-Bough Spruce / Fir):
    - Eliminates stacked conical/rounded donut tiers completely!
    - Models 26 individual sweeping wooden branches in a continuous golden-angle spiral from base to spire tip,
      each carrying layered, feathered 3D evergreen needle-bough sprays that droop and fan outward organically.
    """
    y0 = get_terrain_height(x, z) - 0.06
    bm_trunk = bmesh.new()

    h = 2.52 * scale
    pts = []
    for i in range(15):
        t = i / 14.0
        rad = (0.21 * (1.0 - 0.80 * (t ** 0.85)) + 0.06 * math.exp(-t * 6.0)) * scale
        px = x + (lean_x * (t ** 1.35) + 0.04 * math.sin(t * math.pi)) * scale
        pz = z + (lean_z * (t ** 1.35)) * scale
        py = y0 + h * t
        pts.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts, segs=12, bark_groove_amp=0.05, is_trunk=True)

    bm_canopy = bmesh.new()
    num_boughs = 26
    golden_angle = 2.39996323

    for ib in range(num_boughs):
        u = ib / (num_boughs - 1)  # 0 at lowest bough, 1 near apex
        h_frac = 0.28 + 0.68 * u
        p_idx = min(13, int(h_frac * 14))
        frac_rem = (h_frac * 14) - p_idx
        cx = pts[p_idx][0] * (1 - frac_rem) + pts[p_idx + 1][0] * frac_rem
        cy = pts[p_idx][1] * (1 - frac_rem) + pts[p_idx + 1][1] * frac_rem
        cz = pts[p_idx][2] * (1 - frac_rem) + pts[p_idx + 1][2] * frac_rem

        ang = ib * golden_angle + (x * 0.7)
        # Irregular natural branch reach tapering toward the spire crown
        jitter = 0.86 + 0.28 * math.sin(ib * 3.7 + z)
        bough_len = (0.76 * ((1.0 - u * 0.78) ** 0.88)) * jitter * scale
        dir_x = math.cos(ang)
        dir_z = math.sin(ang)

        # Actual wooden branch extending from trunk into the bough spray
        br_pts = []
        for k in range(5):
            tk = k / 4.0
            droop_y = (-0.14 * tk + 0.09 * (tk ** 2.2)) * bough_len
            br_pts.append((
                cx + dir_x * bough_len * 0.82 * tk,
                cy + droop_y,
                cz + dir_z * bough_len * 0.82 * tk,
                0.042 * (1.0 - 0.72 * tk) * (1.0 - 0.5 * u) * scale,
            ))
        add_curved_branch_tube(bm_trunk, br_pts, segs=6, bark_groove_amp=0.01)

        # Build feathered, shingled 3D evergreen foliage spray along the bough (3 overlapping chevron pads + needle fans)
        nx_d, nz_d = -dir_z, dir_x
        for sub_t, pad_w_mult, pad_l_mult in ((0.38, 0.52, 0.48), (0.68, 0.62, 0.54), (0.94, 0.44, 0.42)):
            px = cx + dir_x * bough_len * sub_t
            pz = cz + dir_z * bough_len * sub_t
            py = cy + (-0.12 * sub_t + 0.07 * (sub_t ** 2)) * bough_len

            pw = bough_len * pad_w_mult
            pl = bough_len * pad_l_mult
            pt_thick = 0.095 * (1.0 - 0.45 * u) * scale

            # Sculpted evergreen bough pad with feathered needle tip
            ret = bmesh.ops.create_icosphere(bm_canopy, subdivisions=2, radius=1.0)
            for v in ret["verts"]:
                p = v.co
                n_s = noise.noise(Vector((p.x * 2.5 + ib, p.y * 2.5 - ib, p.z * 2.5)))
                # Chevron taper toward outer branch tip
                forward = p.x
                chevron_w = pw * (1.0 - 0.35 * forward) * (1.0 + 0.18 * n_s)
                droop_curve = -0.045 * (forward + 0.5) ** 2 * scale
                wx = px + dir_x * (forward * pl) + nx_d * (p.y * chevron_w)
                wz = pz + dir_z * (forward * pl) + nz_d * (p.y * chevron_w)
                wy = py + p.z * pt_thick * (1.1 if p.z > 0 else 0.5) + droop_curve
                v.co = Vector((wx, -wz, wy))

            # Add 4 dimensional 3D draping needle-fan tufts along the outer edge of each bough pad
            for ifr in (-1.5, -0.5, 0.5, 1.5):
                f_ang = ang + ifr * 0.28
                fx_d, fz_d = math.cos(f_ang), math.sin(f_ang)
                ftx, ftz = -fz_d, fx_d
                f_len = (0.16 + 0.04 * (1.8 - abs(ifr))) * (1.0 - 0.38 * u) * scale
                f_wid = f_len * 0.56
                f_thick = f_len * 0.28

                ax_f = px + fx_d * pl * 0.42
                az_f = pz + fz_d * pl * 0.42
                ay_f = py

                ret_nf = bmesh.ops.create_icosphere(bm_canopy, subdivisions=2, radius=1.0)
                for vnf in ret_nf["verts"]:
                    pnf = vnf.co
                    fwd = pnf.x * 0.5 + 0.35
                    droop_nf = -0.18 * (max(0.0, fwd) ** 1.7) * f_len
                    wx_nf = ax_f + fx_d * (fwd * f_len) + ftx * (pnf.y * f_wid * (1.0 - 0.25 * fwd))
                    wz_nf = az_f + fz_d * (fwd * f_len) + ftz * (pnf.y * f_wid * (1.0 - 0.25 * fwd))
                    wy_nf = ay_f + pnf.z * f_thick * (1.05 if pnf.z >= 0 else 0.55) + droop_nf
                    vnf.co = Vector((wx_nf, -wz_nf, wy_nf))

    # Tapered evergreen crown leader spire at the very top
    spire_x, spire_y, spire_z, _ = pts[-1]
    add_sculpted_leaf_mass_with_sprays(
        bm_canopy,
        spire_x,
        spire_y + 0.05 * scale,
        spire_z,
        0.16 * scale,
        0.24 * scale,
        0.16 * scale,
        yaw=0.0,
        pitch=0.0,
        seed_val=x * 3.1,
        num_leaf_fans=10,
        leaf_scale=0.12 * scale,
    )

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(False))
    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
    )


# ==============================================================================
# 3. STAGE 2 — WOODEN SIGNPOST GEOMETRY REPAIR & FINAL NAMING ('Design Trail' / 'Game Trail')
# ==============================================================================

def build_signpost(name, label_text, x, z, yaw_deg, arrow_dir, materials):
    """
    STAGE 2 Complete Structural Reconstruction:
    - Eliminates all overlapping trim boxes, penetrating post straps, and non-planar cube bevels.
    - Constructs the signboard as a single, watertight, multi-segment extruded timber plank
      placed cleanly in front of the post (lz = +0.096 to +0.176), attached via rear-only
      mortise brackets (lz = +0.050 to +0.095).
    - Renders final locked names: 'Design Trail' (left) and 'Game Trail' (right).
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()
    # Tapered chamfered oak post (occupies lz from -0.075 to +0.075)
    add_beveled_box(
        bm_post,
        lambda co: to_world(
            co.x * (0.150 - 0.018 * (co.z + 0.5)),
            0.74 + co.z * 1.56,
            co.y * (0.150 - 0.018 * (co.z + 0.5)),
        ),
        bevel_offset=0.015,
        segments=2,
    )

    # Stepped pyramid weather cap
    ret_cap = bmesh.ops.create_cube(bm_post, size=1.0)
    for v in ret_cap["verts"]:
        t_top = 0.52 if v.co.z > 0 else 1.20
        v.co = to_world(v.co.x * 0.195 * t_top, 1.55 + v.co.z * 0.10, v.co.y * 0.195 * t_top)

    # Base mortised timber collar
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.25, 0.08 + co.z * 0.15, co.y * 0.25),
        bevel_offset=0.012,
        segments=2,
    )

    # Rear-only wrought-iron mortise brackets connecting post front (lz=+0.070) to board back (lz=+0.095)
    # Never penetrates into or across the signboard!
    for bracket_y in (1.04, 1.26):
        add_beveled_box(
            bm_post,
            lambda co, by=bracket_y: to_world(
                co.x * 0.175,
                by + co.z * 0.038,
                0.010 + co.y * 0.168,
            ),
            bevel_offset=0.004,
            segments=1,
        )

    c_post_light = hex_to_rgba("#8A5B38")
    c_post_dark = hex_to_rgba("#4E321D")
    finalize_mesh_object(
        f"{name}_Post",
        bm_post,
        materials["wood_post"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_post_dark, c_post_light, 0.35 + 0.55 * min(1.0, (wy - y_ground) / 1.4)
        ),
    )

    # Watertight, Single-Piece Multi-Segment Hand-Hewn Directional Oak Plank
    # Front face at lz_front = +0.172, Back face at lz_back = +0.096 (solid 0.076 thickness)
    bm_board = bmesh.new()
    board_y = 1.15
    half_h = 0.215
    lz_back = 0.096
    lz_front = 0.172
    bevel_inset = 0.016

    if arrow_dir < 0:
        # Left-pointing arrow profile: arrow tip at x = -0.84, tail at x = +0.74
        x_stations = [
            (-0.84, 0.02),
            (-0.56, half_h * 0.96),
            (-0.28, half_h * 1.00),
            (0.0, half_h * 0.99),
            (0.28, half_h * 1.01),
            (0.54, half_h * 0.98),
            (0.74, half_h * 0.93),
        ]
    else:
        # Right-pointing arrow profile: tail at x = -0.74, arrow tip at x = +0.84
        x_stations = [
            (-0.74, half_h * 0.93),
            (-0.54, half_h * 0.98),
            (-0.28, half_h * 1.01),
            (0.0, half_h * 0.99),
            (0.28, half_h * 1.00),
            (0.56, half_h * 0.96),
            (0.84, 0.02),
        ]

    # Build 4 depth layers (back beveled face, back outer perimeter, front outer perimeter, front beveled face)
    # so the entire signboard is a 100% manifold, bevel-edged solid timber plank with coplanar front/back faces!
    layers_spec = [
        (lz_back, 0.92),
        (lz_back + bevel_inset, 1.00),
        (lz_front - bevel_inset, 1.00),
        (lz_front, 0.92),
    ]

    layer_loops = []
    for lz_val, scale_factor in layers_spec:
        # Trace closed perimeter loop counter-clockwise around the plank profile
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
            top_edge.append(bm_board.verts.new(to_world(x_sh, board_y + h_sh, lz_val)))
            bot_edge.append(bm_board.verts.new(to_world(x_sh, board_y - h_sh, lz_val)))
        layer_loops.append((top_edge, bot_edge))

    # Cap back planar face (layer 0) and front planar face (layer 3) with clean vertical quad strips (zero long diagonal skew!)
    top0, bot0 = layer_loops[0]
    top3, bot3 = layer_loops[3]
    for i in range(len(x_stations) - 1):
        # Back face (normal pointing -Z)
        bm_board.faces.new((top0[i], top0[i + 1], bot0[i + 1], bot0[i]))
        # Front face (normal pointing +Z)
        bm_board.faces.new((bot3[i], bot3[i + 1], top3[i + 1], top3[i]))

    # Stitch bevel & side walls between consecutive depth layers (0->1, 1->2, 2->3)
    for il in range(3):
        tA, bA = layer_loops[il]
        tB, bB = layer_loops[il + 1]
        n_st = len(x_stations)
        for i in range(n_st - 1):
            # Top wall strip
            bm_board.faces.new((tA[i], tB[i], tB[i + 1], tA[i + 1]))
            # Bottom wall strip
            bm_board.faces.new((bA[i + 1], bB[i + 1], bB[i], bA[i]))
        # Left end cap
        bm_board.faces.new((bA[0], bB[0], tB[0], tA[0]))
        # Right end cap
        bm_board.faces.new((tA[n_st - 1], tB[n_st - 1], bB[n_st - 1], bA[n_st - 1]))

    c_plaque_dark = hex_to_rgba("#3D2412")
    c_plaque_warm = hex_to_rgba("#6A4326")
    finalize_mesh_object(
        f"{name}_Board",
        bm_board,
        materials["wood_sign_plaque"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_plaque_dark, c_plaque_warm, 0.38 + 0.45 * abs(ny) + 0.17 * math.sin(wy * 38.0)
        ),
    )

    # Crisp, Restrained Handcrafted 3D Relief Lettering ('Design Trail' & 'Game Trail')
    # Placed flush at lz = +0.1725 (front face is +0.172) so there is zero gap and zero z-fighting!
    bpy.ops.object.text_add(location=(0, 0, 0))
    txt_obj = bpy.context.active_object
    txt_obj.name = f"{name}_Label3D"
    txt_obj.data.body = label_text
    txt_obj.data.align_x = 'CENTER'
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.size = 0.184
    txt_obj.data.space_character = 1.05
    txt_obj.data.extrude = 0.011
    txt_obj.data.bevel_depth = 0.0016
    txt_obj.data.bevel_resolution = 1

    bpy.ops.object.convert(target='MESH')
    text_x_offset = 0.04 if arrow_dir < 0 else -0.04
    for v in txt_obj.data.vertices:
        lx = v.co.x + text_x_offset
        ly = board_y + v.co.y
        lz = 0.172 + v.co.z
        v.co = to_world(lx, ly, lz)

    txt_obj.data.materials.append(materials["ivory_lettering"])
    for poly in txt_obj.data.polygons:
        poly.use_smooth = True


# ==============================================================================
# 4. STAGE 4 — CREEK, SPRING/CASCADE GROTTOS & INTEGRATED ARCHED BRIDGE
# ==============================================================================

def build_stream_and_bridge(materials):
    """
    STAGE 4 Creek & Bridge Reconstruction:
    - Widened creek channel with curved, tapered ends enclosed inside spring/cascade boulder grottos
      (no rectangular water cut edges!).
    - Concave pebble riverbed (Stream_Bed) + translucent depth-tinted water surface (Stream_Water).
    - Arched 13-plank oak bridge with stone-and-timber bank abutments flush with the trail approaches.
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

        # Smoothly round both stream ends inside the spring and cascade rock grottos
        end_envelope = math.sin(u_stream * math.pi) ** 0.42
        hw = stream_half_width(x) * max(0.14, end_envelope)
        bed_center_y = get_terrain_height(x, cz)
        # Water surface sits naturally inside the carved channel below the bank shoulders
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

    c_water_deep = hex_to_rgba("#1A5450")
    c_water_mid = hex_to_rgba("#2F766F")
    c_water_shallow = hex_to_rgba("#598A77")
    c_water_foam = hex_to_rgba("#9EC6BB")

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

    # Handcrafted Arched Wooden Bridge Integrated Flush with Both Trail Approaches
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

    # Stone-and-timber abutment sill beams embedded into both creek banks
    for end_sign in (-1.0, 1.0):
        wz_sill = bridge_center_z + end_sign * (bridge_span * 0.48)
        wy_sill = arch_height(end_sign * (bridge_span * 0.48)) - 0.025
        add_beveled_box(
            bm_bridge,
            lambda co, wz_sill=wz_sill, wy_sill=wy_sill: Vector((
                co.x * (bridge_width + 0.12),
                -(wz_sill + co.y * 0.14),
                wy_sill + co.z * 0.09,
            )),
            bevel_offset=0.010,
            segments=2,
        )

    # Two arched timber stringer beams spanning between the bank sills
    for side in (-0.39, 0.39):
        segs = 16
        beam_verts = []
        for i in range(segs + 1):
            zl = -bridge_span * 0.49 + bridge_span * 0.98 * (i / segs)
            wz = bridge_center_z + zl
            wy = arch_height(zl) - 0.036
            beam_verts.append((side, wz, wy))
        for i in range(segs):
            x0, z0, y0 = beam_verts[i]
            x1, z1, y1 = beam_verts[i + 1]
            ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
            for v in ret["verts"]:
                t = v.co.y + 0.5
                vx = x0 + v.co.x * 0.088
                vz = z0 * (1 - t) + z1 * t
                vy = (y0 * (1 - t) + y1 * t) + v.co.z * 0.075
                v.co = Vector((vx, -vz, vy))

    # 13 individual beveled oak deck planks with natural spacing and camber
    for ip in range(num_planks):
        u = (ip / (num_planks - 1)) * 2.0 - 1.0
        zl = u * (bridge_span * 0.46)
        wz = bridge_center_z + zl
        wy = arch_height(zl) + 0.015
        slope = -0.22 * u
        w_var = bridge_width * (0.99 + 0.018 * math.sin(ip * 2.3))

        def plank_tf(co, wz=wz, wy=wy, slope=slope, w_var=w_var):
            px = co.x * w_var
            pz = co.y * 0.088
            py = co.z * 0.044
            rz = pz * math.cos(slope) - py * math.sin(slope)
            ry = pz * math.sin(slope) + py * math.cos(slope)
            return Vector((px, -(wz + rz), wy + ry))

        add_beveled_box(bm_bridge, plank_tf, bevel_offset=0.009, segments=2)

    # 6 vertical beveled posts + curved double handrails
    for side in (-0.46, 0.46):
        for post_z_local in (-0.58, 0.0, 0.58):
            wz = bridge_center_z + post_z_local
            wy = arch_height(post_z_local)
            add_beveled_box(
                bm_bridge,
                lambda co, side=side, wz=wz, wy=wy: Vector((
                    side + co.x * 0.082,
                    -(wz + co.y * 0.082),
                    wy + 0.15 + co.z * 0.35,
                )),
                bevel_offset=0.010,
                segments=2,
            )

        for rail_h, rail_thick in ((0.29, 0.046), (0.165, 0.030)):
            segs = 14
            for i in range(segs):
                u0 = (i / segs) * 2.0 - 1.0
                u1 = ((i + 1) / segs) * 2.0 - 1.0
                zl0 = u0 * 0.60
                zl1 = u1 * 0.60
                wy0 = arch_height(zl0) + rail_h
                wy1 = arch_height(zl1) + rail_h
                ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
                for v in ret["verts"]:
                    t = v.co.y + 0.5
                    vz = bridge_center_z + (zl0 * (1 - t) + zl1 * t)
                    vy = (wy0 * (1 - t) + wy1 * t) + v.co.z * rail_thick
                    vx = side + v.co.x * 0.052
                    v.co = Vector((vx, -vz, vy))

    c_oak_light = hex_to_rgba("#AD7A50")
    c_oak_dark = hex_to_rgba("#734C2D")
    finalize_mesh_object(
        "Wooden_Bridge",
        bm_bridge,
        materials["wood_oak"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_oak_dark,
            c_oak_light,
            0.45 + 0.35 * max(0.0, ny) + 0.22 * math.sin(wz * 28.0 + wx * 4.0),
        ),
    )


# ==============================================================================
# 5. STAGE 5 — MAILBOX ON STABLE DRY TERRACE & PURPOSEFUL BOTANICAL VEGETATION
# ==============================================================================

def build_woodland_mailbox(x, z, yaw_deg, materials):
    """
    Woodland Mailbox securely anchored on the dry front-right terrace (x=1.28, z=1.36),
    well clear of the widened creek water and bank slope.
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.145, 0.46 + co.z * 0.94, co.y * 0.145),
        bevel_offset=0.015,
        segments=2,
    )
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.46, 0.91 + co.z * 0.065, co.y * 0.60),
        bevel_offset=0.012,
        segments=2,
    )
    add_beveled_box(
        bm_post,
        lambda co: to_world(
            co.x * 0.095,
            0.72 + co.z * 0.24 + co.y * 0.12,
            0.14 + co.y * 0.24,
        ),
        bevel_offset=0.008,
        segments=2,
    )
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.24, 0.07 + co.z * 0.14, co.y * 0.24),
        bevel_offset=0.012,
        segments=2,
    )

    c_post_light = hex_to_rgba("#8F5F3A")
    c_post_dark = hex_to_rgba("#4E321D")
    finalize_mesh_object(
        "Mailbox_Post",
        bm_post,
        materials["wood_post"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_post_dark, c_post_light, 0.35 + 0.55 * min(1.0, (wy - y_ground) / 1.1)
        ),
    )

    bm_body = bmesh.new()
    segs_arch = 24
    segs_len = 10
    mb_w = 0.43
    mb_h = 0.41
    mb_l = 0.58
    base_y = 0.94

    profile_pts = [(-mb_w * 0.5, 0.0), (-mb_w * 0.5, mb_h * 0.48)]
    for i in range(segs_arch + 1):
        ang = math.pi - (math.pi * i) / segs_arch
        px = math.cos(ang) * (mb_w * 0.5)
        py = mb_h * 0.48 + math.sin(ang) * (mb_w * 0.5)
        profile_pts.append((px, py))
    profile_pts.append((mb_w * 0.5, 0.0))

    rings = []
    for il in range(segs_len + 1):
        lz = -mb_l * 0.5 + mb_l * (il / segs_len)
        rib_swell = 1.035 if il in (0, 1, segs_len - 1, segs_len) else 1.0
        row = []
        for px, py in profile_pts:
            row.append(bm_body.verts.new(to_world(px * rib_swell, base_y + py * rib_swell, lz)))
        rings.append(row)

    for il in range(segs_len):
        n_pts = len(profile_pts)
        for ip in range(n_pts):
            nip = (ip + 1) % n_pts
            bm_body.faces.new((
                rings[il][ip],
                rings[il][nip],
                rings[il + 1][nip],
                rings[il + 1][ip],
            ))
    bm_body.faces.new(rings[0][::-1])
    bm_body.faces.new(rings[-1])
    finalize_mesh_object("Mailbox_Body", bm_body, materials["mailbox_forest_metal"])

    bm_door = bmesh.new()
    door_thick = 0.038
    door_tilt = math.radians(22.0)
    hinge_y = base_y + 0.02
    hinge_z = mb_l * 0.5

    def door_point(px, py, dz):
        dy = py * 0.94
        ry = dy * math.cos(door_tilt) - dz * math.sin(door_tilt)
        rz = dy * math.sin(door_tilt) + dz * math.cos(door_tilt)
        return to_world(px * 0.94, hinge_y + ry, hinge_z + rz)

    front_ring = []
    back_ring = []
    for px, py in profile_pts:
        front_ring.append(bm_door.verts.new(door_point(px, py, door_thick)))
        back_ring.append(bm_door.verts.new(door_point(px, py, 0.0)))

    n_pts = len(profile_pts)
    for ip in range(n_pts):
        nip = (ip + 1) % n_pts
        bm_door.faces.new((back_ring[ip], back_ring[nip], front_ring[nip], front_ring[ip]))
    bm_door.faces.new(front_ring)
    bm_door.faces.new(back_ring[::-1])

    add_beveled_box(
        bm_door,
        lambda co: door_point(co.x * 0.11, mb_h * 0.74 + co.z * 0.035, door_thick + 0.025 + co.y * 0.035),
        bevel_offset=0.005,
        segments=2,
    )
    add_beveled_box(
        bm_door,
        lambda co: door_point(co.x * 0.24, mb_h * 0.46 + co.z * 0.045, door_thick + 0.012 + co.y * 0.018),
        bevel_offset=0.004,
        segments=1,
    )
    finalize_mesh_object("Mailbox_Door", bm_door, materials["champagne_brass"])

    bm_letter = bmesh.new()
    add_beveled_box(
        bm_letter,
        lambda co: to_world(co.x * 0.25, base_y + 0.21 + co.z * 0.032 - co.y * 0.04, 0.21 + co.y * 0.28),
        bevel_offset=0.004,
        segments=2,
    )
    finalize_mesh_object("Mailbox_Letter", bm_letter, materials["ivory_lettering"])

    bm_flag = bmesh.new()
    add_beveled_box(
        bm_flag,
        lambda co: to_world(mb_w * 0.55 + co.x * 0.026, base_y + 0.30 + co.z * 0.27, 0.06 + co.y * 0.048),
        bevel_offset=0.004,
        segments=1,
    )
    add_beveled_box(
        bm_flag,
        lambda co: to_world(mb_w * 0.55 + co.x * 0.030, base_y + 0.41 + co.z * 0.095, 0.12 + co.y * 0.15),
        bevel_offset=0.004,
        segments=1,
    )
    finalize_mesh_object("Mailbox_Flag", bm_flag, materials["champagne_brass"])


def build_rocks_and_botanical_groundcover(materials):
    """
    Builds spring/cascade boulder grottos enclosing both ends of the creek, central fork divide boulders,
    and environmentally motivated botanical vegetation (ferns, multi-scale grasses, moss pads, wildflowers).
    """
    bm_rocks = bmesh.new()
    rock_placements = [
        # NW spring headwater grotto enclosing the left creek origin (-3.38, -0.45)
        (-3.48, -0.52, 0.46, 0.32, 0.38), (-3.18, -0.88, 0.38, 0.27, 0.32),
        (-3.24, -0.05, 0.36, 0.25, 0.30), (-2.88, -0.68, 0.28, 0.19, 0.24),
        # SE cascade grotto enclosing the right creek outlet (+3.22, +0.72)
        (3.26, 0.78, 0.44, 0.28, 0.36), (2.98, 1.05, 0.36, 0.24, 0.30),
        (3.04, 0.36, 0.34, 0.23, 0.28), (2.72, 0.88, 0.26, 0.18, 0.22),
        # Creek bank & bridge abutment wing-wall stones
        (-2.15, 0.32, 0.28, 0.19, 0.23), (-1.28, 0.06, 0.25, 0.17, 0.21),
        (-0.56, 0.62, 0.25, 0.19, 0.22), (0.58, -0.22, 0.24, 0.18, 0.21),
        (-0.58, -0.26, 0.24, 0.18, 0.21), (0.56, 0.62, 0.24, 0.18, 0.21),
        (1.52, 0.72, 0.27, 0.19, 0.23), (2.25, 0.88, 0.30, 0.21, 0.25),
        # Partly submerged creek stones
        (-1.75, -0.14, 0.19, 0.09, 0.15), (-0.78, 0.08, 0.17, 0.08, 0.14),
        (0.84, 0.28, 0.18, 0.09, 0.15), (1.78, 0.50, 0.20, 0.10, 0.16),
        # Central fork divide boulder cluster & foreground knoll outcrop
        (-0.08, -1.18, 0.34, 0.23, 0.28), (0.24, -1.28, 0.24, 0.17, 0.20),
        (-1.68, 1.54, 0.32, 0.20, 0.25), (-1.40, 1.68, 0.22, 0.15, 0.18),
        # Signpost & mailbox base anchor stones
        (-1.92, -0.78, 0.25, 0.19, 0.21), (1.92, -0.74, 0.25, 0.19, 0.21),
        (1.55, 1.38, 0.22, 0.15, 0.18), (-0.12, -2.22, 0.36, 0.25, 0.29),
    ]
    for idx, (rx, rz, sx, sy, sz_r) in enumerate(rock_placements):
        ry = get_terrain_height(rx, rz) - 0.03
        ret = bmesh.ops.create_icosphere(bm_rocks, subdivisions=3, radius=1.0)
        yaw = (idx * 1.17) % math.pi
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.3 + idx, p.y * 2.3 - idx, p.z * 2.3)))
            facet = 1.0 + 0.24 * n - 0.10 * abs(p.z) - 0.08 * abs(p.x - p.y)
            lx = p.x * sx * facet
            lz = p.y * sz_r * facet
            wx = rx + lx * math.cos(yaw) - lz * math.sin(yaw)
            wz = rz + lx * math.sin(yaw) + lz * math.cos(yaw)
            wy = ry + p.z * sy * facet * (1.05 if p.z > 0 else 0.55)
            v.co = Vector((wx, -wz, wy))

    c_rock_base = hex_to_rgba("#62685E")
    c_rock_shadow = hex_to_rgba("#3D423B")
    c_rock_moss = hex_to_rgba("#4B6B46")

    def boulder_color_fn(wx, wy, wz, nx, ny, nz):
        col = lerp_color(c_rock_shadow, c_rock_base, 0.4 + 0.5 * max(0.0, ny + nx * 0.3))
        if ny > 0.36:
            col = lerp_color(col, c_rock_moss, min(0.76, (ny - 0.36) * 1.4))
        return col

    finalize_mesh_object("Environment_Rocks", bm_rocks, materials["stone_mossy"], boulder_color_fn)

    # Purposefully Clustered Ferns + Multi-Scale 3D Grass Families + Low Moss Cushions
    bm_foliage_ground = bmesh.new()

    fern_clusters = [
        # Creek bank & spring/cascade grotto ferns
        (-2.95, -0.25, 0.36, 7), (-2.25, 0.48, 0.32, 6), (2.52, 0.96, 0.34, 7),
        (2.85, 0.38, 0.30, 6), (-0.72, 0.72, 0.25, 5), (0.72, 0.70, 0.24, 5),
        # Foreground left stone outcrop & central fork divide ferns
        (-1.85, 1.42, 0.34, 6), (-1.30, 1.72, 0.23, 5), (0.05, -1.24, 0.32, 6),
        # Signpost, mailbox & tree root ferns
        (-1.84, -0.62, 0.26, 6), (1.84, -0.58, 0.26, 6), (1.52, 1.24, 0.24, 5),
        (-2.55, -1.65, 0.35, 7), (2.55, -1.55, 0.34, 7), (-0.22, -2.05, 0.35, 7),
    ]
    for c_idx, (fx, fz, f_scale, num_fronds) in enumerate(fern_clusters):
        fy = get_terrain_height(fx, fz) - 0.015
        for ifr in range(num_fronds):
            ang = (2.0 * math.pi * ifr) / num_fronds + (c_idx * 0.53) + 0.18 * math.sin(ifr * 2.1)
            frond_len = f_scale * (0.72 + 0.38 * ((ifr * 3 + c_idx) % 4) / 3.0)
            droop = 0.70 + 0.24 * ((ifr % 3) / 2.0)
            segs = 6
            rows = []
            for iseg in range(segs + 1):
                t = iseg / segs
                r = frond_len * t
                arch_y = fy + f_scale * (0.42 * math.sin(t * math.pi * droop))
                w = f_scale * 0.19 * math.sin(t * math.pi) * (0.84 + 0.16 * math.sin(t * 18.0))
                wx = fx + math.cos(ang) * r
                wz = fz + math.sin(ang) * r
                nx_d, nz_d = -math.sin(ang), math.cos(ang)
                twist = 0.03 * f_scale * math.sin(t * 4.0 + ifr)
                v_left = bm_foliage_ground.verts.new((wx - nx_d * w, -(wz - nz_d * w), arch_y + twist))
                v_mid = bm_foliage_ground.verts.new((wx, -wz, arch_y + 0.024 * f_scale))
                v_right = bm_foliage_ground.verts.new((wx + nx_d * w, -(wz + nz_d * w), arch_y - twist))
                rows.append((v_left, v_mid, v_right))
            for iseg in range(segs):
                l0, m0, r0 = rows[iseg]
                l1, m1, r1 = rows[iseg + 1]
                bm_foliage_ground.faces.new((l0, m0, m1, l1))
                bm_foliage_ground.faces.new((m0, r0, r1, m1))

    # Environmentally motivated multi-scale 3D grass families (clustered near banks, rocks, and trail shoulders)
    grass_anchor_families = [
        (-1.52, 1.38, 0.25), (-0.54, 0.84, 0.21), (0.54, 0.86, 0.20),
        (-1.24, 0.22, 0.24), (1.38, 0.88, 0.23), (1.48, 1.48, 0.21),
        (-1.74, -0.54, 0.22), (1.74, -0.50, 0.22), (-0.64, -0.38, 0.19),
        (0.64, -0.38, 0.19), (-0.28, -1.12, 0.21), (0.34, -1.15, 0.21),
        (-2.22, -0.92, 0.24), (2.22, -0.88, 0.24), (-0.42, 2.38, 0.18),
        (0.40, 2.28, 0.17),
    ]
    for fam_idx, (ax, az, b_scale) in enumerate(grass_anchor_families):
        sub_tufts = [
            (0.0, 0.0, b_scale * 1.15),
            (0.13 * math.cos(fam_idx * 1.7), 0.13 * math.sin(fam_idx * 1.7), b_scale * 0.76),
            (-0.11 * math.sin(fam_idx * 2.3), 0.11 * math.cos(fam_idx * 2.3), b_scale * 0.55),
        ]
        for s_idx, (dx, dz, g_scale) in enumerate(sub_tufts):
            gx, gz = ax + dx, az + dz
            gy = get_terrain_height(gx, gz) - 0.015
            num_blades = 6 + ((fam_idx + s_idx) % 4)
            for ib in range(num_blades):
                ang = (2.0 * math.pi * ib) / num_blades + fam_idx * 0.71 + s_idx * 1.1
                offset_r = 0.022 + 0.032 * ((ib % 3) * 0.5)
                bx0 = gx + math.cos(ang) * offset_r
                bz0 = gz + math.sin(ang) * offset_r
                blade_h = g_scale * (0.70 + 0.48 * ((ib * 5 + fam_idx) % 4) / 3.0)
                lean_r = blade_h * (0.35 + 0.22 * (ib % 2))
                blade_w = 0.022 * (0.82 + 0.30 * (ib % 2))
                nx_d, nz_d = -math.sin(ang), math.cos(ang)

                segs_b = 4
                b_rows = []
                for iseg in range(segs_b + 1):
                    t = iseg / segs_b
                    r = lean_r * (t ** 1.45)
                    by = gy + blade_h * math.sin(t * math.pi * 0.52)
                    w = blade_w * (1.0 - 0.88 * (t ** 1.2))
                    wx = bx0 + math.cos(ang) * r
                    wz = bz0 + math.sin(ang) * r
                    b_rows.append((
                        bm_foliage_ground.verts.new((wx - nx_d * w, -(wz - nz_d * w), by)),
                        bm_foliage_ground.verts.new((wx + nx_d * w, -(wz + nz_d * w), by)),
                    ))
                for iseg in range(segs_b):
                    v0l, v0r = b_rows[iseg]
                    v1l, v1r = b_rows[iseg + 1]
                    bm_foliage_ground.faces.new((v0l, v0r, v1r, v1l))

    c_fern_base = hex_to_rgba("#21442D")
    c_fern_tip = hex_to_rgba("#779D5F")

    def ground_foliage_color_fn(wx, wy, wz, nx, ny, nz):
        gy = get_terrain_height(wx, wz)
        h_rel = max(0.0, min(1.0, (wy - gy) / 0.22))
        n_f = noise.noise(Vector((wx * 2.0, wz * 2.0, wy)))
        return lerp_color(c_fern_base, c_fern_tip, min(1.0, h_rel * 0.85 + 0.15 + 0.15 * n_f))

    finalize_mesh_object("Forest_Ferns", bm_foliage_ground, materials["foliage_moss"], ground_foliage_color_fn)

    # Selective Wildflower Accents tucked naturally beside boulders & signposts
    bm_flowers = bmesh.new()
    flower_clusters = [
        (-1.76, -0.60, 4), (-1.48, 1.38, 3), (1.76, -0.56, 4),
        (1.45, 1.32, 3), (-0.60, 0.76, 3), (0.12, -1.18, 3),
    ]
    for idx, (cx, cz, count) in enumerate(flower_clusters):
        for sub in range(count):
            ang_s = idx * 1.9 + sub * 2.15
            rad_s = 0.045 + 0.050 * (sub % 3)
            fx = cx + math.cos(ang_s) * rad_s
            fz = cz + math.sin(ang_s) * rad_s
            fy = get_terrain_height(fx, fz) + 0.038 + 0.015 * (sub % 2)
            for ip in range(4):
                p_ang = (math.pi * 0.5) * ip + sub * 0.4
                px = fx + math.cos(p_ang) * 0.018
                pz = fz + math.sin(p_ang) * 0.018
                ret = bmesh.ops.create_icosphere(bm_flowers, subdivisions=1, radius=0.018)
                for v in ret["verts"]:
                    v.co = Vector((px + v.co.x, -(pz + v.co.y), fy + v.co.z * 0.55))

    finalize_mesh_object("Wildflowers", bm_flowers, materials["ivory_lettering"])


# ==============================================================================
# 6. LIGHTING & BLENDER VERIFICATION RENDERS
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
        bg.inputs[1].default_value = 1.05

    sun_data = bpy.data.lights.new(name="LateAfternoonSun", type='SUN')
    sun_data.energy = 3.9
    sun_data.color = hex_to_rgba("#FFF2D6")[:3]
    sun_obj = bpy.data.objects.new(name="LateAfternoonSun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = Euler((math.radians(46), math.radians(-24), math.radians(30)), 'XYZ')

    fill_data = bpy.data.lights.new(name="ForestFill", type='SUN')
    fill_data.energy = 1.55
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
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            v_count = len(obj.data.vertices)
            t_count = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
            total_verts += v_count
            total_tris += t_count
            if obj.name.startswith("Tree_"):
                tree_tris += t_count
    print(
        f"SCENE GEOMETRY STATS: {total_verts} vertices, {total_tris} total triangles "
        f"({tree_tris} tree triangles) across {len(bpy.context.scene.objects)} objects"
    )


def main():
    clear_scene()

    materials = {
        "grass_top": make_pbr_material("Grass_Top_Mat", "#5B7A53", roughness=0.82),
        "rock_underside": make_pbr_material("Rock_Underside_Mat", "#524B44", roughness=0.88),
        "stone_warm": make_pbr_material("Stone_Warm_Mat", "#928A7F", roughness=0.76),
        "stone_mossy": make_pbr_material("Stone_Mossy_Mat", "#646F5E", roughness=0.79),
        "stream_water": make_pbr_material("Stream_Water_Mat", "#2C6861", roughness=0.22, metallic=0.05),
        "wood_oak": make_pbr_material("Wood_Oak_Mat", "#9D6E48", roughness=0.66),
        "wood_post": make_pbr_material("Wood_Post_Mat", "#784F30", roughness=0.70),
        "wood_sign_plaque": make_pbr_material("Wood_Sign_Plaque_Mat", "#54331C", roughness=0.60),
        "wood_bark": make_pbr_material("Wood_Bark_Mat", "#6A4B35", roughness=0.84),
        "foliage_deep": make_pbr_material("Foliage_Deep_Mat", "#26543F", roughness=0.72),
        "foliage_moss": make_pbr_material("Foliage_Moss_Mat", "#4E724A", roughness=0.74),
        "foliage_sage": make_pbr_material("Foliage_Sage_Mat", "#73916C", roughness=0.75),
        "ivory_lettering": make_pbr_material("Ivory_Lettering_Mat", "#F5EFE3", roughness=0.36, use_vertex_color=False),
        "mailbox_forest_metal": make_pbr_material("Mailbox_Forest_Metal_Mat", "#1C4537", roughness=0.38, metallic=0.26, use_vertex_color=False),
        "champagne_brass": make_pbr_material("Champagne_Brass_Mat", "#DCC89A", roughness=0.28, metallic=0.74, use_vertex_color=False),
    }

    build_island_terrain_and_trails(materials)
    build_embedded_identity_plaque(materials)
    build_stream_and_bridge(materials)
    build_rocks_and_botanical_groundcover(materials)

    # STAGE 1 Rebuilt High-Fidelity Trees across 3 Distinct Archetypes
    create_tree_archetype_oak("Tree_NW_Hero", -2.55, -2.05, 1.22, -0.18, -0.10, 0, materials)
    create_tree_archetype_cedar("Tree_N_Left", -1.35, -2.55, 1.18, -0.06, -0.08, 2, materials)
    create_tree_archetype_birch("Tree_N_Center", 0.92, -2.48, 0.94, 0.14, -0.08, 1, materials)
    create_tree_archetype_cedar("Tree_N_Right", 2.15, -2.28, 1.26, 0.10, -0.10, 2, materials)
    create_tree_archetype_oak("Tree_NE_Hero", 3.05, -1.52, 1.05, 0.18, -0.05, 1, materials)
    create_tree_archetype_birch("Tree_W_Flank", -3.18, -0.72, 0.88, -0.18, 0.06, 1, materials)
    create_tree_archetype_cedar("Tree_E_Flank", 3.16, -0.32, 0.84, 0.15, 0.08, 0, materials)

    # STAGE 2 Rebuilt Solid Wooden Signposts with Final Locked Labels: 'Design Trail' & 'Game Trail'
    build_signpost("Signpost_UX", "Design Trail", -1.58, -0.68, 18.0, -1, materials)
    build_signpost("Signpost_Game", "Game Trail", 1.58, -0.64, -18.0, 1, materials)

    # STAGE 5 Mailbox securely anchored on the dry front-right terrace (x=1.28, z=1.36)
    build_woodland_mailbox(1.28, 1.36, -22.0, materials)

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
    print(f"Exported V5 runtime GLB to: {GLB_OUT}")

    setup_lighting_and_render_previews()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved V5 master Blender source to: {BLEND_OUT}")


if __name__ == "__main__":
    main()
