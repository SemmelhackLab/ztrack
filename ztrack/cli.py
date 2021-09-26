from functools import reduce

import click

inputs = click.argument("inputs", nargs=-1, type=click.Path(exists=True))
recursive = click.option(
    "-r", "--recursive", is_flag=True, help="Look for files in subdirectories."
)
overwrite = click.option(
    "--overwrite/--no-overwrite", default=True, show_default=True
)
verbose = click.option("-v", "--verbose", count=True, help="Verbosity.")
common_parameters = (inputs, recursive, verbose)


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
@overwrite
def create_config(**kwargs):
    from ztrack._create_config import create_config

    create_config(**kwargs)


@main.command(
    short_help="Run tracking on videos with created tracking configurations."
)
@my_command
@overwrite
@click.option(
    "-i",
    "--ignore-errors",
    is_flag=True,
    help="Whether to view video in egocentric coordinates.",
)
def run(**kwargs):
    from ztrack._run_tracking import run_tracking

    run_tracking(**kwargs)


@main.command(short_help="View tracking results.")
@my_command
@click.option(
    "--gui/--no-gui",
    default=True,
    show_default=True,
    help="Whether to view results using GUI or generate a tracking video.",
)
@click.option(
    "--codec",
    default="mp4v",
    show_default=True,
    help="Codec to use for generating the tracking video.",
)
@click.option(
    "--fps",
    default=None,
    show_default=True,
    type=float,
    help="Frames per second (default to the FPS of the original video).",
)
@click.option(
    "--line-width",
    default=2,
    show_default=True,
    help="Line width for annotating the body parts.",
)
@click.option(
    "--frame-range",
    default=None,
    type=(int, int),
    show_default=True,
    help="Range to use for generating the tracking video (default to all frames).",
)
@click.option(
    "--format",
    default="mp4",
    show_default=True,
    help="Format to use for generating the tracking video.",
)
@click.option(
    "--egocentric",
    is_flag=True,
    help="Whether to view video in egocentric coordinates.",
)
@click.option(
    "--width",
    default=200,
    show_default=True,
    help="Width of video (for egocentric view)",
)
@click.option(
    "--front",
    default=80,
    show_default=True,
    help="Number of pixels in front of midpoint of eyes (for egocentric view)",
)
@click.option(
    "--behind",
    default=120,
    show_default=True,
    help="Number of pixels behind midpoint of eyes (for egocentric view)",
)
@click.option(
    "--label/--no-label",
    default=True,
    show_default=True,
    help="Whether to label body parts.",
)
@click.option(
    "--timer",
    is_flag=True,
    help="Show timer in the tracking video.",
)
def view(**kwargs):
    from ztrack._view_results import view_results

    view_results(**kwargs)


@main.command(short_help="Open GUI.")
@verbose
@click.option("--style", default="dark", show_default=True)
def gui(**kwargs):
    from ztrack._run_gui import run_gui

    run_gui(**kwargs)
