"use client";

import {
  PointerEvent,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

type OrchestraViewportProps = {
  /** Intrinsic width of the diagram in px (must match SVG/layout width). */
  contentWidth: number;
  /** Intrinsic height of the diagram in px. */
  contentHeight: number;
  /** Hint shown in the corner. */
  hint?: string;
  children: ReactNode;
  className?: string;
};

/**
 * Scrollable + drag-to-pan canvas so wide orchestra trees stay fully reachable.
 */
export function OrchestraViewport({
  contentWidth,
  contentHeight,
  hint = "Drag to pan · scroll to explore",
  children,
  className = "",
}: OrchestraViewportProps) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{
    active: boolean;
    startX: number;
    startY: number;
    scrollLeft: number;
    scrollTop: number;
    pointerId: number;
  } | null>(null);
  const [grabbing, setGrabbing] = useState(false);

  // Center horizontally when content size changes (new workers appear)
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    const maxScroll = Math.max(0, contentWidth - el.clientWidth);
    if (maxScroll > 0 && el.scrollLeft === 0) {
      el.scrollLeft = Math.floor(maxScroll / 2);
    }
  }, [contentWidth]);

  const onPointerDown = useCallback((e: PointerEvent<HTMLDivElement>) => {
    // Only primary button / touch; ignore interactive controls inside
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    if (target.closest("a, button, input, textarea, select")) return;

    const el = scrollerRef.current;
    if (!el) return;
    el.setPointerCapture(e.pointerId);
    dragRef.current = {
      active: true,
      startX: e.clientX,
      startY: e.clientY,
      scrollLeft: el.scrollLeft,
      scrollTop: el.scrollTop,
      pointerId: e.pointerId,
    };
    setGrabbing(true);
  }, []);

  const onPointerMove = useCallback((e: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    const el = scrollerRef.current;
    if (!drag?.active || !el) return;
    const dx = e.clientX - drag.startX;
    const dy = e.clientY - drag.startY;
    el.scrollLeft = drag.scrollLeft - dx;
    el.scrollTop = drag.scrollTop - dy;
  }, []);

  const endDrag = useCallback((e: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    const el = scrollerRef.current;
    if (drag?.active && el) {
      try {
        el.releasePointerCapture(drag.pointerId);
      } catch {
        // already released
      }
    }
    dragRef.current = null;
    setGrabbing(false);
    void e;
  }, []);

  return (
    <div className={`relative ${className}`}>
      <div
        ref={scrollerRef}
        className={`orchestra-canvas orchestra-viewport ${
          grabbing ? "is-grabbing" : "is-grab"
        }`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        role="region"
        aria-label="Orchestra canvas — drag or scroll to explore"
      >
        <div
          className="orchestra-viewport-inner"
          style={{
            width: contentWidth,
            height: contentHeight,
            minWidth: contentWidth,
          }}
        >
          {children}
        </div>
      </div>
      <p className="pointer-events-none absolute bottom-3 right-3 rounded-md bg-white/90 px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-700 shadow-sm ring-1 ring-slate-200">
        {hint}
      </p>
    </div>
  );
}
