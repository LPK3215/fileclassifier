import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { MAX_LEFT_RATIO, MIN_LEFT_RATIO, clamp } from "../lib/ui-helpers";

export default function usePaneSplitter() {
  const [leftPaneRatio, setLeftPaneRatio] = useState(50);
  const [isResizing, setIsResizing] = useState(false);
  const splitRef = useRef(null);

  const handleDividerPointerDown = useCallback((event) => {
    if (event.button !== 0) {
      return;
    }
    if (window.matchMedia?.("(max-width: 1100px)").matches) {
      return;
    }
    event.preventDefault();
    setIsResizing(true);
  }, []);

  const handleDividerKeyDown = useCallback((event) => {
    let delta = 0;
    if (event.key === "ArrowLeft") {
      delta = -2;
    } else if (event.key === "ArrowRight") {
      delta = 2;
    }
    if (delta !== 0) {
      event.preventDefault();
      setLeftPaneRatio((prev) => clamp(prev + delta, MIN_LEFT_RATIO, MAX_LEFT_RATIO));
    }
  }, []);

  useEffect(() => {
    if (!isResizing) {
      return undefined;
    }

    const onPointerMove = (event) => {
      const root = splitRef.current;
      if (!root) {
        return;
      }
      const rect = root.getBoundingClientRect();
      if (rect.width <= 0) {
        return;
      }
      const ratio = ((event.clientX - rect.left) / rect.width) * 100;
      setLeftPaneRatio(clamp(Number(ratio.toFixed(2)), MIN_LEFT_RATIO, MAX_LEFT_RATIO));
    };

    const onPointerUp = () => {
      setIsResizing(false);
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    document.body.classList.add("dragging-splitter");

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      document.body.classList.remove("dragging-splitter");
    };
  }, [isResizing]);

  const leftPaneBasis = useMemo(
    () => `calc((100% - 10px) * ${(leftPaneRatio / 100).toFixed(4)})`,
    [leftPaneRatio]
  );
  const rightPaneBasis = useMemo(
    () => `calc((100% - 10px) * ${((100 - leftPaneRatio) / 100).toFixed(4)})`,
    [leftPaneRatio]
  );

  return {
    leftPaneRatio,
    isResizing,
    splitRef,
    handleDividerPointerDown,
    handleDividerKeyDown,
    leftPaneBasis,
    rightPaneBasis
  };
}
