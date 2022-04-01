from flask.helpers import flash, send_file
import pandas as pd
import numpy as np
import os
from pandas.io import json
from search import find_evth
from dl_insert_data import main, check_file, insert_values_metadata
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text
from sqlalchemy.sql.expression import any_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import session, sessionmaker
from ordered_set import OrderedSet as ordset
from flask import Flask, render_template, request, redirect, sessions, url_for
from werkzeug.utils import secure_filename
import csv
# import plotly
# import plotly.express as px
import json
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time
import threading

app = Flask(__name__)

engine = create_engine('postgresql+psycopg2://lingvist:lingvistpassword@127.0.0.1:5432/mydatabase')

Base = declarative_base()

app.secret_key = 'rgrwfgkfm5mterfmesmf5k4efmlrkltt5FGTvvtgtgrFTY'

CREDENTIALS_FILE = 'fw-gui-creds.json'

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'fw-gui-creds.json', scope
)
gc = gspread.authorize(credentials)

class DF(Base):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True)
    clause = Column(Text)
    tr = Column(Text)
    text = Column(Text)
    subj = Column(Text)
    obj = Column(Text)
    verb = Column(Text)
    wo = Column(Text)


def chunker(req_dict, n, sel_list):
    req_dicts = [dict() for i in range(0, len(req_dict), n)]
    dict_num = 0
    count = 0
    for k, v in req_dict.items():
        # k = ''.join(filter(str.isalpha, k))
        k = k.split('_', maxsplit=1)[1]

        if len(v) == 1 and k not in sel_list:
            v = v[0]
        req_dicts[dict_num][k] = v
        if count < n-1:
            count += 1
        else:
            dict_num += 1
            count = 0
    return req_dicts


# def search_by_parameters(db_session, req_dicts):
#     res_set = ordset()
#     for d in req_dicts:
#         # all_texts = list(set(x.text for x in db_session.query(DF).all() if x))
#         # if not texts:
#         #     texts = all_texts

#         new_query = db_session.query(DF)

#         records = new_query.filter(DF.text.in_(d['source']),
#                                   func.lower(DF.clause).contains(d['word']),
#                                   func.lower(DF.tr).contains(d['trans']),
#                                   DF.subj.in_(d['subj']),
#                                   DF.obj.in_(d['obj']),
#                                   DF.verb.in_(d['verb']),
#                                   DF.wo.in_(d['wo']),
#                                   ).all()

#         res_set.update(list(records))
def chunker2(req_dict, text_list):
    #req_dicts = [dict() for i in range(0, len(req_dict), n)]
    req_dicts = []
    dict_num = 0
    count = 0
    new_li = {}
    for key, value in req_dict.items():
        new_k = key.split('_')
        tup = (new_k[0], new_k[-1])
        int_tup = int(tup[0])
        if int_tup > len(req_dicts):
            req_dicts.append(dict())
        new_li = req_dicts[int_tup - 1]
        found = False
        for elem in text_list:
            if elem in key:
                found = True
                if elem not in new_li:
                    new_li[elem] = []
                for el in value:
                    new_li[elem].append(el)
        if not found:
            elem = tup[-1]
            if elem not in new_li:
                new_li[elem] = []
            for el in value:
                new_li[elem].append(el)
    return req_dicts

def clean_dict(dictt, text_cols):
    v_n = []
    for k,v in dictt.items():
        if k in text_cols:
            v.pop(-1) 
            v_n.append((k, ' '.join(v)))
    for el in v_n:
        dictt[el[0]]= el[1]       
    return

    

def dicter(records, cols_list):
    dicts = []
    for record in records:
        record_dict = dict(record)
        dic = {}
        for col in cols_list:
            dic[col] = record_dict[col]
        if not all(v is None for v in dic.values()):
            dicts.append(dic)
    return dicts


def replace(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]

    stmt = insert(table.table).values(data)
    update_stmt = stmt.on_conflict_do_update(index_elements=['id'], 
                                            set_=dict(zip(stmt.excluded.keys(), 
                                            stmt.excluded.values())))

    conn.execute(update_stmt)

