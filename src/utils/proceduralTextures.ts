import * as THREE from 'three';

let cachedWoodBump: THREE.CanvasTexture | null = null;
let cachedGrassBump: THREE.CanvasTexture | null = null;
let cachedFoliageBump: THREE.CanvasTexture | null = null;
const cachedSignTextures: Record<string, THREE.CanvasTexture> = {};

/**
 * Generates a tactile wood-grain bump & roughness map for oak posts, bridge planks, and signboards.
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
      const wave = Math.sin(y * 0.09) * 16 + Math.cos(y * 0.24) * 8;
      const val = Math.max(64, Math.min(196, Math.round(128 + wave)));
      ctx.fillStyle = `rgb(${val}, ${val}, ${val})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }

    ctx.strokeStyle = 'rgba(58, 58, 58, 0.38)';
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 56; i++) {
      const y = (i * 15) % canvas.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(
        canvas.width * 0.33,
        y + Math.sin(i) * 9,
        canvas.width * 0.66,
        y - Math.cos(i) * 9,
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
 * Generates an organic mossy ground micro-bump texture for the sculpted terrain and rocks.
 */
export function getGrassBumpTexture(): THREE.CanvasTexture {
  if (cachedGrassBump) return cachedGrassBump;

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, 512, 512);

    for (let i = 0; i < 3200; i++) {
      const x = (i * 97) % 512;
      const y = (i * 179) % 512;
      const r = 2 + (i % 6);
      const shade = 104 + (i % 48);
      ctx.fillStyle = `rgba(${shade}, ${shade}, ${shade}, 0.42)`;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(7, 7);
  cachedGrassBump = texture;
  return texture;
}

/**
 * Generates a layered leaf-cluster micro-relief bump texture for tree canopies and ferns.
 */
export function getFoliageBumpTexture(): THREE.CanvasTexture {
  if (cachedFoliageBump) return cachedFoliageBump;

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#787878';
    ctx.fillRect(0, 0, 512, 512);

    for (let i = 0; i < 2200; i++) {
      const x = (i * 113 + (i % 7) * 19) % 512;
      const y = (i * 157 + (i % 5) * 23) % 512;
      const rx = 5 + (i % 8);
      const ry = 3 + (i % 5);
      const rot = (i * 0.45) % Math.PI;
      const shade = 98 + (i % 62);
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rot);
      ctx.fillStyle = `rgba(${shade}, ${shade}, ${shade}, 0.52)`;
      ctx.beginPath();
      ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(4, 4);
  cachedFoliageBump = texture;
  return texture;
}

/**
 * Generates a high-DPI handcrafted wooden sign plaque texture with warm oak grain,
 * champagne border inlay, and refined editorial wayfinding typography.
 */
export function getSignPlaqueTexture(
  label: string,
  direction: 'left' | 'right',
  sublabel?: string
): THREE.CanvasTexture {
  const cacheKey = `${label}_${direction}_${sublabel || ''}_v2`;
  if (cachedSignTextures[cacheKey]) return cachedSignTextures[cacheKey];

  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 320;
  const ctx = canvas.getContext('2d');

  if (ctx) {
    const bgGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bgGrad.addColorStop(0, '#492C18');
    bgGrad.addColorStop(0.5, '#5D3920');
    bgGrad.addColorStop(1, '#3D2412');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let y = 4; y < canvas.height; y += 6) {
      const alpha = 0.035 + 0.025 * Math.sin(y * 0.19);
      ctx.fillStyle =
        y % 12 === 0
          ? `rgba(255, 225, 185, ${alpha})`
          : `rgba(22, 10, 3, ${alpha * 1.35})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }

    const pad = 22;
    ctx.strokeStyle = 'rgba(220, 201, 157, 0.58)';
    ctx.lineWidth = 3.5;
    ctx.strokeRect(pad, pad, canvas.width - pad * 2, canvas.height - pad * 2);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = 'rgba(18, 9, 3, 0.78)';
    ctx.font = '600 80px "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, sans-serif';
    const displayStr = direction === 'left' ? `←  ${label}` : `${label}  →`;
    ctx.fillText(displayStr, canvas.width * 0.5 + 2, canvas.height * 0.5 + 3);

    ctx.fillStyle = '#F6F1E5';
    ctx.fillText(displayStr, canvas.width * 0.5, canvas.height * 0.5);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  cachedSignTextures[cacheKey] = texture;
  return texture;
}

/**
 * Generates a refined engraved brass nameplate texture for the Woodland Mailbox post.
 */
export function getMailboxPlaqueTexture(): THREE.CanvasTexture {
  const cacheKey = '__mailbox_contact_plaque_v2__';
  if (cachedSignTextures[cacheKey]) return cachedSignTextures[cacheKey];

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 160;
  const ctx = canvas.getContext('2d');

  if (ctx) {
    const bg = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bg.addColorStop(0, '#1B3F33');
    bg.addColorStop(1, '#122A22');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = 'rgba(220, 201, 157, 0.78)';
    ctx.lineWidth = 6;
    ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#F6F1E5';
    ctx.font = '600 52px "Plus Jakarta Sans", -apple-system, sans-serif';
    ctx.fillText('✉  CONTACT', canvas.width * 0.5, canvas.height * 0.52);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  texture.needsUpdate = true;
  cachedSignTextures[cacheKey] = texture;
  return texture;
}
