import * as THREE from 'three';

let cachedWoodBump: THREE.CanvasTexture | null = null;
let cachedGrassBump: THREE.CanvasTexture | null = null;
const cachedSignTextures: Record<string, THREE.CanvasTexture> = {};

/**
 * Generates a subtle procedural wood-grain bump & roughness map for oak posts, bridge planks, and signboards.
 */
export function getWoodGrainTexture(): THREE.CanvasTexture {
  if (cachedWoodBump) return cachedWoodBump;

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < canvas.height; y += 2) {
      const wave = Math.sin(y * 0.09) * 14 + Math.cos(y * 0.23) * 7;
      const val = Math.max(70, Math.min(190, Math.round(128 + wave)));
      ctx.fillStyle = `rgb(${val}, ${val}, ${val})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }

    // Subtle wood plank knots and fibers
    ctx.strokeStyle = 'rgba(65, 65, 65, 0.35)';
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 48; i++) {
      const y = (i * 17) % canvas.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(
        canvas.width * 0.33,
        y + Math.sin(i) * 8,
        canvas.width * 0.66,
        y - Math.cos(i) * 8,
        canvas.width,
        y
      );
      ctx.stroke();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2, 2);
  cachedWoodBump = texture;
  return texture;
}

/**
 * Generates an organic mossy ground micro-bump texture for the sculpted terrain.
 */
export function getGrassBumpTexture(): THREE.CanvasTexture {
  if (cachedGrassBump) return cachedGrassBump;

  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, 256, 256);

    for (let i = 0; i < 1400; i++) {
      const x = (i * 73) % 256;
      const y = (i * 137) % 256;
      const r = 2 + (i % 5);
      const shade = 112 + (i % 36);
      ctx.fillStyle = `rgba(${shade}, ${shade}, ${shade}, 0.45)`;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(6, 6);
  cachedGrassBump = texture;
  return texture;
}

/**
 * Generates a high-DPI handcrafted wooden sign plaque texture with warm oak grain,
 * champagne border inlay, directional indicator, and razor-sharp warm ivory typography.
 */
export function getSignPlaqueTexture(
  label: string,
  direction: 'left' | 'right',
  sublabel?: string
): THREE.CanvasTexture {
  const cacheKey = `${label}_${direction}_${sublabel || ''}`;
  if (cachedSignTextures[cacheKey]) return cachedSignTextures[cacheKey];

  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 320;
  const ctx = canvas.getContext('2d');

  if (ctx) {
    // Rich dark roasted oak background with warm center vignette
    const bgGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bgGrad.addColorStop(0, '#4E301B');
    bgGrad.addColorStop(0.5, '#633E24');
    bgGrad.addColorStop(1, '#422815');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle horizontal wood grain streaks
    for (let y = 6; y < canvas.height; y += 8) {
      const alpha = 0.04 + 0.03 * Math.sin(y * 0.17);
      ctx.fillStyle = y % 16 === 0 ? `rgba(255, 225, 185, ${alpha})` : `rgba(25, 12, 4, ${alpha * 1.4})`;
      ctx.fillRect(0, y, canvas.width, 3);
    }

    // Subtle plank seam line in the middle
    ctx.strokeStyle = 'rgba(24, 12, 5, 0.45)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(28, canvas.height * 0.5);
    ctx.lineTo(canvas.width - 28, canvas.height * 0.5);
    ctx.stroke();

    // Inset champagne-gold & warm ivory carved frame border
    const pad = 20;
    ctx.strokeStyle = 'rgba(220, 201, 157, 0.72)';
    ctx.lineWidth = 5;
    ctx.strokeRect(pad, pad, canvas.width - pad * 2, canvas.height - pad * 2);

    // Corner brass studs
    const studOffsets = [
      [pad + 18, pad + 18],
      [canvas.width - pad - 18, pad + 18],
      [pad + 18, canvas.height - pad - 18],
      [canvas.width - pad - 18, canvas.height - pad - 18],
    ];
    for (const [sx, sy] of studOffsets) {
      ctx.fillStyle = '#DCC99D';
      ctx.beginPath();
      ctx.arc(sx, sy, 7, 0, Math.PI * 2);
      ctx.fill();
    }

    // Directional arrow + Exact Sign Label ("UX Portfolio" or "Game Portfolio")
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Soft carved drop shadow behind text
    ctx.fillStyle = 'rgba(18, 9, 3, 0.85)';
    ctx.font = '700 94px "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, sans-serif';
    const displayStr = direction === 'left' ? `←  ${label}` : `${label}  →`;
    ctx.fillText(displayStr, canvas.width * 0.5 + 3, canvas.height * (sublabel ? 0.44 : 0.5) + 4);

    // Main Warm Ivory text
    ctx.fillStyle = '#FAF6EC';
    ctx.fillText(displayStr, canvas.width * 0.5, canvas.height * (sublabel ? 0.44 : 0.5));

    if (sublabel) {
      ctx.font = '600 34px "Plus Jakarta Sans", -apple-system, sans-serif';
      ctx.fillStyle = '#DCC99D';
      ctx.fillText(sublabel.toUpperCase(), canvas.width * 0.5, canvas.height * 0.77);
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  cachedSignTextures[cacheKey] = texture;
  return texture;
}

/**
 * Generates a high-contrast brass & deep forest badge texture for the Woodland Mailbox.
 */
export function getMailboxPlaqueTexture(): THREE.CanvasTexture {
  const cacheKey = '__mailbox_contact_plaque__';
  if (cachedSignTextures[cacheKey]) return cachedSignTextures[cacheKey];

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 192;
  const ctx = canvas.getContext('2d');

  if (ctx) {
    const bg = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bg.addColorStop(0, '#1B4034');
    bg.addColorStop(1, '#122B23');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#DCC99D';
    ctx.lineWidth = 8;
    ctx.strokeRect(12, 12, canvas.width - 24, canvas.height - 24);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#FAF6EC';
    ctx.font = '700 58px "Plus Jakarta Sans", -apple-system, sans-serif';
    ctx.fillText('✉  CONTACT', canvas.width * 0.5, canvas.height * 0.44);

    ctx.fillStyle = '#DCC99D';
    ctx.font = '600 28px "Plus Jakarta Sans", -apple-system, sans-serif';
    ctx.fillText('SAVE VCARD & SHARE', canvas.width * 0.5, canvas.height * 0.76);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  cachedSignTextures[cacheKey] = texture;
  return texture;
}
