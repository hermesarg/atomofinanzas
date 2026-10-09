"use client";

import { useEffect, useRef, useState } from "react";

const ars = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 0
});

export default function AnimatedMoney({
  value,
  className = "",
  duration = 520,
  prefix = ""
}: {
  value: number;
  className?: string;
  duration?: number;
  prefix?: string;
}) {
  const previous = useRef(value);
  const [shown, setShown] = useState(value);

  useEffect(() => {
    const from = previous.current;
    const to = value;
    if (from === to) return;

    let frame = 0;
    const start = performance.now();

    const step = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(from + (to - from) * eased);
      if (p < 1) frame = requestAnimationFrame(step);
      else previous.current = to;
    };

    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return <span className={className}>{prefix}{ars.format(shown)}</span>;
}
