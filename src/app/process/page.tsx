'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import FileUpload from '@/components/ui/FileUpload';
import { processImage, getAssetImageUrl, type ProcessResponse } from '@/lib/api';

type InputMode = 'upload' | 'prompt';

export default function ProcessPage() {
  const [mode, setMode] = useState<InputMode>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [issuerId, setIssuerId] = useState('prototype-issuer');
  const [userNote, setUserNote] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = mode === 'upload' ? !!file : prompt.trim().length > 0;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      if (mode === 'upload' && file) {
        formData.append('image_file', file);
      } else {
        formData.append('prompt', prompt.trim());
      }
      formData.append('issuer_id', issuerId);
      if (userNote.trim()) formData.append('user_note', userNote.trim());

      const res = await processImage(formData);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setFile(null);
    setPrompt('');
  };

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
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
            Process & Protect
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
            Protect your image
          </h1>
          <p className="mt-3 text-slate-500 text-sm max-w-md mx-auto">
            Upload an image or generate one from a prompt. The system will embed an invisible
            cryptographic watermark.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {result ? (
            /* ── Result Card ── */
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm overflow-hidden"
            >
              <div className="p-6 border-b border-slate-100 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                </div>
                <div>
                  <p className="font-semibold text-slate-900 text-sm">Image Protected</p>
                  <p className="text-xs text-slate-400">{result.message}</p>
                </div>
              </div>

              <div className="p-6">
                <div className="flex justify-center mb-6">
                  <img
                    src={getAssetImageUrl(result.asset_id)}
                    alt="Protected"
                    className="max-h-64 rounded-xl shadow-sm border border-slate-100"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="p-3 rounded-xl bg-slate-50">
                    <p className="text-xs text-slate-400 mb-1">Asset ID</p>
                    <p className="font-mono font-medium text-slate-800">{result.asset_id}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50">
                    <p className="text-xs text-slate-400 mb-1">Mode</p>
                    <p className="font-medium text-slate-800 capitalize">{result.input_mode}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50">
                    <p className="text-xs text-slate-400 mb-1">Signature</p>
                    <p className="font-medium text-slate-800 text-xs">{result.signature_alg}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-50">
                    <p className="text-xs text-slate-400 mb-1">Created</p>
                    <p className="font-medium text-slate-800 text-xs">
                      {new Date(result.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <a
                    href={getAssetImageUrl(result.asset_id)}
                    download={`protected-${result.asset_id}.png`}
                    className="flex-1 text-center py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-indigo-200/50 transition-all"
                  >
                    Download Protected Image
                  </a>
                  <Link
                    href="/verify"
                    className="py-2.5 px-4 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 transition-all"
                  >
                    Verify →
                  </Link>
                </div>

                <button
                  onClick={handleReset}
                  className="w-full mt-3 py-2 text-xs text-slate-400 hover:text-slate-600 transition-colors"
                >
                  Process another image
                </button>
              </div>
            </motion.div>
          ) : (
            /* ── Form ── */
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6"
            >
              {/* Mode Toggle */}
              <div className="flex p-1 bg-slate-100/80 rounded-xl mb-6">
                {(['upload', 'prompt'] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                      mode === m
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {m === 'upload' ? '📁 Upload Image' : '✨ Generate from Prompt'}
                  </button>
                ))}
              </div>

              {/* Input Area */}
              <AnimatePresence mode="wait">
                {mode === 'upload' ? (
                  <motion.div
                    key="upload"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 10 }}
                  >
                    <FileUpload onFileSelect={setFile} />
                  </motion.div>
                ) : (
                  <motion.div
                    key="prompt"
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                  >
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Describe the image you want to generate..."
                      rows={4}
                      className="w-full px-4 py-3.5 rounded-2xl border border-slate-200 bg-white/50 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 resize-none transition-all"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Advanced Options */}
              <div className="mt-5">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-xs text-slate-400 hover:text-slate-600 transition-colors flex items-center gap-1"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${showAdvanced ? 'rotate-90' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                  Advanced Options
                </button>
                <AnimatePresence>
                  {showAdvanced && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-3 space-y-3">
                        <input
                          value={issuerId}
                          onChange={(e) => setIssuerId(e.target.value)}
                          placeholder="Issuer ID"
                          className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white/50 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 transition-all"
                        />
                        <input
                          value={userNote}
                          onChange={(e) => setUserNote(e.target.value)}
                          placeholder="User note (optional)"
                          className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-white/50 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 transition-all"
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm"
                >
                  {error}
                </motion.div>
              )}

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={!canSubmit || loading}
                className={`w-full mt-6 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  canSubmit && !loading
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
                    Processing…
                  </span>
                ) : (
                  'Protect Image'
                )}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
