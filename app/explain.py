# -*- coding: utf-8 -*-
import os
from typing import Optional

from app.schema import Decision

# --- Plantillas para Explicaciones (Fallback) ---

FALLBACK_TEMPLATE_APPROVED = """
La solicitud ha sido **APROBADA**.

**Análisis Positivo:**
El solicitante cumple con todos los criterios de riesgo evaluados. Los indicadores financieros y de perfil son sólidos y se alinean con nuestras políticas de crédito.

**Recomendación:**
Proceder con la originación del crédito según los términos solicitados.
"""

FALLBACK_TEMPLATE_REJECTED = """
La solicitud ha sido **RECHAZADA**.

**Razones Principales:**
La decisión se basa en el incumplimiento de las siguientes políticas de crédito:
- {failed_rules_list}

**Recomendaciones para el Solicitante:**
Para mejorar las probabilidades de aprobación en el futuro, se recomienda:
- {recommendations}
"""

RECOMMENDATIONS_MAP = {
    "income_min": "Asegurar que los ingresos mensuales reportados superen el mínimo requerido.",
    "no_delinquency_6m": "Mantener un historial de pagos sin moras en los últimos 6 meses.",
    "age_min": "Cumplir con la edad mínima requerida para solicitar un crédito.",
    "amount_ratio_ok": "Ajustar el monto solicitado para que no exceda el porcentaje máximo permitido sobre los ingresos.",
    "experience_min": "Contar con la experiencia laboral o de negocio mínima requerida.",
    "active_credits_max": "Reducir el número de créditos activos antes de una nueva solicitud.",
    "credit_rating_min": "Mejorar la calificación crediticia a través de un buen manejo de las deudas.",
    "rejections_max": "Evitar realizar múltiples solicitudes de crédito en un corto período de tiempo."
}

def _generate_fallback_explanation(decision: Decision) -> str:
    """Genera una explicación basada en plantillas locales usando los resultados de las reglas."""
    if decision.approved:
        return FALLBACK_TEMPLATE_APPROVED
    else:
        # Une las razones del rechazo en una lista con viñetas.
        failed_rules_str = "\n- ".join(decision.rationale)
        
        # Genera recomendaciones basadas en las reglas fallidas.
        recs = [RECOMMENDATIONS_MAP[rule.id] for rule in decision.rule_results if not rule.passed and rule.id in RECOMMENDATIONS_MAP]
        recommendations_str = "\n- ".join(recs) if recs else "Revisar el perfil crediticio y financiero general."

        return FALLBACK_TEMPLATE_REJECTED.format(failed_rules_list=failed_rules_str, recommendations=recommendations_str)

def explain_decision(decision: Decision, provider: Optional[str] = None) -> str:
    """Genera una explicación de la decisión, usando un LLM si se especifica, o un fallback local."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    use_llm = False
    if provider == "gemini" and google_api_key:
        use_llm = True
        # TODO: Implementar lógica para llamar a la API de Gemini
        # Por ahora, usará el fallback.
        pass
    elif provider == "openai" and openai_api_key:
        use_llm = True
        # TODO: Implementar lógica para llamar a la API de OpenAI
        # Por ahora, usará el fallback.
        pass

    if use_llm:
        # Esta es una implementación de placeholder. La lógica real del LLM iría aquí.
        print(f"(Simulando llamada a LLM con proveedor: {provider}...)")
        # En una implementación real, aquí se construiría el prompt y se llamaría al LLM.
        # Si la llamada al LLM falla, también debería caer en el fallback.
        return _generate_fallback_explanation(decision) # Placeholder, devuelve el fallback por ahora.
    else:
        # Genera la explicación usando la plantilla local si no se especifica un proveedor o no hay API key.
        return _generate_fallback_explanation(decision)
