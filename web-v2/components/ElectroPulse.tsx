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
    "M0 62 L36 62 C44 62 49 55 56 52 C63 49 70 54 76 62 L94 62 L102 62 L108 70 L114 18 L120 95 L127 62 L145 62 C154 62 160 48 173 44 C186 40 198 48 205 62 L242 62 " +
    "L278 62 C286 62 291 55 298 52 C305 49 312 54 318 62 L336 62 L344 62 L350 70 L356 18 L362 95 L369 62 L387 62 C396 62 402 48 415 44 C428 40 440 48 447 62 L484 62 " +
    "L520 62 C528 62 533 55 540 52 C547 49 554 54 560 62 L578 62 L586 62 L592 70 L598 18 L604 95 L611 62 L629 62 C638 62 644 48 657 44 C670 40 682 48 689 62 L726 62 L760 62",
  "firme":
    "M0 62 L28 62 C36 62 41 54 48 51 C55 48 62 54 68 62 L83 62 L91 62 L97 71 L103 16 L109 97 L116 62 L132 62 C141 62 147 47 160 43 C173 39 185 48 192 62 L222 62 " +
    "L250 62 C258 62 263 54 270 51 C277 48 284 54 290 62 L305 62 L313 62 L319 71 L325 16 L331 97 L338 62 L354 62 C363 62 369 47 382 43 C395 39 407 48 414 62 L444 62 " +
    "L472 62 C480 62 485 54 492 51 C499 48 506 54 512 62 L527 62 L535 62 L541 71 L547 16 L553 97 L560 62 L576 62 C585 62 591 47 604 43 C617 39 629 48 636 62 L666 62 " +
    "L694 62 C702 62 707 54 714 51 C721 48 728 54 734 62 L746 62 L752 72 L760 48",
  "estable":
    "M0 62 L22 62 C30 62 35 53 42 50 C49 47 56 54 62 62 L74 62 L82 62 L88 73 L94 14 L100 99 L107 62 L121 62 C130 62 136 46 149 42 C162 38 174 49 181 62 L204 62 " +
    "L225 62 C233 62 238 52 245 49 C252 46 259 54 265 62 L277 62 L285 62 L291 75 L297 12 L303 101 L310 62 L324 62 C333 62 339 44 352 40 C365 36 377 49 384 62 L407 62 " +
    "L428 62 C436 62 441 54 448 51 C455 48 462 55 468 62 L480 62 L488 62 L494 74 L500 13 L506 100 L513 62 L527 62 C536 62 542 45 555 41 C568 37 580 49 587 62 L610 62 " +
    "L631 62 C639 62 644 52 651 49 C658 46 665 54 671 62 L683 62 L691 62 L697 76 L703 11 L709 102 L716 62 L730 62 C739 62 745 45 758 41 L760 62",
  "vigilar":
    "M0 62 L24 63 C31 62 36 50 44 48 C52 46 59 54 65 63 L74 62 L82 63 L88 80 L94 10 L101 108 L109 58 L123 66 C132 66 138 40 151 36 C164 32 176 52 183 64 L200 62 " +
    "L222 64 C229 63 234 51 242 49 C250 47 257 55 263 64 L272 61 L280 63 L286 84 L292 7 L299 111 L307 55 L321 68 C330 67 336 36 349 33 C362 30 374 54 381 65 L398 61 " +
    "L420 63 C427 62 432 53 440 50 C448 48 455 56 461 64 L470 61 L478 64 L484 82 L490 9 L497 109 L505 57 L519 67 C528 66 534 39 547 35 C560 32 572 52 579 64 L596 62 " +
    "L618 65 C625 64 630 49 638 47 C646 45 653 56 659 64 L668 60 L676 64 L682 88 L688 5 L695 114 L703 52 L717 70 C726 69 732 34 745 31 C752 29 756 42 760 58",
  "ajustado":
    "M0 62 L16 67 C22 65 27 45 35 42 C43 39 50 56 56 67 L64 58 L72 68 L78 94 L84 5 L91 116 L100 49 L112 74 C121 72 126 32 139 28 C152 24 164 59 171 68 L186 57 " +
    "L201 69 C208 67 213 43 221 40 C229 37 236 58 242 69 L250 55 L258 70 L264 100 L270 3 L277 117 L286 46 L298 76 C307 74 312 29 325 25 C338 21 350 61 357 70 L372 56 " +
    "L387 68 C394 66 399 45 407 41 C415 38 422 59 428 68 L436 54 L444 71 L450 97 L456 4 L463 116 L472 48 L484 75 C493 73 498 31 511 27 C524 23 536 60 543 69 L558 57 " +
    "L573 70 C580 68 585 42 593 39 C601 36 608 59 614 70 L622 53 L630 72 L636 102 L642 3 L649 118 L658 44 L670 78 C679 76 684 27 697 23 C710 20 722 63 729 71 L744 55 L760 73"
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
