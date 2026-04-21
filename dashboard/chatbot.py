import os
import re

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_float import float_css_helper, float_init

from dashboard.data import FilterState

load_dotenv()
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _render_chat_history(container) -> None:
    with container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def _build_hidden_context(prompt: str, filters: FilterState) -> str:
    dias = ", ".join(filters.selected_days) if filters.selected_days else "Ninguno"
    return f"""
INSTRUCCIONES DE ESTILO PARA EL ASISTENTE:
- Usa un tono claro, directo y poco técnico.
- Responde de forma concisa (entre 3 y 6 líneas normalmente).
- Evita jerga innecesaria; si usas un término técnico, explícalo en palabras simples.
- Enfócate en conclusiones accionables para perfiles técnicos y no técnicos.

IMPORTANTE PARA EL ASISTENTE:
El usuario está viendo un dashboard filtrado con los siguientes parámetros:
- Rango de fechas: desde {filters.start_date} hasta {filters.end_date}
- Días seleccionados: {dias}
- Rango horario: de {filters.start_hour}:00 a {filters.end_hour}:00.

Responde a la siguiente pregunta del usuario basándote en este contexto.
Pregunta del usuario: {prompt}
"""


def _build_dataset_stats(df_filtrado: pd.DataFrame) -> str:
    if df_filtrado.empty:
        return (
            "ESTADÍSTICAS DEL DATASET FILTRADO:\n"
            "- Total de registros: 0\n"
            "- No hay datos para calcular mínimos, máximos o promedios."
        )

    min_fecha = df_filtrado["Fecha"].min()
    max_fecha = df_filtrado["Fecha"].max()
    serie = df_filtrado["Tiendas_Disponibles"]
    p25 = float(serie.quantile(0.25))
    p50 = float(serie.quantile(0.50))
    p75 = float(serie.quantile(0.75))

    return (
        "ESTADÍSTICAS DEL DATASET FILTRADO:\n"
        f"- Total de registros: {len(df_filtrado)}\n"
        f"- Fecha mínima real en los datos: {min_fecha}\n"
        f"- Fecha máxima real en los datos: {max_fecha}\n"
        f"- Tiendas disponibles (mín/prom/max): {int(serie.min())}/{int(serie.mean())}/{int(serie.max())}\n"
        f"- Percentiles (P25/P50/P75): {p25:.2f}/{p50:.2f}/{p75:.2f}"
    )


def _extract_text_payload(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        text_chunks = []
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                text_chunks.append(item["text"])
            elif isinstance(item, str):
                text_chunks.append(item)
        return "\n".join(text_chunks).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("output"), str):
            return value["output"]
    return str(value)


def _is_invalid_answer(answer: str) -> bool:
    suspicious_markers = (
        "OUTPUT_PARSING_FAILURE",
        "Could not parse LLM output",
        "{'type': 'text'",
        '"type": "text"',
        "signature",
    )
    return (not answer.strip()) or any(marker in answer for marker in suspicious_markers)


def _format_chat_exception(error: Exception) -> str:
    raw_error = str(error)
    upper_error = raw_error.upper()

    if "RESOURCE_EXHAUSTED" in upper_error or "429" in raw_error:
        retry_match = re.search(r"retry in ([0-9.]+)s", raw_error, re.IGNORECASE)
        retry_hint = f" Reintenta en ~{retry_match.group(1)}s." if retry_match else ""
        return (
            "Se alcanzó el límite de uso de Gemini para este proyecto (cuota)."
            f"{retry_hint}\n\n"
            "Opciones rápidas:\n"
            "- Esperar y volver a intentar.\n"
            "- Cambiar `GEMINI_MODEL` en `.env` por un modelo con más capacidad.\n"
            "- Revisar límites/facturación de la API en Google AI Studio."
        )

    return (
        "No pude procesar la consulta en este momento. "
        "Intenta nuevamente con una pregunta más corta o en unos segundos."
    )


