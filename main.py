import pandas as pd
import datetime
from fastapi import FastAPI, Request, BackgroundTasks, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
# from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
import traceback
import sqlite3
import os
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="assets"), name="assets")

templates = Jinja2Templates(directory="templates/webapp")


@app.get("/")
async def home(request: Request):
    #try:
    return templates.TemplateResponse('index.html', {"request": request})

    # except Exception as e:
    #     print(e)
    #     return templates.TemplateResponse('v2_error.html', {"request": request})


if __name__ == '__main__':
    uvicorn.run(app, port=4242, host='0.0.0.0')