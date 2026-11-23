export type QualityLevel = 'high' | 'balanced' | 'lite';

export interface QualityPreset {
  id: QualityLevel;
  label: string;
  description: string;
  dpr: [number, number];
  shadows: boolean;
  shadowMapSize: number;
  vegetationMultiplier: number;
  particlesCount: number;
  enableWindAnimation: boolean;
  enableWaterShader: boolean;
}

export type CameraPresetId =
  | 'initial'
  | 'rotated'
  | 'uxSign'
  | 'gameSign'
  | 'mailbox'
  | 'closeupTrees'
  | 'closeupProps';

export interface CameraViewPreset {
  id: CameraPresetId;
  label: string;
  /** Azimuth angle in radians (horizontal orbit angle) */
  azimuth: number;
  /** Polar angle in radians (vertical angle from top) */
  polar: number;
  /** Distance from target on mobile portrait */
  distanceMobile: number;
  /** Distance from target on desktop */
  distanceDesktop: number;
  /** Look-at target in world coordinates */
  target: [number, number, number];
}

export interface PersonalConfig {
  identity: {
    displayName: string;
    professionalTitle: string;
    tagline: string;
    projectSubtitle: string;
  };
  destinations: {
    uxPortfolioLabel: string;
    uxPortfolioUrl: string;
    gamePortfolioLabel: string;
    /**
     * Leave empty ("") while the Game Portfolio is still in development.
     * When empty, selecting the Game Portfolio sign opens the "New world in progress." notice.
     * Once set to a valid https:// URL, the sign navigates directly like the UX Portfolio sign.
     */
    gamePortfolioUrl: string;
    gamePortfolioPlaceholderTitle: string;
    gamePortfolioPlaceholderMessage: string;
  };
  contact: {
    email: string;
    linkedInUrl: string;
    phone: string;
    location: string;
    vCardFileName: string;
    vCardNote: string;
  };
  nfc: {
    publicCardUrl: string;
    fallbackPortfolioUrl: string;
  };
  palette: {
    deepForestGreen: string;
    mutedSage: string;
    mossGreen: string;
    warmIvory: string;
    naturalOak: string;
    softChampagne: string;
  };
  qualityPresets: Record<QualityLevel, QualityPreset>;
  cameraPresets: Record<CameraPresetId, CameraViewPreset>;
}

