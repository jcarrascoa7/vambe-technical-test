import { useState, useEffect } from "react";
import { Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { fetchMetric } from "../../api/client";

ChartJS.register(ArcElement, Tooltip, Legend);

const COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
  "#14b8a6", "#e11d48", "#0ea5e9", "#a855f7", "#22c55e",
  "#eab308", "#64748b",
];

export default function SectorDistribution({ apiParams }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetchMetric("sector-distribution", apiParams)
      .then((res) => {
        setChartData({
          labels: res.data.map((d) => d.sector),
          datasets: [
            {
              data: res.data.map((d) => d.count),
              backgroundColor: COLORS.slice(0, res.data.length),
              borderWidth: 1,
              borderColor: "#fff",
            },
          ],
        });
      })
      .catch(() => setChartData(null));
  }, [apiParams]);

  if (!chartData) return <ChartPlaceholder />;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Sector Distribution
      </h3>
      <div className="h-64 flex items-center justify-center">
        <Doughnut
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "right",
                labels: { boxWidth: 12, font: { size: 11 } },
              },
            },
          }}
        />
      </div>
    </div>
  );
}

function ChartPlaceholder() {
  return (
    <div className="bg-white rounded-lg shadow p-4 h-64 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Loading chart...</p>
    </div>
  );
}
