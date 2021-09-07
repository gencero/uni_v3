"""
template call:
call = {
    "method": "eth_call",
    "jsonrpc": "2.0",
    "id": n,
    "params": [
        {
            "to": "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
            "data": e,
            },
            "latest"]
    }
"""


def create_rpc_params(
    target_contract_address: str,
    encoded_data: str,
    target_block="latest") -> list:
    """
    returns params field for json-rpc call
    """
    params = [
        {
            "to": target_contract_address,
            "data": encoded_data
        },
        target_block        
    ]

    return params

def create_rpc_call(
    id: int,
    params: list
    ) -> dict:
    """
    constructs a single json-rpc call
    """
    call = {
    "method": "eth_call",
    "jsonrpc": "2.0",
    "id": None,
    "params": None
    }

    call["id"] = id
    call["params"] = params

    return call
