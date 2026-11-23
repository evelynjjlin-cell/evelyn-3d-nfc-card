"""
Blender 5.0 High-Fidelity Stylized Environment Authoring Script (V2 Art Direction Overhaul)
Project: The Crossroads — Two Paths, One Designer (Evelyn Lin)

Major V2 Art Upgrades:
1. Three distinct sculpted tree archetypes (Ancient Gnarled Oak, Slender Stream Birch, Layered Woodland Cedar)
   with root-flared grooved trunks, visible secondary branches, and 20-32 smaller varied organic foliage clusters
   with baked 3D vertex-color sunlight & ambient occlusion gradients (no stacked geometric sphere tiers).
2. Asymmetric, multi-elevation sculpted floating island with craggy rock buttresses, irregular overhanging turf,
   protruding rock outcrops, and hanging roots (eliminating the flat layered-cake appearance).
3. Sculpted shallow creek channel with varied width, pebble riverbed, submerged stones, and mossy banks.
4. Stone-and-timber bridge abutments physically integrating the arched oak bridge into the branching pathways.
5. Artisanal wooden signposts with iron joinery straps, recessed plaque frames, and refined wayfinding lettering.
6. Hero-prop woodland mailbox on a dedicated cobblestone alcove with corbel brace, riveted hood, handle, hinge,
   emerging wax-sealed letter, and signal flag.
7. Diverse botanical ground cover: multi-blade 3D grass clumps, asymmetric fern fronds, moss cushions, and
   stemmed petal wildflowers.
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

random.seed(108)


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


def finalize_mesh_object(name, bm, material, color_fn=None, remesh_voxel=None):
    """Converts a BMesh to a smooth-shaded Blender object with optional voxel remesh fusion and vertex colors."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    if remesh_voxel is not None and remesh_voxel > 0:
        bpy.context.view_layer.objects.active = obj
        mod_remesh = obj.modifiers.new(name="VoxelFusion", type='REMESH')
        mod_remesh.mode = 'VOXEL'
        mod_remesh.voxel_size = remesh_voxel
        mod_remesh.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier=mod_remesh.name)

        mod_smooth = obj.modifiers.new(name="OrganicSmooth", type='CORRECTIVE_SMOOTH')
        mod_smooth.factor = 0.65
        mod_smooth.iterations = 6
        mod_smooth.smooth_type = 'LENGTH_WEIGHTED'
        bpy.ops.object.modifier_apply(modifier=mod_smooth.name)

        mod_dec = obj.modifiers.new(name="OptimizePoly", type='DECIMATE')
        mod_dec.ratio = 0.42
        bpy.ops.object.modifier_apply(modifier=mod_dec.name)

        mesh = obj.data
        # Subtle organic surface leaf-tuft displacement after fusion
        for v in mesh.vertices:
            n_leaf = noise.noise(Vector((v.co.x * 3.6, v.co.y * 3.6, v.co.z * 3.6)))
            v.co += v.normal * (0.022 * n_leaf)
        mesh.update()

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
        )


# ==============================================================================
# SPATIAL & TERRAIN FUNCTIONS (Asymmetric Landform with Creek Valley & Ridges)
# ==============================================================================

def island_rim_point(angle):
    """Asymmetric organic island silhouette with rocky headlands and creek coves."""
    rx_base = (
        4.35
        + 0.28 * math.cos(angle * 2.0 - 0.3)
        + 0.19 * math.sin(angle * 3.0 - 0.5)
        - 0.14 * math.cos(angle * 4.0 + 0.7)
        + 0.08 * math.sin(angle * 5.0)
    )
    rz_base = (
        3.32
        + 0.24 * math.sin(angle * 2.0 + 0.4)
        - 0.16 * math.cos(angle * 3.0)
        + 0.11 * math.sin(angle * 4.0 - 0.8)
    )
    x = math.cos(angle) * rx_base - 0.12
    z = math.sin(angle) * rz_base - 0.14 * math.cos(angle)
    return x, z


def island_radial_factor(x, z):
    ang = math.atan2(z + 0.08, x + 0.12)
    rim_x, rim_z = island_rim_point(ang)
    rim_r = math.hypot(rim_x + 0.12, rim_z + 0.08)
    cur_r = math.hypot(x + 0.12, z + 0.08)
    return cur_r / max(1e-4, rim_r)


def stream_center_z(x):
    """Natural S-bend shallow creek centerline Z as a function of X."""
    return 0.26 + 0.17 * x + 0.32 * math.sin(x * 0.68 - 0.15) + 0.07 * math.cos(x * 1.45)


def stream_half_width(x):
    """Varied creek width: wider near spring pool, narrower under bridge, wider in east riffle."""
    bridge_pinch = 1.0 - 0.28 * math.exp(-(x ** 2) / 0.55)
    pool_swell = 1.0 + 0.32 * math.exp(-((x + 2.1) ** 2) / 0.9) + 0.22 * math.exp(-((x - 1.9) ** 2) / 1.1)
    return 0.34 * bridge_pinch * pool_swell


def path_distance_and_branch(x, z):
    """Returns (min_distance_to_path, branch_elevation_bias)."""
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

    # Continuous path from south entry (0.0, 2.38) across bridge (0.0, 0.26) to fork (0.0, -0.22)
    d_main = seg_dist(x, z, 0.0, 2.38, 0.0, -0.22)
    # Left branch climbing northwest toward UX Portfolio sign
    d_left = seg_dist(x, z, 0.0, -0.22, -2.55, -1.58)
    # Right branch curving northeast toward Game Portfolio sign
    d_right = seg_dist(x, z, 0.0, -0.22, 2.55, -1.50)
    return min(d_main, d_left, d_right)


def get_terrain_height(x, z):
    """
    Multi-elevation sculpted landscape heightmap:
    - Raised asymmetric knolls on NW (-2.4, -2.0) and NE (+2.4, -1.9)
    - Gently elevated central crossroads clearing north of the creek
    - Sculpted creek channel with natural bank shoulders
    - Integrated earth abutments on both ends of the wooden bridge
    """
    rf = island_radial_factor(x, z)

    # Asymmetric hills & knolls
    nw_hill = 0.52 * math.exp(-((x + 2.45) ** 2 / 3.2 + (z + 1.95) ** 2 / 2.6))
    ne_hill = 0.44 * math.exp(-((x - 2.35) ** 2 / 3.0 + (z + 1.85) ** 2 / 2.5))
    north_ridge = 0.32 * math.exp(-((x + 0.3) ** 2 / 5.5 + (z + 2.55) ** 2 / 2.2))
    sw_mound = 0.22 * math.exp(-((x + 2.25) ** 2 / 2.4 + (z - 1.25) ** 2 / 2.0))
    se_knoll = 0.19 * math.exp(-((x - 2.30) ** 2 / 2.6 + (z - 1.55) ** 2 / 1.8))

    # Multi-octave organic terrain undulation
    n1 = noise.noise(Vector((x * 0.42 + 4.2, z * 0.42 - 2.8, 1.1))) * 0.12
    n2 = noise.noise(Vector((x * 1.05 - 1.9, z * 1.05 + 3.4, 2.7))) * 0.045

    # Creek channel carving with raised mossy bank shoulders
    sz = stream_center_z(x)
    hw = stream_half_width(x)
    d_stream = abs(z - sz)
    stream_cut = 0.44 * math.exp(-((d_stream / (hw * 1.32)) ** 2.2))
    bank_shoulder = 0.06 * math.exp(-(((d_stream - hw * 1.45) / 0.28) ** 2))

    # Bridge abutment mounds at x=0, z=sz ± 0.56 so path meets bridge deck seamlessly
    abutment_south = 0.11 * math.exp(-((x ** 2) / 0.28 + ((z - (sz + 0.58)) ** 2) / 0.14))
    abutment_north = 0.11 * math.exp(-((x ** 2) / 0.28 + ((z - (sz - 0.58)) ** 2) / 0.14))

    # Subtle worn recess along the footpaths (except across the bridge span itself)
    d_path = path_distance_and_branch(x, z)
    on_bridge = math.exp(-((x ** 2) / 0.35 + ((z - sz) ** 2) / 0.30))
    path_cut = 0.055 * math.exp(-(d_path ** 2) / 0.22) * (1.0 - on_bridge)

    # Asymmetric organic turf rim roll-off
    edge_roll = 0.0
    if rf > 0.74:
        t = min(1.18, (rf - 0.74) / 0.26)
        ang = math.atan2(z, x)
        cliff_var = 0.85 + 0.28 * math.sin(ang * 3.0 + 0.6)
        edge_roll = -0.38 * (t ** 2.0) * cliff_var

    return (
        0.18
        + nw_hill
        + ne_hill
        + north_ridge
        + sw_mound
        + se_knoll
        + n1
        + n2
        + bank_shoulder
        + abutment_south
        + abutment_north
        - stream_cut
        - path_cut
        + edge_roll
    )


# ==============================================================================
# 1. SCULPTED FLOATING ISLAND TERRAIN & ROCKY CLIFF OUTCROPS (NO LAYERED CAKE)
# ==============================================================================

