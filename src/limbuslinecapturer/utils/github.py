import io
import shutil
import zipfile
from pathlib import Path

import requests


def github_downloader(repo_owner: str, repo_name: str, target_dir: Path):
    """Download the source code for the main branch of the specified GitHub repo."""
    zip_url = f"https://github.com/{repo_owner}/{repo_name}/archive/main.zip"
    response = requests.get(zip_url)
    response.raise_for_status()

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    temp_dir = Path("temp_diff")
    temp_dir.mkdir(exist_ok=True)
    zip_file.extractall(temp_dir)

    # Copy the CN directory to the target folder
    source_dir = temp_dir / f"{repo_name}-main" / "CN"
    target_path = Path(target_dir)
    if target_path.exists():
        shutil.rmtree(target_path)
    shutil.copytree(source_dir, target_path)

    shutil.rmtree(temp_dir)
