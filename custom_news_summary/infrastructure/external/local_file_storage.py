from pathlib import Path

from custom_news_summary.application.port.storage_port import FileStoragePort


class LocalFileStorage(FileStoragePort):
    """File Storage 구현체"""

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def save_file(self, file_content: bytes, file_name: str) -> str:
        file_path = self.base_path / file_name
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return str(file_path)