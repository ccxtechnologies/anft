# Copyright: 2018, CCX Technologies

import asyncio
import async_timeout


def wait_intialized(func):
    async def func_wrapper(self, *args, **kwargs):
        if not self.initialized.is_set():
            async with async_timeout.timeout(self.timeout):
                await self.initialized.wait()
        return await func(self, *args, **kwargs)

    return func_wrapper


class Nft:

    timeout = 8
    PROMPT = b'nft> \n'

    def __init__(self, loop=None):

        self.initialized = asyncio.Event()
        self.lock = asyncio.Lock()
        self.nft = None
        self.loop = asyncio.get_event_loop() if loop is None else loop

        asyncio.ensure_future(self._initialize(), loop=self.loop)

    def __del__(self):
        if (self.nft is not None) and (self.nft.returncode is None):
            self.nft.terminate()

    async def _initialize(self):
        if self.initialized.is_set() or (self.nft is not None):
            raise RuntimeError("Already Initialized")

        await self._start_nft()

        self.initialized.set()

    async def _start_nft(self):
        self.nft = await asyncio.create_subprocess_exec(
                '/sbin/nft',
                '--echo',
                '--handle',
                '--stateless',
                '--interactive',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                loop=self.loop,
        )

    @wait_intialized
    async def cmd(self, *command, _recurse=0):
        """Send an nft command."""

        if (self.nft is None) or (self.nft.returncode is not None):
            raise RuntimeError("Nft isn't initialized or has stopped")

        retry = False
        async with self.lock:
            self.nft.stdin.write(b'\n')

            prompt = None
            while prompt != self.PROMPT:
                async with async_timeout.timeout(self.timeout):
                    prompt = await self.nft.stdout.readline()

            self.nft.stdin.write(' '.join(command).encode() + b'\n\n')

            prompt, echo, response, error, other = None, None, None, None, b''

            if command[0] in ('create', 'add', 'insert'):
                cmd = b'add'
            elif command[0] in ('flush', 'delete', 'reset', 'replace'):
                cmd = b'None'
                response = b''
            else:
                cmd = command[0].encode()

            while (
                    (prompt is None) or (echo is None)
                    or ((response is None) and (error is None))
            ):
                try:
                    async with async_timeout.timeout(self.timeout):
                        status = await self.nft.stdout.readline()

                except asyncio.TimeoutError:
                    if _recurse < 3:
                        retry = True
                        break

                    else:
                        raise asyncio.TimeoutError(
                                f"nft timeout: {' '.join(command).encode()}\n"
                                f"prompt ==> {prompt}\necho ==> {echo}\n"
                                f"response ==> {response}\nerror ==> {error}\n"
                                f"other ==> {other}"
                        )

                if not status:
                    break

                if status == self.PROMPT:
                    prompt = status
                elif status.startswith(self.PROMPT[:-1]):
                    echo = status
                elif status.startswith(cmd):
                    response = status
                elif status.startswith(b'Error:'):
                    error = status
                else:
                    other += status

        if retry:
            # lose the socket sometimes, no idea why

            self.nft.terminate()
            await self._start_nft()

            # Can remove this once we get a better
            # handle on what's going on
            import syslog
            syslog.syslog(f"+++ Retrying Command: {command}")

            return await self.cmd(*command, _recurse=_recurse + 1)

        if error is not None:
            if b'File exists' in error:
                raise FileExistsError()
            elif b'No such file or directory' in error:
                raise FileNotFoundError()
            else:
                raise RuntimeError(f"{' '.join(command)} => {error.decode()}")
        else:
            return response.decode()

    async def cmd_stateful(self, *command):
        """Send an nft command so read from stateful objects
        (like counters)."""

        process = await asyncio.create_subprocess_exec(
                'nft',
                '--echo',
                '--handle',
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                loop=self.loop
        )

        try:
            async with async_timeout.timeout(3):
                stdout, stderr = await process.communicate()
        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()

        if process.returncode:
            if b'File exists' in stderr:
                raise FileExistsError()
            else:
                raise RuntimeError(
                        f"Command {' '.join(command)}"
                        f" failed {process.returncode}:"
                        f"\n{stderr.decode()}\n{stdout.decode()}"
                )

        return stdout.decode()
