import os
import pathlib
import sys

class PathCompleter:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.index = -1
        self.candidates = []
        pathsep = '/' if sys.platform != 'win32' else '\\'
        if pathsep in prefix:
            root = pathlib.Path(prefix).parent
            part = pathlib.Path(prefix).name
            for path in os.listdir(root):
                if path.startswith(part):
                    self.candidates.append(os.path.join(root, path))
        else:
            for path in os.listdir():
                if path.startswith(prefix):
                    self.candidates.append(path)
        self.candidates.sort(key=lambda x: len(x))

    def next(self):
        if not self.candidates:
            return None
        if self.index == -1:
            old = self.prefix
        else:
            old = self.candidates[self.index]
        self.index = (self.index + 1) % len(self.candidates)
        return old, self.candidates[self.index]