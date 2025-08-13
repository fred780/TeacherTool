from typing import List, TypedDict, Literal, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun  # pip install langchain-community
from prompts import IDEA_SYSTEM
from prompts import INSTR_SYSTEM
import json

class AgentState(TypedDict):
    """State for the agent graph."""
    mode: Literal["ideas", "instrucciones"]
    topic: str
    selection: str
    output: str
    actividades: List[Dict[str, Any]]  # Titles of activities generated in the first tab
    busqueda_internet: bool  # Whether the ideas were found via internet search
    busqueda_creada: bool  # Whether the ideas were created by the model

def _llm():
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0.4)

def razonar(state: AgentState):
    if state.get("mode") == "instrucciones":
        return {"output": "instrucciones", "actividades": []}
    llm = _llm()
    prompt = (
        f"Analiza el siguiente tema: '{state['topic']}'. "
        "¿Está relacionado estrictamente con actividades educativas? "
        "Responde SOLO con 'valido' si es así, o 'invalido' si no lo es. "
        "Si crees que necesitas buscar información adicional en internet para proponer actividades, responde 'buscar'."
    )
    msg = llm.invoke([HumanMessage(content=prompt)])
    razonamiento = str(msg.content).strip().lower()
    # Guardar el razonamiento en el estado
    return {"output": razonamiento}

def rechazar(state: AgentState):
    return {"output": "Solo puedo responder sobre actividades educativas. Por favor, ajusta tu consulta.", "actividades": []}

def sintetizar(state: AgentState):
    llm = _llm()
    contexto = state.get("output", "")
    prompt = (
        f"Con base en la siguiente información encontrada en internet:\n{contexto}\n"
        "Sintetiza una lista de actividades educativas en formato JSON según el esquema proporcionado."
        "Responde SOLO con el JSON válido según el esquema proporcionado."
    )
    msg = llm.invoke([
        SystemMessage(content=IDEA_SYSTEM),
        HumanMessage(content=prompt)
    ])
    raw = str(msg.content).strip()
    try:
        data = json.loads(raw)
        actividades = data.get("actividades", [])
        assert isinstance(actividades, list) and len(actividades) > 0
        return {
            "output": raw,
            "actividades": actividades,
            "busqueda_internet": True,
            "busqueda_creada": False
        }
    except Exception:
        return {"output": raw, "actividades": [], "busqueda_internet": True, "busqueda_creada": False}

def buscar(state: AgentState):
    consulta = state["topic"]
    # Validación estricta: solo busca si el tema es educativo y contiene "actividad"
    if not consulta or "actividad" not in consulta.lower():
        return {"output": "Solo puedo buscar actividades educativas en internet.", "actividades": []}
    search = DuckDuckGoSearchRun()
    resultados = search.run(consulta)
    return {"output": resultados, "actividades": []}

def idear(state: AgentState):
    llm = _llm()
    msg = llm.invoke([
        SystemMessage(content=IDEA_SYSTEM),
        HumanMessage(content=f"Tema/criterio del docente: {state['topic']}. Responde SOLO con el JSON válido según el esquema proporcionado.")
    ])
    raw = str(msg.content).strip()
    try:
        data = json.loads(raw)
        actividades = data.get("actividades", [])

        assert isinstance(actividades, list) and len(actividades) > 0
        return {
            "output": raw,
            "actividades": actividades,
            "busqueda_creada": True,
            "busqueda_internet": False
        }
    except Exception:
        return {"output": raw, "actividades": [], "busqueda_internet": False, "busqueda_creada": True}


def guiar(state: AgentState):
    llm = _llm()
    actividad= state.get("selection") or state["topic"]
    msg = llm.invoke([
        SystemMessage(content=INSTR_SYSTEM),
        HumanMessage(content=f"Actividad seleccionada: {actividad}")
    ])
    return {"output": msg.content}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("razonar", razonar)
    g.add_node("idear", idear)
    g.add_node("buscar", buscar)
    g.add_node("sintetizar", sintetizar)
    g.add_node("rechazar", rechazar)
    g.add_node("guiar", guiar)

    def route(state: AgentState):
        razonamiento = state.get("output", "")
        if razonamiento == "instrucciones":
            return "guiar"
        if razonamiento == "valido":
            return "idear"
        elif razonamiento == "buscar":
            return "buscar"
        else:
            return "rechazar"

    g.add_edge(START, "razonar")
    g.add_conditional_edges("razonar", route)
    g.add_edge("idear", END)
    g.add_edge("rechazar", END)
    g.add_edge("buscar", "sintetizar")
    g.add_edge("sintetizar", END)
    g.add_edge("guiar", END)
    return g.compile()