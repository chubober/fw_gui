
from os import error
import gspread
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import sqlalchemy
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlite3
from sqlalchemy import create_engine

def proper_column_names(dff):
  dff.columns = ['n', 'clause', 'tr', 'comments', 'text', 'gloss', 'tr1', 'scheme_gloss', 'scheme-gloss1', '3', 'structure', '4', '5', '6', 'subj','obj','verb','v','other','wo', '7', 'text1', '8']
  for elem in dff:
    dff[elem] = dff[elem].astype(object)
  return dff

def create_db():

  engine = create_engine('postgresql+psycopg2://lingvist:lingvistpassword@178.154.193.115/mydatabase')

  CREDENTIALS_FILE = 'client-secret.json'

  creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'])

  httpAuth = creds.authorize(httplib2.Http())
  service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
  client = gspread.authorize(creds)

  sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1FCJWHM149zndo3i4iTXyXV6CJD3lujJarHSk6h8e5Qw/edit?usp=sharing").sheet1

  list_of_hashes = sheet.get_all_records()

  dataframe = pd.DataFrame(list_of_hashes)
  df = dataframe.iloc[:400]
  df.to_sql("data", con=engine, if_exists='replace', method='multi', index = True, index_label='id')

  return 

def save_to_db(text):
  '''
  Добавляем новые строки в таблицу на сервере
  '''
  try:
      connection = psycopg2.connect(user="lingvist",
                                    password="lingvistpassword",
                                    host="178.154.193.115",
                                    port="5432",
                                    database="mydatabase")
      cursor = connection.cursor()

      #id не проставляются автоматически, делаем это вручную
      postgres_select_query = """ select max(id) from data"""
      cursor.execute(postgres_select_query)
      results = cursor.fetchall()
      res = int(''.join(map(str,results[0])))

      #если строка с такой клаузой и названием текста уже есть, то мы ее пропускаем и не вставляем
      postgres_insert_query = """ INSERT INTO data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s);"""
      for elem in text:
        el= elem[1].replace("'", "''")
        query = f"SELECT * FROM data WHERE clause = '{el}' and text = '{elem[4]}'"
        cursor.execute(query)
        res1 = cursor.fetchall()
        #print(len(res1))
        if len(res1) > 0:
          continue
        #здесь вставляем айди и саму строку в таблицу
        elem.insert(0, res+1)
        record_to_insert = tuple(elem)
        #print(record_to_insert)
        cursor.execute(postgres_insert_query, record_to_insert)
        res+=1
      connection.commit()
      
  except (Exception, psycopg2.Error) as error:
      print("Failed to insert record into mobile table", error)

  finally:
      # closing database connection.
      if connection:
          cursor.close()
          connection.close()
          print("PostgreSQL connection is closed")

def merge_dfs(df1, df2):
  #merged = pd.merge(df1, df2, on = 'clause', right_index=True, how='outer')
  #merged[merged['_merge'] == 'right_only']
  merged = pd.concat([df1,df2]).drop_duplicates(keep=False)
  return merged.values.tolist()

def main(filename):
  try:
    test = pd.read_excel(filename, sheet_name = "FW_project",  na_values = "", keep_default_na = False)

    test1 = proper_column_names(test)
    texts_set = set(test['text'].tolist())
    test_list=test1.values.tolist()

    for text_name in texts_set:
      new_text = [x for x in test_list if x[21] == text_name]
      h = [["" if pd.isnull(x) else x for x in elem] for elem in new_text]
      if len(new_text) > 0:
        save_to_db(h)
    return
  except Exception as error:
    return error
