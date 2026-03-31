from dataclasses import dataclass, field

from .operands import Operand


@dataclass(slots=True)
class Instruction:
    mnemonic: str
    operands: list[Operand]
    lineno: int
    operand_names: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    source: str = ""
    syntax: str = ""
    fmt: str = ""
    opcode: int | None = None
    cond: int = 0
    set_flags: int = 0
