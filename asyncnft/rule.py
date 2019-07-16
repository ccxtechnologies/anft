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
        self.chain = chain.name
        self.statement = statement

    async def cmd(self, command, *args):
        return await self.nft.cmd(
                command, 'rule', self.table, self.chain, *args
        )

    async def insert(self, before=None):
        """Add the rule at the top of the chain if before is None,
            otherwise append before the rule passed in the before argument."""

        if self.handle:
            raise RuntimeError("Rule already has a handle.")

        if before is not None:
            if before.handle is None:
                raise RuntimeError("Before rule has no handle.")
            statement = f"position {before.handle} {self.statement}"
        else:
            statement = self.statement

        response = await self.cmd('insert', statement)

        try:
            self.handle = int(response.split('\n')[0].split('# handle ')[-1])
        except ValueError:
            raise RuntimeError(f"Unable to parse handle from {response}")

    async def append(self, after=None):
        """Add the rule at the bottom of the chain if after is None,
            otherwise append after the rule passed in the after argument."""

        if self.handle:
            raise RuntimeError("Rule already has a handle.")

        if after is not None:
            if after.handle is None:
                raise RuntimeError("After rule has no handle.")
            statement = f"position {after.handle} {self.statement}"
        else:
            statement = self.statement

        response = await self.cmd('add', statement)

        try:
            self.handle = int(response.split('# handle ')[-1])
        except ValueError:
            raise RuntimeError(f"Unable to parse handle from {response}")

    async def delete(self):
        """Delete the specified rule."""

        if not self.handle:
            raise RuntimeError("Rule not attached.")

        await self.cmd('delete', 'handle', str(self.handle))

        self.handle = 0

    async def replace(self, statement):
        """Replace the rules statement."""

        if not self.handle:
            raise RuntimeError("Rule not attached.")

        await self.cmd('replace', 'handle', str(self.handle), statement)
