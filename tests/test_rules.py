# -*- coding: utf-8 -*-
import pytest
from app.llm_extractor import extract_with_llm
from app.rules import load_rules, evaluate

# Contenido de las cartas de prueba (copiado de examples/)
aprobado_letter_content = """Solicitud de Crédito Personal
Apreciados señores,

Me dirijo a ustedes con el fin de solicitar un crédito personal por un valor de 400,000 pesos. Mi nombre es Juan Pérez, tengo 32 años y cuento con una experiencia laboral de 5 años. Actualmente, mis ingresos mensuales ascienden a 1,800,000 pesos, lo que me permite afrontar con solvencia mis obligaciones financieras.

Es importante destacar que mi historial crediticio es favorable. En los últimos seis meses no he tenido ningún crédito en mora, mi calificación crediticia es "Buena" y, a la fecha, solo mantengo un crédito activo. Además, en los últimos doce meses no he recibido ningún rechazo de solicitud de crédito.

Confío en que mi perfil financiero cumple con los requisitos necesarios para la aprobación de este préstamo. Adjunto a esta carta, encontrarán la documentación necesaria para su evaluación.

Agradezco de antemano su atención y quedo a su disposición para cualquier información adicional que requieran.

Atentamente,
Juan Pérez"""

rechazado_letter_content = """Estimados señores,

Me dirijo a ustedes para solicitar formalmente un crédito personal por un monto de $500,000. Mi nombre es María Gómez, tengo 25 años y, actualmente, mis ingresos mensuales ascienden a $900,000.

Durante el último año, he solicitado crédito en tres ocasiones, pero lamentablemente mis solicitudes fueron rechazadas. Aunque mi historial crediticio, con una calificación de "Regular", no es perfecto, me gustaría destacar que, a pesar de tener tres créditos activos, solo he tenido un crédito en mora en los últimos seis meses. Reconozco que mi experiencia laboral es limitada, con menos de un año en mi trabajo actual, pero estoy comprometida con el pago puntual de todas mis obligaciones financieras.

Confío en que puedan considerar mi solicitud y evaluar mi capacidad de pago. Agradezco de antemano su tiempo y atención. Quedo a su disposición para cualquier información adicional que requieran.

Atentamente,

María Gómez"""

# Carga las reglas de negocio una sola vez para todas las pruebas.
rules_config = load_rules("business_rules.yaml")

def test_approved_case():
    """Verifica que el caso de Juan Pérez (aprobado) se evalúe correctamente."""
    extracted_data = extract_with_llm(aprobado_letter_content)
    decision = evaluate(extracted_data, rules_config)

    assert decision.approved is True
    assert decision.risk_score == 0.0
    # Verifica que todas las reglas pasaron
    for rule_result in decision.rule_results:
        assert rule_result.passed is True, f"Rule {rule_result.id} failed: {rule_result.reason}"

def test_rejected_case():
    """Verifica que el caso de María Gómez (rechazado) se evalúe correctamente."""
    extracted_data = extract_with_llm(rechazado_letter_content)
    decision = evaluate(extracted_data, rules_config)

    assert decision.approved is False
    assert decision.risk_score > 0.0
    
    # Verifica que las reglas esperadas fallen
    failed_rule_ids = [r.id for r in decision.rule_results if not r.passed]
    expected_failed_rule_ids = [
        "income_min",
        "no_delinquency_6m",
        "amount_ratio_ok",
        "experience_min",
        "active_credits_max",
        "credit_rating_min",
        "rejections_max"
    ]
    assert set(failed_rule_ids) == set(expected_failed_rule_ids)
