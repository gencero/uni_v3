def generate_query_all_tokens(skip_count):
    # all_tokens = """{
    #     tokens (first: 500, skip: %s, orderDirection: desc, orderBy: totalSupply, where: {totalSupply_gte: "5", whitelistPools_: {volumeToken0_gte: "5", volumeToken1_gte: "5"}}) {
    #         id
    #         symbol
    #         name
    #         decimals
    #     }
    #     }""" % (
    #     skip_count
    # )

    all_tokens = """{
        tokens(first: 500, skip: %s, orderBy: totalValueLockedUSD, orderDirection: desc) {
                id
                symbol
                decimals
                name
                totalSupply
                }
        }""" % (
        skip_count
    )
    
    # {
    #     tokens(
    #         first: 1000
    #         orderDirection: desc
    #         skip: 100
    #         where: {totalSupply_gte: "5", whitelistPools_: {volumeToken0_gte: "1", volumeToken1_gte: "1"}}
    #         orderBy: totalSupply
    #     ) {
    #         id
    #         symbol
    #         decimals
    #         name
    #         totalSupply
    #     }
    # }
    
    #where: {totalSupply_gte: "5", whitelistPools_: {volumeToken0_gte: "1", volumeToken1_gte: "1"}}

    # all_tokens = """{
    #     tokens (first: 1000, skip: %s, where: { name_ends_with: "e"}) {
    #         id
    #         symbol
    #         name
    #         decimals
    #     }
    #     }""" % (
    #     skip_count
    #  )

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