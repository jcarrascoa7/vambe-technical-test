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
    text: str


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
        "justification": "Si en educación el dolor dominante es 'no-shows' pero el equipo hace demos enfocadas en 'volumen de mensajes', la conversación no conecta.",
    },
    "close-rate-by-source": {
        "decision": "Dónde invertir en marketing y canales de adquisición",
        "justification": "Si los leads de LinkedIn cierran al 75% y los de Google al 50%, el equipo debe invertir más en LinkedIn.",
    },
    "close-rate-by-concreteness": {
        "decision": "Calificar leads en tiempo real",
        "justification": "Los prospectos que cierran usan lenguaje concreto y accionable; los que no usan lenguaje tentativo. Si la brecha es grande, se convierte en una señal de calificación en tiempo real.",
    },
    "vendor-sector-heatmap": {
        "decision": "A quién asignar cada lead",
        "justification": "Muestra qué vendedor rinde mejor en qué sector. Cuadros oscuros = combinaciones ganadoras; claros = oportunidades perdidas.",
    },
    "temporal-evolution": {
        "decision": "Evaluar tendencia de crecimiento y eficiencia",
        "justification": "Muestra si estamos mejorando: tendencia de crecimiento de leads y eficiencia comercial mes a mes.",
    },
    "integrations-distribution": {
        "decision": "Priorizar la hoja de ruta técnica",
        "justification": "Si el 40% de los prospectos piden integración con Salesforce, eso es input directo para el equipo de producto.",
    },
    "volume-close-rate": {
        "decision": "Identificar 'sweet spots' de sectores",
        "validación": "Valida la propuesta de valor: ¿los sectores con más dolor cierran más?",
        "justification": "Combina volumen promedio de consultas mensuales con tasa de cierre para identificar los sectores de mayor valor estratégico.",
    },
}


def _build_prompt(chart_type: str, context: dict[str, str]) -> str:
    """Build a prompt for the LLM to generate a Spanish insight paragraph."""
    return (
        "Eres un analista de datos experto en ventas y CRM para Vambe, "
        "una startup chilena que automatiza atención al cliente y ventas vía "
        "WhatsApp e Instagram.\n\n"
        f"Debes explicar un gráfico del dashboard de tipo '{chart_type}'.\n\n"
        f"Decisión de negocio que mejora: {context['decision']}\n"
        f"Justificación: {context['justification']}\n\n"
        "Instrucciones:\n"
        "- Escribe UN párrafo explicativo en español (3-5 oraciones).\n"
        "- Explica qué muestra el gráfico y qué decisión de negocio se puede "
        "derivar de los datos.\n"
        "- Sé conciso, profesional y orientado a la acción.\n"
        "- No incluyas números inventados; habla en términos generales sobre "
        "qué buscar en el gráfico.\n"
        "- Responde ÚNICAMENTE con un objeto JSON con la clave 'text'.\n\n"
        'Ejemplo de respuesta: {"text": "Este gráfico muestra..."}'
    )


@router.get("/{chart_type}", response_model=InsightResponse)
async def get_insight(chart_type: str) -> InsightResponse:
    """Return LLM-generated Spanish insight for a chart type."""
    context = _CHART_CONTEXT.get(chart_type)
    if not context:
        return InsightResponse(
            chart_type=chart_type,
            text="Tipo de gráfico no reconocido.",
        )

    prompt = _build_prompt(chart_type, context)
    raw = await call_llm(prompt, timeout=30.0, max_retries=2)

    if not raw:
        return InsightResponse(
            chart_type=chart_type,
            text="No se pudo generar el análisis en este momento. Intente más tarde.",
        )

    try:
        data = json.loads(raw)
        text = data.get("text", "")
        if text:
            return InsightResponse(chart_type=chart_type, text=text)
    except (json.JSONDecodeError, KeyError):
        # LLM returned plain text or malformed JSON — try to use raw text
        if len(raw) > 10:
            return InsightResponse(chart_type=chart_type, text=raw.strip())

    return InsightResponse(
        chart_type=chart_type,
        text="No se pudo generar el análisis en este momento. Intente más tarde.",
    )
