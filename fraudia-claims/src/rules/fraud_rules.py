"""
src/rules/fraud_rules.py
Reglas de negocio para detección de indicadores de riesgo.
Cada regla devuelve (activada: bool, descripción: str, peso: int).
"""

from datetime import datetime
from typing import List, Tuple, Dict, Any


RuleResult = Tuple[bool, str, int]  # (activada, descripción, peso_score)


def regla_monto_elevado(monto: float, umbral: float = 30000) -> RuleResult:
    activada = monto > umbral
    return activada, f"Monto reclamado (${monto:,.0f}) supera umbral de ${umbral:,.0f}", 20


def regla_poliza_reciente(fecha_poliza: str, fecha_incidente: str, dias: int = 60) -> RuleResult:
    fp = datetime.strptime(fecha_poliza, "%Y-%m-%d")
    fi = datetime.strptime(fecha_incidente, "%Y-%m-%d")
    delta = (fi - fp).days
    activada = 0 < delta < dias
    return activada, f"Siniestro ocurrió {delta} días después de contratar la póliza (umbral: {dias} días)", 25


def regla_historial_reclamos(historial: int, umbral: int = 3) -> RuleResult:
    activada = historial >= umbral
    return activada, f"Cliente tiene {historial} reclamos previos (umbral: {umbral})", 20


def regla_monto_cero(monto: float) -> RuleResult:
    activada = monto <= 0
    return activada, "Monto reclamado es cero o negativo", 30


def regla_fecha_futura(fecha_incidente: str) -> RuleResult:
    fi = datetime.strptime(fecha_incidente, "%Y-%m-%d")
    activada = fi > datetime.now()
    return activada, "La fecha del incidente es futura", 35


def regla_proveedor_frecuente(proveedor: str, conteo_proveedor: int, umbral: int = 5) -> RuleResult:
    activada = conteo_proveedor >= umbral
    return activada, f"El proveedor '{proveedor}' aparece en {conteo_proveedor} siniestros recientes", 15


def regla_ramo_inconsistente(ramo_siniestro: str, ramo_poliza: str) -> RuleResult:
    if not ramo_siniestro or not ramo_poliza:
        return False, "Información de ramo incompleta para validación", 0
    rs = ramo_siniestro.strip().lower()
    rp = ramo_poliza.strip().lower()
    activada = rs != rp
    return activada, f"Inconsistencia grave: Ramo del siniestro ({ramo_siniestro}) no coincide con ramo de póliza ({ramo_poliza})", 40


def evaluar_todas_las_reglas(siniestro: Dict[str, Any], contexto: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Ejecuta todas las reglas de negocio sobre un siniestro y devuelve
    un resumen con alertas activadas, score parcial y nivel de riesgo.
    """
    if contexto is None:
        contexto = {}

    resultados: List[Dict] = []
    score_reglas = 0

    reglas = [
        regla_monto_elevado(siniestro.get("monto_reclamado", 0)),
        regla_poliza_reciente(siniestro.get("fecha_poliza", "2000-01-01"), siniestro.get("fecha_incidente", "2000-01-01")),
        regla_historial_reclamos(siniestro.get("historial_reclamos", 0)),
        regla_monto_cero(siniestro.get("monto_reclamado", 0)),
        regla_fecha_futura(siniestro.get("fecha_incidente", "2000-01-01")),
        regla_proveedor_frecuente(
            siniestro.get("proveedor", ""),
            contexto.get("conteo_proveedor", 0),
        ),
        regla_ramo_inconsistente(
            siniestro.get("ramo", ""),
            siniestro.get("ramo_poliza") or contexto.get("ramo_poliza", ""),
        ),
    ]

    for activada, descripcion, peso in reglas:
        resultados.append({"activada": activada, "descripcion": descripcion, "peso": peso})
        if activada:
            score_reglas += peso

    alertas_activas = [r["descripcion"] for r in resultados if r["activada"]]

    return {
        "score_reglas": min(score_reglas, 100),
        "alertas": alertas_activas,
        "detalle_reglas": resultados,
        "total_alertas": len(alertas_activas),
    }
