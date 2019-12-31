from doltpy.data_science.analysis_tools import DoltToDoltContext, Dolt
from doltpy.core.tests.dolt_testing_fixtures import init_repo
import pytest
import pandas as pd
import uuid

BASE_TEST_DATA = pd.DataFrame([{'name': 'Andy', 'major_count': 3}])
FIRST_ADDITIONAL_TEST_DATA = pd.DataFrame([{'name': 'Roger', 'major_count': 20}])
SECOND_ADDITIONAL_TEST_DATA = pd.DataFrame([{'name': 'Rafael', 'major_count': 19}])
MEAN_BASE = 3
MEAN_FIRST_ADDITIONAL_TEST_DATA = (20 + 3) / 2


def _import_data_helper(repo: Dolt, data: pd.DataFrame, target_branch: str = 'master'):
    current_branch = repo.get_current_branch()

    if current_branch != target_branch:
        if target_branch not in repo.get_branch_list():
            repo.create_branch(target_branch)
        repo.checkout(target_branch)

    repo.import_df('input', data, ['name'])
    repo.add_table_to_next_commit('input')
    repo.commit(str(uuid.uuid1()))

    if target_branch != current_branch:
        repo.checkout(current_branch)


@pytest.fixture
def create_input_and_output_repos(init_repo):
    input_repo, output_repo = init_repo(), init_repo()
    _import_data_helper(input_repo, BASE_TEST_DATA)
    return input_repo, output_repo


def add_new_data_to_branch(repo: Dolt, new_data: pd.DataFrame, branch: str = 'master'):
    _import_data_helper(repo, new_data, branch)


def _compute_average_major_count(major_counts: pd.DataFrame):
    return pd.DataFrame(dict(average_value=[major_counts['major_count'].mean()])).assign(average_type='majors')


def dolt_to_dolt_transform(input_repo: Dolt,
                           output_repo: Dolt,
                           message: str,
                           input_branch: str = None,
                           output_branch: str = None,
                           input_commit_ref: str = None):
    with DoltToDoltContext(input_repo,
                           output_repo,
                           message,
                           input_branch=input_branch,
                           output_branch=output_branch,
                           input_commit_ref=input_commit_ref):
        data = _compute_average_major_count(input_repo.read_table('input'))
        signed = data.assign(input_commit_ref=list(input_repo.get_commits())[0].hash)
        output_repo.import_df('averages', signed, ['input_commit_ref', 'average_type'])
        output_repo.add_table_to_next_commit('averages')


def test_dolt_to_dolt_context(create_input_and_output_repos):
    input_repo, output_repo = create_input_and_output_repos
    dolt_to_dolt_transform(input_repo, output_repo, 'created some new data')
    result = output_repo.read_table('averages')
    assert result['average_value'].iloc[0] == MEAN_BASE


def test_dolt_to_dolt_context_input_branch(create_input_and_output_repos):
    input_repo, output_repo = create_input_and_output_repos
    add_new_data_to_branch(input_repo, FIRST_ADDITIONAL_TEST_DATA, 'additional_input_branch')
    master_branch_inputs = input_repo.read_table('input')
    assert len(master_branch_inputs) == 1

    dolt_to_dolt_transform(input_repo, output_repo, 'created some new data', input_branch='additional_input_branch')
    result = output_repo.read_table('averages')
    assert result['average_value'].iloc[0] == MEAN_FIRST_ADDITIONAL_TEST_DATA


def test_dolt_to_dolt_context_input_commit_ref(create_input_and_output_repos):
    input_repo, output_repo = create_input_and_output_repos
    add_new_data_to_branch(input_repo, FIRST_ADDITIONAL_TEST_DATA)
    add_new_data_to_branch(input_repo, SECOND_ADDITIONAL_TEST_DATA)
    input_commit = list(input_repo.get_commits())[1].hash

    dolt_to_dolt_transform(input_repo, output_repo, 'created some new data', input_commit_ref=input_commit)
    result = output_repo.read_table('averages')
    assert result['average_value'].iloc[0] == MEAN_FIRST_ADDITIONAL_TEST_DATA


def test_dolt_to_dolt_context_output_branch(create_input_and_output_repos):
    input_repo, output_repo = create_input_and_output_repos
    add_new_data_to_branch(input_repo, FIRST_ADDITIONAL_TEST_DATA, 'additional_input_branch')
    master_branch_inputs = input_repo.read_table('input')
    assert len(master_branch_inputs) == 1

    dolt_to_dolt_transform(input_repo, output_repo, 'created some new data')
    dolt_to_dolt_transform(input_repo,
                           output_repo,
                           'created some new data',
                           input_branch='additional_input_branch',
                           output_branch='output_branch')

    first_input_hash = list(input_repo.get_commits())[0].hash
    first_result = output_repo.read_table('averages')
    assert first_result.loc[first_result['input_commit_ref'] == first_input_hash, 'average_value'].iloc[0] == MEAN_BASE
    output_repo.checkout('output_branch')
    input_repo.checkout('additional_input_branch')
    second_input_hash = list(input_repo.get_commits())[0].hash
    second_result = output_repo.read_table('averages')
    assert second_result.loc[second_result['input_commit_ref'] == second_input_hash,'average_value'].iloc[0] == MEAN_FIRST_ADDITIONAL_TEST_DATA