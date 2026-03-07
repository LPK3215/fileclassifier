import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

export default function FancySelect({
  value,
  onChange,
  options,
  placeholder,
  ariaLabel,
  disabled = false
}) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [menuStyle, setMenuStyle] = useState({});
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const selectedOption = useMemo(
    () => options.find((item) => item.value === value) || null,
    [options, value]
  );

  const selectByIndex = useCallback(
    (index) => {
      const selected = options[index];
      if (!selected) {
        return;
      }
      onChange(selected.value);
      setOpen(false);
      triggerRef.current?.focus();
    },
    [onChange, options]
  );

  const updateMenuPosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) {
      return;
    }
    const rect = trigger.getBoundingClientRect();
    const viewportGap = 8;
    const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 900;
    const maxHeight = Math.max(180, Math.min(320, viewportHeight - rect.bottom - viewportGap * 2));

    setMenuStyle({
      top: `${Math.max(viewportGap, rect.bottom + 6)}px`,
      left: `${Math.max(viewportGap, rect.left)}px`,
      width: `${Math.max(180, rect.width)}px`,
      maxHeight: `${maxHeight}px`
    });
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }
    const selectedIndex = options.findIndex((item) => item.value === value);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : options.length > 0 ? 0 : -1);
  }, [open, options, value]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    updateMenuPosition();

    const onPointerDown = (event) => {
      const target = event.target;
      if (rootRef.current?.contains(target) || menuRef.current?.contains(target)) {
        return;
      }
      setOpen(false);
    };

    const onViewportChange = () => {
      updateMenuPosition();
    };

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, updateMenuPosition]);

  useEffect(() => {
    if (disabled && open) {
      setOpen(false);
    }
  }, [disabled, open]);

  function handleTriggerKeyDown(event) {
    if (disabled) {
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      if (!options.length) {
        return;
      }
      const step = event.key === "ArrowDown" ? 1 : -1;
      setActiveIndex((prev) => {
        const start = prev < 0 ? (step > 0 ? -1 : 0) : prev;
        return (start + step + options.length) % options.length;
      });
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      if (activeIndex >= 0) {
        selectByIndex(activeIndex);
      }
    }
  }

  const menuNode =
    open && typeof document !== "undefined"
      ? createPortal(
          <ul
            ref={menuRef}
            className="custom-select-menu is-portal"
            style={menuStyle}
            role="listbox"
            aria-label={ariaLabel}
          >
            {options.length ? (
              options.map((option, index) => (
                <li key={`${option.value}_${index}`} role="presentation">
                  <button
                    type="button"
                    className={`custom-select-option${option.value === value ? " is-selected" : ""}${
                      index === activeIndex ? " is-active" : ""
                    }`}
                    role="option"
                    aria-selected={option.value === value}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => selectByIndex(index)}
                  >
                    {option.label}
                  </button>
                </li>
              ))
            ) : (
              <li className="custom-select-empty">暂无可选项</li>
            )}
          </ul>,
          document.body
        )
      : null;

  return (
    <div className={open ? "custom-select is-open" : "custom-select"} ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="custom-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => {
          if (!disabled) {
            setOpen((prev) => !prev);
          }
        }}
        onKeyDown={handleTriggerKeyDown}
        disabled={disabled}
      >
        <span className={selectedOption ? "custom-select-value" : "custom-select-value is-placeholder"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span className="custom-select-chevron" aria-hidden="true" />
      </button>
      {menuNode}
    </div>
  );
}
