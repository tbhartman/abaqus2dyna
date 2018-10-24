import io

from behave import given, then, when

import abaqus2dyna.__main__

@given('{filename}')
def step_impl(context, filename):
    context.name = filename

@when("we convert it")
def step_impl(context):
    context.out = io.StringIO()
    with open(context.name) as fin:
        abaqus2dyna.__main__.convert(fin, context.out)

@then('we expect an output file with {number:d} lines')
def step_impl(context, number):
    context.out.seek(0)
    print(len(context.out.read().splitlines()))
    context.out.seek(0)
    assert len(context.out.read().splitlines()) == number

