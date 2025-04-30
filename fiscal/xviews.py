from django.shortcuts import render, redirect
from pathlib import Path
from django.http import JsonResponse, HttpResponse
import pandas as pd
import os
from sklearn import preprocessing
import sqlalchemy as db
from dotenv import load_dotenv

IS_HEROKU_APP = "DYNO" in os.environ and not "CI" in os.environ

if IS_HEROKU_APP:
   engine = db.create_engine(f"mssql+pymssql://{os.environ.get('UQNT_USER')}:{os.environ.get('UQNT_PASS')}@{os.environ.get('UQNT_SERVER')}:1433/{os.environ.get('UQNT_DB')}")
else: 
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_path = load_dotenv(os.path.join(BASE_DIR, '.env'))
    load_dotenv(env_path)
    engine = db.create_engine(f"mssql+pymssql://{os.environ.get('UQNT_USER')}:{os.environ.get('UQNT_PASS')}@{os.environ.get('UQNT_SERVER')}:1433/{os.environ.get('UQNT_DB')}")

def EconData(request, startDate, endDate):
    cnxn = engine.connect()
    econ_data = f'select * from select_economic_data where date between {startDate} and {endDate};' 
    econ_data_df = pd.read_sql(econ_data, cnxn)
    econ_data_jsn = econ_data_df.to_json(orient='records')
    allObjs = [econ_data_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

def fiscal(request):
    return render(request, 'fiscal_generic.html')

def fiscal_posts(request):
    return render(request, 'fiscal_posts.html')
        
async def fiscalquery(request, startDate, endDate):
    
    cnxn = engine.connect()

    PrevYr = int(startDate) - 1

    fed_debt_1 = f'select round(fygfd, 1) as federal_debt, year as yr ' 
    fed_debt_2 = f'from fygfd where year between {startDate} and {endDate} order by yr;'
    fed_debt = fed_debt_1 + fed_debt_2
    fed_debt_df = pd.read_sql(fed_debt, cnxn)
    fed_debt_jsn = fed_debt_df.to_json(orient='records')

    gov_outlays_1 = f'select fiscal_year, classification_description as clsdesc, parent_cls_desc, subclass_helper, current_fiscal_year_to_date_gross_outlays_amount '
    gov_outlays_2 = f"as amt from gov_outlays_q4_w_helpers where fiscal_year = {startDate} and classification_description like 'Total--%' "
    gov_outlays_3 = f'and Sequence_Level_Number = 2 and current_fiscal_year_to_date_gross_outlays_amount > 0 '
    gov_outlays_4 = f'order by current_fiscal_year_to_date_gross_outlays_amount desc'
    gov_outlays = gov_outlays_1 + gov_outlays_2 + gov_outlays_3 + gov_outlays_4
    gov_outlays_df = pd.read_sql(gov_outlays, cnxn)
    gov_outlays_jsn = gov_outlays_df.to_json(orient='records')

    year_ttl_all_cls_1 = f"select sum(current_fiscal_year_to_date_gross_outlays_amount) as year_ttl_all_cls from gov_outlays_q4_w_helpers where fiscal_year = {startDate} and classification_description like 'Total--%' " 
    year_ttl_all_cls_2 = f'and Sequence_Level_Number = 2 and current_fiscal_year_to_date_gross_outlays_amount > 0'
    year_ttl_all_cls = year_ttl_all_cls_1 + year_ttl_all_cls_2
    year_ttl_all_cls_df = pd.read_sql(year_ttl_all_cls, cnxn)
    year_ttl_all_cls_jsn = year_ttl_all_cls_df.to_json(orient='records')

    prev_yr_ttl = f"select * from gov_outlays_q4_w_helpers where year = {PrevYr} and classification_description like 'Total--%' and Sequence_Level_Number = 2"
    prev_yr_ttl_df = pd.read_sql(prev_yr_ttl, cnxn)
    prev_yr_ttl_jsn = prev_yr_ttl_df.to_json(orient='records')

    expend_and_receipts = f'select * from expenditures_and_receipts where year between {startDate} and {endDate} order by year'
    expend_and_receipts_df = pd.read_sql(expend_and_receipts, cnxn)
    expend_and_receipts_jsn = expend_and_receipts_df.to_json(orient='records')

    allObjs = [fed_debt_jsn, gov_outlays_jsn, year_ttl_all_cls_jsn, prev_yr_ttl_jsn, expend_and_receipts_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe= False)

def get_assoc_chts(request, scriptID):
    match int(scriptID):

        case 1:
        
            cnxn = engine.connect()
            dataset = 'select date, pmsave as personal_saving, pce, m1, cpiu, personal_income from cbo_annual_cy_plus where date between 1990 and 2023'
            dataset_df = pd.read_sql(dataset, cnxn)
            cnxn.close()

            # Calculate change in personal_saving
            for i in range(len(dataset_df)):
                if i != 0: 
                    dataset_df.loc[i, 'change_in_saving'] = round(((dataset_df['personal_saving'][i] - dataset_df['personal_saving'][i - 1])/dataset_df['personal_saving'][i-1]) * 100, 2)
                    dataset_df.loc[i, 'change_in_m1'] = round(((dataset_df['m1'][i] - dataset_df['m1'][i - 1])/dataset_df['m1'][i-1]) * 100, 2)

                else:
                    dataset_df.loc[i, 'change_in_saving'] = 0
                    dataset_df.loc[i, 'change_in_m1'] = 0

            # Get top 10 increases in personal_saving
            get_top_savings = (dataset_df.sort_values('change_in_saving', ascending= False)).head(10)

            # Normalize dataset

            savings = dataset_df['personal_saving']
            consumption = dataset_df['pce']
            m1 = dataset_df['m1']
            cpi = dataset_df['cpiu']

            savings_norm = preprocessing.normalize([savings])
            consumption_norm = preprocessing.normalize([consumption])
            m1_norm =  preprocessing.normalize([m1])
            cpi_norm = preprocessing.normalize([cpi])

            dates = []
            for i in range(len(dataset_df)):
                dates.append(dataset_df.loc[i, 'date'])

            savings_norm_list = savings_norm[0].tolist()
            consumption_norm_list = consumption_norm[0].tolist()
            m1_norm_list = m1_norm[0].tolist()
            cpi_norm_list = cpi_norm[0].tolist()

            norms = [dates, savings_norm_list, consumption_norm_list, m1_norm_list, cpi_norm_list]
            norms_df = pd.DataFrame(norms).transpose()
            norms_df.columns = ['Year', 'Savings', 'Consumption', 'M1', 'CPI']

            norms_jsn = norms_df.to_json(orient='records')
            top_savings_jsn = get_top_savings.to_json(orient='records')
            dataset_jsn = dataset_df.to_json(orient='records')

            allObjs = [norms_jsn, top_savings_jsn, dataset_jsn]
            return JsonResponse(allObjs, safe=False)

        case 2:

            cnxn = engine.connect()
            expend = 'select year, total_expenditures from expenditures_and_receipts where year between 1960 and 2023'
            expend_df = pd.read_sql(expend, cnxn)
            econ_data = 'select date, real_gdp, personal_income, noncyclical_rate_of_unemployment, cpiu from cbo_annual_cy where date between 1960 and 2023'
            econ_data_df = pd.read_sql(econ_data, cnxn)
            population = 'select year, resident_population from us_population'
            population_df = pd.read_sql(population, cnxn)
            cnxn.close()

            # Add change in expenditures 
            for i in range(len(expend_df)):
                if (i != 0):
                    expend_df.loc[i, 'change_in_expend'] =  ((expend_df['total_expenditures'][i] - expend_df['total_expenditures'][i- 1]) / expend_df['total_expenditures'][i -1]) * 100
                    expend_df.loc[i, 'abs_change_in_expend'] = abs(expend_df['change_in_expend'][i])
                    if(i != 1): expend_df.loc[i, 'chg_in_expd_prev_yr'] = expend_df['change_in_expend'][i-1]

                    if(i != 1):
                        if(expend_df['change_in_expend'][i] >  expend_df['change_in_expend'][i-1]):
                            expend_df.loc[i, 'incr_rate_of_chg_expend'] = 1
                        else:
                            expend_df.loc[i, 'incr_rate_of_chg_expend'] = 0

            # Get population data to adjust real_gdp to real_gpd_per_cap
            pops = {}
            for i in range(len(population_df)):
                pops.update({population_df.loc[i, 'year']: population_df.loc[i, 'resident_population']})

            # Access population data based on year of economic data and calculate real_gdp_per_cap.
            for i in range(len(econ_data_df)): 
                    yr = str(econ_data_df.loc[i, 'date'])
                    yr = yr[0:3]
                    yr += '0'
                    intyr = int(yr) 
                    econ_data_df.loc[i, 'real_gdp_per_cap'] = econ_data_df['real_gdp'][i] / pops[intyr]  

            # Add change in econ_data columns
            for i in range(len(econ_data_df)):
                if (i != 0):
                    econ_data_df.loc[i, 'chg_in_real_gdp'] =  ((econ_data_df['real_gdp_per_cap'][i] - econ_data_df['real_gdp_per_cap'][i- 1]) / econ_data_df['real_gdp_per_cap'][i - 1]) * 100
                    econ_data_df.loc[i, 'chg_in_unemp'] =  ((econ_data_df['noncyclical_rate_of_unemployment'][i] - econ_data_df['noncyclical_rate_of_unemployment'][i - 1]) / econ_data_df['noncyclical_rate_of_unemployment'][i - 1]) * 100
                
                    if(i != 1):
                        if(econ_data_df['chg_in_real_gdp'][i] >  econ_data_df['chg_in_real_gdp'][i-1]):
                            econ_data_df.loc[i, 'incr_rate_of_chg_rgdp'] = 1
                        else:
                            econ_data_df.loc[i, 'incr_rate_of_chg_rgdp'] = 0
                        if(econ_data_df['chg_in_unemp'][i] >  econ_data_df['chg_in_unemp'][i-1]):
                            econ_data_df.loc[i, 'incr_rate_of_chg_unemp'] = 1
                        else:
                            econ_data_df.loc[i, 'incr_rate_of_chg_unemp'] = 0

            # Add change in econ data to expenditures df   
            for i in range(len(expend_df)):
                expend_df.loc[i, 'chg_in_real_gdp'] =  econ_data_df['chg_in_real_gdp'][i]
                expend_df.loc[i, 'chg_in_unemp'] = econ_data_df['chg_in_unemp'][i]
                expend_df.loc[i, 'incr_rate_of_chg_rgdp'] =  econ_data_df['incr_rate_of_chg_rgdp'][i]
                expend_df.loc[i, 'incr_rate_of_chg_unemp'] = econ_data_df['incr_rate_of_chg_unemp'][i]

            ttl_outcomes = len(expend_df - 2)
            incr_expend_incr_rgdp = 0
            incr_expend_decr_unemp = 0

            # Compute probability that an increasing rate of change in expenditures leads to and increasing rate of change in rgdp / decreasing rate of change of unemployment
            # the following year
            for i in range(len(expend_df)-1):
                    if(expend_df['incr_rate_of_chg_expend'][i] == 1 and expend_df['incr_rate_of_chg_rgdp'][i+1] == 1):
                        expend_df.loc[i, 'incr_expend_incr_rgdp'] = 1
                        incr_expend_incr_rgdp += 1
                    if(expend_df['incr_rate_of_chg_expend'][i] == 1 and expend_df['incr_rate_of_chg_unemp'][i+1] == 0 ):
                        expend_df.loc[i, 'incr_expend_incr_rgdp'] = 1
                        incr_expend_decr_unemp += 1

            prob_incr_expend_incr_rgdp = incr_expend_incr_rgdp / ttl_outcomes
            prob_incr_expend_decr_unemp = incr_expend_decr_unemp / ttl_outcomes
            expend_df = expend_df[2:-1]

            expend_jsn = expend_df.to_json(orient='records')
            allObjs = [expend_jsn, prob_incr_expend_incr_rgdp, prob_incr_expend_decr_unemp]
            return JsonResponse(allObjs, safe=False)

async def gov_expend_plus(request, startDate, endDate):
        cnxn = engine.connect()
        gov_expend = f'select * from gov_expend_set where date between {startDate} and {endDate};' 
        gov_expend_df = pd.read_sql(gov_expend, cnxn)
        gov_expend_jsn = gov_expend_df.to_json(orient='records')
        allObjs = [gov_expend_jsn]
        cnxn.close()
        
def get_containers(request):
    return render(request, 'post_container.html')

async def get_posts(request):
    cnxn = engine.connect()
    my_posts_qry = """
    select format(post_date, 'MM/dd/yyyy') as post_date, 
    post_time,title, post_description, post, id, script_id from posts
    order by post_date desc, post_time desc
    """
    get_posts_df = pd.read_sql(my_posts_qry, cnxn)
    get_posts_jsn = get_posts_df.to_json(orient='records')
    allObjs = [get_posts_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

def gov_outlays_tbl_drilldown(request, classID):
    cnxn = engine.connect()

    my_qry = f'select classification_description, parent_cls_desc, current_fiscal_year_to_date_gross_outlays_amount as amt from gov_outlays_q4_w_helpers where subclass_helper = {classID} '
    my_qry_df = pd.read_sql(my_qry, cnxn)
    my_qry_jsn  = my_qry_df.to_json(orient='records')

    allObjs = [my_qry_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

def index(request):
    response = redirect('/fiscal/')
    return response

        
async def InterestRates(request, startDate, endDate):
    cnxn = engine.connect()
    interest_rates = f'select * from interest_rates where year between {startDate} and {endDate};' 
    interest_rates_df = pd.read_sql(interest_rates, cnxn)
    interest_rates_jsn = interest_rates_df.to_json(orient='records')
    allObjs = [interest_rates_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)


async def ImportsExports(request, startDate, endDate):
    cnxn = engine.connect()
    imports_exports = f'select * from imports_and_exports where year between {startDate} and {endDate};' 
    imports_exports_df = pd.read_sql(imports_exports, cnxn)
    imports_exports_jsn = imports_exports_df.to_json(orient='records')
    allObjs = [imports_exports_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)
                
async def Population(request, startDate, endDate):
    cnxn = engine.connect()
    population = f'select * from population where year between {startDate} and {endDate};' 
    population_df = pd.read_sql(population, cnxn)
    population_jsn = population_df.to_json(orient='records')
    allObjs = [population_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

async def PriceIndices(request, startDate, endDate):
    cnxn = engine.connect()
    price_indices = f'select * from price_indices where year between {startDate} and {endDate};' 
    price_indices_df = pd.read_sql(price_indices, cnxn)
    price_indices_jsn = price_indices_df.to_json(orient='records')
    allObjs = [price_indices_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

async def ProductionConsumption(request, startDate, endDate):
    cnxn = engine.connect()
    production_and_consumption = f'select * from production_and_consumption where year between {startDate} and {endDate};' 
    production_and_consumption_df = pd.read_sql(production_and_consumption, cnxn)
    production_and_consumption_jsn = production_and_consumption_df.to_json(orient='records')
    allObjs = [production_and_consumption_jsn]
    cnxn.close()
    return JsonResponse(allObjs, safe=False)

async def update_outlays(request, year):
    cnxn = engine.connect()
    PrevYr = int(year) - 1
    
    gov_outlays_1 = f'select fiscal_year, classification_description as clsdesc, parent_cls_desc, subclass_helper, current_fiscal_year_to_date_gross_outlays_amount '
    gov_outlays_2 = f"as amt from gov_outlays_q4_w_helpers where fiscal_year = {year} and classification_description like 'Total--%' "
    gov_outlays_3 = f'and Sequence_Level_Number = 2 and current_fiscal_year_to_date_gross_outlays_amount > 0 '
    gov_outlays_4 = f'order by current_fiscal_year_to_date_gross_outlays_amount desc'
    gov_outlays = gov_outlays_1 + gov_outlays_2 + gov_outlays_3 + gov_outlays_4
    gov_outlays_df = pd.read_sql(gov_outlays, cnxn)
    gov_outlays_jsn = gov_outlays_df.to_json(orient='records')

    year_ttl_all_cls_1 = f"select sum(current_fiscal_year_to_date_gross_outlays_amount) as year_ttl_all_cls from gov_outlays_q4_w_helpers where fiscal_year = {year} and classification_description like 'Total--%' " 
    year_ttl_all_cls_2 = f'and Sequence_Level_Number = 2 and current_fiscal_year_to_date_gross_outlays_amount > 0'
    year_ttl_all_cls = year_ttl_all_cls_1 + year_ttl_all_cls_2
    year_ttl_all_cls_df = pd.read_sql(year_ttl_all_cls, cnxn)
    year_ttl_all_cls_jsn = year_ttl_all_cls_df.to_json(orient='records')

    prev_yr_ttl = f"select * from gov_outlays_q4_w_helpers where year = {PrevYr} and classification_description like 'Total--%' and Sequence_Level_Number = 2"
    prev_yr_ttl_df = pd.read_sql(prev_yr_ttl, cnxn)
    prev_yr_ttl_jsn = prev_yr_ttl_df.to_json(orient='records')

    allObjs = [gov_outlays_jsn, year_ttl_all_cls_jsn, prev_yr_ttl_jsn]

    cnxn.close()
    return JsonResponse(allObjs, safe= False)

# 500 http err
def handler500(request):
    response = render(request, 'handler500.html')
    response.status_code = 500
    return response

# Tests
def test(request):
    if IS_HEROKU_APP:
        return render(request, 'something_went_wrong.html')
    else:
        return render(request, 'test.html')