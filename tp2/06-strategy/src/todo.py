from dataclasses import dataclass


@dataclass
class Todo:
    id: int = 0
    title: str = ""
    completed: bool = False
    priorite: int = 0  # 0 = normale, 1 = haute, 2 = urgente
