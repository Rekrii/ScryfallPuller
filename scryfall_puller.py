'''
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

Need to pip3 install:
requests-html
pandas
openpyxl

'''

from requests_html import HTMLSession
from datetime import datetime, timedelta
import json
import time
import pandas as pd


# Process each card in a list, and basically make sure the
# card is english/en, and print the current progress every 1000 cards
def process_card_list(list):
    for card in list:
        if card['lang'] == 'en':
            add_card_to_db(card)
            if len(db) % 1000 == 0:
                print(len(db))


# Simple page pull using requests, grabbing the content as text then
# doing a json.loads on it here
def pull_page(page_uri):
    print("Pulling page: ", page_uri)
    set_uri = page_uri
    set_response = set_session.get(set_uri)
    content = set_response.text
    return json.loads(content)

# Remove the stuff around the colors on cards. e.g. [W][B] => WB
def fix_color(input):
    return input.replace('[', '').replace(']', '').replace(' ', '').replace(',', '').replace("'", '')


# Set types that ScryFall uses
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

# This is a script, global variable for HTMLSession
set_session = HTMLSession()
# Going through each set that was pulled ignore all digial sets, MTGO/Arena
# compare the release date and make sure it's historial or within the next 45 days
# e.g. don't pull sets from next year
# then continue to process the card list
for set in sets_dict['data']:
    if set['set_type'] in set_names and not set['digital']:
        time.sleep(0.2)  # Sleep a bit to be nice to the API (any limit?)
        set_json = pull_page(set['search_uri'])
        if datetime.strptime(set['released_at'], '%Y-%m-%d') > datetime.now() + timedelta(days=45):
            print("Couldn't pull set, ",
                  set['name'], ". Future release:", set['released_at'])
        elif set_json['object'] == 'error':
            print("Couldn't pull set, ",
                  set['name'], ". Error: ", set_json['details'])
        else:
            process_card_list(set_json['data'])
            # Bit lazy here just checking if we have more data twice,
            # and assuming all sets fit within 3 pages. Should for-loop this.
            if set_json['has_more']:
                page_two = pull_page(set_json['next_page'])
                process_card_list(page_two['data'])
                if page_two['has_more']:
                    page_three = pull_page(page_two['next_page'])
                    process_card_list(page_three['data'])


# Stick all of the cards into a nice dict structure for pandas to handle
# and conver to a csv later on
# too many magic strings here, but it's a hacky script...
db_refine = []
for card in db:
    try:
        c = {}
        c['cmc'] = card['cmc']
        c['color_identity'] = fix_color(str(card['color_identity']))
        c['colors'] = fix_color(str(card.get('colors')))
        c['foil'] = card['foil']
        c['mana_cost'] = card.get('mana_cost')
        c['name'] = card['name']
        c['oracle_text'] = card.get('oracle_text')
        c['oversized'] = card['oversized']
        # If we have loyalty, then stick it into a general 'power-toughness-loyalty' key
        # otherwise get the P/T and store that
        if not card.get('loyalty') is None:
            c['ptl'] = card.get('loyalty')
        elif not card.get('power') is None or not card.get('toughness') is None:
            c['ptl'] = card.get('power') + "/" + card.get('toughness')
        c['rarity'] = card['rarity'][0].upper()  # used rarity code, C/U/R/M
        c['set'] = card['set'].upper()
        c['set_name'] = card['set_name']
        c['type'] = card['type_line']
        c['usd'] = card.get('prices').get('usd')
    except Exception as e:
        print(e)
    db_refine.append(c)

print("Done pulling - Writing to disk")
# Wrap it up in a pandas.Dataframe and then export to csv/excel
# using sensible formatting - yyyy-mm-dd
df = pd.DataFrame(db_refine)
df.to_csv("scryfall_db_" + datetime.today().strftime("%Y-%m-%d") + ".csv")
df.to_excel("scryfall_db_" + datetime.today().strftime("%Y-%m-%d") + ".xlsx")
print("Script complete")


