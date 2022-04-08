import os
import tempfile

from venvman import manager
from virtualenvapi.manage import VirtualEnvironment


class TestVenvManager:
    def test_create_users(self, data_fixtures, runner):
        temp_dir = tempfile.gettempdir()
        venv_dirs = os.path.join(temp_dir, "venvs")
        os.makedirs(venv_dirs, exist_ok=True)

        result = runner.invoke(
            manager.create_users, [str(data_fixtures / "envs.yml"), venv_dirs]
        )
        assert result.exit_code == 0
        assert result.output == "Created envs ['Kyle', 'Sally']\n"

        assert os.listdir(venv_dirs) == ["Kyle", "Sally"]
        user_env = VirtualEnvironment(os.path.join(venv_dirs, "Kyle"))
        assert user_env.is_installed("pandas") == True
        user_env = VirtualEnvironment(os.path.join(venv_dirs, "Sally"))
        assert user_env.is_installed("requests") == True
