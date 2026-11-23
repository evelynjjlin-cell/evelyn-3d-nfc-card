"""
Blender 5.0 High-Poly Stylized Environment Authoring Script (V2 — Art Quality Gate Refined)
Project: The Crossroads — Two Paths, One Designer (Evelyn Lin)
Generates:
  - assets/source/crossroads_master.blend (editable source)
  - public/models/crossroads_environment.glb (runtime 3D environment)
  - assets/renders/blender_view_initial.png
  - assets/renders/blender_view_rotated.png
"""

import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Euler, noise

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND_OUT = os.path.join(ROOT_DIR, "assets", "source", "crossroads_master.blend")
GLB_OUT = os.path.join(ROOT_DIR, "public", "models", "crossroads_environment.glb")
RENDER_DIR = os.path.join(ROOT_DIR, "assets", "renders")

os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
os.makedirs(RENDER_DIR, exist_ok=True)

random.seed(42)


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


def make_pbr_material(name, hex_color, roughness=0.7, metallic=0.0, emission_hex=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(hex_color)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.35
        if emission_hex and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = hex_to_rgba(emission_hex)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def shade_smooth_with_normals(obj):
    bpy.context.view_layer.objects.active = obj
    for poly in obj.data.polygons:
        poly.use_smooth = True


def add_beveled_box(bm, transform_fn, bevel_offset=0.012, segments=2):
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
        )


def island_rim_point(angle):
    """Returns smooth organic (rx, rz) on the island perimeter for a given polar angle."""
    rx_base = 4.25 + 0.22 * math.cos(angle * 2.0) + 0.14 * math.sin(angle * 3.0 - 0.4)
    rz_base = 3.25 + 0.18 * math.sin(angle * 2.0 + 0.5) - 0.12 * math.cos(angle * 3.0)
    x = math.cos(angle) * rx_base
    z = math.sin(angle) * rz_base - 0.12 * math.cos(angle)
    return x, z


def island_radial_factor(x, z):
    """Returns normalized radial distance r in [0, 1+] relative to the organic island perimeter."""
    ang = math.atan2(z + 0.08, x)
    rim_x, rim_z = island_rim_point(ang)
    rim_r = math.hypot(rim_x, rim_z)
    cur_r = math.hypot(x, z)
    return cur_r / max(1e-4, rim_r)


def stream_center_z(x):
    """Meandering stream centerline Z as a function of X."""
    return 0.24 + 0.18 * x + 0.28 * math.sin(x * 0.72)


def path_distance(x, z):
    """Distance to the branching woodland crossroads pathway."""
    def seg_dist(px, pz, ax, az, bx, bz):
        vx, vz = bx - ax, bz - az
        wx, wz = px - ax, pz - az
        c1 = vx * wx + vz * wz
        if c1 <= 0:
            return math.hypot(px - ax, pz - az)
        c2 = vx * vx + vz * vz
        if c2 <= c1:
            return math.hypot(px - bx, pz - bz)
        b = c1 / c2
        pbx, pbz = ax + b * vx, az + b * vz
        return math.hypot(px - pbx, pz - pbz)

    d_main = seg_dist(x, z, 0.0, 2.25, 0.0, -0.10)
    d_left = seg_dist(x, z, 0.0, -0.10, -2.35, -1.45)
    d_right = seg_dist(x, z, 0.0, -0.10, 2.35, -1.45)
    return min(d_main, d_left, d_right)


def get_terrain_height(x, z):
    """Deterministic smooth terrain elevation at world (x, z)."""
    rf = island_radial_factor(x, z)

    # Gentle rolling woodland hills framing the back and sides
    base_hills = (
        0.26 * math.exp(-((x + 2.2) ** 2 + (z + 1.8) ** 2) / 3.4)
        + 0.28 * math.exp(-((x - 2.2) ** 2 + (z + 1.8) ** 2) / 3.4)
        + 0.34 * math.exp(-((x) ** 2 + (z + 2.35) ** 2) / 4.2)
        + 0.08 * math.sin(x * 0.9) * math.cos(z * 0.9)
    )
    n_val = noise.noise(Vector((x * 0.45 + 7.1, z * 0.45 - 3.4, 1.2))) * 0.08

    # Carve stream channel
    sz = stream_center_z(x)
    d_stream = abs(z - sz)
    stream_cut = 0.36 * math.exp(-(d_stream ** 2) / 0.22)

    # Gently recess the crossroads pathway
    d_path = path_distance(x, z)
    path_cut = 0.065 * math.exp(-(d_path ** 2) / 0.26)

    # Smooth rounded turf bevel near the perimeter
    edge_roll = 0.0
    if rf > 0.78:
        t = min(1.15, (rf - 0.78) / 0.22)
        edge_roll = -0.32 * (t ** 2.1)

    return 0.16 + base_hills + n_val - stream_cut - path_cut + edge_roll


