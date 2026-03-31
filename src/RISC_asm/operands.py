from dataclasses import dataclass


@dataclass(slots=True)
class Operand:
    text: str
    kind: str


@dataclass(slots=True)
class Register(Operand):
    name: str
    index: int

    def __init__(self, name: str, index: int):
        self.text = name
        self.kind = "register"
        self.name = name
        self.index = index


@dataclass(slots=True)
class Immediate(Operand):
    value: int

    def __init__(self, value_text: str):
        self.text = value_text
        self.kind = "immediate"
        self.value = int(value_text, 0)


@dataclass(slots=True)
class Label(Operand):
    name: str
    address: int | None = None

    def __init__(self, name: str, address: int | None = None):
        self.text = name
        self.kind = "label"
        self.name = name
        self.address = address
