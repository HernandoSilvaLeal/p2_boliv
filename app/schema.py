from pydantic import BaseModel, Field
from typing import List, Optional

class Applicant(BaseModel):
    full_name: str
    national_id: Optional[str] = None
    dob: Optional[str] = None
    age_years: int
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class Employment(BaseModel):
    employer: Optional[str] = None
    employment_type: Optional[str] = None
    employment_tenure_months: int

class Financials(BaseModel):
    income_monthly: int
    expenses_monthly: Optional[int] = None
    requested_amount: int
    currency: str = "COP"
    credit_purpose: Optional[str] = None
    active_credits: int

class CreditProfile(BaseModel):
    has_delinquencies_last_6m: bool
    credit_rating: str
    rejections_last_12m: int

class ApplicationExtract(BaseModel):
    applicant: Applicant
    employment: Employment
    financials: Financials
    credit: CreditProfile
    raw_letter: str

class RuleResult(BaseModel):
    id: str
    passed: bool
    reason: str
    value: str

class Decision(BaseModel):
    approved: bool
    rule_results: List[RuleResult]
    rationale: List[str]
    risk_score: float
    extracted: ApplicationExtract
