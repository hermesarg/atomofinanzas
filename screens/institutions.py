from core.clock import today as local_today, local_now
import sqlite3
from datetime import datetime
import streamlit as st
from core.config import TIPOS_INSTITUCION
from core.database import con, institutions_df

def render(period, db):
    st.header("🏛️ Instituciones")
    st.write(
        "El catálogo es abierto. Las instituciones sugeridas sirven como atajo: podés sumar cualquier banco, "
        "billetera, broker/ALyC, exchange o plataforma que uses. No es obligatorio usar una institución del listado."
    )
    with st.expander("➕ Agregar institución"):
        with st.form("inst_form",clear_on_submit=False):
            typ=st.selectbox("Tipo",TIPOS_INSTITUCION)
            name=st.text_input("Nombre *")
            source=st.text_input("Fuente / referencia",placeholder="BCRA, CNV, manual…")
            if st.form_submit_button("Agregar"):
                if name.strip():
                    try:
                        with con(db) as cdb:
                            cdb.execute("""
                            INSERT INTO instituciones(tipo,nombre,fuente,activa,creada_en)
                            VALUES (?,?,?,1,?)
                            """,(typ,name.strip(),source or "Manual",local_now().isoformat(timespec="seconds")))
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("Ya existe.")

                else:
                    st.error("Falta el nombre de la institución.")

    search=st.text_input("Buscar")
    inst=institutions_df(db)
    if search:
        inst=inst[inst["nombre"].str.contains(search,case=False,na=False,regex=False)]
    st.dataframe(inst[["tipo","nombre","fuente"]],width="stretch",hide_index=True,height=520)

# =========================================================
# PAGE: CONFIGURACIÓN
# =========================================================
