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
import annotationPlugin from "chartjs-plugin-annotation";
import { fetchMetric } from "../../api/client";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, annotationPlugin);

export default function CloseRateBySource({ apiParams }) {
  const [chartData, setChartData] = useState(null);
  const [globalAvg, setGlobalAvg] = useState(0);

  useEffect(() => {
    fetchMetric("close-rate-by-source", apiParams)
      .then((res) => {
        const sorted = [...res.data].sort((a, b) => b.close_rate - a.close_rate);
        const totalClosed = sorted.reduce((s, d) => s + d.closed_count, 0);
        const totalAll = sorted.reduce((s, d) => s + d.total, 0);
        const avg = totalAll > 0 ? (totalClosed / totalAll) * 100 : 0;
        setGlobalAvg(avg);

        setChartData({
          labels: sorted.map((d) => d.source),
          datasets: [
            {
              label: "Close Rate",
              data: sorted.map((d) => (d.close_rate * 100).toFixed(1)),
              backgroundColor: "#10b981",
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
        Close Rate by Source
      </h3>
      <Bar
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            legend: { display: false },
            annotation: {
              annotations: {
                avgLine: {
                  type: "line",
                  yMin: globalAvg,
                  yMax: globalAvg,
                  borderColor: "#ef4444",
                  borderWidth: 2,
                  borderDash: [6, 4],
                  label: {
                    display: true,
                    content: `Avg ${globalAvg.toFixed(1)}%`,
                    position: "end",
                  },
                },
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
            },
          },
        }}
      />
      <p className="text-xs text-gray-400 mt-2">
        Red dashed line = global average ({globalAvg.toFixed(1)}%)
      </p>
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
