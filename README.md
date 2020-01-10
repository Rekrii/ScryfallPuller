# ScryfallPuller
Simple python script to pull all released (and soon-to-be released) MTG sets from Scryfall and dump them into a file csv and xlsx.

Currently set up to export the following data:
- cmc
- color_identity
- colors
- foil: is/is-not foil
- mana_cost
- name
- oracle_text
- oversized: is/is-not oversized
- ptl: power/toughness/loyalty (if is planeswalker)
- rarity
- set: set code
- set_name
- type
- usd


Usage:
```
python3 scryfall_puller.py
```
