"""LLM-generated insights for dashboard charts."""

from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.categorizer.llm_client import call_llm
from backend.database import get_db
from backend.models import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])

NOT_SPECIFIED = "Not specified"


class InsightResponse(BaseModel):
    chart_type: str
    justification: str
    decision: str


# Decision/justification context per chart from docs/domain.md
_CHART_CONTEXT: dict[str, dict[str, str]] = {
    "close-rate-by-sector": {
        "decision": "Dónde enfocar los esfuerzos comerciales y de marketing",
        "justification": "El ROI de Vambe varía completamente por vertical. La tasa de cierre por sector indica qué sectores priorizar.",
    },
    "sector-distribution": {
        "decision": "Entender la composición actual del portafolio",
        "justification": "Muestra qué tan diversificado está el portafolio actual de clientes por sector.",
    },
    "pain-distribution": {
        "decision": "Calibrar el pitch de ventas por vertical",
        "justification": "Si el dolor dominante no se alinea con el enfoque del equipo de ventas, la conversación no conecta.",
    },
    "close-rate-by-source": {
        "decision": "Dónde invertir en marketing y canales de adquisición",
        "justification": "Los leads de fuentes con mayor tasa de cierre deben recibir más inversión de marketing y seguimiento prioritario.",
    },
    "close-rate-by-concreteness": {
        "decision": "Calificar leads en tiempo real",
        "justification": "Si la brecha de cierre entre lenguaje concreto y tentativo es alta, se convierte en señal de calificación en tiempo real.",
    },
    "vendor-sector-heatmap": {
        "decision": "A quién asignar cada lead",
        "justification": "Las combinaciones vendedor-sector con mayor tasa de cierre deben guiar la asignación de leads entrantes.",
    },
    "temporal-evolution": {
        "decision": "Evaluar tendencia de crecimiento y eficiencia",
        "justification": "La tendencia de leads y cierres por mes muestra si el crecimiento y la eficiencia comercial están mejorando.",
    },
    "integrations-distribution": {
        "decision": "Priorizar la hoja de ruta técnica",
        "justification": "Las integraciones más solicitadas por prospectos deben priorizarse en la hoja de ruta técnica del producto.",
    },
    "volume-close-rate": {
        "decision": "Identificar 'sweet spots' de sectores",
        "justification": "Combina volumen promedio de consultas mensuales con tasa de cierre para identificar sectores de mayor valor estratégico.",
    },
}

_VOLUME_MAP = {"Low": 250, "Medium": 1250, "High": 3500, "Very High": 7500}


