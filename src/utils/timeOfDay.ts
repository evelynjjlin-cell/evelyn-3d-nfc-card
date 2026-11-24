export type TimeOfDayPeriod = 'morning' | 'midday' | 'golden_hour' | 'night';

export interface TimeOfDayPreset {
  id: TimeOfDayPeriod;
  label: string;
  timeRangeLabel: string;
  /** Three.js WebGL clear color & distance fog color */
  clearColor: string;
  /** Outer viewport radial CSS gradient behind the 3D collectible */
  viewportGradient: string;
  /** Ambient base light */
  ambientColor: string;
  ambientIntensity: number;
  /** Hemisphere sky-to-ground bounce light */
  hemiSkyColor: string;
  hemiGroundColor: string;
  hemiIntensity: number;
  /** Primary directional sunlight / moonlight */
  sunPosition: [number, number, number];
  sunColor: string;
  sunIntensity: number;
  /** Secondary directional fill light */
  fillPosition: [number, number, number];
  fillColor: string;
  fillIntensity: number;
  /** Rim backlight separating tree crowns from background */
  rimPosition: [number, number, number];
  rimColor: string;
  rimIntensity: number;
  /** Dedicated creek water specular glint light */
  waterGlintColor: string;
  waterGlintIntensity: number;
  /** Water surface emissive & shimmer highlight tint */
  waterEmissiveColor: string;
  waterEmissiveIntensity: number;
  waterRippleHighlightColor: string;
  /** Warm crossroads lantern fill (active during golden hour & evening/night) */
  lanternIntensity: number;
  lanternColor: string;
  /** Floating forest dust / firefly motes */
  sporeColor: string;
  sporeOpacity: number;
}

export const TORONTO_TIMEZONE = 'America/Toronto';

export const TIME_OF_DAY_PRESETS: Record<TimeOfDayPeriod, TimeOfDayPreset> = {
  morning: {
    id: 'morning',
    label: 'Morning Mist',
    timeRangeLabel: '06:00 – 10:59 ET',
    clearColor: '#1B3A33',
    viewportGradient:
      'radial-gradient(circle at 54% 36%, #295247 0%, #1B3A33 56%, #102420 100%)',
    ambientColor: '#E2F3EC',
    ambientIntensity: 0.72,
    hemiSkyColor: '#DCF2EA',
    hemiGroundColor: '#234235',
    hemiIntensity: 1.08,
    sunPosition: [8.2, 8.8, 5.4],
    sunColor: '#FFF3DC',
    sunIntensity: 2.18,
    fillPosition: [-6.6, 6.2, 4.4],
    fillColor: '#C2E4D8',
    fillIntensity: 0.86,
    rimPosition: [-2.2, 7.4, -7.8],
    rimColor: '#FFEBC2',
    rimIntensity: 0.76,
    waterGlintColor: '#E6FFF9',
    waterGlintIntensity: 1.45,
    waterEmissiveColor: '#1B6660',
    waterEmissiveIntensity: 0.24,
    waterRippleHighlightColor: '#E0FFF7',
    lanternIntensity: 0.15,
    lanternColor: '#FFE3B3',
    sporeColor: '#E6F7EC',
    sporeOpacity: 0.50,
  },
  midday: {
    id: 'midday',
    label: 'Midday Daylight',
    timeRangeLabel: '11:00 – 15:29 ET',
    clearColor: '#16332B',
    viewportGradient:
      'radial-gradient(circle at 50% 38%, #22483D 0%, #16332B 58%, #0D211B 100%)',
    ambientColor: '#EAF4EC',
    ambientIntensity: 0.75,
    hemiSkyColor: '#F3FAF0',
    hemiGroundColor: '#254536',
    hemiIntensity: 1.12,
    sunPosition: [4.8, 12.4, 6.2],
    sunColor: '#FFF9EC',
    sunIntensity: 2.40,
    fillPosition: [-6.8, 7.0, 4.2],
    fillColor: '#C6E2D2',
    fillIntensity: 0.84,
    rimPosition: [-1.0, 8.6, -8.0],
    rimColor: '#FFF0C8',
    rimIntensity: 0.78,
    waterGlintColor: '#ECFFFB',
    waterGlintIntensity: 1.65,
    waterEmissiveColor: '#1E6E68',
    waterEmissiveIntensity: 0.26,
    waterRippleHighlightColor: '#E8FFFA',
    lanternIntensity: 0.0,
    lanternColor: '#FFE3B3',
    sporeColor: '#F6EAC2',
    sporeOpacity: 0.46,
  },
  golden_hour: {
    id: 'golden_hour',
    label: 'Golden Hour',
    timeRangeLabel: '15:30 – 19:29 ET',
    clearColor: '#1E2E24',
    viewportGradient:
      'radial-gradient(circle at 44% 34%, #354431 0%, #1E2E24 56%, #121C16 100%)',
    ambientColor: '#F2E3CE',
    ambientIntensity: 0.68,
    hemiSkyColor: '#FFE1B5',
    hemiGroundColor: '#2B3D2E',
    hemiIntensity: 1.06,
    sunPosition: [-7.8, 6.6, 5.8],
    sunColor: '#FFCE8E',
    sunIntensity: 2.42,
    fillPosition: [6.4, 5.8, 4.4],
    fillColor: '#BFD6C6',
    fillIntensity: 0.78,
    rimPosition: [2.4, 6.8, -7.6],
    rimColor: '#FFB668',
    rimIntensity: 0.98,
    waterGlintColor: '#FFE4B2',
    waterGlintIntensity: 1.75,
    waterEmissiveColor: '#1D5E58',
    waterEmissiveIntensity: 0.25,
    waterRippleHighlightColor: '#FFEAC2',
    lanternIntensity: 0.48,
    lanternColor: '#FFD296',
    sporeColor: '#FFD694',
    sporeOpacity: 0.60,
  },
  night: {
    id: 'night',
    label: 'Evening Twilight',
    timeRangeLabel: '19:30 – 05:59 ET',
    clearColor: '#102229',
    viewportGradient:
      'radial-gradient(circle at 50% 36%, #1B3642 0%, #102229 58%, #091419 100%)',
    ambientColor: '#C8DCF0',
    ambientIntensity: 0.80,
    hemiSkyColor: '#B8D6F5',
    hemiGroundColor: '#1D3338',
    hemiIntensity: 1.05,
    sunPosition: [-5.4, 9.8, 5.6],
    sunColor: '#CAE2FF',
    sunIntensity: 1.75,
    fillPosition: [6.2, 6.5, 4.8],
    fillColor: '#9EC6E0',
    fillIntensity: 0.85,
    rimPosition: [0.0, 7.6, -8.0],
    rimColor: '#A8CEFF',
    rimIntensity: 0.92,
    waterGlintColor: '#CCF4FF',
    waterGlintIntensity: 1.60,
    waterEmissiveColor: '#1B6868',
    waterEmissiveIntensity: 0.30,
    waterRippleHighlightColor: '#D4F8FF',
    lanternIntensity: 1.15,
    lanternColor: '#FFD89E',
    sporeColor: '#DCF8C6',
    sporeOpacity: 0.66,
  },
};

