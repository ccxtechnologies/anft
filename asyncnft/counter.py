# Copyright: 2018, CCX Technologies

import re
import asyncio

from .nft import wait_intialized

counter_match = re.compile(
        r"\spackets\s+(?P<packets>\d+)\s+bytes\s+(?P<bytes>\d+)"
)


class Counter:

    init_timeout = 15

    def __init__(
            self,
            name,
            table,
    ):
        """Counter objects are attached to tables and are identified by an
        unique name. They group counter information from rules."""

        self.initialized = asyncio.Event()

        self.nft = table.nft
        self.name = name
        self.table = table.name
        self.family = table.family

    async def load(self, flush_existing=False):
        """Load the set, must be called before calling any other methods."""

        if self.initialized.is_set():
            raise RuntimeError("Already Initialized")

        await self.nft.cmd(
                'add', 'counter', self.family, self.table, self.name
        )

        self.initialized.set()

        if flush_existing:
            await self.reset()

    @wait_intialized
    async def delete(self):
        """Delete the counter, any subsequent calls to this chain will fail."""
        await self.nft.cmd_stateful(
                'delete', 'counter', self.family, self.table, self.name
        )

        self.initialized.clear()

    @wait_intialized
    async def get(self):
        """Get the value of the counter."""
        value = await self.nft.cmd_stateful(
                'list', 'counter', self.family, self.table, self.name
        )
        try:
            return {
                    k: int(v)
                    for k, v in counter_match.search(value).groupdict().items()
            }
        except AttributeError:
            return None

    @wait_intialized
    async def reset(self):
        """Reset the counter."""
        return await self.nft.cmd(
                'reset', 'counter', self.family, self.table, self.name
        )

    def __str__(self):
        return f"counter name {self.name}"
