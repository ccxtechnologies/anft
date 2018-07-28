# Copyright: 2018, CCX Technologies

import asyncio


async def nft(*command, loop=0):

    if loop > 10:
        raise RuntimeError("To many unknown errors")

    process = await asyncio.create_subprocess_exec(
            'nft',
            '--echo',
            '--handle',
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 1:
        await nft(*command, loop=loop+1)

    elif process.returncode:
        if b'File exists' in stderr:
            raise FileExistsError()
        else:
            raise RuntimeError(
                    f"Command {' '.join(command)} failed {process.returncode}:"
                    f"\n{stderr.decode()}\n{stdout.decode()}"
            )

    return stdout.decode()
