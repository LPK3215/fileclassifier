import { useEffect, useState } from "react";

import { createCondition } from "../lib/ui-helpers";

function createEmptyRangeEditor() {
  return {
    open: false,
    conditionId: "",
    rangeStart: "",
    rangeEnd: ""
  };
}

export default function useConditionsState() {
  const [logic, setLogic] = useState("and");
  const [conditions, setConditions] = useState([createCondition("init")]);
  const [rangeEditor, setRangeEditor] = useState(createEmptyRangeEditor);

  function updateCondition(conditionId, patch) {
    setConditions((prev) =>
      prev.map((item) => {
        if (item.id !== conditionId) {
          return item;
        }
        return { ...item, ...patch };
      })
    );
  }

  function addCondition() {
    setConditions((prev) => [...prev, createCondition(String(prev.length + 1))]);
  }

  function removeCondition(conditionId) {
    setConditions((prev) => (prev.length === 1 ? prev : prev.filter((item) => item.id !== conditionId)));
  }

  function openRangeEditor(condition) {
    setRangeEditor({
      open: true,
      conditionId: condition.id,
      rangeStart: condition.range_start || "",
      rangeEnd: condition.range_end || ""
    });
  }

  function closeRangeEditor() {
    setRangeEditor(createEmptyRangeEditor());
  }

  function applyRangeEditor() {
    if (!rangeEditor.conditionId) {
      closeRangeEditor();
      return;
    }
    updateCondition(rangeEditor.conditionId, {
      range_start: rangeEditor.rangeStart,
      range_end: rangeEditor.rangeEnd
    });
    closeRangeEditor();
  }

  function sanitizeConditionFields(columns) {
    setConditions((prev) =>
      prev.map((item) =>
        item.field_name && !columns.includes(item.field_name) ? { ...item, field_name: "" } : item
      )
    );
  }

  function serializeConditions() {
    return conditions.map(({ id, ...item }) => item);
  }

  useEffect(() => {
    if (!rangeEditor.open) {
      return undefined;
    }

    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeRangeEditor();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [rangeEditor.open]);

  useEffect(() => {
    if (!rangeEditor.open) {
      return;
    }
    const stillExists = conditions.some((item) => item.id === rangeEditor.conditionId);
    if (!stillExists) {
      closeRangeEditor();
    }
  }, [conditions, rangeEditor.open, rangeEditor.conditionId]);

  return {
    logic,
    setLogic,
    conditions,
    updateCondition,
    addCondition,
    removeCondition,
    sanitizeConditionFields,
    serializeConditions,
    rangeEditor,
    setRangeEditor,
    openRangeEditor,
    closeRangeEditor,
    applyRangeEditor
  };
}
