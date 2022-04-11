import os
import shutil

import click
import yaml
from virtualenvapi.manage import VirtualEnvironment

from venvman import __version__ as venvman_version


class VenvManager:
    def __init__(self, cfg):
        with open(cfg, "r") as f:
            config = yaml.safe_load(f)
        self.envs = config["envs"]
        self.default_packages = config["default"]


# alias pass_obj for readability
pass_cfg = click.make_pass_decorator(VenvManager)


@click.group()
@click.option(
    "--cfg",
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
@click.option(
    "--directory",
    "--d",
    default=".",
    help="Directory for creating environments. Defaults to current directory.",
)
@pass_cfg
def create_envs(cfg: VenvManager, directory: str):
    """Creates a virtualenv for each environment specified in the yaml config file."""
    for env_name, packages in cfg.envs.items():
        click.echo(f"Creating env {env_name}")
        env = VirtualEnvironment(os.path.join(directory, env_name))
        for package in cfg.default_packages + packages:
            click.echo(f"Installing package {package}")
            env.install(package)
    click.echo(f"Created envs {list(cfg.envs.keys())}")


@create.command("dirs")
@click.option(
    "--dst",
    default=".",
    help="Directory for creating environment directories. Defaults to current directory.",
)
@click.option(
    "--src",
    default=None,
    help="Source directory or file to copy into each newly created directory.",
)
@pass_cfg
def create_dirs(cfg: VenvManager, dst: str, src: str):
    """Creates a directory in 'dst' for each environment in 'src'. Each directories
    contents is a copy of 'src'.
    """
    for env_name in cfg.envs:
        click.echo(f"Creating dir for {env_name}")
        dest_subdir = os.path.join(dst, env_name)
        if os.path.isdir(dest_subdir):
            click.echo(f"Dir already exists for {env_name}, skipping")
        else:
            click.echo(
                f"Copying {os.path.basename(src)} to {os.path.basename(dest_subdir)}"
            )
            os.makedirs(dest_subdir)
            if src is not None:
                if os.path.isdir(src):
                    shutil.copytree(src, dest_subdir, dirs_exist_ok=True)
                else:
                    shutil.copyfile(src, dest_subdir + f"/{os.path.basename(src)}")
