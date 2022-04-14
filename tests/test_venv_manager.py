import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from virtualenvapi.manage import VirtualEnvironment

from venvman import cli


@pytest.fixture()
def data_fixtures():
    """Load a data fixture."""
    return Path(__file__).parent / "test_data"


class CLIHelper:
    def __init__(self, tmp_path, base_cfg):
        self._tmp_path = tmp_path
        self._base_cfg = base_cfg
        self.ctx = cli.VenvManager(self.cfg())

    def _apply_base_cfg(self, **kw):
        d = {}
        d.update(self._base_cfg)
        d.update(kw)
        return d

    def cfg(self, config_name="cfg.yml", **kw):
        cfg_file = self._tmp_path / config_name
        cfg_file.write_text(json.dumps(self._apply_base_cfg(**kw)))
        return str(cfg_file)

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
            ["--cfg", self.cfg(**cfg)] + args,
            catch_exceptions=False,
        )
        if result.exception is not None:
            raise result.exception.with_traceback(result.exc_info[2])
        assert result.exit_code == exit_code
        return result.output.splitlines()


@pytest.fixture
def cli_helper(tmp_path):
    base_cfg = {
        "environments_directory": str(tmp_path / "envs"),
        "projects_directory": str(tmp_path / "projs"),
        "default_packages": ["numpy"],
        "environments": {"Kyle": ["pandas"], "Sally": ["requests"]},
    }
    return CLIHelper(tmp_path, base_cfg)


class TestVenvManager:
    def test_create_venvman(self, data_fixtures):
        config = cli.VenvManager(data_fixtures / "cfg.yml")
        assert config.default_packages == ["numpy"]
        assert config.environments == {"Kyle": ["pandas"], "Sally": ["requests"]}
        assert config.envs_dir == Path("tests/test_data/envs")
        assert config.projs_dir == Path("tests/test_data/projects")


class TestHelp:
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
            "  --cfg FILE  Project configuration file. Default: ./cfg.yml.",
            "  --version   Show the version and exit.",
            "  --help      Show this message and exit.",
            "",
            "Commands:",
            "  create  Create and manage datasets.",
        ]


class TestCreate:
    def test_create_envs(self, cli_helper, tmp_path):
        tmp_path = str(tmp_path)
        output = cli_helper.invoke(
            ["create", "envs"],
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
        assert sorted(os.listdir(cli_helper.ctx.envs_dir)) == sorted(["Kyle", "Sally"])
        user_env = VirtualEnvironment(str(cli_helper.ctx.envs_dir / "Kyle"))
        assert user_env.is_installed("pandas")
        user_env = VirtualEnvironment(str(cli_helper.ctx.envs_dir / "Sally"))
        assert user_env.is_installed("requests")

    def test_create_env_dir_copy_dir(self, cli_helper, data_fixtures):
        output = cli_helper.invoke(
            [
                "create",
                "dirs",
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
        assert sorted(os.listdir(cli_helper.ctx.projs_dir)) == sorted(["Kyle", "Sally"])
        assert sorted(os.listdir(cli_helper.ctx.projs_dir / "Kyle")) == [
            "test_file.txt"
        ]

    def test_create_env_dir_copy_file(self, cli_helper, data_fixtures):
        output = cli_helper.invoke(
            [
                "create",
                "dirs",
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
        assert sorted(os.listdir(cli_helper.ctx.projs_dir)) == sorted(["Kyle", "Sally"])
        assert os.listdir(str(cli_helper.ctx.projs_dir / "Kyle")) == ["test_file.txt"]
