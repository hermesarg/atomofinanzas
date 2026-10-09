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
    "M0 62 L44 62 L62 58 L73 69 L84 48 L95 76 L107 58 L120 64 L158 62 L177 55 L188 72 L199 45 L211 79 L223 57 L238 64 L278 62 L296 54 L307 73 L319 43 L331 81 L343 56 L357 64 L401 62 L418 56 L430 71 L442 46 L454 78 L466 58 L480 64 L526 62 L544 55 L556 73 L568 44 L580 80 L592 57 L606 64 L650 62 L669 56 L681 71 L693 47 L705 78 L718 59 L734 63 L760 62",
  firme:
    "M0 62 L38 62 L57 53 L69 77 L81 36 L94 88 L108 50 L122 69 L155 62 L174 50 L187 80 L199 31 L212 92 L226 47 L242 70 L280 62 L299 49 L312 82 L325 29 L338 94 L352 45 L369 72 L407 62 L426 51 L439 79 L452 33 L465 91 L479 48 L496 70 L534 62 L553 50 L566 83 L579 30 L592 93 L606 46 L623 71 L660 62 L680 52 L693 78 L706 35 L719 89 L733 50 L746 66 L760 62",
  estable:
    "M0 62 L34 63 L52 47 L67 85 L80 25 L94 101 L110 42 L126 78 L145 54 L160 74 L176 49 L191 87 L205 20 L220 105 L237 39 L252 80 L275 55 L292 72 L308 45 L323 91 L338 18 L353 107 L370 37 L387 83 L412 56 L429 75 L445 43 L460 93 L475 16 L490 109 L507 35 L524 84 L548 57 L565 73 L581 46 L596 90 L611 21 L626 104 L643 40 L660 81 L684 56 L701 75 L717 42 L732 92 L746 35 L760 62",
  vigilar:
    "M0 62 L28 65 L45 42 L59 92 L72 14 L86 112 L101 35 L117 84 L133 51 L149 78 L165 30 L181 99 L195 9 L210 114 L227 29 L244 88 L260 47 L276 80 L292 25 L308 103 L323 8 L338 114 L355 26 L372 91 L389 45 L405 82 L421 24 L437 105 L452 7 L468 115 L485 25 L502 93 L519 43 L536 84 L552 22 L568 107 L583 6 L599 115 L616 24 L633 94 L650 42 L667 86 L683 21 L699 108 L714 8 L730 113 L746 31 L760 62",
  ajustado:
    "M0 62 L22 66 L38 31 L50 105 L62 7 L74 116 L87 24 L100 96 L114 39 L128 88 L141 17 L154 111 L167 5 L180 115 L194 22 L208 99 L222 34 L236 91 L249 13 L262 113 L275 4 L288 116 L302 20 L316 101 L330 32 L344 94 L357 10 L370 114 L383 4 L396 116 L410 18 L424 104 L438 29 L452 96 L465 9 L478 115 L491 4 L504 116 L518 19 L532 102 L546 31 L560 93 L573 12 L586 113 L599 5 L612 116 L626 21 L640 100 L654 35 L668 90 L681 16 L694 111 L707 7 L720 115 L734 25 L747 97 L760 62"
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
  const gradientId = "pulseGradient-" + state;
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
            <linearGradient id={gradientId} x1="0" x2="1">
              <stop offset="0%" stopColor="#c85c0b" />
              <stop offset="48%" stopColor="#e67818" />
              <stop offset="100%" stopColor="#b84d08" />
            </linearGradient>
            <filter id={glowId} x="-20%" y="-50%" width="140%" height="200%">
              <feGaussianBlur stdDeviation="2.2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
          <line x1="0" y1="62" x2="760" y2="62" className="electro-baseline" />
          <path d={path} className="electro-glow" pathLength="1" filter={"url(#" + glowId + ")"} />
          <path id={pulseId} d={path} className="electro-line" pathLength="1" stroke={"url(#" + gradientId + ")"} />
          <g className="particles">
            <circle r="4.2" className="particle p1">
              <animateMotion dur="3.15s" repeatCount="indefinite" rotate="auto">
                <mpath href={"#" + pulseId} />
              </animateMotion>
            </circle>
            <circle r="3" className="particle p2">
              <animateMotion dur="3.15s" begin="-1.05s" repeatCount="indefinite" rotate="auto">
                <mpath href={"#" + pulseId} />
              </animateMotion>
            </circle>
            <circle r="2.1" className="particle p3">
              <animateMotion dur="3.15s" begin="-2.1s" repeatCount="indefinite" rotate="auto">
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