/**
 * Computes the current local hour and minute in `America/Toronto` and returns
 * the matching `TimeOfDayPeriod` along with a formatted Toronto clock string.
 */
export function getTorontoTimeState(date: Date = new Date()): {
  period: TimeOfDayPeriod;
  formattedTime: string;
  decimalHour: number;
} {
  try {
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: TORONTO_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
    const parts = formatter.formatToParts(date);
    const hourStr = parts.find((p) => p.type === 'hour')?.value ?? '12';
    const minStr = parts.find((p) => p.type === 'minute')?.value ?? '00';
    const hour = Number(hourStr) % 24;
    const minute = Number(minStr);
    const decimalHour = hour + minute / 60;

    let period: TimeOfDayPeriod;
    if (decimalHour >= 6.0 && decimalHour < 11.0) {
      period = 'morning';
    } else if (decimalHour >= 11.0 && decimalHour < 15.5) {
      period = 'midday';
    } else if (decimalHour >= 15.5 && decimalHour < 19.5) {
      period = 'golden_hour';
    } else {
      period = 'night';
    }

    return {
      period,
      formattedTime: `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')} ET`,
      decimalHour,
    };
  } catch {
    return {
      period: 'midday',
      formattedTime: '12:00 ET',
      decimalHour: 12,
    };
  }
}

/**
 * Checks for an optional URL query override (`?time=morning|midday|golden_hour|night`)
 * before falling back to live `America/Toronto` local time.
 */
export function getInitialTimeOfDayPeriod(): {
  period: TimeOfDayPeriod;
  isOverridden: boolean;
  formattedTime: string;
} {
  const live = getTorontoTimeState();
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get('time')?.toLowerCase().trim();
    if (raw === 'morning' || raw === 'midday' || raw === 'golden_hour' || raw === 'night') {
      return {
        period: raw,
        isOverridden: true,
        formattedTime: live.formattedTime,
      };
    }
    if (raw === 'golden' || raw === 'afternoon' || raw === 'late_afternoon') {
      return {
        period: 'golden_hour',
        isOverridden: true,
        formattedTime: live.formattedTime,
      };
    }
    if (raw === 'evening') {
      return {
        period: 'night',
        isOverridden: true,
        formattedTime: live.formattedTime,
      };
    }
  }
  return {
    period: live.period,
    isOverridden: false,
    formattedTime: live.formattedTime,
  };
}
