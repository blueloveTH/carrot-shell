from .commands.base import Command, FallbackCommand
import builtins
import os

class Context:
    DoesNotExist = object()

    def __init__(self) -> None:
        self.g = {}
        self.history = []
        self.commands = {}
        self.fallback_commands = {}

    def register_command(self, cmd: Command):
        assert isinstance(cmd, Command)
        if isinstance(cmd, FallbackCommand):
            self.fallback_commands[type(cmd).__name__] = cmd
        else:
            self.commands[type(cmd).__name__] = cmd

    def __getitem__(self, key: str):
        val = self.get(key)
        if val is Context.DoesNotExist:
            raise KeyError(key)
        return val
    
    def __setitem__(self, key: str, val):
        self.g[key] = val

    def get(self, key: str):
        val = self.g.get(key, Context.DoesNotExist)
        if val is not Context.DoesNotExist: return val
        val = builtins.__dict__.get(key, Context.DoesNotExist)
        if val is not Context.DoesNotExist: return val
        val = os.environ.get(key, Context.DoesNotExist)
        if val is not Context.DoesNotExist: return val
        return Context.DoesNotExist