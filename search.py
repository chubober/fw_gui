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
        "clause": "щас|r'izan'-cə|er'a-tamə|.",
        "tr": "",
        "text": "",
        "wo": ["LOC V", 'V'],
        "subj": "pro-1", "obj": "ns", "verb":""
    }, {
        "clause": "",
        "tr": "работала",
        "text": "",
        "wo": "",
        "subj": ['pro-1', 'ns', 'pro1pl'], "obj": "", "verb": ""
    }]



def find_evth(cards):
  '''
  Поиск по карточкам
  '''

  query = f"""select * from data """

  for card_ix, card in enumerate(cards):
    # print(card_ix, card)
    where = ""
    for key, value in card.items():
      if value == "":
        continue
      if key == 'clause' or key == 'tr':
        new_val = "lower("+key+")" + " like lower('%%" + replace_quot_sql(value) + "%%')"
      elif type(value) is list:
        new_val = ""
        for elem_ix, elem in enumerate(value):
          if new_val != "":
            new_val += "or "
          new_val += key + f" = '{replace_quot_sql(elem)}' "
        if new_val != "":
          new_val ="("+new_val+ ")"
          #where += l_val
      else:
        new_val = key + "= '"+replace_quot_sql(value)+"'"
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


  return query

def replace_quot_sql(t):
  return str(t.replace("'", "''"))