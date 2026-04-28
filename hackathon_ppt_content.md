# Hackathon PPT — Image Provenance System
> All content below is derived **strictly** from the existing project files. Nothing is invented or assumed.

---

## Slide 1 — Team Details & Problem Statement

### Team Details
- **Not specified** in any project file. No `README.md`, `CONTRIBUTORS`, or team metadata exists in the repository.

### Problem Statement
*(Extracted from [layout.tsx](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/src/app/layout.tsx), [page.tsx](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/src/app/page.tsx), and [config.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/core/config.py))*

In the age of AI-generated imagery and easy photo manipulation, there is **no reliable way to prove an image's origin or detect tampering** after the fact. Existing metadata (EXIF) can be trivially stripped or forged.

The system addresses: **How do you cryptographically bind provenance data to an image's pixels so that authenticity can be verified later — even if the image is re-saved, slightly modified, or laundered through transformations?**

The app title is *"Cryptographically Bound Semantic Watermark API"* (from `APP_NAME` in config). The frontend branding is *"Provenance — Cryptographic Image Verification"*.

---

## Slide 2 — Brief About the Solution

*(Derived from [process_pipeline.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/process_pipeline.py), [verify_pipeline.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/verify_pipeline.py), and [api.ts](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/src/lib/api.ts))*

The system is a **full-stack image provenance platform** with two core workflows:

### Protect (Process)
1. User uploads an image **or** provides a text prompt (deterministic stub generation).
2. The backend computes dual fingerprints (PDQ perceptual hash + Gemini semantic embedding).
3. A structured provenance payload is built and **RSA-PSS-SHA256 signed**.
4. A compact token (asset ID, commitment hash, mini-MAC, timestamp) is packed with **Reed-Solomon error correction** and embedded as an **invisible DWT-DCT-SVD watermark** directly into the image pixels.
5. The protected image and full record are persisted to a SQLite database.

### Verify
1. User uploads any image.
2. The backend extracts the invisible watermark, decodes the compact token, and looks up the provenance record.
3. It validates the RSA signature, commitment binding, mini-MAC, and compares current vs. baseline fingerprints (PDQ distance + semantic similarity).
4. A multi-signal verdict is produced (8 possible verdicts), and **Gemini AI generates a human-readable forensic explanation**.

---

## Slide 3 — Opportunities & USP

*(Only what is explicitly reflected in the implementation)*

