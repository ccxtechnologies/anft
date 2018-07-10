# Copyright: 2018, CCX Technologies

from .nft import nft


class Set:

    initialized = False

    def __init__(
            self,
            name,
            table,
            type_,
            flag_constant=False,
            flag_interval=False,
            flag_timout=False,
            timeout=None,
            gc_interval=None,
            elements=None,
            size=None,
            policy='performance',
            auto_merge=False
    ):
        """Named sets are sets that need to be defined first before they can be
        referenced in rules. Unlike anonymous sets, elements can be added to or
        removed from a named set at any time."""

        self.name = name
        self.table = table.name
        self.family = table.family

        if type_ not in (
                'ipv4_addr', 'ipv6_addr', 'ether_addr', 'inet_proto',
                'inet_service', 'mark'
        ):
            raise RuntimeError(f"Invalid type {type_}")

        self.type = f"type {type_}"

        flags = []
        if flag_constant:
            flags.append('constant')
        if flag_interval:
            flags.append('constant')

    async def load(self):
        """Load the set, must be called before calling any other methods."""

        if self.initialized:
            return

        await nft('add', 'set', self.family, self.table, self.name)

        self.initialized = True

    async def flush(self):
        """Flush all rules of the chain."""
        if not self.initialized:
            raise RuntimeError(f"Chain {self.name} hasn't been loaded.")

        await nft('flush', 'chain', self.family, self.table, self.name)

    async def delete(self):
        """Delete the chain, any subsequent calls to this chain will fail."""
        if not self.initialized:
            raise RuntimeError(f"Chain {self.name} hasn't been loaded.")

        await self.flush()
        await nft('delete', 'chain', self.family, self.table, self.name)

        self.initialized = False

    async def list(self):
        """List all rules of the specified chain."""
        return await nft('list', 'chain', self.family, self.table, self.name)

    async def insert_rule(self, statement):
        """Insert the rule at the top of the chain."""

        rule = Rule(statement, self)
        await rule.insert()

    async def append_rule(self, statement):
        """Append rule at the bottom of the chain."""

        rule = Rule(statement, self)
        await rule.insert()

    def __str__(self):
        if not self.initialized:
            raise RuntimeError(f"Set {self.name} hasn't been loaded.")

        return f"@{self.name}"
