from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import trafilatura
from lxml import etree
from bs4 import BeautifulSoup
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
    title = "Leitura limpa"
    rendered_html = None

    # Tenta com Trafilatura
    downloaded = trafilatura.fetch_url(req.url)
    if downloaded:
        content = trafilatura.extract(downloaded, include_images=True, output_format='xml')
        if content:
            try:
                soup = BeautifulSoup(content, 'xml')
                title = soup.find('title').text if soup.find('title') else title
                html_body = soup.find('body')
                if html_body:
                    rendered_html = str(html_body)
            except Exception as e:
                print("Erro ao processar com Trafilatura + BeautifulSoup:", e)

    # Fallback com Readability-lxml
    if not rendered_html:
        try:
            response = requests.get(req.url, timeout=10)
            doc = Document(response.text)
            title = doc.short_title()
            html_content = doc.summary()

            # Repassa o HTML diretamente
            rendered_html = html_content
        except Exception as e:
            return HTMLResponse(content=f"<h1>Erro total ao extrair conteúdo</h1><p>{str(e)}</p>", status_code=500)

    if not rendered_html:
        return HTMLResponse(content="<h1>Conteúdo não encontrado</h1>", status_code=404)

    return templates.TemplateResponse("reader.html", {
        "request": {},
        "title": title,
        "content": rendered_html,
        "original_url": req.url
    })
