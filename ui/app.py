# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import json
import os

# URL base de la API de FastAPI
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="Credit Decision App V2")

st.title("Credit Decision App V2")

tab1, tab2 = st.tabs(["Evaluación Individual", "Procesamiento por Lotes"])

with tab1:
    st.header("Evaluación de Carta Individual")
    
    letter_input = st.text_area("Pega aquí la carta de solicitud de crédito:", height=300)
    
    provider_options = {"Ninguno (Fallback)": None, "Gemini": "gemini", "OpenAI": "openai"}
    selected_provider_name = st.selectbox("Proveedor de Explicación (LLM):", list(provider_options.keys()))
    selected_provider = provider_options[selected_provider_name]

    if st.button("Evaluar Carta"):
        if not letter_input:
            st.warning("Por favor, pega el contenido de la carta para evaluar.")
        else:
            try:
                # Llamada al endpoint /explain de la API
                response = requests.post(f"{API_BASE_URL}/explain", json={
                    "letter": letter_input,
                    "rules_path": "business_rules.yaml", # Asumimos la ruta por defecto
                    "provider": selected_provider
                })
                response.raise_for_status() # Lanza una excepción para códigos de estado HTTP erróneos
                result = response.json()

                st.subheader("Decisión y Explicación")
                col1, col2 = st.columns(2)
                with col1:
                    st.json(result["decision"])
                with col2:
                    st.markdown(f"**Explicación:**\n{result["explanation"]}")
                
                st.subheader("Detalle de Extracción")
                st.json(result["decision"]["extracted"])

                st.subheader("Resultados de Reglas")
                rules_df = pd.DataFrame(result["decision"]["rule_results"])
                st.dataframe(rules_df)

            except requests.exceptions.ConnectionError:
                st.error("Error de conexión: Asegúrate de que el servidor de FastAPI esté corriendo en " + API_BASE_URL)
            except requests.exceptions.RequestException as e:
                st.error(f"Error en la solicitud a la API: {e}")
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")

with tab2:
    st.header("Procesamiento por Lotes")
    st.write("Procesa todas las cartas de la carpeta `examples/` y genera un archivo `decisions.csv`.")

    if st.button("Procesar Carpeta de Ejemplos"):
        try:
            # Leer las cartas de la carpeta examples/ (simulando la CLI)
            # Nota: En una aplicación real, esto se haría a través de un endpoint de la API
            # o se subirían los archivos directamente.
            # Para esta demo, simulamos la lectura local y luego llamamos al batch_decision de la API.
            
            # Primero, leemos los archivos localmente para enviarlos a la API
            letters_data = []
            examples_folder = "examples/"
            if not os.path.exists(examples_folder):
                st.error(f"La carpeta '{examples_folder}' no existe.")
            else:
                for filename in os.listdir(examples_folder):
                    if filename.endswith(".txt"):
                        filepath = os.path.join(examples_folder, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            letters_data.append({"id": filename, "letter": f.read()})
                
                if not letters_data:
                    st.warning(f"No se encontraron archivos .txt en la carpeta '{examples_folder}'.")
                else:
                    st.info(f"Enviando {len(letters_data)} cartas a la API para procesamiento por lotes...")
                    batch_response = requests.post(f"{API_BASE_URL}/batch_decision", json={"items": letters_data,
                    "rules_path": "business_rules.yaml"})
                    batch_response.raise_for_status()
                    batch_result = batch_response.json()

                    if batch_result and "rows" in batch_result:
                        df_results = pd.DataFrame(batch_result["rows"])
                        st.subheader("Resultados del Lote")
                        st.dataframe(df_results)

                        csv_output = df_results.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Descargar decisions.csv",
                            data=csv_output,
                            file_name="decisions.csv",
                            mime="text/csv",
                        )
                        st.success("Procesamiento por lotes completado y archivo listo para descargar.")
                    else:
                        st.error("La API no devolvió resultados válidos para el lote.")

        except requests.exceptions.ConnectionError:
            st.error("Error de conexión: Asegúrate de que el servidor de FastAPI esté corriendo en " + API_BASE_URL)
        except requests.exceptions.RequestException as e:
            st.error(f"Error en la solicitud a la API: {e}")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")
