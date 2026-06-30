import { useState, useEffect } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { fetchMetric } from "../../api/client";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
  "#84cc16",
  "#6366f1",
];

export default function IntegrationsDistribution({ apiParams }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetchMetric("integrations-distribution", apiParams)
      .then((res) => {
        const sorted = [...res.data].sort((a, b) => b.count - a.count);
        setChartData({
          labels: sorted.map((d) => d.integration),
          datasets: [
            {
              label: "Requests",
              data: sorted.map((d) => d.count),
              backgroundColor: sorted.map((_, i) => COLORS[i % COLORS.length]),
              borderRadius: 4,
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
        Integraciones Más Solicitadas
      </h3>
      <Bar
        data={chartData}
        options={{
          indexAxis: "y",
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true },
          },
        }}
      />
    </div>
  );
}

function ChartPlaceholder() {
  return (
    <div className="bg-white rounded-lg shadow p-4 h-64 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Cargando gráfico...</p>
    </div>
  );
}
