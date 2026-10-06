import streamlit as st
from core.quick import register, show_recent


def render(period, db):
    st.header('💰 Ingresos')
    register(True, period, db)
    show_recent(period, db, income=True)
