import os
import shutil
import tempfile

from virtualenvapi.manage import VirtualEnvironment

from venvman import manager


class TestVenvManager:
    def test_create_envs(self, tmp_path, yaml_config, runner):
        tmp_path = str(tmp_path)
        result = runner.invoke(manager.create_envs, [yaml_config, tmp_path])
        assert result.exit_code == 0
        assert (
            result.output
            == "Creating env Kyle\nInstalling package numpy\nInstalling package"
            " pandas\nCreating env Sally\nInstalling package numpy\nInstalling"
            " package requests\nCreated envs ['Kyle', 'Sally']\n"
        )

        assert sorted(os.listdir(tmp_path)) == sorted(["Kyle", "Sally"])
        user_env = VirtualEnvironment(os.path.join(tmp_path, "Kyle"))
        assert user_env.is_installed("pandas")
        user_env = VirtualEnvironment(os.path.join(tmp_path, "Sally"))
        assert user_env.is_installed("requests")

    def test_create_env_current_dir(self, yaml_config, runner):
        result = runner.invoke(manager.create_envs, [yaml_config])
        assert result.exit_code == 0

        assert os.path.isdir("Kyle")
        assert os.path.isdir("Sally")
        shutil.rmtree("Kyle")
        shutil.rmtree("Sally")

    def test_create_env_dir_copy_dir(
        self, tmp_path, yaml_config, runner, data_fixtures
    ):
        manager.create_dirs(
            yaml_config,
            str(tmp_path / "dest_dir"),
            str(data_fixtures / "test_copy_dir"),
        )
        assert sorted(os.listdir(str(tmp_path / "dest_dir"))) == sorted(
            ["Kyle", "Sally"]
        )
        assert os.listdir(str(tmp_path / "dest_dir" / "Kyle")) == ["test_file.txt"]
