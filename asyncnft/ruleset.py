# Copyright: 2018, CCX Technologies

from .nft import nft
from .table import Table


class Ruleset:
    def __init__(self):
        """The ruleset keyword is used to identify the whole set of tables,
        chains, etc. currently in place in kernel."""
        pass

    async def flush(self, family=None):
        """Clear the whole ruleset. This will remove all tables and whatever
        they contain, effectively leading to an empty ruleset - no packet
        filtering will happen anymore, so the kernel accepts any valid packet
        it receives.

        If family is set it will only flush tables for that specific family.
        """

        if family not in (
                None, "ip", "ip6", "inet", "arp", "bridge", "netdev"
        ):
            raise RuntimeError(f"Invalid family {family}")

        await nft('flush', 'ruleset', family if family else '')

    async def list(self, family=None):
        """
        List the ruleset contents.

        If family is set it will only list tables for that specific family.
        """

        if family not in (
                None, "ip", "ip6", "inet", "arp", "bridge", "netdev"
        ):
            raise RuntimeError(f"Invalid family {family}")

        return await nft('list', 'ruleset', family if family else '')

    async def table(self, name, family="ip", flush_existing=False):
        """Create a new (or load an existing) Table.

        If flush_existing is True and the table already exists it will be
        flushed."""

        table = Table(name, family)
        await table.load(flush_existing)
        return table
