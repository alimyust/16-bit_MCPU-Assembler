from .operands import Register, Immediate, Label
from .instruction import Instruction

def parse_operand(tok):
    if tok.startswith("r"):
        return Register(tok)
    if tok.lstrip("-").isdigit():
        return Immediate(tok)
    return Label(tok)

def parse_line(line, lineno):
    line = line.split("#")[0].strip()
    if not line:
        return None

    parts = [p.strip() for p in line.replace(",", " ").split()]
    mnemonic = parts[0].upper()
    operands = [parse_operand(p) for p in parts[1:]]
    return Instruction(mnemonic, operands, lineno)
