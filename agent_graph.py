from typing import List, TypedDict, Literal, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
import json

class AgentState(TypedDict):
    """State for the agent graph."""
    mode: Literal["ideas", "instrucciones"]
    topic: str
    selection: str
    output: str
    actividades: List[Dict[str, Any]]  # Titles of activities generated in the first tab

def _llm():
    return ChatGroq(model="llama-3.1-8b-instant", temperature=0.4)

def idear(state: AgentState):
    from prompts import IDEA_SYSTEM
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
            "actividades": actividades
        }
    except Exception:
        return {"output": raw, "actividades": []}
    

def guiar(state: AgentState):
    from prompts import INSTR_SYSTEM
    llm = _llm()
    actividad= state.get("selection") or state["topic"]
    msg = llm.invoke([
        SystemMessage(content=INSTR_SYSTEM),
        HumanMessage(content=f"Actividad seleccionada: {actividad}")
    ])
    return {"output": msg.content}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("idear", idear)
    g.add_node("guiar", guiar)

    def route(state: AgentState):
        return "idear" if state["mode"] == "ideas" else "guiar"

    g.add_conditional_edges(START, route)
    g.add_edge("idear", END)
    g.add_edge("guiar", END)
    return g.compile()