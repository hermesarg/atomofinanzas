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
  // Healthy pattern: visible P wave, narrow QRS complex, short ST segment and rounded T wave.
  "muy-firme":
    "M0 62 L32 62 C40 62 45 55 52 53 C59 51 66 55 72 62 L90 62 L98 62 L104 72 L110 18 L116 94 L122 62 L142 62 C151 62 157 48 170 45 C183 42 195 49 202 62 L232 62 " +
    "L262 62 C270 62 275 55 282 53 C289 51 296 55 302 62 L320 62 L328 62 L334 72 L340 18 L346 94 L352 62 L372 62 C381 62 387 48 400 45 C413 42 425 49 432 62 L462 62 " +
    "L492 62 C500 62 505 55 512 53 C519 51 526 55 532 62 L550 62 L558 62 L564 72 L570 18 L576 94 L582 62 L602 62 C611 62 617 48 630 45 C643 42 655 49 662 62 L692 62 " +
    "L722 62 C730 62 735 55 742 53 C749 51 756 55 760 60",
  "firme":
    "M0 62 L26 62 C34 62 39 54 47 52 C55 50 63 55 69 62 L84 62 L93 62 L100 74 L107 16 L114 96 L121 62 L138 62 C148 62 154 47 168 43 C181 40 194 48 201 62 L222 62 " +
    "L248 62 C256 62 261 55 269 52 C277 49 285 55 291 62 L306 62 L315 62 L322 75 L329 14 L336 98 L343 62 L360 62 C370 62 376 46 390 42 C404 39 417 48 424 62 L446 62 " +
    "L472 62 C480 62 485 54 493 51 C501 49 509 55 515 62 L530 62 L539 62 L546 74 L553 15 L560 97 L567 62 L584 62 C594 62 600 47 614 43 C627 40 640 48 647 62 L669 62 " +
    "L695 62 C703 62 708 55 716 52 C724 50 732 55 738 62 L748 62 L754 72 L760 46",
  // Intermediate/tension states keep P-QRS-T hints but progressively lose regularity.
  estable:
    "M0 62 L22 62 C30 62 34 54 42 52 C50 49 58 55 64 62 L76 62 L85 62 L93 76 L101 14 L110 100 L119 62 L135 62 C145 62 151 46 165 42 C180 38 193 49 200 62 L218 62 " +
    "L238 62 C246 62 251 53 259 51 C267 48 275 55 281 62 L293 62 L302 62 L310 78 L318 11 L327 103 L336 62 L352 62 C362 62 368 44 382 40 C397 36 410 49 417 62 L435 62 " +
    "L454 62 C462 62 467 55 475 52 C483 49 491 55 497 62 L509 62 L518 62 L526 76 L534 14 L543 100 L552 62 L568 62 C578 62 584 46 598 42 C613 38 626 49 633 62 L651 62 " +
    "L670 62 C678 62 683 53 691 51 C699 48 707 55 713 62 L725 62 L734 62 L742 80 L750 8 L760 96",
  vigilar:
    "M0 62 L22 64 C30 63 35 50 44 48 C52 46 60 54 66 63 L76 62 L86 62 L94 82 L103 9 L112 108 L121 58 L137 66 C147 66 154 40 169 36 C184 33 196 52 204 64 L220 62 " +
    "L239 65 C247 64 252 49 261 47 C269 45 277 55 283 64 L293 61 L303 63 L311 86 L320 6 L329 111 L338 56 L354 68 C364 67 371 37 386 34 C401 31 413 54 421 65 L437 61 " +
    "L456 64 C464 63 469 51 478 48 C486 46 494 56 500 64 L510 61 L520 64 L528 84 L537 8 L546 109 L555 58 L571 67 C581 66 588 39 603 35 C618 32 630 52 638 64 L654 62 " +
    "L673 65 C681 64 686 49 695 47 C703 45 711 56 717 64 L727 60 L737 64 L745 89 L754 5 L760 104",
  ajustado:
    "M0 62 L18 66 C25 64 30 43 39 41 C47 39 55 55 61 66 L70 58 L80 66 L88 94 L97 4 L106 116 L116 52 L130 72 C140 70 146 32 161 28 C176 24 189 58 197 67 L212 58 " +
    "L228 68 C236 66 241 42 250 39 C258 37 266 57 272 68 L281 56 L291 69 L299 98 L308 3 L317 117 L327 49 L341 74 C351 72 357 29 372 25 C387 21 400 60 408 69 L423 57 " +
    "L439 67 C447 65 452 44 461 41 C469 38 477 58 483 67 L492 55 L502 70 L510 96 L519 4 L528 116 L538 51 L552 73 C562 71 568 31 583 27 C598 23 611 59 619 68 L634 58 " +
    "L650 69 C658 67 663 41 672 38 C680 36 688 58 694 69 L703 54 L713 71 L721 101 L730 3 L739 117 L749 48 L760 75"
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
        La señal se inspira en un ECG: onda P, complejo QRS y onda T. Cuando la estructura está firme,
        el ritmo se mantiene regular y espaciado; al aumentar la tensión, se vuelve más irregular.
      </p>

      <div className="health-grid">
        <div><span>Liquidez</span><strong>{liquidity}</strong></div>
        <div><span>Solvencia</span><strong>{solvency}</strong></div>
        <div><span>Flujo</span><strong>{flow}</strong></div>
      </div>
    </section>
  );
}
