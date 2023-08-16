import re
import sys
import ctypes
import os

def error(msg: str, end='\n'):
    # use red color
    print(f'\033[91m{msg}\033[0m', end=end)

def warning(msg: str, end='\n'):
    # use yellow color
    print(f'\033[93m{msg}\033[0m', end=end)

import ctypes
import sys

if sys.platform == 'win32':
    libc = ctypes.cdll.msvcrt
    getwch = libc._getwch
else:
    libc = ctypes.cdll.LoadLibrary(None)
    import termios, tty
    def getwch():
        # disable echo
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new)
        tty.setcbreak(sys.stdin.fileno(), termios.TCSANOW)
        # read wchar with no buffer
        c = libc.getwchar()
        # restore echo
        termios.tcsetattr(fd, termios.TCSANOW, old)
        return c


class Shell:
    def __init__(self):
        self.buffer = []
        self.prompt = None

    def process_line(self, s: str) -> None:
        print(s, flush=True)

    def get_prompt(self) -> str:
        return '>> '

    def _write_prompt(self):
        self.prompt = self.get_prompt()
        sys.stdout.write(self.prompt)
        sys.stdout.flush()

    def run(self):
        self._write_prompt()
        while True:
            try:
                c: int = getwch()
                if c == 3: raise KeyboardInterrupt
            except KeyboardInterrupt:
                print()
                exit(0)

            c = chr(c)
            if c == '\b' or c == '\x7f':
                if self.buffer:
                    removed = self.buffer.pop()
                    back_counts = len(removed.encode('gbk'))
                    sys.stdout.write('\b' * back_counts + ' ' * back_counts + '\b' * back_counts)
                    sys.stdout.flush()
                    continue
            if c in ('\r', '\n'):
                sys.stdout.write('\r')
                text = ''.join(self.buffer)
                self.process_line(text)
                self.buffer.clear()
                self._write_prompt()
            elif c == '\t':
                # auto complete
                pass
            else:
                # if c is not a control character
                if re.match(r'[\x20-\x7e]', c):
                    sys.stdout.write(c)
                    sys.stdout.flush()
                    self.buffer.append(c)