#!/usr/bin/python

from asyncnft import Ruleset
import asyncio

ruleset = Ruleset()

async def _test():
    table = await ruleset.table("test_table")

    chain1 = await table.chain("test_chain1")
    chain2 = await table.chain("test_chain2")

    jrule = await chain1.insert_rule("jump test_chain2")

    print(await table.list())

    await chain2.delete()

    print(await table.list())


    await table.delete()

loop = asyncio.get_event_loop()
loop.run_until_complete(_test())
loop.close()

