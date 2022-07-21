import shutil
from pathlib import Path
from typing import Dict

import click
import yaml
from virtualenvapi.manage import VirtualEnvironment, PackageInstallationException

from venvman import __version__ as venvman_version


class VenvManager:
    def __init__(self, cfg):
        with open(cfg, "r") as f:
            config = yaml.safe_load(f)
        self.envs_dir = Path(config.get("environments_directory", "."))
        self.projs_dir = Path(config.get("projects_directory", "."))
        self.default_packages = config.get("default_packages")
        self.envs_cfg = config.get("environments")
        self.envs = self.init_envs()

    def init_envs(self):
        envs = {}
        for env_name in self.envs_cfg:
            envs[env_name] = VirtualEnvironment(
                str(self.envs_dir / env_name), python="python3"
            )
        return envs


# alias pass_obj for readability
pass_cfg = click.make_pass_decorator(VenvManager)


@click.group()
@click.option(
    "--cfg",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="./cfg.yml",
    help="Project configuration file. Default: ./cfg.yml.",
)
@click.version_option(version=venvman_version)
@click.pass_context
def venvman(ctx, cfg):
    """VenvMan. A simple approach to controlling multiple virtualenvs."""
    ctx.obj = VenvManager(cfg=cfg)


""" Create """


@venvman.group("create")
def create():
    """Create environments, directories and jupyter kernels."""


@create.command("envs")
@pass_cfg
def create_envs(cfg: VenvManager):
    """Creates a virtualenv for each environment specified in the yaml config file."""
    for env_name, pkgs in cfg.envs_cfg.items():
        click.echo(f"Creating env {env_name}")
        env = cfg.envs[env_name]
        Path(env.path).mkdir(parents=True)
        for pkg in cfg.default_packages + pkgs:
            click.echo(f"Installing package {pkg}")
            env.install(pkg)
    click.echo(f"Created envs {list(cfg.envs_cfg)}")


@create.command("kernels")
@click.option(
    "--sudo",
    "-s",
    is_flag=True,
    help="If True the command is executed in sudo.",
)
@pass_cfg
def create_kernels(cfg: VenvManager, sudo: bool):
    """Creates a jupyter kernel for each env."""
    for env_name, env in cfg.envs.items():
        click.echo(f"Creating jupyter kernel for {env_name}")
        if not env.is_installed("ipykernel"):
            env.install("ipykernel")
        python_bin = Path(cfg.envs[env_name].path) / "bin" / "python"
        command = [str(python_bin), "-m", "ipykernel", "install", f"--name={env.name}"]
        if sudo:
            command.insert(0, "sudo")
        env._execute(command)


@create.command("dirs")
@click.option(
    "--src",
    default=None,
    type=click.Path(path_type=Path),
    help="Source directory or file to copy into each newly created directory.",
)
@pass_cfg
def create_dirs(cfg: VenvManager, src: Path):
    """Creates a directory for each environment. Each directories contents is a copy of
    'src'.
    """
    for env_name in cfg.envs_cfg:
        dest_subdir = Path(cfg.projs_dir / env_name)
        click.echo(f"Creating dir for {env_name}")
        dest_subdir.mkdir(parents=True, exist_ok=True)
        if src is not None:
            click.echo(f"Copying {src.name} to {dest_subdir.name}")
            if src.is_dir():
                shutil.copytree(src, dest_subdir, dirs_exist_ok=True)
            else:
                shutil.copyfile(src, dest_subdir / src.name)


@create.command("repos")
@pass_cfg
def create_repos(cfg: VenvManager):
    """Clones as repo for each environment into the projects dir."""
    for env_name, env in cfg.envs.items():
        repo_path = Path(cfg.projs_dir) / Path(env_name)
        if repo_path.is_dir():
            click.echo(
                click.style(
                    f"Directory already exists {repo_path}, skipping.", fg="yellow"
                )
            )
            continue
        click.echo(f"Cloning repo for {repo_path}.")
        command = [
            "git",
            "clone",
            f"git@github.com:prodigyfinance/{env.name}.git",
            f"{cfg.projs_dir}/{env_name}",
        ]
        env._execute(command)


""" Install """


@venvman.command("install")
@click.argument("pkgs", nargs=-1)
@pass_cfg
def install_pkgs(cfg: VenvManager, pkgs: str):
    """Installs one or more packages in each environment."""
    for env_name in cfg.envs_cfg:
        env = cfg.envs[env_name]
        click.echo(f"Installing {list(pkgs)} in {env_name}")
        for pkg in pkgs:
            env.install(pkg)


@venvman.command("uninstall")
@click.argument("pkgs", nargs=-1)
@pass_cfg
def uninstall_pkgs(cfg: VenvManager, pkgs: str):
    """Installs one or more packages in each environment."""
    for env_name in cfg.envs_cfg:
        env = cfg.envs[env_name]
        click.echo(f"Uninstalling {list(pkgs)} in {env_name}")
        for pkg in pkgs:
            env.uninstall(pkg)


@venvman.command("install-source")
@pass_cfg
def install_source(cfg: VenvManager):
    """Installs each project from source."""
    for env_name, env in cfg.envs.items():
        repo_path = Path(cfg.projs_dir) / Path(env_name)
        if (repo_path / "setup.py").is_file():
            click.echo(f"Installing project source for {env_name}")
            try:
                env.install(
                    f"-e {repo_path}[dev]",
                )
            except PackageInstallationException:
                click.echo("Package install error, try manually fix package issues.")
                click.echo(f"Check {env._errorfile} for error logs.", err=True)
        else:
            click.echo(
                click.style(
                    f"Project {env_name} is not pip installable, skipping.", fg="yellow"
                )
            )


""" Upgrade """


@venvman.command("upgrade")
@click.argument("pkgs", nargs=-1)
@pass_cfg
def upgrade_pkgs(cfg: VenvManager, pkgs: str):
    """Upgrade one or more packages in each environment."""
    for env_name in cfg.envs_cfg:
        env = cfg.envs[env_name]
        click.echo(f"Upgrading {list(pkgs)} in {env_name}")
        for pkg in pkgs:
            env.upgrade(pkg)


""" Clean """


@venvman.group("clean")
def clean():
    """Remove envs and dirs missing from config."""


def find_missing_dirs(dir_src: Dict, dir_dst: Path):
    """Finds directories in the destination 'dir_dst' whos names are missing from the
    source 'dir_src'.

    :param list dir_src:
        A list of directory names which should be in the destination.
    :param pathlib.Path dir_dst:
        The Path to the directory which should contain each item from src.
    """
    missing = []
    for dir in dir_dst.iterdir():
        if dir.name not in dir_src:
            missing.append(dir)
    return missing


@clean.command("envs")
@pass_cfg
def clean_envs(cfg: VenvManager):
    """Remove folders in the envs dir which are no longer in the config."""
    missing = find_missing_dirs(cfg.envs_cfg, cfg.envs_dir)
    if click.confirm(
        f"Are you sure you want to remove envs {missing} missing from config?"
    ):
        [shutil.rmtree(dir) for dir in missing]


@clean.command("prjs")
@pass_cfg
def clean_dirs(cfg: VenvManager):
    """Remove folders in the prjs dir which are no longer in the config."""
    missing = find_missing_dirs(cfg.envs_cfg, cfg.projs_dir)
    if click.confirm(
        f"Are you sure you want to remove project dirs {missing} missing from config?"
    ):
        [shutil.rmtree(dir) for dir in missing]
