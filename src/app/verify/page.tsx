'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import FileUpload from '@/components/ui/FileUpload';
import { verifyImage, type VerifyResponse } from '@/lib/api';

const verdictConfig: Record<string, { color: string; bg: string; border: string; icon: string; label: string }> = {
  VERIFIED_AUTHENTIC: {
    color: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    icon: '✅',
    label: 'Verified Authentic',
  },
  VERIFIED_MODIFIED: {
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    icon: '⚠️',
    label: 'Verified — Modified',
  },
  FORGED_TOKEN: {
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: '❌',
    label: 'Forged Token',
  },
  TAMPERED_RECORD: {
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: '❌',
    label: 'Tampered Record',
  },
  FORGED_OR_UNKNOWN: {
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: '❌',
    label: 'Forged or Unknown',
  },
  UNVERIFIED_SUSPICIOUS_LAUNDERING: {
    color: 'text-orange-700',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    icon: '🔴',
    label: 'Suspicious Laundering',
  },
  UNKNOWN_ORIGIN: {
    color: 'text-slate-600',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    icon: '❓',
    label: 'Unknown Origin',
  },
  INCONCLUSIVE: {
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    icon: '⚠️',
    label: 'Inconclusive',
  },
};

function SignalBadge({ label, value, pass }: { label: string; value?: string | number | null; pass?: boolean | null }) {
  const isPass = pass === true;
  const isFail = pass === false;
  return (
    <div className={`p-3 rounded-xl border ${isPass ? 'bg-emerald-50/50 border-emerald-100' : isFail ? 'bg-red-50/50 border-red-100' : 'bg-slate-50 border-slate-100'}`}>
      <div className="flex items-center gap-1.5 mb-1">
        {isPass && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
        {isFail && <span className="w-1.5 h-1.5 rounded-full bg-red-500" />}
        {pass === null || pass === undefined ? <span className="w-1.5 h-1.5 rounded-full bg-slate-300" /> : null}
        <p className="text-xs text-slate-500 font-medium">{label}</p>
      </div>
      <p className={`text-sm font-semibold ${isPass ? 'text-emerald-700' : isFail ? 'text-red-700' : 'text-slate-700'}`}>
        {value !== null && value !== undefined ? String(value) : '—'}
      </p>
    </div>
  );
}

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [assetIdHint, setAssetIdHint] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image_file', file);
      if (assetIdHint.trim()) formData.append('asset_id_hint', assetIdHint.trim());
      const res = await verifyImage(formData);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setFile(null);
    setAssetIdHint('');
  };

  const vc = result ? verdictConfig[result.verdict] || verdictConfig.UNKNOWN_ORIGIN : null;

  return (
    <div className="min-h-screen py-16 px-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50/80 text-indigo-600 text-xs font-medium mb-4 border border-indigo-100/50">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
            Forensic Verification
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
            Verify an image
          </h1>
          <p className="mt-3 text-slate-500 text-sm max-w-md mx-auto">
            Upload any image to check its provenance. The system extracts the watermark, verifies
            cryptographic signatures, and analyzes fingerprints.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {result && vc ? (
            /* ── Results ── */
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-5"
            >
              {/* Verdict Card */}
              <div className={`${vc.bg} ${vc.border} border rounded-2xl p-8 text-center`}>
                <div className="text-4xl mb-3">{vc.icon}</div>
                <h2 className={`text-2xl font-bold ${vc.color}`}>{vc.label}</h2>
                {result.asset_id && (
                  <p className="mt-2 text-sm text-slate-500">
                    Asset: <span className="font-mono font-medium">{result.asset_id}</span>
                  </p>
                )}
              </div>

              {/* Signals Grid */}
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6">
                <h3 className="text-sm font-semibold text-slate-700 mb-4">Verification Signals</h3>
                <div className="grid grid-cols-3 gap-3">
                  <SignalBadge
                    label="Signature"
                    value={result.signals.signature_valid ? 'Valid' : 'Invalid'}
                    pass={result.signals.signature_valid}
                  />
                  <SignalBadge
                    label="Watermark"
                    value={result.signals.watermark_detected ? 'Detected' : 'Not Found'}
                    pass={result.signals.watermark_detected}
                  />
                  <SignalBadge
                    label="Mini-MAC"
                    value={result.signals.local_mac_valid === null ? '—' : result.signals.local_mac_valid ? 'Valid' : 'Invalid'}
                    pass={result.signals.local_mac_valid}
                  />
                  <SignalBadge
                    label="Commitment"
                    value={result.signals.commitment_valid === null ? '—' : result.signals.commitment_valid ? 'Valid' : 'Invalid'}
                    pass={result.signals.commitment_valid}
                  />
                  <SignalBadge
                    label="PDQ Distance"
                    value={result.signals.pdq_distance ?? '—'}
                    pass={result.signals.pdq_result === 'IDENTICAL' ? true : result.signals.pdq_result === 'HEAVILY_MODIFIED' ? false : null}
                  />
                  <SignalBadge
                    label="Semantic Similarity"
                    value={result.signals.clip_similarity !== null && result.signals.clip_similarity !== undefined ? result.signals.clip_similarity.toFixed(4) : '—'}
                    pass={result.signals.clip_result === 'SAME_OR_TRIVIAL' ? true : result.signals.clip_result === 'DIFFERENT_CONTENT' ? false : null}
                  />
                </div>
              </div>

              {(result.signals.current_pdq_hash_hex || result.signals.current_semantic_hash_hex) && (
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Computed Hashes</h3>
                  <div className="space-y-3">
                    {result.signals.current_pdq_hash_hex && (
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Current PDQ Hash</p>
                        <p className="font-mono text-xs text-slate-700 break-all">{result.signals.current_pdq_hash_hex}</p>
                      </div>
                    )}
                    {result.signals.current_semantic_hash_hex && (
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Current Semantic Hash</p>
                        <p className="font-mono text-xs text-slate-700 break-all">{result.signals.current_semantic_hash_hex}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* AI Explanation */}
              {result.gemini_explanation && (
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
                      <span className="text-xs">🤖</span>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-700">AI Analysis</h3>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {result.gemini_explanation}
                  </p>
                </div>
              )}

              {/* Reasons */}
              {result.reasons.length > 0 && (
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Detailed Reasons</h3>
                  <ul className="space-y-2">
                    {result.reasons.map((reason, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-500">
                        <span className="w-1 h-1 rounded-full bg-slate-300 mt-2 shrink-0" />
                        <span className="font-mono text-xs">{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={handleReset}
                className="w-full py-3 rounded-xl border border-slate-200 text-sm text-slate-500 hover:text-slate-700 hover:bg-white transition-all"
              >
                Verify another image
              </button>
            </motion.div>
          ) : (
            /* ── Upload Form ── */
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6"
            >
              <FileUpload
                onFileSelect={setFile}
                label="Drop an image to verify"
                sublabel="Upload any image — protected or not"
              />

              <div className="mt-4">
                <label className="block text-xs font-medium text-slate-500 mb-1.5">
                  Asset ID hint (optional)
                </label>
                <input
                  value={assetIdHint}
                  onChange={(e) => setAssetIdHint(e.target.value)}
                  placeholder="Use this if cropping or regeneration removed the watermark"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white/50 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition-all"
                />
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm"
                >
                  {error}
                </motion.div>
              )}

              <button
                onClick={handleSubmit}
                disabled={!file || loading}
                className={`w-full mt-6 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  file && !loading
                    ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:shadow-indigo-300/50 hover:scale-[1.01]'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Analyzing…
                  </span>
                ) : (
                  'Verify Image'
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
