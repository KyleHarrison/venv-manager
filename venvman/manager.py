import os
import shutil

import click
import yaml
from virtualenvapi.manage import VirtualEnvironment


def open_yaml(yaml_file):
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)


@click.command()
@click.argument("yaml_file", default="envs.yaml")
@click.argument("env_dir", default=".")
def create_envs(yaml_file: str, env_dir: str):
    """Creates a virtualenv for each environment specified in the yaml config file.
    Each package specified in the config and each default package is installed in the
    generated environment.

    :param str yaml_file:
        The yaml config file defining environments and packages to be created.
    :param str env_dir:
        The destination directory for environments to be created.
    """
    config = open_yaml(yaml_file)
    for env_name, packages in config["envs"].items():
        click.echo(f"Creating env {env_name}")
        env = VirtualEnvironment(os.path.join(env_dir, env_name))
        for package in config["default"] + packages:
            click.echo(f"Installing package {package}")
            env.install(package)
    click.echo(f"Created envs {list(config['envs'].keys())}")


def create_dirs(yaml_file: str, dest_dir: str, source: str):
    """Creates a directory in 'dest_dir' for each environment in 'yaml_file'. Each
    directories contents is a copy of 'source'.

    :param str yaml_file:
        The yaml config file defining environments and packages to be created.
    :param str dest_dir:
        The destination for directories to be created.
    :param str source:
        The source to be copied to the created directory. Either a file or a directory.
    """
    config = open_yaml(yaml_file)
    for env_name in config["envs"]:
        click.echo(f"Creating dir for {env_name}")
        dest_subdir = os.path.join(dest_dir, env_name)
        if os.path.isdir(dest_subdir):
            click.echo(f"Dir already exists for {env_name}, skipping")
        else:
            click.echo(f"Copying {source} to {dest_subdir}")
            os.makedirs(dest_subdir)
            shutil.copytree(source, dest_subdir, dirs_exist_ok=True)
