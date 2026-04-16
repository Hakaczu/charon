"use client";

import { useMemo } from "react";
import type { CorrelationMatrix } from "@/types/api";

interface Props {
  data: CorrelationMatrix;
  height?: number;
}

function interpolateColor(value: number): string {
  // -1 = red (#ef4444), 0 = white (#f8fafc), 1 = blue (#3b82f6)
  const clamp = Math.max(-1, Math.min(1, value));
  if (clamp < 0) {
    const t = clamp + 1; // 0→red, 1→white
    const r = Math.round(239 + (248 - 239) * t);
    const g = Math.round(68 + (250 - 68) * t);
    const b = Math.round(68 + (252 - 68) * t);
    return `rgb(${r},${g},${b})`;
  } else {
    const t = clamp; // 0→white, 1→blue
    const r = Math.round(248 - (248 - 59) * t);
    const g = Math.round(250 - (250 - 130) * t);
    const b = Math.round(252 - (252 - 246) * t);
    return `rgb(${r},${g},${b})`;
  }
}

function textColor(value: number): string {
  // Dark text on light cells (near 0), light text on saturated cells
  return Math.abs(value) > 0.5 ? "#0f172a" : "hsl(var(--foreground))";
}

export function CorrelationHeatmap({ data, height = 500 }: Props) {
  const { assets, matrix } = useMemo(() => {
    const assets = Object.keys(data);
    const matrix = assets.map((row) =>
      assets.map((col) => parseFloat((data[row]?.[col] ?? 0).toFixed(2)))
    );
    return { assets, matrix };
  }, [data]);

  const cellSize = Math.min(56, Math.floor((height - 48) / Math.max(assets.length, 1)));

  return (
    <div style={{ overflowX: "auto" }}>
      <div
        style={{
          display: "inline-grid",
          gridTemplateColumns: `48px repeat(${assets.length}, ${cellSize}px)`,
          gridTemplateRows: `24px repeat(${assets.length}, ${cellSize}px)`,
          gap: 1,
        }}
      >
        {/* Top-left empty corner */}
        <div />
        {/* Column headers */}
        {assets.map((a) => (
          <div
            key={`col-${a}`}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              fontWeight: 600,
              color: "hsl(var(--muted-foreground))",
            }}
          >
            {a}
          </div>
        ))}
        {/* Rows */}
        {assets.map((rowAsset, ri) => (
          <>
            {/* Row header */}
            <div
              key={`row-${rowAsset}`}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                paddingRight: 6,
                fontSize: 10,
                fontWeight: 600,
                color: "hsl(var(--muted-foreground))",
              }}
            >
              {rowAsset}
            </div>
            {/* Cells */}
            {assets.map((colAsset, ci) => {
              const val = matrix[ri][ci];
              const bg = interpolateColor(val);
              const fg = textColor(val);
              return (
                <div
                  key={`${rowAsset}-${colAsset}`}
                  title={`${rowAsset} / ${colAsset}: ${val}`}
                  style={{
                    background: bg,
                    color: fg,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 9,
                    fontWeight: 500,
                    borderRadius: 2,
                    cursor: "default",
                    transition: "opacity 0.15s",
                  }}
                >
                  {val.toFixed(2)}
                </div>
              );
            })}
          </>
        ))}
      </div>
      {/* Legend */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginTop: 12,
          paddingLeft: 48,
          fontSize: 9,
          color: "hsl(var(--muted-foreground))",
        }}
      >
        <span>-1</span>
        <div
          style={{
            flex: 1,
            height: 8,
            borderRadius: 4,
            background: "linear-gradient(to right, #ef4444, #f8fafc, #3b82f6)",
            maxWidth: 160,
          }}
        />
        <span>+1</span>
      </div>
    </div>
  );
}
