import React from 'react';
import {
  CameraViewPreset,
  PERSONAL_CONFIG,
  QualityLevel,
} from '../../config/personalConfig';
import { SignId } from '../world/WoodenSigns';

interface IdentityOverlayProps {
  activeQuality: QualityLevel;
  onChangeQuality: (q: QualityLevel) => void;
  activeCameraPreset: CameraViewPreset['id'];
  onChangeCameraPreset: (preset: CameraViewPreset['id']) => void;
  activeHover: string | null;
  onHoverNav: (id: string | null) => void;
  onTriggerSign: (id: SignId) => void;
  onTriggerMailbox: () => void;
  onQuickSaveContact: () => void;
  toastMessage: string | null;
}

export const IdentityOverlay: React.FC<IdentityOverlayProps> = ({
  activeQuality,
  onChangeQuality,
  activeCameraPreset,
  onChangeCameraPreset,
  activeHover,
  onHoverNav,
  onTriggerSign,
  onTriggerMailbox,
  onQuickSaveContact,
  toastMessage,
}) => {
  const { identity, destinations } = PERSONAL_CONFIG;

  const isRotated = activeCameraPreset === 'rotated';

  return (
    <div className="overlay-container" aria-live="polite">
      {/* Top Header: Personal Identity & Utility Controls */}
      <header className="identity-header">
        <div className="identity-card">
          <div className="identity-eyebrow">
            <span className="eyebrow-dot" aria-hidden="true" />
            <span>{identity.projectSubtitle}</span>
          </div>
          <h1 className="identity-name">{identity.displayName}</h1>
          <p className="identity-title">{identity.professionalTitle}</p>
          <p className="identity-tagline">“{identity.tagline}”</p>
        </div>

        {/* Camera Angle & Adaptive Quality Bar */}
        <div className="top-controls" role="toolbar" aria-label="3D Scene Controls">
          <div className="camera-pills">
            <button
              type="button"
              className={`pill-btn ${activeCameraPreset === 'initial' ? 'active' : ''}`}
              onClick={() => onChangeCameraPreset('initial')}
              title="Reset to primary crossroads angle"
            >
              Reset View
            </button>
            <button
              type="button"
              className={`pill-btn ${isRotated ? 'active' : ''}`}
              onClick={() => onChangeCameraPreset(isRotated ? 'initial' : 'rotated')}
              title="Rotate camera to secondary crossroads angle"
            >
              {isRotated ? 'Angle 2 · Rotated' : 'Rotate Angle'}
            </button>
          </div>

          <div className="quality-selector" role="group" aria-label="Graphics Quality">
            {(['high', 'balanced', 'lite'] as QualityLevel[]).map((q) => (
              <button
                key={q}
                type="button"
                className={`quality-btn ${activeQuality === q ? 'active' : ''}`}
                onClick={() => onChangeQuality(q)}
                aria-pressed={activeQuality === q}
              >
                {PERSONAL_CONFIG.qualityPresets[q].label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Subtle Interactive Hint / Toast Feedback */}
      <div className="scene-hint-row">
        {toastMessage ? (
          <div className="status-toast" role="status">
            {toastMessage}
          </div>
        ) : (
          <div className="interaction-hint">
            <span>Drag to orbit</span>
            <span className="hint-sep" aria-hidden="true">·</span>
            <span>Tap a wooden sign or the mailbox to explore</span>
          </div>
        )}
      </div>

      {/* Accessible Secondary Navigation Dock (Fallback & Direct Access) */}
      <nav className="bottom-nav-dock" aria-label="Primary Portfolio and Contact Actions">
        <a
          href={destinations.uxPortfolioUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={`dock-item ${activeHover === 'ux' ? 'highlighted' : ''}`}
          onMouseEnter={() => onHoverNav('ux')}
          onMouseLeave={() => onHoverNav(null)}
          onFocus={() => onHoverNav('ux')}
          onBlur={() => onHoverNav(null)}
          onClick={(e) => {
            e.preventDefault();
            onTriggerSign('ux');
          }}
        >
          <span className="dock-kicker">Left Path</span>
          <span className="dock-label">{destinations.uxPortfolioLabel} ↗</span>
        </a>

        <button
          type="button"
          className={`dock-item ${activeHover === 'game' ? 'highlighted' : ''}`}
          onMouseEnter={() => onHoverNav('game')}
          onMouseLeave={() => onHoverNav(null)}
          onFocus={() => onHoverNav('game')}
          onBlur={() => onHoverNav(null)}
          onClick={() => onTriggerSign('game')}
        >
          <span className="dock-kicker">Right Path</span>
          <span className="dock-label">{destinations.gamePortfolioLabel}</span>
        </button>

        <button
          type="button"
          className={`dock-item dock-item-primary ${activeHover === 'mailbox' ? 'highlighted' : ''}`}
          onMouseEnter={() => onHoverNav('mailbox')}
          onMouseLeave={() => onHoverNav(null)}
          onFocus={() => onHoverNav('mailbox')}
          onBlur={() => onHoverNav(null)}
          onClick={onTriggerMailbox}
        >
          <span className="dock-kicker">Woodland Mailbox</span>
          <span className="dock-label">Contact & QR</span>
        </button>

        <button
          type="button"
          className="dock-item dock-item-vcard"
          onClick={onQuickSaveContact}
          title="Download Evelyn Lin vCard (.vcf)"
        >
          <span className="dock-kicker">Instant vCard</span>
          <span className="dock-label">Save Contact</span>
        </button>
      </nav>
    </div>
  );
};
