import json
import os
from pathlib import Path
from unittest import mock

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

    def create_env_dirs(self):
        """Use when envs have not been created, create dirs so they can be init."""
        for env in self.ctx.envs.values():
            Path(env.path).mkdir(parents=True)

    def list_envs(self):
        return sorted(os.listdir(self.ctx.envs_dir))

    def list_prjs(self, sub_dir: Path = None):
        if sub_dir is not None:
            return sorted(os.listdir(self.ctx.projs_dir / sub_dir))
        return sorted(os.listdir(self.ctx.projs_dir))

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
        assert config.envs_cfg == {"Kyle": ["pandas"], "Sally": ["requests"]}
        assert config.envs_dir == Path("tests/test_data/envs")
        assert config.projs_dir == Path("tests/test_data/projects")


class TestHelp:
    def test_help_command(self, cli_helper: CLIHelper):
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
            "  clean    Remove envs and dirs missing from config.",
            "  create   Create environments and directories.",
            "  install  Installs one or more packages in each environment.",
            "  upgrade  Upgrade one or more packages in each environment.",
        ]


class TestCreate:
    def test_create_envs(self, cli_helper: CLIHelper, tmp_path):
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
        assert cli_helper.list_envs() == sorted(["Kyle", "Sally"])
        user_env = VirtualEnvironment(str(cli_helper.ctx.envs_dir / "Kyle"))
        assert user_env.is_installed("pandas")
        assert cli_helper.ctx.envs["Kyle"].is_installed("pandas")
        user_env = VirtualEnvironment(str(cli_helper.ctx.envs_dir / "Sally"))
        assert user_env.is_installed("requests")

    def test_create_prj_dir_copy_dir(self, cli_helper: CLIHelper, data_fixtures):
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
        assert cli_helper.list_prjs() == sorted(["Kyle", "Sally"])
        assert cli_helper.list_prjs("Kyle") == ["test_file.txt"]

    def test_create_prj_dir_copy_file(self, cli_helper, data_fixtures):
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
        assert cli_helper.list_prjs() == sorted(["Kyle", "Sally"])
        assert cli_helper.list_prjs("Kyle") == ["test_file.txt"]

    def test_create_prj_dir_empty(self, cli_helper):
        output = cli_helper.invoke(
            [
                "create",
                "dirs",
            ],
        )
        assert output == [
            "Creating dir for Kyle",
            "Creating dir for Sally",
        ]
        assert cli_helper.list_prjs() == sorted(["Kyle", "Sally"])
        assert cli_helper.list_prjs("Kyle") == []


class TestInstall:
    def test_install_pkg(self, cli_helper: CLIHelper):
        cli_helper.create_env_dirs()
        output = cli_helper.invoke(["install", "eli5"])
        assert output == ["Installing ['eli5'] in Kyle", "Installing ['eli5'] in Sally"]

    def test_install_pkgs(self, cli_helper: CLIHelper):
        cli_helper.create_env_dirs()
        output = cli_helper.invoke(
            ["install", "flake8", "black"],
            cfg={
                "environments": {"Kyle": [], "Sally": []},
            },
        )
        assert output == [
            "Installing ['flake8', 'black'] in Kyle",
            "Installing ['flake8', 'black'] in Sally",
        ]


class TestUpgrade:
    def test_upgrade_pkg(self, cli_helper: CLIHelper):
        cli_helper.create_env_dirs()
        output = cli_helper.invoke(
            ["upgrade", "numpy"],
            cfg={
                "environments": {"Kyle": ["numpy==1.0.0"]},
            },
        )
        assert output == ["Upgrading ['numpy'] in Kyle"]
        assert [
            ver
            for pkg, ver in cli_helper.ctx.envs["Kyle"].installed_packages
            if pkg == "numpy"
        ] != ["1.0.0"]


class TestClean:
    @mock.patch("click.confirm")
    def test_clean_envs(self, mock_click, cli_helper: CLIHelper):
        cli_helper.create_env_dirs()
        mock_click.return_value = "y"
        assert cli_helper.list_envs() == sorted(["Kyle", "Sally"])
        cli_helper.invoke(
            ["clean", "envs"],
            cfg={
                "environments": {"Kyle": []},
            },
        )
        assert cli_helper.list_envs() == ["Kyle"]

    @mock.patch("click.confirm")
    def test_clean_prjs(self, mock_click, cli_helper: CLIHelper):
        mock_click.return_value = "y"
        cli_helper.invoke(
            [
                "create",
                "dirs",
            ],
        )
        assert cli_helper.list_prjs() == sorted(["Kyle", "Sally"])
        cli_helper.invoke(
            ["clean", "prjs"],
            cfg={
                "environments": {"Kyle": []},
            },
        )
        assert cli_helper.list_prjs() == ["Kyle"]
