from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import trafilatura
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Libera requisições da extensão local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, coloque o domínio da extensão
    allow_methods=["POST"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class PageRequest(BaseModel):
    url: str

@app.post("/extract", response_class=HTMLResponse)
async def extract(req: PageRequest):
    downloaded = trafilatura.fetch_url(req.url)
    if downloaded is None:
        return HTMLResponse(content="<h1>Erro ao baixar a página</h1>", status_code=400)

    content = trafilatura.extract(downloaded, include_images=True)
    if content is None:
        return HTMLResponse(content="<h1>Conteúdo não encontrado</h1>", status_code=404)

    # Renderiza em um template simples
    return templates.TemplateResponse("reader.html", {
        "request": {},  # necessário pelo Jinja2Templates
        "content": content,
        "original_url": req.url
    })
