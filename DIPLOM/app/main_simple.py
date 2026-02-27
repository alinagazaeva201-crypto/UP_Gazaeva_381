# app/main_simple.py
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/вход")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/вход")
async def login(request: Request, login: str = Form(...), password: str = Form(...)):
    # Простая проверка для теста
    if login == "admin" and password == "admin":
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="user", value="admin")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

@app.get("/регистрация")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/регистрация")
async def register(request: Request, login: str = Form(...), password: str = Form(...)):
    # Простая регистрация для теста
    return RedirectResponse(url="/вход", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
