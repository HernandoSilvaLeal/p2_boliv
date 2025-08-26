# -*- coding: utf-8 -*- 
# Importaciones necesarias de librerías y módulos locales. 
import argparse  # Para procesar argumentos de la línea de comandos (CLI). 
import json      # Para trabajar con objetos JSON. 
from fastapi import FastAPI, HTTPException  # FastAPI, el framework para crear la API; HTTPException para manejar errores. 
from pydantic import BaseModel  # Pydantic, para validación de datos. 
import uvicorn   # El servidor que ejecutará la API. 

# Importaciones de nuestros propios módulos de la aplicación. 
from app.llm_extractor import extract_with_llm  # Función que extrae datos de la carta. 
from app.rules import load_rules, evaluate      # Funciones para cargar y evaluar las reglas de negocio. 
from app.schema import Decision, ApplicationExtract # Modelos de datos Pydantic para la respuesta. 

# --- Inicialización de la API FastAPI --- 
# Se crea una instancia de FastAPI. La información aquí proporcionada se mostrará en la documentación de Swagger. 
api = FastAPI( 
    title="Credit Approval API", 
    description="API para procesar cartas de crédito con LLM y reglas YAML. Incluye un fallback a regex.", 
    version="1.0.0" 
) 

# --- Modelos de Datos para la API --- 
# Define la estructura de los datos que la API espera recibir en las solicitudes (requests). 
class DecisionRequest(BaseModel): 
    """Define el cuerpo de una solicitud para los endpoints de la API.""" 
    letter: str  # El campo principal: la carta de solicitud de crédito como texto. 
    rules_path: str = "business_rules.yaml"  # Opcional: la ruta al archivo de reglas. Por defecto, usa el local. 

# --- Endpoints de la API --- 

@api.post("/extract", response_model=ApplicationExtract) 
def extract(req: DecisionRequest): 
    """Endpoint para extraer información estructurada de la carta. 
    
    Recibe una carta y devuelve solo los datos extraídos en formato JSON, 
    sin aplicar ninguna regla de negocio. 
    Utiliza el extractor LLM o el fallback de regex. 
    """ 
    try: 
        # Llama a la función de extracción y devuelve directamente el resultado. 
        return extract_with_llm(req.letter) 
    except Exception as e: 
        # Si ocurre cualquier error durante la extracción, se devuelve un error HTTP 500. 
        raise HTTPException(status_code=500, detail=str(e)) 

@api.post("/decision", response_model=Decision) 
def decision(req: DecisionRequest): 
    """Endpoint principal para tomar una decisión de crédito completa. 
    
    Recibe una carta, extrae los datos, los evalúa contra las reglas de negocio 
    y devuelve el veredicto final (Aprobado/Rechazado) junto con el detalle. 
    """ 
    try: 
        # 1. Extraer datos de la carta. 
        ex = extract_with_llm(req.letter) 
        # 2. Cargar la configuración de reglas desde el archivo YAML. 
        cfg = load_rules(req.rules_path) 
        # 3. Evaluar los datos extraídos con las reglas cargadas. 
        dec = evaluate(ex, cfg) 
        # 4. Devolver el objeto de decisión completo. 
        return dec 
    except Exception as e: 
        # Si algo falla en el proceso, se devuelve un error HTTP 500. 
        raise HTTPException(status_code=500, detail=str(e)) 

# --- Lógica para la Ejecución como Script (CLI) --- 

def main(): 
    """Función principal que se ejecuta cuando el script es llamado desde la línea de comandos.""" 
    # 1. Configurar el parser para aceptar argumentos en la consola. 
    parser = argparse.ArgumentParser(description="Credit Decision CLI") 
    parser.add_argument("--letter", required=True, help="Ruta al archivo de texto de la carta.") 
    parser.add_argument("--rules", default="business_rules.yaml", help="Ruta al archivo de reglas YAML.") 
    args = parser.parse_args()  # Procesar los argumentos proporcionados. 

    # 2. Leer el contenido del archivo de la carta. 
    # Se especifica encoding='utf-8' para manejar correctamente tildes y caracteres especiales. 
    with open(args.letter, 'r', encoding='utf-8') as f: 
        letter = f.read() 

    # 3. Ejecutar el mismo flujo que la API: extraer, cargar reglas, evaluar. 
    extracted_data = extract_with_llm(letter) 
    rules = load_rules(args.rules) 
    decision_result = evaluate(extracted_data, rules) 

    # 4. Imprimir los resultados en la consola de forma clara y estructurada. 
    print("--- EXTRACCIÓN ---") 
    # .model_dump_json() es el método de Pydantic v2 para serializar a JSON. 
    print(json.dumps(json.loads(decision_result.extracted.model_dump_json()), indent=2)) 
    print("\n--- REGLAS ---") 
    for result in decision_result.rule_results: 
        status = "[APROBADO]" if result.passed else "[RECHAZADO]" 
        print(f"{status} {result.reason}: {result.value}") 
    print("\n--- DECISIÓN ---") 
    print(f"APROBADO: {decision_result.approved}") 
    print(f"Riesgo: {decision_result.risk_score:.2f}") 

# --- Punto de Entrada del Script --- 
# Este bloque estándar de Python asegura que la función `main()` solo se ejecute 
# cuando el archivo es llamado directamente como un script (ej. `python -m app.main`). 
# No se ejecutará si este archivo es importado por otro módulo. 
if __name__ == "__main__": 
    main() 
