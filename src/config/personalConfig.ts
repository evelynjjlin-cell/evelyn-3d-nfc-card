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
  | 'closeupBroadleaf'
  | 'closeupEvergreen'
  | 'closeupDesignSign'
  | 'closeupGameSign'
  | 'closeupTrailStones'
  | 'closeupBridgeApproaches'
  | 'closeupCreekWater'
  | 'closeupPlaque'
  | 'closeupMailboxBase';

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
    uxPortfolioTheme: string;
    uxPortfolioUrl: string;
    gamePortfolioLabel: string;
    gamePortfolioTheme: string;
    /**
     * Leave empty ("") while the Game Portfolio is still in development.
     * When empty, selecting the Game Trail sign opens the "New world in progress." notice.
     * Once set to a valid https:// URL, the sign navigates directly like the Design Trail sign.
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
    uxPortfolioLabel: 'Design Trail',
    uxPortfolioTheme: 'Design Stories',
    uxPortfolioUrl: 'https://evelynjlin.com',
    gamePortfolioLabel: 'Game Trail',
    gamePortfolioTheme: 'Game Worlds',
    gamePortfolioUrl: '',
    gamePortfolioPlaceholderTitle: 'New world in progress.',
    gamePortfolioPlaceholderMessage:
      'Game Worlds — Evelyn’s dedicated Game UX, interactive environments, and game-inspired design portfolio is currently being crafted. In the meantime, explore Design Stories on her Design Trail or save her contact card below.',
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
      particlesCount: 18,
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
      particlesCount: 14,
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
      particlesCount: 6,
      enableWindAnimation: false,
      enableWaterShader: false,
    },
  },
  cameraPresets: {
    initial: {
      id: 'initial',
      label: 'Collectible Front View',
      azimuth: -0.04,
      polar: 1.04,
      distanceMobile: 17.8,
      distanceDesktop: 12.2,
      target: [0, 0.32, 0.22],
    },
    rotated: {
      id: 'rotated',
      label: 'Rotated Angle',
      azimuth: 0.36,
      polar: 1.01,
      distanceMobile: 18.2,
      distanceDesktop: 12.5,
      target: [-0.04, 0.32, 0.20],
    },
    uxSign: {
      id: 'uxSign',
      label: 'Design Trail',
      azimuth: -0.26,
      polar: 1.04,
      distanceMobile: 15.2,
      distanceDesktop: 9.6,
      target: [-1.15, 0.65, -0.35],
    },
    gameSign: {
      id: 'gameSign',
      label: 'Game Trail',
      azimuth: 0.26,
      polar: 1.04,
      distanceMobile: 15.2,
      distanceDesktop: 9.6,
      target: [1.15, 0.65, -0.35],
    },
    mailbox: {
      id: 'mailbox',
      label: 'Woodland Mailbox',
      azimuth: 0.22,
      polar: 1.05,
      distanceMobile: 14.4,
      distanceDesktop: 9.2,
      target: [0.65, 0.55, 0.95],
    },
    closeupBroadleaf: {
      id: 'closeupBroadleaf',
      label: 'Broadleaf Hero Tree Close-up',
      azimuth: -0.22,
      polar: 1.13,
      distanceMobile: 7.8,
      distanceDesktop: 5.9,
      target: [-2.10, 1.55, -1.85],
    },
    closeupEvergreen: {
      id: 'closeupEvergreen',
      label: 'Evergreen Tree Close-up',
      azimuth: 0.22,
      polar: 1.11,
      distanceMobile: 7.6,
      distanceDesktop: 5.7,
      target: [1.95, 1.55, -1.85],
    },
    closeupDesignSign: {
      id: 'closeupDesignSign',
      label: 'Design Trail Sign Close-up',
      azimuth: -0.18,
      polar: 1.08,
      distanceMobile: 6.2,
      distanceDesktop: 4.4,
      target: [-1.52, 1.05, -0.68],
    },
    closeupGameSign: {
      id: 'closeupGameSign',
      label: 'Game Trail Sign Close-up',
      azimuth: 0.18,
      polar: 1.08,
      distanceMobile: 6.2,
      distanceDesktop: 4.4,
      target: [1.52, 1.05, -0.64],
    },
    closeupTrailStones: {
      id: 'closeupTrailStones',
      label: 'Woodland Trail & Stepping Stones Close-up',
      azimuth: -0.06,
      polar: 0.92,
      distanceMobile: 6.8,
      distanceDesktop: 4.9,
      target: [0.0, 0.35, 0.65],
    },
    closeupBridgeApproaches: {
      id: 'closeupBridgeApproaches',
      label: 'Bridge Approaches Close-up',
      azimuth: 0.26,
      polar: 0.98,
      distanceMobile: 6.6,
      distanceDesktop: 4.8,
      target: [0.05, 0.42, 0.14],
    },
    closeupCreekWater: {
      id: 'closeupCreekWater',
      label: 'Creek & Water Material Close-up',
      azimuth: -0.24,
      polar: 0.96,
      distanceMobile: 6.8,
      distanceDesktop: 4.9,
      target: [-0.85, 0.32, 0.12],
    },
    closeupPlaque: {
      id: 'closeupPlaque',
      label: 'Evelyn Lin Identity Plaque Close-up',
      azimuth: 0.02,
      polar: 1.16,
      distanceMobile: 6.4,
      distanceDesktop: 4.6,
      target: [0.0, -0.35, 3.15],
    },
    closeupMailboxBase: {
      id: 'closeupMailboxBase',
      label: 'Mailbox & Lower Support Base Close-up',
      azimuth: -0.20,
      polar: 1.06,
      distanceMobile: 5.4,
      distanceDesktop: 3.8,
      target: [1.24, 0.78, 1.36],
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
