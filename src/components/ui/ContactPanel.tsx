import React, { useEffect, useState } from 'react';
import { PERSONAL_CONFIG, getResolvedCardUrl } from '../../config/personalConfig';
import {
  copyCardLink,
  downloadVCard,
  generateQrCodeDataUrl,
  shareDigitalCard,
} from '../../utils/nfcAndVcard';

interface ContactPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onStatusToast: (msg: string) => void;
}

export const ContactPanel: React.FC<ContactPanelProps> = ({
  isOpen,
  onClose,
  onStatusToast,
}) => {
  const { identity, destinations, contact } = PERSONAL_CONFIG;
  const [qrDataUrl, setQrDataUrl] = useState<string>('');
  const [localFeedback, setLocalFeedback] = useState<string | null>(null);

  const resolvedCard = getResolvedCardUrl();

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    generateQrCodeDataUrl(resolvedCard.url)
      .then((dataUrl) => {
        if (active) setQrDataUrl(dataUrl);
      })
      .catch(() => {
        if (active) setQrDataUrl('');
      });
    return () => {
      active = false;
    };
  }, [isOpen, resolvedCard.url]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const notify = (msg: string) => {
    setLocalFeedback(msg);
    onStatusToast(msg);
  };

  const handleSaveVCard = () => {
    const res = downloadVCard();
    notify(res.message);
  };

  const handleShare = async () => {
    const res = await shareDigitalCard();
    notify(res.message);
  };

  const handleCopy = async () => {
    const res = await copyCardLink();
    notify(res.message);
  };

  return (
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="contact-panel-title"
      onClick={onClose}
    >
      <div className="modal-card contact-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="modal-eyebrow">Woodland Mailbox · Digital Business Card</span>
            <h2 id="contact-panel-title" className="modal-title">
              {identity.displayName}
            </h2>
            <p className="modal-subtitle">{identity.professionalTitle}</p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close contact panel"
          >
            ✕
          </button>
        </div>

        <p className="contact-tagline">“{identity.tagline}”</p>

        {/* Primary Contact & Portfolio Actions */}
        <div className="contact-actions-grid">
          <button
            type="button"
            className="action-btn action-btn-primary"
            onClick={handleSaveVCard}
          >
            <span className="btn-icon" aria-hidden="true">↓</span>
            <span>Save Contact (.vcf)</span>
          </button>

          <a
            href={destinations.uxPortfolioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="action-btn action-btn-secondary"
          >
            <span className="btn-icon" aria-hidden="true">↗</span>
            <span>{destinations.uxPortfolioLabel}</span>
          </a>

          {destinations.gamePortfolioUrl.trim() && (
            <a
              href={destinations.gamePortfolioUrl.trim()}
              target="_blank"
              rel="noopener noreferrer"
              className="action-btn action-btn-secondary"
            >
              <span className="btn-icon" aria-hidden="true">↗</span>
              <span>{destinations.gamePortfolioLabel}</span>
            </a>
          )}

          {contact.email.trim() && (
            <a
              href={`mailto:${contact.email.trim()}`}
              className="action-btn action-btn-secondary"
            >
              <span className="btn-icon" aria-hidden="true">✉</span>
              <span>{contact.email.trim()}</span>
            </a>
          )}

          {contact.linkedInUrl.trim() && (
            <a
              href={contact.linkedInUrl.trim()}
              target="_blank"
              rel="noopener noreferrer"
              className="action-btn action-btn-secondary"
            >
              <span className="btn-icon" aria-hidden="true">in</span>
              <span>LinkedIn Profile</span>
            </a>
          )}

          <button
            type="button"
            className="action-btn action-btn-outline"
            onClick={handleShare}
          >
            <span className="btn-icon" aria-hidden="true">⌲</span>
            <span>Share Card</span>
          </button>

          <button
            type="button"
            className="action-btn action-btn-outline"
            onClick={handleCopy}
          >
            <span className="btn-icon" aria-hidden="true">⧉</span>
            <span>Copy Link</span>
          </button>
        </div>

        {localFeedback && (
          <div className="inline-feedback" role="status">
            {localFeedback}
          </div>
        )}

        {/* NFC & QR Code Section */}
        <div className="qr-section">
          {qrDataUrl && (
            <img
              src={qrDataUrl}
              alt={`QR Code for ${identity.displayName}`}
              className="qr-image"
              width={116}
              height={116}
            />
          )}
          <div className="qr-meta">
            <span className="qr-title">One Card, One Destination</span>
            <p className="qr-desc">
              Scan this QR code or tap the physical NFC card to open The Crossroads directly on any smartphone.
            </p>
            <span className="qr-url-note">{resolvedCard.statusNote}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
