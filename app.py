import os
import re
import streamlit as st
from dotenv import load_dotenv
from agent_graph import build_graph

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    st.error("Please set the GROQ_API_KEY in the .env file.")
    st.stop()

st.set_page_config(page_title="TeacherTool", page_icon=":book:", layout="centered")
st.title("TeacherTool: Asistente Pedagógico")
st.caption("Asistente para docentes de preescolar de niveles entre 3-6 años.")

#Initial state
if "actividades" not in st.session_state:
    st.session_state["actividades"] = []
if "ideas_raw" not in st.session_state:
    st.session_state["ideas_raw"] = ""


graph = build_graph()
tab1, tab2 = st.tabs(["Idear actividades", "Guía paso a paso"])

with tab1:
    st.write("Ingresa un tema/objetivo/restricción para la actividad:")
    st.header("Idear actividades")
    topic = st.text_input("Tema/criterio del docente:", placeholder="colores y movimiento en 15 minutos, sin pantallas.")
    if st.button("Generar ideas", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Por favor ingresa un tema válido.")
        else:
            with st.spinner("Generando ideas..."):
                result = graph.invoke({"mode": "ideas", "topic": topic, "selection": "", "output": ""})
            st.session_state.actividades = result.get("actividades", [])
            st.session_state.ideas_raw = result.get("output", "")

            
    # show formatted result
    if st.session_state.actividades:
        st.success("Ideas generadas con éxito. Ahora puedes ir a la pestaña 'Guía paso a paso' para seleccionar una actividad.")
        for i, act in enumerate(st.session_state.actividades, start=1):
            with st.expander(f"{i}. {act.get('nombre', '(sin nombre)')}"):
               st.markdown(f"**Habilidad:** {act.get('habilidad', '-')}")
               st.markdown(f"**Duración (min):** {act.get('duracion', '-')}")
               mats = act.get("materiales", [])
               if mats: st.markdown(f"**Materiales:** {', '.join(mats)}")
               vars = act.get("variables", [])
               if vars: st.markdown(f"**Variables:**\n- " + "\n- ".join(vars))
               adaps = act.get("adaptaciones", [])
               if adaps: st.markdown(f"**Adaptaciones:**\n- " + "\n- ".join(adaps))
               inds = act.get("indicadores_exito", [])
               if inds: st.markdown(f"**Indicadores:**\n- " + "\n- ".join(inds))
               nota = act.get("nota_seguridad", "")
               if nota: st.markdown(f"**Nota de seguridad:** {nota}")
    elif st.session_state.ideas_raw:
        st.warning("No se pudo estructurar la información.")
        st.code(st.session_state.ideas_raw, language="json")

with tab2:
    st.header("Guía paso a paso")
    if not st.session_state.actividades:
        st.warning("Por favor genera ideas en la pestaña 'Idear actividades' primero.")
    else:
        selection = st.selectbox("Selecciona una actividad:", [act.get("nombre", "(sin nombre)") for act in st.session_state.actividades], index=0)
        selected_activity = next((act for act in st.session_state.actividades if act.get("nombre") == selection), None)
        
        if selected_activity:
            if st.button("Generar guía", type="primary", use_container_width=True):
                with st.spinner("Generando guía..."):
                    result = graph.invoke({"mode": "instrucciones", "topic": "", "selection": selection, "output": ""})
                st.markdown(result["output"])
        else:
            st.error("Por favor selecciona una actividad válida.")

st.divider()
