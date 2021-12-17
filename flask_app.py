from flask.helpers import flash, send_file
import pandas as pd
import os
from pandas.io import json
from search import find_evth
from dl_insert_data import main
# import gspread
from sqlalchemy import func
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text
from sqlalchemy.sql.expression import any_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker
from ordered_set import OrderedSet as ordset
from flask import Flask, render_template, request, redirect, sessions, url_for
from werkzeug.utils import secure_filename
import csv
import plotly
import plotly.express as px
import json
# from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)


engine = create_engine('postgresql+psycopg2://lingvist:lingvistpassword@178.154.193.115:5432/mydatabase')

Base = declarative_base()

# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# credentials = ServiceAccountCredentials.from_json_keyfile_name('fw-gui-creds.json', scope)
# client = gspread.authorize(credentials)
# sheet = client.open_by_key('1FCJWHM149zndo3i4iTXyXV6CJD3lujJarHSk6h8e5Qw')
# dataframe = pd.DataFrame(sheet.get_all_records())
app.secret_key = 'rgrwfgkfm5mterfmesmf5k4efmlrkltt5FGTvvtgtgrFTY'

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


def chunker(req_dict, n):
    req_dicts = [dict() for i in range(0, len(req_dict), n)]
    dict_num = 0
    count = 0
    for k, v in req_dict.items():
        k = ''.join(filter(str.isalpha, k))
        if len(v) == 1 and k not in ['text', 'subj', 'obj', 'verb', 'wo']:
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
#     return list(res_set)


def dicter(records):
    dicts = []
    for record in records:
        dic = {}
        dic['id'] = record.id
        dic['clause'] = record.clause
        dic['tr'] = record.tr
        dic['text'] = record.text
        dic['subj'] = record.subj
        dic['obj'] = record.obj
        dic['verb'] = record.verb
        dic['wo'] = record.wo
        dicts.append(dic)
    return dicts


@app.route('/')
def main_page():
    
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
    return render_template('index.html', texts=texts,
                           subjs=subjs, objs=objs,
                           verbs=verbs, wos=wos, messages = {'main':''})

    
    return render_template('index.html')

@app.route('/result', methods=['get'])
def result():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    req_dict = request.args.to_dict(flat=False)
    req_dicts = chunker(req_dict, 7)

    # results = search_by_parameters(session, req_dicts)
    # session.close()

    query = find_evth(req_dicts)

    with engine.connect() as con:
        results = con.execute(query)

    result.res_dicts = dicter(results)
    return render_template('result.html', results=result.res_dicts,
                           isinst=isinstance, lst=list)

@app.route('/upload')
def upload():
    return (render_template('upload.html',messages = {'main':''} ))

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
        '''
        colnames = get_colnames(file.filename)
        cols = colnames.columns
        for elem in cols.values:
            cols_str += str(elem) + ", "
        #print(cols_str)
        insert_into_table(new_lang, cols_str)   
        # filename = secure_filename(file.filename)
        '''
        res = main(file.filename)
        print(res)
        if type(res) == ValueError:
            ress = f"Error: {str(res)}.\nUse the following spreadsheet as the reference. Remember to have FW_project sheet and same columns as the template: "
            flash(ress, category = 'error')
            os.remove(os.path.abspath(file.filename))
            return redirect(request.referrer)
        else:
            flash("Your data was successfully uploaded", category='success')
            os.remove(os.path.abspath(file.filename))
            return redirect(url_for('main_page'))

    flash("Please attach a file!", category = 'error')
    return redirect(request.referrer)


@app.route('/get_file', methods=['get'])
def get_file():
    res = result.res_dicts
    #print(res)
    with open("FW_GUI_results.csv", 'w') as file:
        writer = csv.writer(file)
        writer.writerow(('id', 'clause', 'tr', 'text', 'subj', 'obj', 'verb', 'wo'))
        for dic in res:
            writer.writerow((dic['id'],dic['clause'],dic['tr'],dic['text'], dic['subj'], dic['obj'], dic['verb'], dic['wo']))
    return send_file('./FW_GUI_results.csv')
    #return redirect(url_for('main_page'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