def build_island_terrain(materials):
    """
    Creates a 100% smooth radial-ring sculpted upper grass island (ZERO sawtooth edges!),
    an overhanging mossy turf lip, and a deeply sculpted stratified stone & earth base.
    """
    bm_top = bmesh.new()
    rings = 56
    segs = 128

    center_y = get_terrain_height(0.0, 0.0)
    center_vert = bm_top.verts.new((0.0, 0.0, center_y))

    ring_verts = []
    for ir in range(1, rings + 1):
        # Concentrated ring density near the outer rim for a buttery-smooth rounded edge
        u = ir / rings
        r_frac = math.sin(u * math.pi * 0.5) if u > 0.7 else u * (math.sin(0.7 * math.pi * 0.5) / 0.7)
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            wx = rim_x * r_frac
            wz = rim_z * r_frac
            wy = get_terrain_height(wx, wz)
            # Extra overhanging turf lip on the final 3 rings
            if ir >= rings - 2:
                lip_t = (ir - (rings - 2)) / 2.0
                wy -= 0.09 * (lip_t ** 1.6)
            row.append(bm_top.verts.new((wx, -wz, wy)))
        ring_verts.append(row)

    # Connect center fan
    first_ring = ring_verts[0]
    for iseg in range(segs):
        nseg = (iseg + 1) % segs
        bm_top.faces.new((center_vert, first_ring[iseg], first_ring[nseg]))

    # Connect concentric quad rings
    for ir in range(len(ring_verts) - 1):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            v00 = ring_verts[ir][iseg]
            v10 = ring_verts[ir][nseg]
            v11 = ring_verts[ir + 1][nseg]
            v01 = ring_verts[ir + 1][iseg]
            bm_top.faces.new((v00, v01, v11, v10))

    bmesh.ops.recalc_face_normals(bm_top, faces=bm_top.faces)
    mesh_top = bpy.data.meshes.new("Island_Terrain_Top_Mesh")
    bm_top.to_mesh(mesh_top)
    bm_top.free()

    obj_top = bpy.data.objects.new("Island_Terrain_Top", mesh_top)
    bpy.context.collection.objects.link(obj_top)
    obj_top.data.materials.append(materials["grass_top"])
    shade_smooth_with_normals(obj_top)

    # Build layered Earth & Sculpted Stone Floating Island Underside
    bm_rock = bmesh.new()
    rock_rings = 28
    rock_rows = []
    for ir in range(rock_rings + 1):
        t = ir / rock_rings
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            top_y = get_terrain_height(rim_x, rim_z) - 0.07

            # Multi-tiered rocky cliff silhouette visible beneath the soil rim
            tier_wave = 0.045 * math.sin(t * math.pi * 5.0)
            scale = (1.002 - (t ** 1.95) * 0.88) + tier_wave * (1.0 - t)
            rx = rim_x * max(0.04, scale)
            rz = rim_z * max(0.04, scale)

            n1 = noise.noise(Vector((rx * 0.75 + 2.1, rz * 0.75 - 1.7, t * 3.5)))
            n2 = noise.noise(Vector((rx * 1.6 - 1.2, rz * 1.6 + 0.8, t * 6.0)))
            crag = (0.16 * n1 + 0.06 * n2) * (1.0 - t * 0.35) * min(1.0, t * 3.5)

            dir_len = max(1e-4, math.hypot(rim_x, rim_z))
            rx += (rim_x / dir_len) * crag
            rz += (rim_z / dir_len) * crag
            ry = top_y - 0.26 - (2.15 * (t ** 1.05)) + 0.07 * n1 * (1.0 - t)

            row.append(bm_rock.verts.new((rx, -rz, ry)))
        rock_rows.append(row)

    for ir in range(rock_rings):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            v00 = rock_rows[ir][iseg]
            v10 = rock_rows[ir][nseg]
            v11 = rock_rows[ir + 1][nseg]
            v01 = rock_rows[ir + 1][iseg]
            bm_rock.faces.new((v00, v01, v11, v10))

    bmesh.ops.recalc_face_normals(bm_rock, faces=bm_rock.faces)
    mesh_rock = bpy.data.meshes.new("Island_Rock_Underside_Mesh")
    bm_rock.to_mesh(mesh_rock)
    bm_rock.free()

    obj_rock = bpy.data.objects.new("Island_Rock_Underside", mesh_rock)
    bpy.context.collection.objects.link(obj_rock)
    obj_rock.data.materials.append(materials["rock_underside"])
    shade_smooth_with_normals(obj_rock)

    # Warm exposed terracotta/loam soil strata band between grass and deep rock
    bm_soil = bmesh.new()
    soil_rings = 7
    soil_rows = []
    for ir in range(soil_rings + 1):
        t = ir / soil_rings
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            top_y = get_terrain_height(rim_x, rim_z) - 0.04
            n_s = noise.noise(Vector((rim_x * 0.9, rim_z * 0.9, t * 2.0)))
            bulge = 1.003 - 0.035 * (t ** 1.4) + 0.012 * n_s * math.sin(t * math.pi)
            sx = rim_x * bulge
            sz = rim_z * bulge
            sy = top_y - 0.34 * t + 0.025 * n_s
            row.append(bm_soil.verts.new((sx, -sz, sy)))
        soil_rows.append(row)

    for ir in range(soil_rings):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm_soil.faces.new((
                soil_rows[ir][iseg],
                soil_rows[ir + 1][iseg],
                soil_rows[ir + 1][nseg],
                soil_rows[ir][nseg],
            ))

    bmesh.ops.recalc_face_normals(bm_soil, faces=bm_soil.faces)
    mesh_soil = bpy.data.meshes.new("Island_Soil_Rim_Mesh")
    bm_soil.to_mesh(mesh_soil)
    bm_soil.free()

    obj_soil = bpy.data.objects.new("Island_Soil_Rim", mesh_soil)
    bpy.context.collection.objects.link(obj_soil)
    obj_soil.data.materials.append(materials["soil_strata"])
    shade_smooth_with_normals(obj_soil)


