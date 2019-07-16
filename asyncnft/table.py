# Copyright: 2018, CCX Technologies

import re
import asyncio

from .chain import Chain
from .chain import BaseChain
from .set import Set
from .counter import Counter
from .nft import wait_intialized

chain_pattern = re.compile(
        r"^\s+chain (?P<chain>\w+) { # handle (?P<handle>\d+)$"
)
jump_pattern = re.compile(r"^\s+jump (?P<chain>\w+) # handle (?P<handle>\d+)$")


class Table:

    timeout = 10

    def __init__(self, name, ruleset):
        """Tables are containers for chains, sets and stateful objects."""

        self.initialized = asyncio.Event()

        self.nft = ruleset.nft
        self.name = name

    async def cmd(self, command, *args):
        return await self.nft.cmd(command, 'table', self.name, *args)

    async def load(self, flush_existing=False):
        """Load the table, must be called before calling any other methods.

        If flush_existing is True and the table already exists it will be
        flushed."""

        if self.initialized.is_set():
            raise RuntimeError("Already Initialized")

        response = await self.cmd('add')
        if flush_existing and not response:
            await self.cmd('flush')

        self.initialized.set()

    @wait_intialized
    async def flush(self):
        """Flush all chains and rules in the table."""
        await self.cmd('flush')

    @wait_intialized
    async def delete(self):
        """Delete the table, any subsequent calls to this table will fail."""
        await self.flush()
        await self.cmd('delete')

        self.initialized.clear()

    @wait_intialized
    async def chain(self, name, flush_existing=False):
        """Create a new (or load an existing) Regular Chain.

        If flush_existing is True and the table already exists it will be
        flushed."""
        chain = Chain(name, self)
        await chain.load(flush_existing)
        return chain

    @wait_intialized
    async def base_chain(
            self,
            name,
            type_,
            hook,
            device=None,
            priority=0,
            policy='accept',
            flush_existing=False
    ):
        """Create a new (or load an existing) Base Chain.

        If flush_existing is True and the table already exists it will be
        flushed."""
        chain = BaseChain(name, self, type_, hook, device, priority, policy)
        await chain.load(flush_existing)
        return chain

    @wait_intialized
    async def set(
            self,
            name,
            type_,
            flag_constant=False,
            flag_interval=False,
            flag_timeout=False,
            timeout=None,
            gc_interval=None,
            elements=None,
            size=None,
            policy='performance',
            auto_merge=False,
            flush_existing=False
    ):
        """Create a new or load an existing set"""
        set_ = Set(
                name,
                self,
                type_,
                flag_constant,
                flag_interval,
                flag_timeout,
                timeout,
                gc_interval,
                elements,
                size,
                policy,
                auto_merge=False
        )
        await set_.load(flush_existing)
        return set_

    @wait_intialized
    async def counter(self, name, flush_existing=False):
        """Create a new (or load an existing) Counter."""
        counter = Counter(name, self)
        await counter.load(flush_existing)
        return counter

    async def list(self):
        """List all chains and rules of the specified table."""
        return await self.cmd('list')

    async def remove_rule_jumps(self, chain):
        """Remove all rules that jump to a chain. (required to clear jumps
        before deleting a chain)."""

        src_chain = ""
        listing = await self.list()
        for line in listing.split('\n'):
            chain_match = chain_pattern.match(line)
            if chain_match:
                src_chain = chain_match['chain']
                continue

            jump_match = jump_pattern.match(line)
            if jump_match and (jump_match['chain'] == chain.name):
                await self.nft.cmd(
                        'delete', 'rule', self.name, src_chain, 'handle',
                        jump_match['handle']
                )

    def __str__(self):
        return self.name
