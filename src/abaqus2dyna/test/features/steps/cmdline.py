import sys
import io
import shlex

from behave import given, then, fixture, use_fixture

import abaqus2dyna
import abaqus2dyna.__main__

class CmdlineFixture:
    def __init__(self):
        self.code = None
        self.args = None

    def run(self, argv):
        try:
            self.args = abaqus2dyna.__main__.cmdline(argv)
        except SystemExit as e:
            self.code = e.code

@fixture
def cmdline(context):
    context.cmdline = CmdlineFixture()
    yield context.cmdline

@given('no arguments')
def step_impl(context):
    cmd = use_fixture(cmdline, context)
    cmd.run([])

@given('arguments "{argv}"')
def step_impl(context, argv):
    cmd = use_fixture(cmdline, context)
    cmd.run(shlex.split(argv))

@then("we exit with {number:d}")
def step_impl(context, number):
    assert context.cmdline.code == number

@then('we start printing "{string}"')
def step_impl(context, string):
    context.stdout_capture.seek(0)
    assert context.stdout_capture.read().startswith(string)
@then('we start printing error "{string}"')
def step_impl(context, string):
    context.stderr_capture.seek(0)
    assert context.stderr_capture.read().startswith(string)


