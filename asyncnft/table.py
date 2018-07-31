# Copyright: 2018, CCX Technologies

import re
import asyncio

from .chain import Chain
from .chain import BaseChain
from .set import Set
from .counter import Counter
from .nft import wait_intialized


class Table:

    timeout = 10

    def __init__(self, name, family, ruleset):
        """Tables are containers for chains, sets and stateful objects.
        They are identified by their address family and their name.

        The address family must be one of ip, ip6, inet, arp, bridge, netdev.
        The inet address family is a dummy family which is used to create
        hybrid IPv4/IPv6 tables. The meta expression nfproto keyword can be
        used to test which family (ipv4 or ipv6) context the packet is being
        processed in. When no address family is specified, ip is used by
        default."""

        if family not in ("ip", "ip6", "inet", "arp", "bridge", "netdev"):
            raise RuntimeError(f"Invalid family {family}")

        self.initialized = asyncio.Event()

        self.nft = ruleset.nft
        self.name = name
        self.family = family

    async def load(self, flush_existing=False):
        """Load the table, must be called before calling any other methods.

        If flush_existing is True and the table already exists it will be
        flushed."""

        if self.initialized.is_set():
            raise RuntimeError("Already Initialized")

        if flush_existing:
            try:
                await self.nft.cmd('flush', 'table', self.family, self.name)
                # need to delete to reset policies
                await self.nft.cmd('delete', 'table', self.family, self.name)
            except FileNotFoundError:
                pass

        await self.nft.cmd('add', 'table', self.family, self.name)

        self.initialized.set()

    @wait_intialized
    async def flush(self):
        """Flush all chains and rules in the table."""
        await self.nft.cmd('flush', 'table', self.family, self.name)

    @wait_intialized
    async def delete(self):
        """Delete the table, any subsequent calls to this table will fail."""
        await self.flush()
        await self.nft.cmd('delete', 'table', self.family, self.name)

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
        return await self.nft.cmd_stateful(
                'list', 'table', self.family, self.name
        )

    async def remove_rule_jumps(self, chain):
        """Remove all rules that jump to a chain. (required to clear jumps
        before deleting a chain)."""

        chain_pattern = re.compile(r"^\s+chain (?P<chain>\w+) {$")
        jump_pattern = re.compile(
                r"^\s+jump (?P<chain>\w+) # handle (?P<handle>\d+)$"
        )

        src_chain = ""
        listing = await self.list()
        for line in listing.split('\n'):
            chain_match = chain_pattern.match(line)
            if chain_match:
                src_chain = chain_match['chain']
                continue

            jump_match = jump_pattern.match(line)
            if jump_match and (jump_match['chain'] == chain.name):
                await self.nft.cmd_stateful(
                        'delete', 'rule', self.family, self.name, src_chain,
                        'handle', jump_match['handle']
                )

    def __str__(self):
        return self.name
