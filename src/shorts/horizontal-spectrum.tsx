import React from 'react';

export type SpectrumData = {
  fps: number;
  frames: number[][];
  threads: number[][];
  particles: number[][][];
  sourceSha256?: string;
};

// Offline PCM data + global frame clock; no live analyser, timers or random motion.
export const HorizontalSpectrum: React.FC<{data?: SpectrumData; second: number}> = ({data, second}) => {
  const index = Math.max(0, Math.min((data?.frames.length ?? 1)-1, Math.floor(second*(data?.fps ?? 60))));
  const values = data?.frames[index] ?? Array(64).fill(0);
  const inner = data?.threads[index] ?? Array(64).fill(0);
  const points = inner.map((value, i) => `${24+i*832/63},${110+value*28}`).join(' ');
  return <svg width="100%" height="230" viewBox="0 0 880 230" style={{overflow: 'visible'}} aria-label="Audio-reactive light spectrum">
    <defs>
      <linearGradient id="short-spectrum-gradient" gradientUnits="userSpaceOnUse" x1="0" x2="880" y1="0" y2="0">
        <stop offset="0" stopColor="#76FFC0"/><stop offset=".4" stopColor="#65EFE8"/>
        <stop offset=".72" stopColor="#80B9FF"/><stop offset="1" stopColor="#E0A4FF"/>
      </linearGradient>
      <filter id="short-spectrum-glow" x="-20%" y="-80%" width="140%" height="260%">
        <feGaussianBlur stdDeviation="3"/>
      </filter>
      <g id="short-spectrum-lights">
        {values.map((value, i) => <line key={i} x1={24+i*832/63} x2={24+i*832/63}
          y1={106} y2={106-(4+value*64)} strokeWidth={6} strokeLinecap="round"/>) }
        <polyline points={points} fill="none" strokeWidth={2}/>
        {inner.map((value, i) => <circle key={i} cx={24+i*832/63} cy={110+value*28} r={3}/>)}
        {(data?.particles[index] ?? []).map(([x, y, alpha, radius], i) =>
          <circle key={i} cx={24+x*832} cy={106+y} r={radius} opacity={alpha}/>)}
      </g>
    </defs>
    <g fill="url(#short-spectrum-gradient)" stroke="url(#short-spectrum-gradient)">
      <use href="#short-spectrum-lights" filter="url(#short-spectrum-glow)" opacity={.65}/>
      <use href="#short-spectrum-lights"/>
    </g>
  </svg>;
};
