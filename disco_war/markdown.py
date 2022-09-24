from __future__ import annotations


class MarkdownBuilder:
    def __init__(self, new_line_size=2):
        self._new_line_str = '\n' * new_line_size
        self._parts: list[str] = []

    def text(self, t: str) -> MarkdownBuilder:
        self._parts.append(t)
        return self

    def new_line(self) -> MarkdownBuilder:
        self._parts.append(self._new_line_str)
        return self

    def table(self) -> MarkdownTableBuilder:
        return MarkdownTableBuilder(self)

    def build(self) -> str:
        return ''.join(self._parts)


class MarkdownTableBuilder:
    def __init__(self, builder: MarkdownBuilder):
        self.builder = builder
        self.header: tuple[str, ...] | None = None

    def with_header(self, header: tuple[str, ...]) -> MarkdownTableBuilderWithHeader:
        return MarkdownTableBuilderWithHeader(self.builder, header)


class MarkdownTableBuilderWithHeader:
    def __init__(self, builder: MarkdownBuilder, header: tuple[str, ...]):
        self._builder = builder
        self._header = header

    def with_rows(self, rows: list[tuple[str, ...]]) -> MarkdownBuilder:
        rows_lengths = [max(map(len, column)) for column in zip(*rows, self._header)]
        rows_formats = [f'%{row_length}s' for row_length in rows_lengths]
        header_str = f"|{'|'.join(row_format % cell for cell, row_format in zip(self._header, rows_formats))}|"
        delimiter_str = f"|{'|'.join('-' * row_length for row_length in rows_lengths)}|"
        rows_str = '\n'.join(
            f"|{'|'.join(row_format % cell for cell, row_format in zip(row, rows_formats))}|"
            for row in rows
        )
        self._builder.text(f'{header_str}\n{delimiter_str}\n{rows_str}')
        return self._builder
