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
        "word": "щас|r'izan'-cə|er'a-tamə|.",
        "trans": "",
        "source": "",
        "wo": ["LOC V", 'V'],
        "subj": "pro-1", "obj": "ns", "verb":""
    }, {
        "word": "",
        "trans": "работала",
        "source": "",
        "wo": "",
        "subj": ['pro-1', 'ns', 'pro1pl'], "obj": "", "verb": ""
    }]


def find_evth(cards):
  '''
  Поиск по карточкам
  '''
  connection = psycopg2.connect(user="lingvist",
                                    password="lingvistpassword",
                                    host="178.154.193.115",
                                    port="5432",
                                    database="mydatabase")

  cursor = connection.cursor()
  query = f"""select * from data """

  for card_ix, card in enumerate(cards):
    #print(card_ix, card)
    where = ""
    for key, value in card.items():
      if value == "":
        continue
      if key == 'word' or key == 'trans':
        new_val = "lower("+key+")" + " like lower('%" + value.replace("'", "''") + "%')"
      elif type(value) is list:
        new_val = ""
        for elem_ix, elem in enumerate(value):
          if new_val != "":
            new_val += "or "
          new_val += key + f" = '{elem}' "
        if new_val != "":
          new_val ="("+new_val+ ")"
          #where += l_val
      else:
        new_val = key + f"= '{value}'"
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

    #print(query)

  cursor.execute(query)
  res = cursor.fetchall()
  cursor.close()
  connection.close()
  return res


find_evth(cards)
