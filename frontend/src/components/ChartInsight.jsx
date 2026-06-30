import { useState, useEffect } from "react";
import { fetchInsight } from "../api/client";

export default function ChartInsight({ chartType }) {
  const [text, setText] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setText(null);

    fetchInsight(chartType)
      .then((res) => {
        if (!cancelled) setText(res.text);
      })
      .catch(() => {
        if (!cancelled) setText("No se pudo cargar el análisis.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chartType]);

  if (loading) return <InsightSkeleton />;

  return (
    <p className="text-xs text-gray-500 mt-3 leading-relaxed border-t border-gray-100 pt-2">
      {text}
    </p>
  );
}

function InsightSkeleton() {
  return (
    <div className="mt-3 pt-2 border-t border-gray-100 space-y-2 animate-pulse">
      <div className="h-3 bg-gray-200 rounded w-full" />
      <div className="h-3 bg-gray-200 rounded w-5/6" />
      <div className="h-3 bg-gray-200 rounded w-4/6" />
    </div>
  );
}