def build_pathway_and_cobbles(materials):
    """Builds organically tapered, rounded-end crossroads pathways with embedded river-worn stepping stones."""
    bm_path = bmesh.new()

    def add_organic_path_ribbon(pts, half_w_start, half_w_end, taper_start=True, taper_end=True):
        rows = []
        n_pts = len(pts)
        for idx, (px, pz) in enumerate(pts):
            t = idx / max(1, n_pts - 1)
            hw = half_w_start * (1.0 - t) + half_w_end * t
            # Smooth rounded tip tapering so ends never look like sharp cut rectangles
            if taper_start and t < 0.14:
                hw *= math.sin((t / 0.14) * math.pi * 0.5)
            if taper_end and t > 0.84:
                hw *= math.sin(((1.0 - t) / 0.16) * math.pi * 0.5)
            hw = max(0.04, hw)

            if idx < n_pts - 1:
                dx = pts[idx + 1][0] - px
                dz = pts[idx + 1][1] - pz
            else:
                dx = px - pts[idx - 1][0]
                dz = pz - pts[idx - 1][1]
            length = max(1e-4, math.hypot(dx, dz))
            nx_dir, nz_dir = -dz / length, dx / length

            sub_cols = 9
            row = []
            for ic in range(sub_cols):
                u = (ic / (sub_cols - 1)) * 2.0 - 1.0
                # Soft organic edge wiggle
                edge_wiggle = 0.03 * math.sin(t * 14.0 + u * 2.0)
                wx = px + nx_dir * (hw + edge_wiggle) * u
                wz = pz + nz_dir * (hw + edge_wiggle) * u
                crown = 0.022 * (1.0 - u * u) - 0.012 * (u ** 4)
                wy = get_terrain_height(wx, wz) + 0.010 + crown
                row.append(bm_path.verts.new((wx, -wz, wy)))
            rows.append(row)

        for r in range(len(rows) - 1):
            for c in range(len(rows[r]) - 1):
                bm_path.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))

    # South approach (from front meadow to bridge edge)
    south_pts = [
        (0.04 * math.sin(i * 0.4), 2.32 - i * 0.11)
        for i in range(15)
    ]
    # Central crossroads plaza north of the bridge
    plaza_pts = [(0.0, -0.30 - i * 0.07) for i in range(5)]
    # Left branch curving past the UX Portfolio sign toward the northwestern grove
    left_branch = [
        (
            -2.35 * (i / 22.0) - 0.14 * math.sin((i / 22.0) * math.pi),
            -0.24 - 1.32 * (i / 22.0),
        )
        for i in range(23)
    ]
    # Right branch curving past the Game Portfolio sign toward the northeastern grove
    right_branch = [
        (
            2.35 * (i / 22.0) + 0.14 * math.sin((i / 22.0) * math.pi),
            -0.24 - 1.32 * (i / 22.0),
        )
        for i in range(23)
    ]

    add_organic_path_ribbon(south_pts, 0.50, 0.46, taper_start=True, taper_end=False)
    add_organic_path_ribbon(plaza_pts, 0.52, 0.58, taper_start=False, taper_end=True)
    add_organic_path_ribbon(left_branch, 0.46, 0.34, taper_start=False, taper_end=True)
    add_organic_path_ribbon(right_branch, 0.46, 0.34, taper_start=False, taper_end=True)

    bmesh.ops.recalc_face_normals(bm_path, faces=bm_path.faces)
    mesh_path = bpy.data.meshes.new("Crossroads_Pathway_Mesh")
    bm_path.to_mesh(mesh_path)
    bm_path.free()

    obj_path = bpy.data.objects.new("Crossroads_Pathway", mesh_path)
    bpy.context.collection.objects.link(obj_path)
    obj_path.data.materials.append(materials["pathway_earth"])
    shade_smooth_with_normals(obj_path)

    # Smooth beveled stepping stones & edging pebbles along pathways
    bm_stones = bmesh.new()
    stone_coords = [
        (0.02, 2.15, 0.21, 0.15), (-0.14, 1.88, 0.17, 0.14), (0.13, 1.62, 0.19, 0.16),
        (-0.10, 1.35, 0.18, 0.14), (0.11, 1.08, 0.16, 0.13), (-0.06, 0.86, 0.17, 0.14),
        (0.0, -0.30, 0.23, 0.18), (-0.42, -0.45, 0.18, 0.15), (-0.82, -0.66, 0.20, 0.15),
        (-1.22, -0.88, 0.17, 0.14), (-1.65, -1.12, 0.19, 0.15), (-2.05, -1.32, 0.16, 0.13),
        (0.42, -0.45, 0.18, 0.15), (0.82, -0.66, 0.20, 0.15), (1.22, -0.88, 0.17, 0.14),
        (1.65, -1.12, 0.19, 0.15), (2.05, -1.32, 0.16, 0.13),
        # Curbside border pebbles
        (-0.38, 1.95, 0.09, 0.08), (0.36, 1.75, 0.10, 0.08), (-0.36, 1.22, 0.09, 0.07),
        (0.35, 1.18, 0.08, 0.07), (-0.72, -0.32, 0.10, 0.08), (0.72, -0.32, 0.10, 0.08),
    ]
    for idx, (sx, sz, rx_s, rz_s) in enumerate(stone_coords):
        sy = get_terrain_height(sx, sz) + 0.018
        ret = bmesh.ops.create_icosphere(bm_stones, subdivisions=3, radius=1.0)
        yaw = (idx * 0.7) % math.pi
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.8 + sx, p.y * 2.8 + sz, p.z * 2.8)))
            lx = p.x * rx_s * (1.0 + 0.12 * n)
            lz = p.y * rz_s * (1.0 + 0.12 * n)
            wx = sx + lx * math.cos(yaw) - lz * math.sin(yaw)
            wz = sz + lx * math.sin(yaw) + lz * math.cos(yaw)
            wy = sy + p.z * 0.036 * (1.0 if p.z > 0 else 0.5)
            v.co = Vector((wx, -wz, wy))

    bmesh.ops.recalc_face_normals(bm_stones, faces=bm_stones.faces)
    mesh_stones = bpy.data.meshes.new("Pathway_Cobbles_Mesh")
    bm_stones.to_mesh(mesh_stones)
    bm_stones.free()

    obj_stones = bpy.data.objects.new("Pathway_Cobbles", mesh_stones)
    bpy.context.collection.objects.link(obj_stones)
    obj_stones.data.materials.append(materials["stone_warm"])
    shade_smooth_with_normals(obj_stones)


