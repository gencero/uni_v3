from requests.models import HTTPError
from web3 import Web3
import json
import requests
import pandas as pd
import eth_abi.packed
import eth_abi


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

    UNISWAP_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984" 

    with open("./abis/UniswapV3Factory.json", "r") as f:
        uniswap_factory_abi = json.loads(f.read())

    with open("./abis/UniswapV3Pool.json", "r") as f:
        uniswap_pool_abi = json.loads(f.read())

    def __init__(self, w3):
        print("__init__")
        self.w3 = w3

        with open("abis/quoter_abi.json") as jfile:
            self.abi = json.load(jfile)

        self.contract = self.w3.eth.contract(
            address=self.quoter_address, abi=self.abi
        )
        
        self.df = self.load_unique_tokens()

    def _single_fetch(self, to_skip: int) -> set:
        print("_single_fetch")
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
        
        #print("r.status_code: ", r.status_code)    
        if r.status_code == 200:
            for t in r.json()["data"]["tokens"]:

                #if t["id"] == "0xfca59cd816ab1ead66534d82bc21e7515ce441cf":
                #    print("RARI XX:", self.w3.to_checksum_address(t["id"]) )    

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
        print("load_unique_tokens")
        all_tokens = []
        to_skip = 0

        r = self._single_fetch(to_skip)
        all_tokens = all_tokens + r

        #while len(r) == 1000:
        #print(to_skip)
        # while to_skip < 500:
        #     print("****** ", to_skip)
        #     to_skip += 500
        #     r = self._single_fetch(to_skip)
        #     all_tokens = all_tokens + r

        with open('emre.json', 'w') as f:
            json.dump(all_tokens, f)

        df = pd.DataFrame(all_tokens)

        # data = df.to_json('./self_df.json', orient='index')

        print("end load_unique_tokens")
        return df

    def update_unique_tokens(self):
        print("update_unique_tokens") 
        self.df = self.load_unique_tokens()

    def _update_batches(self):
        print("_update_batches")  
        # self.batches = [self.call_list[i:i + 2000] for i in range(0, len(self.call_list), 2000)]
        self.batches = [self.call_list[i:i + 1000] for i in range(0, len(self.call_list), 1000)]

        with open('batches.json', 'w') as f:
            json.dump(self.batches, f)

        #with open("batches2.json", 'w') as file_handler:
        #    for item in self.batches:
        #        file_handler.write("{}\n".format(item))
        
        #with open('batches2.txt', 'w') as out_file:
        #    json.dump(self.batches, out_file, sort_keys = True, indent = 4, ensure_ascii = False)

    def _update_call_list(self):
        print("_update_call_list")  
        self.call_list = self.df["rpc_in"].tolist() + self.df["rpc_out"].tolist()
        with open('call_list.json', 'w') as f:
            json.dump(self.call_list, f)

        self._update_batches()

    def get_pool_address(self, token0_address, token1_address, fee):
        factory = self.w3.eth.contract(address = self.UNISWAP_FACTORY_ADDRESS , abi = self.uniswap_factory_abi)

        pool_address = factory.functions.getPool(token0_address, token1_address, fee).call()

        print("***** pool_address: ", pool_address)

        return pool_address
        # print("token0_address ", token0_address)
        # pool_address = self.contract.functions.getPool(token0_address, token1_address, fee).call()
        # print("pool_address: ", pool_address)
        # return pool_address
    
    def get_sqrt_price(self, pool_address):
        pool_contract = self.w3.eth.contract(address = pool_address , abi = self.uniswap_pool_abi)

        slot0 = pool_contract.functions.slot0().call()
        print(slot0)
        sqrtPriceX96 = slot0[0]

        return sqrtPriceX96

    def calc_price_with_sqrt(self, sqrtPrice, decimal0, decimal1):
        diff_decimals = decimal1-decimal0

        price = sqrtPrice **2 / 2**192
        print("USDC/ETH: ", price / 10**(diff_decimals))
        price = 1/price * 10**diff_decimals
        print("**** price: ", price)

    def encode_txs(self, fee=3000):
        print("encode_txs")  
    #def encode_txs(self, fee=3000):
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
        # print("self.WETH: ", self.WETH)
        self.df["encoded_in"] = self.df["address"].apply(
            lambda x: self.contract.functions.quoteExactInputSingle(
            self.WETH, x, fee, self.ETH_SIZE, 0
        )._encode_transaction_data()
        )

        # self.df["encoded_in"] = self.df["address"].apply(
        #     lambda x: self.contract.functions.quoteExactInput(
        #     eth_abi.packed.encode_packed(['address','uint24','address'], [self.WETH, fee, x]), self.ETH_SIZE
        # )._encode_transaction_data()
        # )

        # path = eth_abi.packed.encode_packed(['address','uint24','address'], [self.WETH, 3000, self.quoter_address])
        
        # path = eth_abi.encode(['address','uint24','address'],[self.WETH, 3000, self.quoter_address])
        # print("path: ", path)

        # print("decode: ", eth_abi.decode(['address','uint24','address'],path))

        # pool_adr = self.get_pool_address('0x514910771AF9Ca656af840dff83E8264EcF986CA', self.WETH, 3000)
        # print("**** pool_adr: ", pool_adr)
        # sqrtPrice = self.get_sqrt_price(pool_adr)
        # print("**** sqrtPrice: ", sqrtPrice)
        # self.calc_price_with_sqrt(sqrtPrice, 18, 18)

        encoded_in = self.df["encoded_in"].to_json('./encoded_in.json', orient='index')

        self.df["encoded_out"] = self.df["address"].apply(
            lambda x: self.contract.functions.quoteExactOutputSingle(
            x, self.WETH, fee, self.ETH_SIZE, 0
        )._encode_transaction_data()
        )

        # self.df["encoded_out"] = self.df["address"].apply(
        #     lambda x: self.contract.functions.quoteExactOutput(
        #     eth_abi.packed.encode_packed(['address','uint24','address'], [x, fee, self.WETH]), self.ETH_SIZE
        # )._encode_transaction_data()
        # )

        #pool adresini df'ye alabiliyoruz bu şekilde.
        # self.df["pool_address"] = self.df["address"].apply(
        #     lambda x: self.contract.functions.getPool(
        #         x, self.WETH, 10000
        # )._encode_transaction_data()
        # )

        # const decoded = web3.eth.abi.decodeParameters(
        # // Decoding event data. Exclude the `indexed` parameters.
        # ["address", "uint256", "uint256", "uint16", "address"],
        # removeFunctionSelector(data)
        # );

        # self.df["slot0"] = self.df["pool_address"].apply(
        #     lambda x: self.contract.functions.slot0(
        #         self.contract(address = x , abi = self.abi)
        # )._encode_transaction_data()
        # )

        

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
        print("get_prices")   
        prices = self.df.copy()

        all_r = []

        for batch in self.batches:
            print("self.http_url: ", self.http_url)
            #print("batch: ", batch)
            #print("len batch: ", len(batch))

            headers = {'Content-Type': 'application/json', 'Accept':'application/json'}    
            r = requests.post(self.http_url, json=batch, headers=headers)
            #r = requests.post(self.http_url, data=open('batches2.txt', 'rb'), headers=headers)
            #r = requests.post(self.http_url, data=json.dumps(batch), headers=headers)

            #with open('batches.json') as json_file:
            #    json_data = json.load(json_file)
            #    print("XXX", json_data)

            #r = requests.post(self.http_url, data=json.dumps(json_data), headers=headers)
            #r = requests.post(self.http_url, data=json.dumps(json_data), headers=headers)

            #print("r: ", r.json())
            print("r.status_code: ", r.status_code)
            if r.status_code == 200:
                all_r = all_r + r.json()

                #print("all_r len : ", all_r)
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

        # with open("Output.txt", "w") as text_file:
        #     text_file.write(prices.to_string()) 

        # with open("dataframe.txt", "w") as text_file:
        #     text_file.write(r_df.to_string()) 

        # if prices["address"] == "0x10633216e7e8281e33c86f02bf8e565a635d9770":
        #     print("OK OK OK")
        # else:
        #     print("NOK")

        print("len : ", len(prices))

        #ethToTokenPrice = r_df["result"].iloc[:len(prices)].to_json('./ethToTokenPrice.json', orient='index')
        #etokenToETHPrice = r_df["result"].iloc[-len(prices):].tolist().to_json('./tokenToETHPrice.json', orient='index')

        data = prices.to_json('./prices.json', orient='index')
        data = r_df.to_json('./r_df.json', orient='index')

        # print("XX ", r_df["result"].iloc[:len(prices)])

        # print("YY ", r_df["result"].iloc[-len(prices):])

        prices["ethToTokenPrice"] = r_df["result"].iloc[:len(prices)]
        prices["tokenToETHPrice"] = r_df["result"].iloc[-len(prices):].tolist()

        # data = prices.to_json('./prices2.json', orient='index')

        prices = prices.dropna(subset=["ethToTokenPrice"])

        # data = prices.to_json('./prices3.json', orient='index')

        prices["tokenToETHPrice"] = prices["tokenToETHPrice"].fillna("0")

        # data = prices.to_json('./prices4.json', orient='index')

        prices["ethToTokenPrice"] = prices["ethToTokenPrice"].apply(lambda x: int(x, 16))
        prices["tokenToETHPrice"] = prices["tokenToETHPrice"].apply(lambda x: int(x, 16))

        # data = prices.to_json('./prices5.json', orient='index')

        prices["decimals"] = prices["decimals"].astype("int64")

        # data = prices.to_json('./prices6.json', orient='index')

        prices["ethToTokenPrice"] = prices["ethToTokenPrice"] / 10 ** prices["decimals"]

        # data = prices.to_json('./prices7.json', orient='index')

        def handle_zeros_1(row):
            if row["tokenToETHPrice"] == 0:
                return 0
            else:
                return row["tokenToETHPrice"] / 10 ** row["decimals"]

        prices["tokenToETHPrice"] = prices.apply(
            handle_zeros_1, axis=1
        )

        #prices["ethToTokenPrice"] = 1 / prices["ethToTokenPrice"] 
        def handle_zeros_2(row):
            if row["tokenToETHPrice"] == 0:
                return 0
            else:
                return 1 / row["tokenToETHPrice"]

        prices["tokenToETHPrice"] = prices.apply(
            handle_zeros_2, axis=1
        )
        #print("4")

        # data = prices.to_json('./prices_last.json', orient='index')

        self.prices = prices

    def dump_to_API_format(self):
        print("dump_to_API_format")    
        # target_cols = ["name", "symbol", "address", "ethToTokenPrice", "tokenToETHPrice", "decimals", "pool_address"]
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