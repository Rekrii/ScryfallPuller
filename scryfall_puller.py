'''
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
'''


from requests_html import HTMLSession
from datetime import datetime, timedelta
import json
import time
import pandas as pd

# pull all sets

set_names = {
    'archenemy', 'commander', 'core', 'draft_innovation', 'duel_deck',
    'expansion', 'from_the_vault', 'masters', 'planechase',
    'premium_deck', 'spellbook', 'starter', 'vanguard'}

session = HTMLSession()
r = session.get('https://api.scryfall.com/sets/')
content = r.text
sets_dict = json.loads(content)

db = []


def add_card_to_db(card):
    db.append(card)


def process_card_list(list):
    for card in list:
        if card['lang'] == 'en':
            add_card_to_db(card)
            if len(db) % 1000 == 0:
                print(len(db))
        # else:
        #   print("Dropped card non-en: ", card)


def pull_page(page_uri):
    print("Pulling page: ", page_uri)
    set_uri = page_uri
    set_response = set_session.get(set_uri)
    content = set_response.text
    return json.loads(content)


set_session = HTMLSession()
for set in sets_dict['data']:
    if set['set_type'] in set_names and not set['digital']:
        time.sleep(0.2)
        set_json = pull_page(set['search_uri'])
        if datetime.strptime(set['released_at'], '%Y-%m-%d') > datetime.now() + timedelta(days=45):
            print("Couldn't pull set, ",
                  set['name'], ". Future release:", set['released_at'])
        elif set_json['object'] == 'error':
            print("Couldn't pull set, ",
                  set['name'], ". Error: ", set_json['details'])
        else:
            process_card_list(set_json['data'])
            if set_json['has_more']:
                page_two = pull_page(set_json['next_page'])
                process_card_list(page_two['data'])
                if page_two['has_more']:
                    page_three = pull_page(page_two['next_page'])
                    process_card_list(page_three['data'])


def fix_color(input):
    return input.replace('[', '').replace(']', '').replace(' ', '').replace(',', '').replace("'", '')


db_refine = []
for card in db:
    try:
        c = {}
        c['name'] = card['name']
        c['set_name'] = card['set_name']
        c['set'] = card['set'].upper()
        c['rarity'] = card['rarity'][0].upper()  # used rarity code, C/U/R/M
        c['colors'] = fix_color(str(card.get('colors')))
        c['color_identity'] = fix_color(str(card['color_identity']))
        c['mana_cost'] = card.get('mana_cost')
        c['cmc'] = card['cmc']
        c['type'] = card['type_line']
        if not card.get('loyalty') is None:
            c['ptl'] = card.get('loyalty')
        elif not card.get('power') is None or not card.get('toughness') is None:
            c['ptl'] = card.get('power') + "/" + card.get('toughness')
        c['oracle_text'] = card.get('oracle_text')
        c['usd'] = card.get('prices').get('usd')
        c['oversized'] = card['oversized']
        c['foil'] = card['foil']
    except Exception as e:
        print(e)
    db_refine.append(c)


df = pd.DataFrame(db_refine)
df.to_csv("db_refine.csv")
df.to_excel("db_refine.xlsx")

print("Done pulling")