| USP | Evidence in Code |
|---|---|
| **Cryptographic watermark binding** — not just metadata | Token is embedded into pixel data via DWT-DCT-SVD steganography ([watermark_codec.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/watermark_codec.py)) |
| **Dual fingerprinting** — pixel + semantic | PDQ hash (perceptual) + Gemini embedding (semantic) computed for every image ([fingerprint_pdq.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/fingerprint_pdq.py), [fingerprint_clip.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/fingerprint_clip.py)) |
| **Laundering attack detection** | Specific verdict `UNVERIFIED_SUSPICIOUS_LAUNDERING` when semantic similarity stays high but pixel hash diverges heavily ([verify_pipeline.py L213-214](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/verify_pipeline.py#L213-L214)) |
| **Reed-Solomon error correction** | Watermark payload survives mild image compression/noise via RS codec ([watermark_codec.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/watermark_codec.py)) |
| **AI-powered forensic explanation** | Gemini LLM generates natural-language verdict explanations ([gemini_explainer.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/gemini_explainer.py)) |
| **Offline-capable mini verification** | 16-bit HMAC mini-MAC allows local/offline token validation without DB lookup ([crypto_mac.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/crypto_mac.py), `/verify/local` endpoint) |
| **Dual-mode input** | Supports both image upload and text-prompt generation in a single workflow ([process route](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/api/routes/process.py)) |

---

## Slide 4 — Features of the Solution

*(Only features actually implemented in code/UI)*

1. **Image Protection** — Upload or prompt → sign → watermark → persist → return protected PNG
2. **Image Verification** — Upload → extract watermark → validate signature + commitment + MAC → dual fingerprint comparison → AI explanation
3. **Local/Offline Verification** — `/verify/local` endpoint for lightweight token-only check without full DB lookup
4. **Provenance Record Lookup** — Search by asset ID to retrieve full cryptographic record (payload, signature, hashes, commitment, MAC)
5. **Protected Image Download** — Retrieve the watermarked image as PNG via `/assets/{id}/image`
6. **System Health Dashboard** — Real-time health checks for all 6 backend services (RSA, watermark, CLIP/Gemini fingerprint, PDQ fingerprint, Gemini explainer, provenance store)
7. **8-Level Verification Verdicts**: `VERIFIED_AUTHENTIC`, `VERIFIED_MODIFIED`, `FORGED_TOKEN`, `TAMPERED_RECORD`, `FORGED_OR_UNKNOWN`, `UNVERIFIED_SUSPICIOUS_LAUNDERING`, `UNKNOWN_ORIGIN`, `INCONCLUSIVE`
8. **Advanced Options** — Configurable issuer ID and user notes during protection
9. **Auto-key Generation** — RSA keys and HMAC secret are auto-generated on first startup if absent
10. **Image Canonicalization** — Auto-resize (min 256×256, max 1024) for watermark compatibility

---

## Slide 5 — Process Flow / Use Case

### Use Case 1: Protect an Image

```
User → Upload image (or enter prompt)
  ↓
[If prompt] → DeterministicImageGenerationService generates striped image from hash
[If upload] → canonicalize_image() resizes to 256–1024px
  ↓
PDQFingerprintService.hash_image() → 256-bit perceptual hash
CLIPFingerprintService.embedding() → Gemini 3072-dim semantic vector
  ↓
Build payload JSON (asset_id, issuer_id, mode, timestamp, prompt_sha256, image_hash, pdq_hash, semantic_hash)
  ↓
RSASignatureService.sign(payload) → RSA-PSS-SHA256 signature
CommitmentService.build(asset_id, signature) → 64-bit SHA-256 commitment
MiniMACService.build(asset_id, issued_at) → 16-bit HMAC
  ↓
Pack compact token (v, asset_id, commitment, mini_mac, issued_at) → 19 bytes
RS encode → Reed-Solomon error correction
  ↓
WatermarkCodecService.embed(image, packed) → DWT-DCT-SVD invisible watermark
  ↓
ProvenanceStoreService.upsert_record() → SQLite persistence
  ↓
Return: asset_id, mode, protected_image_ref, created_at
```

### Use Case 2: Verify an Image

```
User → Upload image to verify
  ↓
canonicalize_image() → compute current PDQ hash + Gemini embedding
WatermarkCodecService.extract() → extract bytes from pixels
  ↓
[No watermark?] → Verdict: UNKNOWN_ORIGIN
[Unpack fails?] → Verdict: FORGED_TOKEN
  ↓
unpack_token() → extract asset_id, commitment, mini_mac, issued_at
MiniMACService.verify() → local MAC check
  ↓
ProvenanceStoreService.get_record(asset_id)
[No record?] → FORGED_OR_UNKNOWN or FORGED_TOKEN
  ↓
RSASignatureService.verify(payload, signature) → signature check
CommitmentService.verify() → commitment binding check
  ↓
Compare PDQ distance + semantic similarity against thresholds
  ↓
Determine verdict (8 possible outcomes)
GeminiExplainerService.explain_verification() → AI explanation
  ↓
Return: verdict, signals, explanation, reasons
```

---

## Slide 6 — Wireframes / UI Description

*(Based on actual TSX components in the codebase)*

### Global Layout
- **Navbar**: Fixed top, glassmorphic (`backdrop-blur-xl bg-white/60`), gradient logo (indigo→violet shield icon), 5 nav links: Home, Protect, Verify, Records, Health. Active tab has animated indicator via Framer Motion `layoutId`.
- **Wave Background**: Full-screen fixed background with diagonal shining gradient animation (14s cycle) + two ambient floating glow blobs (22s & 28s cycles, indigo/violet radial gradients with 100px blur).
- **Typography**: Inter font (Google Fonts), light theme (`#FAFBFF` body bg).

### Home Page (`/`)
- Hero section (88vh) with animated badge "Cryptographic Image Provenance", large heading "Image Provenance, Verified." with gradient text, subtitle, two CTA buttons (Protect → gradient, Verify → outlined).
- "How It Works" section: 3-column card grid (Upload/Generate → Cryptographic Protection → Forensic Verification) with step numbers, icons, hover shadows.
- "Under The Hood" section: 2×2 feature cards (RSA-PSS Signing, Invisible Watermark, Dual Fingerprinting, AI Explanation) with color-coded gradient dots.
- Footer: "Hackathon 2026" branding.

### Protect Page (`/process`)
- Mode toggle (Upload Image / Generate from Prompt) — pill-style switcher.
- Upload mode: drag-and-drop zone with preview (FileUpload component with drag states, image preview, file name display).
- Prompt mode: multi-line textarea.
- Collapsible "Advanced Options" section (Issuer ID input, User Note input).
- Submit button with loading spinner. Error display in red banner.
- **Result card**: Green checkmark header, protected image preview loaded from API, 2×2 info grid (Asset ID, Mode, Signature algo, Created date), "Download Protected Image" gradient button + "Verify →" link, "Process another" reset button.

### Verify Page (`/verify`)
- File upload zone (same FileUpload component, "Drop an image to verify").
- Submit with loading spinner.
- **Results**: Large verdict card with color-coded background/icon (8 verdict variants mapped to specific colors — emerald for authentic, amber for modified, red for forged, orange for laundering, slate for unknown).
- **Signals grid**: 3×2 grid of SignalBadge components showing Signature, Watermark, Mini-MAC, Commitment, PDQ Distance, Semantic Similarity — each color-coded (green dot for pass, red for fail, gray for N/A).
- **AI Analysis** section: Robot icon + Gemini explanation text.
- **Detailed Reasons** section: Bulleted monospace list of all diagnostic reasons.

### Records Page (`/records`)
- Search bar (monospace input for asset ID) + Search button.
- Result card: Asset ID header with timestamp, 2×2 info grid (PDQ Hash, Semantic Hash, Commitment, Mini-MAC), Signature (B64) field, Payload JSON block (formatted, scrollable).

### Health Page (`/health`)
- Auto-loads on mount (useEffect).
- Overall status card (green "All Systems Operational" or amber "Degraded") with version number.
- Services list: Each service shown with name + Healthy/Down badge (green/red pill with dot indicator). Services checked: RSA Service, Watermark Service, CLIP Fingerprint Service, PDQ Fingerprint Service, Gemini Explainer Service, Provenance Store.

---

## Slide 7 — System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐│
│  │  Home    │ │ Process  │ │  Verify  │ │Records │ │Health││
│  │  page    │ │  page    │ │  page    │ │ page   │ │ page ││
│  └──────────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └──┬───┘│
│                    │            │            │         │     │
│              ┌─────┴────────────┴────────────┴─────────┴──┐  │
│              │          api.ts (HTTP client)               │  │
│              │  processImage / verifyImage / getRecord /   │  │
│              │  getHealth / getAssetImageUrl               │  │
│              └─────────────────┬───────────────────────────┘  │
└────────────────────────────────┼──────────────────────────────┘
                                 │  HTTP (localhost:8000)
                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI + Uvicorn)                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  API Layer (/api/v1)                                  │    │
│  │  POST /process │ POST /verify │ POST /verify/local    │    │
│  │  GET /records/{id} │ GET /assets/{id}/image           │    │
│  │  GET /health                                          │    │
│  └────────────────────────┬──────────────────────────────┘    │
│                           ▼                                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  AppContainer (Singleton via Lifespan)                │    │
│  │  ┌────────────────┐ ┌──────────────────────────┐      │    │
│  │  │ RSASignature   │ │ WatermarkCodecService    │      │    │
│  │  │ Service        │ │ (DWT-DCT-SVD + RS codec) │      │    │
│  │  ├────────────────┤ ├──────────────────────────┤      │    │
│  │  │ Commitment     │ │ PDQFingerprintService    │      │    │
│  │  │ Service        │ │ (pdqhash)                │      │    │
│  │  ├────────────────┤ ├──────────────────────────┤      │    │
│  │  │ MiniMAC        │ │ CLIPFingerprintService   │      │    │
│  │  │ Service        │ │ (Gemini Embeddings)      │      │    │
│  │  ├────────────────┤ ├──────────────────────────┤      │    │
│  │  │ GeminiExplainer│ │ ImageGeneration (stub)   │      │    │
│  │  │ Service        │ │                          │      │    │
│  │  └────────────────┘ └──────────────────────────┘      │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │ ProvenanceStoreService (SQLite)                │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌───────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│  │ keys/     │  │ data/         │  │ External APIs         │ │
│  │ RSA .pem  │  │ provenance.db │  │ Gemini Embedding API  │ │
│  │ HMAC .key │  │ (SQLite)      │  │ Gemini Generate API   │ │
│  └───────────┘  └───────────────┘  └───────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Key Architecture Points
- **Dependency Injection**: All services instantiated once at startup in `AppContainer` dataclass, injected via `request.app.state.container`.
- **CORS**: Wide-open (`allow_origins=["*"]`) for development.
- **Database**: Single-file SQLite with thread-safe locking, auto-schema migration on startup.
- **Key Management**: RSA 2048-bit keys + 32-byte HMAC secret auto-generated if absent, stored as PEM/binary files.
- **Gemini Integration**: Used for both semantic embeddings (embedding model) and natural-language explanations (generative model, `gemini-2.5-flash`). Falls back gracefully if disabled.

---

## Slide 8 — Technologies Used

### Backend
| Technology | Version/Details | Purpose |
|---|---|---|
| **Python** | 3.10+ (type hints with `X \| None`) | Core language |
| **FastAPI** | ≥0.115.0 | REST API framework |
| **Uvicorn** | ≥0.30.0 (standard) | ASGI server |
| **Pydantic** | ≥2.8.0 | Schema validation |
| **Pillow** | ≥10.4.0 | Image processing |
| **OpenCV** (`opencv-python`) | ≥4.10.0 | Image color space conversion |
| **NumPy** | ≥1.26.4 | Array operations |
| **invisible-watermark** | ≥0.2.0 | DWT-DCT-SVD steganography |
| **reedsolo** | ≥1.7.0 | Reed-Solomon error correction |
| **cryptography** | ≥43.0.0 | RSA-PSS signing, HMAC |
| **pdqhash** | ≥0.2.6 | PDQ perceptual hashing |
| **google-genai** | ≥1.0.0 | Gemini embedding + generation API |
| **python-dotenv** | ≥1.0.1 | Environment loading |
| **python-multipart** | ≥0.0.9 | File upload parsing |
| **SQLite** | (stdlib) | Provenance record persistence |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 14.2.15 | React framework (App Router) |
| **React** | ^18.3.1 | UI library |
| **TypeScript** | ^5.6.0 | Type safety |
| **Tailwind CSS** | ^3.4.13 | Utility-first styling |
| **Framer Motion** | ^11.11.0 | Animations & transitions |
| **Inter** (Google Font) | — | Typography |
| **PostCSS + Autoprefixer** | ^8.4.47 / ^10.4.20 | CSS processing |

---

## Slide 9 — MVP & Implementation Cost

### Current MVP Status

| Feature | Status |
|---|---|
| Image upload → watermark → protected download | ✅ Implemented |
| Prompt → deterministic image generation → watermark | ✅ Implemented (stub/placeholder images, not real AI generation) |
| RSA-PSS-SHA256 digital signing | ✅ Implemented |
| Invisible DWT-DCT-SVD watermark embedding | ✅ Implemented |
| Reed-Solomon error-corrected compact token | ✅ Implemented |
| Watermark extraction & token decoding | ✅ Implemented |
| Multi-signal verification (signature + commitment + MAC + dual fingerprint) | ✅ Implemented |
| 8-level verdict classification | ✅ Implemented |
| PDQ perceptual hash fingerprinting | ✅ Implemented |
| Gemini semantic embedding fingerprinting | ✅ Implemented (with fallback hash-based when disabled) |
| Gemini AI forensic explanation | ✅ Implemented (with local fallback text) |
| Offline local verification (`/verify/local`) | ✅ Implemented |
| Provenance record storage (SQLite) | ✅ Implemented |
| Protected image retrieval API | ✅ Implemented |
| Health check dashboard | ✅ Implemented |
| Record lookup by asset ID | ✅ Implemented |
| Full responsive frontend with animations | ✅ Implemented |

### What Is **Not** in the MVP
- Image generation is a **deterministic stub** (hashed color stripes + text overlay), not a real generative AI model.
- CLIP model support is **commented out / deprecated** — replaced entirely by Gemini embeddings.
- No user authentication or authorization.
- No batch processing or listing of all records.
- No deployment configuration files (Dockerfile, docker-compose, Vercel config) present in the repo.

### Implementation Cost
**Not specified** — No cost estimates, pricing models, or budget documents exist in the project files.

---

## Slide 10 — Future Scope & Links

### Future Scope
**Not explicitly mentioned** in any project file. There is no `ROADMAP.md`, `TODO.md`, or inline future-scope comments in the codebase.

> [!NOTE]
> The following are **observable gaps** (not future scope), stated factually:
> - CLIP model integration is commented out and marked `deprecated, kept for compat` in [config.py L45](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/core/config.py#L45), indicating it was replaced by Gemini embeddings.
> - The image generation service is documented as a *"Deterministic local prompt-to-image stub for prototype flow wiring"* in [image_generation.py](file:///c:/Users/Acer/OneDrive/Desktop/image-provenance-system2/backend/app/services/image_generation.py), indicating a real generative model was anticipated but not implemented.
> - The footer explicitly says *"Hackathon 2026"*, confirming this is a hackathon prototype.

### Links
- **Repository URL**: Not available in any project file.
- **Deployed URL**: Not available in any project file.
- **Demo Video**: Not available.
- **API Docs**: When the backend runs, FastAPI auto-generates docs at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc` (ReDoc) — this is standard FastAPI behavior, not custom.
- **Frontend Dev Server**: `http://localhost:3000` (via `npm run dev`)
- **Backend Dev Server**: `http://localhost:8000` (via uvicorn)