def _fetch_chart_data(chart_type: str, db: Session) -> str:
    """Query actual metric data and return a concise summary for the LLM."""
    base = db.query(Client).filter(Client.categorized == True)  # noqa: E712

    if chart_type == "close-rate-by-sector":
        rows = (
            base.filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
            .with_entities(
                Client.sector,
                func.count().label("total"),
                func.sum(case((Client.closed == True, 1), else_=0)).label(
                    "closed"
                ),  # noqa: E712
            )
            .group_by(Client.sector)
            .all()
        )
        items = sorted(
            [(r.sector, r.total, int(r.closed or 0)) for r in rows],
            key=lambda x: (x[2] / x[1] if x[1] else 0),
            reverse=True,
        )
        lines = [
            f"- {name}: {closed}/{total} ({closed/total*100:.1f}%)"
            for name, total, closed in items[:5]
        ]
        return (
            "Tasa de cierre por sector (top 5):\n" + "\n".join(lines) if lines else ""
        )

    if chart_type == "sector-distribution":
        rows = (
            base.filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
            .with_entities(Client.sector, func.count().label("count"))
            .group_by(Client.sector)
            .all()
        )
        total = sum(r.count for r in rows)
        items = sorted(rows, key=lambda r: r.count, reverse=True)
        lines = [
            f"- {r.sector}: {r.count} ({r.count/total*100:.1f}%)" for r in items[:5]
        ]
        return "Distribución de sectores (top 5):\n" + "\n".join(lines) if lines else ""

    if chart_type == "pain-distribution":
        rows = (
            base.filter(
                Client.pain != NOT_SPECIFIED,
                Client.pain.isnot(None),
                Client.sector != NOT_SPECIFIED,
                Client.sector.isnot(None),
            )
            .with_entities(Client.sector, Client.pain, func.count().label("count"))
            .group_by(Client.sector, Client.pain)
            .all()
        )
        by_sector: dict[str, list[str]] = {}
        for r in rows:
            by_sector.setdefault(r.sector, []).append(f"{r.pain}: {r.count}")
        top = sorted(
            by_sector.items(),
            key=lambda kv: sum(int(s.split(": ")[1]) for s in kv[1]),
            reverse=True,
        )[:5]
        blocks = []
        for sector, pains in top:
            blocks.append(f"- {sector}: {', '.join(pains)}")
        return (
            "Dolor principal por sector (top 5):\n" + "\n".join(blocks)
            if blocks
            else ""
        )

    if chart_type == "close-rate-by-source":
        rows = (
            base.filter(Client.source != NOT_SPECIFIED, Client.source.isnot(None))
            .with_entities(
                Client.source,
                func.count().label("total"),
                func.sum(case((Client.closed == True, 1), else_=0)).label(
                    "closed"
                ),  # noqa: E712
            )
            .group_by(Client.source)
            .all()
        )
        items = sorted(
            [(r.source, r.total, int(r.closed or 0)) for r in rows],
            key=lambda x: (x[2] / x[1] if x[1] else 0),
            reverse=True,
        )
        lines = [
            f"- {name}: {closed}/{total} ({closed/total*100:.1f}%)"
            for name, total, closed in items
        ]
        return (
            "Tasa de cierre por fuente de adquisición:\n" + "\n".join(lines)
            if lines
            else ""
        )

    if chart_type == "close-rate-by-concreteness":
        rows = (
            base.filter(
                Client.concreteness != NOT_SPECIFIED, Client.concreteness.isnot(None)
            )
            .with_entities(
                Client.concreteness,
                func.count().label("total"),
                func.sum(case((Client.closed == True, 1), else_=0)).label(
                    "closed"
                ),  # noqa: E712
            )
            .group_by(Client.concreteness)
            .all()
        )
        items = sorted(
            [(r.concreteness, r.total, int(r.closed or 0)) for r in rows],
            key=lambda x: (x[2] / x[1] if x[1] else 0),
            reverse=True,
        )
        lines = [
            f"- {name}: {closed}/{total} ({closed/total*100:.1f}%)"
            for name, total, closed in items
        ]
        return (
            "Tasa de cierre por concreción del lenguaje:\n" + "\n".join(lines)
            if lines
            else ""
        )

    if chart_type == "vendor-sector-heatmap":
        rows = (
            base.filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
            .with_entities(
                Client.vendor,
                Client.sector,
                func.count().label("total"),
                func.sum(case((Client.closed == True, 1), else_=0)).label(
                    "closed"
                ),  # noqa: E712
            )
            .group_by(Client.vendor, Client.sector)
            .all()
        )
        items = sorted(
            [(r.vendor, r.sector, r.total, int(r.closed or 0)) for r in rows],
            key=lambda x: (x[3] / x[2] if x[2] else 0),
            reverse=True,
        )
        lines = [
            f"- {vendor}/{sector}: {closed}/{total} ({closed/total*100:.1f}%)"
            for vendor, sector, total, closed in items[:8]
        ]
        return (
            "Tasa de cierre por vendedor/sector (top 8):\n" + "\n".join(lines)
            if lines
            else ""
        )

    if chart_type == "temporal-evolution":
        rows = (
            base.filter(Client.meeting_date.isnot(None))
            .with_entities(Client.meeting_date, Client.closed)
            .all()
        )
        months: dict[str, dict] = {}
        for dt, closed in rows:
            key = f"{dt.year:04d}-{dt.month:02d}"
            if key not in months:
                months[key] = {"leads": 0, "closes": 0}
            months[key]["leads"] += 1
            if closed:
                months[key]["closes"] += 1
        last6 = sorted(months.items())[-6:]
        lines = []
        for k, v in last6:
            rate = round(v["closes"] / v["leads"] * 100, 1) if v["leads"] else 0
            lines.append(f"- {k}: {v['leads']} leads, {v['closes']} cierres ({rate}%)")
        return (
            "Evolución temporal (últimos 6 meses):\n" + "\n".join(lines)
            if lines
            else ""
        )

    if chart_type == "integrations-distribution":
        rows = (
            base.filter(
                Client.integrations != NOT_SPECIFIED, Client.integrations.isnot(None)
            )
            .with_entities(Client.integrations)
            .all()
        )
        counts: dict[str, int] = {}
        for (integrations,) in rows:
            for item in integrations.split(","):
                item = item.strip()
                if item:
                    counts[item] = counts.get(item, 0) + 1
        top = sorted(counts.items(), key=lambda x: -x[1])[:5]
        lines = [f"- {name}: {count}" for name, count in top]
        return (
            "Integraciones más solicitadas (top 5):\n" + "\n".join(lines)
            if lines
            else ""
        )

    if chart_type == "volume-close-rate":
        close_rows = (
            base.filter(Client.sector != NOT_SPECIFIED, Client.sector.isnot(None))
            .with_entities(
                Client.sector,
                func.count().label("total"),
                func.sum(case((Client.closed == True, 1), else_=0)).label(
                    "closed"
                ),  # noqa: E712
            )
            .group_by(Client.sector)
            .all()
        )
        close_map = {
            r.sector: (int(r.closed or 0) / r.total if r.total else 0)
            for r in close_rows
        }
        vol_rows = (
            base.filter(
                Client.inquiry_volume != NOT_SPECIFIED,
                Client.inquiry_volume.isnot(None),
                Client.sector != NOT_SPECIFIED,
                Client.sector.isnot(None),
            )
            .with_entities(
                Client.sector, Client.inquiry_volume, func.count().label("count")
            )
            .group_by(Client.sector, Client.inquiry_volume)
            .all()
        )
        sector_totals: dict[str, float] = {}
        sector_counts: dict[str, int] = {}
        for r in vol_rows:
            vol = _VOLUME_MAP.get(r.inquiry_volume, 0)
            sector_totals[r.sector] = sector_totals.get(r.sector, 0) + vol * r.count
            sector_counts[r.sector] = sector_counts.get(r.sector, 0) + r.count
        scored = []
        for sector in close_map:
            avg_vol = (
                (sector_totals.get(sector, 0) / sector_counts.get(sector, 1))
                if sector_counts.get(sector)
                else 0
            )
            rate = close_map.get(sector, 0)
            scored.append((sector, avg_vol, rate, avg_vol * rate))
        scored.sort(key=lambda x: -x[3])
        lines = [
            f"- {s}: vol≈{v:.0f}, cierre={r*100:.1f}%, score={sc:.0f}"
            for s, v, r, sc in scored[:5]
        ]
        return (
            "Sectores por volumen × tasa de cierre (top 5):\n" + "\n".join(lines)
            if lines
            else ""
        )

    return ""


