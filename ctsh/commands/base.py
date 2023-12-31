import os
import argparse
import sys
import shutil
from ..utils import error

class Command:
    def __call__(self, context, *args):
        raise NotImplementedError
    
class FallbackCommand(Command):
    pass

class cd(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='cd')
        self.parser.add_argument('path')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        path = args.path
        if path.startswith('~'):
            path = os.path.expanduser(path)
        if not os.path.exists(path):
            error(f'cd: no such file or directory: {path}')
            return
        if not os.path.isdir(path):
            error(f'cd: not a directory: {path}')
            return
        os.chdir(path)

class clear(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='clear')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        if sys.platform == 'win32':
            os.system('cls')
        else:
            os.system('clear')

class history(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='history')
        self.parser.add_argument('-c', action='store_true', help='clear history')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        if args.c:
            context.history.clear()
            return
        for i in range(len(context.history)-1):
            print(f'{i+1}  {context.history[i]}')

class ls(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='ls')
        self.parser.add_argument('path', nargs='?', default='.')
        self.parser.add_argument('-a', action='store_true', help='show hidden files')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        path = args.path
        if not os.path.exists(path):
            error(f'ls: cannot access {repr(path)}: No such file or directory')
            return
        if not os.path.isdir(path):
            error(f'ls: cannot access {repr(path)}: Not a directory')
            return
        names = []
        for name in sorted(os.listdir(path)):
            if name.startswith('.') and not args.a:
                continue
            if os.path.isdir(os.path.join(path, name)):
                name += '/'
            names.append(name)
        if len(names) == 0:
            print()
            return
        # pretty print name like bash's ls
        # make each column's length equal as far as possible
        max_len = max(map(len, names))
        cols = shutil.get_terminal_size().columns
        cols = cols // (max_len + 1)
        cols = max(cols, 1)
        rows = len(names) // cols
        if len(names) % cols != 0:
            rows += 1
        for i in range(rows):
            for j in range(cols):
                index = j * rows + i
                if index >= len(names):
                    break
                if cols == 1:
                    print(names[index], end='')
                else:
                    print(names[index].ljust(max_len + 1), end='')
            print()

class cp(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='cp')
        self.parser.add_argument('-r', action='store_true', help='copy directories recursively')
        self.parser.add_argument('src')
        self.parser.add_argument('dst')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        src = args.src
        dst = args.dst
        if not os.path.exists(src):
            error(f'cp: cannot stat {repr(src)}: No such file or directory')
            return
        if os.path.isdir(src) and not args.r:
            error(f'cp: cannot copy directory {repr(src)} without -r')
            return
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)

class mv(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='mv')
        self.parser.add_argument('src')
        self.parser.add_argument('dst')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        src = args.src
        dst = args.dst
        if not os.path.exists(src):
            error(f'mv: cannot stat {repr(src)}: No such file or directory')
            return
        shutil.move(src, dst)

class cat(Command):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='cat')
        self.parser.add_argument('path')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        path = args.path
        if not os.path.exists(path):
            error(f'cat: cannot stat {repr(path)}: No such file or directory')
            return
        if os.path.isdir(path):
            error(f'cat: {repr(path)}: Is a directory')
            return
        with open(path) as f:
            print(f.read())

class rm(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='rm')
        self.parser.add_argument('-r', action='store_true', help='remove directories and their contents recursively')
        self.parser.add_argument('-f', action='store_true', help='ignore nonexistent files and arguments, never prompt')
        self.parser.add_argument('path')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        path = args.path
        if not os.path.exists(path):
            if not args.f:
                error(f'rm: cannot remove {repr(path)}: No such file or directory')
            return
        if os.path.isdir(path) and not args.r:
            error(f'rm: cannot remove directory {repr(path)} without -r')
            return
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

class pwd(Command):
    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(prog='pwd')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        print(os.getcwd())