def build_stream_and_bridge(materials):
    """Builds the flowing stream ribbon clipped cleanly inside the island rim, plus the arched wooden bridge."""
    bm_water = bmesh.new()
    steps = 72
    cols = 11
    rows = []
    for i in range(steps + 1):
        x = -3.85 + 7.70 * (i / steps)
        cz = stream_center_z(x)
        rf = island_radial_factor(x, cz)
        if rf > 0.90:
            continue
        dx = 0.08
        dz = stream_center_z(x + dx) - cz
        length = math.hypot(dx, dz)
        nx_d, nz_d = -dz / length, dx / length

        # Taper stream width gently at the spring source and cascade outlet
        end_taper = min(1.0, (0.90 - rf) / 0.14)
        half_w = (0.42 + 0.05 * math.sin(x * 1.2)) * (0.45 + 0.55 * end_taper)
        row = []
        for c in range(cols):
            u = (c / (cols - 1)) * 2.0 - 1.0
            wx = x + nx_d * half_w * u
            wz = cz + nz_d * half_w * u
            wy = get_terrain_height(x, cz) + 0.14 + 0.008 * math.sin(x * 4.0 + u * 2.0)
            row.append(bm_water.verts.new((wx, -wz, wy)))
        rows.append(row)

    for r in range(len(rows) - 1):
        for c in range(len(rows[r]) - 1):
            bm_water.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))

    bmesh.ops.recalc_face_normals(bm_water, faces=bm_water.faces)
    mesh_water = bpy.data.meshes.new("Stream_Water_Mesh")
    bm_water.to_mesh(mesh_water)
    bm_water.free()

    obj_water = bpy.data.objects.new("Stream_Water", mesh_water)
    bpy.context.collection.objects.link(obj_water)
    obj_water.data.materials.append(materials["stream_water"])
    shade_smooth_with_normals(obj_water)

    # Handcrafted Arched Wooden Bridge spanning the stream at x=0, z=0.24
    bm_bridge = bmesh.new()
    bridge_center_z = 0.24
    bridge_span = 1.26
    bridge_width = 1.04
    num_planks = 9

    def arch_height(z_local):
        norm = z_local / (bridge_span * 0.5)
        return 0.17 + 0.15 * max(0.0, 1.0 - norm * norm)

    # Two arched under-beams
    for side in (-0.41, 0.41):
        segs = 14
        beam_verts = []
        for i in range(segs + 1):
            zl = -bridge_span * 0.52 + bridge_span * 1.04 * (i / segs)
            wz = bridge_center_z + zl
            wy = arch_height(zl) - 0.042
            beam_verts.append((side, wz, wy))
        for i in range(segs):
            x0, z0, y0 = beam_verts[i]
            x1, z1, y1 = beam_verts[i + 1]
            ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
            for v in ret["verts"]:
                t = v.co.y + 0.5
                vx = x0 + v.co.x * 0.085
                vz = z0 * (1 - t) + z1 * t
                vy = (y0 * (1 - t) + y1 * t) + v.co.z * 0.075
                v.co = Vector((vx, -vz, vy))

    # 9 individual beveled oak planks across the arch
    for ip in range(num_planks):
        u = (ip / (num_planks - 1)) * 2.0 - 1.0
        zl = u * (bridge_span * 0.44)
        wz = bridge_center_z + zl
        wy = arch_height(zl) + 0.015
        slope = -0.24 * u

        def plank_tf(co, wz=wz, wy=wy, slope=slope):
            px = co.x * bridge_width
            pz = co.y * 0.112
            py = co.z * 0.042
            rz = pz * math.cos(slope) - py * math.sin(slope)
            ry = pz * math.sin(slope) + py * math.cos(slope)
            return Vector((px, -(wz + rz), wy + ry))

        add_beveled_box(bm_bridge, plank_tf, bevel_offset=0.009, segments=2)

    # 6 vertical beveled posts + arched timber handrails
    for side in (-0.47, 0.47):
        for post_z_local in (-0.51, 0.0, 0.51):
            wz = bridge_center_z + post_z_local
            wy = arch_height(post_z_local)
            add_beveled_box(
                bm_bridge,
                lambda co, side=side, wz=wz, wy=wy: Vector((
                    side + co.x * 0.082,
                    -(wz + co.y * 0.082),
                    wy + 0.14 + co.z * 0.35,
                )),
                bevel_offset=0.010,
                segments=2,
            )

        # Top & mid handrails
        for rail_h, rail_thick in ((0.29, 0.046), (0.16, 0.032)):
            segs = 12
            for i in range(segs):
                u0 = (i / segs) * 2.0 - 1.0
                u1 = ((i + 1) / segs) * 2.0 - 1.0
                zl0 = u0 * 0.53
                zl1 = u1 * 0.53
                wy0 = arch_height(zl0) + rail_h
                wy1 = arch_height(zl1) + rail_h
                ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
                for v in ret["verts"]:
                    t = v.co.y + 0.5
                    vz = bridge_center_z + (zl0 * (1 - t) + zl1 * t)
                    vy = (wy0 * (1 - t) + wy1 * t) + v.co.z * rail_thick
                    vx = side + v.co.x * 0.052
                    v.co = Vector((vx, -vz, vy))

    bmesh.ops.recalc_face_normals(bm_bridge, faces=bm_bridge.faces)
    mesh_bridge = bpy.data.meshes.new("Wooden_Bridge_Mesh")
    bm_bridge.to_mesh(mesh_bridge)
    bm_bridge.free()

    obj_bridge = bpy.data.objects.new("Wooden_Bridge", mesh_bridge)
    bpy.context.collection.objects.link(obj_bridge)
    obj_bridge.data.materials.append(materials["wood_oak"])
    shade_smooth_with_normals(obj_bridge)