def build_island_terrain(materials):
    """
    Builds the sculpted upper terrain with irregular draping turf lip, craggy rock underside
    with protruding cliff buttresses, and emergent rock outcrops breaking through the rim.
    """
    bm_top = bmesh.new()
    rings = 64
    segs = 144

    center_y = get_terrain_height(0.0, 0.0)
    center_vert = bm_top.verts.new((0.0, 0.0, center_y))

    ring_verts = []
    for ir in range(1, rings + 1):
        u = ir / rings
        r_frac = math.sin(u * math.pi * 0.5) if u > 0.68 else u * (math.sin(0.68 * math.pi * 0.5) / 0.68)
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            wx = rim_x * r_frac
            wz = rim_z * r_frac
            wy = get_terrain_height(wx, wz)

            # Irregular draping turf lip that varies organically around the perimeter
            if ir >= rings - 3:
                lip_t = (ir - (rings - 3)) / 3.0
                drape_noise = noise.noise(Vector((wx * 1.1, wz * 1.1, 0.5)))
                drape_depth = 0.12 * (0.75 + 0.55 * drape_noise)
                wy -= drape_depth * (lip_t ** 1.5)
                # Pull outer turf edge slightly inward/outward unevenly
                flare = 1.0 + 0.015 * drape_noise * lip_t
                wx *= flare
                wz *= flare
            row.append(bm_top.verts.new((wx, -wz, wy)))
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

    # Rich vertex-color terrain splat shader (meadow grass, creek moss, sunlit ridge, pathside loam)
    c_moss_deep = hex_to_rgba("#385A3E")
    c_grass_mid = hex_to_rgba("#587850")
    c_grass_sun = hex_to_rgba("#7A9866")
    c_earth_loam = hex_to_rgba("#765A40")

    def terrain_color_fn(wx, wy, wz, nx, ny, nz):
        sz = stream_center_z(wx)
        d_stream = abs(wz - sz)
        d_path = path_distance_and_branch(wx, wz)
        rf = island_radial_factor(wx, wz)
        n_c = noise.noise(Vector((wx * 0.8 + 1.3, wz * 0.8 - 2.1, wy)))

        # Base blend from mid grass to sunlit ridge grass
        h_factor = max(0.0, min(1.0, (wy - 0.12) / 0.55 + 0.25 * n_c))
        col = lerp_color(c_grass_mid, c_grass_sun, h_factor)

        # Lush dark moss along the creek banks
        moss_factor = math.exp(-(d_stream ** 2) / 0.65)
        col = lerp_color(col, c_moss_deep, moss_factor * 0.72)

        # Warm earth transition along pathway edges and outer draping lip
        path_edge = math.exp(-((d_path - 0.35) ** 2) / 0.08) * 0.42
        rim_earth = max(0.0, (rf - 0.86) / 0.14) * 0.65
        col = lerp_color(col, c_earth_loam, min(0.85, path_edge + rim_earth))
        return col

    finalize_mesh_object("Island_Terrain_Top", bm_top, materials["grass_top"], terrain_color_fn)

    # Unified Sculpted Craggy Rock & Earth Underside (NO horizontal cake bands!)
    bm_rock = bmesh.new()
    rock_rings = 36
    rock_rows = []
    for ir in range(rock_rings + 1):
        t = ir / rock_rings
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            top_y = get_terrain_height(rim_x, rim_z) - 0.04

            # Vertical craggy buttress ribs & natural cliff shelves visible from the 3/4 camera view
            buttress = 0.075 * math.sin(ang * 7.0 + t * 1.8) + 0.045 * math.cos(ang * 11.0 - t * 2.5)
            n_crag1 = noise.noise(Vector((rim_x * 0.72 + 1.4, rim_z * 0.72 - 2.2, t * 2.8)))
            n_crag2 = noise.noise(Vector((rim_x * 1.60 - 0.8, rim_z * 1.60 + 1.9, t * 5.5)))

            # Upper cliff wall stays wide before tapering into a craggy central spire below
            ledge_step = 0.035 * math.sin(t * math.pi * 3.0 + n_crag1 * 2.0) * (1.0 - t)
            taper = (1.005 - (t ** 2.15) * 0.90) + buttress * (1.0 - t * 0.5) * min(1.0, t * 2.2) + ledge_step

            rx = rim_x * max(0.03, taper)
            rz = rim_z * max(0.03, taper)

            radial_disp = (0.20 * n_crag1 + 0.08 * n_crag2) * (1.0 - t * 0.35) * min(1.0, t * 3.0)
            dir_len = max(1e-4, math.hypot(rim_x, rim_z))
            rx += (rim_x / dir_len) * radial_disp
            rz += (rim_z / dir_len) * radial_disp

            depth_scale = 2.30 + 0.32 * math.sin(ang - 1.1) + 0.20 * math.cos(ang * 3.0)
            ry = top_y - (depth_scale * (t ** 1.04)) + 0.12 * n_crag1 * (1.0 - t * 0.4)

            row.append(bm_rock.verts.new((rx, -rz, ry)))
        rock_rows.append(row)

    # Cap the bottom apex cleanly
    bottom_apex = bm_rock.verts.new((-0.12, 0.15, -2.42))

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
        soil_blend = max(0.0, min(1.0, (wy + 0.36 + 0.25 * n_v) / 0.38))
        depth_ao = max(0.0, min(1.0, (-wy - 0.15) / 1.95))
        col = lerp_color(c_rock_mid, c_rock_deep, depth_ao)
        col = lerp_color(col, c_soil_top, soil_blend)
        if ny > 0.22 and wy > -1.05:
            col = lerp_color(col, c_rock_moss, min(0.68, (ny - 0.22) * 1.25))
        return col

    finalize_mesh_object("Island_Rock_Underside", bm_rock, materials["rock_underside"], rock_color_fn)

    # Build Sculpted Cliff Ledges & Hanging Root Systems tucked naturally under the cliff face
    bm_outcrops = bmesh.new()
    outcrop_specs = [
        # Integrated cliff buttress ledges tucked beneath the grass rim (y_offset < -0.22)
        (-0.42, 0.93, -0.34, 0.52, 0.26, 0.36),
        (-1.15, 0.92, -0.42, 0.58, 0.28, 0.38),
        (-2.15, 0.93, -0.38, 0.54, 0.26, 0.36),
        (2.35, 0.93, -0.36, 0.50, 0.25, 0.34),
        (0.85, 0.92, -0.40, 0.52, 0.25, 0.35),
        (1.65, 0.93, -0.45, 0.48, 0.24, 0.32),
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
            chisel = 1.0 + 0.24 * n - 0.14 * abs(p.z)
            v.co = Vector((
                ox + p.x * sx * chisel,
                -(oz + p.y * sz_r * chisel),
                oy + p.z * sy * chisel,
            ))

    # Hanging root tendrils underneath the turf overhang
    root_angles = [-1.85, -1.15, -0.42, 0.48, 1.35, 2.15, 2.75]
    for r_idx, ang in enumerate(root_angles):
        rim_x, rim_z = island_rim_point(ang)
        rx_start = rim_x * 0.95
        rz_start = rim_z * 0.95
        ry_start = get_terrain_height(rx_start, rz_start) - 0.14
        segs_r = 7
        cols_r = 6
        rows_r = []
        for ir in range(segs_r + 1):
            t = ir / segs_r
            rad = 0.048 * (1.0 - 0.82 * t)
            cx = rx_start * (1.0 - 0.06 * t) + 0.05 * math.sin(t * 5.0 + r_idx)
            cz = rz_start * (1.0 - 0.06 * t) + 0.05 * math.cos(t * 4.5 - r_idx)
            cy = ry_start - 0.68 * (t ** 1.15)
            row = []
            for ic in range(cols_r):
                a = (2.0 * math.pi * ic) / cols_r
                row.append(bm_outcrops.verts.new((cx + math.cos(a) * rad, -(cz + math.sin(a) * rad), cy)))
            rows_r.append(row)
        for ir in range(segs_r):
            for ic in range(cols_r):
                nic = (ic + 1) % cols_r
                bm_outcrops.faces.new((
                    rows_r[ir][ic],
                    rows_r[ir][nic],
                    rows_r[ir + 1][nic],
                    rows_r[ir + 1][ic],
                ))

    finalize_mesh_object("Island_Soil_Rim", bm_outcrops, materials["rock_underside"], rock_color_fn)


# ==============================================================================
# 2. THREE DISTINCT HIGH-FIDELITY TREE ARCHETYPES (NO STACKED SPHERES)
# ==============================================================================

def add_foliage_cluster_lobe(bm, cx, cy, cz, rx, ry, rz, yaw, pitch, seed_val):
    """
    Creates an organic, leaf-tufted foliage cluster with ruffled leaf-clump displacement
    rather than a smooth primitive sphere.
    """
    ret = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    cy_cos, cy_sin = math.cos(yaw), math.sin(yaw)
    cp_cos, cp_sin = math.cos(pitch), math.sin(pitch)

    for v in ret["verts"]:
        p = v.co
        # Multi-frequency leaf-clump sculpting
        n_broad = noise.noise(Vector((p.x * 1.7 + seed_val, p.y * 1.7 - seed_val, p.z * 1.7)))
        n_tuft = abs(noise.noise(Vector((p.x * 3.8 - seed_val, p.y * 3.8 + seed_val, p.z * 3.8))))
        disp = 1.0 + 0.18 * n_broad + 0.14 * (n_tuft - 0.35)

        # Slightly scalloped bottom, billowy leaf-tufted crown top
        y_shape = 1.08 if p.z >= 0 else 0.64
        lx = p.x * rx * disp
        lz = p.y * rz * disp
        ly = p.z * ry * disp * y_shape

        # Pitch & yaw rotation so clusters orient along branch growth directions
        ly_p = ly * cp_cos - lz * cp_sin
        lz_p = ly * cp_sin + lz * cp_cos
        wx = cx + lx * cy_cos + lz_p * cy_sin
        wz = cz - lx * cy_sin + lz_p * cy_cos
        wy = cy + ly_p
        v.co = Vector((wx, -wz, wy))


def add_curved_branch_tube(bm, points_xyz_rad, segs=12, bark_groove_amp=0.04):
    """Builds a smooth curved trunk or branch tube along a sequence of (x, y, z, radius) control points."""
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
            # Root buttress flare near base (t < 0.28) + twisted bark ridges
            flair = 1.0 + (0.34 * max(0.0, 1.0 - t * 3.6) * math.cos(ang * 4.0 + px))
            groove = 1.0 + bark_groove_amp * math.sin(ang * 6.0 + t * 5.0)
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


def make_foliage_color_fn(tree_x, tree_y_base, tree_z, palette_mode):
    """
    Computes rich 3D vertex color with sunlit top highlights, inner-canopy ambient occlusion,
    and per-cluster botanical hue variation.
    """
    if palette_mode == 0:  # Deep Emerald & Sunlit Sage Oak
        c_shadow = hex_to_rgba("#16382B")
        c_mid = hex_to_rgba("#386546")
        c_sun = hex_to_rgba("#7FA368")
    elif palette_mode == 1:  # Warm Golden-Moss & Olive Birch
        c_shadow = hex_to_rgba("#274734")
        c_mid = hex_to_rgba("#557A4E")
        c_sun = hex_to_rgba("#9CB678")
    else:  # Cool Pine & Alpine Spruce Cedar
        c_shadow = hex_to_rgba("#14332A")
        c_mid = hex_to_rgba("#2E5947")
        c_sun = hex_to_rgba("#688E6C")

    sun_dir = Vector((0.52, 0.74, 0.42)).normalized()

    def color_fn(wx, wy, wz, nx, ny, nz):
        norm = Vector((nx, ny, nz)).normalized()
        sun_dot = max(0.0, norm.dot(sun_dir))
        height_t = max(0.0, min(1.0, (wy - (tree_y_base + 1.1)) / 1.85))
        n_cluster = noise.noise(Vector((wx * 1.4, wy * 1.4, wz * 1.4)))

        # Interior ambient occlusion near trunk core
        radial_d = math.hypot(wx - tree_x, wz - tree_z)
        core_ao = max(0.0, min(1.0, (radial_d - 0.25) / 0.85))

        light_val = max(0.0, min(1.0, 0.35 * height_t + 0.50 * sun_dot + 0.15 * core_ao + 0.14 * n_cluster))
        if light_val < 0.48:
            return lerp_color(c_shadow, c_mid, light_val / 0.48)
        return lerp_color(c_mid, c_sun, (light_val - 0.48) / 0.52)

    return color_fn


def make_bark_color_fn(is_birch=False):
    if is_birch:
        c_base = hex_to_rgba("#9E9180")
        c_dark = hex_to_rgba("#4A4138")
        c_moss = hex_to_rgba("#4A6344")
    else:
        c_base = hex_to_rgba("#6E4F38")
        c_dark = hex_to_rgba("#3D2B1E")
        c_moss = hex_to_rgba("#445E3E")

    def color_fn(wx, wy, wz, nx, ny, nz):
        n_b = noise.noise(Vector((wx * 2.5, wy * 4.0, wz * 2.5)))
        col = lerp_color(c_dark, c_base, 0.45 + 0.45 * max(0.0, nx * 0.5 + ny * 0.5) + 0.2 * n_b)
        if is_birch:
            # Horizontal birch bark lenticel markings
            band = math.sin(wy * 22.0 + n_b * 4.0)
            if band > 0.72:
                col = lerp_color(col, c_dark, 0.65)
        # Moss creeping up the lower trunk base
        if wy < 0.72:
            moss_t = max(0.0, (0.72 - wy) / 0.45) * (0.6 + 0.4 * n_b)
            col = lerp_color(col, c_moss, min(0.75, moss_t))
        return col

    return color_fn


def create_tree_archetype_oak(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Archetype 1: Gnarled Ancient Woodland Oak.
    Broad, sweeping multi-limb boughs with visible secondary branches and 22 varied leaf clusters.
    """
    y0 = get_terrain_height(x, z) - 0.06
    bm_trunk = bmesh.new()

    # S-curved gnarled main trunk
    trunk_pts = []
    steps = 11
    h = 1.65 * scale
    for i in range(steps + 1):
        t = i / steps
        rad = (0.25 * (1.0 - 0.55 * (t ** 0.75)) + 0.08 * math.exp(-t * 6.0)) * scale
        px = x + (lean_x * (t ** 1.3) + 0.07 * math.sin(t * math.pi * 1.4)) * scale
        pz = z + (lean_z * (t ** 1.3) - 0.05 * math.sin(t * math.pi)) * scale
        py = y0 + h * t
        trunk_pts.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, trunk_pts, segs=14, bark_groove_amp=0.055)

    top_x, top_y, top_z, _ = trunk_pts[-1]

    # 5 major diverging oak limbs + sub-branches
    bough_specs = [
        (-0.78, 0.58, 0.22, 0.11, -0.35),
        (0.74, 0.54, -0.18, 0.11, 0.32),
        (-0.28, 0.76, -0.58, 0.10, -0.18),
        (0.34, 0.72, 0.52, 0.095, 0.24),
        (0.04, 0.92, -0.08, 0.09, 0.05),
    ]
    bough_tips = []
    for bx_d, by_d, bz_d, b_rad, start_offset in bough_specs:
        sx = x + lean_x * 0.75 * scale
        sy = y0 + h * (0.72 + abs(start_offset) * 0.35)
        sz = z + lean_z * 0.75 * scale
        b_pts = []
        for ib in range(7):
            tb = ib / 6.0
            r_b = b_rad * (1.0 - 0.68 * tb) * scale
            px = sx + bx_d * (tb ** 1.08) * scale
            py = sy + (by_d * (tb ** 0.82) + 0.06 * math.sin(tb * math.pi)) * scale
            pz = sz + bz_d * (tb ** 1.08) * scale
            b_pts.append((px, py, pz, r_b))
        add_curved_branch_tube(bm_trunk, b_pts, segs=10, bark_groove_amp=0.03)
        bough_tips.append(b_pts[-1][:3])

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(False))

    # 22 varied, asymmetric leaf-cluster boughs arranged around the 5 limb tips (with sky gaps!)
    bm_canopy = bmesh.new()
    cluster_offsets = [
        # Around Bough 0 (Left-Front)
        (0, 0.0, 0.04, 0.0, 0.44, 0.28, 0.40, 0.2, 0.1),
        (0, -0.26, -0.06, 0.14, 0.35, 0.23, 0.32, 0.5, -0.12),
        (0, 0.18, 0.16, 0.18, 0.32, 0.22, 0.30, -0.3, 0.08),
        (0, -0.14, 0.18, -0.22, 0.34, 0.24, 0.32, 0.1, 0.15),
        # Around Bough 1 (Right-Back)
        (1, 0.0, 0.05, 0.0, 0.43, 0.27, 0.39, -0.25, -0.1),
        (1, 0.25, -0.05, -0.12, 0.34, 0.22, 0.31, 0.4, 0.12),
        (1, -0.16, 0.15, -0.20, 0.33, 0.22, 0.30, -0.4, -0.08),
        (1, 0.15, 0.18, 0.20, 0.32, 0.23, 0.29, 0.2, -0.14),
        # Around Bough 2 (Back-Left)
        (2, 0.0, 0.04, 0.0, 0.42, 0.27, 0.38, 0.3, 0.08),
        (2, -0.24, -0.04, -0.18, 0.34, 0.22, 0.32, -0.2, 0.14),
        (2, 0.18, 0.14, -0.22, 0.32, 0.21, 0.30, 0.6, -0.1),
        (2, -0.10, 0.22, 0.12, 0.30, 0.20, 0.28, -0.5, 0.05),
        # Around Bough 3 (Front-Right)
        (3, 0.0, 0.04, 0.0, 0.40, 0.26, 0.36, -0.35, -0.08),
        (3, 0.22, -0.06, 0.16, 0.32, 0.21, 0.30, 0.25, 0.12),
        (3, -0.15, 0.14, 0.18, 0.30, 0.20, 0.28, -0.15, -0.12),
        (3, 0.12, 0.18, -0.14, 0.29, 0.20, 0.27, 0.45, 0.06),
        # Around Bough 4 (Upper Crown Apex — Asymmetric)
        (4, 0.0, 0.06, 0.0, 0.45, 0.29, 0.41, 0.15, 0.05),
        (4, -0.26, 0.02, 0.10, 0.36, 0.24, 0.33, -0.3, 0.12),
        (4, 0.24, 0.04, -0.12, 0.35, 0.23, 0.32, 0.35, -0.10),
        (4, -0.08, 0.24, -0.06, 0.33, 0.22, 0.31, -0.1, 0.08),
        (4, 0.14, 0.20, 0.15, 0.28, 0.19, 0.26, 0.5, -0.06),
        (4, -0.20, -0.12, -0.22, 0.31, 0.21, 0.29, -0.4, 0.10),
    ]
    for c_idx, (b_idx, dx, dy, dz, rx, ry, rz, yaw, pitch) in enumerate(cluster_offsets):
        bx, by, bz = bough_tips[b_idx]
        add_foliage_cluster_lobe(
            bm_canopy,
            bx + dx * scale,
            by + dy * scale,
            bz + dz * scale,
            rx * scale,
            ry * scale,
            rz * scale,
            yaw,
            pitch,
            seed_val=c_idx * 1.7 + x,
        )

    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
        remesh_voxel=0.062,
    )


def create_tree_archetype_birch(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Archetype 2: Slender Multi-Stem Stream Birch / Alder.
    Graceful leaning twin trunks with pale lenticel bark and airy, layered foliage clusters at varied heights.
    """
    y0 = get_terrain_height(x, z) - 0.05
    bm_trunk = bmesh.new()

    # Main slender leaning stem
    h_main = 1.95 * scale
    pts_main = []
    for i in range(12):
        t = i / 11.0
        rad = (0.14 * (1.0 - 0.65 * (t ** 0.8)) + 0.04 * math.exp(-t * 7.0)) * scale
        px = x + (lean_x * (t ** 1.25) + 0.09 * math.sin(t * math.pi)) * scale
        pz = z + (lean_z * (t ** 1.25) + 0.04 * math.cos(t * math.pi)) * scale
        py = y0 + h_main * t
        pts_main.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts_main, segs=12, bark_groove_amp=0.02)

    # Secondary companion stem diverging from low base
    h_sec = 1.45 * scale
    side_sign = -1.0 if lean_x >= 0 else 1.0
    pts_sec = []
    for i in range(10):
        t = i / 9.0
        rad = (0.10 * (1.0 - 0.68 * t)) * scale
        px = x + (side_sign * 0.52 * (t ** 1.15)) * scale
        pz = z + (0.26 * (t ** 1.1)) * scale
        py = y0 + h_sec * (t ** 0.92)
        pts_sec.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts_sec, segs=10, bark_groove_amp=0.02)

    # 3 delicate upper branches off main stem
    branch_anchors = [
        (0.58, -0.46, 0.35, 0.18),
        (0.74, 0.44, 0.38, -0.20),
        (0.88, -0.22, 0.40, -0.25),
    ]
    sub_tips = [pts_main[-1][:3], pts_sec[-1][:3]]
    for t_anchor, dx, dy, dz in branch_anchors:
        idx_a = int(t_anchor * 11)
        ax, ay, az, _ = pts_main[idx_a]
        b_pts = []
        for ib in range(6):
            tb = ib / 5.0
            b_pts.append((
                ax + dx * tb * scale,
                ay + dy * (tb ** 0.85) * scale,
                az + dz * tb * scale,
                0.055 * (1.0 - 0.7 * tb) * scale,
            ))
        add_curved_branch_tube(bm_trunk, b_pts, segs=8, bark_groove_amp=0.015)
        sub_tips.append(b_pts[-1][:3])

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(True))

    # Airy, multi-level birch leaf clusters around the 5 tips
    bm_canopy = bmesh.new()
    birch_clusters = [
        # Tip 0 (Main top crown)
        (0, 0.0, 0.05, 0.0, 0.38, 0.24, 0.35, 0.1, 0.05),
        (0, -0.22, -0.06, 0.10, 0.30, 0.19, 0.28, -0.3, 0.12),
        (0, 0.20, -0.04, -0.10, 0.29, 0.18, 0.27, 0.4, -0.10),
        (0, 0.02, 0.18, -0.04, 0.27, 0.18, 0.25, 0.0, 0.08),
        # Tip 1 (Companion stem lower-side canopy pad)
        (1, 0.0, 0.04, 0.0, 0.35, 0.21, 0.32, -0.25, 0.10),
        (1, side_sign * 0.20, -0.05, 0.10, 0.27, 0.17, 0.25, 0.35, -0.08),
        (1, -side_sign * 0.12, 0.12, -0.10, 0.25, 0.16, 0.24, -0.15, 0.06),
        # Tip 2 (Mid-left branch)
        (2, 0.0, 0.02, 0.0, 0.33, 0.20, 0.30, 0.3, 0.10),
        (2, -0.18, -0.06, 0.08, 0.25, 0.16, 0.24, -0.2, -0.12),
        (2, 0.12, 0.10, -0.08, 0.24, 0.16, 0.22, 0.5, 0.05),
        # Tip 3 (Upper-right branch)
        (3, 0.0, 0.03, 0.0, 0.34, 0.20, 0.31, -0.3, -0.08),
        (3, 0.18, -0.05, -0.08, 0.26, 0.17, 0.24, 0.2, 0.12),
        (3, -0.10, 0.11, 0.08, 0.24, 0.15, 0.22, -0.4, -0.05),
        # Tip 4 (High back branch)
        (4, 0.0, 0.04, 0.0, 0.32, 0.20, 0.29, 0.15, 0.08),
        (4, -0.15, 0.08, -0.10, 0.25, 0.16, 0.23, -0.25, 0.10),
        (4, 0.14, -0.04, 0.09, 0.24, 0.15, 0.22, 0.35, -0.06),
    ]
    for c_idx, (t_idx, dx, dy, dz, rx, ry, rz, yaw, pitch) in enumerate(birch_clusters):
        tx, ty, tz = sub_tips[t_idx]
        add_foliage_cluster_lobe(
            bm_canopy,
            tx + dx * scale,
            ty + dy * scale,
            tz + dz * scale,
            rx * scale,
            ry * scale,
            rz * scale,
            yaw,
            pitch,
            seed_val=c_idx * 2.1 + x,
        )

    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
        remesh_voxel=0.062,
    )


