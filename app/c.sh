python -m app.main --letter examples/aprobado.txt --rules business_rules.yaml
python -m app.main --letter examples/rechazado.txt --rules business_rules.yaml
python -m app.main --letter examples/sample_letter.txt --rules business_rules.yaml

python -m app.main --letter examples/Carta1.txt --rules business_rules.yaml

uvicorn app.main:api --reload




Cartas en formatos JSON.

