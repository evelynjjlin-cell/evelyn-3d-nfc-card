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
  onHoverNav,
  onTriggerSign,
  onTriggerMailbox,
  onQuickSaveContact,
  toastMessage,
}) => {
  const { identity, destinations } = PERSONAL_CONFIG;
  const [menuOpen, setMenuOpen] = useState(false);

  const isRotated = activeCameraPreset === 'rotated';

  return (
    <div className="overlay-container" aria-live="polite">
      {/* Screen-Reader Accessible Equivalent for the Embedded 3D Identity Plaque & 3D Landmarks */}
      <div className="sr-only">
        <h1>{identity.displayName}</h1>
        <p>{identity.professionalTitle}</p>
        <p>{identity.tagline}</p>
        <nav aria-label="Accessible Portfolio and Contact Actions">
          <a href={destinations.uxPortfolioUrl} target="_blank" rel="noopener noreferrer">
            {destinations.uxPortfolioLabel}
          </a>
          <button type="button" onClick={() => onTriggerSign('game')}>
            {destinations.gamePortfolioLabel}
          </button>
          <button type="button" onClick={onTriggerMailbox}>
            Open Contact Letter
          </button>
          <button type="button" onClick={onQuickSaveContact}>
            Save Contact (.vcf)
          </button>
        </nav>
      </div>

      {/* Ultra-Restrained Corner Collectible Controls (No Website Header or Footer) */}
      <div className="collectible-corner-controls" role="toolbar" aria-label="Collectible Controls">
        {activeCameraPreset !== 'initial' && (
          <button
            type="button"
            className="corner-icon-pill"
            onClick={() => onChangeCameraPreset('initial')}
            title="Reset orientation"
            aria-label="Reset orientation"
          >
            ↺
          </button>
        )}

        <div className="settings-menu-anchor">
          <button
            type="button"
            className={`corner-icon-pill ${menuOpen ? 'active' : ''}`}
            onClick={() => setMenuOpen((prev) => !prev)}
            aria-expanded={menuOpen}
            aria-label="Open accessible menu and view options"
            title="Accessible menu & view options"
          >
            ⋯
          </button>

          {menuOpen && (
            <div className="settings-popover" role="dialog" aria-label="Accessible Navigation and View Options">
              <div className="popover-identity-summary">
                <strong>{identity.displayName}</strong>
                <span>{identity.professionalTitle}</span>
              </div>

              <div className="popover-group">
                <span className="popover-label">Quick Actions</span>
                <div className="popover-action-list">
                  <a
                    href={destinations.uxPortfolioUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="popover-action-link"
                    onMouseEnter={() => onHoverNav('ux')}
                    onMouseLeave={() => onHoverNav(null)}
                    onClick={(e) => {
                      e.preventDefault();
                      setMenuOpen(false);
                      onTriggerSign('ux');
                    }}
                  >
                    <span>{destinations.uxPortfolioLabel}</span>
                    <span aria-hidden="true">↗</span>
                  </a>

                  <button
                    type="button"
                    className="popover-action-link"
                    onMouseEnter={() => onHoverNav('game')}
                    onMouseLeave={() => onHoverNav(null)}
                    onClick={() => {
                      setMenuOpen(false);
                      onTriggerSign('game');
                    }}
                  >
                    <span>{destinations.gamePortfolioLabel}</span>
                    <span aria-hidden="true">→</span>
                  </button>

                  <button
                    type="button"
                    className="popover-action-link"
                    onMouseEnter={() => onHoverNav('mailbox')}
                    onMouseLeave={() => onHoverNav(null)}
                    onClick={() => {
                      setMenuOpen(false);
                      onTriggerMailbox();
                    }}
                  >
                    <span>Contact Letter & QR</span>
                    <span aria-hidden="true">✉</span>
                  </button>

                  <button
                    type="button"
                    className="popover-action-link"
                    onClick={() => {
                      setMenuOpen(false);
                      onQuickSaveContact();
                    }}
                  >
                    <span>Save Contact (.vcf)</span>
                    <span aria-hidden="true">↓</span>
                  </button>
                </div>
              </div>

              <div className="popover-group">
                <span className="popover-label">Orientation</span>
                <div className="popover-pills">
                  <button
                    type="button"
                    className={`popover-btn ${activeCameraPreset === 'initial' ? 'active' : ''}`}
                    onClick={() => onChangeCameraPreset('initial')}
                  >
                    Front
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
                <span className="popover-label">Quality</span>
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

      {/* Transient Status Toast (Only visible after an action like Copy Link or Save vCard) */}
      {toastMessage && (
        <div className="bottom-toast-anchor">
          <div className="status-toast" role="status">
            {toastMessage}
          </div>
        </div>
      )}
    </div>
  );
};
