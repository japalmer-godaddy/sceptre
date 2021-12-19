import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
    catch_exceptions,
    write
)
from sceptre.plan.plan import SceptrePlan


@click.group(name="drift")
def drift_group():
    """
    Commands for calling drift detection.
    """
    pass


@drift_group.command(name="detect", short_help="Run detect stack drift on running stacks.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def drift_detect(ctx, path):
    """
    Detect stack drift and return if drift has occurred.
    \f

    :param path: The path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.drift_detect()

    exit_status = 0
    for stack, (status, response) in responses.values():
        if status in ["DETECTION_FAILED", "TIMED_OUT"]:
            exit_status += 1
        write({stack: response}, context.output_format)

    exit(exit_status)


@drift_group.command(name="show", short_help="Shows stack drift on running stacks.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def drift_show(ctx, path):
    """
    Show stack drift on running stacks.
    \f

    :param path: The path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.drift_show()

    exit_status = 0
    for stack, (status, response) in responses.values():
        if status in ["DETECTION_FAILED", "TIMED_OUT"]:
            exit_status += 1
        write({stack: response}, context.output_format)

    exit(exit_status)