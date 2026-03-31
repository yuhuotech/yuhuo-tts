from dataclasses import dataclass
from typing import Optional


@dataclass
class Tokenizer:
    encoding: object
    num_languages: int = 99
    language: Optional[str] = None
    task: Optional[str] = None

    def encode(self, text: str, allowed_special: str | set[str] = "all") -> list[int]:
        return self.encoding.encode(text, allowed_special=allowed_special)

    def decode(self, tokens: list[int]) -> str:
        return self.encoding.decode(tokens)
