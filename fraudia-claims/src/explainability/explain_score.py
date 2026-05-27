"""
src/explainability/explain_score.py
Explicaciones inteligentes de scores de riesgo usando GPT-4o-mini.
"""

import os
import json
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _get_client() -> Optional[Any]:
    if not _OPENAI_AVAILABLE:
        return None
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("sk-..."):
        return None
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """Eres un analista experto en detección de fraudes en seguros.
Tu rol es ASISTIR al analista humano — jamás acusas de fraude directamente.
Analizas indicadores de riesgo y generas explicaciones claras, profesionales y accionables.
Responde siempre en español. Sé conciso pero completo.
Usa bullet points cuando sea útil. Nunca menciones que eres una IA en tus análisis."""


def explicar_siniestro(
    siniestro: Dict[str, Any],
    features: Dict[str, Any],
) -> str:
    """
    Genera una explicación narrativa del score de riesgo para un siniestro específico.
    """
    client = _get_client()

    contexto = {
        "id_siniestro": siniestro.get("id_siniestro"),
        "cliente": siniestro.get("cliente"),
        "tipo": siniestro.get("tipo_siniestro"),
        "monto": siniestro.get("monto_reclamado"),
        "historial_reclamos": siniestro.get("historial_reclamos"),
        "dias_desde_poliza": _calcular_dias(siniestro),
        "score_final": features.get("score_final"),
        "nivel_riesgo": features.get("nivel_riesgo"),
        "alertas_activadas": features.get("alertas", []),
        "similitud_narrativa": features.get("nlp", {}).get("max_similitud", 0),
        "narrativa": siniestro.get("narrativa", ""),
    }

    if client is None:
        return _explicacion_local(contexto)

    try:
        prompt = f"""Analiza este siniestro y explica los indicadores de riesgo detectados:

{json.dumps(contexto, ensure_ascii=False, indent=2)}

Proporciona:
1. Resumen ejecutivo del nivel de riesgo (2-3 oraciones)
2. Factores que elevan el riesgo (lista)
3. Factores que reducen el riesgo (lista)
4. Recomendación para el analista
5. Próximos pasos sugeridos"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        return _explicacion_local(contexto) + f"\n\n*(Modo local: {str(e)[:50]})*"


def responder_consulta(
    pregunta: str,
    historial: List[Dict[str, str]],
    contexto_datos: str,
) -> str:
    """Responde preguntas conversacionales del analista sobre el portafolio."""
    client = _get_client()

    if client is None:
        return _respuesta_local(pregunta, contexto_datos)

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]

    if contexto_datos:
        mensajes.append({
            "role": "user",
            "content": f"Contexto actual del sistema:\n{contexto_datos}"
        })
        mensajes.append({
            "role": "assistant",
            "content": "Entendido. Tengo acceso al contexto del portafolio de siniestros. ¿En qué puedo ayudarte?"
        })

    for msg in historial[-6:]:  # últimos 3 turnos
        mensajes.append(msg)

    mensajes.append({"role": "user", "content": pregunta})

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=mensajes,
            max_tokens=800,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        return _respuesta_local(pregunta, contexto_datos) + f"\n\n*(Error API: {str(e)[:50]})*"


def _calcular_dias(siniestro: Dict) -> int:
    from datetime import datetime
    try:
        fp = datetime.strptime(siniestro.get("fecha_poliza", "2020-01-01"), "%Y-%m-%d")
        fi = datetime.strptime(siniestro.get("fecha_incidente", "2020-01-01"), "%Y-%m-%d")
        return max((fi - fp).days, 0)
    except Exception:
        return 0


def _explicacion_local(ctx: Dict) -> str:
    """Explicación determinista cuando la API no está disponible."""
    nivel = ctx.get("nivel_riesgo", "Bajo")
    score = ctx.get("score_final", 0)
    alertas = ctx.get("alertas_activadas", [])

    lineas = [
        f"**Resumen ejecutivo:** El siniestro {ctx.get('id_siniestro')} presenta nivel de riesgo **{nivel}** "
        f"con score de {score}/100.",
        "",
        "**Indicadores detectados:**",
    ]
    if alertas:
        for a in alertas:
            lineas.append(f"• {a}")
    else:
        lineas.append("• No se identificaron alertas adicionales.")

    lineas += [
        "",
        f"**Recomendación:** {'Se sugiere revisión prioritaria y solicitud de documentación adicional.' if nivel == 'Alto' else 'Continuar proceso estándar con seguimiento rutinario.' if nivel == 'Medio' else 'Caso dentro de parámetros normales. Proceder con trámite regular.'}",
        "",
        "⚠️ *Esta es una asistencia automatizada. La decisión final corresponde al analista.*",
    ]
    return "\n".join(lineas)


def _respuesta_local(pregunta: str, contexto: str) -> str:
    pregunta_lower = pregunta.lower()
    if "riesgo alto" in pregunta_lower or "prioritar" in pregunta_lower:
        return "Basado en el análisis del portafolio, los casos con mayor prioridad son aquellos con score superior a 70, múltiples alertas activas y siniestros recientes en pólizas nuevas. Revise el panel de 'Riesgo Alto' en el dashboard."
    elif "proveedor" in pregunta_lower:
        return "Los proveedores con más alertas activas son aquellos que aparecen en múltiples siniestros de alto riesgo. Filtre la tabla por proveedor para identificar patrones de concentración."
    elif "narrativa" in pregunta_lower or "similar" in pregunta_lower:
        return "El módulo NLP detecta narrativas con similitud semántica superior al 65%. Los casos marcados con '🔴 Narrativa similar' presentan descripciones que coinciden con patrones previamente documentados."
    else:
        return f"He analizado su consulta: *'{pregunta}'*. Para una respuesta precisa configure la API key de OpenAI en el archivo .env. El sistema opera en modo local con capacidades de análisis reducidas."