def _get_chat_response(prompt: str, df_filtrado: pd.DataFrame, filters: FilterState) -> str:
    if not os.getenv("GOOGLE_API_KEY"):
        return "Falta GOOGLE_API_KEY. Añádela en el archivo .env."

    try:
        model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        agent = create_pandas_dataframe_agent(
            llm,
            df_filtrado,
            agent_type="tool-calling",
            verbose=False,
            allow_dangerous_code=True,
            agent_executor_kwargs={"handle_parsing_errors": True},
        )

        contexto_base = _build_hidden_context(prompt, filters)
        contexto_stats = _build_dataset_stats(df_filtrado)
        contexto_oculto = f"{contexto_base}\n\n{contexto_stats}"

        with st.spinner("Analizando datos..."):
            try:
                response = agent.invoke({"input": contexto_oculto})
                respuesta_texto = _extract_text_payload(response.get("output", ""))
            except Exception:
                respuesta_texto = ""

            if _is_invalid_answer(respuesta_texto):
                fallback_prompt = (
                    f"{contexto_oculto}\n\n"
                    "Si no necesitas ejecutar herramientas, responde directamente en texto plano."
                )
                fallback_response = llm.invoke(fallback_prompt)
                respuesta_texto = _extract_text_payload(fallback_response.content)

            if _is_invalid_answer(respuesta_texto):
                respuesta_texto = (
                    "No pude generar una respuesta clara en este intento. "
                    "Prueba reformular la pregunta en una frase corta y específica."
                )
            return respuesta_texto
    except Exception as e:
        return _format_chat_exception(e)


def render_chatbot_section(df_filtrado: pd.DataFrame, filters: FilterState) -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    float_init(theme=True)
    st.markdown(
        """
        <style>
            div[data-testid="stFloatingElementContainer"] button[kind="secondary"] {
                border-radius: 12px !important;
                border: 1px solid #3b475f !important;
                background: #111827 !important;
                color: #f9fafb !important;
            }
            div[data-testid="stFloatingElementContainer"] input {
                background: #0f172a !important;
                color: #f8fafc !important;
                border: 1px solid #334155 !important;
            }
            div[data-testid="stFloatingElementContainer"] [data-testid="stChatMessage"] {
                background: rgba(15, 23, 42, 0.85) !important;
                border: 1px solid rgba(71, 85, 105, 0.55) !important;
                border-radius: 10px !important;
                padding: 8px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.chat_open:
        launcher = st.container()
        with launcher:
            if st.button("...", key="open_chat_widget", help="Abrir asistente", use_container_width=True):
                st.session_state.chat_open = True
                st.rerun()
        launcher.float(
            float_css_helper(
                width="64px",
                bottom="24px",
                right="24px",
                z_index="9999",
                background="#111827",
                border="1px solid #374151",
                shadow="0 10px 30px rgba(0,0,0,0.45)",
                css="border-radius: 999px; padding: 6px;",
            )
        )
        return

    panel = st.container()
    with panel:
        st.markdown("### Asistente IA")
        col_title, col_min = st.columns([0.8, 0.2])
        with col_title:
            st.caption("Respuestas simples y accionables según tus filtros.")
        with col_min:
            if st.button("—", key="minimize_chat_widget", help="Minimizar", use_container_width=True):
                st.session_state.chat_open = False
                st.rerun()

        history = st.container(height=280)
        _render_chat_history(history)

        with st.form("floating_chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "Pregunta",
                placeholder="Pregunta lo que quieras sobre los datos",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Enviar", use_container_width=True)

        if submitted and prompt.strip():
            user_prompt = prompt.strip()
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            respuesta_texto = _get_chat_response(user_prompt, df_filtrado, filters)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
            st.rerun()

    panel.float(
        float_css_helper(
            width="430px",
            bottom="24px",
            right="24px",
            z_index="9998",
            background="#0b1220",
            border="1px solid #334155",
            shadow="0 24px 50px rgba(0,0,0,0.50)",
            css="border-radius: 14px; padding: 12px; color: #e2e8f0;",
        )
    )