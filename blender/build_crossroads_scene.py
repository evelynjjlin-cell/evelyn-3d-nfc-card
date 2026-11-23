"""
Blender 5.0 High-Fidelity Stylized Environment Authoring Script
(V3 Object-First Identity Transformation + Creek, Front Terrain, Vegetation & Signpost Refinement)
Project: The Crossroads — Two Paths, One Designer (Evelyn Lin)

V3 Upgrades:
1. Embedded 3D Personal Identity Plaque ('Evelyn Lin' / 'UX & Interactive Experience Designer')
   physically sculpted into the front cliff mantle of the floating island.
2. Widened, more prominent shallow woodland creek with sculpted pebble riverbed (Stream_Bed),
   clearer sculpted banks, enlarged bridge water pool, and natural flow detail.
3. Front terrain & island lip cleanup: smooth rim attenuation, rolling foreground knolls,
   integrated stone outcrops, and seamless pathway-to-terrain blending.
4. Purposefully clustered ground vegetation (varied-scale 3D grass clumps, ferns, moss cushions,
   and wildflowers anchored around boulders, creek banks, and posts).
5. Renamed 3D wooden signposts: 'Design Path' (Left) and 'Play Path' (Right).
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
            bsdf.inputs["Specular IOR Level"].default_value = 0.30
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
# SPATIAL & TERRAIN FUNCTIONS (Refined Front Contour + Widened Woodland Creek)
# ==============================================================================

def island_rim_point(angle):
    """
    Smooth asymmetric organic island silhouette with a refined, intentional front contour
    that cradles the front-center 3D identity plaque and prevents any rim pinching.
    """
    rx_base = (
        4.38
        + 0.24 * math.cos(angle * 2.0 - 0.25)
        + 0.14 * math.sin(angle * 3.0 - 0.4)
        - 0.08 * math.cos(angle * 4.0 + 0.5)
    )
    rz_base = (
        3.36
        + 0.20 * math.sin(angle * 2.0 + 0.35)
        - 0.12 * math.cos(angle * 3.0)
        + 0.07 * math.sin(angle * 4.0 - 0.6)
    )
    x = math.cos(angle) * rx_base - 0.08
    z = math.sin(angle) * rz_base - 0.10 * math.cos(angle)
    return x, z


def island_radial_factor(x, z):
    ang = math.atan2(z + 0.06, x + 0.08)
    rim_x, rim_z = island_rim_point(ang)
    rim_r = math.hypot(rim_x + 0.08, rim_z + 0.06)
    cur_r = math.hypot(x + 0.08, z + 0.06)
    return cur_r / max(1e-4, rim_r)


def stream_center_z(x):
    """
    Graceful, continuous S-curve woodland creek centerline Z as a function of X.
    """
    return 0.22 + 0.16 * x + 0.34 * math.sin(x * 0.64 - 0.12) + 0.06 * math.cos(x * 1.35)


def stream_half_width(x):
    """
    Noticeably wider, legible woodland creek:
    - Generous pool around and under the bridge (half-width ~0.68 -> total width ~1.36 units)
    - Broad spring basin on the northwest (-2.0) and clear riffle pool on the southeast (+1.6)
    """
    bridge_pool = 1.0 + 0.24 * math.exp(-(x ** 2) / 1.15)
    spring_swell = 1.0 + 0.22 * math.exp(-((x + 1.95) ** 2) / 1.1) + 0.20 * math.exp(-((x - 1.65) ** 2) / 1.1)
    return 0.56 * bridge_pool * spring_swell


def path_distance_and_branch(x, z):
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

    d_main = seg_dist(x, z, 0.0, 2.52, 0.0, -0.26)
    d_left = seg_dist(x, z, 0.0, -0.26, -2.55, -1.58)
    d_right = seg_dist(x, z, 0.0, -0.26, 2.55, -1.50)
    return min(d_main, d_left, d_right)


def get_terrain_height(x, z):
    """
    Refined V3 multi-elevation sculpted landscape heightmap:
    - Elevated NW and NE background forest hills
    - Intentional foreground relief (front-left mossy knoll, front-right mailbox terrace)
      so the foreground never feels flat or empty
    - Deeply carved, well-defined creek channel with smooth rim attenuation so the island edge
      never collapses or pinches where the stream exits
    - Sculpted bridge abutment mounds on both banks
    """
    rf = island_radial_factor(x, z)

    # Background & flanking hills
    nw_hill = 0.54 * math.exp(-((x + 2.45) ** 2 / 3.2 + (z + 1.95) ** 2 / 2.6))
    ne_hill = 0.46 * math.exp(-((x - 2.35) ** 2 / 3.0 + (z + 1.85) ** 2 / 2.5))
    north_ridge = 0.34 * math.exp(-((x + 0.25) ** 2 / 5.5 + (z + 2.55) ** 2 / 2.2))

    # Intentional foreground sculpting (eliminates flat front meadow patch)
    fg_left_knoll = 0.24 * math.exp(-((x + 1.65) ** 2 / 1.85 + (z - 1.55) ** 2 / 1.35))
    fg_left_west = 0.19 * math.exp(-((x + 2.85) ** 2 / 1.6 + (z - 0.85) ** 2 / 1.4))
    fg_right_terrace = 0.21 * math.exp(-((x - 1.55) ** 2 / 1.95 + (z - 1.35) ** 2 / 1.35))

    # Multi-octave organic terrain undulation
    n1 = noise.noise(Vector((x * 0.45 + 4.2, z * 0.45 - 2.8, 1.1))) * 0.11
    n2 = noise.noise(Vector((x * 1.10 - 1.9, z * 1.10 + 3.4, 2.7))) * 0.042

    # Creek channel carving with clear, defined bank shoulders and smooth rim attenuation
    sz = stream_center_z(x)
    hw = stream_half_width(x)
    d_stream = abs(z - sz)
    rim_atten = 1.0 if rf < 0.76 else max(0.28, 1.0 - ((rf - 0.76) / 0.24) ** 1.5)
    stream_cut = 0.52 * math.exp(-((d_stream / (hw * 1.18)) ** 2.4)) * rim_atten
    bank_shoulder = 0.085 * math.exp(-(((d_stream - hw * 1.32) / 0.28) ** 2)) * rim_atten

    # Bridge abutment mounds at x=0, z=sz ± 0.68 so path meets the longer bridge span seamlessly
    abutment_south = 0.13 * math.exp(-((x ** 2) / 0.34 + ((z - (sz + 0.68)) ** 2) / 0.16))
    abutment_north = 0.13 * math.exp(-((x ** 2) / 0.34 + ((z - (sz - 0.68)) ** 2) / 0.16))

    # Subtle worn recess along the footpaths
    d_path = path_distance_and_branch(x, z)
    on_bridge = math.exp(-((x ** 2) / 0.42 + ((z - sz) ** 2) / 0.44))
    path_cut = 0.052 * math.exp(-(d_path ** 2) / 0.24) * (1.0 - on_bridge)

    # Smooth, well-supported outer turf rim roll-off (no collapsed or pinched edges)
    edge_roll = 0.0
    if rf > 0.76:
        t = min(1.08, (rf - 0.76) / 0.24)
        ang = math.atan2(z, x)
        cliff_var = 0.90 + 0.16 * math.sin(ang * 3.0 + 0.5)
        edge_roll = -0.32 * (t ** 1.95) * cliff_var

    return (
        0.20
        + nw_hill
        + ne_hill
        + north_ridge
        + fg_left_knoll
        + fg_left_west
        + fg_right_terrace
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
# 1. SCULPTED FLOATING ISLAND TERRAIN & EMBEDDED 3D IDENTITY PLAQUE
# ==============================================================================

def build_island_terrain(materials):
    """
    Builds the sculpted upper terrain, craggy rock underside, and integrated cliff outcrops
    with a clean, intentional front lip contour.
    """
    bm_top = bmesh.new()
    rings = 68
    segs = 152

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

            # Controlled, smooth draping turf lip around the perimeter (no sharp folds)
            if ir >= rings - 3:
                lip_t = (ir - (rings - 3)) / 3.0
                drape_noise = noise.noise(Vector((wx * 0.9, wz * 0.9, 0.5)))
                drape_depth = 0.095 * (0.82 + 0.36 * drape_noise)
                wy -= drape_depth * (lip_t ** 1.45)
                flare = 1.0 + 0.008 * drape_noise * lip_t
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

    c_moss_bank = hex_to_rgba("#32583B")
    c_grass_mid = hex_to_rgba("#587850")
    c_grass_sun = hex_to_rgba("#7B9A67")
    c_earth_loam = hex_to_rgba("#785C42")

    def terrain_color_fn(wx, wy, wz, nx, ny, nz):
        sz = stream_center_z(wx)
        hw = stream_half_width(wx)
        d_stream = abs(wz - sz)
        d_path = path_distance_and_branch(wx, wz)
        rf = island_radial_factor(wx, wz)
        n_c = noise.noise(Vector((wx * 0.8 + 1.3, wz * 0.8 - 2.1, wy)))

        h_factor = max(0.0, min(1.0, (wy - 0.14) / 0.52 + 0.24 * n_c))
        col = lerp_color(c_grass_mid, c_grass_sun, h_factor)

        # Rich dark moss & damp earth along the sculpted creek banks
        bank_zone = math.exp(-((d_stream / (hw * 1.45)) ** 2.2))
        col = lerp_color(col, c_moss_bank, bank_zone * 0.78)

        # Natural earth blending along pathway edges and outer turf lip
        path_blend = math.exp(-(d_path ** 2) / 0.24) * 0.55
        rim_earth = max(0.0, (rf - 0.88) / 0.12) * 0.58
        col = lerp_color(col, c_earth_loam, min(0.82, path_blend + rim_earth))
        return col

    finalize_mesh_object("Island_Terrain_Top", bm_top, materials["grass_top"], terrain_color_fn)

    # Unified Sculpted Craggy Rock & Earth Underside
    bm_rock = bmesh.new()
    rock_rings = 36
    rock_rows = []
    for ir in range(rock_rings + 1):
        t = ir / rock_rings
        row = []
        for iseg in range(segs):
            ang = (2.0 * math.pi * iseg) / segs
            rim_x, rim_z = island_rim_point(ang)
            top_y = get_terrain_height(rim_x, rim_z) - 0.035

            buttress = 0.068 * math.sin(ang * 7.0 + t * 1.8) + 0.042 * math.cos(ang * 11.0 - t * 2.5)
            n_crag1 = noise.noise(Vector((rim_x * 0.70 + 1.4, rim_z * 0.70 - 2.2, t * 2.8)))
            n_crag2 = noise.noise(Vector((rim_x * 1.55 - 0.8, rim_z * 1.55 + 1.9, t * 5.2)))

            ledge_step = 0.032 * math.sin(t * math.pi * 3.0 + n_crag1 * 2.0) * (1.0 - t)
            taper = (1.004 - (t ** 2.15) * 0.90) + buttress * (1.0 - t * 0.5) * min(1.0, t * 2.2) + ledge_step

            rx = rim_x * max(0.03, taper)
            rz = rim_z * max(0.03, taper)

            radial_disp = (0.18 * n_crag1 + 0.07 * n_crag2) * (1.0 - t * 0.35) * min(1.0, t * 3.0)
            dir_len = max(1e-4, math.hypot(rim_x, rim_z))
            rx += (rim_x / dir_len) * radial_disp
            rz += (rim_z / dir_len) * radial_disp

            depth_scale = 2.28 + 0.30 * math.sin(ang - 1.1) + 0.18 * math.cos(ang * 3.0)
            ry = top_y - (depth_scale * (t ** 1.05)) + 0.10 * n_crag1 * (1.0 - t * 0.4)

            row.append(bm_rock.verts.new((rx, -rz, ry)))
        rock_rows.append(row)

    bottom_apex = bm_rock.verts.new((-0.10, 0.14, -2.38))

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

    # Integrated Cliff Ledges, Hanging Roots & Front Identity Plaque Stone Mantle (in Island_Soil_Rim)
    bm_outcrops = bmesh.new()
    outcrop_specs = [
        (-0.42, 0.93, -0.36, 0.52, 0.25, 0.35),
        (-1.15, 0.92, -0.42, 0.56, 0.27, 0.36),
        (-2.15, 0.93, -0.38, 0.52, 0.25, 0.35),
        (2.35, 0.93, -0.36, 0.48, 0.24, 0.33),
        (0.85, 0.92, -0.40, 0.50, 0.24, 0.34),
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
            chisel = 1.0 + 0.22 * n - 0.14 * abs(p.z)
            v.co = Vector((
                ox + p.x * sx * chisel,
                -(oz + p.y * sz_r * chisel),
                oy + p.z * sy * chisel,
            ))

    # Front-center sculpted stone mantle housing the embedded 3D Identity Plaque at (0.0, -0.34, 3.36)
    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.36
    plaque_pitch = math.radians(-22.0)

    def plaque_to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    # Chiseled stone architectural surround embedded into the front island cliff
    add_beveled_box(
        bm_outcrops,
        lambda co: plaque_to_world(co.x * 2.86, co.z * 0.80, -0.06 + co.y * 0.34),
        bevel_offset=0.042,
        segments=3,
    )

    finalize_mesh_object("Island_Soil_Rim", bm_outcrops, materials["rock_underside"], rock_color_fn)


def build_embedded_identity_plaque(materials):
    """
    Physically embeds Evelyn Lin's 3D Identity Plaque into the front cliff mantle of the floating island:
    - Identity_Plaque_Frame: Beveled champagne-brass outer bezel & corner rivets
    - Identity_Plaque_Plate: Recessed deep-forest oxidized slate/bronze inner tablet
    - Identity_Plaque_Text3D: Extruded & beveled 3D typography ('Evelyn Lin' & 'UX & INTERACTIVE EXPERIENCE DESIGNER')
    """
    plaque_cx, plaque_cy, plaque_cz = 0.0, -0.34, 3.36
    plaque_pitch = math.radians(-22.0)

    def to_world(lx, ly, lz):
        ry = ly * math.cos(plaque_pitch) - lz * math.sin(plaque_pitch)
        rz = ly * math.sin(plaque_pitch) + lz * math.cos(plaque_pitch)
        return Vector((plaque_cx + lx, -(plaque_cz + rz), plaque_cy + ry))

    # 1. Beveled Champagne-Brass Frame + 4 Corner Rivets
    bm_frame = bmesh.new()
    add_beveled_box(
        bm_frame,
        lambda co: to_world(co.x * 2.66, co.z * 0.68, 0.09 + co.y * 0.10),
        bevel_offset=0.020,
        segments=3,
    )
    for rx_s in (-1.20, 1.20):
        for ry_s in (-0.23, 0.23):
            add_beveled_box(
                bm_frame,
                lambda co, rxs=rx_s, rys=ry_s: to_world(
                    rxs + co.x * 0.042,
                    rys + co.z * 0.042,
                    0.155 + co.y * 0.028,
                ),
                bevel_offset=0.007,
                segments=2,
            )
    finalize_mesh_object("Identity_Plaque_Frame", bm_frame, materials["champagne_brass"])

    # 2. Recessed Deep-Forest Slate / Bronze Inner Tablet
    bm_plate = bmesh.new()
    add_beveled_box(
        bm_plate,
        lambda co: to_world(co.x * 2.50, co.z * 0.55, 0.115 + co.y * 0.08),
        bevel_offset=0.014,
        segments=2,
    )
    finalize_mesh_object("Identity_Plaque_Plate", bm_plate, materials["mailbox_forest_metal"])

    # 3. Physical 3D Relief Typography: 'Evelyn Lin' + 'UX & INTERACTIVE EXPERIENCE DESIGNER'
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
# 2. THREE DISTINCT HIGH-FIDELITY TREE ARCHETYPES (PRESERVED FROM V2)
# ==============================================================================

def add_foliage_cluster_lobe(bm, cx, cy, cz, rx, ry, rz, yaw, pitch, seed_val):
    ret = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    cy_cos, cy_sin = math.cos(yaw), math.sin(yaw)
    cp_cos, cp_sin = math.cos(pitch), math.sin(pitch)

    for v in ret["verts"]:
        p = v.co
        n_broad = noise.noise(Vector((p.x * 1.7 + seed_val, p.y * 1.7 - seed_val, p.z * 1.7)))
        n_tuft = abs(noise.noise(Vector((p.x * 3.8 - seed_val, p.y * 3.8 + seed_val, p.z * 3.8))))
        disp = 1.0 + 0.18 * n_broad + 0.14 * (n_tuft - 0.35)

        y_shape = 1.08 if p.z >= 0 else 0.64
        lx = p.x * rx * disp
        lz = p.y * rz * disp
        ly = p.z * ry * disp * y_shape

        ly_p = ly * cp_cos - lz * cp_sin
        lz_p = ly * cp_sin + lz * cp_cos
        wx = cx + lx * cy_cos + lz_p * cy_sin
        wz = cz - lx * cy_sin + lz_p * cy_cos
        wy = cy + ly_p
        v.co = Vector((wx, -wz, wy))


def add_curved_branch_tube(bm, points_xyz_rad, segs=12, bark_groove_amp=0.04):
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
    if palette_mode == 0:
        c_shadow = hex_to_rgba("#16382B")
        c_mid = hex_to_rgba("#386546")
        c_sun = hex_to_rgba("#7FA368")
    elif palette_mode == 1:
        c_shadow = hex_to_rgba("#274734")
        c_mid = hex_to_rgba("#557A4E")
        c_sun = hex_to_rgba("#9CB678")
    else:
        c_shadow = hex_to_rgba("#14332A")
        c_mid = hex_to_rgba("#2E5947")
        c_sun = hex_to_rgba("#688E6C")

    sun_dir = Vector((0.52, 0.74, 0.42)).normalized()

    def color_fn(wx, wy, wz, nx, ny, nz):
        norm = Vector((nx, ny, nz)).normalized()
        sun_dot = max(0.0, norm.dot(sun_dir))
        height_t = max(0.0, min(1.0, (wy - (tree_y_base + 1.1)) / 1.85))
        n_cluster = noise.noise(Vector((wx * 1.4, wy * 1.4, wz * 1.4)))

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
            band = math.sin(wy * 22.0 + n_b * 4.0)
            if band > 0.72:
                col = lerp_color(col, c_dark, 0.65)
        if wy < 0.72:
            moss_t = max(0.0, (0.72 - wy) / 0.45) * (0.6 + 0.4 * n_b)
            col = lerp_color(col, c_moss, min(0.75, moss_t))
        return col

    return color_fn


def create_tree_archetype_oak(name, x, z, scale, lean_x, lean_z, palette_mode, materials):
    y0 = get_terrain_height(x, z) - 0.06
    bm_trunk = bmesh.new()

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

    bm_canopy = bmesh.new()
    cluster_offsets = [
        (0, 0.0, 0.04, 0.0, 0.44, 0.28, 0.40, 0.2, 0.1),
        (0, -0.26, -0.06, 0.14, 0.35, 0.23, 0.32, 0.5, -0.12),
        (0, 0.18, 0.16, 0.18, 0.32, 0.22, 0.30, -0.3, 0.08),
        (0, -0.14, 0.18, -0.22, 0.34, 0.24, 0.32, 0.1, 0.15),
        (1, 0.0, 0.05, 0.0, 0.43, 0.27, 0.39, -0.25, -0.1),
        (1, 0.25, -0.05, -0.12, 0.34, 0.22, 0.31, 0.4, 0.12),
        (1, -0.16, 0.15, -0.20, 0.33, 0.22, 0.30, -0.4, -0.08),
        (1, 0.15, 0.18, 0.20, 0.32, 0.23, 0.29, 0.2, -0.14),
        (2, 0.0, 0.04, 0.0, 0.42, 0.27, 0.38, 0.3, 0.08),
        (2, -0.24, -0.04, -0.18, 0.34, 0.22, 0.32, -0.2, 0.14),
        (2, 0.18, 0.14, -0.22, 0.32, 0.21, 0.30, 0.6, -0.1),
        (2, -0.10, 0.22, 0.12, 0.30, 0.20, 0.28, -0.5, 0.05),
        (3, 0.0, 0.04, 0.0, 0.40, 0.26, 0.36, -0.35, -0.08),
        (3, 0.22, -0.06, 0.16, 0.32, 0.21, 0.30, 0.25, 0.12),
        (3, -0.15, 0.14, 0.18, 0.30, 0.20, 0.28, -0.15, -0.12),
        (3, 0.12, 0.18, -0.14, 0.29, 0.20, 0.27, 0.45, 0.06),
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
    y0 = get_terrain_height(x, z) - 0.05
    bm_trunk = bmesh.new()

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

    bm_canopy = bmesh.new()
    birch_clusters = [
        (0, 0.0, 0.05, 0.0, 0.38, 0.24, 0.35, 0.1, 0.05),
        (0, -0.22, -0.06, 0.10, 0.30, 0.19, 0.28, -0.3, 0.12),
        (0, 0.20, -0.04, -0.10, 0.29, 0.18, 0.27, 0.4, -0.10),
        (0, 0.02, 0.18, -0.04, 0.27, 0.18, 0.25, 0.0, 0.08),
        (1, 0.0, 0.04, 0.0, 0.35, 0.21, 0.32, -0.25, 0.10),
        (1, side_sign * 0.20, -0.05, 0.10, 0.27, 0.17, 0.25, 0.35, -0.08),
        (1, -side_sign * 0.12, 0.12, -0.10, 0.25, 0.16, 0.24, -0.15, 0.06),
        (2, 0.0, 0.02, 0.0, 0.33, 0.20, 0.30, 0.3, 0.10),
        (2, -0.18, -0.06, 0.08, 0.25, 0.16, 0.24, -0.2, -0.12),
        (2, 0.12, 0.10, -0.08, 0.24, 0.16, 0.22, 0.5, 0.05),
        (3, 0.0, 0.03, 0.0, 0.34, 0.20, 0.31, -0.3, -0.08),
        (3, 0.18, -0.05, -0.08, 0.26, 0.17, 0.24, 0.2, 0.12),
        (3, -0.10, 0.11, 0.08, 0.24, 0.15, 0.22, -0.4, -0.05),
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
    whorls = [
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
# 3. INTEGRATED PATHWAYS, WIDENED WOODLAND CREEK & ARCHED OAK BRIDGE
# ==============================================================================

def build_pathway_and_cobbles(materials):
    """
    Continuous woodland pathways that blend organically into the sculpted front terrain
    and connect directly onto both ends of the arched oak bridge.
    """
    bm_path = bmesh.new()

    def add_organic_path_ribbon(pts, half_w_start, half_w_end, taper_start=False, taper_end=False):
        rows = []
        n_pts = len(pts)
        for idx, (px, pz, y_lift) in enumerate(pts):
            t = idx / max(1, n_pts - 1)
            hw = half_w_start * (1.0 - t) + half_w_end * t
            if taper_start and t < 0.22:
                hw *= math.sin((t / 0.22) * math.pi * 0.5)
            if taper_end and t > 0.80:
                hw *= math.sin(((1.0 - t) / 0.20) * math.pi * 0.5)
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
                wiggle = 0.035 * math.sin(t * 13.0 + u * 2.3)
                wx = px + nx_dir * (hw + wiggle) * u
                wz = pz + nz_dir * (hw + wiggle) * u
                # Edges sink smoothly below terrain surface so path blends without hard borders
                edge_sink = 0.016 * (1.0 - u * u) - 0.018 * (u ** 4)
                # Feather front tip into the terrain
                tip_feather = min(1.0, t / 0.16) if taper_start else 1.0
                wy = get_terrain_height(wx, wz) + (0.008 + edge_sink) * tip_feather + y_lift * (1.0 - 0.35 * u * u)
                row.append(bm_path.verts.new((wx, -wz, wy)))
            rows.append(row)

        for r in range(len(rows) - 1):
            for c in range(len(rows[r]) - 1):
                bm_path.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))

    sz_center = stream_center_z(0.0)  # ~0.22

    # South approach: feathers smoothly from front threshold (z=2.55) onto the south bridge abutment (z=sz+0.60)
    south_steps = 18
    south_pts = []
    for i in range(south_steps + 1):
        t = i / south_steps
        pz = 2.55 * (1.0 - t) + (sz_center + 0.60) * t
        px = 0.06 * math.sin(t * math.pi * 1.4) * (1.0 - t)
        ramp_lift = 0.055 * (t ** 3)
        south_pts.append((px, pz, ramp_lift))

    # North bridge exit into the central crossroads fork (from z=sz-0.60 to z=-0.42)
    north_steps = 8
    north_pts = []
    for i in range(north_steps + 1):
        t = i / north_steps
        pz = (sz_center - 0.60) * (1.0 - t) + (-0.42) * t
        ramp_lift = 0.055 * ((1.0 - t) ** 3)
        north_pts.append((0.0, pz, ramp_lift))

    # Left crossroads branch: climbs northwest past the 'Design Path' sign (-1.58, -0.64)
    left_steps = 22
    left_pts = []
    for i in range(left_steps + 1):
        t = i / left_steps
        px = -2.42 * t - 0.14 * math.sin(t * math.pi)
        pz = -0.26 - 1.34 * (t ** 1.05)
        left_pts.append((px, pz, 0.008 * (1.0 - t)))

    # Right crossroads branch: curves northeast past the 'Play Path' sign (+1.58, -0.60)
    right_steps = 22
    right_pts = []
    for i in range(right_steps + 1):
        t = i / right_steps
        px = 2.42 * t + 0.14 * math.sin(t * math.pi)
        pz = -0.26 - 1.26 * (t ** 1.05)
        right_pts.append((px, pz, 0.008 * (1.0 - t)))

    # Mailbox side spur connecting main south path to the mailbox alcove at (1.18, 1.15)
    spur_pts = [
        (0.16 + 1.04 * (i / 8.0), 1.24 - 0.09 * (i / 8.0), 0.006)
        for i in range(9)
    ]

    add_organic_path_ribbon(south_pts, 0.44, 0.45, taper_start=True, taper_end=False)
    add_organic_path_ribbon(north_pts, 0.46, 0.56, taper_start=False, taper_end=False)
    add_organic_path_ribbon(left_pts, 0.44, 0.30, taper_start=False, taper_end=True)
    add_organic_path_ribbon(right_pts, 0.44, 0.30, taper_start=False, taper_end=True)
    add_organic_path_ribbon(spur_pts, 0.28, 0.36, taper_start=False, taper_end=True)

    c_path_center = hex_to_rgba("#C2A47C")
    c_path_edge = hex_to_rgba("#726146")

    def path_color_fn(wx, wy, wz, nx, ny, nz):
        d = path_distance_and_branch(wx, wz)
        n_p = noise.noise(Vector((wx * 2.2, wz * 2.2, wy)))
        t = max(0.0, min(1.0, (d / 0.38) + 0.18 * n_p))
        return lerp_color(c_path_center, c_path_edge, t)

    finalize_mesh_object("Crossroads_Pathway", bm_path, materials["pathway_earth"], path_color_fn)

    # Irregular flat sandstone stepping flagstones & border cobbles
    bm_stones = bmesh.new()
    stone_coords = [
        (0.02, 2.32, 0.18, 0.13), (-0.11, 2.05, 0.17, 0.13), (0.10, 1.78, 0.18, 0.15),
        (-0.09, 1.50, 0.17, 0.13), (0.09, 1.22, 0.16, 0.13), (-0.04, 0.98, 0.18, 0.14),
        (0.62, 1.20, 0.15, 0.12), (0.94, 1.16, 0.18, 0.15), (1.20, 1.14, 0.26, 0.22),
        (0.0, -0.40, 0.22, 0.17), (-0.42, -0.50, 0.18, 0.14), (-0.84, -0.68, 0.19, 0.14),
        (-1.25, -0.90, 0.17, 0.13), (-1.68, -1.12, 0.18, 0.14), (-2.08, -1.34, 0.15, 0.12),
        (0.42, -0.50, 0.18, 0.14), (0.84, -0.66, 0.19, 0.14), (1.25, -0.87, 0.17, 0.13),
        (1.68, -1.08, 0.18, 0.14), (2.08, -1.28, 0.15, 0.12),
    ]
    for idx, (sx, sz, rx_s, rz_s) in enumerate(stone_coords):
        sy = get_terrain_height(sx, sz) + 0.018
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
    Widened, visually prominent shallow woodland creek with:
    - Sculpted pebble-and-sand creek bed (Stream_Bed)
    - Generous water surface area around and under the bridge (Stream_Water)
    - Arched 13-plank hand-hewn oak footbridge spanning bank-to-bank
    """
    bm_bed = bmesh.new()
    bm_water = bmesh.new()
    steps = 84
    cols = 15
    bed_rows = []
    water_rows = []

    for i in range(steps + 1):
        x = -3.65 + 7.20 * (i / steps)
        cz = stream_center_z(x)
        rf = island_radial_factor(x, cz)
        if rf > 0.84:
            continue
        dx = 0.07
        dz = stream_center_z(x + dx) - cz
        length = math.hypot(dx, dz)
        nx_d, nz_d = -dz / length, dx / length

        end_taper = min(1.0, (0.84 - rf) / 0.14)
        hw = stream_half_width(x) * (0.48 + 0.52 * end_taper)
        bed_center_y = get_terrain_height(x, cz)
        water_y = bed_center_y + 0.175 * (0.65 + 0.35 * end_taper)

        b_row = []
        w_row = []
        for c in range(cols):
            u = (c / (cols - 1)) * 2.0 - 1.0
            wx = x + nx_d * hw * u
            wz = cz + nz_d * hw * u

            # Pebble riverbed concave profile
            bed_y = bed_center_y + 0.14 * (u * u) + 0.015 * math.sin(x * 8.0 + u * 6.0)
            b_row.append(bm_bed.verts.new((wx, -wz, bed_y)))

            # Gentle surface current undulation
            ripple = 0.008 * math.sin(x * 4.8 + u * 3.0) * (1.0 - 0.4 * u * u)
            w_row.append(bm_water.verts.new((wx, -wz, water_y + ripple)))
        bed_rows.append(b_row)
        water_rows.append(w_row)

    for r in range(len(bed_rows) - 1):
        for c in range(len(bed_rows[r]) - 1):
            bm_bed.faces.new((bed_rows[r][c], bed_rows[r][c + 1], bed_rows[r + 1][c + 1], bed_rows[r + 1][c]))
            bm_water.faces.new((water_rows[r][c], water_rows[r][c + 1], water_rows[r + 1][c + 1], water_rows[r + 1][c]))

    c_bed_deep = hex_to_rgba("#1E332E")
    c_bed_pebble = hex_to_rgba("#524D40")
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

    c_water_deep = hex_to_rgba("#1C5854")
    c_water_mid = hex_to_rgba("#327A73")
    c_water_shallow = hex_to_rgba("#5A8C79")
    c_water_foam = hex_to_rgba("#A8CFC4")

    def water_color_fn(wx, wy, wz, nx, ny, nz):
        cz = stream_center_z(wx)
        hw = max(0.25, stream_half_width(wx))
        edge_t = min(1.0, abs(wz - cz) / hw)
        if edge_t < 0.55:
            col = lerp_color(c_water_deep, c_water_mid, edge_t / 0.55)
        else:
            col = lerp_color(c_water_mid, c_water_shallow, (edge_t - 0.55) / 0.45)

        n_w = noise.noise(Vector((wx * 3.0, wz * 3.0, 0.5)))
        if n_w > 0.32 or edge_t > 0.84:
            col = lerp_color(col, c_water_foam, 0.32)
        return col

    finalize_mesh_object("Stream_Water", bm_water, materials["stream_water"], water_color_fn)

    # Handcrafted Arched Wooden Bridge spanning the widened creek (span = 1.44, 13 planks)
    bm_bridge = bmesh.new()
    bridge_center_z = stream_center_z(0.0)
    bridge_span = 1.44
    bridge_width = 1.04
    num_planks = 13

    y_south_ground = get_terrain_height(0.0, bridge_center_z + bridge_span * 0.5)
    y_north_ground = get_terrain_height(0.0, bridge_center_z - bridge_span * 0.5)
    base_abutment_y = max(y_south_ground, y_north_ground) + 0.025

    def arch_height(z_local):
        norm = z_local / (bridge_span * 0.5)
        return base_abutment_y + 0.16 * max(0.0, 1.0 - norm * norm)

    # Timber sill beams embedded into both riverbanks at the bridge ends
    for end_sign in (-1.0, 1.0):
        wz_sill = bridge_center_z + end_sign * (bridge_span * 0.49)
        wy_sill = arch_height(end_sign * (bridge_span * 0.49)) - 0.035
        add_beveled_box(
            bm_bridge,
            lambda co, wz_sill=wz_sill, wy_sill=wy_sill: Vector((
                co.x * (bridge_width + 0.16),
                -(wz_sill + co.y * 0.16),
                wy_sill + co.z * 0.11,
            )),
            bevel_offset=0.012,
            segments=2,
        )

    # Two arched timber stringer beams spanning between the bank sills
    for side in (-0.40, 0.40):
        segs = 16
        beam_verts = []
        for i in range(segs + 1):
            zl = -bridge_span * 0.50 + bridge_span * 1.00 * (i / segs)
            wz = bridge_center_z + zl
            wy = arch_height(zl) - 0.040
            beam_verts.append((side, wz, wy))
        for i in range(segs):
            x0, z0, y0 = beam_verts[i]
            x1, z1, y1 = beam_verts[i + 1]
            ret = bmesh.ops.create_cube(bm_bridge, size=1.0)
            for v in ret["verts"]:
                t = v.co.y + 0.5
                vx = x0 + v.co.x * 0.090
                vz = z0 * (1 - t) + z1 * t
                vy = (y0 * (1 - t) + y1 * t) + v.co.z * 0.080
                v.co = Vector((vx, -vz, vy))

    # 13 individual beveled oak deck planks
    for ip in range(num_planks):
        u = (ip / (num_planks - 1)) * 2.0 - 1.0
        zl = u * (bridge_span * 0.45)
        wz = bridge_center_z + zl
        wy = arch_height(zl) + 0.018
        slope = -0.22 * u
        w_var = bridge_width * (0.99 + 0.02 * math.sin(ip * 2.3))

        def plank_tf(co, wz=wz, wy=wy, slope=slope, w_var=w_var):
            px = co.x * w_var
            pz = co.y * 0.092
            py = co.z * 0.046
            rz = pz * math.cos(slope) - py * math.sin(slope)
            ry = pz * math.sin(slope) + py * math.cos(slope)
            return Vector((px, -(wz + rz), wy + ry))

        add_beveled_box(bm_bridge, plank_tf, bevel_offset=0.009, segments=2)

    # 6 vertical beveled posts + curved double handrails
    for side in (-0.47, 0.47):
        for post_z_local in (-0.58, 0.0, 0.58):
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
# 4. ARTISANAL WOODEN SIGNPOSTS ('Design Path' & 'Play Path') + HERO MAILBOX
# ==============================================================================

