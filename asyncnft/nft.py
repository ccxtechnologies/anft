# Copyright: 2018, CCX Technologies

import asyncio


async def nft(*command):
    process = await asyncio.create_subprocess_exec(
            'nft',
            '--echo',
            '--handle',
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode:
        if b'File exists' in stderr:
            raise FileExistsError()
        else:
            raise RuntimeError(
                    f"Command {' '.join(command)} failed:"
                    f"\n{stderr.decode()}"
            )

    return stdout.decode()
