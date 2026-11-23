# Physical NFC Card Setup & Print Artwork Concept
**Project:** The Crossroads — High-Fidelity 3D Interactive NFC Business Card (`evelyn-3d-nfc-card`)  
**Owner:** Evelyn Lin · UX & Interactive Experience Designer

---

## 1. NFC Architecture — One Card, One Destination

The physical NFC business card stores **one NDEF URI record** pointing to the permanent `https://` URL of this digital business card.

- **Do not** attempt to store the 3D application on the NFC chip itself.
- **Do not** require the recipient to install an NFC reader app. Modern iPhones (iOS 14+) and Android devices with NFC enabled read NDEF URI records natively from the lock screen / home screen.
- When tapped, compatible smartphones display a system notification banner prompting the visitor to open the website in their default mobile browser.
- **Important note on Contact Saving:** Tapping the physical NFC card opens the interactive 3D forest webpage; from there, tapping the **Woodland Mailbox** or **Save Contact** button downloads the `.vcf` vCard (`Evelyn-Lin.vcf`) for one-tap saving into the visitor's address book.

---

## 2. Recommended NFC Hardware

- **Chip Type:** `NTAG213` (144 bytes user memory — plenty for any HTTPS URL), `NTAG215` (504 bytes), or `NTAG216` (888 bytes).
- **Form Factor:** Standard CR80 credit-card size (`85.60 × 53.98 mm` / `3.375 × 2.125 in`), matte PVC or coated bamboo/wood card.
- **Condition:** Unlocked / writable (do **not** set permanent write-lock during initial testing so the URL can be updated if the domain ever changes).

---

## 3. Step-by-Step NFC Encoding Instructions

1. **Deploy the web application** to its permanent HTTPS domain (for example, `https://card.evelynjlin.com` or your chosen Vercel production domain).
2. **Update `src/config/personalConfig.ts`**:
   ```ts
   nfc: {
     publicCardUrl: 'https://your-permanent-card-domain.com',
     fallbackPortfolioUrl: 'https://evelynjlin.com',
   }
   ```
3. **Install a free NFC writing utility** on your smartphone, such as **NFC Tools** (iOS / Android) or **NXP TagWriter** (iOS / Android).
4. **Write the NDEF URI Record**:
   - Open **NFC Tools** → **Write** → **Add a record** → **URL / URI**.
   - Select protocol `https://` and enter your permanent card URL.
   - Tap **Write** and hold the physical NFC card against the top-rear NFC antenna of your phone until confirmation appears.
5. **Verify on iPhone and Android**:
   - Wake the phone screen (no app open).
   - Hold the card near the top edge (iPhone) or center-back (Android).
   - Confirm the system banner appears and opens **The Crossroads** in Safari/Chrome.
6. **Rewriting Later**:
   - As long as you do not choose "Lock Tag Permanently", you can repeat step 4 at any time to overwrite the NDEF record with a new URL.

---

## 4. Physical NFC Card — Print Artwork Concept (CR80 Standard)

> [!NOTE]
> The specifications below are an initial visual concept matching the 3D environment palette. Always verify bleed (`+3 mm`), safe margin (`3.5 mm`), and internal NFC antenna/chip clearance against your card printer's template before ordering.

### Front Concept — Minimal Collectible Identity
- **Background:** Deep Forest Green (`#193C32`) ultra-matte finish
- **Center / Left Emblem:** Subtle blind-debossed or soft champagne (`#DCC99D`) line-art crossroads & botanical sprig motif
- **Primary Typography:**
  - **Evelyn Lin** — Editorial Serif (`Cormorant Garamond SemiBold`, Warm Ivory `#F4F0E6`)
  - **UX & INTERACTIVE EXPERIENCE DESIGNER** — Clean Sans (`Plus Jakarta Sans SemiBold`, Soft Champagne `#DCC99D`, tracked uppercase)

### Back Concept — Tap & Scan Discovery
- **Background:** Deep Forest Green (`#193C32`) with a fine champagne border hairline
- **QR Code:** High-contrast Warm Ivory (`#F4F0E6`) & Deep Forest (`#193C32`) QR code exported from the deployed card's production URL (minimum `18 × 18 mm` print size for instant camera recognition)
- **Call to Action:**
  - **Tap to Explore the Forest** (NFC waves icon + `"Or scan QR to enter The Crossroads"`)
  - `evelynjlin.com`
