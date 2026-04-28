'use client';

export default function WaveBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="wave-shine" />
      <div className="wave-glow wave-glow-1" />
      <div className="wave-glow wave-glow-2" />
    </div>
  );
}
