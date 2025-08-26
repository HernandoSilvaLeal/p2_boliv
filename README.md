# 📊 Procesador de Solicitudes de Crédito — MVP V1

Este proyecto implementa un **MVP funcional** para la aprobación o rechazo de solicitudes de crédito a partir de **cartas en texto libre**, aplicando **reglas de negocio parametrizadas** en YAML y soportado por **IA generativa (LLM)** con fallback heurístico.

---

## 🚀 Arquitectura del Sistema

El flujo es el siguiente:

**Carta (input)** → **Extractor (LLM o Fallback Regex)** → **Validación (Pydantic)** → **Motor de Reglas (YAML)** → **Decisión (JSON con Aprobado/Rechazado + Rationale + Riesgo)**

![Diagrama de Arquitectura](https://res.cloudinary.com/dqvny6ewr/image/upload/v1756244914/boliv_nqubsj.png)

---

## 📂 Estructura del Proyecto

/
├─ app/
│  ├─ main.py          → CLI + API FastAPI
│  ├─ schema.py        → Modelos Pydantic
│  ├─ llm_extractor.py → Extracción con LLM y Fallback
│  └─ rules.py         → Motor de reglas YAML
├─ examples/
│  ├─ aprobado.txt
│  ├─ rechazado.txt
│  ├─ Carta1.txt … Carta9.txt
│  └─ sample_letter.txt
├─ business_rules.yaml → Reglas de negocio parametrizadas
├─ requirements.txt
├─ .env.example
└─ README.md

---

## ⚙️ Instalación

1. Crear y activar entorno virtual:
`bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
`

2. Instalar dependencias:
`bash
pip install -r requirements.txt
`

3. Configurar variables de entorno:
- Copiar `.env.example` a `.env`
- Definir una sola clave activa:
  - `GOOGLE_API_KEY` y `GOOGLE_MODEL=gemini-1.5-flash`
  - o `OPENAI_API_KEY` y `OPENAI_MODEL=gpt-4o-mini`

---

## 🖥️ Uso por CLI

Ejecutar:
`bash
python -m app.main --letter examples/aprobado.txt --rules business_rules.yaml
python -m app.main --letter examples/rechazado.txt --rules business_rules.yaml
`

Salida esperada:
- **EXTRACCIÓN** (JSON de la carta)
- **REGLAS** (lista con ✅/❌ + razón)
- **DECISIÓN** (Aprobado/Rechazado + Riesgo)

---

## 🌐 Uso por API (Swagger UI)

1. Levantar servidor:
`bash
uvicorn app.main:api --reload
`

2. Abrir en navegador:
http://127.0.0.1:8000/docs

3. Probar endpoints:
- **POST /extract** → Devuelve JSON estructurado
- **POST /decision** → Devuelve decisión (aprobado/rechazado)

Ejemplo payload:
`json
{
  "letter": "Pega aquí el contenido de la carta",
  "rules_path": "business_rules.yaml"
}
`

---

## 📜 Reglas de Negocio (business_rules.yaml)

1. Ingreso mensual > $1.000.000 COP  
2. Sin mora en últimos 6 meses  
3. Edad ≥ 21 años  
4. Monto solicitado ≤ 30% de ingresos  
5. Experiencia ≥ 12 meses  
6. Créditos activos ≤ 2  
7. Calificación ≥ “Buena” (Mala < Regular < Buena < Muy Buena < Excelente)  
8. Rechazos últimos 12 meses ≤ 2  

Decisión: aprobar solo si **todas** las reglas se cumplen (`logic="all"`).

---

## ✅ Estado del Proyecto

- CLI validado con ejemplos **aprobado** y **rechazado**.  
- API Swagger (`/docs`) funcional.  
- Fallback heurístico robusto (años→meses, números en palabras, mora con negación).  
- Reglas parametrizadas en YAML.  
- Listo para demo y explicación técnica.
