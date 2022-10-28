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
        return templates.TemplateResponse('index_v2.html', {"request": request})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})

@app.get("/input")
async def user_input(request: Request):
    try:
        return templates.TemplateResponse('input_cont_v3.html', {"request": request})

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
        # Create sql
        base_sql = f"""Select Name, Cuisine, Location, Cocktails, Beer, Food, Seating, Price FROM {username} """
        if out_list[0] != 'Any':
            if out_list[1] != 'Any':
                insert = f"WHERE Cuisine = '{out_list[0]}' and Location = '{out_list[1]}'"
            else:
                insert = f"WHERE Cuisine = '{out_list[0]}'"
        else:
            if out_list[1] != 'Any':
                insert = f"WHERE Location = '{out_list[1]}'"
            else:
                insert =""
        sql = base_sql+insert
        df = pd.read_sql(sql, con=con)
        if len(df) == 0:
            df = pd.read_sql(base_sql, con=con)

        # Calculate similarity for remaining rows
        def calcSimScore(row, user_array):
            user_array = np.array([int(i) for i in user_array[2:]])
            row_array = np.array([row['Cocktails'], row['Beer'], row['Food'], row['Seating'], row['Price']])
            dist = np.linalg.norm(user_array - row_array)
            return dist

        df['sim_score'] = df.apply(lambda x: calcSimScore(x, out_list), axis=1)
        outdf = df.sort_values('sim_score', ascending= False)
        rec = outdf.loc[0].to_dict()


        # Translate Scores to human-readable
        cocktails_ref ={0:"No Cocktails", 1:"Basic well drinks", 2: "fun and casual", 3:"Good drinks", 4:"Nicer Cocktails",
                        5:"Fancy and Bougie"}
        beer_ref ={0:"No beer", 1:"Domestics only", 2: "domestics, basic craft", 3:"Some locals and crafts", 4:"Locals and crafts",
                        5:"Exceptional locals and crafts"}
        vibe_ref ={0:"Counter service", 1:"Casual bar food", 2: "fun atmosphere and casual", 3:"Standard sit down", 4:"Date Night",
                        5:"Fine Dining"}
        seating_ref ={0:"Indoor intimate", 1:"Indoor cozy", 2: "Indoor modern", 3:"Variety", 4:"More outdoor modern",
                        5:"All outdoor modern"}
        price_ref ={0:"Cheap", 1:"$", 2: "$$", 3:"$$$", 4:"$$$$",
                        5:"$$$$$"}

        rec_trans = rec
        rec_trans['Cocktails'] = cocktails_ref[rec_trans['Cocktails']]
        rec_trans['Beer'] = beer_ref[rec_trans['Beer']]
        rec_trans['Food'] = vibe_ref[rec_trans['Food']]
        rec_trans['Seating'] = seating_ref[rec_trans['Seating']]
        rec_trans['Price'] = price_ref[rec_trans['Price']]

        rec['request'] = request


        return templates.TemplateResponse('rec.html', rec)

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})


if __name__ == '__main__':
    if os.environ['MODE'] == 'dev':
        uvicorn.run(app, port=4242, host='0.0.0.0')