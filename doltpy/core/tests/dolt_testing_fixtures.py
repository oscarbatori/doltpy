import os
from doltpy.core.dolt import Dolt
import pytest
import shutil
from typing import Tuple
import uuid


def get_repo_path_tmp_path(path: str) -> Tuple[str, str]:
    return path, os.path.join(path, '.dolt')


@pytest.fixture
def init_repo(tmpdir) -> Dolt:
    created_repo_paths = []

    def _init_repo():
        repo_path = tmpdir.mkdir(str(uuid.uuid1()))
        repo_data_dir = os.path.join(repo_path, '.dolt')
        assert not os.path.exists(repo_data_dir)
        repo = Dolt(repo_path)
        repo.init_new_repo()
        created_repo_paths.append(repo_data_dir)
        return repo

    yield _init_repo

    for created_repo_path in created_repo_paths:
        if os.path.exists(created_repo_path):
            shutil.rmtree(created_repo_path)