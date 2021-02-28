import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from string import punctuation, whitespace
from sys import stdout
from time import time, sleep
from typing import List
from aiocqhttp import CQHttp, Event
import httpx

# Log utils

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s, %(levelname)s, %(name)s, %(message)s")

console_handler = logging.StreamHandler(stream=stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
log.addHandler(console_handler)

file_handler = logging.FileHandler(filename="log.csv")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
log.addHandler(file_handler)

# Attestation API

KEY = Path("key").read_text(encoding="utf-8")

client = httpx.AsyncClient(headers={"Api-Key": KEY})


async def attest(qq_number: int, token: str):
    payload = {"qq_number": str(qq_number), "token": token}

    resp = await client.post("https://plus.sjtu.edu.cn/attest/verify", json=payload)

    log_content = json.dumps(
        {
            "event": "VERIFICATION",
            "request": payload,
            "response": {"status": resp.status_code, "body": resp.text},
        }
    )

    if resp.status_code == 200 and resp.json().get("success"):
        log.info(log_content)
    else:
        log.warn(log_content)

    return resp.json()


# CQBot

COMMAND_REGEX = re.compile(r"问\s*(\S+)")
bot = CQHttp()


@bot.on_request("group")
async def verify(event: Event):
    if event.sub_type == "add":
        token = event.comment.split("：")[-1]
        result = await attest(event.user_id, token)

        if result and "success" in result:
            if result["success"]:
                return {"approve": True}
            else:
                return {"approve": False}


@bot.on_message("private")
async def echo(event: Event):
    await bot.send(event, repr(event))
    return {"reply": event.message}


if __name__ == "__main__":
    bot.run(host="0.0.0.0", port=8080)
