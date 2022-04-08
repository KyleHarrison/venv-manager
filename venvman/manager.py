import os

import click
import yaml
from virtualenvapi.manage import VirtualEnvironment


@click.command()
@click.argument("yaml_file", default="envs.yaml")
@click.argument("env_dir", default=".")
def create_users(yaml_file, env_dir):
    with open(yaml_file, "r") as f:
        config = yaml.safe_load(f)
    for env_name, packages in config["envs"].items():
        env = VirtualEnvironment(os.path.join(env_dir, env_name))
        for package in config["default"] + packages:
            env.install(package)
    click.echo(f"Created envs {list(config['envs'].keys())}")
