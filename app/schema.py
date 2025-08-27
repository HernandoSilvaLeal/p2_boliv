# -*- coding: utf-8 -*-
# Importaciones de Pydantic para definir los modelos de datos.
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Modelos de Datos Pydantic V1 ---
# Estos modelos definen la estructura de los datos con los que trabaja la aplicación.
# Sirven para validación automática, serialización (convertir a JSON) y documentación.
# `Optional[str] = None` significa que el campo es opcional y su valor por defecto es None.

class Applicant(BaseModel):
    """Modela la información personal del solicitante."""
    full_name: str
    national_id: Optional[str] = None
    dob: Optional[str] = None
    age_years: int
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class Employment(BaseModel):
    """Modela la información laboral del solicitante."""
    employer: Optional[str] = None
    employment_type: Optional[str] = None
    employment_tenure_months: int # La antigüedad se manejará siempre en meses.
    employment_bussines: bool

class Financials(BaseModel):
    """Modela la información financiera del solicitante."""
    income_monthly: int
    expenses_monthly: Optional[int] = None
    requested_amount: int
    currency: str = "COP" # Valor por defecto para la moneda.
    credit_purpose: Optional[str] = None
    active_credits: int

class CreditProfile(BaseModel):
    """Modela el perfil crediticio del solicitante."""
    has_delinquencies_last_6m: bool # True si ha tenido moras, False si no.
    credit_rating: str # Ej. "Buena", "Regular", "Mala".
    rejections_last_12m: int # Número de rechazos de crédito en el último año.

class ApplicationExtract(BaseModel):
    """Este es el modelo principal que agrupa toda la información extraída de la carta.
    
    Es el objeto que devuelve el módulo `llm_extractor`.
    """
    applicant: Applicant
    employment: Employment
    financials: Financials
    credit: CreditProfile
    raw_letter: str # Se guarda la carta original para referencia.

class RuleResult(BaseModel):
    """Modela el resultado de la evaluación de una única regla de negocio."""
    id: str # El identificador de la regla (ej. "income_min").
    passed: bool # True si la regla se cumplió, False si no.
    reason: str # La descripción de la regla (ej. "Ingresos mensuales > $1.000.000 COP").
    value: str # El valor que se evaluó (ej. "1800000 >= 1000000").

class Decision(BaseModel):
    """Este es el modelo de respuesta final de la API y la CLI.
    
    Agrupa el veredicto final, el detalle de cada regla, el riesgo y los datos extraídos.
    """
    approved: bool # El veredicto final: True para Aprobado, False para Rechazado.
    rule_results: List[RuleResult] # Una lista con los resultados de cada regla evaluada.
    rationale: List[str] # Una lista con las razones del rechazo (si aplica).
    risk_score: float # La puntuación de riesgo calculada (0.0 a 1.0).
    extracted: ApplicationExtract # El objeto completo con los datos extraídos.

# --- Modelos de Datos Pydantic V2 ---

# Para /batch_decision
class BatchItem(BaseModel):
    """Modela un único item en una solicitud de lote."""
    id: str
    letter: str

class BatchRequest(BaseModel):
    """Modela el cuerpo de la solicitud para el endpoint /batch_decision."""
    items: List[BatchItem]
    rules_path: str = "business_rules.yaml"

class BatchRow(BaseModel):
    """Modela una fila en la respuesta del endpoint /batch_decision."""
    id: str
    approved: bool
    risk_score: float
    failed_rules: List[str]
    extracted: ApplicationExtract

class BatchResponse(BaseModel):
    """Modela la respuesta completa del endpoint /batch_decision."""
    rows: List[BatchRow]

# Para /explain
class ExplainRequest(BaseModel):
    """Modela el cuerpo de la solicitud para el endpoint /explain."""
    letter: str
    rules_path: str = "business_rules.yaml"
    provider: Optional[str] = None

class ExplainResponse(BaseModel):
    """Modela la respuesta del endpoint /explain."""
    decision: Decision
    explanation: str
