"use client";

import { useEffect, useState } from "react";

/**
 * Cinematic multi-layer landing backdrop.
 * GPU-friendly: transform + opacity only. Reduced layers on mobile.
 */
export function LandingBackdrop() {
  const [reduceMotion, setReduceMotion] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mqMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const mqMobile = window.matchMedia("(max-width: 768px)");
    const sync = () => {
      setReduceMotion(mqMotion.matches);
      setIsMobile(mqMobile.matches);
    };
    sync();
    mqMotion.addEventListener("change", sync);
    mqMobile.addEventListener("change", sync);
    return () => {
      mqMotion.removeEventListener("change", sync);
      mqMobile.removeEventListener("change", sync);
    };
  }, []);

  const animate = !reduceMotion;

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-void"
    >
      {/* Layer 1 — deep gradient atmosphere */}
      <div className="absolute inset-0 bg-atmosphere" />
      <div className="absolute inset-0 bg-vignette" />

      {/* Layer 2 — large blurred orbs */}
      <div
        className={`orb orb-a ${animate ? "orb-drift-a" : ""}`}
        style={{ opacity: isMobile ? 0.35 : 0.55 }}
      />
      <div
        className={`orb orb-b ${animate ? "orb-drift-b" : ""}`}
        style={{ opacity: isMobile ? 0.25 : 0.45 }}
      />
      {!isMobile && (
        <div className={`orb orb-c ${animate ? "orb-drift-c" : ""}`} />
      )}

      {/* Layer 3 — perspective infinite floor grid */}
      <div className="absolute inset-0 flex items-end justify-center perspective-floor">
        <div
          className={`floor-grid ${animate ? "floor-scroll" : ""}`}
          style={{ opacity: isMobile ? 0.22 : 0.35 }}
        />
        <div className="floor-fade" />
      </div>

      {/* Layer 4 — network graph (SVG) */}
      {!isMobile && (
        <svg
          className={`absolute inset-0 h-full w-full ${animate ? "network-breathe" : ""}`}
          viewBox="0 0 1440 900"
          preserveAspectRatio="xMidYMid slice"
          style={{ opacity: 0.45 }}
        >
          <defs>
            <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0D9488" stopOpacity="0" />
              <stop offset="50%" stopColor="#0D9488" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#0284C7" stopOpacity="0" />
            </linearGradient>
            <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2.5" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* crawl edges */}
          <g stroke="url(#edgeGrad)" strokeWidth="1" fill="none">
            <path d="M180 220 L340 310 L520 250 L710 340 L900 280 L1080 360 L1260 290" className={animate ? "edge-dash" : ""} />
            <path d="M220 520 L400 440 L580 510 L760 430 L940 500 L1120 420 L1300 490" className={animate ? "edge-dash-slow" : ""} />
            <path d="M340 310 L400 440 M520 250 L580 510 M710 340 L760 430 M900 280 L940 500" opacity="0.35" />
            <path d="M520 250 L710 180 L900 220 L1080 160" opacity="0.4" className={animate ? "edge-dash" : ""} />
          </g>

          {/* nodes */}
          <g filter="url(#softGlow)">
            {[
              [180, 220], [340, 310], [520, 250], [710, 340], [900, 280],
              [1080, 360], [1260, 290], [220, 520], [400, 440], [580, 510],
              [760, 430], [940, 500], [1120, 420], [1300, 490], [710, 180],
              [900, 220], [1080, 160],
            ].map(([x, y], i) => (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={i % 4 === 0 ? 3.2 : 2.2}
                fill={i % 3 === 0 ? "#5EEAD4" : "#0D9488"}
                className={animate ? "node-pulse" : ""}
                style={{ animationDelay: `${(i % 7) * 0.35}s` }}
                opacity={0.75}
              />
            ))}
          </g>

          {/* packet travelers along paths */}
          {animate && (
            <g>
              <circle r="2.5" fill="#0D9488" filter="url(#softGlow)">
                <animateMotion dur="9s" repeatCount="indefinite" path="M180 220 L340 310 L520 250 L710 340 L900 280 L1080 360 L1260 290" />
              </circle>
              <circle r="2" fill="#0284C7" filter="url(#softGlow)">
                <animateMotion dur="12s" repeatCount="indefinite" path="M220 520 L400 440 L580 510 L760 430 L940 500 L1120 420 L1300 490" />
              </circle>
              <circle r="2.2" fill="#14B8A6" filter="url(#softGlow)">
                <animateMotion dur="8s" repeatCount="indefinite" path="M520 250 L710 180 L900 220 L1080 160" />
              </circle>
            </g>
          )}
        </svg>
      )}

      {/* Layer 5 — data particles along arcs */}
      {animate && !isMobile && (
        <div className="absolute inset-0">
          {PARTICLE_PATHS.map((p, i) => (
            <span
              key={i}
              className="data-particle"
              style={{
                left: p.x,
                top: p.y,
                animationDuration: p.dur,
                animationDelay: p.delay,
                ["--dx" as string]: p.dx,
                ["--dy" as string]: p.dy,
              }}
            />
          ))}
        </div>
      )}

      {/* Layer 6 — soft light rays */}
      {!isMobile && (
        <div className={`light-rays ${animate ? "rays-sweep" : ""}`} />
      )}

      {/* Subtle symbolic glyphs — JSON, hex, binary (very low opacity) */}
      {!isMobile && (
        <div className="glyph-layer">
          <span className="glyph g1">{`{ }`}</span>
          <span className="glyph g2">GET /api</span>
          <span className="glyph g3">01001</span>
          <span className="glyph g4">[data]</span>
          <span className="glyph g5">⟨node⟩</span>
          <span className="glyph g6">→ JSON</span>
        </div>
      )}

      {/* Top haze so content stays readable */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/50 via-transparent to-void/90" />
    </div>
  );
}

const PARTICLE_PATHS = [
  { x: "12%", y: "28%", dx: "40vw", dy: "18vh", dur: "14s", delay: "0s" },
  { x: "78%", y: "22%", dx: "-35vw", dy: "25vh", dur: "16s", delay: "2s" },
  { x: "25%", y: "62%", dx: "30vw", dy: "-20vh", dur: "13s", delay: "1s" },
  { x: "65%", y: "70%", dx: "-28vw", dy: "-15vh", dur: "15s", delay: "3.5s" },
  { x: "45%", y: "18%", dx: "20vw", dy: "35vh", dur: "18s", delay: "0.8s" },
  { x: "88%", y: "55%", dx: "-45vw", dy: "10vh", dur: "17s", delay: "4s" },
];
