"""
스미싱 탐지 시스템 FastAPI 서버
실행: python app.py  →  http://localhost:8000
UI 편집: templates/index.html
"""
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pipeline

app = FastAPI(title="스미싱 탐지 시스템", version="1.0.0")
TEMPLATE = pathlib.Path(__file__).parent / "templates" / "index.html"


class ScanRequest(BaseModel):
    text: str


@app.post("/scan")
async def scan(req: ScanRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="문자 내용을 입력하세요.")
    if len(req.text) > 2000:
        raise HTTPException(status_code=400, detail="2000자 이하로 입력하세요.")
    report = pipeline.scan(req.text)
    return report.to_dict()


@app.get("/", response_class=HTMLResponse)
async def index():
    return TEMPLATE.read_text(encoding="utf-8")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
