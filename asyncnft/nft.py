# Copyright: 2018-2019, CCX Technologies

import asyncio
import async_timeout
import syslog
import signal


def wait_intialized(func):
    async def func_wrapper(self, *args, **kwargs):
        if not self.initialized.is_set():
            async with async_timeout.timeout(self.timeout):
                await self.initialized.wait()
        return await func(self, *args, **kwargs)

    return func_wrapper


class Nft:

    timeout = 30
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
        def _preexec_function():
            # Ignore the SIGINT signal by setting the handler to the standard
            # signal handler SIG_IGN.
            signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.nft = await asyncio.create_subprocess_exec(
                '/sbin/nft',
                '--echo',
                '--handle',
                '--interactive',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                loop=self.loop,
                preexec_fn=_preexec_function,
        )

    @wait_intialized
    async def cmd(self, *command, _recurse=0):
        """Send an nft command."""

        if self.nft is None:
            raise RuntimeError("Nft isn't initialized.")

        if self.nft.returncode is not None:
            raise RuntimeError(f"Nft has stopped: {self.nft.returncode}")

        async with self.lock:
            self.nft.stdin.write(' '.join(command).encode() + b'\n')

            prompt, echo, response, error = False, None, b'', None

            while True:
                try:
                    async with async_timeout.timeout(self.timeout):
                        status = await self.nft.stdout.readline()

                except asyncio.TimeoutError:
                    syslog.syslog(
                            f"nft timeout: {' '.join(command).encode()}\n"
                            f"prompt ==> {prompt}\n"
                            f"echo ==> {echo}\n"
                            f"response ==> {response}\n"
                            f"error ==> {error}\n"
                    )
                    raise asyncio.TimeoutError(
                            f"nft timeout: {' '.join(command).encode()}\n"
                            f"prompt ==> {prompt}\n"
                            f"echo ==> {echo}\n"
                            f"response ==> {response}\n"
                            f"error ==> {error}\n"
                    )

                if not status:
                    break

                if status == self.PROMPT:
                    prompt = status

                elif status.startswith(self.PROMPT[:-1]):
                    echo = status
                    self.nft.stdin.write(b'\n')

                elif status.startswith(b'Error:'):
                    error = status

                else:
                    response += status

                if echo and prompt:
                    break

        if error is not None:
            if b'File exists' in error:
                raise FileExistsError(' '.join(command))

            elif b'No such file or directory' in error:
                raise FileNotFoundError(' '.join(command))

            else:
                raise RuntimeError(f"{' '.join(command)} => {error.decode()}")

        return response.decode()
