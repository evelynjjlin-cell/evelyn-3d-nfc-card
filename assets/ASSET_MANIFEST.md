# 3D Asset Package & Provenance Manifest (V3 Object-First Collectible Transformation)
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin  
**Authoring Tool:** Blender 5.0.0 (`/Applications/Blender.app/Contents/MacOS/Blender`)  
**License:** 100% Original Custom-Authored Assets for Evelyn Lin (No third-party asset packs or Friends Community assets used)

---

## 1. File Inventory & Runtime Statistics

| Asset Path | Role | Format | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `blender/build_crossroads_scene.py` | Procedural & BMesh/Voxel Sculpting Pipeline | Python (`bpy` / `bmesh`) | ~41 KB | Deterministic Blender 5.0 V3 generator authoring the embedded 3D front identity plaque, widened pebble-bed creek, cleaned-up front terrain contour, purposefully clustered vegetation, 3 tree archetypes, and renamed `Design Path` / `Play Path` signs. |
| `assets/source/crossroads_master.blend` | Master Editable 3D Source | Blender 5.0 (`.blend`) | ~2.3 MB | Editable master Blender scene containing all 40 separated objects, vertex color layers (`Col`), PBR material nodes, lighting rig, and preview camera. |
| `public/models/crossroads_environment.glb` | Optimized Runtime 3D Scene | Binary glTF 2.0 (`.glb`) | ~3.1 MB (`~840 KB` gzip) | Optimized Y-up runtime scene with baked `COLOR_0` vertex attributes loaded by React Three Fiber. |
| `assets/renders/blender_view_initial.png` | Blender Reference Render (Initial) | PNG (`960×1200`) | ~420 KB | Headless Blender EEVEE verification render of the initial V3 collectible composition. |
| `assets/renders/blender_view_rotated.png` | Blender Reference Render (Rotated) | PNG (`960×1200`) | ~425 KB | Headless Blender EEVEE verification render of the rotated V3 collectible composition. |

### Geometry & Polygon Budget
- **Total Vertices:** `77,557`
- **Total Triangles:** `133,538`
- **Total Scene Objects / Draw Primitives:** `40`

---

## 2. V3 Scene Graph & Collectible Architecture

- **Embedded 3D Personal Identity Plaque (Front Cliff Edge)**
  - `Identity_Plaque_Frame` — Beveled champagne-brass outer bezel (`2.66 × 0.68`) with 4 corner rivets mounted into the chiseled front stone mantle (`Island_Soil_Rim`).
  - `Identity_Plaque_Plate` — Recessed deep-forest oxidized slate/bronze inner tablet (`2.50 × 0.55`).
  - `Identity_Plaque_Name3D` — Extruded and beveled 3D relief typography: **`Evelyn Lin`**.
  - `Identity_Plaque_Title3D` — Extruded and beveled 3D relief subtitle: **`UX & INTERACTIVE EXPERIENCE DESIGNER`**.
- **Sculpted Floating Island & Cleaned-Up Front Terrain**
  - `Island_Terrain_Top` — 68 concentric radial rings × 152 segments of asymmetric multi-elevation terrain with northwest/northeast ridges, intentional foreground knolls (front-left mossy outcrop knoll and front-right mailbox terrace), smooth rim attenuation around the creek outlet, and 4-channel vertex-color terrain splatting.
  - `Island_Rock_Underside` & `Island_Soil_Rim` — Unified craggy rock-and-earth underside with vertical cliff buttresses, hanging root systems, and the front chiseled stone plaque mantle.
- **Widened Woodland Creek, Pebble Riverbed & Integrated Arched Bridge**
  - `Stream_Bed` — Concave pebble-and-silt riverbed mesh visible beneath the translucent water surface.
  - `Stream_Water` — Widened shallow creek with an enlarged water pool around and under the bridge, depth-tinted emerald-teal to amber-sage vertex color gradients, and animated surface current detail.
  - `Wooden_Bridge` — Arched 13-plank hand-hewn oak footbridge anchored into bank timber sill beams and stone-and-earth abutments.
  - `Crossroads_Pathway` & `Pathway_Cobbles` — Continuous sunken loam pathways with feathered front-terrain blending, sandstone flagstones, and a cobblestone spur to the mailbox alcove.
- **Three Distinct Sculpted Tree Archetypes & Purposefully Clustered Botanicals**
  - `Tree_NW_Hero_*`, `Tree_NE_Hero_*` (Archetype 1: Gnarled Ancient Oak)
  - `Tree_N_Center_*`, `Tree_W_Flank_*` (Archetype 2: Slender Twin-Stem Stream Birch)
  - `Tree_N_Left_*`, `Tree_N_Right_*`, `Tree_E_Flank_*` (Archetype 3: Layered Woodland Cedar)
  - `Environment_Rocks`, `Forest_Ferns`, `Wildflowers` — Purposefully clustered boulders, asymmetric fern rosettes, multi-scale 3D grass families, and wildflowers anchored around boulders, creek banks, and posts.
- **Interactive 3D Landmarks**
  - `Signpost_UX_Post`, `Signpost_UX_Board`, `Signpost_UX_Label3D` — Left crossroads wooden signpost labeled **`Design Path`** (`https://evelynjlin.com`).
  - `Signpost_Game_Post`, `Signpost_Game_Board`, `Signpost_Game_Label3D` — Right crossroads wooden signpost labeled **`Play Path`**.
  - `Mailbox_Post`, `Mailbox_Body`, `Mailbox_Door`, `Mailbox_Letter`, `Mailbox_Flag` — Hero-prop vintage woodland mailbox that animates open to unfold the physical cream-parchment contact letter.
