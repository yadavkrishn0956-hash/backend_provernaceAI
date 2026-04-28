'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

const steps = [
  {
    num: '01',
    title: 'Upload or Generate',
    desc: 'Provide an image file or text prompt — the system handles both paths seamlessly.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    num: '02',
    title: 'Cryptographic Protection',
    desc: 'RSA-signed provenance payload is packed into an invisible watermark embedded directly into pixels.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
  },
  {
    num: '03',
    title: 'Forensic Verification',
    desc: 'AI-powered analysis extracts the token, verifies signatures, and compares dual fingerprints.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
];

const features = [
  {
    title: 'RSA-PSS Signing',
    desc: '2048-bit RSA digital signatures for tamper-proof provenance binding.',
    gradient: 'from-blue-500 to-indigo-500',
  },
  {
    title: 'Invisible Watermark',
    desc: 'DWT-DCT-SVD steganography with Reed-Solomon error correction.',
    gradient: 'from-indigo-500 to-violet-500',
  },
  {
    title: 'Dual Fingerprinting',
    desc: 'PDQ perceptual hashes + Gemini semantic embeddings detect even laundering attacks.',
    gradient: 'from-violet-500 to-purple-500',
  },
  {
    title: 'AI Explanation',
    desc: 'Gemini-powered natural language forensic analysis for every verification.',
    gradient: 'from-purple-500 to-pink-500',
  },
];

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

export default function HomePage() {
  return (
    <div className="relative">
      {/* ── Hero ── */}
      <section className="relative min-h-[88vh] flex items-center justify-center px-6">
        <div className="text-center max-w-3xl mx-auto">
          <motion.div {...fadeUp} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50/80 text-indigo-600 text-sm font-medium mb-8 border border-indigo-100/50">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              Cryptographic Image Provenance
            </div>
          </motion.div>

          <motion.h1
            {...fadeUp}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight text-slate-900 leading-[1.1]"
          >
            Image Provenance,{' '}
            <span className="bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 bg-clip-text text-transparent">
              Verified.
            </span>
          </motion.h1>

          <motion.p
            {...fadeUp}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-7 text-lg md:text-xl text-slate-500 max-w-xl mx-auto leading-relaxed"
          >
            Embed invisible cryptographic watermarks into any image.
            Verify authenticity with AI-powered forensic analysis.
          </motion.p>

          <motion.div
            {...fadeUp}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/process"
              className="px-7 py-3.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-medium shadow-lg shadow-indigo-200/50 hover:shadow-xl hover:shadow-indigo-300/50 hover:scale-[1.02] transition-all duration-200 text-sm"
            >
              Protect an Image →
            </Link>
            <Link
              href="/verify"
              className="px-7 py-3.5 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-white hover:border-slate-300 hover:shadow-sm transition-all duration-200 text-sm bg-white/50"
            >
              Verify an Image
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-sm font-medium text-indigo-500 mb-3 tracking-wide uppercase">
              How It Works
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
              Three steps to provenance
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12, duration: 0.5 }}
                className="relative p-7 rounded-2xl bg-white/70 backdrop-blur-sm border border-slate-100 shadow-sm hover:shadow-md hover:border-slate-200 transition-all duration-300 group"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center text-indigo-600 mb-5 group-hover:shadow-md group-hover:shadow-indigo-100 transition-shadow">
                  {step.icon}
                </div>
                <div className="text-xs font-bold text-indigo-400 mb-2 tracking-widest">
                  STEP {step.num}
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech Features ── */}
      <section className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-sm font-medium text-indigo-500 mb-3 tracking-wide uppercase">
              Under The Hood
            </p>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
              Built on real cryptography
            </h2>
          </motion.div>

          <div className="grid sm:grid-cols-2 gap-5">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="p-6 rounded-2xl bg-white/70 backdrop-blur-sm border border-slate-100 hover:border-slate-200 shadow-sm hover:shadow-md transition-all duration-300"
              >
                <div
                  className={`inline-block w-2 h-2 rounded-full bg-gradient-to-r ${f.gradient} mb-4`}
                />
                <h3 className="text-base font-semibold text-slate-900 mb-1.5">
                  {f.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-12 px-6 border-t border-slate-100">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <span className="text-sm font-semibold text-slate-700">Provenance</span>
          </div>
          <p className="text-xs text-slate-400">
            Cryptographically Bound Semantic Watermark System — Hackathon 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
