from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from dotenv import load_dotenv
import os
import pandas as pd
from pathlib import Path
import sqlalchemy as db

IS_HEROKU_APP = "DYNO" in os.environ and not "CI" in os.environ

if IS_HEROKU_APP:
   engine = db.create_engine(f"mssql+pymssql://{os.environ.get('UQNT_USER')}:{os.environ.get('UQNT_PASS')}@{os.environ.get('UQNT_SERVER')}:1433/{os.environ.get('UQNT_DB')}")
else: 
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_path = load_dotenv(os.path.join(BASE_DIR, '.env'))
    load_dotenv(env_path)
    engine = db.create_engine(f"mssql+pymssql://{os.environ.get('UQNT_USER')}:{os.environ.get('UQNT_PASS')}@{os.environ.get('UQNT_SERVER')}:1433/{os.environ.get('UQNT_DB')}")

def uwm_fs_expend(request, range):
    
    cnxn = engine.connect()
    records = []
    department_codes = {
        '026808': 'Facility_Repair',
        '026403': 'Mechanicals',
        '026804': 'Stores',
        '026909': 'Electrical_Elevator_Inventory',
        '026404': 'Plumbing',
        '026805': 'Grounds',
        '026911': 'Stores_Inventory',
        '026809': 'Preventive_Maintenance',
        '026806': 'Garage_Services',
        '026400': 'Carpenters',
        '026401': 'Electricians',
        '026803': 'Custodial_Services',
        '026807': 'A_E_Services',
        '026402': 'Painters',
    }

    query = f"select sum((Ordered) * (Unit_Cost)) as uwm_fs_{range}_day_ttl from uwm_purchaseHist12Mo where Order_date > dateadd(dd, -{int(range)+1}, current_date);"
    query_df = pd.read_sql(query, cnxn)
    query_jsn = query_df.to_json(orient='records')
    records.append(query_jsn)

    for key, val in department_codes.items():
        query = f"select sum((Ordered) * (Unit_Cost)) as {val} from uwm_purchaseHist12Mo where Department_Code = {key} and Order_date > dateadd(dd, -{int(range)+1}, current_date)"
        query_df = pd.read_sql(query, cnxn)
        query_jsn = query_df.to_json(orient='records')
        records.append(query_jsn)

    cnxn.close()

    return JsonResponse(records, safe=False)