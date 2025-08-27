from datetime import date
from django.http import JsonResponse, HttpResponse, FileResponse
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

cur_mo = date.today().month

def get_dept_codes(department_codes, cnxn ):

        query = 'select distinct department_name from uwm_purchaseHist12Mo'
        query_df = pd.read_sql(query, cnxn)
        for i in range(len(query_df)):
            name_split = query_df['department_name'][i].split(" ")
            dept_code = str(name_split[0])
            dept_arr = name_split[1:]
            dept_name = ''
            for i in range(len(dept_arr)):
                if i != 0: 
                    dept_name += "_" + dept_arr[i]
                else:
                    dept_name += dept_arr[i]
            department_codes.update({dept_code: dept_name})

def expend(request, range):
        
        try:
            
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

            department_codes = {}
            get_dept_codes(department_codes, cnxn)

            for key, val in department_codes.items():
                query_2 = f"select sum((Ordered) * (Unit_Cost)) as '{val}' from uwm_purchaseHist12Mo where Department_Code = '{key}' and {where_statement_2}"
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
                query_4 = f"select sum((Ordered) * (Unit_Cost)) as '{val}' from uwm_purchaseHistLt732Gt365 where Department_Code = '{key}' and {where_statement_4}"
                query_4_df = pd.read_sql(query_4, cnxn)
                query_4_jsn = query_4_df.to_json(orient='records')
                dept_totals_earlier_12_mo.append(query_4_jsn)
            records.append(json.dumps([{"dept_totals_earlier_12_mo": dept_totals_earlier_12_mo}]))
            
            cnxn.close()
            return JsonResponse(records, safe=False)
        except:
            cnxn.close()
            data = {'message': 'unable to complete operation'}
            return JsonResponse(data, status=500)
        
def expend_month(request, month, year):
        
    try:
        
        mo = int(month)
        yr = int(year)

        if mo == 0: 
            mo = 'month(order_date)'
            yr = 'year(order_date)'

        cnxn = engine.connect()
        records = []
        # Total costs for each dept...specific month of most recent 12 months.
        where_cont = ''
        if mo == 'month(order_date)':
            where_cont = f"year(order_date) = {yr} and month(order_date) != {cur_mo}"
        else:
            where_cont = f"year(order_date) = {yr} and month(order_date) = {mo}"
        dept_totals_latest_12_mo = []

        department_codes = {}
        get_dept_codes(department_codes, cnxn)
        for key, val in department_codes.items():
            query_1 = f"select sum((Ordered) * (Unit_Cost)) as '{val}' from uwm_purchaseHist12Mo where Department_Code = '{key}' and {where_cont}"
            query_1_df = pd.read_sql(query_1, cnxn)
            query_1_jsn = query_1_df.to_json(orient='records')
            dept_totals_latest_12_mo.append(query_1_jsn)
        records.append(json.dumps([{"dept_totals_latest_12_mo": dept_totals_latest_12_mo}]))

        # Total costs for each dept...specific month of earlier 12 month period.
        where_cont_2 = ''
        if mo == 'month(order_date)':
            where_cont_2 = f"year(order_date) = {yr} and month(order_date) != {cur_mo}"
        else:
            where_cont_2 = f"year(order_date) = {yr - 1} and month(order_date) = {mo}"
        dept_totals_earlier_12_mo = []
        for key, val in department_codes.items():
            query_2 = f"select sum((Ordered) * (Unit_Cost)) as '{val}' from uwm_purchaseHistLt732Gt365 where Department_Code = '{key}' and {where_cont_2}"
            query_2_df = pd.read_sql(query_2, cnxn)
            query_2_jsn = query_2_df.to_json(orient='records')
            dept_totals_earlier_12_mo.append(query_2_jsn)
        records.append(json.dumps([{"dept_totals_earlier_12_mo": dept_totals_earlier_12_mo}]))
        
        cnxn.close()
        return JsonResponse(records, safe=False)
    except Exception as e:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)
        
