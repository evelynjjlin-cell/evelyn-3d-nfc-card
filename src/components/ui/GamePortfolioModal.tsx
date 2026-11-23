import React, { useEffect } from 'react';
import { PERSONAL_CONFIG } from '../../config/personalConfig';

interface GamePortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenContact: () => void;
}

export const GamePortfolioModal: React.FC<GamePortfolioModalProps> = ({
  isOpen,
  onClose,
  onOpenContact,
}) => {
  const { destinations } = PERSONAL_CONFIG;

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="game-modal-title"
      onClick={onClose}
    >
      <div className="modal-card game-placeholder-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">Right Woodland Path · {destinations.gamePortfolioLabel}</span>
            <h2 id="game-modal-title" className="modal-title">
              {destinations.gamePortfolioPlaceholderTitle}
            </h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close message"
          >
            ✕
          </button>
        </div>

        <p className="modal-body-text">
          {destinations.gamePortfolioPlaceholderMessage}
        </p>

        <div className="modal-footer-actions">
          <a
            href={destinations.uxPortfolioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn action-btn-primary"
          >
            <span>Visit {destinations.uxPortfolioLabel} ↗</span>
          </a>
          <button
            type="button"
            className="action-btn action-btn-secondary"
            onClick={() => {
              onClose();
              onOpenContact();
            }}
          >
            <span>Open Contact Card</span>
          </button>
        </div>
      </div>
    </div>
  );
};