def build_signpost(name, label_text, x, z, yaw_deg, arrow_dir, materials):
    """
    Handcrafted woodland wayfinding signpost:
    - Left sign: 'Design Path'
    - Right sign: 'Play Path'
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
        lambda co: to_world(
            co.x * (0.155 - 0.02 * (co.z + 0.5)),
            0.74 + co.z * 1.56,
            co.y * (0.155 - 0.02 * (co.z + 0.5)),
        ),
        bevel_offset=0.016,
        segments=2,
    )

    ret_cap = bmesh.ops.create_cube(bm_post, size=1.0)
    for v in ret_cap["verts"]:
        t_top = 0.50 if v.co.z > 0 else 1.22
        v.co = to_world(v.co.x * 0.20 * t_top, 1.55 + v.co.z * 0.11, v.co.y * 0.20 * t_top)

    add_beveled_box(
        bm_post,
        lambda co: to_world(co.x * 0.26, 0.08 + co.z * 0.16, co.y * 0.26),
        bevel_offset=0.014,
        segments=2,
    )

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

    bm_board = bmesh.new()
    board_w = 1.56
    board_h = 0.44
    board_d = 0.092
    board_y = 1.15

    def board_tf(co):
        lx = co.x * board_w
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

    for trim_z in (-0.205, 0.205):
        trim_x_shift = 0.11 if arrow_dir < 0 else -0.11
        add_beveled_box(
            bm_board,
            lambda co, tz=trim_z, txs=trim_x_shift: to_world(
                txs + co.x * 1.14,
                board_y + tz + co.z * 0.040,
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

    bpy.ops.object.text_add(location=(0, 0, 0))
    txt_obj = bpy.context.active_object
    txt_obj.name = f"{name}_Label3D"
    txt_obj.data.body = label_text
    txt_obj.data.align_x = 'CENTER'
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.size = 0.202
    txt_obj.data.space_character = 1.05
    txt_obj.data.extrude = 0.013
    txt_obj.data.bevel_depth = 0.0020
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

    c_mb_dark = hex_to_rgba("#143329")
    c_mb_top = hex_to_rgba("#275948")
    finalize_mesh_object(
        "Mailbox_Body",
        bm_body,
        materials["mailbox_forest_metal"],
        lambda wx, wy, wz, nx, ny, nz: lerp_color(c_mb_dark, c_mb_top, 0.4 + 0.5 * max(0.0, ny)),
    )

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


# ==============================================================================
# 5. PURPOSEFULLY CLUSTERED BOTANICAL VEGETATION & CREEK BANK STONES
# ==============================================================================

def build_rocks_and_botanical_groundcover(materials):
    """
    Purposefully clustered rocks, ferns, varied-scale 3D grass clumps, and wildflowers
    anchored naturally around creek banks, boulders, sign bases, and bridge abutments.
    """
    bm_rocks = bmesh.new()
    rock_placements = [
        # NW spring headwater grotto boulders
        (-3.68, -0.58, 0.46, 0.33, 0.38), (-3.32, -0.10, 0.34, 0.25, 0.30), (-3.48, -0.98, 0.38, 0.28, 0.32),
        # SE cascade rocks
        (3.46, 1.02, 0.42, 0.30, 0.35), (3.16, 0.54, 0.30, 0.22, 0.26),
        # Creek bank & bridge wing-wall stones flanking the widened stream
        (-2.22, 0.36, 0.30, 0.21, 0.25), (-1.32, 0.12, 0.26, 0.18, 0.22),
        (-0.62, 0.62, 0.26, 0.20, 0.23), (0.64, -0.08, 0.25, 0.18, 0.22),
        (-0.64, -0.14, 0.24, 0.18, 0.21), (0.62, 0.64, 0.25, 0.19, 0.22),
        (1.62, 0.72, 0.28, 0.20, 0.24), (2.42, 0.92, 0.33, 0.23, 0.27),
        # Submerged creek bed cobbles
        (-1.85, -0.06, 0.20, 0.10, 0.16), (-0.82, 0.14, 0.18, 0.09, 0.15),
        (0.88, 0.35, 0.19, 0.10, 0.16), (1.88, 0.58, 0.21, 0.11, 0.17),
        # Foreground left knoll outcrop & signpost/mailbox anchor stones
        (-1.68, 1.52, 0.32, 0.21, 0.25), (-1.42, 1.66, 0.22, 0.15, 0.18),
        (-1.92, -0.74, 0.26, 0.20, 0.22), (1.92, -0.70, 0.26, 0.20, 0.22),
        (1.46, 1.18, 0.22, 0.16, 0.19), (-0.15, -2.18, 0.38, 0.26, 0.30),
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

    # Purposefully Clustered Ferns + Varied-Scale 3D Grass Tufts + Creek Lily Pads
    bm_foliage_ground = bmesh.new()

    fern_clusters = [
        # Anchored beside the foreground left stone outcrop & creek banks
        (-1.88, 1.38, 0.36, 7), (-1.32, 1.72, 0.24, 5), (-2.38, 0.58, 0.34, 6),
        (1.68, 1.32, 0.30, 6), (2.48, 1.12, 0.34, 7), (-2.62, -0.45, 0.38, 8),
        (2.62, -0.28, 0.35, 7), (-0.88, -1.58, 0.32, 6), (0.88, -1.55, 0.30, 6),
        (-0.18, -1.95, 0.36, 7), (-1.82, -0.56, 0.26, 6), (1.82, -0.52, 0.26, 6),
        (1.42, 0.96, 0.24, 5), (-0.76, 0.72, 0.25, 5), (0.76, 0.70, 0.23, 5),
    ]
    for c_idx, (fx, fz, f_scale, num_fronds) in enumerate(fern_clusters):
        fy = get_terrain_height(fx, fz) - 0.015
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

    # Purposefully grouped grass families (parent clump + 2 smaller satellite tufts at varied scales)
    grass_anchor_families = [
        # (anchor_x, anchor_z, base_scale)
        (-1.48, 1.38, 0.26), (-0.58, 0.82, 0.22), (0.56, 0.84, 0.21),
        (-1.22, 0.34, 0.25), (1.35, 0.84, 0.24), (1.52, 1.24, 0.22),
        (-1.72, -0.48, 0.23), (1.72, -0.44, 0.23), (-0.72, -0.35, 0.20),
        (0.72, -0.35, 0.20), (-0.42, -1.28, 0.22), (0.42, -1.25, 0.22),
        (-2.22, -0.88, 0.25), (2.22, -0.84, 0.25), (-0.46, 1.92, 0.19),
        (0.46, 1.85, 0.18),
    ]
    for fam_idx, (ax, az, b_scale) in enumerate(grass_anchor_families):
        sub_tufts = [
            (0.0, 0.0, b_scale * 1.15),
            (0.14 * math.cos(fam_idx * 1.7), 0.14 * math.sin(fam_idx * 1.7), b_scale * 0.78),
            (-0.12 * math.sin(fam_idx * 2.3), 0.12 * math.cos(fam_idx * 2.3), b_scale * 0.58),
        ]
        for s_idx, (dx, dz, g_scale) in enumerate(sub_tufts):
            gx, gz = ax + dx, az + dz
            gy = get_terrain_height(gx, gz) - 0.015
            num_blades = 6 + ((fam_idx + s_idx) % 4)
            for ib in range(num_blades):
                ang = (2.0 * math.pi * ib) / num_blades + fam_idx * 0.71 + s_idx * 1.1
                offset_r = 0.025 + 0.035 * ((ib % 3) * 0.5)
                bx0 = gx + math.cos(ang) * offset_r
                bz0 = gz + math.sin(ang) * offset_r
                blade_h = g_scale * (0.72 + 0.48 * ((ib * 5 + fam_idx) % 4) / 3.0)
                lean_r = blade_h * (0.36 + 0.22 * (ib % 2))
                blade_w = 0.024 * (0.82 + 0.32 * (ib % 2))
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

    c_fern_base = hex_to_rgba("#22452E")
    c_fern_tip = hex_to_rgba("#769C5E")

    def ground_foliage_color_fn(wx, wy, wz, nx, ny, nz):
        gy = get_terrain_height(wx, wz)
        h_rel = max(0.0, min(1.0, (wy - gy) / 0.22))
        n_f = noise.noise(Vector((wx * 2.0, wz * 2.0, wy)))
        return lerp_color(c_fern_base, c_fern_tip, min(1.0, h_rel * 0.85 + 0.15 + 0.15 * n_f))

    finalize_mesh_object("Forest_Ferns", bm_foliage_ground, materials["foliage_moss"], ground_foliage_color_fn)

    # Purposefully Clustered Wildflower Patches anchored beside boulders & posts
    bm_flowers = bmesh.new()
    flower_clusters = [
        (-1.76, -0.56, 4), (-1.48, 1.36, 4), (1.76, -0.52, 4),
        (1.38, 1.20, 4), (-0.64, 0.76, 3), (0.64, 0.78, 3),
        (-0.38, -1.62, 3), (0.42, -1.52, 3),
    ]
    for idx, (cx, cz, count) in enumerate(flower_clusters):
        for sub in range(count):
            ang_s = idx * 1.9 + sub * 2.15
            rad_s = 0.05 + 0.055 * (sub % 3)
            fx = cx + math.cos(ang_s) * rad_s
            fz = cz + math.sin(ang_s) * rad_s
            fy = get_terrain_height(fx, fz) + 0.042 + 0.016 * (sub % 2)
            for ip in range(4):
                p_ang = (math.pi * 0.5) * ip + sub * 0.4
                px = fx + math.cos(p_ang) * 0.020
                pz = fz + math.sin(p_ang) * 0.020
                ret = bmesh.ops.create_icosphere(bm_flowers, subdivisions=1, radius=0.020)
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

    aim_camera((-0.35, -12.6, 7.1), (0.0, 0.0, 0.35))
    scene.render.filepath = os.path.join(RENDER_DIR, "blender_view_initial.png")
    bpy.ops.render.render(write_still=True)

    aim_camera((5.2, -11.6, 7.3), (-0.05, 0.0, 0.35))
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
        "stream_water": make_pbr_material("Stream_Water_Mat", "#2E6A63", roughness=0.20, metallic=0.06),
        "wood_oak": make_pbr_material("Wood_Oak_Mat", "#9D6E48", roughness=0.66),
        "wood_post": make_pbr_material("Wood_Post_Mat", "#784F30", roughness=0.70),
        "wood_sign_plaque": make_pbr_material("Wood_Sign_Plaque_Mat", "#54331C", roughness=0.60),
        "wood_bark": make_pbr_material("Wood_Bark_Mat", "#6A4B35", roughness=0.84),
        "foliage_deep": make_pbr_material("Foliage_Deep_Mat", "#26543F", roughness=0.74),
        "foliage_moss": make_pbr_material("Foliage_Moss_Mat", "#4E724A", roughness=0.75),
        "foliage_sage": make_pbr_material("Foliage_Sage_Mat", "#73916C", roughness=0.76),
        "ivory_lettering": make_pbr_material("Ivory_Lettering_Mat", "#F5EFE3", roughness=0.36, use_vertex_color=False),
        "mailbox_forest_metal": make_pbr_material("Mailbox_Forest_Metal_Mat", "#1C4537", roughness=0.38, metallic=0.26, use_vertex_color=False),
        "champagne_brass": make_pbr_material("Champagne_Brass_Mat", "#DCC89A", roughness=0.28, metallic=0.74, use_vertex_color=False),
    }

    build_island_terrain(materials)
    build_embedded_identity_plaque(materials)
    build_pathway_and_cobbles(materials)
    build_stream_and_bridge(materials)
    build_rocks_and_botanical_groundcover(materials)

    # Spatial Hierarchy & Layered Composition of 7 Varied Trees across 3 Archetypes
    create_tree_archetype_oak("Tree_NW_Hero", -2.55, -2.05, 1.24, -0.18, -0.10, 0, materials)
    create_tree_archetype_cedar("Tree_N_Left", -1.35, -2.55, 1.18, -0.06, -0.08, 2, materials)
    create_tree_archetype_birch("Tree_N_Center", 0.92, -2.48, 0.94, 0.14, -0.08, 1, materials)
    create_tree_archetype_cedar("Tree_N_Right", 2.15, -2.28, 1.28, 0.10, -0.10, 2, materials)
    create_tree_archetype_oak("Tree_NE_Hero", 3.05, -1.52, 1.06, 0.18, -0.05, 1, materials)
    create_tree_archetype_birch("Tree_W_Flank", -3.22, -0.65, 0.90, -0.20, 0.06, 1, materials)
    create_tree_archetype_cedar("Tree_E_Flank", 3.18, -0.28, 0.84, 0.16, 0.08, 0, materials)

    # Renamed Interactive 3D Wooden Signposts ('Design Path' & 'Play Path') + Hero Mailbox
    build_signpost("Signpost_UX", "Design Path", -1.58, -0.64, 18.0, -1, materials)
    build_signpost("Signpost_Game", "Play Path", 1.58, -0.60, -18.0, 1, materials)
    build_woodland_mailbox(1.18, 1.14, -22.0, materials)

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
    print(f"Exported V3 runtime GLB to: {GLB_OUT}")

    setup_lighting_and_render_previews()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Saved V3 master Blender source to: {BLEND_OUT}")


if __name__ == "__main__":
    main()
