import yaml
from app.schema import ApplicationExtract, Decision, RuleResult

def load_rules(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def evaluate(ex: ApplicationExtract, cfg: dict) -> Decision:
    rules = cfg['rules']
    thresholds = cfg['thresholds']
    decision_logic = cfg['decision']['logic']

    credit_rating_order = ["Mala", "Regular", "Buena", "Muy Buena", "Excelente"]

    rule_results = []
    for rule in rules:
        passed = False
        reason = ""
        value = ""

        if rule['id'] == 'income_min':
            passed = ex.financials.income_monthly >= thresholds['min_income']
            value = f"{ex.financials.income_monthly} >= {thresholds['min_income']}"
            reason = rule['desc']
        elif rule['id'] == 'no_delinquency_6m':
            passed = not ex.credit.has_delinquencies_last_6m
            value = f"has_delinquencies_last_6m: {ex.credit.has_delinquencies_last_6m}"
            reason = rule['desc']
        elif rule['id'] == 'age_min':
            passed = ex.applicant.age_years >= thresholds['min_age']
            value = f"{ex.applicant.age_years} >= {thresholds['min_age']}"
            reason = rule['desc']
        elif rule['id'] == 'amount_ratio_ok':
            ratio = ex.financials.requested_amount / ex.financials.income_monthly if ex.financials.income_monthly > 0 else float('inf')
            passed = ratio <= thresholds['max_amount_income_ratio']
            value = f"{ratio:.2f} <= {thresholds['max_amount_income_ratio']}"
            reason = rule['desc']
        elif rule['id'] == 'experience_min':
            passed = ex.employment.employment_tenure_months >= thresholds['min_experience_months']
            value = f"{ex.employment.employment_tenure_months} >= {thresholds['min_experience_months']}"
            reason = rule['desc']
        elif rule['id'] == 'active_credits_max':
            passed = ex.financials.active_credits <= thresholds['max_active_credits']
            value = f"{ex.financials.active_credits} <= {thresholds['max_active_credits']}"
            reason = rule['desc']
        elif rule['id'] == 'credit_rating_min':
            rating_index = credit_rating_order.index(ex.credit.credit_rating) if ex.credit.credit_rating in credit_rating_order else -1
            min_rating_index = credit_rating_order.index(thresholds['min_credit_rating'])
            passed = rating_index >= min_rating_index
            value = f"{ex.credit.credit_rating} >= {thresholds['min_credit_rating']}"
            reason = rule['desc']
        elif rule['id'] == 'rejections_max':
            passed = ex.credit.rejections_last_12m <= thresholds['max_rejections_12m']
            value = f"{ex.credit.rejections_last_12m} <= {thresholds['max_rejections_12m']}"
            reason = rule['desc']

        rule_results.append(RuleResult(id=rule['id'], passed=passed, reason=reason, value=value))

    approved = all(r.passed for r in rule_results) if decision_logic == 'all' else any(r.passed for r in rule_results)
    
    risk_score = 1 - (sum(1 for r in rule_results if r.passed) / len(rule_results))

    rationale = [r.reason for r in rule_results if not r.passed]

    return Decision(
        approved=approved,
        rule_results=rule_results,
        rationale=rationale,
        risk_score=risk_score,
        extracted=ex
    )
