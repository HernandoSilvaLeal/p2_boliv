# -*- coding: utf-8 -*- 
# Importaciones necesarias.
import os
import re
import json
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from app.schema import ApplicationExtract, Applicant, Employment, Financials, CreditProfile

# Carga las variables de entorno desde un archivo .env (si existe).
# Aquí es donde buscará las claves de API.
load_dotenv()

# --- Función Principal de Extracción ---

def extract_with_llm(letter: str) -> ApplicationExtract:
    """Intenta extraer datos usando un LLM (Google o OpenAI) y si falla, usa un fallback de regex."""
    # Lee las claves de API desde las variables de entorno.
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Prioridad 1: Intentar con Google Gemini.
    if google_api_key:
        try:
            # Configura la API de Google.
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel(os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"))
            # El prompt le da al LLM el contexto y la estructura JSON deseada.
            prompt = f"""Extract the following information from the letter below and provide the output in a valid JSON format. 
            The JSON object should conform to the following structure:
            {{'applicant': {{'full_name': 'str', 'age_years': 'int'}}, 'employment': {{'employment_tenure_months': 'int'}}, 'financials': {{'income_monthly': 'int', 'requested_amount': 'int', 'active_credits': 'int'}}, 'credit': {{'has_delinquencies_last_6m': 'bool', 'credit_rating': 'str', 'rejections_last_12m': 'int'}}, 'raw_letter': 'str'}}
            
            Letter:
            {letter}
            """
            response = model.generate_content(prompt)
            # Limpia la respuesta del LLM para asegurar que sea un JSON válido.
            cleaned_response = response.text.strip().replace('`', '').replace('json', '')
            extracted_data = json.loads(cleaned_response)
            extracted_data['raw_letter'] = letter # Añade la carta original a los datos.
            # Valida y estructura los datos usando el modelo Pydantic.
            return ApplicationExtract(**extracted_data)
        except Exception as e:
            print(f"Error with Gemini: {e}")
            # Si algo falla, se llama al método de fallback.
            return extract_with_fallback(letter)

    # Prioridad 2: Si no hay clave de Google, intentar con OpenAI.
    elif openai_api_key:
        try:
            client = openai.OpenAI(api_key=openai_api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            # El prompt es similar, pidiendo una extracción estructurada.
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
            cleaned_response = response.choices[0].message.content.strip().replace('`', '').replace('json', '')
            extracted_data = json.loads(cleaned_response)
            extracted_data['raw_letter'] = letter
            return ApplicationExtract(**extracted_data)
        except Exception as e:
            print(f"Error with OpenAI: {e}")
            return extract_with_fallback(letter)
    
    # Opción final: Si no hay ninguna clave de API, usar directamente el fallback.
    else:
        return extract_with_fallback(letter)

# --- Fallback: Extracción Heurística con Regex ---

def extract_with_fallback(letter: str) -> ApplicationExtract:
    """Extrae datos de la carta usando expresiones regulares (regex).
    
    Este es el motor de extracción offline. Es menos flexible que un LLM pero es determinista y gratuito.
    """
    # Normaliza la carta a minúsculas y quita espacios extra para facilitar la búsqueda de patrones.
    normalized_letter = " ".join(letter.lower().split())
    # Diccionario para convertir números escritos con letra a dígitos.
    word_to_num = {"un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5}

    # Función auxiliar para buscar y limpiar números.
    def find_number(pattern, text, is_money=False):
        match = re.search(pattern, text, re.IGNORECASE) # Busca el patrón sin importar mayúsculas/minúsculas.
        if not match:
            return 0
        
        val = match.group(1) # Obtiene el valor capturado por el paréntesis en el regex.
        if is_money:
            # Si es dinero, elimina puntos y comas (ej. "1.800.000" -> "1800000").
            return int(re.sub(r'[^\d]', '', val))

        if val in word_to_num:
            return word_to_num[val] # Convierte "tres" a 3.
        
        if val.isdigit():
            return int(val) # Convierte "5" a 5.
        
        return 0

    # Aplicación de los patrones de regex para cada campo.
    income = find_number(r"ingresos mensuales.*?([\d\.,]+)", normalized_letter, is_money=True)
    amount = find_number(r"(?:valor|monto) de \$?([\d\.,]+)", normalized_letter, is_money=True)
    age = find_number(r"tengo (\d{2})\s*a[nñ]os", normalized_letter)

    # Lógica para experiencia (más compleja).
    experience_in_months = 0
    # Intenta encontrar "experiencia laboral de 5 años".
    exp_match = re.search(r"experiencia laboral de (\d+|un|uno|dos|tres|cuatro|cinco)\s*a[ñn]o(s)?", normalized_letter)
    if exp_match:
        val = exp_match.group(1)
        years = int(val) if val.isdigit() else word_to_num.get(val, 0)
        experience_in_months = years * 12
    
    # Si no encontró años, busca meses o frases como "menos de un año".
    if experience_in_months == 0:
        months_match = re.search(r"(\d+)\s*mes(es)? de experiencia", normalized_letter)
        if months_match:
            experience_in_months = int(months_match.group(1))
        elif "menos de un año" in normalized_letter or "<12 meses" in normalized_letter:
            experience_in_months = 6 # Asigna un valor por defecto (6 meses).

    active_credits = find_number(r"(\w+) créditos activos", normalized_letter)
    rejections = find_number(r"crédito en (\w+) ocasiones", normalized_letter)
    # Caso especial para "ningún rechazo".
    if re.search(r"no he recibido ning.n rechazo", normalized_letter):
        rejections = 0

    # Lógica de negación para la mora.
    has_delinquencies_last_6m = False
    if "mora" in normalized_letter:
        # Solo es True si "mora" existe Y NO hay una negación ("sin" o "no") cerca.
        if not re.search(r"(sin|no).{0,40}mora", normalized_letter):
            has_delinquencies_last_6m = True

    # Extrae el rating, capitalizando el resultado (ej. "buena" -> "Buena").
    rating_match = re.search(r'calificación de \"(.*?)\"', letter, re.IGNORECASE | re.DOTALL)
    rating = rating_match.group(1).capitalize() if rating_match else "Regular"

    # Extrae el nombre completo.
    full_name_match = re.search(r"Mi nombre es (.*?)[,.]", letter)
    full_name = full_name_match.group(1) if full_name_match else "Unknown"

    # Devuelve el objeto ApplicationExtract, validado por Pydantic.
    return ApplicationExtract(
        applicant=Applicant(full_name=full_name, age_years=age),
        employment=Employment(employment_tenure_months=experience_in_months),
        financials=Financials(income_monthly=income, requested_amount=amount, active_credits=active_credits),
        credit=CreditProfile(has_delinquencies_last_6m=has_delinquencies_last_6m, credit_rating=rating, rejections_last_12m=rejections),
        raw_letter=letter
    )