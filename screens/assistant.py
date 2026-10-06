import os
import streamlit as st
from openai import OpenAI
from core.finance import ai_context

def render(period, db):
    st.header("🤖 Preguntale a Átomo")
    st.write(
        "Átomo explica, compara escenarios y ayuda a leer los números. "
        "El Electro y los cálculos principales siguen funcionando sin IA."
    )

    if not os.getenv("OPENAI_API_KEY"):
        st.error(
            "No encuentro OPENAI_API_KEY en el proceso que abrió la app. "
            "Esto se puede arreglar en el lanzador; el resto de la aplicación funciona igual."
        )
    else:
        q=st.text_area("Pregunta",height=110,placeholder="Ej.: si adelanto $300.000 de esta deuda, ¿cómo cambia mi margen?")
        if st.button("Consultar",type="primary"):
            if q.strip():
                instructions="""
Sos Átomo, asistente de una app argentina de finanzas personales.
La persona decide. No ejecutes ni presentes ninguna decisión como obligatoria.
Explicá alternativas y tradeoffs de forma clara.
No inventes números. Usá únicamente el contexto suministrado.
El Electro financiero (Liquidez, Solvencia y Flujo) y las sumas fueron calculados de forma determinista por la app: no los reemplaces.
Diferenciá gasto, transferencia propia, compromiso, deuda e inversión.
Si se habla de inversión, aclarar que rendimiento, liquidez y riesgo deben evaluarse juntos.
""".strip()
                try:
                    client=OpenAI(timeout=30, max_retries=1)
                    with st.spinner("Analizando…"):
                        resp=client.responses.create(
                            model=os.getenv("ATOMO_OPENAI_MODEL", "gpt-5-mini"),
                            reasoning={"effort":"low"},
                            instructions=instructions,
                            input=f"DATOS:\n{ai_context(period,db)}\n\nPREGUNTA:\n{q}",
                        )
                    if resp.output_text.strip():
                        st.markdown(resp.output_text)
                    else:
                        st.warning("La IA devolvió una respuesta vacía. Podés intentar otra consulta.")
                except Exception as e:
                    st.error("No pude consultar la IA. Revisá la conexión y la configuración externa. Tus datos y cálculos siguen disponibles.")

# =========================================================
# PAGE: INSTITUCIONES
# =========================================================
