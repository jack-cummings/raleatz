import pandas as pd
import numpy as np
import random
from fastapi import FastAPI, Request, BackgroundTasks, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
#from sqlalchemy import create_engine
import starlette.status as status
import traceback
import sqlite3
import uvicorn
import os
import subprocess

# Launch app and mount assets
app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates/webapp")
# Init DB from most recent backup
con = sqlite3.connect("restaurants.db")
ref_df = pd.read_csv('./rest_ref.csv')
username = 'jack_cait'
ref_df.to_sql(name=username, con=con, if_exists='replace', index=False)


@app.get("/")
async def home(request: Request):
    try:
        # rest card template
        out_html = ''
        base_card = """ <div class="card border-primary mb-3" style="max-width: 20rem;">
                    <div class="card-header">_cuisine_ - _location_ - _price_</div>
                    <div class="card-body">
                      <h4 class="card-title">_name_</h4>
                      <ul class="list-unstyled">
                        <li><b>Cocktails:</b><small class="text-secondary">(none to craft)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _cocktailsV_%;" aria-valuenow="_coctailsV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Beers:</b><small class="text-secondary">(none to craft)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _beersV_%;" aria-valuenow="_beersV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Fanciness:</b><small class="text-secondary">(counter service to stuffy)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _fancinessV_%;" aria-valuenow="_seatingV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Cosiness:</b><small class="text-secondary">(cozy to party)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _cozinessV_%;" aria-valuenow="_vibeV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                      </ul>
                    </div>
                    </div> """
        # read existing db
        base_sql = f"""Select Name, Cuisine, Location, Cocktails, Beer, Fanciness, Coziness, Price FROM {username} """
        df = pd.read_sql(base_sql, con=con)
        lol = df.head(10).values.tolist()
        for x in lol:
            out_html = out_html+base_card.replace("_name_",str(x[0])).replace(
                                                    "_cuisine_",str(x[1])).replace(
                                                    "_location_",str(x[2])).replace(
                                                    "_price_", str('$'*x[7])).replace(
                                                    "_cocktailsV_",str(100*(x[3]/5))).replace(
                                                    "_beersV_",str(100*(x[4]/5))).replace(
                                                    "_fancinessV_",str(100*(x[5]/5))).replace(
                                                    "_cozinessV_",str(100*(x[6]/5)))

        return templates.TemplateResponse('index_inset.html', {"request": request, 'card_inserts':out_html})

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
    try:
        # Collect User Input
        body = await request.body()
        print(body)
        out_list = []
        for x in body.decode('UTF-8').split('&')[:-1]:
            out_list.append(x.split('=')[1].replace('+', ' '))
        # Create Input Dataframe
        df = pd.DataFrame([out_list], columns=['Name', 'Cuisine', 'Location', 'Cocktails', 'Beer', 'Fanciness', 'Coziness',
                                               'Price'])
        # Update DB
        username = 'jack_cait'
        df.to_sql(name=username, con=con, if_exists='append', index=False)
        print('Record Updated')

        # Create Backup
        out_df = pd.read_sql(f'select * from {username}', con)
        out_df.to_csv('./rest_ref.csv', index=False)

        # # push new to git
        # subprocess.run(['sh', f'./push_ref.sh'], capture_output=True, text=True, shell=True, input='hazelnut')

        # re-direct to index
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

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
        base_sql = f"""Select Name, Cuisine, Location, Cocktails, Beer, Fanciness, Coziness, Price FROM {username} """
        if out_list[0] != 'Any':
            if out_list[1] != 'Any':
                insert = f"WHERE Cuisine = '{out_list[0].strip()}' and Location = '{out_list[1].strip()}'"
            else:
                insert = f"WHERE Cuisine = '{out_list[0].strip()}'"
        else:
            if out_list[1] != 'Any':
                insert = f"WHERE Location = '{out_list[1].strip()}'"
            else:
                insert =""
        sql = base_sql+insert
        df = pd.read_sql(sql, con=con)
        if len(df) == 0:
            df = pd.read_sql(base_sql, con=con)

        # Calculate similarity for remaining rows
        # remove columsn where row = 0
        def calcSimScore(row, user_array):
            user_array = np.array([int(i) for i in user_array[2:]])
            row_array = np.array([row['Cocktails'], row['Beer'], row['Fanciness'], row['Coziness'], row['Price']])
            #set row array to zeros where user specified zeros to avoid search on that attribute
            drop_indexes = np.where(user_array==0)[0].tolist()
            for x in drop_indexes:
                row_array[x] = 0
            dist = np.linalg.norm(user_array - row_array)
            return dist

        df['dif_score'] = df.apply(lambda x: calcSimScore(x, out_list), axis=1)
        outdf = df.sort_values('dif_score', ascending= True)

        # rest card template
        out_html = ''
        base_card = """ <div class="card border-primary mb-3" style="max-width: 20rem;">
                    <div class="card-header">_cuisine_ - _location_ - _price_</div>
                    <div class="card-body">
                      <h4 class="card-title">_name_</h4>
                      <ul class="list-unstyled">
                        <li><b>Cocktails:</b><small class="text-secondary">(none to craft)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _cocktailsV_%;" aria-valuenow="_coctailsV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Beers:</b><small class="text-secondary">(none to craft)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _beersV_%;" aria-valuenow="_beersV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Fanciness:</b><small class="text-secondary">(counter service to stuffy)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _seatingV_%;" aria-valuenow="_seatingV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                        <li><b>Cosiness:</b><small class="text-secondary">(cozy to party)</small><div class="progress"><div class="progress-bar" role="progressbar" style="width: _vibeV_%;" aria-valuenow="_vibeV_" aria-valuemin="0" aria-valuemax="100"></div></div></li>
                      </ul>
                    </div>
                    </div> """
        lol = outdf.head(5).values.tolist()
        for x in lol:
            out_html = out_html+base_card.replace("_name_",str(x[0])).replace(
                                                    "_cuisine_",str(x[1])).replace(
                                                    "_location_",str(x[2])).replace(
                                                    "_price_", str('$'*x[7])).replace(
                                                    "_cocktailsV_",str(100*(x[3]/5))).replace(
                                                    "_beersV_",str(100*(x[4]/5))).replace(
                                                    "_seatingV_",str(100*(x[5]/5))).replace(
                                                    "_vibeV_",str(100*(x[6]/5)))


        return templates.TemplateResponse('rec.html', {"request": request, 'card_inserts':out_html})

    except Exception as e:
        print(e)
        return templates.TemplateResponse('error.html', {"request": request})


if __name__ == '__main__':
    if os.environ['MODE'] == 'dev':
        uvicorn.run(app, port=4242, host='0.0.0.0')