# API
from fastapi import FastAPI
from pydantic import BaseModel
from agent_graph import build_graph

app = FastAPI()
graph = build_graph()

class IdeasRequest(BaseModel):
    topic: str

class GuiaRequest(BaseModel):
    selection: str

@app.post("/ideas/")
def generar_ideas(req: IdeasRequest):
    result = graph.invoke({"mode": "ideas", "topic": req.topic, "selection": "", "output": ""})
    return result

@app.post("/guia/")
def generar_guia(req: GuiaRequest):
    result = graph.invoke({"mode": "instrucciones", "topic": "", "selection": req.selection, "output": ""})
    return result