import React, { useState } from 'react';
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
  const [settingsOpen, setSettingsOpen] = useState(false);

  const isRotated = activeCameraPreset === 'rotated';

  return (
    <div className="overlay-container" aria-live="polite">
      {/* Top Editorial Identity Header & Compact Scene Controls */}
      <header className="identity-header">
        <div className="identity-editorial">
          <h1 className="identity-name">{identity.displayName}</h1>
          <p className="identity-title">{identity.professionalTitle}</p>
          <p className="identity-tagline">“{identity.tagline}”</p>
        </div>

        {/* Discreet Camera Reset & Compact View/Quality Menu */}
        <div className="utility-cluster" role="toolbar" aria-label="Scene and View Controls">
          <button
            type="button"
            className={`utility-pill ${activeCameraPreset !== 'initial' ? 'utility-pill-highlight' : ''}`}
            onClick={() => onChangeCameraPreset('initial')}
            title="Reset camera to initial crossroads view"
          >
            ↺ Reset View
          </button>

          <div className="settings-menu-anchor">
            <button
              type="button"
              className={`utility-pill utility-icon-btn ${settingsOpen ? 'active' : ''}`}
              onClick={() => setSettingsOpen((prev) => !prev)}
              aria-expanded={settingsOpen}
              aria-label="Camera angles and graphics quality"
              title="Camera angles & graphics quality"
            >
              ⚙
            </button>

            {settingsOpen && (
              <div className="settings-popover" role="dialog" aria-label="View and Quality Settings">
                <div className="popover-group">
                  <span className="popover-label">Camera Angle</span>
                  <div className="popover-pills">
                    <button
                      type="button"
                      className={`popover-btn ${activeCameraPreset === 'initial' ? 'active' : ''}`}
                      onClick={() => onChangeCameraPreset('initial')}
                    >
                      Initial
                    </button>
                    <button
                      type="button"
                      className={`popover-btn ${isRotated ? 'active' : ''}`}
                      onClick={() => onChangeCameraPreset('rotated')}
                    >
                      Rotated
                    </button>
                  </div>
                </div>

                <div className="popover-group">
                  <span className="popover-label">Graphics Quality</span>
                  <div className="popover-pills">
                    {(['high', 'balanced', 'lite'] as QualityLevel[]).map((q) => (
                      <button
                        key={q}
                        type="button"
                        className={`popover-btn ${activeQuality === q ? 'active' : ''}`}
                        onClick={() => onChangeQuality(q)}
                      >
                        {PERSONAL_CONFIG.qualityPresets[q].label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Bottom Footer: Toast feedback + Compact Secondary Navigation Pill */}
      <div className="bottom-bar-stack">
        {toastMessage && (
          <div className="status-toast" role="status">
            {toastMessage}
          </div>
        )}

        <nav className="compact-nav-pill" aria-label="Portfolio and Contact Links">
          <a
            href={destinations.uxPortfolioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`nav-link-item ${activeHover === 'ux' ? 'highlighted' : ''}`}
            onMouseEnter={() => onHoverNav('ux')}
            onMouseLeave={() => onHoverNav(null)}
            onFocus={() => onHoverNav('ux')}
            onBlur={() => onHoverNav(null)}
            onClick={(e) => {
              e.preventDefault();
              onTriggerSign('ux');
            }}
          >
            {destinations.uxPortfolioLabel} <span className="arrow-glyph" aria-hidden="true">↗</span>
          </a>

          <span className="nav-divider" aria-hidden="true">·</span>

          <button
            type="button"
            className={`nav-link-item ${activeHover === 'game' ? 'highlighted' : ''}`}
            onMouseEnter={() => onHoverNav('game')}
            onMouseLeave={() => onHoverNav(null)}
            onFocus={() => onHoverNav('game')}
            onBlur={() => onHoverNav(null)}
            onClick={() => onTriggerSign('game')}
          >
            {destinations.gamePortfolioLabel}
          </button>

          <span className="nav-divider" aria-hidden="true">·</span>

          <button
            type="button"
            className={`nav-link-item nav-link-contact ${activeHover === 'mailbox' ? 'highlighted' : ''}`}
            onMouseEnter={() => onHoverNav('mailbox')}
            onMouseLeave={() => onHoverNav(null)}
            onFocus={() => onHoverNav('mailbox')}
            onBlur={() => onHoverNav(null)}
            onClick={onTriggerMailbox}
          >
            Save Contact
          </button>

          <button
            type="button"
            className="nav-vcard-quick"
            onClick={onQuickSaveContact}
            title="Download Evelyn-Lin.vcf directly"
            aria-label="Download vCard file directly"
          >
            ↓ .vcf
          </button>
        </nav>
      </div>
    </div>
  );
};
