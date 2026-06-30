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

export default function CloseRateBySector({ apiParams }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetchMetric("close-rate-by-sector", apiParams)
      .then((res) => {
        const sorted = [...res.data].sort(
          (a, b) => b.close_rate - a.close_rate,
        );
        setChartData({
          labels: sorted.map((d) => d.sector),
          datasets: [
            {
              label: "Close Rate",
              data: sorted.map((d) => (d.close_rate * 100).toFixed(1)),
              backgroundColor: "#3b82f6",
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
        Tasa de Cierre por Sector
      </h3>
      <Bar
        data={chartData}
        options={{
          indexAxis: "y",
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: {
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
            },
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
