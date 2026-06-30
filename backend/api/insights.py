"""LLM-generated insights for dashboard charts."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from backend.categorizer.llm_client import call_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


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


def _truncate_justification(text: str, max_words: int = 25) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _build_prompt(chart_type: str, context: dict[str, str]) -> str:
    return (
        "Eres un analista de datos experto en ventas y CRM para Vambe, "
        "una startup chilena que automatiza atención al cliente y ventas vía "
        "WhatsApp e Instagram.\n\n"
        f"Debes analizar un gráfico del dashboard de tipo '{chart_type}'.\n\n"
        f"Contexto de negocio: {context['decision']}\n\n"
        "Instrucciones:\n"
        "- Escribe UN párrafo corto en español (2-4 oraciones) con una decisión "
        "accionable basada en los datos del gráfico.\n"
        "- Enfócate solo en qué decisión tomar según la información del gráfico.\n"
        "- Sé conciso, profesional y orientado a la acción.\n"
        "- No incluyas números inventados; habla en términos generales sobre "
        "qué buscar en el gráfico.\n"
        "- Responde ÚNICAMENTE con un objeto JSON con la clave 'decision'.\n\n"
        'Ejemplo de respuesta: {"decision": "Priorizar los sectores con mayor tasa de cierre y asignar más recursos comerciales a esas verticales."}'
    )


@router.get("/{chart_type}", response_model=InsightResponse)
async def get_insight(chart_type: str) -> InsightResponse:
    context = _CHART_CONTEXT.get(chart_type)
    if not context:
        return InsightResponse(
            chart_type=chart_type,
            justification="",
            decision="Tipo de gráfico no reconocido.",
        )

    justification = _truncate_justification(context["justification"])
    prompt = _build_prompt(chart_type, context)
    raw = await call_llm(prompt, timeout=30.0, max_retries=2)

    if not raw:
        return InsightResponse(
            chart_type=chart_type,
            justification=justification,
            decision="No se pudo generar la decisión en este momento.",
        )

    try:
        data = json.loads(raw)
        decision = data.get("decision", "")
        if decision:
            return InsightResponse(
                chart_type=chart_type, justification=justification, decision=decision
            )
    except (json.JSONDecodeError, KeyError):
        if len(raw) > 10:
            return InsightResponse(
                chart_type=chart_type, justification=justification, decision=raw.strip()
            )

    return InsightResponse(
        chart_type=chart_type,
        justification=justification,
        decision="No se pudo generar la decisión en este momento.",
    )
