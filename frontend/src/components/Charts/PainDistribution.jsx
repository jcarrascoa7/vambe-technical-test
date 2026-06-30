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

const PAIN_COLORS = {
  "High message volume": "#ef4444",
  "Slow response": "#f97316",
  "Lost leads/follow-up": "#f59e0b",
  "Appointment no-shows": "#10b981",
  "Lack of automation": "#3b82f6",
  "Team saturation": "#8b5cf6",
  "No 24/7 availability": "#ec4899",
};

export default function PainDistribution({ apiParams }) {
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    fetchMetric("pain-distribution-by-sector", apiParams)
      .then((res) => {
        const sectors = [...new Set(res.data.map((d) => d.sector))];
        const pains = [...new Set(res.data.map((d) => d.pain))];

        const lookup = {};
        const sectorTotals = {};
        for (const row of res.data) {
          const key = `${row.sector}||${row.pain}`;
          lookup[key] = row.count;
          sectorTotals[row.sector] =
            (sectorTotals[row.sector] || 0) + row.count;
        }

        const datasets = pains.map((pain) => {
          const data = sectors.map((s) => {
            const count = lookup[`${s}||${pain}`] || 0;
            const total = sectorTotals[s] || 1;
            return ((count / total) * 100).toFixed(1);
          });
          return {
            label: pain,
            data,
            backgroundColor: PAIN_COLORS[pain] || "#94a3b8",
          };
        });

        setChartData({ labels: sectors, datasets });
      })
      .catch(() => setChartData(null));
  }, [apiParams]);

  if (!chartData) return <ChartPlaceholder />;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Pain Distribution by Sector
      </h3>
      <Bar
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 12, font: { size: 10 } },
            },
          },
          scales: {
            x: { stacked: true },
            y: {
              stacked: true,
              ticks: { callback: (v) => `${v}%` },
              max: 100,
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
      <p className="text-gray-400 text-sm">Loading chart...</p>
    </div>
  );
}