@app.route('/corp_update/<corp_id>/<sh_id>')
def corp_update(corp_id, sh_id):
    spreadsheet = gc.open_by_key(sh_id)
    worksheet = spreadsheet.get_worksheet(0)
    df = pd.DataFrame(worksheet.get_all_records())
    with engine.connect() as con:
        df.to_sql(corp_id, con=con, if_exists='append', index=False, method=replace)
    
    query = f'''
    SELECT column_name
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = N'{corp_id}'
    '''
    with engine.connect() as con:    
        col_names = con.execute(query)
    col_names = [col_name[0] for col_name in col_names if col_name[0] != 'id']

    with engine.connect() as con:
        for col in col_names:
            con.execute(f'UPDATE {corp_id} SET \"{col}\"=NULL where \"{col}\"=\'\'')
    # print('done')
    # return schedule.CancelJob
    return redirect(url_for('main_page'))


# def run_continuously(interval=1):
#     """Continuously run, while executing pending jobs at each
#     elapsed time interval.
#     @return cease_continuous_run: threading. Event which can
#     be set to cease continuous run. Please note that it is
#     *intended behavior that run_continuously() does not run
#     missed jobs*. For example, if you've registered a job that
#     should run every minute and you set a continuous run
#     interval of one hour then your job won't be run 60 times
#     at each interval but only once.
#     """
#     cease_continuous_run = threading.Event()

#     class ScheduleThread(threading.Thread):
#         @classmethod
#         def run(cls):
#             while not cease_continuous_run.is_set():
#                 schedule.run_pending()
#                 time.sleep(interval)

#     continuous_thread = ScheduleThread()
#     continuous_thread.start()
#     return cease_continuous_run


@app.route('/')
def main_page():

    return render_template('index.html')


@app.route('/corps')
def corps():
    corp_data = []

    query = 'SELECT id, name FROM languages WHERE name IS NOT NULL'

    with engine.connect() as con:
        res = con.execute(query)

    for entry in res:
        corp_data.append(('/corp_' + str(entry[0]), entry[1]))

    return render_template('corps.html', corp_data=corp_data)


@app.route('/<corp_id>')
def corp_search(corp_id):
    id = int(corp_id.split('_')[1])
    
    cols_query = f'SELECT name, sel_cols, text_cols FROM languages WHERE id = {id}'

    with engine.connect() as con:
        cols_res = con.execute(cols_query)
    
    corp_name, sel_cols, text_cols = list(cols_res)[0]

    sel_query = f'SELECT {sel_cols} FROM {corp_id}'

    with engine.connect() as con:
        sel_res = con.execute(sel_query)

    recs = {}
    sel_list = sel_cols.split(',')

    for sel_col in sel_list:
        recs[sel_col] = set()

    for entry in sel_res:
        for i, sel_col in enumerate(sel_list):
            if entry[i]:
                recs[sel_col].add(entry[i])
            else:
                recs[sel_col].add('')
    
    for sel_col in sel_list:
        recs[sel_col] = sorted(list(recs[sel_col]))
    
    text_list = text_cols.split(',')
        
    return render_template('corp_search.html', recs = recs, corp_id = corp_id,
                            text_list = text_list, corp_name = corp_name)

@app.route('/moksha')
def moksha():
    
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    recs = session.query(DF).all()
    texts = sorted(list(set(x.text for x in recs if x)))
    subjs = sorted(list(set(x.subj for x in recs if x)))
    objs = sorted(list(set(x.obj for x in recs if x)))
    verbs = sorted(list(set(x.verb for x in recs if x)))
    wos = sorted(list(set(x.wo for x in recs if x)))
    session.close()
    return render_template('moksha.html', texts=texts,
                           subjs=subjs, objs=objs,
                           verbs=verbs, wos=wos, messages = {'main':''})


