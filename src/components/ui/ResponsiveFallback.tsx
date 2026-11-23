import React from 'react';
import { PERSONAL_CONFIG } from '../../config/personalConfig';
import { downloadVCard } from '../../utils/nfcAndVcard';

interface ResponsiveFallbackProps {
  mode: 'loading' | 'webgl-unavailable';
  onOpenContact: () => void;
  onOpenGamePlaceholder: () => void;
}

export const ResponsiveFallback: React.FC<ResponsiveFallbackProps> = ({
  mode,
  onOpenContact,
  onOpenGamePlaceholder,
}) => {
  const { identity, destinations } = PERSONAL_CONFIG;

  if (mode === 'loading') {
    return (
      <div className="scene-loading-badge" role="status" aria-live="polite">
        <span className="loading-spinner" aria-hidden="true" />
        <span>Entering The Crossroads…</span>
      </div>
    );
  }

  return (
    <section className="webgl-fallback-card" aria-label="Accessible Business Card Fallback">
      <div className="fallback-inner">
        <span className="modal-eyebrow">Interactive 3D Forest · Standard View</span>
        <h2>{identity.displayName}</h2>
        <p className="fallback-role">{identity.professionalTitle}</p>
        <p className="fallback-tagline">“{identity.tagline}”</p>
        <div className="fallback-actions">
          <a
            href={destinations.uxPortfolioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn action-btn-primary"
          >
            {destinations.uxPortfolioLabel} ↗
          </a>
          <button
            type="button"
            className="action-btn action-btn-secondary"
            onClick={onOpenGamePlaceholder}
          >
            {destinations.gamePortfolioLabel}
          </button>
          <button
            type="button"
            className="action-btn action-btn-secondary"
            onClick={onOpenContact}
          >
            Contact & QR Code
          </button>
          <button
            type="button"
            className="action-btn action-btn-outline"
            onClick={() => downloadVCard()}
          >
            Save Contact (.vcf)
          </button>
        </div>
      </div>
    </section>
  );
};
