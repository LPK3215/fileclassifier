export const THEME_STORAGE_KEY = "fileclassifier.theme";
export const DEFAULT_EXCEL_DIR = "";
export const DEFAULT_INPUT_DIR = "";
export const DEFAULT_OUTPUT_DIR = "";
export const MIN_LEFT_RATIO = 28;
export const MAX_LEFT_RATIO = 72;
export const MIN_COLUMN_WIDTH = 120;
export const MAX_COLUMN_WIDTH = 640;
export const MATCH_MODES = [
  { value: "exact", label: "精确" },
  { value: "contains", label: "包含" },
  { value: "fuzzy", label: "模糊" },
  { value: "range", label: "范围" }
];

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function compareCellValues(leftValue, rightValue) {
  const leftText = String(leftValue ?? "").trim();
  const rightText = String(rightValue ?? "").trim();

  const leftNumber = Number(leftText);
  const rightNumber = Number(rightText);
  const bothNumeric =
    Number.isFinite(leftNumber) &&
    Number.isFinite(rightNumber) &&
    leftText !== "" &&
    rightText !== "";

  if (bothNumeric) {
    return leftNumber - rightNumber;
  }

  return leftText.localeCompare(rightText, "zh-Hans-CN", { numeric: true, sensitivity: "base" });
}

export function getInitialTheme() {
  if (typeof window === "undefined") {
    return "light";
  }
  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function createCondition(seed = "") {
  const unique = `${Date.now()}_${Math.random().toString(16).slice(2)}_${seed}`;
  return {
    id: unique,
    field_name: "",
    match_mode: "contains",
    value: "",
    range_start: "",
    range_end: ""
  };
}
