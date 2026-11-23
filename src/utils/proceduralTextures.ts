import * as THREE from 'three';

let cachedWoodBump: THREE.CanvasTexture | null = null;
let cachedWoodAlbedo: THREE.CanvasTexture | null = null;
let cachedWoodRoughness: THREE.CanvasTexture | null = null;
let cachedGrassBump: THREE.CanvasTexture | null = null;
let cachedFoliageBump: THREE.CanvasTexture | null = null;
const cachedSignTextures: Record<string, THREE.CanvasTexture> = {};

/**
 * Generates a high-resolution (1024x512) wood-grain bump map with long cathedral fibers,
 * growth rings, and subtle carved plank striations.
 */
export function getWoodGrainTexture(): THREE.CanvasTexture {
  if (cachedWoodBump) return cachedWoodBump;

  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < canvas.height; y += 2) {
      const wave =
        Math.sin(y * 0.075) * 20 +
        Math.cos(y * 0.19) * 11 +
        Math.sin(y * 0.48) * 6;
      const val = Math.max(48, Math.min(212, Math.round(128 + wave)));
      ctx.fillStyle = `rgb(${val}, ${val}, ${val})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }

    // Long wavy cathedral wood grain fibers along U (X axis)
    for (let i = 0; i < 110; i++) {
      const y = (i * 9.3) % canvas.height;
      const isDark = i % 2 === 0;
      ctx.strokeStyle = isDark ? 'rgba(42, 42, 42, 0.44)' : 'rgba(215, 215, 215, 0.34)';
      ctx.lineWidth = 1.2 + (i % 3) * 0.6;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(
        canvas.width * 0.28,
        y + Math.sin(i * 0.7) * 14,
        canvas.width * 0.68,
        y - Math.cos(i * 0.9) * 14,
        canvas.width,
        y
      );
      ctx.stroke();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1, 1);
  texture.anisotropy = 8;
  cachedWoodBump = texture;
  return texture;
}

/**
 * Generates a warm, handcrafted wood-grain albedo modulation texture (1024x512)
 * that multiplies with vertex colors (`COLOR_0`) to produce visible wood grain streaks,
 * subtle growth rings, and warm planed-timber variation.
 */
export function getWoodGrainAlbedoTexture(): THREE.CanvasTexture {
  if (cachedWoodAlbedo) return cachedWoodAlbedo;

  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#E8DDD0';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle warm plank banding
    for (let y = 0; y < canvas.height; y += 2) {
      const wave =
        Math.sin(y * 0.06) * 16 +
        Math.cos(y * 0.17) * 10 +
        Math.sin(y * 0.41) * 5;
      const r = Math.max(175, Math.min(252, Math.round(226 + wave)));
      const g = Math.max(160, Math.min(242, Math.round(212 + wave * 0.92)));
      const b = Math.max(142, Math.min(228, Math.round(196 + wave * 0.82)));
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }

    // Cathedral grain curves & fine dark/warm fiber streaks
    for (let i = 0; i < 140; i++) {
      const y = (i * 7.4) % canvas.height;
      const isDark = i % 3 !== 0;
      ctx.strokeStyle = isDark
        ? 'rgba(115, 82, 54, 0.28)'
        : 'rgba(255, 244, 228, 0.26)';
      ctx.lineWidth = 1.1 + (i % 3) * 0.55;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(
        canvas.width * 0.32,
        y + Math.sin(i * 0.8) * 16,
        canvas.width * 0.68,
        y - Math.cos(i * 0.85) * 16,
        canvas.width,
        y
      );
      ctx.stroke();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1, 1);
  texture.anisotropy = 8;
  cachedWoodAlbedo = texture;
  return texture;
}

/**
 * Generates a subtle matte roughness variation texture (512x256) so wood grain pores
 * and ridges exhibit realistic, non-plastic matte roughness variation.
 */
export function getWoodRoughnessTexture(): THREE.CanvasTexture {
  if (cachedWoodRoughness) return cachedWoodRoughness;

  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#D8D8D8';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let y = 0; y < canvas.height; y += 2) {
      const wave = Math.sin(y * 0.11) * 18 + Math.cos(y * 0.29) * 10;
      const val = Math.max(185, Math.min(248, Math.round(218 + wave)));
      ctx.fillStyle = `rgb(${val}, ${val}, ${val})`;
      ctx.fillRect(0, y, canvas.width, 2);
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1, 1);
  cachedWoodRoughness = texture;
  return texture;
}

/**
 * Generates an organic mossy ground micro-bump texture for the sculpted terrain.
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
 * Generates a layered leaf-cluster micro-relief bump texture for foliage.
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
 * Generates a refined engraved brass nameplate texture for the Woodland Mailbox post.
 */
export function getMailboxPlaqueTexture(): THREE.CanvasTexture {
  const cacheKey = '__mailbox_contact_plaque_v3__';
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
