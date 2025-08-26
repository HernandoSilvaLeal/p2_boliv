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
    def find_number(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return int(re.sub(r'\D', '', match.group(1))) if match else 0

    income = find_number(r"ingresos mensuales ascienden a \$([\d,.]+)", letter)
    amount = find_number(r"solicitar un crédito personal por un (?:valor|monto) de \$([\d,.]+)", letter)
    age = find_number(r"tengo (\d+) años", letter)
    experience = find_number(r"experiencia laboral de (\d+) años", letter) * 12
    active_credits = find_number(r"solo mantengo (\w+) crédito activo", letter)
    if active_credits == 0: # Handle 'un' crédito
        if re.search(r"un crédito activo", letter, re.IGNORECASE):
            active_credits = 1

    rejections = find_number(r"solicitado crédito en (\w+) ocasiones", letter)
    if rejections == 0: # Handle 'tres' ocasiones
        if re.search(r"tres ocasiones", letter, re.IGNORECASE):
            rejections = 3

    mora = bool(re.search(r"crédito en mora", letter, re.IGNORECASE))
    
    rating_match = re.search(r'calificación de "(.*?)"', letter, re.IGNORECASE)
    rating = rating_match.group(1) if rating_match else "Regular"

    full_name_match = re.search(r"Mi nombre es (.*?)[,.]", letter)
    full_name = full_name_match.group(1) if full_name_match else "Unknown"

    return ApplicationExtract(
        applicant=Applicant(full_name=full_name, age_years=age),
        employment=Employment(employment_tenure_months=experience),
        financials=Financials(income_monthly=income, requested_amount=amount, active_credits=active_credits),
        credit=CreditProfile(has_delinquencies_last_6m=mora, credit_rating=rating, rejections_last_12m=rejections),
        raw_letter=letter
    )
