from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    """File Storage Port - 인터페이스"""

    @abstractmethod
    def save_file(self, file_content: bytes, file_name: str) -> str:
        """Returns file_path"""
        pass