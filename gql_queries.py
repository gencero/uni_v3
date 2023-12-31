def generate_query_all_tokens(skip_count):
    all_tokens = """{
        tokens (first: 1000, skip: %s, orderDirection: desc, orderBy: totalSupply, where: {name_ends_with: "Dvision"}) {
            id
            symbol
            name
            decimals
        }
        }""" % (
        skip_count
    )

    #where: {totalSupply_gte: "5", whitelistPools_: {volumeToken0_gte: "1", volumeToken1_gte: "1"}}


    # all_tokens = """{
    #     tokens (first: 1000, skip: %s, where: { name_ends_with: "Dvision"}) {
    #         id
    #         symbol
    #         name
    #         decimals
    #     }
    #     }""" % (
    #     skip_count
    #  )


    return all_tokens