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


class PathCompleter:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.index = -1
        self.candidates = []
        pathsep = '/' if sys.platform != 'win32' else '\\'
        if pathsep in prefix:
            # if the prefix contains path separator, then we only complete the last part
            root, part = prefix.rsplit(pathsep, 1)
            for path in os.listdir(root):
                if path.startswith(part):
                    self.candidates.append(os.path.join(root, path))
        else:
            for path in os.listdir():
                if path.startswith(prefix):
                    self.candidates.append(path)

    def next(self):
        if not self.candidates:
            return None
        if self.index == -1:
            old = self.prefix
        else:
            old = self.candidates[self.index]
        self.index = (self.index + 1) % len(self.candidates)
        return old, self.candidates[self.index]


class Shell:
    def __init__(self):
        self.buffer = []
        self.prompt = None
        self.completer = None

    def process_line(self, s: str) -> None:
        print(s, flush=True)

    def get_prompt(self) -> str:
        return '>> '

    def _write_prompt(self):
        self.prompt = self.get_prompt()
        sys.stdout.write(self.prompt)
        sys.stdout.flush()

    def backspace_s(self, s: str):
        back_counts = len(s.encode('gbk'))
        sys.stdout.write('\b' * back_counts + ' ' * back_counts + '\b' * back_counts)
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
                self.completer = None
                if self.buffer:
                    removed = self.buffer.pop()
                    self.backspace_s(removed)
                    continue
            if c in ('\r', '\n'):
                self.completer = None
                sys.stdout.write('\r')
                text = ''.join(self.buffer)
                self.process_line(text)
                self.buffer.clear()
                self._write_prompt()
            elif c == '\t':
                text = ''.join(self.buffer)
                if self.completer is None:
                    words = text.split()
                    if words and words[-1]:
                        self.completer = PathCompleter(words[-1])

                if self.completer is not None:
                    completed = self.completer.next()
                    if completed:
                        old, new = completed
                        self.backspace_s(old)
                        sys.stdout.write(new)
                        sys.stdout.flush()
                        self.buffer[ -len(old) : ] = list(new)
            else:
                self.completer = None
                # if c is not a control character
                if re.match(r'[\x20-\x7e]', c):
                    sys.stdout.write(c)
                    sys.stdout.flush()
                    self.buffer.append(c)