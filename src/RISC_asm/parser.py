from __future__ import annotations

from pathlib import Path

from .instruction import Instruction
from .isa import ISA
from .operands import Immediate, Label, Register


class ParseError(ValueError):
    pass


def _split_comment(line: str) -> str:
    for marker in ("#", ";"):
        if marker in line:
            line = line.split(marker, 1)[0]
    return line.strip()


def _extract_labels(line: str) -> tuple[list[str], str]:
    labels: list[str] = []
    remainder = line.strip()

    while ":" in remainder:
        candidate, rest = remainder.split(":", 1)
        label = candidate.strip()
        if not label or any(ch.isspace() for ch in label):
            break
        labels.append(label)
        remainder = rest.strip()

    return labels, remainder


def _parse_operand_names(syntax: str) -> list[str]:
    _, _, operand_text = syntax.partition(" ")
    if not operand_text:
        return []
    return _flatten_operand_parts(operand_text)


def _split_operands(operand_text: str) -> list[str]:
    if not operand_text.strip():
        return []
    return _flatten_operand_parts(operand_text)


def _flatten_operand_parts(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    bracket_depth = 0

    for char in text:
        if char == "[":
            bracket_depth += 1
            current.append(char)
            continue
        if char == "]":
            bracket_depth -= 1
            current.append(char)
            continue
        if char == "," and bracket_depth == 0:
            token = "".join(current).strip()
            if token:
                parts.extend(_expand_operand_token(token))
            current = []
            continue
        current.append(char)

    token = "".join(current).strip()
    if token:
        parts.extend(_expand_operand_token(token))

    return parts


def _expand_operand_token(token: str) -> list[str]:
    if token.startswith("[") and token.endswith("]"):
        inner = token[1:-1].strip()
        return _flatten_operand_parts(inner)
    return [token]


def _parse_mnemonic(token: str, isa: ISA, lineno: int):
    for mnemonic, spec in isa.spec["instructions"].items():
        mnemonic_pattern = spec["syntax"].split(" ", 1)[0]
        base = mnemonic_pattern.split("{", 1)[0]
        if not token.startswith(base):
            continue

        suffix = token[len(base):]
        set_flags = 0
        if "{s}" in mnemonic_pattern and suffix.startswith("S"):
            set_flags = 1
            suffix = suffix[1:]

        cond = isa.default_condition() if "{cond}" in mnemonic_pattern else 0
        if "{cond}" in mnemonic_pattern and suffix:
            if suffix not in isa.conditions:
                continue
            cond = isa.conditions[suffix]
            suffix = ""

        if suffix:
            continue

        return mnemonic, spec, cond, set_flags

    raise ParseError(f"Line {lineno}: unknown instruction '{token}'")


def _build_register(token: str, isa: ISA, lineno: int) -> Register:
    register_names = isa.register_names
    if token not in register_names:
        raise ParseError(
            f"Line {lineno}: unknown register '{token}', expected one of {register_names}"
        )
    return Register(token, register_names.index(token))


def _build_immediate(token: str, lineno: int) -> Immediate:
    try:
        return Immediate(token)
    except ValueError as exc:
        raise ParseError(f"Line {lineno}: invalid immediate '{token}'") from exc


def _build_operand(token: str, operand_name: str, isa: ISA, lineno: int):
    register_fields = set(isa.register_fields)
    label_fields = {"offset"}

    if operand_name in register_fields:
        return _build_register(token, isa, lineno)
    if operand_name in label_fields:
        try:
            return _build_immediate(token, lineno)
        except ParseError:
            return Label(token)
    return _build_immediate(token, lineno)


def parse_line(line: str, lineno: int, isa: ISA) -> Instruction | None:
    stripped = _split_comment(line)
    if not stripped:
        return None

    labels, remainder = _extract_labels(stripped)
    if not remainder:
        return None

    mnemonic, _, operand_text = remainder.partition(" ")
    mnemonic = mnemonic.upper()

    mnemonic, spec, cond, set_flags = _parse_mnemonic(mnemonic, isa, lineno)

    expected_operand_names = _parse_operand_names(spec["syntax"])
    operand_tokens = _split_operands(operand_text)

    if len(operand_tokens) != len(expected_operand_names):
        raise ParseError(
            f"Line {lineno}: '{mnemonic}' expects {len(expected_operand_names)} "
            f"operand(s), got {len(operand_tokens)}"
        )

    operands = [
        _build_operand(token, operand_name, isa, lineno)
        for token, operand_name in zip(operand_tokens, expected_operand_names)
    ]

    return Instruction(
        mnemonic=mnemonic,
        operands=operands,
        lineno=lineno,
        operand_names=expected_operand_names,
        labels=labels,
        source=line.rstrip("\n"),
        syntax=spec["syntax"],
        fmt=spec["format"],
        opcode=spec["opcode"],
        cond=cond,
        set_flags=set_flags,
    )


def parse_text(source: str, isa: ISA) -> list[Instruction]:
    instructions: list[Instruction] = []
    pending_labels: list[str] = []

    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = _split_comment(line)
        if not stripped:
            continue

        labels, remainder = _extract_labels(stripped)
        if not remainder:
            pending_labels.extend(labels)
            continue

        instruction = parse_line(line, lineno, isa)
        if instruction is not None:
            instruction.labels = [*pending_labels, *instruction.labels]
            instructions.append(instruction)
            pending_labels = []

    if pending_labels:
        raise ParseError(
            f"Dangling label(s) without an instruction: {', '.join(pending_labels)}"
        )

    return instructions


def parse_file(path: str | Path, isa_path: str | Path | None = None) -> list[Instruction]:
    source_path = Path(path)
    resolved_isa_path = (
        Path(isa_path)
        if isa_path is not None
        else Path(__file__).resolve().parent.parent / "isa.yaml"
    )
    isa = ISA(resolved_isa_path)
    return parse_text(source_path.read_text(encoding="utf-8"), isa)
