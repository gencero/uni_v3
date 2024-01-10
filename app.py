import quoter, data_submission
from constants import HTTP_URL

from web3 import Web3
import time
import datetime
import json
import traceback

print("Point a")

w3 = Web3(Web3.HTTPProvider(HTTP_URL))

print("point b")

q = quoter.Quoter(w3)
#q.load_unique_tokens()
q.encode_txs()

print("point c")

ok_counter = 0

current_block = w3.eth.block_number

print("starting")

while True:
    try:
        while current_block == w3.eth.block_number:
            time.sleep(3)
            print(f"{datetime.datetime.now()} --- Waiting on {current_block} at {w3.eth.block_number}")

        current_block = w3.eth.block_number

        q.get_prices()

        d = q.dump_to_API_format()
        with open('submission_data.json', 'w') as f:
            json.dump(d, f)

        data_submission.post_data(
           q.dump_to_API_format()
        )

        print(f"{datetime.datetime.now()} --- Ok block:", current_block)

        ok_counter += 1
        if ok_counter > 100:
            ok_counter = 0
            print(f"{datetime.datetime.now()} --- Processed 100 blocks OK")
            
    except Exception as e:
        print(f"{datetime.datetime.now()} --- FAILED on block {current_block} ({ok_counter} OK)")
        print(f"{datetime.datetime.now()}: {e}")
        print(traceback.format_exc())

        w3 = Web3(Web3.HTTPProvider(HTTP_URL))

        time.sleep(1)

        q = quoter.Quoter(w3)
        q.load_unique_tokens()
        q.encode_txs()

        current_block = w3.eth.block_number
        ok_counter = 0

