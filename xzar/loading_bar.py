from casanova import Reader
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    SpinnerColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)

from .console import console


# ref: https://rich.readthedocs.io/en/stable/progress.html
class LoadingBar:
    def __init__(self, title: str, total: int | None = None, transient: bool = False):
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn(),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=transient,
        )
        self.task = self.progress.add_task(title, total=total)

    @classmethod
    def from_reader(
        cls, reader: Reader, title: str, total: int | None = None
    ) -> "LoadingBar":
        actual_total = reader.total

        if actual_total is None:
            actual_total = total

        return cls(title, total=actual_total)

    def advance(self, count: int = 1):
        self.progress.update(self.task, advance=count)

    def __enter__(self) -> "LoadingBar":
        self.progress.__enter__()
        return self

    def __exit__(self, *args):
        self.progress.__exit__(*args)

    def print(self, msg):
        console.print(msg)