def create_tree_archetype_cedar(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    """
    Archetype 3: Stylized Woodland Cedar / Spruce.
    Tall, tapered vertical conifer with swept, asymmetric drooping bough pads arranged spirally
    around a curved reddish-brown trunk (providing strong vertical silhouette contrast).
    """
    y0 = get_terrain_height(x, z) - 0.06
    bm_trunk = bmesh.new()

    h = 2.45 * scale
    pts = []
    for i in range(13):
        t = i / 12.0
        rad = (0.20 * (1.0 - 0.78 * (t ** 0.85)) + 0.06 * math.exp(-t * 6.0)) * scale
        px = x + (lean_x * (t ** 1.35) + 0.04 * math.sin(t * math.pi)) * scale
        pz = z + (lean_z * (t ** 1.35)) * scale
        py = y0 + h * t
        pts.append((px, py, pz, rad))
    add_curved_branch_tube(bm_trunk, pts, segs=12, bark_groove_amp=0.045)

    finalize_mesh_object(f"{name}_Trunk", bm_trunk, materials["wood_bark"], make_bark_color_fn(False))

    bm_canopy = bmesh.new()
    # Spiral arrangement of 19 swept, layered cedar bough clusters from mid-trunk to spire tip
    whorls = [
        # (height_frac, num_pads, radius_out, rx, ry, rz, droop_pitch, phase_deg)
        (0.40, 5, 0.44, 0.38, 0.16, 0.28, 0.24, 0.0),
        (0.55, 5, 0.36, 0.33, 0.15, 0.25, 0.20, 36.0),
        (0.70, 4, 0.28, 0.28, 0.15, 0.22, 0.16, 18.0),
        (0.84, 3, 0.18, 0.23, 0.15, 0.19, 0.12, 52.0),
        (0.96, 2, 0.07, 0.19, 0.18, 0.18, 0.04, 10.0),
    ]
    c_seed = 0
    for h_frac, n_pads, r_out, rx, ry, rz, pitch, phase_deg in whorls:
        idx_p = min(11, int(h_frac * 12))
        cx, cy, cz, _ = pts[idx_p]
        for ip in range(n_pads):
            c_seed += 1
            ang = math.radians(phase_deg) + (2.0 * math.pi * ip) / n_pads + 0.14 * math.sin(c_seed * 1.7)
            r_j = r_out * (0.88 + 0.24 * ((c_seed % 3) * 0.5))
            px = cx + math.cos(ang) * r_j * scale
            pz = cz + math.sin(ang) * r_j * scale
            py = cy + 0.05 * ((ip % 2) - 0.5) * scale
            add_foliage_cluster_lobe(
                bm_canopy,
                px,
                py,
                pz,
                rx * scale,
                ry * scale,
                rz * scale,
                yaw=-ang,
                pitch=pitch,
                seed_val=c_seed * 1.9 + x,
            )

    mat_key = ["foliage_deep", "foliage_moss", "foliage_sage"][palette_mode % 3]
    finalize_mesh_object(
        f"{name}_Canopy",
        bm_canopy,
        materials[mat_key],
        make_foliage_color_fn(x, y0, z, palette_mode),
        remesh_voxel=0.062,
    )


# ==============================================================================
# 3. INTEGRATED PATHWAYS, PEBBLE CREEK & ARCHED BRIDGE WITH ABUTMENTS
# ==============================================================================

def build_pathway_and_cobbles(materials):
    """
    Builds continuous, organically bordered woodland pathways that connect directly onto
    both ends of the arched wooden bridge and diverge genuinely across the 3D terrain.
    """
    bm_path = bmesh.new()

    def add_organic_path_ribbon(pts, half_w_start, half_w_end, taper_start=False, taper_end=False):
        rows = []
        n_pts = len(pts)
        for idx, (px, pz, y_lift) in enumerate(pts):
            t = idx / max(1, n_pts - 1)
            hw = half_w_start * (1.0 - t) + half_w_end * t
            if taper_start and t < 0.15:
                hw *= math.sin((t / 0.15) * math.pi * 0.5)
            if taper_end and t > 0.82:
                hw *= math.sin(((1.0 - t) / 0.18) * math.pi * 0.5)
            hw = max(0.05, hw)

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
                wiggle = 0.035 * math.sin(t * 13.0 + u * 2.3)
                wx = px + nx_dir * (hw + wiggle) * u
                wz = pz + nz_dir * (hw + wiggle) * u
                crown = 0.020 * (1.0 - u * u) - 0.015 * (u ** 4)
                wy = get_terrain_height(wx, wz) + 0.012 + crown + y_lift * (1.0 - 0.35 * u * u)
                row.append(bm_path.verts.new((wx, -wz, wy)))
            rows.append(row)

        for r in range(len(rows) - 1):
            for c in range(len(rows[r]) - 1):
                bm_path.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))

    sz_center = stream_center_z(0.0)  # ~0.26

    # South approach: starts at front meadow (z=2.36) and rises directly onto the south bridge abutment (z=sz+0.55)
    south_steps = 16
    south_pts = []
    for i in range(south_steps + 1):
        t = i / south_steps
        pz = 2.36 * (1.0 - t) + (sz_center + 0.50) * t
        px = 0.05 * math.sin(t * math.pi * 1.5) * (1.0 - t)
        # Smooth ramp lift at the bridge threshold
        ramp_lift = 0.055 * (t ** 3)
        south_pts.append((px, pz, ramp_lift))

    # North bridge exit into the central crossroads fork (from z=sz-0.50 to z=-0.38)
    north_steps = 8
    north_pts = []
    for i in range(north_steps + 1):
        t = i / north_steps
        pz = (sz_center - 0.50) * (1.0 - t) + (-0.36) * t
        ramp_lift = 0.055 * ((1.0 - t) ** 3)
        north_pts.append((0.0, pz, ramp_lift))

    # Left crossroads branch: climbs northwest past the UX Portfolio sign (-1.58, -0.64) toward the oak hill
    left_steps = 22
    left_pts = []
    for i in range(left_steps + 1):
        t = i / left_steps
        px = -2.42 * t - 0.14 * math.sin(t * math.pi)
        pz = -0.22 - 1.36 * (t ** 1.05)
        left_pts.append((px, pz, 0.008 * (1.0 - t)))

    # Right crossroads branch: curves northeast past the Game Portfolio sign (+1.58, -0.60) toward the cedar ridge
    right_steps = 22
    right_pts = []
    for i in range(right_steps + 1):
        t = i / right_steps
        px = 2.42 * t + 0.14 * math.sin(t * math.pi)
        pz = -0.22 - 1.28 * (t ** 1.05)
        right_pts.append((px, pz, 0.008 * (1.0 - t)))

    # Mailbox side spur connecting main south path to the mailbox cobblestone plinth at (1.18, 1.08)
    spur_pts = [
        (0.18 + 1.04 * (i / 8.0), 1.16 - 0.08 * (i / 8.0), 0.006)
        for i in range(9)
    ]

    add_organic_path_ribbon(south_pts, 0.48, 0.45, taper_start=True, taper_end=False)
    add_organic_path_ribbon(north_pts, 0.46, 0.56, taper_start=False, taper_end=False)
    add_organic_path_ribbon(left_pts, 0.44, 0.30, taper_start=False, taper_end=True)
    add_organic_path_ribbon(right_pts, 0.44, 0.30, taper_start=False, taper_end=True)
    add_organic_path_ribbon(spur_pts, 0.28, 0.36, taper_start=False, taper_end=True)

    c_path_center = hex_to_rgba("#C2A47C")
    c_path_edge = hex_to_rgba("#8A6E4E")

    def path_color_fn(wx, wy, wz, nx, ny, nz):
        d = path_distance_and_branch(wx, wz)
        n_p = noise.noise(Vector((wx * 2.2, wz * 2.2, wy)))
        t = max(0.0, min(1.0, (d / 0.42) + 0.18 * n_p))
        return lerp_color(c_path_center, c_path_edge, t)

    finalize_mesh_object("Crossroads_Pathway", bm_path, materials["pathway_earth"], path_color_fn)

    # Irregular flat sandstone stepping flagstones & border cobbles
    bm_stones = bmesh.new()
    stone_coords = [
        # South approach flagstones leading right up to the bridge deck
        (0.02, 2.16, 0.20, 0.14), (-0.12, 1.90, 0.17, 0.13), (0.11, 1.64, 0.18, 0.15),
        (-0.09, 1.38, 0.17, 0.13), (0.09, 1.12, 0.16, 0.13), (-0.04, 0.89, 0.18, 0.14),
        # Mailbox plinth cobbles
        (0.62, 1.14, 0.15, 0.12), (0.94, 1.10, 0.18, 0.15), (1.20, 1.08, 0.26, 0.22),
        # Crossroads fork & diverging branches
        (0.0, -0.34, 0.22, 0.17), (-0.42, -0.46, 0.18, 0.14), (-0.84, -0.66, 0.19, 0.14),
        (-1.25, -0.88, 0.17, 0.13), (-1.68, -1.10, 0.18, 0.14), (-2.08, -1.32, 0.15, 0.12),
        (0.42, -0.46, 0.18, 0.14), (0.84, -0.64, 0.19, 0.14), (1.25, -0.85, 0.17, 0.13),
        (1.68, -1.06, 0.18, 0.14), (2.08, -1.26, 0.15, 0.12),
    ]
    for idx, (sx, sz, rx_s, rz_s) in enumerate(stone_coords):
        sy = get_terrain_height(sx, sz) + 0.020
        ret = bmesh.ops.create_icosphere(bm_stones, subdivisions=3, radius=1.0)
        yaw = (idx * 0.83) % math.pi
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.6 + sx, p.y * 2.6 + sz, p.z * 2.6)))
            lx = p.x * rx_s * (1.0 + 0.14 * n)
            lz = p.y * rz_s * (1.0 + 0.14 * n)
            wx = sx + lx * math.cos(yaw) - lz * math.sin(yaw)
            wz = sz + lx * math.sin(yaw) + lz * math.cos(yaw)
            wy = sy + p.z * 0.032 * (1.0 if p.z > 0 else 0.45)
            v.co = Vector((wx, -wz, wy))

    c_stone_light = hex_to_rgba("#9E9588")
    c_stone_dark = hex_to_rgba("#6E685F")
    finalize_mesh_object(
        "Pathway_Cobbles",
        bm_stones,
        materials["stone_warm"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_stone_dark, c_stone_light, 0.5 + 0.35 * ny + 0.2 * noise.noise(Vector((wx * 3.0, wz * 3.0, wy)))
        ),
    )


