import React, { useState, useEffect } from 'react';

export default function LandingPage({ onEnter }: { onEnter: () => void }) {
  const [stage, setStage] = useState('loading');

  useEffect(() => {
    const revealTimer = setTimeout(() => {
      setStage('revealing');
    }, 1200);

    const doneTimer = setTimeout(() => {
      setStage('done');
    }, 1900);

    return () => {
      clearTimeout(revealTimer);
      clearTimeout(doneTimer);
    };
  }, []);

  const letters = "KSHAYA".split('');
  
  const shutterClass = "absolute inset-0 z-50 bg-[#151718] flex items-center justify-center border-b-4 border-[#000] transition-transform duration-700 ease-in-out " + (stage === 'revealing' ? '-translate-y-full' : 'translate-y-0');

  const bgStyle = "radial-gradient(circle at center, transparent 30%, #151718 100%), repeating-linear-gradient(0deg, transparent, transparent 19px, rgba(124, 148, 115, 0.05) 19px, rgba(124, 148, 115, 0.05) 20px), repeating-linear-gradient(90deg, transparent, transparent 19px, rgba(124, 148, 115, 0.05) 19px, rgba(124, 148, 115, 0.05) 20px)";

  return (
    <div className="relative w-full min-h-screen overflow-hidden flex items-center justify-center bg-[#2C3033]">
      
      {/* Background Radar / Metal Grid */}
      <div 
        className="absolute inset-0 z-0"
        style={{ backgroundImage: bgStyle }}
      />

      <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 w-full">
        {/* Embossed Stamped Logo */}
        <h1 
          className="logo-font text-7xl md:text-9xl mb-6 font-black tracking-tight text-[#7C9473]"
          style={{
            textShadow: '-1px -1px 2px rgba(255,255,255,0.4), 2px 2px 6px rgba(0,0,0,0.9), 6px 6px 12px rgba(0,0,0,0.8)',
            filter: 'drop-shadow(0 0 15px rgba(124,148,115,0.8))'
          }}
        >
          KSHAYA
        </h1>
        
        {/* Subtitle & LED */}
        <div className="flex flex-col items-center mb-16">
          <p className="font-mono text-lg md:text-xl text-[#7C9473]  mb-6 text-center opacity-80">
            RECOVER WHAT MATTERS. DESTROY WHAT MUST DIE.
          </p>
          <div className="flex items-center space-x-3 bg-[#1A1C1E] px-5 py-2 rounded-sm border-[2px] border-[#0F1112] shadow-[inset_0_2px_6px_rgba(0,0,0,0.9)]">
            <div className="w-3.5 h-3.5 rounded-full bg-[#7C9473] shadow-[0_0_12px_#7C9473] animate-pulse"></div>
            <span className="font-mono text-[#7C9473] tracking-[0.2em] text-sm font-bold mt-1">STATUS: READY</span>
          </div>
        </div>

        {/* Heavy Mechanical Switch */}
        <button 
          onClick={onEnter}
          className="relative flex items-center justify-center px-12 py-5 bg-gradient-to-b from-[#EDE6D6] to-[#D9CFB8] rounded-sm border-[4px] border-[#A69B8A] transition-all duration-75 group active:translate-y-[10px]"
          style={{
            boxShadow: '0 10px 0 #A69B8A, 0 15px 25px rgba(0,0,0,0.8), inset 0 2px 1px rgba(255,255,255,0.7)',
          }}
        >
          <span className="logo-font text-[#2E2B26] text-2xl md:text-3xl tracking-widest drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)]">
            ENTER PLATFORM
          </span>
        </button>
      </div>

      {/* Shutter / Loading Screen */}
      {stage !== 'done' && (
        <div 
          className={shutterClass}
          style={{ boxShadow: '0 15px 40px rgba(0,0,0,0.8)' }}
        >
          <div className="flex space-x-2">
            {letters.map((letter, i) => (
              <span 
                key={i} 
                className="logo-font text-5xl md:text-7xl text-[#7C9473] opacity-0 animate-letter-reveal"
                style={{ 
                  animationDelay: i * 0.15 + 's',
                  textShadow: '0 0 15px rgba(124,148,115,0.5)'
                }}
              >
                {letter}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
