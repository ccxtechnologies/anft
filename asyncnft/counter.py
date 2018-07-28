# Copyright: 2018, CCX Technologies

import re
import asyncio
import async_timeout

from .nft import nft

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

        self.name = name
        self.table = table.name
        self.family = table.family

    async def load(self, flush_existing=False):
        """Load the set, must be called before calling any other methods."""

        if self.initialized.is_set():
            raise RuntimeError("Already Initialized")

        await nft('add', 'counter', self.family, self.table, self.name)

        self.initialized.set()

        if flush_existing:
            await self.reset()

    async def delete(self):
        """Delete the counter, any subsequent calls to this chain will fail."""
        async with async_timeout.timeout(self.init_timeout):
            await self.initialized.wait()

        await nft('delete', 'counter', self.family, self.table, self.name)

        self.initialized.clear()

    async def get(self):
        """Get the value of the counter."""
        async with async_timeout.timeout(self.init_timeout):
            await self.initialized.wait()

        value = await nft(
                'list', 'counter', self.family, self.table, self.name
        )
        try:
            return {
                    k: int(v)
                    for k, v in counter_match.search(value).groupdict().items()
            }
        except AttributeError:
            return None

    async def reset(self):
        """Reset the counter."""
        if not self.initialized:
            raise RuntimeError(f"Counter {self.name} hasn't been loaded.")
        async with async_timeout.timeout(self.init_timeout):
            await self.initialized.wait()

        return await nft(
                'reset', 'counter', self.family, self.table, self.name
        )

    def __str__(self):
        return f"counter name {self.name}"