def build_stream_and_bridge(materials):
    """
    Builds a naturalistic shallow woodland creek with varied width, pebble bed, submerged stones,
    and an arched oak bridge physically anchored into stone-and-timber bank abutments.
    """
    bm_water = bmesh.new()
    steps = 76
    cols = 13
    rows = []
    for i in range(steps + 1):
        x = -3.85 + 7.70 * (i / steps)
        cz = stream_center_z(x)
        rf = island_radial_factor(x, cz)
        if rf > 0.91:
            continue
        dx = 0.07
        dz = stream_center_z(x + dx) - cz
        length = math.hypot(dx, dz)
        nx_d, nz_d = -dz / length, dx / length

        end_taper = min(1.0, (0.91 - rf) / 0.14)
        hw = stream_half_width(x) * (0.45 + 0.55 * end_taper)
        bed_center_y = get_terrain_height(x, cz)
        water_y = bed_center_y + 0.135

        row = []
        for c in range(cols):
            u = (c / (cols - 1)) * 2.0 - 1.0
            wx = x + nx_d * hw * u
            wz = cz + nz_d * hw * u
            # Subtle flow ripples
            ripple = 0.006 * math.sin(x * 5.2 + u * 2.8) * (1.0 - 0.5 * u * u)
            row.append(bm_water.verts.new((wx, -wz, water_y + ripple)))
        rows.append(row)

    for r in range(len(rows) - 1):
        for c in range(len(rows[r]) - 1):
            bm_water.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))

    c_water_deep = hex_to_rgba("#214B47")
    c_water_shallow = hex_to_rgba("#4E7261")
    c_water_foam = hex_to_rgba("#8EB2A4")

    def water_color_fn(wx, wy, wz, nx, ny, nz):
        cz = stream_center_z(wx)
        hw = max(0.2, stream_half_width(wx))
        edge_t = min(1.0, abs(wz - cz) / hw)
        col = lerp_color(c_water_deep, c_water_shallow, edge_t ** 1.3)
        # Subtle riffle highlight near rocks and spring
        n_w = noise.noise(Vector((wx * 3.2, wz * 3.2, 0.5)))
        if n_w > 0.35 or edge_t > 0.85:
            col = lerp_color(col, c_water_foam, 0.25)
        return col

    finalize_mesh_object("Stream_Water", bm_water, materials["stream_water"], water_color_fn)

    # Handcrafted Arched Wooden Bridge + Stone & Timber Bank Abutments
    bm_bridge = bmesh.new()
    bridge_center_z = stream_center_z(0.0)
    bridge_span = 1.24
    bridge_width = 1.02
    num_planks = 11

    y_south_ground = get_terrain_height(0.0, bridge_center_z + bridge_span * 0.5)
    y_north_ground = get_terrain_height(0.0, bridge_center_z - bridge_span * 0.5)
    base_abutment_y = max(y_south_ground, y_north_ground) + 0.03

    def arch_height(z_local):
        norm = z_local / (bridge_span * 0.5)
        return base_abutment_y + 0.13 * max(0.0, 1.0 - norm * norm)

    # Timber sill beams embedded into both riverbanks at the bridge ends
    for end_sign in (-1.0, 1.0):
        wz_sill = bridge_center_z + end_sign * (bridge_span * 0.49)
        wy_sill = arch_height(end_sign * (bridge_span * 0.49)) - 0.035
        add_beveled_box(
            bm_bridge,
            lambda co, wz_sill=wz_sill, wy_sill=wy_sill: Vector((
                co.x * (bridge_width + 0.14),
                -(wz_sill + co.y * 0.15),
                wy_sill + co.z * 0.11,
            )),
            bevel_offset=0.012,
            segments=2,
        )

    # Two arched timber stringer beams spanning between the bank sills
    for side in (-0.39, 0.39):
        segs = 14
        beam_verts = []
        for i in range(segs + 1):
            zl = -bridge_span * 0.50 + bridge_span * 1.00 * (i / segs)
            wz = bridge_center_z + zl
            wy = arch_height(zl) - 0.038
            beam_verts.append((side, wz, wy))
        for i in range(segs):
            x0, z0, y0 = beam_verts[i]
            x1, z1, y1 = beam_verts[i + 1]
            ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
            for v in ret["verts"]:
                t = v.co.y + 0.5
                vx = x0 + v.co.x * 0.088
                vz = z0 * (1 - t) + z1 * t
                vy = (y0 * (1 - t) + y1 * t) + v.co.z * 0.078
                v.co = Vector((vx, -vz, vy))

    # 11 individual beveled oak deck planks with slight organic irregularity
    for ip in range(num_planks):
        u = (ip / (num_planks - 1)) * 2.0 - 1.0
        zl = u * (bridge_span * 0.45)
        wz = bridge_center_z + zl
        wy = arch_height(zl) + 0.018
        slope = -0.21 * u
        w_var = bridge_width * (0.99 + 0.02 * math.sin(ip * 2.3))

        def plank_tf(co, wz=wz, wy=wy, slope=slope, w_var=w_var):
            px = co.x * w_var
            pz = co.y * 0.095
            py = co.z * 0.046
            rz = pz * math.cos(slope) - py * math.sin(slope)
            ry = pz * math.sin(slope) + py * math.cos(slope)
            return Vector((px, -(wz + rz), wy + ry))

        add_beveled_box(bm_bridge, plank_tf, bevel_offset=0.009, segments=2)

    # 6 vertical beveled posts with pyramid caps + curved double handrails
    for side in (-0.46, 0.46):
        for post_z_local in (-0.50, 0.0, 0.50):
            wz = bridge_center_z + post_z_local
            wy = arch_height(post_z_local)
            add_beveled_box(
                bm_bridge,
                lambda co, side=side, wz=wz, wy=wy: Vector((
                    side + co.x * 0.084,
                    -(wz + co.y * 0.084),
                    wy + 0.15 + co.z * 0.36,
                )),
                bevel_offset=0.010,
                segments=2,
            )

        for rail_h, rail_thick in ((0.30, 0.048), (0.17, 0.032)):
            segs = 12
            for i in range(segs):
                u0 = (i / segs) * 2.0 - 1.0
                u1 = ((i + 1) / segs) * 2.0 - 1.0
                zl0 = u0 * 0.52
                zl1 = u1 * 0.52
                wy0 = arch_height(zl0) + rail_h
                wy1 = arch_height(zl1) + rail_h
                ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
                for v in ret["verts"]:
                    t = v.co.y + 0.5
                    vz = bridge_center_z + (zl0 * (1 - t) + zl1 * t)
                    vy = (wy0 * (1 - t) + wy1 * t) + v.co.z * rail_thick
                    vx = side + v.co.x * 0.054
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
# 4. ARTISANAL WOODEN SIGNPOSTS & HERO PROP WOODLAND MAILBOX
# ==============================================================================

