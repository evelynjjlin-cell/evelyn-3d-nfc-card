# 3D Asset Package & Provenance Manifest (V5 Unified 3D Environment & Interaction Refinement)
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin  
**Authoring Tool:** Blender 5.0.0 (`/Applications/Blender.app/Contents/MacOS/Blender`)  
**License:** 100% Original Custom-Authored Assets for Evelyn Lin (No third-party asset packs or Friends Community assets used)

---

## 1. File Inventory & Runtime Statistics

| Asset Path | Role | Format | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `blender/build_crossroads_scene.py` | Procedural & BMesh Sculpting Pipeline | Python (`bpy` / `bmesh`) | ~44 KB | Deterministic Blender 5.0 V5 generator authoring the 3-tier botanical tree hierarchy, watertight 4-layer wooden signboards (`Design Trail` / `Game Trail`), unified `112×224` terrain surface with vertex-splatted woodland trails, stitched cliff underside, widened grotto-bounded creek, and front cliff identity plaque. |
| `assets/source/crossroads_master.blend` | Master Editable 3D Source | Blender 5.0 (`.blend`) | 7.5 MB | Editable master Blender scene containing all 39 separated objects, vertex color layers (`Col`), PBR material nodes, lighting rig, and preview camera. |
| `public/models/crossroads_environment.glb` | Optimized Runtime 3D Scene | Binary glTF 2.0 (`.glb`) | 8.3 MB (`~2.05 MB` gzip) | Optimized Y-up runtime scene with baked `COLOR_0` vertex attributes loaded by React Three Fiber. |
| `assets/renders/blender_view_initial.png` | Blender Reference Render (Initial) | PNG (`960×1200`) | ~430 KB | Headless Blender EEVEE verification render of the initial V5 collectible composition. |
| `assets/renders/blender_view_rotated.png` | Blender Reference Render (Rotated) | PNG (`960×1200`) | ~435 KB | Headless Blender EEVEE verification render of the rotated V5 collectible composition. |

### Geometry & Polygon Budget (V5 High-Fidelity Build)
- **Total Vertices:** `201,946`
- **Total Triangles:** `370,572`
- **Tree Architecture Triangles (7 trees across 3 archetypes):** `226,312` (`~32,330` triangles per tree on average)
- **Total Scene Objects / Draw Primitives:** `39`

---

## 2. V5 Scene Graph & Collectible Architecture

- **Embedded 3D Personal Identity Plaque (Front Cliff Edge)**
  - `Identity_Plaque_Frame` — Beveled champagne-brass outer bezel (`2.66 × 0.68`) with 4 corner rivets mounted into the chiseled front stone mantle (`Island_Soil_Rim`).
  - `Identity_Plaque_Plate` — Recessed deep-forest oxidized slate/bronze inner tablet (`2.50 × 0.55`).
  - `Identity_Plaque_Name3D` — Extruded and beveled 3D relief typography: **`Evelyn Lin`**.
  - `Identity_Plaque_Title3D` — Extruded and beveled 3D relief subtitle: **`UX & INTERACTIVE EXPERIENCE DESIGNER`**.
- **Unified Watertight Floating Island & Naturalized Woodland Trails**
  - `Island_Terrain_Top` — `112` concentric radial rings × `224` segments of asymmetric multi-elevation terrain with integrated vertex-splatted woodland trails (`trail_wear_weight`), subtle compaction (`≤ 0.011`), organic grass transition borders, northwest/northeast hillocks, and dry front-right mailbox terrace.
  - `Island_Rock_Underside` & `Island_Soil_Rim` — Unified craggy rock-and-earth underside whose top ring (`ring 0`) is mathematically stitched directly to the exact 3D vertex coordinates (`outer_rim_coords`) of `Island_Terrain_Top` to eliminate all rim gaps or protruding rock slivers.
  - `Pathway_Cobbles` — Flat river-worn stepping stones deeply bedded into the terrain compaction bed (`top surface +0.010` above dirt, bottom skirt embedded `-0.028` below).
- **Widened Woodland Creek, Boulder Grottos & Integrated Arched Bridge**
  - `Stream_Bed` — Concave pebble-and-silt riverbed mesh visible beneath the translucent water surface, enclosed at both stream ends by natural spring/cascade boulder grottos (`Environment_Rocks`).
  - `Stream_Water` — Widened shallow creek with an enlarged water pool around and under the bridge (`stream_half_width`), depth-tinted emerald-teal to amber-sage vertex color gradients, and balanced surface roughness (`0.56`) eliminating harsh white specular glare.
  - `Wooden_Bridge` — Arched 13-plank hand-hewn oak footbridge (`z = 0.08 → 0.88`) with timber sill beams and stone-and-earth abutments meeting the natural trail grades flush.
- **Three High-Fidelity Sculpted Tree Archetypes & Purposefully Clustered Botanicals**
  - `Tree_NW_Hero_*`, `Tree_NE_Hero_*` (*Archetype A — Broadleaf Hero Oak*): Root-flared grooved trunk, primary/secondary/tertiary fork branches, dark interior shadow core lobes, medium chiseled foliage pads, and outer dimensional 3D leaf-spray tufts.
  - `Tree_N_Center_*`, `Tree_W_Flank_*` (*Archetype B — Slender Multi-Stem Stream Birch*): Twin curving silver-birch trunks with dark horizontal lenticel bands, high branching forks, and airy multi-layered crown clusters.
  - `Tree_N_Left_*`, `Tree_N_Right_*`, `Tree_E_Flank_*` (*Archetype C — Layered Evergreen Spruce*): Fibonacci-spiral (`2.39996 rad`) staggered bough clusters across 8 elevation tiers with downward-draping individual frond tips and sculpted bark ridges.
  - `Environment_Rocks`, `Forest_Ferns`, `Wildflowers` — Purposefully clustered boulders, spring/outflow water grottos, asymmetric fern rosettes, multi-scale 3D grass tufts, and wildflowers anchored around boulders, creek banks, and posts.
- **Interactive 3D Landmarks (Final Locked V5 Naming)**
  - `Signpost_UX_Post`, `Signpost_UX_Board`, `Signpost_UX_Label3D` — Left crossroads wooden signpost constructed as a single watertight 4-layer extruded plank (`lz = +0.096` to `+0.172`) with non-penetrating rear mortise brackets (`lz ≤ +0.095`) and raised 3D relief typography labeled **`Design Trail`** (conceptual theme: *Design Stories*; opens `https://evelynjlin.com`).
  - `Signpost_Game_Post`, `Signpost_Game_Board`, `Signpost_Game_Label3D` — Right crossroads wooden signpost labeled **`Game Trail`** (conceptual theme: *Game Worlds*; opens the `"New world in progress."` modal until `gamePortfolioUrl` is set).
  - `Mailbox_Post`, `Mailbox_Body`, `Mailbox_Door`, `Mailbox_Letter`, `Mailbox_Flag` — Hero-prop vintage woodland mailbox anchored on the dry front-right terrace (`[1.28, y, 1.36]`) that animates open to unfold the physical cream-parchment contact letter.
