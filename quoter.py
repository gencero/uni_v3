from requests.models import HTTPError
from web3 import Web3
import json
import requests
import pandas as pd

import constants
import gql_queries
from erc_token import Token
import rpc_encoder

class Quoter:
    quoter_address = constants.QUOTER_CONTRACT_ADDRESS
    graph_node_url = constants.GQL_URL
    ETH_SIZE = constants.ETH_SIZE
    WETH = constants.WETH_ADDRESS
    http_url = constants.HTTP_URL

    def __init__(self, w3):
        self.w3 = w3

        with open("abis/quoter_abi.json") as jfile:
            self.abi = json.load(jfile)

        self.contract = self.w3.eth.contract(
            address=self.quoter_address, abi=self.abi
        )
        
        self.df = self.load_unique_tokens()

    def _single_fetch(self, to_skip: int) -> set:
        """
        Fetch single graphQL data response
        """
        all_tokens = []
        query = gql_queries.generate_query_all_tokens(to_skip)

        #print("query: ", query)
        r = requests.post(
            self.graph_node_url,
            json = {"query": query},
            headers = {"Content-Type": "application/json"}
            )
        
        if r.status_code == 200:
            for t in r.json()["data"]["tokens"]:

                if t["id"] == "0xfca59cd816ab1ead66534d82bc21e7515ce441cf":
                    print("RARI XX:", self.w3.to_checksum_address(t["id"]) )    

                all_tokens.append(
                    Token(
                        t["name"],
                        t["symbol"],
                        #self.w3.toChecksumAddress(t["id"]),
                        self.w3.to_checksum_address(t["id"]),
                        t["decimals"]
                    ).__dict__() # Hacky way to bypass the use of Token for now
                )
            return all_tokens
        else:
            return []                              

    def load_unique_tokens(self):
        all_tokens = []
        to_skip = 0

        r = self._single_fetch(to_skip)
        all_tokens = all_tokens + r

        while len(r) == 1000:
        #print(to_skip)
        #while to_skip == 5000:
            to_skip += 1000
            r = self._single_fetch(to_skip)
            all_tokens = all_tokens + r

        with open('emre.json', 'w') as f:
            json.dump(all_tokens, f)

        df = pd.DataFrame(all_tokens)
        return df

    def update_unique_tokens(self):
        self.df = self.load_unique_tokens()

    def _update_batches(self):
        self.batches = [self.call_list[i:i + 2000] for i in range(0, len(self.call_list), 2000)]
        with open('batches.json', 'w') as f:
            json.dump(self.batches, f)

    def _update_call_list(self):
        self.call_list = self.df["rpc_in"].tolist() + self.df["rpc_out"].tolist()
        with open('call_list.json', 'w') as f:
            json.dump(self.call_list, f)

        self._update_batches()

    #def encode_txs(self, fee=10000):
    def encode_txs(self, fee=3000):
        """
        Encodes all the tx queries using pandas df operations
        """
        if len(self.df) == 0:
            self.update_unique_tokens()
        
        # TODO: Something more like this (not using apply)
        """
        self.df["encoded_out"] = self.contract.functions.quoteExactInputSingle(
            self.WETH, self.df["address"], fee, self.ETH_SIZE, 0
        )._encode_transaction_data()
        """
        self.df["encoded_in"] = self.df["address"].apply(
            lambda x: self.contract.functions.quoteExactInputSingle(
            self.WETH, x, fee, self.ETH_SIZE, 0
        )._encode_transaction_data()
        )

        orhan_1 = self.contract.functions.quoteExactInputSingle(
            self.WETH, '0x10633216E7E8281e33c86F02Bf8e565a635D9770', fee, self.ETH_SIZE, 0
        ).call()
        print("ORHAN 1: ", orhan_1)
        print("orhan_1:", (orhan_1/(10**18)))

        orhan_2= self.contract.functions.quoteExactOutputSingle(
            '0x10633216E7E8281e33c86F02Bf8e565a635D9770', self.WETH, fee, self.ETH_SIZE, 0
        ).call()
        print("ORHAN 2: ", orhan_2)
        print("orhan 2", (orhan_2/(10**18)))

        encoded_in = self.df["encoded_in"].to_json('./encoded_in.json', orient='index')

        self.df["encoded_out"] = self.df["address"].apply(
            lambda x: self.contract.functions.quoteExactOutputSingle(
            x, self.WETH, fee, self.ETH_SIZE, 0
        )._encode_transaction_data()
        )

        encoded_out = self.df["encoded_out"].to_json('./encoded_out.json', orient='index')

        #TODO: Logger WARN
        #assert len(q.df) == q.df["encoded_out"].nunique(), "Duplicate encodings"
        #assert len(q.df) == q.df["encoded_in"].nunique(), "Duplicate decodings"

        #self.df["padded_idx"] = self.df.index + len(self.df)
        
        self.df["rpc_in"] = self.df.apply(
            lambda x: rpc_encoder.create_rpc_call(
                x.name,
                rpc_encoder.create_rpc_params(
                    self.quoter_address,
                    x["encoded_in"]
                )
            ), axis=1
        )

        rpc_in = self.df["rpc_in"].to_json('./rpc_in.json', orient='index')

        self.df["rpc_out"] = self.df.apply(
            lambda x: rpc_encoder.create_rpc_call(
                x.name + len(self.df),
                rpc_encoder.create_rpc_params(
                    self.quoter_address,
                    x["encoded_out"]
                )
            ), axis=1
        )
        
        rpc_out = self.df["rpc_out"].to_json('./rpc_out.json', orient='index')

        self._update_call_list()

    def get_prices(self):
        prices = self.df.copy()

        all_r = []

        for batch in self.batches:
            print("self.http_url: ", self.http_url)
            #print("batch", batch)
            print("len batch", len(batch))

            headers = {'Content-Type': 'application/json', 'Accept':'application/json'}    
            #r = requests.post(self.http_url, json=batch, headers=headers)
            r = requests.post(self.http_url, data=json.dumps(batch), headers=headers)

            print("r: ", r.json())
            print("r.status_code: ", r.status_code)
            if r.status_code == 200:
                all_r = all_r + r.json()

                print("all_r len : ", all_r)
            else:
                print("HTTPError ", HTTPError)
                raise(HTTPError)
        
        with open('all_r.json', 'w') as f:
            json.dump(all_r, f)

        r_df = pd.DataFrame(all_r)
        r_df = r_df.sort_values(by=["id"])

        data = r_df.to_json('./export.json', orient='index')

        # with open('orhan.json', 'w') as f:
        #    json.dump(r_df, f)

        with open("Output.txt", "w") as text_file:
            text_file.write(prices.to_string()) 

        with open("dataframe.txt", "w") as text_file:
            text_file.write(r_df.to_string()) 

        # if prices["address"] == "0x10633216e7e8281e33c86f02bf8e565a635d9770":
        #     print("OK OK OK")
        # else:
        #     print("NOK")

        # if prices["address"] == "0xFca59Cd816aB1eaD66534D82bc21E7515cE441CF":
        #     print("OK 2")
        # else:
        #     print("NOK 2")

        print("len : ", len(prices))

        #ethToTokenPrice = r_df["result"].iloc[:len(prices)].to_json('./ethToTokenPrice.json', orient='index')
        #etokenToETHPrice = r_df["result"].iloc[-len(prices):].tolist().to_json('./tokenToETHPrice.json', orient='index')

        prices["ethToTokenPrice"] = r_df["result"].iloc[:len(prices)]
        print("1111")
        prices["tokenToETHPrice"] = r_df["result"].iloc[-len(prices):].tolist()
        print("2222")
        prices = prices.dropna(subset=["ethToTokenPrice"])
        print("1")
        prices["tokenToETHPrice"] = prices["tokenToETHPrice"].fillna("0")

        prices["ethToTokenPrice"] = prices["ethToTokenPrice"].apply(lambda x: int(x, 16))
        prices["tokenToETHPrice"] = prices["tokenToETHPrice"].apply(lambda x: int(x, 16))

        prices["decimals"] = prices["decimals"].astype("int64")

        prices["ethToTokenPrice"] = prices["ethToTokenPrice"] / 10 ** prices["decimals"]
        print("2")
        def handle_zeros_1(row):
            if row["tokenToETHPrice"] == 0:
                return 0
            else:
                return row["tokenToETHPrice"] / 10 ** row["decimals"]

        prices["tokenToETHPrice"] = prices.apply(
            handle_zeros_1, axis=1
        )

        #prices["ethToTokenPrice"] = 1 / prices["ethToTokenPrice"] 
        print("3")
        def handle_zeros_2(row):
            if row["tokenToETHPrice"] == 0:
                return 0
            else:
                return 1 / row["tokenToETHPrice"]

        prices["tokenToETHPrice"] = prices.apply(
            handle_zeros_2, axis=1
        )
        print("4")
        print("XXXX: ", prices)
        self.prices = prices

    def dump_to_API_format(self):
        print("dump_to_API_format")    
        target_cols = ["name", "symbol", "address", "ethToTokenPrice", "tokenToETHPrice", "decimals"]

        out = self.prices[target_cols]

        return out.to_dict("records")

if __name__ == "__main__":
    
    from pprint import pprint

    http_url = "https://flamboyant-knuth:maimed-hubcap-evict-chance-frown-circus@nd-835-181-531.p2pify.com"
    
    print("http_url ", http_url)
    w3 = Web3(Web3.HTTPProvider(http_url))

    q = Quoter(w3)

    q.load_unique_tokens()

    q.encode_txs()

    pprint(len(q.batches))
    
    import requests
    import time

    print(q.df.head())

    s = time.time()

    q.get_prices()

    fetch_time = time.time() - s

    print("Fetched prices in", fetch_time)

    data = q.dump_to_API_format()
    print("LEN", len(data))

    import json
    
    with open("data.json", "w") as f:
        json.dump(data, f)