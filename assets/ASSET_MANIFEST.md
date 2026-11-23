# 3D Asset Package & Provenance Manifest (V6 External CC0 Asset Overhaul & Wood Rendering Fix)
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin — *UX & Interactive Experience Designer*  
**Authoring & Integration Tool:** Blender 5.0.0 (`/Applications/Blender.app/Contents/MacOS/Blender`)  
**License:** Custom-Authored Hero Props & Terrain + Official Quaternius Stylized Nature MegaKit (`CC0 1.0 Universal` Public Domain)

---

## 1. External Web-Sourced 3D Assets & Provenance

All external forest, botanical, and stone assets were sourced from **Quaternius — Stylized Nature MegaKit (Standard 1.0)**, officially published by **Quaternius** (`https://quaternius.com/packs/stylizednaturemegakit.html` / official Godot Asset Store distribution `https://store.godotengine.org/asset/quaternius/stylized-nature-megakit/`) under the **Creative Commons Zero (`CC0 1.0 Universal`)** license (`https://creativecommons.org/publicdomain/zero/1.0/`).

Curated source files are stored in [`assets/external/quaternius_stylized_nature/`](./external/quaternius_stylized_nature/):

| Category | External Assets Used (`.gltf` / `.bin`) | Embedded Textures (`.png`) | Modifications & Optimizations Applied |
| :--- | :--- | :--- | :--- |
| **Broadleaf Trees** | `TwistedTree_1.gltf`, `TwistedTree_2.gltf`, `CommonTree_1.gltf`, `CommonTree_2.gltf`, `CommonTree_3.gltf` | `Bark_TwistedTree.png`, `Bark_TwistedTree_Normal.png`, `Bark_NormalTree.png`, `Bark_NormalTree_Normal.png`, `Leaves_NormalTree_C.png`, `Leaves_TwistedTree_C.png` | Split into single-material `${id}_Trunk` and `${id}_Canopy` meshes; harmonized `Leaves_TwistedTree_C.png` and `Leaves_NormalTree_C.png` to unified sRGB woodland emerald-moss radial gradients with matching alpha-border bleed; softened trunk root AO (`[0.62..1.0]`); baked 3D canopy sunlight/AO vertex color gradients (`Color`); downsampled 2K bark diffuse/normal maps to `512×512`. |
| **Evergreen Trees** | `Pine_1.gltf`, `Pine_2.gltf`, `Pine_3.gltf`, `Pine_4.gltf` | `Bark_NormalTree.png`, `Bark_NormalTree_Normal.png`, `Leaf_Pine_C.png` | Split into `${id}_Trunk` and `${id}_Canopy`; enriched `Leaf_Pine_C.png` (`1024×1024`) with stem-to-tip pine needle value gradients; softened trunk root AO; configured depth-writing `alphaTest: 0.28` cutout shading for crisp leaf-shaped shadow casting. |
| **Woodland Shrubs** | `Bush_Common.gltf`, `Bush_Common_Flowers.gltf` | `Leaves_TwistedTree_C.png`, `Leaves_NormalTree_C.png`, `Flowers.png` | Unified into `Forest_Shrubs` (foliage) and `Wildflowers` (blossoms) with 3D dome-lit vertex color gradients and `alphaTest: 0.28` depth-writing cutout materials. |
| **Ferns & Ground Cover** | `Fern_1.gltf`, `Plant_1.gltf`, `Plant_1_Big.gltf`, `Plant_7.gltf`, `Plant_7_Big.gltf`, `Clover_1.gltf`, `Clover_2.gltf` | `Leaves.png` (`1024×1024`) | Clustered naturally along creek banks, boulder bases, and signposts; merged into a single single-material mesh `Forest_Ferns` (`Primitives created: 1`). |
| **Grass & Wildflowers** | `Grass_Common_Short.gltf`, `Grass_Common_Tall.gltf`, `Grass_Wispy_Short.gltf`, `Flower_3_Group.gltf`, `Flower_4_Group.gltf` | `Grass.png`, `Flowers.png` (`512×512`) | Merged by canonical material into `Forest_Grass` and `Wildflowers` (`Primitives created: 1`). |
| **Mossy Boulders & Trail Stones** | `Rock_Medium_1.gltf`, `Rock_Medium_2.gltf`, `Rock_Medium_3.gltf`, `Pebble_Round_1..4.gltf` | `Rocks_Diffuse.png` (`512×512`), `PathRocks_Diffuse.png` (`512×512`) | Placed around the NW spring grotto, SE cascade grotto, central fork divider, foreground knoll (`Environment_Rocks`), and embedded into the compacted woodland trails (`Pathway_Cobbles`). |

---

## 2. Custom-Authored Collectible & Interactive Architecture

| Mesh Object(s) | Description | Root-Cause Structural & Material Engineering |
| :--- | :--- | :--- |
| `Signpost_UX_Post`, `Signpost_UX_Board`, `Signpost_UX_Label3D` | Left crossroads signpost labeled **`Design Trail`** (*Design Stories* → `https://evelynjlin.com`) | Built with positive-determinant right-handed local bevels (`add_oriented_box`, `det = +1`), non-overlapping post joinery, grain-aligned UV maps (`UVMap`), verified outward face normals, and `1024×512` cathedral oak grain diffuse + bump + roughness textures (`transparent: false, depthWrite: true, side: THREE.FrontSide`). |
| `Signpost_Game_Post`, `Signpost_Game_Board`, `Signpost_Game_Label3D` | Right crossroads signpost labeled **`Game Trail`** (*Game Worlds*) | Identical solid, opaque right-handed construction (`det = +1`) pointing right toward *Game Worlds*. |
| `Mailbox_Post`, `Mailbox_Body`, `Mailbox_Door`, `Mailbox_Letter`, `Mailbox_Flag` | Woodland Contact Mailbox on dry front-right terrace (`[1.28, y, 1.36]`) | Rebuilt lower timber plinth, collar, vertical oak shaft, front/rear mortise corbel knee braces, upper oak deck, and side cradle rails with right-handed bevels (`det = +1`) and grain-aligned UVs; enclosed `Mailbox_Body` with verified outward normals. |
| `Wooden_Bridge`, `Stream_Bed`, `Stream_Water` | Arched 13-plank oak bridge spanning the widened pebble-bed woodland creek | All 13 planks, stringers, bank sills, posts, finials, and double handrails built with right-handed oriented bevels (`det = +1`) and grain-aligned UVs; non-glare water surface (`roughness: 0.56`). |
| `Island_Terrain_Top`, `Island_Rock_Underside`, `Island_Soil_Rim` | Unified `112×224` floating island with stitched cliff underside & vertex-splatted trails | Mathematically stitched outer perimeter ring (`outer_rim_coords`) with zero rim gaps. |
| `Identity_Plaque_Frame`, `Identity_Plaque_Plate`, `Identity_Plaque_Name3D`, `Identity_Plaque_Title3D` | Embedded 3D front cliff plaque (`Evelyn Lin — UX & Interactive Experience Designer`) | Built with right-handed chamfered brass frame, corner rivets, oxidized slate tablet, and raised 3D relief typography. |
