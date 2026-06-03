from typing import List
from typing_extensions import Unpack

from ._types import AnsiFormatOptions

class AnsiFormatter:
    ESCAPE_CHARACTER = '\x1B'
    CSI = '['
    SGR_TERMINATOR = 'm'
    COLOR_CODE = { 'FG_BLACK': '30', 'FG_RED': '31', 'FG_GREEN': '32', 'FG_YELLOW': '33', 'FG_BLUE': '34', 'FG_MAGENTA': '35', 'FG_CYAN': '36',
        'FG_WHITE': '37', 'BG_BLACK': '40', 'BG_RED': '41', 'BG_GREEN': '42', 'BG_YELLOW': '43', 'BG_BLUE': '44', 'BG_MAGENTA': '45',
        'BG_CYAN': '46', 'BG_WHITE': '47' }
    STYLES = { 'BOLD': '1', 'DIM': '2', 'ITALIC': '3', 'UNDERLINE': '4', 'BLINK': '5', 'FAST_BLINK': '6', 'REVERSE': '7', 'HIDDEN': '8', 'STRIKETHROUGH': '9' }
    RESET = { 'FG': '39', 'BG': '49', 'ALL': '0' }

    def format_text(self,text: str, **kwargs: Unpack[AnsiFormatOptions]) -> str:
        codes: List[str] = []
        reset_string = None
        code_string = None
        debug = kwargs.get('debug', False)
        reset_type = kwargs.get('reset', 'ALL')
        fg_color = kwargs.get('fg_color')
        bg_color = kwargs.get('bg_color')
        styles = kwargs.get('styles')
        if fg_color and fg_color in self.COLOR_CODE:
            codes.append(self.COLOR_CODE[fg_color])
        if bg_color and bg_color in self.COLOR_CODE:
            codes.append(self.COLOR_CODE[bg_color])
        if styles:
            for s in styles:
                if s in self.STYLES:
                    codes.append(self.STYLES[s])
        consolidated_codes = ';'.join(codes)
        debug_string = f"{self.ESCAPE_CHARACTER}{self.CSI}{self.COLOR_CODE['FG_CYAN']}{self.SGR_TERMINATOR}-=-[DEBUG]-=- {self.ESCAPE_CHARACTER}{self.CSI}{self.RESET['ALL']}{self.SGR_TERMINATOR} " if debug else ''
        code_string = f"{self.ESCAPE_CHARACTER}{self.CSI}{consolidated_codes}{self.SGR_TERMINATOR}" if consolidated_codes else ''
        reset_string = f"{self.ESCAPE_CHARACTER}{self.CSI}{self.RESET[reset_type]}{self.SGR_TERMINATOR}" if reset_type in self.RESET else ''
        return f"{debug_string}{code_string}{text}{reset_string}"

    @staticmethod
    def print(text: str, **kwargs: Unpack[AnsiFormatOptions]) -> None:
        import builtins
        
        builtins.print(AnsiFormatter().format_text(text, **kwargs))