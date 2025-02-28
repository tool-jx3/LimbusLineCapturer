from hashlib import md5
from pathlib import Path

from limbuslinecapturer.utils import COMPARISON_LOGGER


class FileComparator:
    def __init__(self, source: Path, target: Path, exclude_dirs: list[str]) -> None:
        self.source_dir = source
        self.target_dir = target
        self.exclude_dirs = exclude_dirs

        # {relative_dir: hash}
        self.source_files = {}
        self.target_files = {}

        # Status List
        self.deleted: list[Path] = []
        self.added: list[Path] = []
        self.modified: list[Path] = []

    @staticmethod
    def compute_hash(file_path: Path) -> str:
        hasher = md5()
        try:
            with file_path.open("rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            COMPARISON_LOGGER.error(f"Hash calculation failed {file_path}: {e!s}")
        return ""

    def collect_files(self, directory: Path) -> dict[str, str]:
        files = {}
        for file in directory.rglob("*.json"):
            if not file.is_file():
                continue
            relative_path = file.relative_to(directory)
            files[str(relative_path.as_posix())] = self.compute_hash(file)
        return files

    def compare(self):
        self.source_files = self.collect_files(self.source_dir)
        self.target_files = self.collect_files(self.target_dir)

        source_keys = set(self.source_files.keys())
        target_keys = set(self.target_files.keys())

        # Deleted (Exist on source but not exist on target)
        self.deleted = [Path(p) for p in (source_keys - target_keys)]

        # Added (Exist on target but not exist on source)
        self.added = [Path(p) for p in (target_keys - source_keys)]

        # Modified (Coexistence but hash difference)
        common = source_keys & target_keys
        for relative_path in common:
            if self.source_files[relative_path] == self.target_files[relative_path]:
                continue

            path_obj = Path(relative_path)
            if path_obj.parts[0] not in self.exclude_dirs:
                self.modified.append(path_obj)

        COMPARISON_LOGGER.info(
            f"Comparison results: delete {len(self.deleted)}\tadd {len(self.added)}\tmodify {len(self.modified)}",
        )

    def get_entries(self, path_list: list[Path]) -> list[dict]:
        entries = []
        for path in path_list:
            target_full_path = self.target_dir / path
            if not target_full_path.exists():
                continue
            entries.append(
                {
                    "target_relative_path": path.as_posix(),
                    "path": (self.target_dir / path.parent).as_posix(),
                    "filename": path.name,
                },
            )
        return entries
