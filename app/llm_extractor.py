import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from app.schema import ApplicationExtract, Applicant, Employment, Financials, CreditProfile

load_dotenv()

def extract_with_llm(letter: str) -> ApplicationExtract:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if google_api_key:
        try:
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel(os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"))
            prompt = f"""Extract the following information from the letter below and provide the output in a valid JSON format. 
            The JSON object should conform to the following structure:
            {{'applicant': {{'full_name': 'str', 'age_years': 'int'}}, 'employment': {{'employment_tenure_months': 'int'}}, 'financials': {{'income_monthly': 'int', 'requested_amount': 'int', 'active_credits': 'int'}}, 'credit': {{'has_delinquencies_last_6m': 'bool', 'credit_rating': 'str', 'rejections_last_12m': 'int'}}, 'raw_letter': 'str'}}
            
            Letter:
            {letter}
            """
            response = model.generate_content(prompt)
            # Clean the response to ensure it is valid JSON
            cleaned_response = response.text.strip().replace('`', '').replace('json', '')
            extracted_data = json.loads(cleaned_response)
            extracted_data['raw_letter'] = letter
            return ApplicationExtract(**extracted_data)
        except Exception as e:
            print(f"Error with Gemini: {e}")
            # Fallback to regex if LLM fails
            return extract_with_fallback(letter)

    elif openai_api_key:
        try:
            client = openai.OpenAI(api_key=openai_api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            prompt = f"""Extract the following information from the letter below and provide the output in a valid JSON format. 
            The JSON object should conform to the following structure:
            {{'applicant': {{'full_name': 'str', 'age_years': 'int'}}, 'employment': {{'employment_tenure_months': 'int'}}, 'financials': {{'income_monthly': 'int', 'requested_amount': 'int', 'active_credits': 'int'}}, 'credit': {{'has_delinquencies_last_6m': 'bool', 'credit_rating': 'str', 'rejections_last_12m': 'int'}}, 'raw_letter': 'str'}}
            
            Letter:
            {letter}
            """
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            # Clean the response to ensure it is valid JSON
            cleaned_response = response.choices[0].message.content.strip().replace('`', '').replace('json', '')
            extracted_data = json.loads(cleaned_response)
            extracted_data['raw_letter'] = letter
            return ApplicationExtract(**extracted_data)
        except Exception as e:
            print(f"Error with OpenAI: {e}")
            # Fallback to regex if LLM fails
            return extract_with_fallback(letter)
    else:
        # Fallback to regex if no API key is provided
        return extract_with_fallback(letter)

def extract_with_fallback(letter: str) -> ApplicationExtract:
    # Heuristic extraction using regex
    normalized_letter = " ".join(letter.lower().split())
    word_to_num = {"un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5}

    def find_number(pattern, text, is_money=False):
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return 0
        
        val = match.group(1)
        if is_money:
            return int(re.sub(r'[^\d]', '', val))

        if val in word_to_num:
            return word_to_num[val]
        
        if val.isdigit():
            return int(val)
        
        return 0

    income = find_number(r"ingresos mensuales.*?([\d\.,]+)", normalized_letter, is_money=True)
    amount = find_number(r"(?:valor|monto) de \$?([\d\.,]+)", normalized_letter, is_money=True)
    age = find_number(r"tengo (\d{2})\s*a[nñ]os", normalized_letter)

    # Experience
    experience_in_months = 0
    exp_match = re.search(r"experiencia laboral de (\d+|un|uno|dos|tres|cuatro|cinco)\s*a[ñn]o(s)?", normalized_letter)
    if exp_match:
        val = exp_match.group(1)
        years = int(val) if val.isdigit() else word_to_num.get(val, 0)
        experience_in_months = years * 12
    
    if experience_in_months == 0:
        months_match = re.search(r"(\d+)\s*mes(es)? de experiencia", normalized_letter)
        if months_match:
            experience_in_months = int(months_match.group(1))
        elif "menos de un año" in normalized_letter or "<12 meses" in normalized_letter:
            experience_in_months = 6 # less than a year


    # Active Credits
    active_credits = find_number(r"(\w+) créditos activos", normalized_letter)

    # Rejections
    rejections = find_number(r"crédito en (\w+) ocasiones", normalized_letter)
    if re.search(r"no he recibido ning.n rechazo", normalized_letter):
        rejections = 0

    # Delinquencies
    has_delinquencies_last_6m = False
    if "mora" in normalized_letter:
        if not re.search(r"(sin|no).{0,40}mora", normalized_letter):
            has_delinquencies_last_6m = True

    # Rating
    rating_match = re.search(r'calificación de \"(.*?)\"', letter, re.IGNORECASE | re.DOTALL)
    rating = rating_match.group(1).capitalize() if rating_match else "Regular"

    # Full Name
    full_name_match = re.search(r"Mi nombre es (.*?)[,.]", letter)
    full_name = full_name_match.group(1) if full_name_match else "Unknown"

    return ApplicationExtract(
        applicant=Applicant(full_name=full_name, age_years=age),
        employment=Employment(employment_tenure_months=experience_in_months),
        financials=Financials(income_monthly=income, requested_amount=amount, active_credits=active_credits),
        credit=CreditProfile(has_delinquencies_last_6m=has_delinquencies_last_6m, credit_rating=rating, rejections_last_12m=rejections),
        raw_letter=letter
    )
