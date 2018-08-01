# Copyright: 2018, CCX Technologies

import asyncio
import async_timeout

from .nft import wait_intialized


class Set:

    init_timeout = 15

    def __init__(
            self,
            name,
            table,
            type_,
            flag_constant=False,
            flag_interval=False,
            flag_timeout=False,
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

        self.initialized = asyncio.Event()

        self.nft = table.nft
        self.name = name
        self.table = table.name
        self.family = table.family

        if type_ not in (
                'ipv4_addr', 'ipv6_addr', 'ether_addr', 'inet_proto',
                'inet_service', 'mark'
        ):
            raise RuntimeError(f"Invalid type {type_}")

        self.config = []
        self.config.append(f"type {type_};")

        flags = []
        if flag_constant:
            flags.append('constant')
        if flag_interval:
            flags.append('interval')
        if flag_timeout:
            flags.append('timeout')
        if flags:
            self.config.append(f"flags {','.join(flags)};")

        if timeout:
            self.config.append(f"timeout {timeout};")

        if gc_interval:
            self.config.append(f"gc-interval {gc_interval};")

        if elements:
            self.config.append(f"elements = {{ {','.join(elements)} }};")

        if size:
            self.config.append(f"size {size};")

        if policy:
            self.config.append(f"policy {policy};")

        if auto_merge:
            self.config.append(f"auto-merge;")

    async def load(self, flush_existing=False):
        """Load the set, must be called before calling any other methods."""

        if self.initialized.is_set():
            raise RuntimeError("Already Initialized")

        await self.nft.cmd(
                'add', 'set', self.family, self.table, self.name,
                f"{{ {' '.join(self.config)} }}"
        )

        if flush_existing:
            await self.nft.cmd(
                    'flush', 'set', self.family, self.table, self.name
            )

        self.initialized.set()

    @wait_intialized
    async def flush(self):
        """Flush all elements of the chain."""
        await self.nft.cmd('flush', 'set', self.family, self.table, self.name)

    @wait_intialized
    async def delete(self):
        """Delete the set, any subsequent calls to this chain will fail."""
        await self.flush()
        await self.nft.cmd('delete', 'set', self.family, self.table, self.name)

        self.initialized.clear()

    @wait_intialized
    async def list(self):
        """List all elements of the set."""
        return await self.nft.cmd(
                'list', 'set', self.family, self.table, self.name
        )

    @wait_intialized
    async def add_elements(self, elements):
        """Add a list of elements to the set."""
        await self.nft.cmd(
                'add', 'element', self.family, self.table, self.name,
                f"{{ {','.join(elements)} }}"
        )

    @wait_intialized
    async def remove_elements(self, elements):
        """Remove a list of elements to the set."""
        await self.nft.cmd(
                'delete', 'element', self.family, self.table, self.name,
                f"{{ {','.join(elements)} }}"
        )

    def __str__(self):
        return f"@{self.name}"
