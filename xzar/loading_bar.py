from typing import ContextManager

from contextlib import nullcontext
from casanova import Enricher, RowCountResumer
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
    def __init__(
        self,
        title: str,
        total: int | None = None,
        transient: bool = False,
        already_completed: int | None = None,
    ):
        if total is not None:
            columns = [
                TextColumn("[progress.description]{task.description}"),
                SpinnerColumn(),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
            ]
        else:
            columns = [
                TextColumn("[progress.description]{task.description}"),
                SpinnerColumn(),
                MofNCompleteColumn(),
            ]

        self.progress = Progress(
            *columns,
            console=console,
            transient=transient,
        )
        self.task = self.progress.add_task(title, total=total)

        if already_completed is not None:
            self.advance(already_completed)

    @classmethod
    def from_enricher(
        cls, enricher: Enricher, title: str, total: int | None = None
    ) -> "LoadingBar":
        actual_total = enricher.total

        if actual_total is None:
            actual_total = total

        already_completed = None

        if enricher.resumer is not None:
            already_completed = enricher.resumer.already_done_count()

        return cls(title, total=actual_total, already_completed=already_completed)

    @classmethod
    def resuming(cls, output) -> ContextManager:
        if not isinstance(output, RowCountResumer):
            return nullcontext()

        resume_loading_bar = LoadingBar(
            title="Resuming",
            transient=False,
        )

        def listener(event, _):
            if event == "output.row.read":
                resume_loading_bar.advance()

        output.set_listener(listener)

        return resume_loading_bar

    def advance(self, count: int = 1):
        self.progress.update(self.task, advance=count)

    def __enter__(self) -> "LoadingBar":
        self.progress.__enter__()
        return self

    def __exit__(self, *args):
        self.progress.__exit__(*args)

    def print(self, msg):
        console.print(msg)
