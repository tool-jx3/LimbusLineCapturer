from pathlib import Path
from sys import exit

from .comparison import COMPARISON_LOGGER, FileComparator
from .paratranz import APIClient


class SyncManager:
    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        tokens: list[str],
        exclude_dirs: tuple[str] | None = (
            "PersonalityVoiceDlg",
            "StoryData",
            "BattleAnnouncerDlg",
        ),
    ) -> None:
        exclude = list(exclude_dirs) if exclude_dirs is not None else []
        self.comparator = FileComparator(source_dir, target_dir, exclude)

        self.api = APIClient(tokens)
        self.target_dir = target_dir

    def process_deleted(self, path_entries: list[Path]) -> None:
        for path in path_entries:
            entry = path.as_posix()
            file_id = self.api.find_file_id(entry)
            if file_id:
                self.api.delete_file(file_id)
            else:
                COMPARISON_LOGGER.warning(f"File to be deleted not found: {entry}")

    def process_added(self, entries: list[dict]) -> None:
        for entry in entries:
            file_path = Path(entry["path"]).resolve() / entry["filename"]
            target_path = Path(entry["target_relative_path"]).parent.as_posix()
            target_path = target_path if target_path != "." else ""

            file_id = self.api.upload_new_file(file_path, target_path)
            if file_id:
                self.api.handle_translation(file_id, entry["filename"])

    def process_modified(self, entries: list[dict]) -> None:
        for entry in entries:
            file_id = self.api.find_file_id(entry["target_relative_path"])
            if file_id and self.api.update_file(
                file_id,
                self.target_dir / entry["target_relative_path"],
            ):
                self.api.handle_translation(file_id, entry["filename"], process_stage_zero=True)

    def run(self):
        comparator = self.comparator
        comparator.compare()

        if self.api.fetch_files_list() is None:
            exit(1)

        added_entries = comparator.get_entries(comparator.added)
        modified_entries = comparator.get_entries(comparator.modified)

        self.process_deleted(comparator.deleted)
        self.process_added(added_entries)
        self.process_modified(modified_entries)


def clean_paratranz(tokens: list[str]):
    """Clean ParaTranz."""
    api = APIClient(tokens)
    api.clean_paratranz()