@app.route('/<corp_id>/result', methods=['get'])
def corp_result(corp_id):
    #print(corp_id)
    id = int(corp_id.split('_')[1])

    cols_query = f'SELECT sel_cols, text_cols FROM languages WHERE id = {id}'

    with engine.connect() as con:
        cols_res = con.execute(cols_query)
    
    sel_cols, text_cols = list(cols_res)[0]
    result.sel_list = sel_cols.split(',')
    result.text_list = text_cols.split(',')
    result.cols_list = result.text_list + result.sel_list

    req_dict = request.args.to_dict(flat=False)
    #req_dict = {'1_kh_full_1': ['он', 'or'], '1_kh_full_2': ['я', 'and'], '1_per_full_1': ['он', 'and'], '1_per_full_2': ['она', 'or'], '1_per_full_3': ['они', 'or'], '1_so': ['', '0.0', '1.0'], '1_trans': ['', 'bitr', 'ntr', 'tr'], '1_pass': ['', '0.0', '1.0'], '1_wo': ['', 'N-Vtr', 'OV', 'S', 'SOV', 'SV', 'V', 'Vtr-LOC-Nposs'], '2_kh_full_1': ['kkkhk', 'and'], '2_kh_full_2': ['lkjmljlj', 'or'], '2_per_full_1': ['', 'or'], '2_so': ['', '0.0', '1.0'], '2_trans': ['', 'bitr', 'ntr', 'tr'], '2_pass': ['', '0.0', '1.0'], '2_wo': ['', 'N-Vtr', 'OV', 'S', 'SOV', 'SV', 'V', 'Vtr-LOC-Nposs']}

    req_dicts = chunker2(req_dict, result.text_list)
    for elem in req_dicts:
        clean_dict(elem, result.text_list)
    print(req_dict)
    print(req_dicts)
    query = find_evth(req_dicts, corp_id)
    # print(query)
    with engine.connect() as con:
        results = con.execute(query)

    result.res_dicts = dicter(results, result.cols_list)
    
    return render_template('result.html', results=result.res_dicts, cols = result.cols_list, 
                            corp_id=corp_id, query=query, text_cols=result.text_list, enumerate=enumerate)


@app.route('/moksha/result', methods=['get'])
def result():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    cols_list = ['clause', 'tr', 'text', 'subj', 'obj', 'verb', 'wo']
    sel_list = ['text', 'subj', 'obj', 'verb', 'wo']

    req_dict = request.args.to_dict(flat=False)
    req_dicts = chunker(req_dict, len(cols_list), sel_list)
    # results = search_by_parameters(session, req_dicts)
    # session.close()

    query = find_evth(req_dicts, 'data')

    with engine.connect() as con:
        results = con.execute(query)

    res_dicts = dicter(results, cols_list)
    return render_template('result.html', results=res_dicts)

@app.route('/upload')
def upload():
    return (render_template('upload.html',messages = {'main':''} ))


@app.route('/upload/new/<corp_id>')
def upload_new(corp_id):
    query = f'''
    SELECT column_name
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = N'{corp_id}'
    '''

    with engine.connect() as con:
        col_names = con.execute(query)
        
    col_names = [col_name[0] for col_name in col_names]

    return (render_template('upload_new.html', corp_id = corp_id, col_names=col_names, messages = {'main':''} ))

@app.route('/end_of_new_upl', methods=['post'] )
def end_of_new_upl():
    if request.method == 'POST':
        corp_id = request.form.get('corp_id')
        corp_name = request.form.get('name')
        sel_cols = request.form.getlist('sel_cols')
        text_cols = request.form.getlist('text_cols')
        id = int(corp_id.split('_')[1])
        sel = ','.join(sel_cols)
        text = ','.join(text_cols)
        
        sh = gc.create(f'{corp_name} permissions blank')
        sh.share('', perm_type='anyone', role='writer', with_link=True)

        perm_id = sh.id
        spreadsheet = gc.open_by_key(perm_id)
        worksheet = spreadsheet.add_worksheet('blank', rows=3, cols=3)
        worksheet.update('A1', 'Please use the «Share» function to set permissions')
        main_link = url_for('main_page', _external=True)
        worksheet.update('B3', f'=HYPERLINK("{main_link}";"MAIN PAGE")', raw=False)
        spreadsheet.del_worksheet(spreadsheet.sheet1)

        insert_values_metadata(id, corp_name, sel, text, perm_id)
    return redirect(sh.url)    
    

