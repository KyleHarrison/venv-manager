import shutil
from pathlib import Path

import click
import yaml
from virtualenvapi.manage import VirtualEnvironment

from venvman import __version__ as venvman_version


class VenvManager:
    def __init__(self, cfg):
        with open(cfg, "r") as f:
            config = yaml.safe_load(f)
        self.envs_dir = Path(config["environments_directory"])
        self.projs_dir = Path(config["projects_directory"])
        self.default_packages = config["default_packages"]
        self.environments = config["environments"]


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


@venvman.group("create")
def create():
    """Create and manage datasets."""


@create.command("envs")
@pass_cfg
def create_envs(cfg: VenvManager):
    """Creates a virtualenv for each environment specified in the yaml config file."""
    for env_name, packages in cfg.environments.items():
        click.echo(f"Creating env {env_name}")
        env_dir = cfg.envs_dir / env_name
        env_dir.mkdir(parents=True)
        env = VirtualEnvironment(str(env_dir))
        for package in cfg.default_packages + packages:
            click.echo(f"Installing package {package}")
            env.install(package)
    click.echo(f"Created envs {list(cfg.environments.keys())}")


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
    for env_name in cfg.environments:
        click.echo(f"Creating dir for {env_name}")
        dest_subdir = Path(cfg.projs_dir / env_name)
        if dest_subdir.is_dir():
            click.echo(f"Dir already exists for {env_name}, skipping")
        else:
            click.echo(f"Copying {src.name} to {dest_subdir.name}")
            dest_subdir.mkdir(parents=True)
            if src is not None:
                if src.is_dir():
                    shutil.copytree(src, dest_subdir, dirs_exist_ok=True)
                else:
                    shutil.copyfile(src, dest_subdir / src.name)
