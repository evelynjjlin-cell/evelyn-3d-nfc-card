# The Crossroads — High-Fidelity 3D Interactive NFC Business Card (V5)

**Owner:** Evelyn Lin — *UX & Interactive Experience Designer*  
**Tagline:** *"Designing thoughtful interactions and playful digital experiences."*

An independent, mobile-first 3D interactive business card featuring a custom Blender-authored floating forest collectible island where a woodland trail crosses a central stream and arched oak bridge before branching toward Evelyn's **Design Trail** (`https://evelynjlin.com`), her **Game Trail** (*Game Worlds*), and an interactive **Woodland Contact Mailbox**, with an embedded 3D stone-and-brass **Evelyn Lin** identity plaque sculpted directly into the front cliff edge.

---

## 1. Quick Start

```bash
# Install dependencies
npm install

# Start local development server
npm run dev

# Build production bundle
npm run build

# Preview production build
npm run preview
```

### Regenerating 3D Assets from Blender 5.0 (Optional)
All runtime 3D assets (`public/models/crossroads_environment.glb`) and editable Blender sources (`assets/source/crossroads_master.blend`) are already built and committed. To re-run the headless Blender 5.0 authoring pipeline:

```bash
npm run build:assets
```

---

## 2. Central Configuration (`src/config/personalConfig.ts`)

All personal identity strings, portfolio links, contact details, NFC URLs, and camera presets live in a single file: [`src/config/personalConfig.ts`](./src/config/personalConfig.ts).

### Final Locked Signpost Naming
- **Left Sign (`Design Trail`):** Conceptual theme *Design Stories* — opens `https://evelynjlin.com`.
- **Right Sign (`Game Trail`):** Conceptual theme *Game Worlds* — opens the *"New world in progress."* modal until `destinations.gamePortfolioUrl` is configured.

### Connecting the Future Game Portfolio URL
When Evelyn's Game Portfolio website is ready to launch, open `src/config/personalConfig.ts` and set `gamePortfolioUrl`:

```ts
destinations: {
  uxPortfolioLabel: 'Design Trail',
  uxPortfolioSubtitle: 'Design Stories',
  uxPortfolioUrl: 'https://evelynjlin.com',
  gamePortfolioLabel: 'Game Trail',
  gamePortfolioSubtitle: 'Game Worlds',
  gamePortfolioUrl: 'https://your-future-game-portfolio-url.com', // <-- Add URL here
  ...
}
```
Once a valid URL is provided, tapping the **Game Trail** wooden signpost in the 3D forest automatically navigates to that URL instead of opening the *"New world in progress."* modal.

### Adding Optional Email, LinkedIn, or Permanent NFC Card URL
In `src/config/personalConfig.ts`:
- Set `contact.email` or `contact.linkedInUrl` to display them in the unfolded Contact Letter and include them automatically in the downloadable `.vcf` vCard (`Evelyn-Lin.vcf`).
- Set `nfc.publicCardUrl` to your permanent deployed HTTPS URL for QR code generation.

---

## 3. Project Structure

- `blender/build_crossroads_scene.py` — Blender 5.0 Python BMesh/procedural sculpting pipeline (`370,572` triangles, `201,946` vertices across `39` objects)
- `assets/source/crossroads_master.blend` — Editable master Blender 5.0 file (`7.5 MB`)
- `assets/ASSET_MANIFEST.md` — 3D asset inventory, scene hierarchy, and provenance notes
- `public/models/crossroads_environment.glb` — Optimized runtime glTF 2.0 binary scene (`8.3 MB` raw, `~2.05 MB` gzip)
- `src/config/personalConfig.ts` — Single source of truth for identity, links, vCard, and camera presets
- `src/components/world/` — Modular React Three Fiber 3D scene components (`ForestEnvironment`, `Terrain`, `TreesAndVegetation`, `Stream`, `Bridge`, `WoodenSigns`, `Mailbox`, `IdentityPlaque3D`, `CameraController`, `Lighting`)
- `src/components/ui/` — Discreet accessible secondary menu (`IdentityOverlay`), unfolded parchment Contact Letter (`ContactPanel`), Game Trail modal (`GamePortfolioModal`), and accessible fallback (`ResponsiveFallback`)
- `src/utils/` — vCard 3.0 generator, Web Share / Clipboard utilities, QR generator, and procedural PBR bump/plaque textures
- `screenshots/` — 15 automated WebGL visual verification captures covering full views, 8 macro art close-ups, and 3 functional states
- `docs/NFC_SETUP_AND_CARD_DESIGN.md` — Physical NTAG213 NFC encoding instructions and print card concept
