import os
import pathlib

import pytest
from click.testing import CliRunner
from virtualenvapi.manage import VirtualEnvironment

from venvman import cli


@pytest.fixture()
def data_fixtures():
    """Load a data fixture."""
    return pathlib.Path(__file__).parent / "test_data"


class CLIHelper:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path

    def invoke(
        self,
        args,
        exit_code=0,
        cfg=None,
    ):
        if cfg is None:
            cfg = {}
        runner = CliRunner()
        result = runner.invoke(
            cli.venvman,
            ["--cfg", self.cfg_path] + args,
            catch_exceptions=False,
        )
        if result.exception is not None:
            raise result.exception.with_traceback(result.exc_info[2])
        assert result.exit_code == exit_code
        return result.output.splitlines()


@pytest.fixture
def cli_helper(data_fixtures):
    return CLIHelper(data_fixtures / "cfg.yml")


class TestCreateVenv:
    def test_help_command(self, cli_helper):
        output = cli_helper.invoke(
            ["--help"],
        )
        assert output == [
            "Usage: venvman [OPTIONS] COMMAND [ARGS]...",
            "",
            "  VenvMan. A simple approach to controlling multiple virtualenvs.",
            "",
            "Options:",
            "  --cfg TEXT  Project configuration file. Default: ./cfg.yml.",
            "  --version   Show the version and exit.",
            "  --help      Show this message and exit.",
            "",
            "Commands:",
            "  create  Create and manage datasets.",
        ]

    def test_create_envs(self, cli_helper, tmp_path):
        tmp_path = str(tmp_path)
        output = cli_helper.invoke(
            ["create", "envs", "--d", tmp_path],
        )
        assert output == [
            "Creating env Kyle",
            "Installing package numpy",
            "Installing package pandas",
            "Creating env Sally",
            "Installing package numpy",
            "Installing package requests",
            "Created envs ['Kyle', 'Sally']",
        ]
        assert sorted(os.listdir(tmp_path)) == sorted(["Kyle", "Sally"])
        user_env = VirtualEnvironment(os.path.join(tmp_path, "Kyle"))
        assert user_env.is_installed("pandas")
        user_env = VirtualEnvironment(os.path.join(tmp_path, "Sally"))
        assert user_env.is_installed("requests")


class TestCreateDir:
    def test_create_env_dir_copy_dir(self, cli_helper, tmp_path, data_fixtures):
        output = cli_helper.invoke(
            [
                "create",
                "dirs",
                "--dst",
                str(tmp_path),
                "--src",
                str(data_fixtures / "test_copy_dir"),
            ],
        )
        assert output == [
            "Creating dir for Kyle",
            "Copying test_copy_dir to Kyle",
            "Creating dir for Sally",
            "Copying test_copy_dir to Sally",
        ]
        assert sorted(os.listdir(str(tmp_path))) == sorted(["Kyle", "Sally"])
        assert os.listdir(str(tmp_path / "Kyle")) == ["test_file.txt"]

    def test_create_env_dir_copy_file(self, cli_helper, tmp_path, data_fixtures):
        output = cli_helper.invoke(
            [
                "create",
                "dirs",
                "--dst",
                str(tmp_path),
                "--src",
                str(data_fixtures / "test_copy_dir" / "test_file.txt"),
            ],
        )
        assert output == [
            "Creating dir for Kyle",
            "Copying test_file.txt to Kyle",
            "Creating dir for Sally",
            "Copying test_file.txt to Sally",
        ]
        assert sorted(os.listdir(str(tmp_path))) == sorted(["Kyle", "Sally"])
        assert os.listdir(str(tmp_path / "Kyle")) == ["test_file.txt"]
