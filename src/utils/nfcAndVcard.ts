import QRCode from 'qrcode';
import { PERSONAL_CONFIG, getResolvedCardUrl } from '../config/personalConfig';

/**
 * Generates a standards-compliant vCard 3.0 payload using only verified fields
 * from PERSONAL_CONFIG. Unconfigured fields (such as empty email or phone) are omitted.
 */
export function buildVCardPayload(): string {
  const { identity, destinations, contact } = PERSONAL_CONFIG;
  const resolvedCard = getResolvedCardUrl();

  const escapeVCard = (value: string): string =>
    value
      .replace(/\\/g, '\\\\')
      .replace(/\n/g, '\\n')
      .replace(/;/g, '\\;')
      .replace(/,/g, '\\,');

  const lines: string[] = [
    'BEGIN:VCARD',
    'VERSION:3.0',
    'N:Lin;Evelyn;;;',
    `FN:${escapeVCard(identity.displayName)}`,
    `TITLE:${escapeVCard(identity.professionalTitle)}`,
    `URL;TYPE=WORK:${destinations.uxPortfolioUrl}`,
  ];

  if (resolvedCard.isProductionUrl && resolvedCard.url !== destinations.uxPortfolioUrl) {
    lines.push(`URL;TYPE=DIGITAL-CARD:${resolvedCard.url}`);
  }

  if (destinations.gamePortfolioUrl.trim()) {
    lines.push(`URL;TYPE=GAME-PORTFOLIO:${destinations.gamePortfolioUrl.trim()}`);
  }

  if (contact.email.trim()) {
    lines.push(`EMAIL;TYPE=INTERNET,WORK:${contact.email.trim()}`);
  }

  if (contact.phone.trim()) {
    lines.push(`TEL;TYPE=CELL:${contact.phone.trim()}`);
  }

  if (contact.linkedInUrl.trim()) {
    lines.push(`X-SOCIALPROFILE;TYPE=linkedin:${contact.linkedInUrl.trim()}`);
  }

  if (contact.location.trim()) {
    lines.push(`ADR;TYPE=WORK:;;${escapeVCard(contact.location.trim())};;;;`);
  }

  lines.push(`NOTE:${escapeVCard(contact.vCardNote)}`);
  lines.push('END:VCARD');

  return lines.join('\r\n') + '\r\n';
}

export function downloadVCard(): { success: boolean; message: string } {
  try {
    const vcardContent = buildVCardPayload();
    const blob = new Blob([vcardContent], { type: 'text/vcard;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = PERSONAL_CONFIG.contact.vCardFileName || 'Evelyn-Lin.vcf';
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);

    setTimeout(() => URL.revokeObjectURL(url), 4000);
    return {
      success: true,
      message: 'Downloaded Evelyn-Lin.vcf — open the file to save to your contacts.',
    };
  } catch (err) {
    return {
      success: false,
      message:
        err instanceof Error
          ? `Unable to download vCard: ${err.message}`
          : 'Unable to initiate vCard download.',
    };
  }
}

export async function shareDigitalCard(): Promise<{
  mode: 'web-share' | 'clipboard' | 'error';
  message: string;
}> {
  const { identity, destinations } = PERSONAL_CONFIG;
  const resolved = getResolvedCardUrl();
  const shareUrl = resolved.isProductionUrl
    ? resolved.url
    : typeof window !== 'undefined' && window.location.href.startsWith('https://')
      ? window.location.href
      : destinations.uxPortfolioUrl;

  const shareData: ShareData = {
    title: `${identity.displayName} — ${identity.professionalTitle}`,
    text: `${identity.displayName} · ${identity.professionalTitle} — "${identity.tagline}"`,
    url: shareUrl,
  };

  if (typeof navigator !== 'undefined' && typeof navigator.share === 'function') {
    try {
      await navigator.share(shareData);
      return {
        mode: 'web-share',
        message: 'Card shared via your device share sheet.',
      };
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return {
          mode: 'web-share',
          message: 'Share cancelled.',
        };
      }
      // Fall through to clipboard copy if Web Share API failed
    }
  }

  return copyCardLink();
}

export async function copyCardLink(): Promise<{
  mode: 'clipboard' | 'error';
  message: string;
}> {
  const resolved = getResolvedCardUrl();
  const targetUrl =
    resolved.isProductionUrl || typeof window === 'undefined'
      ? resolved.url
      : window.location.href;

  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(targetUrl);
      return {
        mode: 'clipboard',
        message: `Link copied to clipboard (${targetUrl}).`,
      };
    }

    // Legacy textarea fallback
    const textarea = document.createElement('textarea');
    textarea.value = targetUrl;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    return {
      mode: 'clipboard',
      message: `Link copied to clipboard (${targetUrl}).`,
    };
  } catch {
    return {
      mode: 'error',
      message: `Please copy the link manually: ${targetUrl}`,
    };
  }
}

export async function generateQrCodeDataUrl(url: string): Promise<string> {
  return QRCode.toDataURL(url, {
    width: 240,
    margin: 2,
    color: {
      dark: '#193C32',
      light: '#F4F0E6',
    },
    errorCorrectionLevel: 'M',
  });
}
