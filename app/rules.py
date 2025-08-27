# -*- coding: utf-8 -*-
# Importaciones necesarias.
import yaml  # Librería para leer y escribir archivos YAML.
from app.schema import ApplicationExtract, Decision, RuleResult # Modelos de datos Pydantic.

# --- Carga de Reglas ---

def load_rules(path: str) -> dict:
    """Carga las reglas de negocio desde un archivo YAML.
    
    Args:
        path (str): La ruta al archivo business_rules.yaml.
    
    Returns:
        dict: Un diccionario con la configuración de umbrales, reglas y lógica de decisión.
    """
    with open(path, 'r', encoding='utf-8') as f:
        # yaml.safe_load es la forma segura de parsear un archivo YAML.
        return yaml.safe_load(f)

# --- Motor de Evaluación ---

def evaluate(ex: ApplicationExtract, cfg: dict) -> Decision:
    """Evalúa los datos extraídos de la aplicación contra las reglas de negocio.
    
    Args:
        ex (ApplicationExtract): El objeto con los datos extraídos de la carta.
        cfg (dict): El diccionario de configuración cargado desde el archivo YAML.
        
    Returns:
        Decision: Un objeto que contiene el resultado de la evaluación, la decisión final y el detalle.
    """
    # Extrae las secciones principales del diccionario de configuración.
    rules = cfg['rules']
    thresholds = cfg['thresholds']
    decision_logic = cfg['decision']['logic']

    # Define el orden jerárquico de las calificaciones crediticias. "Mala" es el peor, "Excelente" es el mejor.
    credit_rating_order = ["Mala", "Regular", "Buena", "Muy Buena", "Excelente"]

    # Lista para almacenar el resultado de la evaluación de cada regla individual.
    rule_results = []
    
    # Itera sobre cada una de las reglas definidas en el archivo YAML.
    for rule in rules:
        passed = False  # Por defecto, la regla no se ha pasado.
        reason = ""    # Descripción de la regla.
        value = ""      # Texto que muestra la comparación realizada (ej. "1800000 >= 1000000").

        # --- Bloque de Condiciones: Evalúa cada regla por su ID ---
        # Cada bloque compara un dato extraído (ex) con un umbral (thresholds).

        if rule['id'] == 'income_min':
            passed = ex.financials.income_monthly >= thresholds['min_income']
            value = f"{ex.financials.income_monthly} >= {thresholds['min_income']}"
            reason = rule['desc']
        
        elif rule['id'] == 'no_delinquency_6m':
            # La regla pasa si el aplicante NO tiene moras.
            passed = not ex.credit.has_delinquencies_last_6m
            value = f"has_delinquencies_last_6m: {ex.credit.has_delinquencies_last_6m}"
            reason = rule['desc']

        elif rule['id'] == 'age_min':
            passed = ex.applicant.age_years >= thresholds['min_age']
            value = f"{ex.applicant.age_years} >= {thresholds['min_age']}"
            reason = rule['desc']

        elif rule['id'] == 'amount_ratio_ok': 
            # Calcula el ratio entre el monto solicitado y el ingreso mensual.
            # Se protege contra una división por cero si el ingreso es 0.
            ratio = ex.financials.requested_amount / ex.financials.income_monthly if ex.financials.income_monthly > 0 else float('inf')
            passed = ratio <= thresholds['max_amount_income_ratio']
            value = f"{ratio:.2f} <= {thresholds['max_amount_income_ratio']}" # Formatea el ratio a 2 decimales.
            reason = rule['desc']

        elif rule['id'] == 'experience_or_entrepreneur_ok':
            # --- Nueva regla OR: antigüedad >= umbral  O  emprendimiento propio ---
            text = (ex.raw_letter or "").lower()

            # Heurística para emprendimiento: tipo de empleo o palabras clave en la carta
            kw = ["emprendimiento propio", "negocio propio", "emprendedor", "independiente",
                  "autónomo", "propietario", "dueño", "freelance"]
            is_entrepreneur = False
            etype = (ex.employment.employment_type or "").strip().lower()

            if etype in ["independiente", "autónomo", "contratista", "freelance", "emprendedor"]:
                is_entrepreneur = True
            elif any(k in text for k in kw):
                is_entrepreneur = True

            exp_ok = ex.employment.employment_tenure_months >= thresholds["min_experience_months"]
            or_ok = exp_ok or is_entrepreneur

            passed = or_ok
            reason = (
                f"Antigüedad={ex.employment.employment_tenure_months}m >= {thresholds['min_experience_months']}m"
                if exp_ok else
                ("Evidencia de emprendimiento/negocio propio" if is_entrepreneur else
                 "No cumple antigüedad mínima ni se evidencia emprendimiento")
            )
            value = str(ex.employment.employment_tenure_months) 

        elif rule['id'] == 'active_credits_max':
            passed = ex.financials.active_credits <= thresholds['max_active_credits']
            value = f"{ex.financials.active_credits} <= {thresholds['max_active_credits']}"
            reason = rule['desc']

        elif rule['id'] == 'credit_rating_min':
            # Compara la calificación crediticia usando el orden jerárquico definido arriba.
            # Obtiene el índice numérico de la calificación del aplicante y el mínimo requerido.
            rating_index = credit_rating_order.index(ex.credit.credit_rating) if ex.credit.credit_rating in credit_rating_order else -1
            min_rating_index = credit_rating_order.index(thresholds['min_credit_rating'])
            passed = rating_index >= min_rating_index # Compara los índices.
            value = f"{ex.credit.credit_rating} >= {thresholds['min_credit_rating']}"
            reason = rule['desc']

        elif rule['id'] == 'rejections_max':
            passed = ex.credit.rejections_last_12m <= thresholds['max_rejections_12m']
            value = f"{ex.credit.rejections_last_12m} <= {thresholds['max_rejections_12m']}"
            reason = rule['desc']

        # Añade el resultado de esta regla a la lista de resultados.
        rule_results.append(RuleResult(id=rule['id'], passed=passed, reason=reason, value=value))

    # --- Decisión Final y Puntuación de Riesgo ---

    # Basado en la lógica del YAML ('all' o 'any'), se determina la aprobación.
    # all() devuelve True si todos los elementos de la lista son verdaderos.
    approved = all(r.passed for r in rule_results) if decision_logic == 'all' else any(r.passed for r in rule_results)
    
    # Calcula una puntuación de riesgo simple: 1 - (reglas pasadas / total de reglas).
    # Un riesgo de 0.0 significa que todas las reglas pasaron.
    # Un riesgo de 1.0 significaría que ninguna regla pasó.
    risk_score = 1 - (sum(1 for r in rule_results if r.passed) / len(rule_results))

    # Crea una lista con las razones de por qué fue rechazado (si aplica).
    rationale = [r.reason for r in rule_results if not r.passed]

    # Construye y devuelve el objeto de Decisión final, que contiene toda la información del proceso.
    return Decision(
        approved=approved,
        rule_results=rule_results,
        rationale=rationale,
        risk_score=risk_score,
        extracted=ex
    )