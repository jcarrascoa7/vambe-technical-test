import { useState, useEffect, useCallback } from "react";
import "./index.css";
import Filters from "./components/Filters";
import KPICards from "./components/KPICards";
import ClientTable from "./components/ClientTable";
import CloseRateBySector from "./components/Charts/CloseRateBySector";
import SectorDistribution from "./components/Charts/SectorDistribution";
import PainDistribution from "./components/Charts/PainDistribution";
import CloseRateBySource from "./components/Charts/CloseRateBySource";
import CloseRateByConcreteness from "./components/Charts/CloseRateByConcreteness";
import VendorSectorHeatmap from "./components/Charts/VendorSectorHeatmap";
import TemporalEvolution from "./components/Charts/TemporalEvolution";
import IntegrationsDistribution from "./components/Charts/IntegrationsDistribution";
import VolumeCloseRateScatter from "./components/Charts/VolumeCloseRateScatter";
import useFilters from "./hooks/useFilters";
import { fetchClients, fetchStatus, fetchMetric } from "./api/client";

const PAGE_LIMIT = 20;

export default function App() {
  const { filters, setFilter, resetFilters, apiParams } = useFilters();
  const [clients, setClients] = useState([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState({
    closeRate: 0,
    topSector: "",
    topVendor: "",
  });
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);

  const loadClients = useCallback(async () => {
    setLoading(true);
    try {
      const params = { ...apiParams, limit: PAGE_LIMIT, offset };
      if (search) params.search = search;
      const data = await fetchClients(params);
      setClients(data.items);
      setTotal(data.total);
    } catch {
      setClients([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [apiParams, search, offset]);

  const loadKpis = useCallback(async () => {
    try {
      const [sectorData, vendorData] = await Promise.all([
        fetchMetric("close-rate-by-sector", apiParams),
        fetchMetric("close-rate-by-vendor-sector", apiParams),
      ]);

      let totalClosed = 0;
      let totalAll = 0;
      let bestSector = "";
      let bestSectorRate = -1;
      for (const row of sectorData.data) {
        totalClosed += row.closed_count;
        totalAll += row.total;
        if (row.close_rate > bestSectorRate) {
          bestSectorRate = row.close_rate;
          bestSector = row.sector;
        }
      }
      const closeRate =
        totalAll > 0 ? ((totalClosed / totalAll) * 100).toFixed(1) : "0";

      const vendorMap = {};
      for (const row of vendorData.data) {
        if (!vendorMap[row.vendor])
          vendorMap[row.vendor] = { closed: 0, total: 0 };
        vendorMap[row.vendor].closed += row.closed_count;
        vendorMap[row.vendor].total += row.total;
      }
      let bestVendor = "";
      let bestVendorRate = -1;
      for (const [vendor, agg] of Object.entries(vendorMap)) {
        const rate = agg.total > 0 ? agg.closed / agg.total : 0;
        if (rate > bestVendorRate) {
          bestVendorRate = rate;
          bestVendor = vendor;
        }
      }

      setKpis({ closeRate, topSector: bestSector, topVendor: bestVendor });
    } catch {
      setKpis({ closeRate: 0, topSector: "", topVendor: "" });
    }
  }, [apiParams]);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  useEffect(() => {
    loadKpis();
  }, [loadKpis]);

  useEffect(() => {
    fetchStatus()
      .then(setStatus)
      .catch(() => {});
    // ponytail: poll status every 10s so progress bar updates during categorization
    const id = setInterval(() => {
      fetchStatus()
        .then(setStatus)
        .catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, []);

  const handleSearch = useCallback((term) => {
    setSearch(term);
    setOffset(0);
  }, []);

  const handlePaginate = useCallback((newOffset) => {
    setOffset(newOffset);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">Vambe Dashboard</h1>
          {status && <CategorizationProgress status={status} />}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <Filters
          filters={filters}
          setFilter={setFilter}
          resetFilters={resetFilters}
        />

        <KPICards
          total={total}
          closeRate={kpis.closeRate}
          topSector={kpis.topSector}
          topVendor={kpis.topVendor}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <CloseRateBySector apiParams={apiParams} />
          <SectorDistribution apiParams={apiParams} />
          <PainDistribution apiParams={apiParams} />
          <CloseRateBySource apiParams={apiParams} />
          <CloseRateByConcreteness apiParams={apiParams} />
          <VendorSectorHeatmap apiParams={apiParams} />
          <TemporalEvolution apiParams={apiParams} />
          <IntegrationsDistribution apiParams={apiParams} />
          <VolumeCloseRateScatter apiParams={apiParams} />
        </div>

        <ClientTable
          clients={clients}
          total={total}
          loading={loading}
          onSearch={handleSearch}
          onPaginate={handlePaginate}
          limit={PAGE_LIMIT}
          offset={offset}
        />
      </main>
    </div>
  );
}

function CategorizationProgress({ status }) {
  const { progress, categorized, total, is_complete } = status;
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>
          {categorized}/{total} categorized
        </span>
        <span>{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${
            is_complete ? "bg-green-500" : "bg-blue-500"
          }`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      {!is_complete && (
        <p className="text-xs text-gray-400 mt-1">
          Processing in background...
        </p>
      )}
    </div>
  );
}
