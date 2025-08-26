# -*- coding: utf-8 -*- 
# Importaciones necesarias de librerías y módulos locales.
import argparse
import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

# Importaciones de nuestros propios módulos de la aplicación.
from app.llm_extractor import extract_with_llm
from app.rules import load_rules, evaluate
from app.schema import Decision, ApplicationExtract, BatchItem, BatchRequest, BatchRow, BatchResponse, ExplainRequest, ExplainResponse
from app.batch import read_letters_from_folder, evaluate_batch, to_csv
from app.explain import explain_decision

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Inicialización de la API FastAPI ---
api = FastAPI( 
    title="Credit Approval API", 
    description="API para procesar cartas de crédito con LLM y reglas YAML. Incluye un fallback a regex.", 
    version="1.0.0"
)

# --- Modelos de Datos para la API ---
class DecisionRequest(BaseModel): 
    letter: str 
    rules_path: str = "business_rules.yaml"

# --- Endpoints de la API ---
@api.post("/extract", response_model=ApplicationExtract)
def extract(req: DecisionRequest):
    """Extrae variables estructuradas de la carta usando LLM o fallback"""
    logger.info(f"[API] Recibida solicitud /extract para carta (longitud: {len(req.letter)}).")
    try: 
        return extract_with_llm(req.letter) 
    except Exception as e: 
        logger.error(f"[API] Error en /extract: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/decision", response_model=Decision)
def decision(req: DecisionRequest):
    """Evalúa reglas de negocio y devuelve decisión Aprobado/Rechazado"""
    logger.info(f"[API] Recibida solicitud /decision para carta (longitud: {len(req.letter)}).")
    try: 
        ex = extract_with_llm(req.letter) 
        cfg = load_rules(req.rules_path) 
        dec = evaluate(ex, cfg) 
        return dec 
    except Exception as e: 
        logger.error(f"[API] Error en /decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/batch_decision", response_model=BatchResponse)