export const PERSONAL_CONFIG: PersonalConfig = {
  identity: {
    displayName: 'Evelyn Lin',
    professionalTitle: 'UX & Interactive Experience Designer',
    tagline: 'Designing thoughtful interactions and playful digital experiences.',
    projectSubtitle: 'The Crossroads',
  },
  destinations: {
    uxPortfolioLabel: 'UX Portfolio',
    uxPortfolioUrl: 'https://evelynjlin.com',
    gamePortfolioLabel: 'Game Portfolio',
    gamePortfolioUrl: '',
    gamePortfolioPlaceholderTitle: 'New world in progress.',
    gamePortfolioPlaceholderMessage:
      'Evelyn’s dedicated Game UX & Game-Inspired Design portfolio is currently being crafted. In the meantime, explore her UX & Interactive Experience work or save her contact card below.',
  },
  contact: {
    email: '',
    linkedInUrl: '',
    phone: '',
    location: '',
    vCardFileName: 'Evelyn-Lin.vcf',
    vCardNote:
      'Evelyn Lin — UX & Interactive Experience Designer. Designing thoughtful interactions and playful digital experiences.',
  },
  nfc: {
    publicCardUrl: '',
    fallbackPortfolioUrl: 'https://evelynjlin.com',
  },
  palette: {
    deepForestGreen: '#193C32',
    mutedSage: '#819783',
    mossGreen: '#60765A',
    warmIvory: '#F4F0E6',
    naturalOak: '#A57752',
    softChampagne: '#DCC99D',
  },
  qualityPresets: {
    high: {
      id: 'high',
      label: 'High',
      description: 'Full high-poly detail, soft shadows, water shimmer, and ambient forest motion.',
      dpr: [1.5, 2],
      shadows: true,
      shadowMapSize: 2048,
      vegetationMultiplier: 1.0,
      particlesCount: 22,
      enableWindAnimation: true,
      enableWaterShader: true,
    },
    balanced: {
      id: 'balanced',
      label: 'Balanced',
      description: 'Optimized for modern smartphones with crisp silhouettes and selective shadows.',
      dpr: [1.25, 1.75],
      shadows: true,
      shadowMapSize: 1024,
      vegetationMultiplier: 0.8,
      particlesCount: 16,
      enableWindAnimation: true,
      enableWaterShader: true,
    },
    lite: {
      id: 'lite',
      label: 'Lite',
      description: 'Streamlined rendering for battery saving or constrained mobile hardware.',
      dpr: [1, 1.25],
      shadows: false,
      shadowMapSize: 512,
      vegetationMultiplier: 0.45,
      particlesCount: 8,
      enableWindAnimation: false,
      enableWaterShader: false,
    },
  },
  cameraPresets: {
    initial: {
      id: 'initial',
      label: 'Crossroads View',
      azimuth: -0.05,
      polar: 1.03,
      distanceMobile: 18.4,
      distanceDesktop: 12.1,
      target: [0, 0.42, 0.05],
    },
    rotated: {
      id: 'rotated',
      label: 'Rotated Angle',
      azimuth: 0.38,
      polar: 0.99,
      distanceMobile: 18.8,
      distanceDesktop: 12.3,
      target: [-0.06, 0.42, 0.04],
    },
    uxSign: {
      id: 'uxSign',
      label: 'UX Portfolio Path',
      azimuth: -0.26,
      polar: 1.04,
      distanceMobile: 15.6,
      distanceDesktop: 9.8,
      target: [-1.15, 0.65, -0.35],
    },
    gameSign: {
      id: 'gameSign',
      label: 'Game Portfolio Path',
      azimuth: 0.26,
      polar: 1.04,
      distanceMobile: 15.6,
      distanceDesktop: 9.8,
      target: [1.15, 0.65, -0.35],
    },
    mailbox: {
      id: 'mailbox',
      label: 'Woodland Mailbox',
      azimuth: 0.22,
      polar: 1.05,
      distanceMobile: 14.8,
      distanceDesktop: 9.4,
      target: [0.65, 0.55, 0.95],
    },
    closeupTrees: {
      id: 'closeupTrees',
      label: 'Foliage & Trees Close-up',
      azimuth: -0.24,
      polar: 1.08,
      distanceMobile: 9.6,
      distanceDesktop: 7.4,
      target: [-1.45, 1.65, -1.65],
    },
    closeupProps: {
      id: 'closeupProps',
      label: 'Signs & Mailbox Close-up',
      azimuth: 0.22,
      polar: 1.06,
      distanceMobile: 8.8,
      distanceDesktop: 6.4,
      target: [0.68, 0.96, 0.32],
    },
  },
};

export function detectDefaultQuality(): QualityLevel {
  if (typeof window === 'undefined') return 'balanced';
  const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return 'lite';

  const isMobile =
    window.innerWidth < 768 ||
    /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || '');

  const cores = navigator.hardwareConcurrency || 4;
  if (isMobile) {
    return cores <= 4 ? 'lite' : 'balanced';
  }
  return cores >= 6 ? 'high' : 'balanced';
}

export function getResolvedCardUrl(): {
  url: string;
  isProductionUrl: boolean;
  statusNote: string;
} {
  const configured = PERSONAL_CONFIG.nfc.publicCardUrl.trim();
  if (configured && /^https:\/\//i.test(configured)) {
    return {
      url: configured,
      isProductionUrl: true,
      statusNote: 'Configured permanent NFC destination URL',
    };
  }

  if (typeof window !== 'undefined') {
    const origin = window.location.origin;
    const isLocal =
      origin.includes('localhost') ||
      origin.includes('127.0.0.1') ||
      origin.startsWith('http://192.168.');
    if (!isLocal && origin.startsWith('https://')) {
      return {
        url: window.location.href.split('#')[0].split('?')[0],
        isProductionUrl: true,
        statusNote: 'Live deployed HTTPS card URL',
      };
    }
  }

  return {
    url: PERSONAL_CONFIG.nfc.fallbackPortfolioUrl,
    isProductionUrl: false,
    statusNote:
      'Preview mode: QR encodes https://evelynjlin.com until publicCardUrl or HTTPS deployment domain is assigned.',
  };
}