def create_sculpted_tree(name, x, z, scale, trunk_lean_x, trunk_lean_z, canopy_variant, materials):
    """
    Creates a high-poly stylized tree with tapered root-flared trunk, curved secondary limbs,
    and multi-tiered sculpted foliage crowns with smoothed organic vertex normals.
    """
    y_ground = get_terrain_height(x, z) - 0.05
    bm_trunk = bmesh.new()

    rings = 16
    segs = 16
    ring_verts = []
    height = 1.88 * scale
    for ir in range(rings + 1):
        t = ir / rings
        rad = (0.23 * (1.0 - 0.60 * (t ** 0.78)) + 0.09 * math.exp(-t * 7.0)) * scale
        cx = x + trunk_lean_x * (t ** 1.35) * scale + 0.05 * math.sin(t * math.pi) * scale
        cz = z + trunk_lean_z * (t ** 1.35) * scale
        cy = y_ground + height * t
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            root_flair = 1.0 + (0.32 * max(0.0, 1.0 - t * 3.2) * math.cos(ang * 4.0 + x))
            bark_grooves = 1.0 + 0.035 * math.sin(ang * 7.0 + t * 4.0)
            rx = cx + math.cos(ang) * rad * root_flair * bark_grooves
            rz = cz + math.sin(ang) * rad * root_flair * bark_grooves
            row.append(bm_trunk.verts.new((rx, -rz, cy)))
        ring_verts.append(row)

    for ir in range(rings):
        for iseg in range(segs):
            nseg = (iseg + 1) % segs
            bm_trunk.faces.new((
                ring_verts[ir][iseg],
                ring_verts[ir][nseg],
                ring_verts[ir + 1][nseg],
                ring_verts[ir + 1][iseg],
            ))

    # Add two curved secondary branches reaching into the canopy
    for b_dir in (-1.0, 1.0):
        b_rings = 8
        b_segs = 10
        b_rows = []
        start_x = x + trunk_lean_x * 0.65 * scale
        start_z = z + trunk_lean_z * 0.65 * scale
        start_y = y_ground + height * 0.68
        for ir in range(b_rings + 1):
            t = ir / b_rings
            rad = 0.09 * (1.0 - 0.65 * t) * scale
            bx = start_x + b_dir * 0.42 * (t ** 1.1) * scale
            bz = start_z + (0.14 * b_dir) * t * scale
            by = start_y + 0.42 * (t ** 0.85) * scale
            row = []
            for iseg in range(b_segs):
                ang = (2.0 * math.pi * iseg) / b_segs
                row.append(bm_trunk.verts.new((
                    bx + math.cos(ang) * rad,
                    -(bz + math.sin(ang) * rad),
                    by,
                )))
            b_rows.append(row)
        for ir in range(b_rings):
            for iseg in range(b_segs):
                nseg = (iseg + 1) % b_segs
                bm_trunk.faces.new((
                    b_rows[ir][iseg],
                    b_rows[ir][nseg],
                    b_rows[ir + 1][nseg],
                    b_rows[ir + 1][iseg],
                ))

    bmesh.ops.recalc_face_normals(bm_trunk, faces=bm_trunk.faces)
    mesh_trunk = bpy.data.meshes.new(f"{name}_Trunk_Mesh")
    bm_trunk.to_mesh(mesh_trunk)
    bm_trunk.free()

    obj_trunk = bpy.data.objects.new(f"{name}_Trunk", mesh_trunk)
    bpy.context.collection.objects.link(obj_trunk)
    obj_trunk.data.materials.append(materials["wood_bark"])
    shade_smooth_with_normals(obj_trunk)

    # Multi-tiered sculpted cloud-foliage crown (broad flat-bottomed stylized canopy layers)
    bm_canopy = bmesh.new()
    top_x = x + trunk_lean_x * scale
    top_z = z + trunk_lean_z * scale
    top_y = y_ground + height

    tiers = [
        # (dx, dy, dz, rx, ry, rz)
        (0.0, 0.02, 0.0, 0.92, 0.48, 0.84),
        (-0.42, 0.14, 0.10, 0.64, 0.42, 0.60),
        (0.42, 0.12, -0.08, 0.62, 0.40, 0.58),
        (0.0, 0.36, -0.04, 0.72, 0.44, 0.68),
        (0.02, 0.62, 0.02, 0.48, 0.34, 0.46),
    ]
    for lx, ly, lz, sx, sy, sz in tiers:
        ret = bmesh.ops.create_icosphere(bm_canopy, subdivisions=3, radius=1.0)
        for v in ret["verts"]:
            p = v.co
            n1 = noise.noise(Vector((p.x * 1.6 + x, p.y * 1.6 + z, p.z * 1.6 + ly)))
            n2 = noise.noise(Vector((p.x * 3.4 - z, p.y * 3.4 + x, p.z * 3.4)))
            disp = 1.0 + 0.14 * n1 + 0.05 * n2
            # Stylized leaf-pad profile: gently flattened underside, billowy upper crown
            vert_profile = 1.05 if p.z >= 0 else 0.58
            wx = top_x + lx * scale + p.x * sx * scale * disp
            wz = top_z + lz * scale - p.y * sz * scale * disp
            wy = top_y + ly * scale + p.z * sy * scale * disp * vert_profile
            v.co = Vector((wx, -wz, wy))

    bmesh.ops.recalc_face_normals(bm_canopy, faces=bm_canopy.faces)
    mesh_canopy = bpy.data.meshes.new(f"{name}_Canopy_Mesh")
    bm_canopy.to_mesh(mesh_canopy)
    bm_canopy.free()

    obj_canopy = bpy.data.objects.new(f"{name}_Canopy", mesh_canopy)
    bpy.context.collection.objects.link(obj_canopy)
    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][canopy_variant % 3]
    obj_canopy.data.materials.append(materials[mat_key])
    shade_smooth_with_normals(obj_canopy)


