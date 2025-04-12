from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import trafilatura
from lxml import etree

app = FastAPI()

# Libera requisições da extensão local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

    # Extrai conteúdo no formato XML
    extracted_xml = trafilatura.extract(downloaded, output_format='xml', include_images=True)
    if not extracted_xml:
        return HTMLResponse(content="<h1>Erro ao extrair conteúdo</h1>", status_code=500)

    try:
        # Parseia o XML
        tree = etree.fromstring(extracted_xml.encode())

        title = tree.findtext("title", default="Leitura limpa")
        paragraphs = [p.text for p in tree.findall(".//p") if p.text]

    except Exception as e:
        return HTMLResponse(content=f"<h1>Erro ao processar conteúdo</h1><p>{str(e)}</p>", status_code=500)

    return templates.TemplateResponse("reader.html", {
        "request": {},
        "title": title,
        "paragraphs": paragraphs,
        "original_url": req.url
    })
