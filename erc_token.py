class Token:
    """
    Object representing a single coin/oken
    """
    def __init__(self, name, symbol, address, decimals):
        self.name = name
        self.symbol = symbol
        self.address = address
        self.decimals = decimals
        self.ethToTokenPrice = None
        self.tokenToETHPrice = None
        
        #self.query_id = None

    def __dict__(self):
        d = {
            "name": self.name,
            "symbol": self.symbol,
            "address": self.address,
            "decimals": self.decimals,
            "ethToTokenPrice": self.ethToTokenPrice,
            "tokenToETHPrice": self.tokenToETHPrice,
            #"query_id": self.query_id
        }
        return d

    def __str__(self):
        return f"<Coin({self.name} ({self.symbol}) @ {self.address} - Decimals: {self.decimals} - > {self.ethToTokenPrice}/{self.tokenToETHPrice})"