import traceback
from .utils import error, warning
import re, sys, subprocess
from . import fmt
from .commands.base import Command, FallbackCommand
import os
from .context import Context
from typing import List

def is_identifier(s: str):
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s) is not None

def has_system_command(cmd: str):
    if cmd in ['from', 'import', 'class', 'def']:
        return False
    if sys.platform == 'win32':
        if cmd in ['cls', 'mkdir']:
            return True
        query = f'where {cmd}'
    else:
        query = f'which {cmd}'
    return subprocess.call(query, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def advance_split(s: str):
    """split a string by spaces, but ignore spaces inside quotes"""
    units = []
    unit = ''
    quote = None
    for c in s:
        if c == quote:
            quote = None
        elif c in ['"', "'"]:
            assert quote is None
            quote = c
        elif c == ' ' and quote is None:
            if unit:
                units.append(unit)
            unit = ''
            continue
        unit += c
    if unit:
        units.append(unit)
    return units


class Parsed:
    def __init__(self, s: str):
        self.s = s

    def __call__(self, context: Context):
        """execute the parsed object with the given context
        
        + `context`: a dict-like object that contains the variables
        """
        raise NotImplementedError
    
    def string(self) -> str:
        return self.s
    
    def icon(self):
        return None
    
class EmptyScript(Parsed):
    def __call__(self, context: Context):
        pass

class PythonScript(Parsed):
    def __init__(self, s: str, mode: str = 'single'):
        super().__init__(s)
        self.mode = mode

    def __call__(self, context: Context):
        code = None
        try:
            code = compile(self.s + '\n', '<stdin>', self.mode)
        except SyntaxError as e:
            error(f'line {e.lineno}: {e.msg}')
        except:
            error(traceback.format_exc(), end='')
        if code is None:
            return
        try:
            exec(code, context.g)
        except SystemExit:
            raise
        except:
            tb = traceback.TracebackException(*sys.exc_info())
            tb.stack.pop(0)     # Skips the first stack frame
            error(''.join(tb.format()), end='')

def replace_vars(string: str, context: Context) -> str:
    def replace(m):
        key = m.group(1)
        val = context.get(key)
        if val is Context.DoesNotExist:
            raise KeyError(key)
        return str(val)
    try:
        cmd = string
        for pattern in [r'\${(\w+)}', r'\$(\w+)\b']:
            cmd = re.sub(pattern, replace, cmd)
        return cmd
    except KeyError as e:
        error(f'variable {e} does not exist')
        return string
    
def fmt_replace_vars(string: str) -> str:
    def replace(m):
        return fmt.blue(m.group(0))
    try:
        cmd = string
        for pattern in [r'\${(\w+)}', r'\$(\w+)\b']:
            cmd = re.sub(pattern, replace, cmd)
        return fmt.green(cmd)
    except KeyError as e:
        error(f'variable {e} does not exist')
        return string

class ParsedValue(Parsed):
    def __init__(self, s: str, val):
        super().__init__(s)
        self.val = val

    def __call__(self, context: Context):
        print(self.val)

    def string(self) -> str:
        return fmt.blue(self.s)
    
class ParsedCommand(Parsed):
    pass

class BuiltinCommand(ParsedCommand):
    def __init__(self, s: str, cmd: Command, args: List[str]):
        super().__init__(s)
        self.cmd = cmd
        self.args = args

    def __call__(self, context: Context):
        args = [
            replace_vars(arg, context)
            for arg in self.args
        ]
        self.cmd(context, *args)

    def string(self) -> str:
        return fmt_replace_vars(self.s)
    
    def icon(self):
        return '🍋'

class ShellScript(ParsedCommand):
    def __call__(self, context: Context):
        os.system(replace_vars(self.s, context))

    def icon(self):
        return '🍋'

    def string(self) -> str:
        return fmt_replace_vars(self.s)

class ParsedError(Parsed):
    def __init__(self, s: str, msg: str):
        super().__init__(s)
        self.msg = msg

    def __call__(self, context: Context):
        error(self.msg)

def parse_single(s: str, context: Context) -> Parsed:
    """parse a single unit"""
    if is_identifier(s):
        val = context.get(s)
        if val is not Context.DoesNotExist:
            return ParsedValue(s, val)
        cmd = context.commands.get(s)
        if cmd is not None:
            return BuiltinCommand(s, cmd, [])
        if has_system_command(s):
            return ShellScript(s)
        cmd = context.fallback_commands.get(s)
        if cmd is not None:
            return BuiltinCommand(s, cmd, [])
        return ParsedError(s, f'{repr(s)} is neither a variable nor a command')
    else:
        if os.path.exists(s):
            return ShellScript(s)
        return PythonScript(s)
    
def parse_multi(s: str, units: List[str], context: Context) -> Parsed:
    """parse multiple units"""
    if is_identifier(units[0]):
        cmd = context.commands.get(units[0])
        if cmd is not None:
            return BuiltinCommand(s, cmd, units[1:])
        if has_system_command(units[0]):
            return ShellScript(s)
        cmd = context.fallback_commands.get(units[0])
        if cmd is not None:
            return BuiltinCommand(s, cmd, units[1:])
    if os.path.exists(units[0]):
        return ShellScript(s)
    return PythonScript(s)

class Block:
    """a multiline code block"""
    def __init__(self, need_more_lines: int = 2) -> None:
        # https://github.com/blueloveTH/pocketpy/blob/main/src/repl.cpp
        assert need_more_lines in (2, 3)
        self.buffer = ''
        self.line = None
        self.need_more_lines = need_more_lines

    def string(self):
        return self.line

    def input(self, s: str) -> bool:
        """input a line of code, return True if more lines are needed"""
        if self.need_more_lines > 0:
            self.buffer += s
            self.buffer += '\n'
            n = len(self.buffer)
            if n >= self.need_more_lines:
                for i in range(n-self.need_more_lines, n):
                    # no enough lines
                    if self.buffer[i] != '\n':
                        return True
                self.need_more_lines = 0
                self.line = self.buffer
                self.buffer = ''
                return False
            else:
                return True

def parse(s: str, context: Context) -> Parsed:
    units = advance_split(s)
    if len(units) == 0:
        return EmptyScript(s)
    
    if units[-1].endswith(':'):
        b = Block(3 if units[0] == 'class' else 2)
        assert b.input(s)
        return b

    if len(units) == 1:
        return parse_single(units[0], context)
    return parse_multi(s, units, context)
