# -*- coding: utf-8 -*-
import os
import glob
from typing import List, Dict
import pandas as pd

from app.llm_extractor import extract_with_llm
from app.rules import load_rules, evaluate

def read_letters_from_folder(folder_path: str = "examples/") -> List[Dict[str, str]]:
    """Lee todos los archivos .txt de una carpeta y los devuelve en una lista de diccionarios."""
    letters = []
    # Busca todos los archivos que terminen en .txt en la carpeta especificada.
    for filepath in glob.glob(os.path.join(folder_path, "*.txt")):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Usa el nombre del archivo como ID.
        filename = os.path.basename(filepath)
        letters.append({"id": filename, "letter": content})
    return letters

def evaluate_batch(letters: List[Dict[str, str]], rules_path: str = "business_rules.yaml") -> pd.DataFrame:
    """Procesa un lote de cartas y devuelve los resultados en un DataFrame de pandas."""
    results = []
    # Carga las reglas una sola vez.
    rules_config = load_rules(rules_path)

    for item in letters:
        letter_id = item['id']
        letter_text = item['letter']
        
        try:
            # Ejecuta el pipeline de extracción y evaluación para cada carta.
            extracted_data = extract_with_llm(letter_text)
            decision = evaluate(extracted_data, rules_config)

            # Calcula el ratio de deuda sobre ingresos.
            ratio = (decision.extracted.financials.requested_amount / decision.extracted.financials.income_monthly 
                     if decision.extracted.financials.income_monthly > 0 else float('inf'))

            # Recopila los resultados en un diccionario.
            results.append({
                "id": letter_id,
                "approved": decision.approved,
                "risk_score": decision.risk_score,
                "failed_rules": ", ".join(decision.rationale),
                "income": decision.extracted.financials.income_monthly,
                "requested_amount": decision.extracted.financials.requested_amount,
                "amount_income_ratio": ratio,
                "age_years": decision.extracted.applicant.age_years,
                "active_credits": decision.extracted.financials.active_credits,
                "rating": decision.extracted.credit.credit_rating,
                "rejections_12m": decision.extracted.credit.rejections_last_12m,
                "has_mora": decision.extracted.credit.has_delinquencies_last_6m,
                "tenure_months": decision.extracted.employment.employment_tenure_months
            })
        except Exception as e:
            # Si una carta falla, se registra el error y se continúa con las demás.
            results.append({"id": letter_id, "approved": False, "failed_rules": f"parse_error: {e}"})

    # Convierte la lista de resultados a un DataFrame de pandas.
    return pd.DataFrame(results)

def to_csv(df: pd.DataFrame, path: str = "decisions.csv"):
    """Guarda un DataFrame en un archivo CSV."""
    df.to_csv(path, index=False)
