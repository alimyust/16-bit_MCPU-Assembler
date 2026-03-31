from __future__ import annotations

import argparse
from pathlib import Path

from .instruction import Instruction
from .isa import ISA
from .operands import Immediate, Label, Register
from .parser import parse_file, parse_text


class AssemblyError(ValueError):
    pass


def _operand_map(instruction: Instruction) -> dict[str, object]:
    return {
        operand_name: operand
        for operand_name, operand in zip(instruction.operand_names, instruction.operands)
    }


def _encode_value(value: int, width: int, field_name: str, lineno: int) -> int:
    max_unsigned = (1 << width) - 1
    min_signed = -(1 << (width - 1))

    if value < 0:
        if value < min_signed:
            raise AssemblyError(
                f"Line {lineno}: {field_name} value {value} does not fit in {width} bits"
            )
        return value & max_unsigned

    if value > max_unsigned:
        raise AssemblyError(
            f"Line {lineno}: {field_name} value {value} does not fit in {width} bits"
        )
    return value


def _resolve_field_value(
    field_name: str,
    instruction: Instruction,
    labels: dict[str, int],
    address: int,
) -> int:
    operands = _operand_map(instruction)

    if field_name == "opcode":
        return int(instruction.opcode or 0)
    if field_name == "cond":
        return instruction.cond
    if field_name == "s":
        return instruction.set_flags
    if field_name not in operands:
        return 0

    operand = operands[field_name]
    if isinstance(operand, Register):
        return operand.index
    if isinstance(operand, Immediate):
        return operand.value
    if isinstance(operand, Label):
        if operand.name not in labels:
            raise AssemblyError(
                f"Line {instruction.lineno}: unknown label '{operand.name}'"
            )
        operand.address = labels[operand.name]
        return labels[operand.name] - (address + 1)

    raise AssemblyError(f"Line {instruction.lineno}: unsupported operand for {field_name}")


def encode_instruction(
    instruction: Instruction,
    isa: ISA,
    labels: dict[str, int],
    address: int,
) -> int:
    encoded = 0
    for field_name, width in isa.format_fields(instruction.fmt).items():
        field_value = _resolve_field_value(field_name, instruction, labels, address)
        encoded = (encoded << width) | _encode_value(
            field_value, width, field_name, instruction.lineno
        )
    return encoded


def resolve_labels(instructions: list[Instruction]) -> dict[str, int]:
    labels: dict[str, int] = {}
    for address, instruction in enumerate(instructions):
        for label in instruction.labels:
            if label in labels:
                raise AssemblyError(
                    f"Line {instruction.lineno}: duplicate label '{label}'"
                )
            labels[label] = address
    return labels


def assemble_instructions(
    instructions: list[Instruction],
    isa: ISA,
) -> list[int]:
    labels = resolve_labels(instructions)
    return [
        encode_instruction(instruction, isa, labels, address)
        for address, instruction in enumerate(instructions)
    ]


def assemble_text(source: str, isa: ISA) -> tuple[list[Instruction], list[int]]:
    instructions = parse_text(source, isa)
    return instructions, assemble_instructions(instructions, isa)


def assemble_file(
    source_path: str | Path,
    isa_path: str | Path | None = None,
) -> tuple[list[Instruction], list[int]]:
    source_path = Path(source_path)
    resolved_isa_path = (
        Path(isa_path)
        if isa_path is not None
        else Path(__file__).resolve().parent.parent / "isa.yaml"
    )
    isa = ISA(resolved_isa_path)
    instructions = parse_file(source_path, resolved_isa_path)
    return instructions, assemble_instructions(instructions, isa)


def _format_word(word: int, width: int) -> tuple[str, str]:
    hex_digits = (width + 3) // 4
    return f"0x{word:0{hex_digits}X}", f"0b{word:0{width}b}"


def main(argv: list[str] | None = None) -> int:
    arg_parser = argparse.ArgumentParser(
        description="Assemble a .as file into 16-bit machine code."
    )
    arg_parser.add_argument("source", help="Path to the assembly source file")
    arg_parser.add_argument(
        "--isa",
        dest="isa_path",
        help="Optional path to the ISA yaml file",
    )
    args = arg_parser.parse_args(argv)

    isa = ISA(args.isa_path or Path(__file__).resolve().parent.parent / "isa.yaml")
    instructions, machine_code = assemble_file(args.source, args.isa_path)

    for address, (instruction, word) in enumerate(zip(instructions, machine_code)):
        width = max(isa.word_size, sum(isa.format_fields(instruction.fmt).values()))
        hex_word, binary_word = _format_word(word, width)
        print(f"{address:04}: {hex_word}  {binary_word}  {instruction.source}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
