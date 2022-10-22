import pandas as pd
import numpy as np
import random
from fastapi import FastAPI, Request, BackgroundTasks, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
# from fastapi.responses import RedirectResponse
#from sqlalchemy import create_engine
import traceback
import sqlite3
import uvicorn
import os

# Launch app and mount assets
app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates/webapp")
# Init DB from most recent backup
con = sqlite3.connect("restaurants.db")
ref_df = pd.read_csv('./rest_ref.csv')
username = 'jack_cait'
ref_df.to_sql(name=username, con=con, if_exists='replace')

@app.get("/")
async def home(request: Request):
    try:
        return templates.TemplateResponse('index.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.get("/input")
async def user_input(request: Request):
    try:
        return templates.TemplateResponse('input_cont.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.post("/save_input")
async def save_input(request: Request):
    # Collect User Input
    body = await request.body()
    print(body)
    out_list = []
    for x in body.decode('UTF-8').split('&')[:-1]:
        out_list.append(x.split('=')[1].replace('+', ' '))
    # Create Input Dataframe
    df = pd.DataFrame([out_list], columns=['Name', 'Cuisine', 'Location', 'Cocktails', 'Beer', 'Food', 'Seating',
                                           'Price'])
    # Update DB
    username = 'jack_cait'
    df.to_sql(name=username, con=con, if_exists='append')
    print('Record Updated')

    # Create Backup
    out_df = pd.read_sql(f'select * from {username}', con)
    out_df.to_csv('./rest_ref.csv', index=False)

    try:
        return templates.TemplateResponse('index.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.get("/search")
async def user_input(request: Request):
    try:
        return templates.TemplateResponse('search.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.post("/run_search")
async def user_input(request: Request):
    try:
        # receive and process input
        body = await request.body()
        print(body)
        out_list = []
        for x in body.decode('UTF-8').split('&')[:-1]:
            out_list.append(x.split('=')[1].replace('+', ' '))

        # Filter down Dataframe
        sql = f'Select Name, Cuisine, Location, Cocktails, Beer, Food, Seating, Price' \
              f' FROM {username} WHERE Cuisine = {out_list[0]} and Location = {out_list[1]}'
        df = pd.read_sql(sql, con=con)

        # Calculate similarity for remaining rows
        def calcSimScore(row, user_array):
            user_array = np.array([int(i) for i in user_array[2:]])
            row_array = np.array([row['Cocktails'], row['Beer'], row['Food'], row['Seating'], row['Price']])
            dist = np.linalg.norm(user_array - row_array)
            return dist

        df['sim_score'] = df.apply(lambda x: calcSimScore(x, out_list), axis=1)
        outdf = df.sort_values('sim_score', ascending= False)
        recs = outdf['Name'].values.tolist()[:2]


        return templates.TemplateResponse('rec.html', {"request": request, "rec": random.choice(recs)})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})


if __name__ == '__main__':
    if os.environ['MODE'] == 'dev':
        uvicorn.run(app, port=4242, host='0.0.0.0')