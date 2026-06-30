import { useState, useCallback, useMemo } from "react";

const EMPTY_FILTERS = {
  sector: "",
  vendor: "",
  source: "",
  channel: "",
  closed: "",
  date_from: "",
  date_to: "",
};

export default function useFilters() {
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  const setFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(EMPTY_FILTERS);
  }, []);

  const apiParams = useMemo(() => {
    const params = {};
    for (const [key, value] of Object.entries(filters)) {
      if (value !== "") {
        params[key] = value;
      }
    }
    return params;
  }, [filters]);

  return { filters, setFilter, resetFilters, apiParams };
}
