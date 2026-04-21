import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.config import ALL_DAYS, RAPPI_COLOR, RAPPI_LOGO_URL
from dashboard.data import FilterState


def apply_metric_css() -> None:
    st.markdown(
        """
<style>
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        color: black;
    }
</style>
""",
        unsafe_allow_html=True,
    )


def render_sidebar_filters(df: pd.DataFrame) -> FilterState:
    with st.sidebar:
        st.image(RAPPI_LOGO_URL, width=150)
        st.markdown("### Panel de Filtros")
        if st.button("Reiniciar filtros", use_container_width=True):
            for key in ("filtro_fechas", "filtro_dias", "filtro_horas"):
                st.session_state.pop(key, None)
            st.rerun()

        min_date = df["Fecha"].min().date()
        max_date = df["Fecha"].max().date()
        fechas = st.slider(
            "Rango de fechas:",
            min_date,
            max_date,
            (min_date, max_date),
            key="filtro_fechas",
        )

        dias_seleccionados = st.multiselect(
            "Días de la semana:",
            ALL_DAYS,
            default=ALL_DAYS,
            key="filtro_dias",
        )
        rango_horas = st.slider(
            "Rango de Horas (0-23):",
            0,
            23,
            (0, 23),
            key="filtro_horas",
        )

    return FilterState(
        start_date=fechas[0],
        end_date=fechas[1],
        selected_days=dias_seleccionados,
        start_hour=rango_horas[0],
        end_hour=rango_horas[1],
    )


def render_header() -> None:
    st.title("Monitoreo de Disponibilidad de Tiendas")
    st.markdown("Analítica histórica e identificación de incidentes de plataforma impulsado por IA.")


def _safe_metric_values(df: pd.DataFrame) -> tuple[int, int, int, int]:
    if df.empty:
        return 0, 0, 0, 0
    return (
        int(df["Tiendas_Disponibles"].mean()),
        int(df["Tiendas_Disponibles"].max()),
        int(df["Tiendas_Disponibles"].min()),
        len(df),
    )


def render_kpis(df_filtrado: pd.DataFrame) -> None:
    promedio, maximo, minimo, registros = _safe_metric_values(df_filtrado)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Promedio Visibles", f"{promedio:,}")
    with col2:
        st.metric("Pico Máximo", f"{maximo:,}")
    with col3:
        st.metric("Punto más bajo", f"{minimo:,}")
    with col4:
        st.metric("Registros Analizados", f"{registros:,}")


def render_tabs(df_filtrado: pd.DataFrame) -> None:
    tab1, tab2, tab3 = st.tabs(
        ["Serie de Tiempo", "Análisis Horario y Días", "Tabla de Incidentes-Caídas"]
    )

    with tab1:
        st.subheader("Evolución temporal de la disponibilidad")
        fig_line = px.line(
            df_filtrado,
            x="Fecha",
            y="Tiendas_Disponibles",
            color_discrete_sequence=[RAPPI_COLOR],
        )
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("Promedio por Hora del Día")
            df_hora = df_filtrado.groupby("Hora")["Tiendas_Disponibles"].mean().reset_index()
            fig_bar1 = px.bar(
                df_hora,
                x="Hora",
                y="Tiendas_Disponibles",
                color="Tiendas_Disponibles",
                color_continuous_scale="Reds",
            )
            fig_bar1.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar1, use_container_width=True)

        with col_chart2:
            st.subheader("Promedio por Día de la Semana")
            df_dias = df_filtrado.groupby("Dia_Semana")["Tiendas_Disponibles"].mean().reset_index()
            df_dias["Orden"] = df_dias["Dia_Semana"].map({d: i for i, d in enumerate(ALL_DAYS)})
            df_dias = df_dias.sort_values("Orden")

            fig_bar2 = px.bar(
                df_dias,
                x="Dia_Semana",
                y="Tiendas_Disponibles",
                color_discrete_sequence=[RAPPI_COLOR],
            )
            fig_bar2.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar2, use_container_width=True)

    with tab3:
        st.subheader("Top 20 Momentos Críticos con Posibles Incidentes")
        st.markdown(
            "Muestra los registros con la menor cantidad de tiendas disponibles, "
            "indicando posibles fallas en el sistema o cierres masivos."
        )
        df_peores = df_filtrado.sort_values("Tiendas_Disponibles", ascending=True).head(20)
        st.dataframe(
            df_peores[["Fecha", "Dia_Semana", "Hora", "Tiendas_Disponibles"]],
            use_container_width=True,
            hide_index=True,
        )