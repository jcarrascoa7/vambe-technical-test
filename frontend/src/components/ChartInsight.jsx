import { useState, useEffect } from "react";
import { fetchInsight } from "../api/client";

export default function ChartInsight({ chartType }) {
  const [justificacion, setJustificacion] = useState(null);
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setJustificacion(null);
    setDecision(null);

    fetchInsight(chartType)
      .then((res) => {
        if (!cancelled) {
          setJustificacion(res.justification);
          setDecision(res.decision);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setJustificacion("");
          setDecision("No se pudo cargar el análisis.");
        }
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
    <div className="mt-3 border-t border-gray-100 pt-2 space-y-1">
      {justificacion && (
        <p className="text-xs text-gray-500 leading-relaxed">{justificacion}</p>
      )}
      <p className="text-xs text-gray-700 font-medium leading-relaxed">
        {decision}
      </p>
    </div>
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