def expend_month_mod(request, month, year, perct_mod, sign):
        
    try:
        mo = int(month)
        yr = int(year)

        if mo == 0: 
            mo = 'month(order_date)'
            yr = 'year(order_date)'

        perct_mod =  float(perct_mod)
        if sign  == 'neg':
            perct_mod *= (-1)

        cnxn = engine.connect()
        records = []

        # Total costs for each dept...specific month of most recent 12 months.
        where_cont = ''
        if mo == 'month(order_date)':
            where_cont = f"year(order_date) = {yr} and month(order_date) != {cur_mo}"
        else:
            where_cont = f"year(order_date) = {yr} and month(order_date) = {mo}"
        dept_totals_latest_12_mo = []

        department_codes = {}
        get_dept_codes(department_codes, cnxn)

        for key, val in department_codes.items():
            query_1 = f"select(select sum((Ordered) * (Unit_Cost)) * {perct_mod} from uwm_purchaseHist12Mo where Department_Code = '{key}' and {where_cont}) + (select sum((Ordered) * (Unit_Cost)) from uwm_purchaseHist12Mo where Department_Code = '{key}' and {where_cont}) as '{val}'"
            query_1_df = pd.read_sql(query_1, cnxn)
            query_1_jsn = query_1_df.to_json(orient='records')
            dept_totals_latest_12_mo.append(query_1_jsn)
        records.append(json.dumps([{"dept_totals_latest_12_mo": dept_totals_latest_12_mo}]))

        # Total costs for each dept...specific month of earlier 12 month period.
        where_cont_2 = ''
        if mo == 'month(order_date)':
            where_cont_2 = f"year(order_date) = {yr} and month(order_date) != {cur_mo}"
        else:
            where_cont_2 = f"year(order_date) = {yr - 1} and month(order_date) = {mo}"
        dept_totals_earlier_12_mo = []
        for key, val in department_codes.items():
            query_2 = f"select(select sum((Ordered) * (Unit_Cost)) * {perct_mod} from uwm_purchaseHistLt732Gt365 where Department_Code = '{key}' and {where_cont_2}) + (select sum((Ordered) * (Unit_Cost)) from uwm_purchaseHistLt732Gt365 where Department_Code = '{key}' and {where_cont_2}) as '{val}'"
            query_2_df = pd.read_sql(query_2, cnxn)
            query_2_jsn = query_2_df.to_json(orient='records')
            dept_totals_earlier_12_mo.append(query_2_jsn)
        records.append(json.dumps([{"dept_totals_earlier_12_mo": dept_totals_earlier_12_mo}]))
        
        cnxn.close()
        return JsonResponse(records, safe=False)
    except:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)
    
def get_dataset(request, table):
    try:
        cnxn = engine.connect()
        query = f"select * from {table}"
        query_df = pd.read_sql(query, cnxn)
        query_jsn = query_df.to_json(orient='records')
        return JsonResponse(query_jsn, safe=False)
    except Exception as e:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)

def get_purchase_freq(request):
    try:
        cnxn = engine.connect()
        query = f"select count (*) as total, PO_Item_Code from uwm_purchaseHist12Mo where PO_Item_Code not like '%tool' group by PO_Item_Code order by total desc;"
        query_df = pd.read_sql(query, cnxn)
        query_jsn = query_df.to_json(orient='records')
        return JsonResponse(query_jsn, safe=False)
    except Exception as e:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)

def get_purchase_hist(request, item_code):
    try:
        cnxn = engine.connect()
        query = f"select * from uwm_purchaseHist12Mo where PO_Item_Code = '{item_code}' order by Order_Date asc"
        query_df = pd.read_sql(query, cnxn)
        query_jsn = query_df.to_json(orient='records')
        return JsonResponse(query_jsn, safe=False)
    except Exception as e:
        cnxn.close()
        print(e)
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)

def monthly_totals(request):
    try:
        cnxn = engine.connect()
        current_year  = 'select * from uwm_purchaseHist12Mo_ttls'
        current_year_df = pd.read_sql(current_year, cnxn)
        current_year_jsn = current_year_df.to_json(orient='records')

        prev_yr = 'select * from uwm_purchaseHist_prev_12Mo_ttls'
        prev_yr_df = pd.read_sql(prev_yr, cnxn)
        prev_yr_df_jsn = prev_yr_df.to_json(orient='records')

        cnxn.close()
        return JsonResponse([current_year_jsn, prev_yr_df_jsn], safe=False)
    
    except Exception as e:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)
    
def monthly_totals_mod(request, perct_mod, sign):
    try:
        cnxn = engine.connect()
        perct_mod =  float(perct_mod)
        if sign  == 'neg':
            perct_mod *= (-1)

        # Calculates new/adjusted totals with percentage modification param.
        current_year  = f"select(sum(total_cost) * {perct_mod}) + sum(total_cost) as monthly_total, moYr from mod_uwm_purchaseHist12Mo group by moYr"
        current_year_df = pd.read_sql(current_year, cnxn)
        current_year_jsn = current_year_df.to_json(orient='records')

        prev_yr = f"select(sum(total_cost) * {perct_mod}) + sum(total_cost) as monthly_total, moYr from mod_uwm_purchaseHistLt732Gt365 group by moYr"
        prev_yr_df = pd.read_sql(prev_yr, cnxn)
        prev_yr_df_jsn = prev_yr_df.to_json(orient='records')

        cnxn.close()
        return JsonResponse([current_year_jsn, prev_yr_df_jsn], safe=False)
    except Exception as e:
        cnxn.close()
        data = {'message': 'unable to complete operation'}
        return JsonResponse(data, status=500)
