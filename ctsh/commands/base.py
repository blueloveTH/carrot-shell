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
        for name in sorted(os.listdir(path)):
            if name.startswith('.') and not args.a:
                continue
            if os.path.isdir(os.path.join(path, name)):
                name += '/'
            print(name, end='  ')
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