def build_signpost(name, label_text, x, z, yaw_deg, arrow_dir, materials):
    """
    Creates a handcrafted wooden signpost with beveled oak post, stone collar,
    iron mounting straps, double-beveled directional wooden board, and raised 3D lettering.
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()
    # Vertical beveled oak post
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.16, 0.72 + co.z * 1.56, co.y * 0.16),
        bevel_offset=0.015,
        segments=2,
    )

    # Decorative chamfered cap on top of post
    ret_cap = bmesh.ops.create_cube(bm_post, size=1.0)
    for v in ret_cap["verts"]:
        t_top = 0.58 if v.co.z > 0 else 1.18
        v.co = to_world(v.co.x * 0.21 * t_top, 1.53 + v.co.z * 0.11, v.co.y * 0.21 * t_top)

    # Base timber collar
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.24, 0.08 + co.z * 0.14, co.y * 0.24),
        bevel_offset=0.012,
        segments=2,
    )

    bmesh.ops.recalc_face_normals(bm_post, faces=bm_post.faces)
    mesh_post = bpy.data.meshes.new(f"{name}_Post_Mesh")
    bm_post.to_mesh(mesh_post)
    bm_post.free()

    obj_post = bpy.data.objects.new(f"{name}_Post", mesh_post)
    bpy.context.collection.objects.link(obj_post)
    obj_post.data.materials.append(materials["wood_post"])
    shade_smooth_with_normals(obj_post)

    # Handcrafted beveled directional wooden signboard
    bm_board = bmesh.new()
    board_w = 1.64
    board_h = 0.48
    board_d = 0.10
    board_y = 1.15

    def board_tf(co):
        lx = co.x * board_w
        ly = board_y + co.z * board_h
        lz = 0.11 + co.y * board_d
        if arrow_dir < 0 and co.x < -0.36:
            tip_factor = max(0.24, 1.0 - abs(co.x + 0.36) * 1.15)
            ly = board_y + (ly - board_y) * tip_factor
        elif arrow_dir > 0 and co.x > 0.36:
            tip_factor = max(0.24, 1.0 - abs(co.x - 0.36) * 1.15)
            ly = board_y + (ly - board_y) * tip_factor
        return to_world(lx, ly, lz)

    add_beveled_box(bm_board, board_tf, bevel_offset=0.014, segments=3)

    bmesh.ops.recalc_face_normals(bm_board, faces=bm_board.faces)
    mesh_board = bpy.data.meshes.new(f"{name}_Board_Mesh")
    bm_board.to_mesh(mesh_board)
    bm_board.free()

    obj_board = bpy.data.objects.new(f"{name}_Board", mesh_board)
    bpy.context.collection.objects.link(obj_board)
    obj_board.data.materials.append(materials["wood_sign_plaque"])
    shade_smooth_with_normals(obj_board)

    # Add physical 3D extruded beveled lettering on the front of the wooden board
    bpy.ops.object.text_add(location=(0, 0, 0))
    txt_obj = bpy.context.active_object
    txt_obj.name = f"{name}_Label3D"
    txt_obj.data.body = label_text
    txt_obj.data.align_x = 'CENTER'
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.size = 0.215
    txt_obj.data.extrude = 0.025
    txt_obj.data.bevel_depth = 0.004
    txt_obj.data.bevel_resolution = 2

    bpy.ops.object.convert(target='MESH')
    for v in txt_obj.data.vertices:
        lx = v.co.x
        ly = board_y + v.co.y
        lz = 0.165 + v.co.z
        v.co = to_world(lx, ly, lz)

    txt_obj.data.materials.append(materials["ivory_lettering"])
    shade_smooth_with_normals(txt_obj)


def build_woodland_mailbox(x, z, yaw_deg, materials):
    """
    Creates the vintage woodland mailbox with post, diagonal brace, arched forest-green body,
    articulated front door (Mailbox_Door), emerging parchment letter (Mailbox_Letter),
    brass flag (Mailbox_Flag), and raised 3D 'Contact' plaque.
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    # 1. Turned wooden post + stone collar + under-shelf
    bm_post = bmesh.new()
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.14, 0.45 + co.z * 0.92, co.y * 0.14),
        bevel_offset=0.014,
        segments=2,
    )
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.44, 0.89 + co.z * 0.06, co.y * 0.56),
        bevel_offset=0.010,
        segments=2,
    )
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.22, 0.06 + co.z * 0.12, co.y * 0.22),
        bevel_offset=0.010,
        segments=2,
    )

    bmesh.ops.recalc_face_normals(bm_post, faces=bm_post.faces)
    mesh_post = bpy.data.meshes.new("Mailbox_Post_Mesh")
    bm_post.to_mesh(mesh_post)
    bm_post.free()

    obj_post = bpy.data.objects.new("Mailbox_Post", mesh_post)
    bpy.context.collection.objects.link(obj_post)
    obj_post.data.materials.append(materials["wood_post"])
    shade_smooth_with_normals(obj_post)

    # 2. Rounded arched vintage mailbox body
    bm_body = bmesh.new()
    segs_arch = 22
    segs_len = 8
    mb_w = 0.42
    mb_h = 0.40
    mb_l = 0.56
    base_y = 0.92

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
        row = []
        for px, py in profile_pts:
            row.append(bm_body.verts.new(to_world(px, base_y + py, lz)))
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

    bmesh.ops.recalc_face_normals(bm_body, faces=bm_body.faces)
    mesh_body = bpy.data.meshes.new("Mailbox_Body_Mesh")
    bm_body.to_mesh(mesh_body)
    bm_body.free()

    obj_body = bpy.data.objects.new("Mailbox_Body", mesh_body)
    bpy.context.collection.objects.link(obj_body)
    obj_body.data.materials.append(materials["mailbox_forest_metal"])
    shade_smooth_with_normals(obj_body)

    # 3. Articulated Mailbox Door (slightly ajar so the cream letter peeks out invitingly)
    bm_door = bmesh.new()
    door_thick = 0.036
    door_tilt = math.radians(24.0)
    hinge_y = base_y + 0.02
    hinge_z = mb_l * 0.5

    def door_point(px, py, dz):
        dy = py * 0.95
        # Rotate forward around bottom hinge by door_tilt
        ry = dy * math.cos(door_tilt) - dz * math.sin(door_tilt)
        rz = dy * math.sin(door_tilt) + dz * math.cos(door_tilt)
        return to_world(px * 0.95, hinge_y + ry, hinge_z + rz)

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

    bmesh.ops.recalc_face_normals(bm_door, faces=bm_door.faces)
    mesh_door = bpy.data.meshes.new("Mailbox_Door_Mesh")
    bm_door.to_mesh(mesh_door)
    bm_door.free()

    obj_door = bpy.data.objects.new("Mailbox_Door", mesh_door)
    bpy.context.collection.objects.link(obj_door)
    obj_door.data.materials.append(materials["champagne_brass"])
    shade_smooth_with_normals(obj_door)

    # 4. Emerging folded cream letter peeking out of the mailbox opening
    bm_letter = bmesh.new()
    add_beveled_box(
        bm_letter,
        lambda co: to_world(co.x * 0.25, base_y + 0.21 + co.z * 0.032 - co.y * 0.04, 0.20 + co.y * 0.28),
        bevel_offset=0.004,
        segments=2,
    )
    bmesh.ops.recalc_face_normals(bm_letter, faces=bm_letter.faces)
    mesh_letter = bpy.data.meshes.new("Mailbox_Letter_Mesh")
    bm_letter.to_mesh(mesh_letter)
    bm_letter.free()

    obj_letter = bpy.data.objects.new("Mailbox_Letter", mesh_letter)
    bpy.context.collection.objects.link(obj_letter)
    obj_letter.data.materials.append(materials["ivory_lettering"])
    shade_smooth_with_normals(obj_letter)

    # 5. Raised side brass signal flag
    bm_flag = bmesh.new()
    add_beveled_box(
        bm_flag,
        lambda co: to_world(mb_w * 0.54 + co.x * 0.025, base_y + 0.30 + co.z * 0.26, 0.06 + co.y * 0.05),
        bevel_offset=0.004,
        segments=1,
    )
    add_beveled_box(
        bm_flag,
        lambda co: to_world(mb_w * 0.54 + co.x * 0.028, base_y + 0.40 + co.z * 0.09, 0.12 + co.y * 0.14),
        bevel_offset=0.004,
        segments=1,
    )
    bmesh.ops.recalc_face_normals(bm_flag, faces=bm_flag.faces)
    mesh_flag = bpy.data.meshes.new("Mailbox_Flag_Mesh")
    bm_flag.to_mesh(mesh_flag)
    bm_flag.free()

    obj_flag = bpy.data.objects.new("Mailbox_Flag", mesh_flag)
    bpy.context.collection.objects.link(obj_flag)
    obj_flag.data.materials.append(materials["champagne_brass"])
    shade_smooth_with_normals(obj_flag)