def _truncate_justification(text: str, max_words: int = 25) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _build_prompt(chart_type: str, context: dict[str, str], data_summary: str) -> str:
    data_block = ""
    if data_summary:
        data_block = f"\nDatos reales del gráfico:\n{data_summary}\n"

    return (
        "Eres un analista de datos experto en ventas y CRM para Vambe, "
        "una startup chilena que automatiza atención al cliente y ventas vía "
        "WhatsApp e Instagram.\n\n"
        f"Debes analizar un gráfico del dashboard de tipo '{chart_type}'.\n\n"
        f"Contexto de negocio: {context['decision']}\n"
        f"{data_block}\n"
        "Instrucciones:\n"
        "- Escribe UNA SOLA oración corta en español (máximo 30 palabras) con una "
        "decisión accionable basada EXCLUSIVAMENTE en los datos mostrados arriba.\n"
        "- Menciona los sectores/fuentes/categorías específicas con mejor o peor "
        "rendimiento según los datos.\n"
        "- No incluyas números ni porcentajes exactos, solo referencias cualitativas "
        "a los datos (ej: 'Retail lidera', 'LinkedIn supera a Google').\n"
        "- Sé conciso, profesional y orientado a la acción.\n"
        "- Responde ÚNICAMENTE con un objeto JSON con la clave 'decision'.\n\n"
        'Ejemplo de respuesta: {"decision": "Priorizar Retail y Health donde la tasa de cierre es más alta, y reforzar el equipo en Education donde aún hay margen de mejora."}'
    )


def _clean_decision(text: str) -> str:
    """Strip JSON wrapper if LLM leaks it into the decision string."""
    if not text:
        return text
    m = re.search(r'\{[^}]*"decision"\s*:\s*"([^"]*)"\s*\}', text)
    if m:
        return m.group(1).strip()
    return text.strip()


@router.get("/{chart_type}", response_model=InsightResponse)
async def get_insight(
    chart_type: str, db: Session = Depends(get_db)
) -> InsightResponse:
    context = _CHART_CONTEXT.get(chart_type)
    if not context:
        return InsightResponse(
            chart_type=chart_type,
            justification="",
            decision="Tipo de gráfico no reconocido.",
        )

    justification = _truncate_justification(context["justification"])
    data_summary = _fetch_chart_data(chart_type, db)
    prompt = _build_prompt(chart_type, context, data_summary)
    raw = await call_llm(prompt, timeout=30.0, max_retries=2)

    if not raw:
        return InsightResponse(
            chart_type=chart_type,
            justification=justification,
            decision="No se pudo generar la decisión en este momento.",
        )

    try:
        data = json.loads(raw)
        decision = _clean_decision(data.get("decision", ""))
        if decision:
            return InsightResponse(
                chart_type=chart_type, justification=justification, decision=decision
            )
    except (json.JSONDecodeError, KeyError):
        cleaned = _clean_decision(raw)
        if len(cleaned) > 10:
            return InsightResponse(
                chart_type=chart_type, justification=justification, decision=cleaned
            )

    return InsightResponse(
        chart_type=chart_type,
        justification=justification,
        decision="No se pudo generar la decisión en este momento.",
    )
