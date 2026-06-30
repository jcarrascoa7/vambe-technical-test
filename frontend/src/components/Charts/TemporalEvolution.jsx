import { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { fetchMetric } from "../../api/client";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function TemporalEvolution({ apiParams }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetchMetric("temporal-evolution", apiParams)
      .then((res) => {
        const sorted = [...res.data].sort((a, b) => a.month.localeCompare(b.month));
        setChartData({
          labels: sorted.map((d) => d.month),
          datasets: [
            {
              label: "Leads",
              data: sorted.map((d) => d.leads),
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              fill: true,
              tension: 0.3,
              pointRadius: 3,
            },
            {
              label: "Closes",
              data: sorted.map((d) => d.closes),
              borderColor: "#10b981",
              backgroundColor: "rgba(16, 185, 129, 0.1)",
              fill: true,
              tension: 0.3,
              pointRadius: 3,
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
        Leads &amp; Closes Over Time
      </h3>
      <Line
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 12, font: { size: 11 } },
            },
          },
          scales: {
            y: { beginAtZero: true },
          },
          interaction: {
            mode: "index",
            intersect: false,
          },
        }}
      />
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
