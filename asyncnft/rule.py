# Copyright: 2018, CCX Technologies


class Rule:

    handle = 0

    def __init__(self, statement, chain):
        """Rules are added to chain in a table. Rules are constructed from two
        kinds of components according to a set of grammatical rules:
        expressions and statements.

        Refer to the netfilter man page for more info in expressions."""

        self.nft = chain.nft
        self.table = chain.table
        self.family = chain.family
        self.chain = chain.name
        self.statement = statement

    async def insert(self):
        """Insert the rule at the top of the chain."""
        if self.handle:
            raise RuntimeError("Rule already has a handle.")

        response = await self.nft.cmd(
                'insert', 'rule', self.family, self.table, self.chain,
                self.statement
        )

        try:
            self.handle = int(response.split('\n')[0].split('# handle ')[-1])
        except ValueError:
            raise RuntimeError(f"Unable to parse handle from {response}")

    async def append(self):
        """Add the rule at the bottom of the chain."""
        if self.handle:
            raise RuntimeError("Rule already has a handle.")

        response = await self.nft.cmd(
                'add', 'rule', self.family, self.table, self.chain,
                self.statement
        )

        try:
            self.handle = int(response.split('# handle ')[-1])
        except ValueError:
            raise RuntimeError(f"Unable to parse handle from {response}")

    async def delete(self):
        """Delete the specified rule."""

        if not self.handle:
            raise RuntimeError("Rule not attached.")

        await self.nft.cmd_stateful(
                'delete', 'rule', self.family, self.table, self.chain,
                'handle', str(self.handle)
        )

        self.handle = 0

    async def replace(self, statement):
        """Replace the rules statement."""

        if not self.handle:
            raise RuntimeError("Rule not attached.")

        await self.nft.cmd(
                'replace', 'rule', self.family, self.table, self.chain,
                'handle', str(self.handle), statement
        )