def build_rocks_ferns_and_flowers(materials):
    """Builds sculpted mossy boulders, multi-frond fern clusters, shrubs, and wildflower blossoms."""
    bm_rocks = bmesh.new()
    rock_placements = [
        # Stream source spring grotto & outlet cascade rocks
        (-3.65, -0.52, 0.38), (-3.45, -0.18, 0.30), (3.45, 0.92, 0.38), (3.25, 0.58, 0.28),
        # Stream bank & bridge abutment boulders
        (-2.35, 0.22, 0.26), (-1.25, -0.02, 0.24), (-0.65, 0.48, 0.21),
        (0.68, 0.08, 0.22), (1.42, 0.58, 0.25), (2.35, 0.82, 0.30),
        # Signpost & tree base boulders
        (-1.90, -0.74, 0.23), (1.90, -0.74, 0.23), (0.68, 1.28, 0.18),
        (-3.05, -1.65, 0.34), (3.05, -1.65, 0.34),
    ]
    for idx, (rx, rz, rrad) in enumerate(rock_placements):
        ry = get_terrain_height(rx, rz) - 0.04
        ret = bmesh.ops.create_icosphere(bm_rocks, subdivisions=3, radius=rrad)
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.4 + idx, p.y * 2.4 - idx, p.z * 2.4)))
            # Stylize rocks with slightly planar beveled facets
            facet = 1.0 + 0.22 * n - 0.08 * abs(p.z)
            v.co = Vector((
                rx + p.x * facet * 1.18,
                -(rz + p.y * facet * 0.96),
                ry + p.z * facet * 0.65,
            ))

    bmesh.ops.recalc_face_normals(bm_rocks, faces=bm_rocks.faces)
    mesh_rocks = bpy.data.meshes.new("Environment_Rocks_Mesh")
    bm_rocks.to_mesh(mesh_rocks)
    bm_rocks.free()

    obj_rocks = bpy.data.objects.new("Environment_Rocks", mesh_rocks)
    bpy.context.collection.objects.link(obj_rocks)
    obj_rocks.data.materials.append(materials["stone_mossy"])
    shade_smooth_with_normals(obj_rocks)

    # Sculpted Fern Rosettes & Woodland Shrubs (multi-frond botanical geometry instead of plain half-spheres)
    bm_ferns = bmesh.new()
    fern_clusters = [
        (-2.45, 1.35, 0.34, 7), (-1.75, 1.65, 0.28, 6), (1.75, 1.62, 0.30, 7),
        (2.55, 1.25, 0.32, 6), (-2.65, -0.35, 0.35, 7), (2.65, -0.25, 0.34, 7),
        (-0.85, -1.65, 0.32, 7), (0.85, -1.65, 0.32, 7), (0.0, -1.85, 0.38, 8),
        (-1.35, -0.58, 0.24, 5), (1.35, -0.58, 0.24, 5), (1.18, 1.28, 0.22, 5),
        (-0.95, 1.25, 0.25, 6),
    ]
    for c_idx, (fx, fz, f_scale, num_fronds) in enumerate(fern_clusters):
        fy = get_terrain_height(fx, fz) - 0.01
        for ifr in range(num_fronds):
            ang = (2.0 * math.pi * ifr) / num_fronds + (c_idx * 0.37)
            frond_len = f_scale * (0.88 + 0.22 * ((ifr % 2) - 0.5))
            segs = 5
            rows = []
            for iseg in range(segs + 1):
                t = iseg / segs
                r = frond_len * t
                arch_y = fy + f_scale * (0.42 * math.sin(t * math.pi * 0.82))
                w = f_scale * 0.22 * math.sin(t * math.pi)
                wx = fx + math.cos(ang) * r
                wz = fz + math.sin(ang) * r
                nx_d, nz_d = -math.sin(ang), math.cos(ang)
                v_left = bm_ferns.verts.new((wx - nx_d * w, -(wz - nz_d * w), arch_y))
                v_mid = bm_ferns.verts.new((wx, -wz, arch_y + 0.02 * f_scale))
                v_right = bm_ferns.verts.new((wx + nx_d * w, -(wz + nz_d * w), arch_y))
                rows.append((v_left, v_mid, v_right))
            for iseg in range(segs):
                l0, m0, r0 = rows[iseg]
                l1, m1, r1 = rows[iseg + 1]
                bm_ferns.faces.new((l0, m0, m1, l1))
                bm_ferns.faces.new((m0, r0, r1, m1))

    bmesh.ops.recalc_face_normals(bm_ferns, faces=bm_ferns.faces)
    mesh_ferns = bpy.data.meshes.new("Forest_Ferns_Mesh")
    bm_ferns.to_mesh(mesh_ferns)
    bm_ferns.free()

    obj_ferns = bpy.data.objects.new("Forest_Ferns", mesh_ferns)
    bpy.context.collection.objects.link(obj_ferns)
    obj_ferns.data.materials.append(materials["foliage_moss"])
    shade_smooth_with_normals(obj_ferns)

    # Wildflower Blossoms in Warm Ivory & Soft Champagne around paths and signs
    bm_flowers = bmesh.new()
    flower_spots = [
        (-1.25, -0.52), (-1.75, -0.58), (-1.45, -0.88),
        (1.25, -0.52), (1.75, -0.58), (1.45, -0.88),
        (0.68, 1.38), (1.12, 1.15), (-0.75, 1.45), (-0.52, 1.92),
        (0.55, 1.85), (-2.15, 0.95), (2.15, 1.35), (0.0, -1.55),
    ]
    for idx, (flx, flz) in enumerate(flower_spots):
        for sub in range(3):
            ox = flx + 0.14 * math.cos(idx * 2.1 + sub * 2.09)
            oz = flz + 0.14 * math.sin(idx * 2.1 + sub * 2.09)
            oy = get_terrain_height(ox, oz) + 0.06 + 0.02 * sub
            ret = bmesh.ops.create_icosphere(bm_flowers, subdivisions=2, radius=0.042)
            for v in ret["verts"]:
                v.co = Vector((ox + v.co.x, -(oz + v.co.y), oy + v.co.z * 0.65))

    bmesh.ops.recalc_face_normals(bm_flowers, faces=bm_flowers.faces)
    mesh_flowers = bpy.data.meshes.new("Wildflowers_Mesh")
    bm_flowers.to_mesh(mesh_flowers)
    bm_flowers.free()

    obj_flowers = bpy.data.objects.new("Wildflowers", mesh_flowers)
    bpy.context.collection.objects.link(obj_flowers)
    obj_flowers.data.materials.append(materials["ivory_lettering"])
    shade_smooth_with_normals(obj_flowers)


