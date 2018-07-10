# Copyright: 2018, CCX Technologies

import asyncio
import async_timeout


class Nftables:
    def __init__(self, loop=None, timeout=15):

        self.timeout = timeout
        self._command_queue = asyncio.Queue()

        self.loop = asyncio.get_event_loop() if loop is None else loop
        asyncio.ensure_future(self._nft_interactive(), loop=self.loop)

    async def _nft_interactive(self):
        process = await asyncio.create_subprocess_exec(
                'nft',
                '--interactive',
                stdin=asyncio.subprocess.PIPE,
                loop=self.loop
        )

        while True:
            command = await self._command_queue.get()
            process.stdin.write(command.encode() + b'\n')

    async def add_table(self, table, protocol='ip'):
        await self._command_queue.put(f'add table {protocol} {table}')
        await self._command_queue.put(f'flush table {protocol} {table}')
