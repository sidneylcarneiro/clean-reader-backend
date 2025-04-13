from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import trafilatura
from lxml import etree
import requests
from readability import Document

app = FastAPI()

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
    # Primeira tentativa com trafilatura
    downloaded = trafilatura.fetch_url(req.url)
    title = "Leitura limpa"
    paragraphs = []

    if downloaded:
        extracted_xml = trafilatura.extract(downloaded, output_format='xml', include_images=True)
        if extracted_xml:
            try:
                tree = etree.fromstring(extracted_xml.encode())
                title = tree.findtext("title", default=title)
                paragraphs = [p.text for p in tree.findall(".//p") if p.text]
            except Exception as e:
                print("Erro ao parsear XML do Trafilatura:", e)

    # Fallback com readability-lxml se necessário
    if not paragraphs:
        try:
            response = requests.get(req.url, timeout=10)
            doc = Document(response.text)
            title = doc.short_title()
            html_content = doc.summary()

            # Parseia HTML da summary
            parsed = etree.HTML(html_content)
            paragraphs = [el.text for el in parsed.findall(".//p") if el.text]
        except Exception as e:
            return HTMLResponse(content=f"<h1>Erro total ao extrair conteúdo</h1><p>{str(e)}</p>", status_code=500)

    return templates.TemplateResponse("reader.html", {
        "request": {},
        "title": title,
        "paragraphs": paragraphs,
        "original_url": req.url
    })
