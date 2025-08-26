python -m app.main --letter examples/aprobado.txt --rules business_rules.yaml
python -m app.main --letter examples/rechazado.txt --rules business_rules.yaml
python -m app.main --letter examples/sample_letter.txt --rules business_rules.yaml

python -m app.main --letter examples/Carta1.txt --rules business_rules.yaml

uvicorn app.main:api --reload



**************************************
POST
/extract
Extract

Cartas en formatos JSON.

{
  "letter": "Banco Unión\nÁrea de Originación de Crédito\n\nReferencia: Crédito de nómina — Monto $115.258.777 — Plazo 12 meses\n\nReciban un cordial saludo. Soy María Castro López (Cédula de ciudadanía 535901256). Trabajo como analista, con ingresos aproximados de $7.860.000 mensuales. Solicito la evaluación y desembolso de un Crédito de nómina por $115.258.777 para cubrir gastos médicos.\n\nInformación adicional:\n\nEstado civil: soltero(a)\n\nCiudad: Cali\n\nObligaciones actuales: ninguna\n\nSoportes enviados: RUT, paz y salvo, extractos bancarios, declaración de renta\n\nContacto: 3962458591 / maria.castro.lopez755@gmail.com\n\nGracias por su atención y respuesta oportuna.",
  "rules_path": "business_rules.yaml"
}


{
  "letter": "Bogotá, 2025-01-12\n\nSeñores\nDepartamento de Créditos — Banco del Centro\n\nAsunto: Solicitud de Crédito de vehículo\n\nRespetados señores:\n\nYo, Andrés Ramírez González, identificado con Cédula de ciudadanía No. 1045896325, de estado civil casado y con ocupación de ingeniero, me permito solicitar la aprobación de un Crédito de vehículo por un monto de $48.320.000, a un plazo de 36 meses. Declaro ingresos mensuales promedio por $6.540.000 y una antigüedad laboral de 8 años.\n\nMotivo de la solicitud: adquisición de un vehículo usado para transporte familiar.\n\nRelación de obligaciones vigentes: tarjeta de crédito con cupo moderado. Califico mi historial como bueno.\n\nAdjunto: certificado laboral, desprendibles de pago y paz y salvo.\nAgradezco su amable gestión y quedo atento a cualquier validación adicional.\n\nAtentamente,\n\nAndrés Ramírez González\nBogotá — Tel: 3145298745 — Email: andres.ramirez.gonzalez247@gmail.com\n\nCanal de envío: correo electrónico",
  "rules_path": "business_rules.yaml"
}


{
  "letter": "Bogotá, 2025-08-26\n\nSeñores\nBanco Unión\nDepartamento de Créditos\n\nAsunto: Solicitud de Crédito de libre inversión\n\nRespetados señores:\n\nYo, Camila Torres Rodríguez, identificada con Cédula de ciudadanía No. 1.029.854.321, residente en Bogotá, de 28 años de edad, me permito solicitar la aprobación de un Crédito de libre inversión por valor de $2.400.000 COP, a un plazo de 12 meses.\n\nDeclaro los siguientes aspectos para su evaluación:\n\nMis ingresos mensuales promedio ascienden a $8.000.000 COP, lo cual supera el requisito mínimo.\n\nNo presento créditos en mora en los últimos 6 meses.\n\nCuento con 5 años de experiencia laboral en el área de consultoría empresarial.\n\nEl monto solicitado corresponde al 30% de mis ingresos mensuales, en cumplimiento con la política de endeudamiento.\n\nActualmente tengo 2 créditos activos, todos al día.\n\nMi calificación crediticia actual es “Muy Buena”.\n\nEn los últimos 12 meses no he tenido rechazos de crédito.\n\nAdjunto copia de mi cédula, certificado laboral y extractos bancarios como soportes.\n\nAgradezco su atención y quedo atenta a su respuesta.\n\nAtentamente,\n\nCamila Torres Rodríguez\nTel: 3156789432 — Email: camila.torres.rodriguez215@gmail.com",
  "rules_path": "business_rules.yaml"
}


