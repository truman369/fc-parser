#!/usr/bin/env python3

# internal imports
import locale
import logging
import re
from datetime import datetime, timedelta

# external imports
import mechanicalsoup

# config vars
source_link = 'https://2b.2fnl.com/competitions/season-2024/3/'
output_file = 'out.htm'
log_file = 'parser.log'
team = 'Коломна'

# init logging
logging.basicConfig(
    filename=log_file,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
)
# set russian locale for datetime parsing
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
# init browser
br = mechanicalsoup.StatefulBrowser()
br.open(source_link)

# get list of dates and urls for all games of team
games = []
for row in br.page.find(class_='games-table').children:
    if isinstance(row, str) or 'class' not in row.attrs.keys():
        continue
    if row.attrs['class'][0] == 'games-tour-tr':
        g_date = row.text.strip()
    if re.search(team, row.text):
        g_time = row.find(class_='match-date').text.replace('-', '00:00')
        g_date = datetime.strptime(f'{g_date} {g_time}', '%d %B %Y %H:%M')
        url = br.absolute_url(row.find(class_='game-score').a.get('href'))
        games.append({
            'date': g_date,
            'url': url,
        })

if len(games) == 0:
    logging.error('Empty list of games')
    exit(1)

# caclultate last and next games
for idx, game in enumerate(games):
    if game['date'] > datetime.now():
        next_game = game
        if idx > 0:
            last_game = games[idx-1]
        else:
            last_game = next_game
        break
    if idx == len(games) - 1:
        logging.error('No more games')
        exit(1)

# check time from last game and set current game
if last_game['date'] + timedelta(days=1) > datetime.now():
    game = last_game
else:
    game = next_game

# get current game url data and format output
br.open(game['url'])
res = br.page.find(class_='game-header')
res = re.sub(r'/upload/s4y_teams/\d+/BigImage/', '/team/big/', res.prettify())
res = res.replace('href="/', f"href=\"{br.absolute_url('/')}")

# update file if needed
try:
    with open(output_file, 'a+t') as f:
        f.seek(0)
        old = f.read()
        if old != res:
            logging.info(f'Current game: {game["date"]}')
            f.truncate(0)
            f.write(res)
            logging.info(f'File updated: {output_file}')
        else:
            logging.debug('Nothing to change')
except Exception as e:
    logging.error(f'File update failed: {e}')
