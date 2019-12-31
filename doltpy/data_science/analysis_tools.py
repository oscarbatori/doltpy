from doltpy.core import Dolt
from doltpy.etl import DoltTableWriter
import pandas as pd
from typing import List
import uuid
import logging


logger = logging.getLogger(__name__)


class DoltToDoltContext:
    # """
    # A context manager for defining transformations from one Dolt repo to another, usage looks like
    # >>> from doltpy.core import Dolt
    # >>> input, output = Dolt(...), Dolt(...)
    # >>> with DoltToDolt(inpput, outpout, writers, 'update data'):
    # >>>
    # """

    def __init__(self,
                 input_repo: Dolt,
                 output_repo: Dolt,
                 commit_message: str,
                 input_branch: str = None,
                 input_commit_ref: str = None,
                 output_branch: str = None):
        self.input_repo = input_repo
        self.output_repo = output_repo
        self.commit_message = commit_message
        self.input_branch = input_branch
        self.input_commit_ref = input_commit_ref
        self.output_branch = output_branch
        self.input_branch_on_entry = self.input_repo.get_current_branch()
        self.output_branch_on_entry = self.output_repo.get_current_branch()

    @classmethod
    def _report_repo_state(cls, repo_type: str, repo):
        logger.info('{} repo at {}, on branch {}, commit {}'.format(repo_type,
                                                                    repo.repo_dir,
                                                                    repo.get_current_branch(),
                                                                    list(repo.get_commits())[0].hash))

    def __enter__(self):
        if self.input_commit_ref:
            branch = str(uuid.uuid1())
            logger.info('Input using ref {}, creating temp branch {}'.format(self.input_commit_ref, branch))
            self.input_repo.create_branch(branch, commit_ref=self.input_commit_ref)
            self.input_repo.checkout(branch)
        else:
            branch = self.input_branch or self.input_repo.get_current_branch()
            if branch != self.input_repo.get_current_branch():
                self.input_repo.checkout(branch)

        if self.output_branch and self.output_branch != self.output_repo.get_current_branch():
            logger.info('Checking out output branch {}'.format(self.output_branch_on_entry))
            if self.output_branch not in self.output_repo.get_branch_list():
                logger.info('{} does not exist on output repo, creating'.format(self.output_branch))
                self.output_repo.create_branch(self.output_branch)
            self.output_repo.checkout(self.output_branch)

        self._report_repo_state('input', self.input_repo)

    def __exit__(self, exception_type, exception_value, traceback):
        logger.info('Generating output data')
        self._report_repo_state('output', self.output_repo)
        self.output_repo.commit(commit_message=self.commit_message)

        if self.output_branch_on_entry != self.output_repo.get_current_branch():
            logger.info('Moving output repo back to branch {}'.format(self.output_branch_on_entry))
            self.output_repo.checkout(self.output_branch_on_entry)
        if self.input_branch_on_entry != self.input_repo.get_current_branch():
            logger.info('Moving input repo back to branch {}'.format(self.input_branch_on_entry))
            self.input_repo.checkout(self.input_branch_on_entry)
