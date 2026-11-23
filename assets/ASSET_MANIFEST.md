# 3D Asset Package & Provenance Manifest
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin  
**Authoring Tool:** Blender 5.0.0 (`/Applications/Blender.app/Contents/MacOS/Blender`)  
**License:** 100% Original Custom-Authored Assets for Evelyn Lin (No third-party asset packs or Friends Community assets used)

---

## 1. File Inventory

| Asset Path | Role | Format | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `blender/build_crossroads_scene.py` | Procedural & BMesh Sculpting Script | Python (`bpy` / `bmesh`) | ~28 KB | Deterministic Blender 5.0 generator script authoring all high-poly meshes, bevels, 3D lettering, materials, and verification renders. |
| `assets/source/crossroads_master.blend` | Master Editable 3D Source | Blender 5.0 (`.blend`) | ~1.3 MB | Editable master Blender scene containing all separated objects, PBR material nodes, lighting rig, and preview camera. |
| `public/models/crossroads_environment.glb` | Runtime 3D Environment | Binary glTF 2.0 (`.glb`) | ~1.8 MB | Optimized Y-up runtime scene loaded by React Three Fiber with custom shader & interaction enhancements. |
| `assets/renders/blender_view_initial.png` | Blender Reference Render (Portrait) | PNG (`780×1688`) | ~360 KB | Headless Blender EEVEE verification render of the initial mobile portrait composition. |
| `assets/renders/blender_view_rotated.png` | Blender Reference Render (Rotated) | PNG (`780×1688`) | ~370 KB | Headless Blender EEVEE verification render of the rotated camera composition. |

---

## 2. Scene Graph & Named Meshes inside `crossroads_environment.glb`

- **Terrain & Floating Island Base**
  - `Island_Terrain_Top` — 56 concentric radial rings × 128 segments of smooth organic terrain with carved stream channel, recessed crossroads pathways, and overhanging mossy turf rim.
  - `Island_Soil_Rim` — Sculpted warm loam/terracotta soil strata band beneath the grass lip.
  - `Island_Rock_Underside` — Multi-tiered, noise-sculpted rocky cliff underside tapering beneath the floating island.
- **Crossroads Pathways & Stream**
  - `Crossroads_Pathway` — Crowned, organically tapered woodland pathway entering from front-center, crossing the wooden bridge, and branching left (`UX Portfolio`) and right (`Game Portfolio`).
  - `Pathway_Cobbles` — Smooth beveled river-stone stepping cobbles and border stones embedded along the pathways.
  - `Stream_Water` — Meandering stream surface mesh running from the northwest spring grotto under the bridge to the southeast cascade rocks.
  - `Wooden_Bridge` — Arched multi-plank oak footbridge with curved under-beams, 9 individual beveled planks, 6 chamfered posts, and double timber handrails.
- **Trees & Botanical Props**
  - `Tree_NW_Hero_*`, `Tree_N_Left_*`, `Tree_N_Center_*`, `Tree_N_Right_*`, `Tree_NE_Hero_*`, `Tree_W_Flank_*`, `Tree_E_Flank_*` — 7 hero framing trees, each separated into `*_Trunk` (root-flared tapered trunk + secondary limbs) and `*_Canopy` (multi-tiered sculpted cloud-foliage crowns).
  - `Environment_Rocks` — Sculpted mossy boulders along stream banks, spring grotto, bridge abutments, and sign bases.
  - `Forest_Ferns` — Multi-frond arched botanical fern rosettes.
  - `Wildflowers` — Warm ivory and champagne wildflower clusters bordering the pathways.
- **Interactive Hero Objects**
  - `Signpost_UX_Post`, `Signpost_UX_Board`, `Signpost_UX_Label3D` — Left crossroads wooden signpost with beveled directional board and extruded 3D lettering (`UX Portfolio`).
  - `Signpost_Game_Post`, `Signpost_Game_Board`, `Signpost_Game_Label3D` — Right crossroads wooden signpost with beveled directional board and extruded 3D lettering (`Game Portfolio`).
  - `Mailbox_Post`, `Mailbox_Body`, `Mailbox_Door`, `Mailbox_Letter`, `Mailbox_Flag` — Front-right crossroads vintage woodland mailbox with articulated brass door, emerging folded cream letter, and raised brass flag.
