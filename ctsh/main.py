import os, sys
from .utils import *
from .parser import *
from . import commands, fmt
from .version import __version__

class CarrotShell(Shell):
    def __init__(self):
        super().__init__()
        self.context = Context()
        # add command.base
        for _, obj in commands.base.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, Command):
                self.context.register_command(obj())

        # add common modules
        self.context.g['os'] = os
        self.context.g['sys'] = sys

        self.context.g['__context__'] = self.context
        # temp variables
        self.curr_block = None

        self.curr_history_count = None
        self.curr_history_index = None

        # only display this on startup
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_info = f"(Python {python_ver} on {sys.platform})"
        if os.environ.get('CTSH_FIRST_RUN_FLAG') is None:
            print(f"CarrotShell {__version__} {python_info}")
            print(fmt.blue("https://github.com/blueloveTH/carrot-shell"))
            print()
            os.environ['CTSH_FIRST_RUN_FLAG'] = '1'
        else:
            name = fmt.blue(os.environ.get("CONDA_DEFAULT_ENV"))
            print(f'switch to {name} {python_info}')

    def get_prompt(self) -> str:
        cwd = os.getcwd()
        home_path = os.path.expanduser('~')

        prefix = ''
        conda_env = os.environ.get('CONDA_DEFAULT_ENV')
        if conda_env is not None:
            prefix += fmt.gray(f'({conda_env}) ')

        if cwd.startswith(home_path):
            cwd = '~' + cwd[len(home_path):]
        cwd = fmt.gray(cwd)

        prompt = f'{prefix}{cwd} 🥕 '
        if self.curr_block is not None:
            prompt = prompt[:-2] + '... '
        return prompt
    
    def toggle_history(self, delta: int):
        # if two count is not equal, reset index
        if self.curr_history_count != len(self.context.history):
            self.curr_history_count = len(self.context.history)
            self.curr_history_index = len(self.context.history) - 1
        else:
            # if two count is equal, change index
            self.curr_history_index += delta
        # clamp index
        if self.curr_history_index < 0:
            self.curr_history_index = 0
        if self.curr_history_index >= len(self.context.history):
            self.curr_history_index = len(self.context.history) - 1
        # if index is valid, change buffer
        if 0 <= self.curr_history_index < len(self.context.history):
            self.backspace_s(self.buffer)
            self.buffer = self.context.history[self.curr_history_index]
            self.write(self.buffer)
    
    def handle_custom_key(self, c) -> bool:
        if sys.platform == 'win32':
            if c == 224:
                c = getwch()
                if c == 72:     # up
                    self.toggle_history(-1)
                elif c == 80:   # down
                    self.toggle_history(1)
                elif c == 77:   # right
                    pass
                elif c == 75:   # left
                    pass
                else:
                    raise NotImplementedError
                return True
        elif c == 27:
            c = getwch()
            if c != 91:
                return
            c = getwch()
            if c == 65:     # up
                self.toggle_history(-1)
            elif c == 66:   # down
                self.toggle_history(1)
            elif c == 67:   # right
                pass
            elif c == 68:   # left
                pass
            else:
                raise NotImplementedError
            return True
        return False
    
    def process_line(self, s: str) -> None:
        prompt = self.prompt

        if s.strip():
            self.context.history.append(s)

        if self.curr_block is not None:
            need_more_lines = self.curr_block.input(s)
            print(prompt + s, flush=True)
            if need_more_lines:
                pass
            else:
                s = self.curr_block.string()
                self.curr_block = None
                PythonScript(s, mode='exec')(self.context)
            return
        
        obj: Parsed = parse(s, self.context)

        if isinstance(obj, Block):
            self.curr_block = obj
            prompt = self.prompt[:-2] + '>>> '
            print(prompt + s, flush=True)
            return
        
        if obj.icon() is not None:
            prompt = self.prompt[:-2] + obj.icon() + ' '
        print(prompt + obj.string(), flush=True)

        try:
            obj(self.context)
        except SystemExit:
            raise
        except:
            error(traceback.format_exc(), end='')

def main():
    # set http_proxy=http://127.0.0.1:7890 & set https_proxy=http://127.0.0.1:7890
    os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    CarrotShell().run()


