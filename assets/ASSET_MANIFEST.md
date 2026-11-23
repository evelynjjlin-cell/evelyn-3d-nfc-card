# 3D Asset Package & Provenance Manifest (V2 Art Direction Overhaul)
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin  
**Authoring Tool:** Blender 5.0.0 (`/Applications/Blender.app/Contents/MacOS/Blender`)  
**License:** 100% Original Custom-Authored Assets for Evelyn Lin (No third-party asset packs or Friends Community assets used)

---

## 1. File Inventory & Runtime Statistics

| Asset Path | Role | Format | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `blender/build_crossroads_scene.py` | Procedural & BMesh/Voxel Sculpting Pipeline | Python (`bpy` / `bmesh`) | ~36 KB | Deterministic Blender 5.0 V2 generator authoring 3 distinct tree archetypes, craggy island terrain, integrated bridge abutments, 3D vertex-color AO/sunlight gradients, and hero props. |
| `assets/source/crossroads_master.blend` | Master Editable 3D Source | Blender 5.0 (`.blend`) | ~4.2 MB | Editable master Blender scene containing all 35 separated objects, vertex color layers (`Col`), PBR material nodes, lighting rig, and preview camera. |
| `public/models/crossroads_environment.glb` | Optimized Runtime 3D Scene | Binary glTF 2.0 (`.glb`) | ~3.9 MB (`~1.05 MB` gzip) | Optimized Y-up runtime scene with baked `COLOR_0` vertex attributes loaded by React Three Fiber. |
| `assets/renders/blender_view_initial.png` | Blender Reference Render (Initial) | PNG (`960×1200`) | ~410 KB | Headless Blender EEVEE verification render of the initial V2 composition. |
| `assets/renders/blender_view_rotated.png` | Blender Reference Render (Rotated) | PNG (`960×1200`) | ~415 KB | Headless Blender EEVEE verification render of the rotated V2 composition. |

### Geometry & Polygon Budget
- **Total Vertices:** `60,772`
- **Total Triangles:** `107,934`
- **Total Scene Objects / Draw Primitives:** `35`

---

## 2. V2 Art Direction Overhaul — Scene Graph & Material System

- **Sculpted Floating Island & Cliff Outcrops**
  - `Island_Terrain_Top` — 64 concentric radial rings × 144 segments of asymmetric multi-elevation terrain with northwest/northeast ridges, carved diagonal creek valley, integrated bridge abutment ramps, irregular draping turf overhang, and 4-channel vertex-color terrain splatting (meadow grass, creek moss, sunlit ridge, pathside loam).
  - `Island_Rock_Underside` — 36-ring × 144-segment unified craggy rock-and-earth underside with vertical cliff buttresses, stone ledges, and eroded soil-to-rock vertex color transitions (replacing flat horizontal layers).
  - `Island_Soil_Rim` — Integrated cliff buttress shelves and hanging root tendrils underneath the turf lip.
- **Three Distinct Sculpted Tree Archetypes (with VoxelFusion + CorrectiveSmooth + 3D Vertex Color Gradients)**
  - **Archetype 1 — Gnarled Ancient Woodland Oak (`Tree_NW_Hero`, `Tree_NE_Hero`):** S-curved root-buttressed trunk with 5 diverging limbs, visible secondary branches, and 22 varied foliage bough clusters fused via Voxel Remesh + Corrective Smooth + organic leaf-tuft displacement.
  - **Archetype 2 — Slender Twin-Stem Stream Birch / Alder (`Tree_N_Center`, `Tree_W_Flank`):** Graceful leaning twin trunks with pale cinereous bark and dark horizontal lenticel markings, supporting airy multi-level foliage pads.
  - **Archetype 3 — Layered Woodland Cedar / Spruce (`Tree_N_Left`, `Tree_N_Right`, `Tree_E_Flank`):** Tall vertical conifer with spirally arranged, drooping scalloped bough clusters providing strong vertical silhouette contrast.
- **Shallow Woodland Creek, Integrated Bridge & Crossroads Pathways**
  - `Stream_Water` — Varied-width shallow creek with depth-tinted olive-teal to amber-sage vertex color gradients and subtle flow ripples.
  - `Wooden_Bridge` — Arched 11-plank hand-hewn oak footbridge anchored into bank timber sill beams and stone-and-earth abutments.
  - `Crossroads_Pathway` & `Pathway_Cobbles` — Continuous sunken loam pathways with feathered borders, sandstone flagstones, and a dedicated cobblestone spur leading to the mailbox alcove.
- **Botanical Ground Cover & Boulders**
  - `Environment_Rocks` — Chiseled mossy boulders at the NW spring grotto, creek banks, submerged riverbed, and ridge vista.
  - `Forest_Ferns` — Asymmetric pinnate woodland fern rosettes and multi-blade 3D grass clumps with root-to-tip vertex color gradients.
  - `Wildflowers` — Clustered multi-petal wildflower blossoms tucked beside rocks and signposts.
- **Interactive Hero Landmarks**
  - `Signpost_UX_Post`, `Signpost_UX_Board`, `Signpost_UX_Label3D` — Tapered chamfered oak post with pyramid cap, wrought-iron mounting straps, molded directional plaque, and low-relief chiseled `UX Portfolio` lettering.
  - `Signpost_Game_Post`, `Signpost_Game_Board`, `Signpost_Game_Label3D` — Matching artisanal signpost with low-relief chiseled `Game Portfolio` lettering.
  - `Mailbox_Post`, `Mailbox_Body`, `Mailbox_Door`, `Mailbox_Letter`, `Mailbox_Flag` — Hero-prop vintage woodland mailbox on a cobblestone alcove with curved corbel brace, riveted forest-green hood, articulated brass door with pull handle and louver slot, emerging crimson wax-sealed letter, and signal flag.
