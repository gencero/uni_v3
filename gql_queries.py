def generate_query_all_tokens(skip_count):
    all_tokens = """{
        tokens (first: 1000, skip: %s) {
            id
            symbol
            name
            decimals
        }
        }""" % (
        skip_count
    )

    return all_tokens