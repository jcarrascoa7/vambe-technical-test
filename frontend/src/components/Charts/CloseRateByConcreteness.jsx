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

export default function CloseRateByConcreteness({ apiParams }) {
  const [chartData, setChartData] = useState(null);
  const [gap, setGap] = useState(0);

  useEffect(() => {
    fetchMetric("close-rate-by-concreteness", apiParams)
      .then((res) => {
        const rates = res.data.map((d) => d.close_rate * 100);
        const max = Math.max(...rates);
        const min = Math.min(...rates);
        setGap(max - min);

        const colors = res.data.map((d) => {
          const r = d.close_rate * 100;
          return r === max ? "#10b981" : r === min ? "#ef4444" : "#3b82f6";
        });

        setChartData({
          labels: res.data.map((d) => d.concreteness),
          datasets: [
            {
              label: "Close Rate",
              data: rates.map((r) => r.toFixed(1)),
              backgroundColor: colors,
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
        Close Rate by Language Concreteness
      </h3>
      <Bar
        data={chartData}
        options={{
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
            },
          },
        }}
      />
      {gap > 0 && (
        <p className="text-xs text-gray-500 mt-2">
          Gap:{" "}
          <span className="font-bold text-gray-700">{gap.toFixed(1)}pp</span>{" "}
          between highest and lowest concreteness levels
        </p>
      )}
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
