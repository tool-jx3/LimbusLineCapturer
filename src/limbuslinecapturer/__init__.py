from pathlib import Path

from .syncer import SyncManager, clean_paratranz
from .utils import github_downloader as gh_dl

with open("TOKEN") as file:
    __TOKENS = [line.strip() for line in file]


def main() -> None:
    """Starter entry."""
    data_folder = Path().cwd().resolve() / "data"
    data_folder.mkdir(parents=True, exist_ok=True)
    source = data_folder / "source"
    target = data_folder / "CN"

    gh_dl("LibraryCorp", "LimbusLineCapturer", source)
    gh_dl("LocalizeLimbusCompany", "LLC_Release", target)

    # Delete
    target = data_folder / "source"
    source = data_folder / "CN"

    manager = SyncManager(source, target, __TOKENS)
    manager.run()


def init() -> None:
    """Creator entry."""
    data_folder = Path().cwd().resolve() / "data"
    source = data_folder / "TW"
    source.mkdir(parents=True, exist_ok=True)
    target = data_folder / "CN"

    gh_dl("LibraryCorp", "LimbusLineCapturer", target)

    manager = SyncManager(source, target, __TOKENS, exclude_dirs=None)
    manager.run()


def clear() -> None:
    """Clean ParaTranz."""
    clean_paratranz(__TOKENS)