def to_human_readable_size(size):
    if size == 0:
        return '0'
    for x in ['B', 'K', 'M', 'G', 'T']:
        if size < 1000.0:
            # 包括小数点3个字符，如8.0，152，16
            if size < 10:
                return f'{size:.1f}{x}'
            else:
                size = round(size)
                return f'{size}{x}'
        size /= 1000.0

class wget(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='wget')
        self.parser.add_argument('url')

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        url = args.url
        from urllib.request import urlopen
        from urllib.parse import urlparse
        filename = os.path.basename(urlparse(url).path)
        if not filename or filename == '/':
            filename = 'index.html'
        filepath = os.path.join(os.getcwd(), filename)
        with urlopen(url) as f:
            size = int(f.getheader('Content-Length'))
            with open(filepath, 'wb') as f2:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    f2.write(data)
                    percent = f2.tell() / size * 100
                    size_0 = to_human_readable_size(f2.tell()).rjust(5)
                    size_1 = to_human_readable_size(size)
                    print(f'{size_0} / {size_1} ({percent:.2f}%)', end='\r')
                print()


class du(FallbackCommand):
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='du', add_help=False)
        self.parser.add_argument('-h', action='store_true', help='print sizes in human readable format (e.g., 1K 234M 2G)')
        self.parser.add_argument('path', nargs='?', default='.')

    @staticmethod
    def convert_bytes(size):
        return to_human_readable_size(size)

    def _file(self, args, filepath) -> int:
        size = os.path.getsize(filepath)
        if args.h:
            size_s = self.convert_bytes(size)
        else:
            size_s = size
        print(str(size_s).ljust(8), filepath)
        return size

    def _dir(self, args, filepath) -> int:
        size = 0
        for root, dirs, files in os.walk(filepath):
            for f in files:
                size += os.path.getsize(os.path.join(root, f))
        if args.h:
            size_s = self.convert_bytes(size)
        else:
            size_s = size
        print(str(size_s).ljust(8), filepath)
        return size

    def __call__(self, context, *args):
        try:
            args = self.parser.parse_args(args)
        except SystemExit:
            return
        path = args.path
        if not os.path.exists(path):
            error(f'du: cannot access {repr(path)}: No such file or directory')
            return
        if os.path.isdir(path):
            size = 0
            for name in sorted(os.listdir(path)):
                if os.path.isdir(os.path.join(path, name)):
                    size += self._dir(args, os.path.join(path, name))
                else:
                    size += self._file(args, os.path.join(path, name))
            if args.h:
                size = self.convert_bytes(size)
            print(str(size).ljust(8), path)
        else:
            self._file(args, path)
        

class conda(Command):
    def __init__(self) -> None:
        pass

    def activate(self, name: str):
        # get the current module path
        ctsh_path = __file__
        for _ in range(3):
            ctsh_path = os.path.dirname(ctsh_path)

        script = f"__import__('sys').path.append('{ctsh_path}');__import__('runpy').run_module('ctsh')"
        code = os.system(
            f'conda run -n {name} --no-capture-output python -c "{script}"'
        )
        if code == 0:
            exit(0)

    def __call__(self, context, *args):
        if len(args) == 2 and args[0] == 'activate':
            self.activate(args[1])
            return
        if len(args) == 1 and args[0] == 'deactivate':
            self.activate('base')
            return
        full_cmd = 'conda ' + ' '.join(args)
        os.system(full_cmd)

from ast import literal_eval

class export(Command):
    def __call__(self, context, *args):
        flag = False
        for a in args:
            if '=' not in a:
                continue
            key, value = a.split('=')
            if not key or not value:
                continue
            try:
                new_value = literal_eval(value)
                if isinstance(new_value, str):
                    value = new_value
            except:
                pass
            os.environ[key] = value
            flag = True
        if not flag:
            name = type(self).__name__.lstrip('_')
            error(f'{name}: invalid arguments')

class _set(export):
    pass

