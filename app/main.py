import argparse
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from app.llm_extractor import extract_with_llm
from app.rules import load_rules, evaluate
from app.schema import Decision

api = FastAPI(
    title="Credit Decision API",
    version="1.0.0",
    description="API for credit decision based on a letter using LLM and business rules."
)

class DecisionRequest(BaseModel):
    letter: str
    rules_path: str = "business_rules.yaml"

@api.post("/extract", response_model=Decision)
async def extract(request: DecisionRequest):
    try:
        extracted_data = extract_with_llm(request.letter)
        rules = load_rules(request.rules_path)
        decision = evaluate(extracted_data, rules)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api.post("/decision", response_model=Decision)
async def get_decision(request: DecisionRequest):
    try:
        extracted_data = extract_with_llm(request.letter)
        rules = load_rules(request.rules_path)
        decision = evaluate(extracted_data, rules)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    parser = argparse.ArgumentParser(description="Credit Decision CLI")
    parser.add_argument("--letter", required=True, help="Path to the letter file")
    parser.add_argument("--rules", default="business_rules.yaml", help="Path to the business rules YAML file")
    args = parser.parse_args()

    with open(args.letter, 'r') as f:
        letter = f.read()

    extracted_data = extract_with_llm(letter)
    rules = load_rules(args.rules)
    decision = evaluate(extracted_data, rules)

    print("--- EXTRACCIÓN ---")
    print(json.dumps(decision.extracted.dict(), indent=2))
    print("\n--- REGLAS ---")
    for result in decision.rule_results:
        status = "✅" if result.passed else "❌"
        print(f"{status} {result.reason}: {result.value}")
    print("\n--- DECISIÓN ---")
    print(f"APROBADO: {decision.approved}")
    print(f"Riesgo: {decision.risk_score:.2f}")

if __name__ == "__main__":
    main()
