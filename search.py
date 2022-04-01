# import gspread
# import httplib2
# import apiclient.discovery
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd
# import sqlalchemy
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# from sqlalchemy import create_engine

cards = [{
        'clause': 'sss or ghjt', 
        'tr': 'я or он and они', 
        'text': ['AET_AK_inteview_2013', 'LVJ_AK_280713_oryol_i_mysh', 'TAM_IE_04072014_housekeeping'], 
        'subj': ['pro-1'], 
        'obj': ['ns'], 
        'verb': ['intr'], 
        'wo': ['V ADV', 'loc']
    }, {
        'clause': '', 
        'tr': '', 
        'text': ['AET_AK_inteview_2013'], 
        'subj': ['pro-1'], 
        'obj': ['ns'], 
        'verb': ['intr'], 
        'wo': ['V ADV', 'loc']
    }]



def find_evth(cards, corp_id):
  '''
  Поиск по карточкам
  '''

  query = f"""select * from {corp_id} """

  for card_ix, card in enumerate(cards):
    # print(card_ix, card)
    where = ""
    for key, value in card.items():
      if value == "":
        continue
      if type(value) is str:
        new_liv = value.split(' ')
        #print(new_liv)
        new_val = ""
        for word in new_liv:
          if word == "or" or word == "and":
            new_val += word + " "
            continue
          new_val += "lower("+key+")" + " like lower('%%" + replace_quot_sql(word) + "%%') "
        #print(new_val)
        #new_val += "lower("+key+")" + " like lower('%%" + replace_quot_sql(value) + "%%')"
      elif type(value) is list:
        new_val = ""
        for elem_ix, elem in enumerate(value):
          if new_val != "":
            new_val += "or "
          new_val += key + f" = '{replace_quot_sql(elem)}' "
          if elem == '':
            new_val = key + f" is NULL "
        if new_val != "":
          new_val ="("+new_val+ ")"
          #where += l_val
      if new_val != "":
        if where != "":
          where += " and "
        where += new_val
    if 'where' in query:
      query += ' or '
    else:
      query += 'where '
    if where != "":
      query += where

  print(query)
  return query

def replace_quot_sql(t):
  return str(t.replace("'", "''"))

#print(find_evth(cards, 1))