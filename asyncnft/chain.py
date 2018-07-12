# Copyright: 2018, CCX Technologies

from .nft import nft
from .rule import Rule


class Chain:

    initialized = False

    def __init__(self, name, table):
        """Regular chains are containers for rules, a regular chain may be
        used as jump target and is used for better rule organization."""

        self.name = name
        self.table = table.name
        self.family = table.family
        self._table = table

    async def load(self, flush_existing=False):
        """Load the chain, must be called before calling any other methods.

        If flush_existing is True and the table already exists it will be
        flushed."""

        if self.initialized:
            return

        try:
            await nft('create', 'chain', self.family, self.table, self.name)
        except FileExistsError:
            if flush_existing:
                await nft('flush', 'chain', self.family, self.table, self.name)

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
        await self._table.remove_rule_jumps(self)
        await nft('delete', 'chain', self.family, self.table, self.name)

        self.initialized = False

    async def list(self):
        """List all rules of the specified chain."""
        return await nft('list', 'chain', self.family, self.table, self.name)

    async def insert_rule(self, statement):
        """Insert the rule at the top of the chain."""

        rule = Rule(statement, self)
        await rule.insert()
        return rule

    async def append_rule(self, statement):
        """Append rule at the bottom of the chain."""

        rule = Rule(statement, self)
        await rule.append()
        return rule

    def __str__(self):
        return self.name


class BaseChain(Chain):
    def __init__(
            self,
            name,
            table,
            type_,
            hook,
            device=None,
            priority=0,
            policy='accept'
    ):
        """A base chain is an entry point for packets from the networking stack.

        The priority parameter accepts a signed integer value which specifies
        the order in which chains with same hook value are traversed. The
        ordering is ascending, i.e. lower priority values have precedence over
        higher ones.

        Base chains also allow to set the chain's policy, i.e. what happens to
        packets not explicitly accepted or refused in contained rules.
        Supported policy values are accept (which is the default) or drop."""

        super().__init__(name, table)

        if type_ not in ('filter', 'nat', 'route'):
            raise RuntimeError(f"Invalid type {type_})")

        if (type_ in ('nat', 'route')) and (self.family not in ('ip', 'ip6')):
            raise RuntimeError(
                    f"Invalid family {self.family} for type {type_}"
            )

        if (
                (
                        self.family in ('ip', 'ip6', 'inet', 'bridge')
                        and hook not in (
                                'prerouting', 'input', 'forward', 'output',
                                'postrouting'
                        )
                )
                or (self.family == 'arp' and hook not in ('input', 'output'))
                or (self.family == 'netdev' and hook != 'ingress')
        ):
            raise RuntimeError(f"Invalid hook {hook} for family {self.family}")

        self.type = f"type {type_}"
        self.hook = f"hook {hook}"
        self.device = f"device {device}" if device else ""
        self.priority = f"priority {priority}"
        self.policy = f" policy {policy}"

    async def load(self, flush_existing=False):
        """Load the chain, must be called before calling any other methods.

        If clear_existing is True and the table already exists it will be
        flushed."""

        if self.initialized:
            return

        try:
            await nft(
                    'create', 'chain', self.family, self.table, self.name,
                    "{ "
                    f"{self.type} {self.hook} {self.device} {self.priority};"
                    f" {self.policy};"
                    " }"
            )
        except FileExistsError:
            if flush_existing:
                await nft('flush', 'chain', self.family, self.table, self.name)
                await nft(
                        'delete', 'chain', self.family, self.table, self.name
                )
                await self.load()

        self.initialized = True