@app.route('/res_corp', methods=['post'])
def res_corp():
    #print(request.files)
    cols_str = ''
    if request.method == 'POST':
        file = request.files.get('filename')
        #formm = request.form.get('lang_select')
        #new_lang = request.form.get('lang_name')
        #print("nuka 4etut", file.filename, 'a ento: ', str(formm), "echo:", new_lang)
    if file.filename != '':
        
        file.save(file.filename)
        check = check_file(file.filename)
        print(check)
        if check == False:
            ress = f"Use the following spreadsheet as the reference. Remember to have FW_project sheet, for more information see the template: "
            flash(ress, category = 'error')
            os.remove(os.path.abspath(file.filename))
            return redirect(request.referrer)
        else:
            res = main(file.filename)
            # flash("Your data was successfully uploaded", category='success')
            os.remove(os.path.abspath(file.filename))
            return redirect(url_for('upload_new', corp_id=res))

    flash("Please attach a file!", category = 'error')
    return redirect(request.referrer)

def save_res():
    res = result.res_dicts
    #print(res)
    cols = result.cols_list
    #print(cols)
    with open("FW_GUI_results.csv", 'w') as file:
        writer = csv.DictWriter(file, delimiter = ",", 
                                 lineterminator="\r", fieldnames=cols)
        writer.writeheader()
        #writer.writerow(cols)
        for elem in res:
            writer.writerow(elem)
    return(file.name)

@app.route('/get_file', methods=['get'])
def get_file():
    save_res()
    return send_file('./FW_GUI_results.csv')
    #return redirect(url_for('main_page'))

@app.route('/read_gsheet', methods=['get'])
def read_gsheet():
    res = result.res_dicts

    df = pd.DataFrame(res)
    n_rows = len(df) + 1
    n_cols = len(df.columns)

    sh = gc.create('Search results')
    sh.share('', perm_type='anyone', role='reader')
    # sh.share('saltymon@gmail.com', perm_type='user', role='owner')

    spreadsheet = gc.open('Search results')
    worksheet = spreadsheet.add_worksheet('search results', rows=n_rows, cols=n_cols)
    spreadsheet.del_worksheet(spreadsheet.sheet1)
    set_with_dataframe(worksheet, df)

    return redirect(sh.url)

@app.route('/get_stats', methods=['get'])
def get_stats():
    data = result.res_dicts
    text_list = result.text_list
    #print(sel_list)
    for elem in data:
        [elem.pop(key) for key in text_list]
    #print(all_data)    
    return (render_template('stats.html', data = data, sel_cols = result.sel_list ))

@app.route('/edit_gsheet', methods=['post'])
def edit_gsheet():
    # res = result.res_dicts

    if request.method == 'POST':
        corp_id = request.form.get('corp_id')
        query = request.form.get('query')

    with engine.connect() as con:
        df = pd.read_sql_query(query, con)
    n_rows = len(df) + 1
    n_cols = len(df.columns)

    id = int(corp_id.split('_')[1])
    perm_query = f'SELECT perm_id FROM languages WHERE id = {id}'

    with engine.connect() as con:
        perm_res = con.execute(perm_query)

    perm_id = list(perm_res)[0][0]
    perm_list = gc.list_permissions(perm_id)
    # print(perm_list)

    sh = gc.create('Search results')
    for user in perm_list:
        if 'emailAddress' in user:
            sh.share(user['emailAddress'], perm_type=user['type'], role=user['role'], notify=False)
    sh.share('', perm_type='anyone', role='reader')
    # sh.share('saltymon@gmail.com', perm_type='user', role='owner')

    spreadsheet = gc.open('Search results')
    worksheet = spreadsheet.add_worksheet('search results', rows=n_rows, cols=n_cols)
    spreadsheet.del_worksheet(spreadsheet.sheet1)
    set_with_dataframe(worksheet, df)

    submit_worksheet = spreadsheet.add_worksheet('submit', rows=3, cols=3)
    submit_worksheet.update('A1', 'Submit all changes and upload them to corpus:')
    submit_link = url_for('corp_update', corp_id=corp_id, sh_id=spreadsheet.id, _external=True)
    submit_worksheet.update('B3', f'=HYPERLINK("{submit_link}";"SUBMIT")', raw=False)

    # schedule.every(1).minutes.do(corp_update, corp_id=corp_id, sh_id=spreadsheet.id, wsh_id=worksheet.id)
    # schedule.every(1).hours.do(corp_update, corp_id=corp_id, sh_id=spreadsheet.id, wsh_id=worksheet.id)
    # stop_run_continuously = run_continuously()

    return redirect(sh.url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

