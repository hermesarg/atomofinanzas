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
    "M0 62 L18 62 C23 62 26 56 31 53 C36 50 41 55 45 62 L56 62 L61 62 L65 70 L69 18 L73 95 L78 62 L90 62 C97 62 101 48 110 44 C119 40 127 48 132 62 L154 62 " +
    "L172 62 C177 62 180 56 185 53 C190 50 195 55 199 62 L210 62 L215 62 L219 70 L223 18 L227 95 L232 62 L244 62 C251 62 255 48 264 44 C273 40 281 48 286 62 L308 62 " +
    "L326 62 C331 62 334 56 339 53 C344 50 349 55 353 62 L364 62 L369 62 L373 70 L377 18 L381 95 L386 62 L398 62 C405 62 409 48 418 44 C427 40 435 48 440 62 L462 62 " +
    "L480 62 C485 62 488 56 493 53 C498 50 503 55 507 62 L518 62 L523 62 L527 70 L531 18 L535 95 L540 62 L552 62 C559 62 563 48 572 44 C581 40 589 48 594 62 L616 62 " +
    "L634 62 C639 62 642 56 647 53 C652 50 657 55 661 62 L672 62 L677 62 L681 70 L685 18 L689 95 L694 62 L706 62 C713 62 717 48 726 44 C735 40 743 48 748 62 L760 62",
  "firme":
    "M0 62 L15 62 C20 62 23 55 28 52 C33 49 38 55 42 62 L52 62 L57 62 L61 72 L65 16 L69 97 L74 62 L85 62 C92 62 96 47 105 43 C114 39 122 48 127 62 L148 62 " +
    "L164 62 C169 62 172 54 177 51 C182 48 187 55 191 62 L201 62 L206 62 L210 73 L214 15 L218 98 L223 62 L234 62 C241 62 245 46 254 42 C263 38 271 49 276 62 L297 62 " +
    "L313 62 C318 62 321 55 326 52 C331 49 336 55 340 62 L350 62 L355 62 L359 72 L363 16 L367 97 L372 62 L383 62 C390 62 394 47 403 43 C412 39 420 48 425 62 L446 62 " +
    "L462 62 C467 62 470 54 475 51 C480 48 485 55 489 62 L499 62 L504 62 L508 74 L512 14 L516 99 L521 62 L532 62 C539 62 543 46 552 42 C561 38 569 49 574 62 L595 62 " +
    "L611 62 C616 62 619 55 624 52 C629 49 634 55 638 62 L648 62 L653 62 L657 73 L661 15 L665 98 L670 62 L681 62 C688 62 692 47 701 43 C710 39 718 48 723 62 L744 62 L760 62",
  "estable":
    "M0 62 L12 62 C17 62 20 54 25 51 C30 48 35 55 39 62 L48 62 L53 62 L57 75 L61 13 L65 100 L70 62 L80 62 C87 62 91 45 100 41 C109 37 117 49 122 62 L142 62 " +
    "L158 62 C163 62 166 53 171 50 C176 47 181 55 185 62 L194 62 L199 62 L203 76 L207 12 L211 101 L216 62 L226 62 C233 62 237 44 246 40 C255 36 263 49 268 62 L288 62 " +
    "L304 62 C309 62 312 54 317 51 C322 48 327 55 331 62 L340 62 L345 62 L349 75 L353 13 L357 100 L362 62 L372 62 C379 62 383 45 392 41 C401 37 409 49 414 62 L434 62 " +
    "L450 62 C455 62 458 52 463 49 C468 46 473 55 477 62 L486 62 L491 62 L495 77 L499 11 L503 102 L508 62 L518 62 C525 62 529 43 538 39 C547 35 555 50 560 62 L580 62 " +
    "L596 62 C601 62 604 54 609 51 C614 48 619 55 623 62 L632 62 L637 62 L641 76 L645 12 L649 101 L654 62 L664 62 C671 62 675 45 684 41 C693 37 701 49 706 62 L726 62 L760 62",
  "vigilar":
    "M0 62 L11 63 C16 62 19 50 24 48 C29 46 34 55 38 63 L46 61 L51 63 L55 82 L59 9 L64 108 L69 57 L79 67 C86 67 90 39 99 35 C108 31 116 53 121 64 L139 62 " +
    "L153 64 C158 63 161 52 166 49 C171 46 176 56 180 64 L188 60 L193 64 L197 86 L201 7 L206 111 L211 55 L221 69 C228 68 232 35 241 32 C250 29 258 55 263 65 L281 61 " +
    "L295 63 C300 62 303 50 308 48 C313 45 318 57 322 64 L330 60 L335 65 L339 83 L343 9 L348 109 L353 57 L363 68 C370 67 374 38 383 34 C392 31 400 53 405 64 L423 62 " +
    "L437 65 C442 64 445 49 450 47 C455 44 460 57 464 65 L472 59 L477 65 L481 89 L485 5 L490 114 L495 52 L505 71 C512 70 516 33 525 30 C534 27 542 56 547 66 L565 61 " +
    "L579 64 C584 63 587 51 592 48 C597 45 602 57 606 65 L614 59 L619 65 L623 87 L627 6 L632 113 L637 53 L647 70 C654 69 658 34 667 31 C676 28 684 55 689 65 L707 62 L760 62",
  "ajustado":
    "M0 62 L9 67 C14 65 17 45 22 42 C27 39 32 57 36 67 L43 57 L49 68 L53 96 L57 4 L62 116 L68 48 L77 75 C84 73 88 31 97 27 C106 23 114 60 119 68 L134 56 " +
    "L148 69 C153 67 156 43 161 40 C166 37 171 59 175 69 L182 55 L188 70 L192 101 L196 3 L201 117 L207 45 L216 77 C223 75 227 28 236 24 C245 20 253 62 258 70 L273 55 " +
    "L287 68 C292 66 295 45 300 41 C305 38 310 60 314 68 L321 54 L327 71 L331 98 L335 4 L340 116 L346 47 L355 76 C362 74 366 30 375 26 C384 22 392 61 397 69 L412 56 " +
    "L426 70 C431 68 434 42 439 39 C444 36 449 60 453 70 L460 53 L466 72 L470 103 L474 3 L479 118 L485 43 L494 79 C501 77 505 26 514 22 C523 19 531 64 536 71 L551 54 " +
    "L565 69 C570 67 573 44 578 40 C583 37 588 60 592 69 L599 52 L605 73 L609 101 L613 3 L618 117 L624 44 L633 78 C640 76 644 27 653 23 C662 20 670 63 675 71 L690 55 L760 73"
};

