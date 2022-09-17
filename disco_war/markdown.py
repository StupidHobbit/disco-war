from __future__ import annotations


class MarkdownBuilder:
    def __init__(self, new_line_size=2):
        self.new_line = '\n' * new_line_size
        self.parts: list[str] = []

    def text(self, t: str) -> MarkdownBuilder:
        self.parts.append(t)
        return self

    def table(self):
        pass


class MarkdownTableBuilder:
    def __init__(self, builder: MarkdownBuilder):
        self.builder = builder

