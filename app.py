import streamlit as st

from dashboard.chatbot import render_chatbot_section
from dashboard.config import PAGE_ICON, PAGE_LAYOUT, PAGE_TITLE
from dashboard.data import apply_filters, load_data
from dashboard.ui import (
    apply_metric_css,
    render_header,
    render_kpis,
    render_sidebar_filters,
    render_tabs,
)

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=PAGE_LAYOUT)
apply_metric_css()

df = load_data()
filters = render_sidebar_filters(df)
df_filtrado = apply_filters(df, filters)

render_header()
render_kpis(df_filtrado)
st.divider()
render_tabs(df_filtrado)
st.divider()
render_chatbot_section(df_filtrado, filters)