const DURATIONS: Record<ElectroBand, number> = {
  "muy-firme": 7.2,
  firme: 6.3,
  estable: 5.2,
  vigilar: 4.0,
  ajustado: 3.0
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
  const waveformTransform = "translate(0 62) scale(1 0.76) translate(0 -62)";
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
          <path d={path} className="electro-shadow" pathLength="1" filter={"url(#" + glowId + ")"} transform={waveformTransform} />
          <path
            id={pulseId}
            d={path}
            className="electro-line electro-window"
            pathLength="1"
            strokeDasharray=".23 .77"
            strokeDashoffset="1"
            transform={waveformTransform}
          >
            <animate attributeName="stroke-dashoffset" from="1" to="0" dur={duration + "s"} repeatCount="indefinite" />
          </path>
          <path
            d={path}
            className="electro-trail"
            pathLength="1"
            strokeDasharray=".15 .85"
            strokeDashoffset="1"
            transform={waveformTransform}
          >
            <animate attributeName="stroke-dashoffset" from="1" to="0" dur={duration + "s"} repeatCount="indefinite" />
          </path>
          <circle r="2.2" className="particle particle-head">
            <animateMotion dur={duration + "s"} repeatCount="indefinite" rotate="auto">
              <mpath href={"#" + pulseId} />
            </animateMotion>
          </circle>
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
