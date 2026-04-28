'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { getHealth, type HealthResponse } from '@/lib/api';

export default function HealthPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            System Health
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
            Service Status
          </h1>
          <p className="mt-3 text-slate-500 text-sm">
            Real-time health of all backend services.
          </p>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <svg className="w-8 h-8 animate-spin text-indigo-400 mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4 rounded-2xl bg-red-50 border border-red-100 text-red-600 text-sm text-center"
          >
            Backend unreachable: {error}
          </motion.div>
        )}

        {health && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-5"
          >
            {/* Overall Status */}
            <div
              className={`p-6 rounded-2xl border text-center ${
                health.status === 'ok'
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-amber-50 border-amber-200'
              }`}
            >
              <div className="text-3xl mb-2">{health.status === 'ok' ? '✅' : '⚠️'}</div>
              <h2
                className={`text-xl font-bold ${
                  health.status === 'ok' ? 'text-emerald-700' : 'text-amber-700'
                }`}
              >
                {health.status === 'ok' ? 'All Systems Operational' : 'Degraded'}
              </h2>
              <p className="text-sm text-slate-500 mt-1">Version {health.version}</p>
            </div>

            {/* Service Checks */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 shadow-sm p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Services</h3>
              <div className="space-y-3">
                {Object.entries(health.checks).map(([service, ok]) => (
                  <div
                    key={service}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50"
                  >
                    <span className="text-sm text-slate-700 font-medium">
                      {service.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${
                        ok
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
                      {ok ? 'Healthy' : 'Down'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