def setup_lighting_and_render_previews():
    """Configures late-afternoon forest lighting in Blender and renders verification views."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 780
    scene.render.resolution_y = 1688

    world = bpy.data.worlds.new("CrossroadsWorld")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = hex_to_rgba("#162E26")
        bg.inputs[1].default_value = 0.90

    # Warm late-afternoon sun
    sun_data = bpy.data.lights.new(name="LateAfternoonSun", type='SUN')
    sun_data.energy = 3.8
    sun_data.color = hex_to_rgba("#FFF2D6")[:3]
    sun_obj = bpy.data.objects.new(name="LateAfternoonSun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = Euler((math.radians(48), math.radians(-22), math.radians(28)), 'XYZ')

    # Soft sage fill light
    fill_data = bpy.data.lights.new(name="ForestFill", type='SUN')
    fill_data.energy = 1.45
    fill_data.color = hex_to_rgba("#B5D2C0")[:3]
    fill_obj = bpy.data.objects.new(name="ForestFill", object_data=fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Euler((math.radians(62), math.radians(35), math.radians(-140)), 'XYZ')

    cam_data = bpy.data.cameras.new(name="PreviewCamera")
    cam_data.lens = 31
    cam_obj = bpy.data.objects.new("PreviewCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    def aim_camera(cam_pos, target_pos):
        cam_obj.location = Vector(cam_pos)
        direction = Vector(target_pos) - cam_obj.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

    # Render 1: Initial Mobile Portrait View
    aim_camera((-0.30, -13.4, 7.5), (0.0, 0.0, 0.35))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_initial.png")
    bpy.ops.render.render(write_still=True)

    # Render 2: Rotated Second Angle
    aim_camera((5.4, -12.2, 7.7), (0.0, 0.0, 0.35))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_rotated.png")
    bpy.ops.render.render(write_still=True)


def main():
    clear_scene()

    materials = {
        "grass_top": make_pbr_material("Grass_Top_Mat", "#577352", roughness=0.80),
        "soil_strata": make_pbr_material("Soil_Strata_Mat", "#7C5B42", roughness=0.85),
        "rock_underside": make_pbr_material("Rock_Underside_Mat", "#4D463F", roughness=0.88),
        "pathway_earth": make_pbr_material("Pathway_Earth_Mat", "#B89B74", roughness=0.85),
        "stone_warm": make_pbr_material("Stone_Warm_Mat", "#8E877C", roughness=0.76),
        "stone_mossy": make_pbr_material("Stone_Mossy_Mat", "#6A7564", roughness=0.78),
        "stream_water": make_pbr_material("Stream_Water_Mat", "#3E848C", roughness=0.16, metallic=0.05),
        "wood_oak": make_pbr_material("Wood_Oak_Mat", "#9D6E48", roughness=0.66),
        "wood_post": make_pbr_material("Wood_Post_Mat", "#784F30", roughness=0.70),
        "wood_sign_plaque": make_pbr_material("Wood_Sign_Plaque_Mat", "#5A3820", roughness=0.60),
        "wood_bark": make_pbr_material("Wood_Bark_Mat", "#6A4B35", roughness=0.82),
        "foliage_deep": make_pbr_material("Foliage_Deep_Mat", "#1F4A3B", roughness=0.72),
        "foliage_moss": make_pbr_material("Foliage_Moss_Mat", "#4D6D49", roughness=0.74),
        "foliage_sage": make_pbr_material("Foliage_Sage_Mat", "#769173", roughness=0.75),
        "ivory_lettering": make_pbr_material(
            "Ivory_Lettering_Mat", "#F4F0E6", roughness=0.36, emission_hex="#F4F0E6", emission_strength=0.18
        ),
        "mailbox_forest_metal": make_pbr_material("Mailbox_Forest_Metal_Mat", "#1E473A", roughness=0.38, metallic=0.25),
        "champagne_brass": make_pbr_material("Champagne_Brass_Mat", "#DCC99D", roughness=0.30, metallic=0.72),
    }

    build_island_terrain(materials)
    build_pathway_and_cobbles(materials)
    build_stream_and_bridge(materials)
    build_rocks_ferns_and_flowers(materials)

    # Framing high-poly stylized trees around the northern arc & outer flanks
    # Framed within [-3.25, +3.25] so the full silhouette fits mobile portrait viewports
    # while leaving Signpost_UX, Signpost_Game, and Woodland_Mailbox 100% unobstructed.
    tree_specs = [
        ("Tree_NW_Hero", -2.95, -1.85, 1.04, -0.14, -0.08, 0),
        ("Tree_N_Left", -1.65, -2.35, 1.16, -0.08, -0.12, 1),
        ("Tree_N_Center", 0.0, -2.55, 1.24, 0.02, -0.14, 0),
        ("Tree_N_Right", 1.65, -2.35, 1.15, 0.10, -0.12, 2),
        ("Tree_NE_Hero", 2.95, -1.85, 1.05, 0.14, -0.08, 1),
        ("Tree_W_Flank", -3.28, -0.45, 0.88, -0.16, 0.04, 2),
        ("Tree_E_Flank", 3.28, -0.35, 0.88, 0.16, 0.04, 0),
    ]
    for t_name, tx, tz, t_scale, lx, lz, variant in tree_specs:
        create_sculpted_tree(t_name, tx, tz, t_scale, lx, lz, variant, materials)

    # Interactive Hero Objects
    build_signpost("Signpost_UX", "UX Portfolio", -1.52, -0.66, 16.0, -1, materials)
    build_signpost("Signpost_Game", "Game Portfolio", 1.52, -0.66, -16.0, 1, materials)
    build_woodland_mailbox(0.90, 1.20, -16.0, materials)

    # Export glTF / GLB runtime asset before adding Blender preview camera/lights
    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
    )
    print(f"Exported runtime GLB to: {GLB_OUT}")

    setup_lighting_and_render_previews()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved master Blender source to: {BLEND_OUT}")


if __name__ == "__main__":
    main()
