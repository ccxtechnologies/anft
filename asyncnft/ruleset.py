# Copyright: 2018, CCX Technologies

from .nft import Nft
from .table import Table


class Ruleset:
    def __init__(self, loop=None):
        """The ruleset keyword is used to identify the whole set of tables,
        chains, etc. currently in place in kernel."""

        self.nft = Nft(loop)

    async def cmd(self, command, *args):
        return await self.nft.cmd(command, 'ruleset', *args)

    async def flush(self):
        """Clear the entire ruleset. This will remove all tables and whatever
        they contain, effectively leading to an empty ruleset - no packet
        filtering will happen anymore, so the kernel accepts any valid packet
        it receives.
        """

        await self.cmd('flush')

    async def list(self):
        """
        List the ruleset contents.
        """

        return await self.cmd('list')

    async def table(self, name, flush_existing=False):
        """Create a new (or load an existing) Table.

        If flush_existing is True and the table already exists it will be
        flushed."""

        table = Table(name, self)
        await table.load(flush_existing)
        return table
