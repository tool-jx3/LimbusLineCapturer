from collections import deque
from json import dumps
from pathlib import Path
from sys import exit

import requests
from opencc import OpenCC

from limbuslinecapturer.utils import API_LOGGER


class APIClient:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens: deque[str] = deque(tokens)
        self.session = requests.Session()
        self.BASE_URL = "https://paratranz.cn/api/projects/13260"
        self.files_cache = []

        # Translation
        self.converter = OpenCC("s2tw")

    def rotate_token(self) -> dict:
        token = self.tokens[0]
        self.tokens.rotate(1)
        return {"Authorization": token}

    def fetch_files_list(self) -> dict | None:
        url = f"{self.BASE_URL}/files"
        try:
            response = self.session.get(url, headers=self.rotate_token())
            if response.status_code == 200:
                self.files_cache = response.json()
                return self.files_cache
            API_LOGGER.error(f"Failed to get list: {response.status_code}")
        except Exception as e:
            API_LOGGER.error(f"Get list exception: {e!s}")
        return None

    def find_file_id(self, file_path: str) -> int | None:
        for f in self.files_cache:
            if str(f["name"]).endswith(file_path):
                return f["id"]
        return None

    def delete_file(self, file_id: int) -> bool:
        url = f"{self.BASE_URL}/files/{file_id}"
        try:
            response = self.session.delete(url, headers=self.rotate_token())
            if response.status_code == 200:
                API_LOGGER.info(f"Delete successful: {file_id}")
                return True
            API_LOGGER.error(f"Delete {file_id} failed: {response.status_code}")
        except Exception as e:
            API_LOGGER.error(f"Delete exception on file {file_id}: {e!s}")
        return False

    def upload_new_file(self, file_path: Path, target_path: str) -> int | None:
        url = f"{self.BASE_URL}/files"
        try:
            with file_path.open("rb") as f:
                response = self.session.post(
                    url,
                    headers=self.rotate_token(),
                    files={"file": (file_path.name, f)},
                    data={"path": target_path},
                )
            if response.status_code == 200:
                data = response.json()
                data_id = data["file"]["id"]
                API_LOGGER.info(f"Upload successful: {data_id}")
                return data_id
            API_LOGGER.error(f"Upload {file_path.name} failed: {response.status_code}")
        except Exception as e:
            API_LOGGER.error(f"Upload exception on file {file_path.name}: {e!s}")
        return None

    def update_file(self, file_id: int, file_path: Path) -> bool:
        url = f"{self.BASE_URL}/files/{file_id}"
        try:
            with file_path.open("rb") as f:
                response = self.session.post(
                    url,
                    headers=self.rotate_token(),
                    files={"file": (file_path.name, f)},
                )
            if response.status_code == 200:
                API_LOGGER.info(f"Update successful: {file_id}")
                return True
            API_LOGGER.error(f"Update {file_id} failed: {response.status_code}")
        except Exception as e:
            API_LOGGER.error(f"Update exception on file {file_id}: {e!s}")
        return False

    def handle_translation(
        self,
        file_id: int,
        file_name: str,
        process_stage_zero: bool = False,
    ) -> bool:
        url = f"{self.BASE_URL}/files/{file_id}/translation"

        try:
            response = self.session.get(url, headers=self.rotate_token())
            if response.status_code != 200:
                return False
            data = response.json()
        except Exception as e:
            API_LOGGER.error(f"Failed to get translation {file_id}: {e!s}")
            return False

        modified = False
        for item in data:
            if process_stage_zero and item.get("stage", 0) != 0:
                continue
            if not item["translation"] and item["original"]:
                item["translation"] = self.converter.convert(item["original"])
                item["stage"] = 1
                modified = True

        if modified:
            try:
                response = self.session.post(
                    url,
                    headers=self.rotate_token(),
                    files={"file": (file_name, dumps(data))},
                )
                return response.status_code == 200
            except Exception as e:
                API_LOGGER.error(f"Submission of translation {file_id} failed: {e!s}")
        return False

    def clean_paratranz(self) -> None:
        if self.fetch_files_list() is None:
            exit(1)

        file_ids = [file["id"] for file in self.files_cache if "id" in file]
        API_LOGGER.info(f"A total of {len(file_ids)} files found that need to be processed")

        for idx, file_id in enumerate(file_ids, 1):
            url = f"{self.BASE_URL}/files/{file_id}"

            try:
                response = requests.delete(url, headers=self.rotate_token())

                if response.status_code == 200:
                    API_LOGGER.info(f"({idx}/{len(file_ids)}) Successfully deleted file {file_id}")
                else:
                    API_LOGGER.error(
                        f"({idx}/{len(file_ids)}) Deletion of file {file_id} failed, status code: {response.status_code}",
                    )
            except requests.exceptions.RequestException as e:
                API_LOGGER.error(
                    f"({idx}/{len(file_ids)}) Exception deleting file {file_id}: {e!s}",
                )
                continue
