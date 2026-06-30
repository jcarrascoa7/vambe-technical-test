import { useState, useEffect } from "react";
import { Scatter } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";
import { fetchMetric } from "../../api/client";

ChartJS.register(LinearScale, PointElement, Tooltip, Legend);

export default function VolumeCloseRateScatter({ apiParams }) {
  const [chartData, setChartData] = useState(null);
  const [labels, setLabels] = useState([]);

  useEffect(() => {
    fetchMetric("top-sectors-by-volume-rate", apiParams)
      .then((res) => {
        const sectorLabels = res.data.map((d) => d.sector);
        setLabels(sectorLabels);
        setChartData({
          datasets: [
            {
              label: "Sectors",
              data: res.data.map((d) => ({
                x: d.avg_volume,
                y: d.close_rate * 100,
              })),
              backgroundColor: "#3b82f6",
              pointRadius: 8,
              pointHoverRadius: 10,
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
        Volume × Close Rate by Sector
      </h3>
      <Scatter
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const i = ctx.dataIndex;
                  const sector = labels[i] || "";
                  return `${sector}: ${ctx.parsed.x.toFixed(0)} avg vol, ${ctx.parsed.y.toFixed(1)}% close`;
                },
              },
            },
          },
          scales: {
            x: {
              title: { display: true, text: "Avg Monthly Volume" },
              beginAtZero: true,
            },
            y: {
              title: { display: true, text: "Close Rate (%)" },
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
            },
          },
        }}
      />
      <div className="flex flex-wrap gap-2 mt-3">
        {labels.map((label, i) => (
          <span key={label} className="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
            {i + 1}. {label}
          </span>
        ))}
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
