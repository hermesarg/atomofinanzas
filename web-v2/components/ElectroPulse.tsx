"use client";

import type { ElectroBand } from "@/lib/types";

type ElectroPulseProps = {
  state?: ElectroBand;
  liquidity?: string;
  solvency?: string;
  flow?: string;
  large?: boolean;
};

const PATHS: Record<ElectroBand, string> = {
  "muy-firme":
    "M0 62 L88 62 L103 60 L112 66 L120 50 L128 82 L137 27 L148 96 L160 54 L174 64 L190 62 L276 62 L291 60 L300 66 L308 50 L316 82 L325 27 L336 96 L348 54 L362 64 L378 62 L464 62 L479 60 L488 66 L496 50 L504 82 L513 27 L524 96 L536 54 L550 64 L566 62 L652 62 L667 60 L676 66 L684 50 L692 82 L701 27 L712 96 L724 54 L738 64 L760 62",
  firme:
    "M0 62 L62 62 L78 58 L88 70 L98 46 L109 84 L119 31 L131 94 L144 52 L160 66 L176 62 L218 62 L234 58 L244 70 L254 46 L265 84 L275 31 L287 94 L300 52 L316 66 L332 62 L374 62 L390 58 L400 70 L410 46 L421 84 L431 31 L443 94 L456 52 L472 66 L488 62 L530 62 L546 58 L556 70 L566 46 L577 84 L587 31 L599 94 L612 52 L628 66 L644 62 L686 62 L702 58 L712 70 L722 46 L733 84 L743 33 L754 90 L760 62",
  estable:
    "M0 62 L48 62 L66 56 L78 77 L90 36 L103 88 L118 54 L134 69 L176 62 L196 54 L208 79 L220 32 L234 92 L250 52 L268 71 L310 62 L330 53 L342 80 L354 30 L368 94 L384 50 L402 72 L444 62 L464 54 L476 78 L488 34 L502 91 L518 52 L536 70 L578 62 L598 53 L610 81 L622 31 L636 93 L652 51 L670 72 L712 62 L732 55 L744 78 L756 42 L760 62",
  vigilar:
    "M0 62 L36 64 L54 48 L68 83 L81 26 L95 99 L111 42 L128 77 L146 54 L162 74 L178 45 L193 90 L208 18 L223 106 L240 37 L257 82 L278 55 L295 72 L311 42 L326 94 L341 15 L356 109 L373 34 L390 85 L412 56 L429 75 L445 40 L460 96 L475 14 L490 110 L507 33 L524 86 L546 57 L563 73 L579 43 L594 93 L609 19 L624 105 L641 38 L658 82 L680 56 L697 75 L713 39 L728 95 L743 24 L760 62",
  ajustado:
    "M0 62 L22 66 L38 31 L50 105 L62 7 L74 116 L87 24 L100 96 L114 39 L128 88 L141 17 L154 111 L167 5 L180 115 L194 22 L208 99 L222 34 L236 91 L249 13 L262 113 L275 4 L288 116 L302 20 L316 101 L330 32 L344 94 L357 10 L370 114 L383 4 L396 116 L410 18 L424 104 L438 29 L452 96 L465 9 L478 115 L491 4 L504 116 L518 19 L532 102 L546 31 L560 93 L573 12 L586 113 L599 5 L612 116 L626 21 L640 100 L654 35 L668 90 L681 16 L694 111 L707 7 L720 115 L734 25 L747 97 L760 62"
};

const DURATIONS: Record<ElectroBand, number> = {
  "muy-firme": 5.8,
  firme: 4.9,
  estable: 4.0,
  vigilar: 3.1,
  ajustado: 2.35
};

const LABELS: Record<ElectroBand, string> = {
  "muy-firme": "Muy firme",
  firme: "Firme",
  estable: "Estable",
  vigilar: "A vigilar",
  ajustado: "Ajustado"
};

export default function ElectroPulse({
  state = "firme",
  liquidity = "Firme",
  solvency = "Muy firme",
  flow = "Estable",
  large = false
}: ElectroPulseProps) {
  const path = PATHS[state];
  const pulseId = "pulsePath-" + state;
  const duration = DURATIONS[state];
  const glowId = "softGlow-" + state;

  return (
    <section className={"electro-panel " + (large ? "electro-large" : "")} aria-label={"Electro financiero: " + LABELS[state]}>
      <div className="section-heading compact">
        <div>
          <span className="eyebrow">ELECTRO FINANCIERO</span>
          <h2>{LABELS[state]}</h2>
        </div>
        <span className={"health-dot " + state} />
      </div>

      <div className="electro-stage">
        <svg viewBox="0 0 760 120" preserveAspectRatio="none" role="img" aria-label={"Señal " + LABELS[state]}>
          <defs>
            <filter id={glowId} x="-20%" y="-50%" width="140%" height="200%">
              <feGaussianBlur stdDeviation="1.2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
          <line x1="0" y1="62" x2="760" y2="62" className="electro-baseline" />
          <path d={path} className="electro-shadow" pathLength="1" filter={"url(#" + glowId + ")"} />
          <path id={pulseId} d={path} className="electro-line" pathLength="1" />
          <path d={path} className="electro-trail" pathLength="1" strokeDasharray=".18 .82" strokeDashoffset="1">
            <animate attributeName="stroke-dashoffset" from="1" to="0" dur={duration + "s"} repeatCount="indefinite" />
          </path>
          <g className="particles">
            <circle r="4.4" className="particle p1">
              <animateMotion dur={duration + "s"} repeatCount="indefinite" rotate="auto">
                <mpath href={"#" + pulseId} />
              </animateMotion>
            </circle>
          </g>
        </svg>
        <div className="scan-light" />
      </div>

      <p className="electro-copy">
        La señal se dibuja de izquierda a derecha. Una estructura firme mantiene un pulso marcado pero regular;
        cuando aumenta la tensión, crecen los saltos y cambia el ritmo.
      </p>

      <div className="health-grid">
        <div><span>Liquidez</span><strong>{liquidity}</strong></div>
        <div><span>Solvencia</span><strong>{solvency}</strong></div>
        <div><span>Flujo</span><strong>{flow}</strong></div>
      </div>
    </section>
  );
}