def batch_decision(req: BatchRequest):
    """Procesa un lote de cartas y devuelve los resultados en formato estructurado."""
    logger.info(f"[API] Recibida solicitud /batch_decision con {len(req.items)} ítems.")
    if not req.items:
        logger.warning("[API] Solicitud /batch_decision con 0 ítems.")
        raise HTTPException(status_code=400, detail="La lista de ítems no puede estar vacía.")
    
    if len(req.items) > 100:
        logger.warning(f"[API] Solicitud /batch_decision excede el límite de 100 ítems ({len(req.items)}).")
        raise HTTPException(status_code=400, detail="El número máximo de ítems por lote es 100.")

    # Convertir la lista de BatchItem a un formato que evaluate_batch pueda usar
    letters_for_batch = [{'id': item.id, 'letter': item.letter} for item in req.items]
    
    try:
        results_df = evaluate_batch(letters_for_batch, req.rules_path)
        
        # Transformar el DataFrame de pandas a la lista de BatchRow
        batch_rows = []
        for index, row in results_df.iterrows():
            # Manejo de errores de parseo en ítems individuales
            if "parse_error" in row and pd.notna(row["parse_error"]):
                batch_rows.append(BatchRow(
                    id=row["id"],
                    approved=False,
                    risk_score=1.0, # Máximo riesgo para errores de parseo
                    failed_rules=["parse_error"], # Indicar que falló por error de parseo
                    extracted=ApplicationExtract(applicant=None, employment=None, financials=None, credit=None, raw_letter=row["letter"])
                ))
            else:
                # Reconstruir ApplicationExtract para el campo 'extracted'
                extracted_app = ApplicationExtract(
                    applicant=ApplicationExtract.Applicant(full_name=row['full_name'], age_years=row['age_years']),
                    employment=ApplicationExtract.Employment(employment_tenure_months=row['tenure_months']),
                    financials=ApplicationExtract.Financials(income_monthly=row['income'], requested_amount=row['requested_amount'], active_credits=row['active_credits']),
                    credit=ApplicationExtract.CreditProfile(has_delinquencies_last_6m=row['has_mora'], credit_rating=row['rating'], rejections_last_12m=row['rejections_12m']),
                    raw_letter=row['letter']
                )
                batch_rows.append(BatchRow(
                    id=row["id"],
                    approved=row["approved"],
                    risk_score=row["risk_score"],
                    failed_rules=row["failed_rules"].split(", ") if isinstance(row["failed_rules"], str) else [],
                    extracted=extracted_app
                ))
        logger.info(f"[API] Procesado /batch_decision: {len(batch_rows)} ítems.")
        return BatchResponse(rows=batch_rows)
    except Exception as e:
        logger.error(f"[API] Error en /batch_decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    """Genera una explicación en lenguaje natural de la decisión de crédito."""
    logger.info(f"[API] Recibida solicitud /explain para carta (longitud: {len(req.letter)}), proveedor: {req.provider}.")
    try:
        # Primero, obtener la decisión completa
        extracted_data = extract_with_llm(req.letter)
        rules_config = load_rules(req.rules_path)
        decision_obj = evaluate(extracted_data, rules_config)
        
        # Luego, generar la explicación
        explanation_text = explain_decision(decision_obj, req.provider)
        
        logger.info(f"[API] Explicación generada para decisión: {decision_obj.approved}.")
        return ExplainResponse(decision=decision_obj, explanation=explanation_text)
    except Exception as e:
        logger.error(f"[API] Error en /explain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Lógica para la Ejecución como Script (CLI) ---
def main():
    """Función principal que se ejecuta cuando el script es llamado desde la línea de comandos."""
    parser = argparse.ArgumentParser(description="Credit Decision CLI - V2")
    parser.add_argument("--rules", default="business_rules.yaml", help="Ruta al archivo de reglas YAML.")
    
    # Grupo de argumentos mutuamente excluyentes: o se procesa una carta, o un batch.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--letter", help="Ruta al archivo de texto de una sola carta.")
    group.add_argument("--batch_examples", action="store_true", help="Procesa todos los .txt de la carpeta /examples.")
    group.add_argument("--batch_csv", help="Ruta a un archivo CSV con columnas ['id', 'letter'].")

    args = parser.parse_args()

    # --- Lógica para procesar un solo archivo ---
    if args.letter:
        logger.info(f"[CLI] Procesando carta individual: {args.letter}")
        with open(args.letter, 'r', encoding='utf-8') as f:
            letter = f.read()
        
        extracted_data = extract_with_llm(letter)
        rules = load_rules(args.rules)
        decision_result = evaluate(extracted_data, rules)

        print("--- EXTRACCIÓN ---")
        print(json.dumps(json.loads(decision_result.extracted.model_dump_json()), indent=2))
        print("\n--- REGLAS ---")
        for result in decision_result.rule_results:
            status = "[APROBADO]" if result.passed else "[RECHAZADO]"
            print(f"{status} {result.reason}: {result.value}")
        print("\n--- DECISIÓN ---")
        print(f"APROBADO: {decision_result.approved}")
        print(f"Riesgo: {decision_result.risk_score:.2f}")

    # --- Lógica para procesar la carpeta de ejemplos ---
    elif args.batch_examples:
        logger.info("[CLI] Procesando lote de ejemplos desde la carpeta /examples...")
        letters = read_letters_from_folder("examples/")
        results_df = evaluate_batch(letters, args.rules)
        output_path = "decisions.csv"
        to_csv(results_df, output_path)
        
        # Muestra conteos de resultados
        approved_count = results_df['approved'].sum()
        rejected_count = len(results_df) - approved_count
        logger.info(f"[CLI] Proceso de lote completado. Resultados guardados en '{output_path}'.")
        print(f"Proceso de lote completado. Resultados guardados en '{output_path}'.")
        print(f"  - Aprobados: {approved_count}")
        print(f"  - Rechazados: {rejected_count}")

    # --- Lógica para procesar un archivo CSV ---
    elif args.batch_csv:
        logger.info(f"[CLI] Procesando lote desde el archivo CSV: {args.batch_csv}...")
        df = pd.read_csv(args.batch_csv)
        # Asegurarse de que el CSV tiene las columnas correctas
        if 'id' not in df.columns or 'letter' not in df.columns:
            raise ValueError("El archivo CSV debe contener las columnas 'id' y 'letter'.")
        
        letters = df.to_dict('records')
        results_df = evaluate_batch(letters, args.rules)
        output_path = "decisions_from_csv.csv"
        to_csv(results_df, output_path)

        approved_count = results_df['approved'].sum()
        rejected_count = len(results_df) - approved_count
        logger.info(f"[CLI] Proceso de lote completado. Resultados guardados en '{output_path}'.")
        print(f"Proceso de lote completado. Resultados guardados en '{output_path}'.")
        print(f"  - Aprobados: {approved_count}")
        print(f"  - Rechazados: {rejected_count}")

# --- Punto de Entrada del Script ---
if __name__ == "__main__": 
    main()
