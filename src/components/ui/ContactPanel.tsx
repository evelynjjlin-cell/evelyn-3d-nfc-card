import React, { useEffect, useRef, useState } from 'react';
import { PERSONAL_CONFIG, getResolvedCardUrl } from '../../config/personalConfig';
import { downloadVCard, generateQrCodeDataUrl } from '../../utils/nfcAndVcard';

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
  const { identity, contact } = PERSONAL_CONFIG;
  const [qrDataUrl, setQrDataUrl] = useState('');
  const [localFeedback, setLocalFeedback] = useState<string | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
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
    const previousFocus = document.activeElement;
    setLocalFeedback(null);
    closeButtonRef.current?.focus({ preventScroll: true });

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;

      const panel = panelRef.current;
      const focusable = panel?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!panel || !focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const focusIsOutside = !panel.contains(document.activeElement);

      if (event.shiftKey && (document.activeElement === first || focusIsOutside)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || focusIsOutside)) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) {
        previousFocus.focus({ preventScroll: true });
      }
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSaveVCard = () => {
    const result = downloadVCard();
    setLocalFeedback(result.success ? 'Open the downloaded file to save my contact.' : result.message);
    onStatusToast(result.message);
  };

  return (
    <div className="modal-backdrop contact-backdrop" onClick={onClose}>
      <article
        ref={panelRef}
        className="parchment-letter-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="contact-panel-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="letter-top-bar">
          <img
            src="/brand/evelyn-orbit.svg"
            alt="Evelyn Lin's logo"
            className="letter-brand-mark"
            width={48}
            height={56}
          />
          <button
            ref={closeButtonRef}
            type="button"
            className="letter-close-btn"
            onClick={onClose}
            aria-label="Close contact letter"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <header className="letter-identity">
          <h2 id="contact-panel-title" className="letter-name">{identity.displayName}</h2>
          <p className="letter-role">{identity.professionalTitle}</p>
          <p className="letter-quote">{identity.tagline}</p>
        </header>

        <div className="letter-contact-links">
          {contact.email.trim() && (
            <a href={`mailto:${contact.email.trim()}`} className="letter-contact-link">
              {contact.email.trim()}
            </a>
          )}
          {contact.linkedInUrl.trim() && (
            <a
              href={contact.linkedInUrl.trim()}
              target="_blank"
              rel="noopener noreferrer"
              className="letter-contact-link"
            >
              LinkedIn <span aria-hidden="true">↗</span>
            </a>
          )}
        </div>

        <footer className="letter-save-footer">
          <button type="button" className="letter-save-btn" onClick={handleSaveVCard}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 4v12m-5-5 5 5 5-5M5 20h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Save Contact</span>
          </button>
          {qrDataUrl && (
            <figure className="letter-qr">
              <img
                src={qrDataUrl}
                alt={`QR code to reopen ${identity.displayName}'s digital card`}
                className="letter-qr-img"
                width={96}
                height={96}
              />
              <figcaption>Scan to revisit</figcaption>
            </figure>
          )}
        </footer>

        {localFeedback && <p className="letter-feedback" role="status">{localFeedback}</p>}
      </article>
    </div>
  );
};
