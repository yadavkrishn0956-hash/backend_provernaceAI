'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { getRecord, type RecordResponse } from '@/lib/api';

export default function RecordsPage() {
  const [assetId, setAssetId] = useState('');
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<RecordResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!assetId.trim()) return;
    setLoading(true);
    setError(null);
    setRecord(null);

    try {
      const res = await getRecord(assetId.trim());
      setRecord(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Record not found');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-16 px-6">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50/80 text-indigo-600 text-xs font-medium mb-4 border border-indigo-100/50">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            Provenance Records
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
            Lookup a record
          </h1>
          <p className="mt-3 text-slate-500 text-sm">
            Enter an asset ID to retrieve its full provenance record.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6"
        >
          <div className="flex gap-3">
            <input
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. a1b2c3d4"
              className="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-white/50 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition-all"
            />
            <button
              onClick={handleSearch}
              disabled={!assetId.trim() || loading}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-indigo-200/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '…' : 'Search'}
            </button>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm"
            >
              {error}
            </motion.div>
          )}
        </motion.div>

        {record && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6 space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">
                Asset <span className="font-mono text-indigo-600">{record.asset_id}</span>
              </h3>
              <span className="text-xs text-slate-400">
                {new Date(record.created_at).toLocaleString()}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 rounded-xl bg-slate-50">
                <p className="text-xs text-slate-400 mb-1">PDQ Hash</p>
                <p className="font-mono text-xs text-slate-700 break-all">{record.pdq_hash_hex}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50">
                <p className="text-xs text-slate-400 mb-1">Semantic Hash</p>
                <p className="font-mono text-xs text-slate-700 break-all">{record.semantic_hash_hex}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50">
                <p className="text-xs text-slate-400 mb-1">Commitment</p>
                <p className="font-mono text-xs text-slate-700">{record.commitment || '—'}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50">
                <p className="text-xs text-slate-400 mb-1">Mini-MAC</p>
                <p className="font-mono text-xs text-slate-700">{record.mini_mac || '—'}</p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50">
              <p className="text-xs text-slate-400 mb-1">Signature (B64)</p>
              <p className="font-mono text-xs text-slate-700 break-all line-clamp-2">{record.signature_b64}</p>
            </div>

            <div className="p-3 rounded-xl bg-slate-50">
              <p className="text-xs text-slate-400 mb-2">Payload</p>
              <pre className="text-xs text-slate-600 overflow-auto max-h-48 font-mono">
                {JSON.stringify(record.payload, null, 2)}
              </pre>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