def build_signpost(name, label_text, x, z, yaw_deg, arrow_dir, materials):
    """
    Handcrafted woodland wayfinding signpost:
    - Tapered chamfered oak post with pyramid weather-cap & stone-and-timber base collar
    - Wrought-iron mounting brackets
    - Beveled oak directional plaque with recessed inner border molding
    - Subtle low-relief chiseled lettering (refined, not puffy balloon text)
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    bm_post = bmesh.new()
    # Tapered chamfered oak post
    add_beveled_box(
        bm_post,
        lambda co: to_world(
            co.x * (0.155 - 0.02 * (co.z + 0.5)),
            0.74 + co.z * 1.56,
            co.y * (0.155 - 0.02 * (co.z + 0.5)),
        ),
        bevel_offset=0.016,
        segments=2,
    )

    # Stepped pyramid weather cap
    ret_cap = bmesh.ops.create_cube(bm_post, size=1.0)
    for v in ret_cap["verts"]:
        t_top = 0.50 if v.co.z > 0 else 1.22
        v.co = to_world(v.co.x * 0.20 * t_top, 1.55 + v.co.z * 0.11, v.co.y * 0.20 * t_top)

    # Base mortised timber collar + diagonal foot braces
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.26, 0.08 + co.z * 0.16, co.y * 0.26),
        bevel_offset=0.014,
        segments=2,
    )

    # Wrought-iron mounting straps wrapping the post at signboard height
    for strap_y in (1.02, 1.28):
        add_beveled_box(
            bm_post,
            lambda co, sy=strap_y: to_world(co.x * 0.185, sy + co.z * 0.042, co.y * 0.195),
            bevel_offset=0.005,
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

    # Handcrafted beveled directional wooden signboard with outer molding rails
    bm_board = bmesh.new()
    board_w = 1.62
    board_h = 0.45
    board_d = 0.092
    board_y = 1.15

    def board_tf(co):
        lx = co.x * board_w
        # Subtle organic top/bottom wave so the plank feels hand-hewn
        wave = 0.008 * math.sin(lx * 3.5)
        ly = board_y + co.z * board_h + wave
        lz = 0.105 + co.y * board_d
        if arrow_dir < 0 and co.x < -0.34:
            tip_factor = max(0.20, 1.0 - abs(co.x + 0.34) * 1.25)
            ly = board_y + (ly - board_y) * tip_factor
        elif arrow_dir > 0 and co.x > 0.34:
            tip_factor = max(0.20, 1.0 - abs(co.x - 0.34) * 1.25)
            ly = board_y + (ly - board_y) * tip_factor
        return to_world(lx, ly, lz)

    add_beveled_box(bm_board, board_tf, bevel_offset=0.015, segments=3)

    # Top and bottom chamfered frame trim bars along the non-pointed section of the signboard
    for trim_z in (-0.21, 0.21):
        trim_x_shift = 0.12 if arrow_dir < 0 else -0.12
        add_beveled_box(
            bm_board,
            lambda co, tz=trim_z, txs=trim_x_shift: to_world(
                txs + co.x * 1.18,
                board_y + tz + co.z * 0.042,
                0.115 + co.y * 0.115,
            ),
            bevel_offset=0.006,
            segments=2,
        )

    c_plaque_dark = hex_to_rgba("#3E2513")
    c_plaque_warm = hex_to_rgba("#694225")
    finalize_mesh_object(
        f"{name}_Board",
        bm_board,
        materials["wood_sign_plaque"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_plaque_dark, c_plaque_warm, 0.4 + 0.45 * abs(ny) + 0.15 * math.sin(wy * 40.0)
        ),
    )

    # Refined, crisp chiseled wayfinding lettering (slim profile, balanced proportion)
    bpy.ops.object.text_add(location=(0, 0, 0))
    txt_obj = bpy.context.active_object
    txt_obj.name = f"{name}_Label3D"
    txt_obj.data.body = label_text
    txt_obj.data.align_x = 'CENTER'
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.size = 0.188
    txt_obj.data.space_character = 1.04
    txt_obj.data.extrude = 0.012
    txt_obj.data.bevel_depth = 0.0018
    txt_obj.data.bevel_resolution = 1

    bpy.ops.object.convert(target='MESH')
    text_x_offset = 0.05 if arrow_dir < 0 else -0.05
    for v in txt_obj.data.vertices:
        lx = v.co.x + text_x_offset
        ly = board_y + v.co.y
        lz = 0.154 + v.co.z
        v.co = to_world(lx, ly, lz)

    txt_obj.data.materials.append(materials["ivory_lettering"])
    for poly in txt_obj.data.polygons:
        poly.use_smooth = True


def build_woodland_mailbox(x, z, yaw_deg, materials):
    """
    Hero Prop Woodland Mailbox positioned on its dedicated cobblestone alcove at (1.18, y, 1.08):
    - Chamfered oak post with curved corbel brace & iron base collar
    - Arched forest-green body with raised brass end-straps & rolled roof overhang
    - Articulated brass front door with bottom hinge barrel, louver slot, and turned pull knob
    - Emerging folded cream letter with wax seal & pivoted brass signal flag
    """
    y_ground = get_terrain_height(x, z)
    yaw = math.radians(yaw_deg)

    def to_world(lx, ly, lz):
        wx = x + lx * math.cos(yaw) + lz * math.sin(yaw)
        wz = z - lx * math.sin(yaw) + lz * math.cos(yaw)
        wy = y_ground + ly
        return Vector((wx, -wz, wy))

    # 1. Chamfered oak post + curved corbel brace + molded shelf
    bm_post = bmesh.new()
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.145, 0.46 + co.z * 0.94, co.y * 0.145),
        bevel_offset=0.015,
        segments=2,
    )
    # Molded oak mounting tray
    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.46, 0.91 + co.z * 0.065, co.y * 0.60),
        bevel_offset=0.012,
        segments=2,
    )
    # Front diagonal corbel support brace under the tray
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
    # Base collar
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

    # 2. Rounded arched vintage mailbox body with rolled roof overhang
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
        # Subtle decorative end-band swell at front and back ribs
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

    c_mb_dark = hex_to_rgba("#143329")
    c_mb_top = hex_to_rgba("#275948")
    finalize_mesh_object(
        "Mailbox_Body",
        bm_body,
        materials["mailbox_forest_metal"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(c_mb_dark, c_mb_top, 0.4 + 0.5 * max(0.0, ny)),
    )

    # 3. Articulated Brass Front Door with hinge barrel, embossed mail slot, and pull handle knob
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

    # Turned brass pull handle & mail slot hood on the front of the door
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

    # 4. Emerging folded cream-linen letter peeking out of the mailbox opening
    bm_letter = bmesh.new()
    add_beveled_box(
        bm_letter,
        lambda co: to_world(co.x * 0.25, base_y + 0.21 + co.z * 0.032 - co.y * 0.04, 0.21 + co.y * 0.28),
        bevel_offset=0.004,
        segments=2,
    )
    finalize_mesh_object("Mailbox_Letter", bm_letter, materials["ivory_lettering"])

    # 5. Raised side brass signal flag with pivot boss
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


# ==============================================================================
# 5. DIVERSE BOTANICAL GROUND VEGETATION & SCULPTED BOULDERS
# ==============================================================================

def build_rocks_and_botanical_groundcover(materials):
    """
    Replaces repetitive geometric ground blobs with:
    - Chiseled mossy boulders & creek bank stones
    - Asymmetric pinnate fern fronds + multi-blade 3D grass clumps
    - Stemmed wildflower clusters with multi-petal blossoms
    """
    bm_rocks = bmesh.new()
    rock_placements = [
        # NW spring headwater grotto boulders
        (-3.68, -0.55, 0.44, 0.32, 0.36), (-3.38, -0.15, 0.32, 0.24, 0.28), (-3.50, -0.95, 0.36, 0.28, 0.30),
        # SE cascade rocks
        (3.48, 0.96, 0.42, 0.30, 0.35), (3.20, 0.56, 0.30, 0.22, 0.26),
        # Creek bank & bridge wing-wall stones
        (-2.25, 0.24, 0.28, 0.20, 0.24), (-1.28, -0.04, 0.25, 0.18, 0.22),
        (-0.56, 0.44, 0.24, 0.19, 0.22), (0.58, 0.06, 0.24, 0.18, 0.22),
        (-0.58, 0.08, 0.22, 0.17, 0.20), (0.56, 0.46, 0.23, 0.18, 0.21),
        (1.52, 0.54, 0.26, 0.19, 0.22), (2.38, 0.80, 0.32, 0.22, 0.26),
        # Submerged creek bed cobbles
        (-1.85, -0.05, 0.18, 0.10, 0.15), (-0.85, 0.15, 0.16, 0.09, 0.14),
        (0.95, 0.38, 0.17, 0.10, 0.15), (1.85, 0.62, 0.19, 0.11, 0.16),
        # Signpost, mailbox, and background ridge boulders
        (-1.92, -0.72, 0.26, 0.20, 0.22), (1.92, -0.68, 0.26, 0.20, 0.22),
        (1.42, 1.12, 0.20, 0.15, 0.18), (-0.15, -2.18, 0.38, 0.26, 0.30),
        (0.32, -2.35, 0.28, 0.20, 0.24), (-2.85, -1.55, 0.36, 0.25, 0.30),
        (2.85, -1.50, 0.35, 0.24, 0.29),
    ]
    for idx, (rx, rz, sx, sy, sz_r) in enumerate(rock_placements):
        ry = get_terrain_height(rx, rz) - 0.03
        ret = bmesh.ops.create_icosphere(bm_rocks, subdivisions=3, radius=1.0)
        yaw = (idx * 1.17) % math.pi
        for v in ret["verts"]:
            p = v.co
            n = noise.noise(Vector((p.x * 2.3 + idx, p.y * 2.3 - idx, p.z * 2.3)))
            # Stylize rocks with planar beveled faces
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
        if ny > 0.38:
            col = lerp_color(col, c_rock_moss, min(0.75, (ny - 0.38) * 1.4))
        return col

    finalize_mesh_object("Environment_Rocks", bm_rocks, materials["stone_mossy"], boulder_color_fn)

    # Botanical Ferns + Multi-Blade 3D Grass Clumps + Moss Cushions (combined in Forest_Ferns)
    bm_foliage_ground = bmesh.new()

    # 1) Asymmetric Woodland Fern Rosettes
    fern_clusters = [
        (-2.35, 1.15, 0.36, 7), (-1.55, 1.48, 0.26, 5), (1.72, 1.45, 0.30, 6),
        (2.48, 1.18, 0.34, 7), (-2.62, -0.38, 0.38, 8), (2.62, -0.28, 0.35, 7),
        (-0.88, -1.58, 0.32, 6), (0.88, -1.55, 0.30, 6), (-0.18, -1.95, 0.36, 7),
        (-1.82, -0.52, 0.25, 5), (1.82, -0.48, 0.25, 5), (1.38, 0.92, 0.24, 5),
        (-0.78, 0.65, 0.24, 5), (0.76, 0.58, 0.22, 5),
    ]
    for c_idx, (fx, fz, f_scale, num_fronds) in enumerate(fern_clusters):
        fy = get_terrain_height(fx, fz) - 0.01
        for ifr in range(num_fronds):
            ang = (2.0 * math.pi * ifr) / num_fronds + (c_idx * 0.53) + 0.18 * math.sin(ifr * 2.1)
            frond_len = f_scale * (0.75 + 0.35 * ((ifr * 3 + c_idx) % 4) / 3.0)
            droop = 0.72 + 0.22 * ((ifr % 3) / 2.0)
            segs = 6
            rows = []
            for iseg in range(segs + 1):
                t = iseg / segs
                r = frond_len * t
                arch_y = fy + f_scale * (0.44 * math.sin(t * math.pi * droop))
                # Pinnate scalloped frond width profile
                w = f_scale * 0.20 * math.sin(t * math.pi) * (0.85 + 0.15 * math.sin(t * 18.0))
                wx = fx + math.cos(ang) * r
                wz = fz + math.sin(ang) * r
                nx_d, nz_d = -math.sin(ang), math.cos(ang)
                twist = 0.03 * f_scale * math.sin(t * 4.0 + ifr)
                v_left = bm_foliage_ground.verts.new((wx - nx_d * w, -(wz - nz_d * w), arch_y + twist))
                v_mid = bm_foliage_ground.verts.new((wx, -wz, arch_y + 0.025 * f_scale))
                v_right = bm_foliage_ground.verts.new((wx + nx_d * w, -(wz + nz_d * w), arch_y - twist))
                rows.append((v_left, v_mid, v_right))
            for iseg in range(segs):
                l0, m0, r0 = rows[iseg]
                l1, m1, r1 = rows[iseg + 1]
                bm_foliage_ground.faces.new((l0, m0, m1, l1))
                bm_foliage_ground.faces.new((m0, r0, r1, m1))

    # 2) Diverse Multi-Blade 3D Grass Clumps scattered naturally across meadow & path margins
    grass_spots = [
        (-0.52, 2.05, 0.22), (0.48, 1.92, 0.20), (-0.46, 1.42, 0.19), (0.46, 1.38, 0.18),
        (-1.12, 0.95, 0.24), (-1.85, 0.72, 0.26), (1.68, 0.92, 0.23), (2.15, 1.42, 0.25),
        (-2.15, 1.55, 0.25), (-1.15, -0.35, 0.20), (1.15, -0.35, 0.20), (-0.52, -0.82, 0.21),
        (0.52, -0.82, 0.21), (-2.15, -0.88, 0.24), (2.15, -0.84, 0.24), (-1.45, -1.45, 0.25),
        (1.45, -1.42, 0.25), (0.28, -1.35, 0.22), (-0.32, -1.25, 0.20), (1.05, 1.35, 0.19),
        (-2.95, 0.45, 0.26), (2.95, 0.35, 0.26), (-0.85, 1.85, 0.22), (0.85, 1.78, 0.21),
    ]
    for g_idx, (gx, gz, g_scale) in enumerate(grass_spots):
        gy = get_terrain_height(gx, gz) - 0.01
        num_blades = 7 + (g_idx % 4)
        for ib in range(num_blades):
            ang = (2.0 * math.pi * ib) / num_blades + g_idx * 0.71
            offset_r = 0.04 + 0.05 * ((ib % 3) * 0.5)
            bx0 = gx + math.cos(ang) * offset_r
            bz0 = gz + math.sin(ang) * offset_r
            blade_h = g_scale * (0.75 + 0.45 * ((ib * 5 + g_idx) % 4) / 3.0)
            lean_r = blade_h * (0.38 + 0.22 * ((ib % 2)))
            blade_w = 0.028 * (0.85 + 0.3 * (ib % 2))
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

    c_fern_base = hex_to_rgba("#244730")
    c_fern_tip = hex_to_rgba("#769C5E")

    def ground_foliage_color_fn(wx, wy, wz, nx, ny, nz):
        gy = get_terrain_height(wx, wz)
        h_rel = max(0.0, min(1.0, (wy - gy) / 0.22))
        n_f = noise.noise(Vector((wx * 2.0, wz * 2.0, wy)))
        return lerp_color(c_fern_base, c_fern_tip, min(1.0, h_rel * 0.85 + 0.15 + 0.15 * n_f))

    finalize_mesh_object("Forest_Ferns", bm_foliage_ground, materials["foliage_moss"], ground_foliage_color_fn)

    # 3) Botanical Wildflower Clusters with Stems & Multi-Petal Blossoms (not polka-dot spheres!)
    bm_flowers = bmesh.new()
    flower_clusters = [
        # Tucked naturally beside rocks, signposts, and meadow clusters
        (-1.76, -0.54, 4), (-1.34, -0.78, 3), (1.76, -0.50, 4), (1.36, -0.74, 3),
        (1.36, 1.22, 4), (0.98, 0.94, 3), (-0.72, 1.52, 4), (0.64, 1.72, 3),
        (-2.05, 1.02, 4), (2.05, 1.28, 4), (-0.38, -1.62, 3), (0.42, -1.52, 3),
    ]
    for idx, (cx, cz, count) in enumerate(flower_clusters):
        for sub in range(count):
            ang_s = idx * 1.9 + sub * 2.15
            rad_s = 0.06 + 0.07 * (sub % 3)
            fx = cx + math.cos(ang_s) * rad_s
            fz = cz + math.sin(ang_s) * rad_s
            fy = get_terrain_height(fx, fz) + 0.045 + 0.018 * (sub % 2)
            # 4-petal tiny blossom cluster
            for ip in range(4):
                p_ang = (math.pi * 0.5) * ip + sub * 0.4
                px = fx + math.cos(p_ang) * 0.022
                pz = fz + math.sin(p_ang) * 0.022
                ret = bmesh.ops.create_icosphere(bm_flowers, subdivisions=1, radius=0.022)
                for v in ret["verts"]:
                    v.co = Vector((px + v.co.x, -(pz + v.co.y), fy + v.co.z * 0.55))

    c_fl_ivory = hex_to_rgba("#F6F1E4")
    c_fl_champagne = hex_to_rgba("#E4C98E")
    finalize_mesh_object(
        "Wildflowers",
        bm_flowers,
        materials["ivory_lettering"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(
            c_fl_champagne, c_fl_ivory, 0.5 + 0.5 * math.sin(wx * 12.0 + wz * 9.0)
        ),
    )


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

    aim_camera((-0.35, -12.6, 7.1), (0.0, 0.0, 0.42))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_initial.png")
    bpy.ops.render.render(write_still=True)

    aim_camera((5.2, -11.6, 7.3), (-0.05, 0.0, 0.42))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_rotated.png")
    bpy.ops.render.render(write_still=True)


def print_mesh_statistics():
    total_verts = 0
    total_tris = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            v_count = len(obj.data.vertices)
            t_count = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
            total_verts += v_count
            total_tris += t_count
    print(f"SCENE GEOMETRY STATS: {total_verts} vertices, {total_tris} triangles across {len(bpy.context.scene.objects)} objects")


def main():
    clear_scene()

    materials = {
        "grass_top": make_pbr_material("Grass_Top_Mat", "#5B7A53", roughness=0.82),
        "rock_underside": make_pbr_material("Rock_Underside_Mat", "#524B44", roughness=0.88),
        "pathway_earth": make_pbr_material("Pathway_Earth_Mat", "#BC9E76", roughness=0.85),
        "stone_warm": make_pbr_material("Stone_Warm_Mat", "#928A7F", roughness=0.76),
        "stone_mossy": make_pbr_material("Stone_Mossy_Mat", "#646F5E", roughness=0.79),
        "stream_water": make_pbr_material("Stream_Water_Mat", "#2E5E57", roughness=0.22, metallic=0.04),
        "wood_oak": make_pbr_material("Wood_Oak_Mat", "#9D6E48", roughness=0.66),
        "wood_post": make_pbr_material("Wood_Post_Mat", "#784F30", roughness=0.70),
        "wood_sign_plaque": make_pbr_material("Wood_Sign_Plaque_Mat", "#54331C", roughness=0.60),
        "wood_bark": make_pbr_material("Wood_Bark_Mat", "#6A4B35", roughness=0.84),
        "foliage_deep": make_pbr_material("Foliage_Deep_Mat", "#26543F", roughness=0.74),
        "foliage_moss": make_pbr_material("Foliage_Moss_Mat", "#4E724A", roughness=0.75),
        "foliage_sage": make_pbr_material("Foliage_Sage_Mat", "#73916C", roughness=0.76),
        "ivory_lettering": make_pbr_material("Ivory_Lettering_Mat", "#F4EFE3", roughness=0.38, use_vertex_color=False),
        "mailbox_forest_metal": make_pbr_material("Mailbox_Forest_Metal_Mat", "#1E493B", roughness=0.38, metallic=0.24),
        "champagne_brass": make_pbr_material("Champagne_Brass_Mat", "#DCC89A", roughness=0.30, metallic=0.72, use_vertex_color=False),
    }

    build_island_terrain(materials)
    build_pathway_and_cobbles(materials)
    build_stream_and_bridge(materials)
    build_rocks_and_botanical_groundcover(materials)

    # Spatial Hierarchy & Layered Composition of 7 Varied Trees across 3 Archetypes
    # Notice: Deliberate open negative space in the center-north (-0.8 to +0.8) so trees frame
    # rather than form a flat wall, with strong height & silhouette contrast!
    create_tree_archetype_oak("Tree_NW_Hero", -2.55, -2.05, 1.24, -0.18, -0.10, 0, materials)
    create_tree_archetype_cedar("Tree_N_Left", -1.35, -2.55, 1.18, -0.06, -0.08, 2, materials)
    create_tree_archetype_birch("Tree_N_Center", 0.92, -2.48, 0.94, 0.14, -0.08, 1, materials)
    create_tree_archetype_cedar("Tree_N_Right", 2.15, -2.28, 1.28, 0.10, -0.10, 2, materials)
    create_tree_archetype_oak("Tree_NE_Hero", 3.05, -1.52, 1.06, 0.18, -0.05, 1, materials)
    create_tree_archetype_birch("Tree_W_Flank", -3.22, -0.65, 0.90, -0.20, 0.06, 1, materials)
    create_tree_archetype_cedar("Tree_E_Flank", 3.18, -0.28, 0.84, 0.16, 0.08, 0, materials)

    # Interactive Hero Props
    build_signpost("Signpost_UX", "UX Portfolio", -1.58, -0.62, 18.0, -1, materials)
    build_signpost("Signpost_Game", "Game Portfolio", 1.58, -0.58, -18.0, 1, materials)
    build_woodland_mailbox(1.18, 1.08, -22.0, materials)

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
    print(f"Exported V2 runtime GLB to: {GLB_OUT}")

    setup_lighting_and_render_previews()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved V2 master Blender source to: {BLEND_OUT}")


if __name__ == "__main__":
    main()
