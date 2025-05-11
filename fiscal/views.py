from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from dotenv import load_dotenv
import json
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
        
        # try:
            rangeReq = int(range)
            match rangeReq:
                case 30:
                    pass
                case 60:
                    pass
                case 90:
                    pass
                case 365:
                    pass
                case _:
                    raise Exception()

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

            # Total costs including all depts...most recent 12 months.
            # -{int(range)+1} => explanation: if range = 30, Order_date  > today - 31 days. 
            # This data falls within the range of of the past 30 days.
            query = f"select sum((Ordered) * (Unit_Cost)) as uwm_fs_{range}_day_ttl_latest_12_mo from uwm_purchaseHist12Mo where Order_date > dateadd(dd, -{int(range)+1}, current_date);"
            query_df = pd.read_sql(query, cnxn)
            query_jsn = query_df.to_json(orient='records')
            records.append(query_jsn)

            # Total costs for each dept...most recent 12 months.
            # DATEADD(DAY, 1, EOMONTH(GETDATE(), -1)) => excludes current month data
            where_statement_2 = f"dateadd(dd, -{int(range)+1}, current_date) < order_date and order_date < DATEADD(DAY, 1, EOMONTH(GETDATE(), -1))"
            dept_totals_latest_12_mo = []
            for key, val in department_codes.items():
                query_2 = f"select sum((Ordered) * (Unit_Cost)) as {val} from uwm_purchaseHist12Mo where Department_Code = {key} and {where_statement_2}"
                query_2_df = pd.read_sql(query_2, cnxn)
                query_2_jsn = query_2_df.to_json(orient='records')
                dept_totals_latest_12_mo.append(query_2_jsn)
            records.append(json.dumps([{"dept_totals_latest_12_mo": dept_totals_latest_12_mo}]))

            # Total costs including all depts...earlier 12 month period.
            query_3 = f"select sum((Ordered) * (Unit_Cost)) as uwm_fs_{range}_day_ttl_earlier_12_mo from uwm_purchaseHistLt732Gt365 where Order_date > dateadd(dd, -{(int(range)+1) + 365}, current_date);"
            query_3_df = pd.read_sql(query_3, cnxn)
            query_3_jsn = query_3_df.to_json(orient='records')
            records.append(query_3_jsn)

            # Total costs for each dept...earlier 12 month period.
            #DATEADD(DAY, 1, EOMONTH(GETDATE()-365, -1)) => excludes currentmonth of last year
            where_statement_4 = f"dateadd(dd, -{(int(range)+1) + 365}, current_date) < order_date and order_date < DATEADD(DAY, 1, EOMONTH(GETDATE()-365, -1))"
            dept_totals_earlier_12_mo = []
            for key, val in department_codes.items():
                query_4 = f"select sum((Ordered) * (Unit_Cost)) as {val} from uwm_purchaseHistLt732Gt365 where Department_Code = {key} and {where_statement_4}"
                query_4_df = pd.read_sql(query_4, cnxn)
                query_4_jsn = query_4_df.to_json(orient='records')
                dept_totals_earlier_12_mo.append(query_4_jsn)
            records.append(json.dumps([{"dept_totals_earlier_12_mo": dept_totals_earlier_12_mo}]))
            
            cnxn.close()
            return JsonResponse(records, safe=False)
        # except Exception as e:
        #     cnxn.close()
        #     print(e)
        #     return HttpResponse('Cou')

def uwm_fs_expend_monthly_totals_with_prev_yr(request):

    cnxn = engine.connect()

    current_year  = 'select * from uwm_purchaseHist12Mo_ttls'
    current_year_df = pd.read_sql(current_year, cnxn)
    current_year_jsn = current_year_df.to_json(orient='records')

    prev_yr = 'select * from uwm_purchaseHist_prev_12Mo_ttls'
    prev_yr_df = pd.read_sql(prev_yr, cnxn)
    prev_yr_df_jsn = prev_yr_df.to_json(orient='records')

    cnxn.close()
    return JsonResponse([current_year_jsn, prev_yr_df_jsn], safe=False)