{
  "letter": "Medellín, 2025-08-26\n\nSeñores\nBanco Andino\nDepartamento de Créditos\n\nAsunto: Solicitud de Crédito Educativo\n\nRespetados señores:\n\nYo, Juan Esteban Ramírez López, identificado con Cédula de ciudadanía No. 1.045.326.987, residente en Medellín, de 32 años de edad, solicito la aprobación de un Crédito Educativo por valor de $3.000.000 COP, a un plazo de 18 meses.\n\nDeclaro los siguientes aspectos:\n\nMis ingresos mensuales son de $10.500.000 COP, cumpliendo con el mínimo requerido.\n\nNo tengo créditos en mora en los últimos 6 meses.\n\nPoseo 7 años de experiencia laboral como ingeniero de software en una empresa multinacional.\n\nEl monto solicitado representa menos del 30% de mis ingresos mensuales.\n\nActualmente cuento con un crédito activo totalmente al día.\n\nMi calificación crediticia es “Excelente”.\n\nNo he tenido rechazos de crédito en los últimos 12 meses.\n\nAdjunto copia de mi cédula, certificado laboral, declaración de renta y extractos bancarios.\n\nAtentamente,\n\nJuan Esteban Ramírez López\nTel: 3125468795 — Email: juan.ramirez.lopez312@gmail.com",
  "rules_path": "business_rules.yaml"
}


{
  "letter": "Cali, 2025-08-26\n\nSeñores\nBanco Continental\nDepartamento de Créditos\n\nAsunto: Solicitud de Microcrédito\n\nRespetados señores:\n\nYo, Diana Marcela Gómez Castaño, identificada con Cédula de ciudadanía No. 1.083.452.119, residente en Cali, con 27 años de edad, solicito respetuosamente la aprobación de un Microcrédito por valor de $1.800.000 COP, a un plazo de 12 meses.\n\nDeclaro lo siguiente para su consideración:\n\nMis ingresos mensuales son de $6.200.000 COP, superiores al mínimo requerido.\n\nNo presento créditos en mora en los últimos 6 meses.\n\nTengo 3 años de experiencia como comerciante independiente.\n\nEl valor solicitado es menor al 30% de mis ingresos mensuales.\n\nActualmente poseo 2 créditos activos, ambos al día.\n\nMi calificación crediticia se encuentra en nivel “Buena”.\n\nEn los últimos 12 meses no he tenido rechazos de crédito.\n\nAdjunto copia de mi cédula, RUT y extractos bancarios como soporte.\n\nAtentamente,\n\nDiana Marcela Gómez Castaño\nTel: 3164892750 — Email: diana.gomez.castaño876@gmail.com",
  "rules_path": "business_rules.yaml"
}



{
  "letter": "Bogotá, 2025-08-26\n\nSeñores\nBanco del Centro\nDepartamento de Créditos\n\nAsunto: Solicitud de Crédito de vehículo\n\nRespetados señores:\n\nYo, Felipe Andrés Rodríguez Muñoz, identificado con Cédula de ciudadanía No. 1.024.589.654, residente en Bogotá, de 29 años de edad, solicito la aprobación de un Crédito de vehículo por valor de $4.200.000 COP, a un plazo de 24 meses.\n\nDeclaro los siguientes aspectos:\n\nMis ingresos mensuales son de $14.500.000 COP, cumpliendo ampliamente con el mínimo exigido.\n\nNo presento reportes de mora en los últimos 6 meses.\n\nTengo 5 años de experiencia laboral como administrador de proyectos.\n\nEl monto solicitado equivale a menos del 30% de mis ingresos mensuales.\n\nActualmente tengo 1 crédito activo, en estado vigente y al día.\n\nMi calificación crediticia es “Muy Buena”.\n\nNo presento rechazos de crédito en los últimos 12 meses.\n\nAdjunto copia de la cédula, certificado laboral, desprendibles de nómina y extractos bancarios.\n\nAtentamente,\n\nFelipe Andrés Rodríguez Muñoz\nTel: 3146792580 — Email: felipe.rodriguez.munoz321@gmail.com",
  "rules_path": "business_rules.yaml"
}


