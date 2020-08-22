import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from sys import stdout
from time import time, sleep
from typing import List

from aiocqhttp import CQHttp, Event
from rapidfuzz import process

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(stream=stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
log.addHandler(console_handler)

file_handler = logging.FileHandler(filename='log.csv')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s, %(levelname)s, %(name)s, %(message)s'))
log.addHandler(file_handler)

FAQ: dict = {}
QUESTIONS: List[str] = []

CHI_BOT = 1486024403
CORPUS: List[str] = []
TRIGGER: List[str] = []
REFUSE: List[str] = []
BOOK: List[str] = []

COMMAND_REGEX = re.compile(r'问\s*(\S+)')


class Config:
    repeat_prob: float
    repeat_delay: float
    weak_prob: float
    weak_delay: float
    battle_prob: float
    recall_react_delay: float

    def __init__(self,
                 repeat_prob: float,
                 repeat_delay: float,
                 weak_prob: float,
                 weak_delay: float,
                 battle_prob: float,
                 recall_react_delay: float):
        self.repeat_prob = repeat_prob
        self.repeat_delay = repeat_delay
        self.weak_prob = weak_prob
        self.weak_delay = weak_delay
        self.battle_prob = battle_prob
        self.recall_react_delay = recall_react_delay


active_config = Config(
    repeat_prob=0.8,
    repeat_delay=0.5,
    weak_prob=1,
    weak_delay=0.5,
    battle_prob=0.4,
    recall_react_delay=0.5
)

night_config = Config(
    repeat_prob=0.2,
    repeat_delay=1,
    weak_prob=0.5,
    weak_delay=2,
    battle_prob=0.05,
    recall_react_delay=0.5
)

daylight_config = Config(
    repeat_prob=0.05,
    repeat_delay=2,
    weak_prob=0.06,
    weak_delay=4,
    battle_prob=0.03,
    recall_react_delay=1
)

bot = CQHttp()


def answer_book():
    return {'reply': random.choice(BOOK)}


def answer_weakness():
    return {'reply': random.choice(CORPUS)}


def answer_battle():
    return {'reply': random.choice(TRIGGER) + f' [CQ:at,qq={CHI_BOT}]'}


def answer_repeat(event):
    return {'reply': event.raw_message}


@bot.on_message('group')
async def _(event: Event):
    config = None

    if f'[CQ:at,qq={event.self_id}]' in event.raw_message:
        config = active_config
        for message in filter(lambda m: m['type'] == 'text', event.message):
            msg: str = message['data']['text'].strip('?？')
            log.debug(f'AT    {event.sender["card"]} -> {msg}')

            if msg.startswith('问'):
                start = time()
                question = COMMAND_REGEX.search(msg).groups()[0]
                (match_choice, score) = process.extractOne(question, QUESTIONS)
                end = time()
                log.info(','.join([str(x) for x in [question, match_choice, score, end - start]]))
                if score < 20:
                    return {'reply': random.choice(REFUSE + ['无可奉告'])}
                if score < 50:
                    return {'reply': f'你要问的是不是 {match_choice}'}
                else:
                    return {'reply': f'{match_choice}：\n{FAQ[match_choice]}'}
            if msg.startswith('我') and msg.endswith('吗'):
                return answer_book()
            elif msg == 'all':
                return {'reply': '\n'.join(QUESTIONS)}

    r = random.random()

    if config is None:
        if datetime.now().hour < 8:
            log.debug(f'NIGHT {r} {event.sender["card"]} -> {event.raw_message}')
            config = night_config
        else:
            log.debug(f'DAY   {r} {event.sender["card"]} -> {event.raw_message}')
            config = daylight_config

    if '[CQ:video' in event.raw_message:
        return answer_weakness()

    (match_choice, score) = process.extractOne(event.raw_message, TRIGGER + CORPUS)
    log.debug(f'{event.sender["card"]} == 检测卖弱 {config.weak_prob}')
    log.info(','.join([str(x) for x in [event.raw_message, match_choice, score]]))
    if score > 50 and r < config.weak_prob:
        sleep(random.random() * config.weak_delay)
        if r < config.battle_prob:
            return {'reply': random.choice(TRIGGER) + f' [CQ:at,qq={CHI_BOT}]'}
        else:
            return answer_weakness()

    log.debug(f'{event.sender["card"]} == 随机复读 {config.repeat_prob}')
    if r < config.repeat_prob:
        sleep(random.random() * config.repeat_delay)
        return answer_repeat(event)


@bot.on_notice('group_recall')
async def recall(event: Event):
    return answer_weakness()


def load_corpus():
    global CORPUS, TRIGGER, REFUSE
    CORPUS = Path('Chi-Corpus/common.txt').read_text('utf-8').splitlines()
    CORPUS = list(filter(lambda c: '?' not in c, CORPUS))
    TRIGGER = Path('Chi-Corpus/trigger.txt').read_text('utf-8').splitlines()
    REFUSE = Path('Chi-Corpus/refuse.txt').read_text('utf-8').splitlines()
    BOOK = Path('answers.txt').read_text('utf-8').splitlines()


def load_faq():
    global FAQ, QUESTIONS
    FAQ = json.loads(Path('faq.json').read_text(encoding='utf-8'))
    QUESTIONS = list(FAQ.keys())


if __name__ == '__main__':
    load_faq()
    load_corpus()
    bot.run(host='localhost', port=8765)
