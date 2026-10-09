"use client";

type ElectroPulseProps = {
  state?: "muy-firme" | "firme" | "estable" | "vigilar" | "ajustado";
};

const PATHS: Record<NonNullable<ElectroPulseProps["state"]>, string> = {
  "muy-firme": "M0 62 L70 62 L86 60 L96 64 L106 61 L116 62 L150 62 L168 59 L178 65 L188 61 L198 62 L240 62 L256 60 L266 64 L276 61 L286 62 L340 62 L356 60 L366 64 L376 61 L386 62 L450 62 L466 60 L476 64 L486 61 L496 62 L560 62 L576 60 L586 64 L596 61 L606 62 L680 62 L760 62",
  firme: "M0 62 L60 62 L82 59 L94 67 L106 55 L116 70 L128 61 L170 62 L190 57 L202 69 L214 51 L226 73 L238 61 L286 62 L304 56 L316 69 L328 50 L340 74 L352 61 L402 62 L420 57 L432 68 L444 53 L456 71 L468 61 L520 62 L540 58 L552 67 L564 54 L576 70 L588 61 L760 62",
  estable: "M0 62 L52 62 L74 56 L88 70 L102 45 L116 78 L132 60 L164 62 L184 54 L198 72 L212 41 L226 82 L242 60 L284 62 L304 53 L318 73 L332 38 L348 84 L364 59 L408 62 L428 55 L442 71 L456 43 L470 79 L486 60 L530 62 L550 54 L564 74 L578 40 L594 83 L610 59 L760 62",
  vigilar: "M0 62 L44 63 L66 50 L82 78 L96 31 L110 91 L128 55 L144 68 L166 58 L184 76 L198 24 L214 94 L232 52 L250 67 L282 62 L300 45 L318 82 L334 29 L350 92 L368 49 L386 70 L422 61 L440 48 L456 80 L472 26 L488 95 L506 50 L524 71 L560 62 L578 44 L594 84 L610 32 L626 90 L644 54 L662 67 L760 62",
  ajustado: "M0 62 L34 64 L52 43 L68 86 L82 18 L96 99 L112 47 L126 75 L144 54 L160 82 L174 12 L190 101 L208 39 L224 79 L242 50 L258 88 L274 22 L290 96 L308 42 L326 76 L348 61 L366 37 L382 91 L398 16 L414 101 L432 38 L448 83 L466 51 L482 89 L498 20 L514 98 L532 43 L548 78 L568 55 L586 85 L602 25 L618 96 L636 44 L654 78 L676 56 L694 83 L712 36 L730 88 L760 62"
};

const LABELS = {
  "muy-firme": "Muy firme",
  firme: "Firme",
  estable: "Estable",
  vigilar: "A vigilar",
  ajustado: "Ajustado"
};

export default function ElectroPulse({ state = "firme" }: ElectroPulseProps) {
  const path = PATHS[state];

  return (
    <section className="electro-panel" aria-label={"Electro financiero: " + LABELS[state]}>
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">ELECTRO FINANCIERO</span>
          <h2>{LABELS[state]}</h2>
        </div>
        <span className={"health-dot " + state} />
      </div>

      <div className="electro-stage">
        <svg viewBox="0 0 760 120" preserveAspectRatio="none" role="img">
          <defs>
            <linearGradient id="pulseGradient" x1="0" x2="1">
              <stop offset="0%" stopColor="#ff7b24" />
              <stop offset="50%" stopColor="#ff9f45" />
              <stop offset="100%" stopColor="#ffd09a" />
            </linearGradient>
            <filter id="softGlow" x="-20%" y="-40%" width="140%" height="180%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
          <line x1="0" y1="62" x2="760" y2="62" className="electro-baseline" />
          <path d={path} className="electro-glow" pathLength="1" />
          <path id="pulsePath" d={path} className="electro-line" pathLength="1" />
          <g className="particles">
            <circle r="2.6" className="particle p1">
              <animateMotion dur="3.2s" repeatCount="indefinite" rotate="auto">
                <mpath href="#pulsePath" />
              </animateMotion>
            </circle>
            <circle r="1.8" className="particle p2">
              <animateMotion dur="3.2s" begin="-1.05s" repeatCount="indefinite" rotate="auto">
                <mpath href="#pulsePath" />
              </animateMotion>
            </circle>
            <circle r="1.25" className="particle p3">
              <animateMotion dur="3.2s" begin="-2.1s" repeatCount="indefinite" rotate="auto">
                <mpath href="#pulsePath" />
              </animateMotion>
            </circle>
          </g>
        </svg>
        <div className="scan-light" />
      </div>

      <p className="electro-copy">
        La señal aparece de izquierda a derecha. Cuanto más firme está tu estructura,
        más pareja y contenida se ve.
      </p>

      <div className="health-grid">
        <div><span>Liquidez</span><strong>Firme</strong></div>
        <div><span>Solvencia</span><strong>Muy firme</strong></div>
        <div><span>Flujo</span><strong>Estable</strong></div>
      </div>
    </section>
  );
}
