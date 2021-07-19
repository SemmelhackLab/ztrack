from functools import reduce

import click

common_parameters = (
    click.argument("inputs", nargs=-1, type=click.Path(exists=True)),
    click.option(
        "-r",
        "--recursive",
        is_flag=True,
        help="Look for files in subdirectories.",
    ),
    click.option(
        "--overwrite/--no-overwrite", default=True, show_default=True
    ),
    click.option(
        "-v",
        "--verbose",
        count=True,
        help="Level of logging (default: WARNING; -v: INFO; -vv: DEBUG).",
    ),
)


def my_command(f):
    return reduce(lambda x, dec: dec(x), reversed(common_parameters), f)


@click.group()
def main():
    pass


@main.command(short_help="Create tracking configurations for videos.")
@my_command
@click.option(
    "-s",
    "--same-config",
    default=False,
    show_default=True,
    is_flag=True,
    help="Generate the same configuration file for all videos in the "
    "directory",
)
def create_config(**kwargs):
    from ztrack._create_config import create_config

    create_config(**kwargs)


@main.command(
    short_help="Run tracking on videos with created tracking configurations."
)
@my_command
def run(**kwargs):
    pass


@main.command(short_help="Plot tracking results.")
@my_command
def plot(**kwargs):
    pass


@main.command(short_help="Open GUI.")
@click.option("--style", default="dark", show_default=True)
def gui(**kwargs):
    from ztrack.gui.menu_widget import main as main_
    main_()
