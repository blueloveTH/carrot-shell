def rgb(r: int, g: int, b: int, s: str) -> str:
    return f'\033[38;2;{r};{g};{b}m{s}\033[0m'


def rgb_bg(r: int, g: int, b: int, s: str) -> str:
    return f'\033[48;2;{r};{g};{b}m{s}\033[0m'

def blue(s: str) -> str:
    return rgb(0, 192, 255, s)

def green(s: str) -> str:
    return rgb(0, 255, 0, s)

def bold(s: str) -> str:
    return f'\033[1m{s}\033[0m'

def gray(s: str) -> str:
    return f'\033[90m{s}\033[0m'