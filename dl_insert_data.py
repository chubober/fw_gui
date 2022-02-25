
from os import error
import gspread
import httplib2
import json

import numpy as np
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import sqlalchemy
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, JSON
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import Column, Integer, Text
from sqlalchemy.sql.expression import any_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import session, sessionmaker

engine = create_engine('postgresql+psycopg2://lingvist:lingvistpassword@178.154.193.115:5432/mydatabase')
connection = psycopg2.connect(user="lingvist",
                                    password="lingvistpassword",
                                    host="178.154.193.115",
                                    port="5432",
                                    database="mydatabase")
cursor = connection.cursor()

def proper_column_names(dff):
  #dff.columns = ['n', 'clause', 'tr', 'comments', 'text', 'gloss', 'tr1', 'scheme_gloss', 'scheme-gloss1', '3', 'structure', '4', '5', '6', 'subj','obj','verb','v','other','wo', '7', 'text1', '8']
  for elem in dff:
    dff[elem] = dff[elem.lower()].astype(object)
  return dff


def create_corp_table(id, cols):
  st = ""
  for elem in cols:
    new_col = f' "{str(elem)}" text'
    if st != "":
      st+= ', '
    st += new_col.lower()
  #print(st)
  query = f"""CREATE TABLE IF NOT EXISTS corp_{id} ( {st} )"""
  cursor.execute(query)
  connection.commit()
  return


def create_metatable():
  query = """CREATE TABLE IF NOT EXISTS languages (
    id serial PRIMARY KEY,
    name VARCHAR(255),
    sel_cols VARCHAR(255),
    text_cols VARCHAR(255),
    perm_id VARCHAR(255)
    )"""
  cursor.execute(query)
  connection.commit()
  return

def insert_new_line():
  query = f"insert into languages (name, sel_cols, text_cols) values (NULL,NULL,NULL) "
  cursor.execute(query)
  connection.commit()
  cursor.execute("select id from languages order by id desc limit 1")
  res = cursor.fetchall()
  return res[0][0]

def insert_values_metadata(id, name, sel_cols, text_cols, perm_id):
  query = f"update languages set name = '{name}', sel_cols = '{sel_cols}', text_cols = '{text_cols}', perm_id = '{perm_id}' where id = {id} "
  cursor.execute(query)
  connection.commit()



def make_options():
  options = []
  query = f"select name from languages"
  cursor.execute(query)
  results = cursor.fetchall()
  for elem in results:
    #print(" ".join(elem))
    options.append(" ".join(elem))
  return options

def save_to_db(text):
  '''
  Добавляем новые строки в таблицу на сервере
  '''
  try:
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

def download_new_texts(filename):
  data = get_colnames(filename)
  #texts_set = set(data[0].tolist())
  test_list=data.values.tolist()
  for elem in data:
    new_text = [x for x in test_list]
    h = [["" if pd.isnull(x) else x for x in elem] for elem in new_text]

  print(h)
  #test_list=test1.values.tolist()
  #h = [["" if pd.isnull(x) else x for x in elem] for elem in new_text]
  #print(h)

def read_excel(filename):
  test = pd.read_excel(filename, sheet_name = "FW_project",  na_values = "", keep_default_na = False)
  return test

def col_names(filename):
  data = read_excel(filename)
  cols = data.columns
  values = cols.values
  return values, data

def insert_into_corp_table(data, id):
    st = ""
    for elem in data.columns:
      new_v = '%s'
      if st != "":
        st+= ', '
      st += new_v
    query = f"insert into corp_{id} values ({st})"
    #data.fillna("")
    for row in data.values:
      for ix, cell in enumerate(row):
        if pd.isna(cell):
          row[ix] = None
      #print(row)
      record_to_ins = tuple(row)
      cursor.execute(query, record_to_ins)
    connection.commit()    


def get_colnames(filename):
  test = pd.read_excel(filename, sheet_name = "FW_project",  na_values = "", keep_default_na = False)
  return test

def check_file(filename):
  xl = pd.ExcelFile(filename)
  sheets = xl.sheet_names
  for elem in sheets:
    if elem == "FW_project":
      return True
  return False

def add_primary(id):
  query = f"""ALTER TABLE corp_{id} ADD COLUMN ID SERIAL PRIMARY KEY"""
  cursor.execute(query)
  connection.commit()
  return



def main(filename):
  #engine = create_engine('postgresql+psycopg2://lingvist:lingvistpassword@178.154.193.115:5432/mydatabase')
  #connection = psycopg2.connect(user="lingvist",
  #                                  password="lingvistpassword",
  #                                  host="178.154.193.115",
  #                                  port="5432",
  #                                  database="mydatabase")
  #cursor = connection.cursor()
  create_metatable()
  id = insert_new_line()
  names, data = col_names(filename)
  create_corp_table(id, names)
  insert_into_corp_table(data, id)
  add_primary(id)

  #return
  return(f'corp_{id}')



