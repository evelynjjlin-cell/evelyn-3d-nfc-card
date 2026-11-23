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
      {/* Physical-Looking Unfolded Cream-Parchment Woodland Letter */}
      <article className="parchment-letter-card" onClick={(e) => e.stopPropagation()}>
        <div className="letter-inner-border">
          {/* Top Wax Seal Emblem & Close Button */}
          <div className="letter-top-bar">
            <div className="wax-seal-badge" aria-hidden="true">
              <span>EL</span>
            </div>
            <span className="letter-postmark">THE CROSSROADS · WOODLAND POST</span>
            <button
              type="button"
              className="letter-close-btn"
              onClick={onClose}
              aria-label="Fold and close letter"
              title="Close letter"
            >
              ✕
            </button>
          </div>

          {/* Letter Salutation & Identity */}
          <header className="letter-identity">
            <h2 id="contact-panel-title" className="letter-name">
              {identity.displayName}
            </h2>
            <p className="letter-role">{identity.professionalTitle}</p>
            <p className="letter-quote">“{identity.tagline}”</p>
          </header>

          <hr className="letter-fold-crease" aria-hidden="true" />

          {/* Contact & Portfolio Actions */}
          <div className="letter-actions-grid">
            <button
              type="button"
              className="letter-btn letter-btn-primary"
              onClick={handleSaveVCard}
            >
              <span aria-hidden="true">↓</span>
              <span>Save Contact (.vcf)</span>
            </button>

            <a
              href={destinations.uxPortfolioUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="letter-btn letter-btn-secondary"
            >
              <span>{destinations.uxPortfolioLabel}</span>
              <span aria-hidden="true">↗</span>
            </a>

            {destinations.gamePortfolioUrl.trim() && (
              <a
                href={destinations.gamePortfolioUrl.trim()}
                target="_blank"
                rel="noopener noreferrer"
                className="letter-btn letter-btn-secondary"
              >
                <span>{destinations.gamePortfolioLabel}</span>
                <span aria-hidden="true">↗</span>
              </a>
            )}

            {contact.email.trim() && (
              <a
                href={`mailto:${contact.email.trim()}`}
                className="letter-btn letter-btn-secondary"
              >
                <span>{contact.email.trim()}</span>
              </a>
            )}

            {contact.linkedInUrl.trim() && (
              <a
                href={contact.linkedInUrl.trim()}
                target="_blank"
                rel="noopener noreferrer"
                className="letter-btn letter-btn-secondary"
              >
                <span>LinkedIn</span>
              </a>
            )}

            <button
              type="button"
              className="letter-btn letter-btn-outline"
              onClick={handleShare}
            >
              <span>Share Card</span>
            </button>

            <button
              type="button"
              className="letter-btn letter-btn-outline"
              onClick={handleCopy}
            >
              <span>Copy Link</span>
            </button>
          </div>

          {localFeedback && (
            <div className="letter-feedback" role="status">
              {localFeedback}
            </div>
          )}

          {/* Postage Stamp QR Footer */}
          <footer className="letter-qr-footer">
            {qrDataUrl && (
              <div className="stamp-frame">
                <img
                  src={qrDataUrl}
                  alt={`QR Code for ${identity.displayName}`}
                  className="letter-qr-img"
                  width={96}
                  height={96}
                />
              </div>
            )}
            <div className="letter-qr-copy">
              <span className="letter-qr-heading">Tap or Scan to Keep</span>
              <p className="letter-qr-text">
                Point any smartphone camera at this stamp or tap the NFC card to revisit Evelyn’s forest crossroads.
              </p>
            </div>
          </footer>
        </div>
      </article>
    </div>
  );
};
