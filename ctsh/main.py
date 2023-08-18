import os
from .utils import *
from .parser import *
from . import commands, fmt

class CarrotShell(Shell):
    def __init__(self):
        super().__init__()
        self.context = Context()
        self.context.register_command(commands.base.cd())
        self.context.register_command(commands.base.clear())
        self.context.register_command(commands.base.history())
        self.context.register_command(commands.base.cat())

        self.context.register_command(commands.base.ls())
        self.context.register_command(commands.base.cp())
        self.context.register_command(commands.base.mv())
        self.context.register_command(commands.base.rm())
        # add common modules
        self.context.g['os'] = os
        self.context.g['sys'] = sys

        self.context.g['__context__'] = self.context
        # settings
        self.show_prefix = False
        # temp variables
        self.curr_block = None

        self.curr_history_count = None
        self.curr_history_index = None

    def get_prompt(self) -> str:
        cwd = os.getcwd()
        home_path = os.path.expanduser('~')

        if self.show_prefix:
            user = home_path.split('/')[-1]
            host = os.uname().nodename
            if host.endswith('.local'):
                host = host[:-6]
            prefix = f'{user}@{host} '
        else:
            prefix = ''

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
    
    def handle_escape(self, c):
        c = getwch()
        if c != 91:
            return
        c = getwch()
        if c == 65: # up
            self.toggle_history(-1)
        elif c == 66: # down
            self.toggle_history(1)
        elif c == 67: # right
            pass
        elif c == 68: # left
            pass
        else:
            raise NotImplementedError
    
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
    CarrotShell().run()