{
  "letter": "Pereira, 2025-08-26\n\nSeñores\nBanco Unión\nDepartamento de Créditos\n\nAsunto: Solicitud de Crédito de libre inversión\n\nRespetados señores:\n\nYo, Karen Juliana Salazar Hoyos, identificada con Cédula de ciudadanía No. 1.052.874.963, residente en Pereira, de 34 años de edad, solicito la aprobación de un Crédito de libre inversión por valor de $2.700.000 COP, a un plazo de 18 meses.\n\nDeclaro lo siguiente:\n\nMis ingresos mensuales son de $9.000.000 COP, cumpliendo el requisito mínimo.\n\nNo tengo créditos en mora en los últimos 6 meses.\n\nSoy propietaria de un negocio de confecciones con 6 años de experiencia.\n\nEl monto solicitado no supera el 30% de mis ingresos mensuales.\n\nActualmente poseo 2 créditos activos, ambos al día.\n\nMi calificación crediticia es “Buena”.\n\nNo he tenido rechazos de crédito en los últimos 12 meses.\n\nAdjunto copia de mi cédula, RUT, estados financieros y extractos bancarios.\n\nAtentamente,\n\nKaren Juliana Salazar Hoyos\nTel: 3174528960 — Email: karen.salazar.hoyos582@gmail.com",
  "rules_path": "business_rules.yaml"
}



{
  "letter": "Barranquilla, 2025-08-26\n\nSeñores\nBanco Andino\nDepartamento de Créditos\n\nAsunto: Solicitud de Crédito de vivienda\n\nRespetados señores:\n\nYo, Luis Fernando Cabrera Méndez, identificado con Cédula de ciudadanía No. 79.452.316, residente en Barranquilla, de 45 años de edad, solicito la aprobación de un Crédito de vivienda por valor de $6.000.000 COP, a un plazo de 24 meses.\n\nDeclaro lo siguiente para su evaluación:\n\nMis ingresos mensuales ascienden a $20.000.000 COP, cumpliendo el mínimo requerido.\n\nNo tengo créditos en mora en los últimos 6 meses.\n\nCuento con 15 años de experiencia laboral como gerente comercial.\n\nEl monto solicitado corresponde al 30% de mis ingresos mensuales.\n\nActualmente tengo 1 crédito activo, al día.\n\nMi calificación crediticia se encuentra en nivel “Excelente”.\n\nEn los últimos 12 meses no he tenido rechazos de crédito.\n\nAdjunto copia de la cédula, certificado laboral, declaración de renta y extractos bancarios.\n\nAtentamente,\n\nLuis Fernando Cabrera Méndez\nTel: 3185479632 — Email: luis.cabrera.mendez741@gmail.com",
  "rules_path": "business_rules.yaml"
}



{
  "letter": "Bucaramanga, 2025-08-26\n\nSeñores\nBanco Continental\nDepartamento de Créditos\n\nAsunto: Solicitud de Microcrédito\n\nRespetados señores:\n\nYo, Sebastián Morales Duarte, identificado con Cédula de ciudadanía No. 1.064.589.742, residente en Bucaramanga, de 26 años de edad, solicito la aprobación de un Microcrédito por valor de $2.100.000 COP, a un plazo de 12 meses.\n\nDeclaro lo siguiente:\n\nMis ingresos mensuales son de $7.200.000 COP, superiores al mínimo exigido.\n\nNo tengo créditos en mora en los últimos 6 meses.\n\nSoy trabajador independiente con 3 años de experiencia en un negocio propio de mensajería.\n\nEl monto solicitado representa menos del 30% de mis ingresos mensuales.\n\nActualmente tengo 1 crédito activo, al día.\n\nMi calificación crediticia es “Muy Buena”.\n\nEn los últimos 12 meses no he tenido rechazos de crédito.\n\nAdjunto copia de mi cédula, RUT y extractos bancarios como soportes.\n\nAtentamente,\n\nSebastián Morales Duarte\nTel: 3157986420 — Email: sebastian.morales.duarte987@gmail.com",
  "rules_path": "business_rules.yaml"
}





****************************************************
