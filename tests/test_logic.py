
# Local library
from . import lib

import pyblish.plugin
import pyblish.logic

from pyblish.vendor.nose.tools import *


@with_setup(lib.setup_empty, lib.teardown)
def test_process_callables():
    """logic.process can take either data or callables"""

    count = {"#": 0}

    class SelectInstance(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    class ValidateInstance(pyblish.api.Validator):
        def process(self, instance):
            count["#"] += 1
            assert False, "I was programmed to fail"

    class ExtractInstance(pyblish.api.Extractor):
        def process(self, instance):
            count["#"] += 1

    pyblish.api.register_plugin(SelectInstance)
    pyblish.api.register_plugin(ValidateInstance)
    pyblish.api.register_plugin(ExtractInstance)

    _context = pyblish.plugin.Context()

    for result in pyblish.logic.process(
            func=pyblish.util.process,
            plugins=pyblish.plugin.discover(),
            context=_context):

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 2)

    def context():
        return _context

    count["#"] = 0

    for result in pyblish.logic.process(
            func=pyblish.util.process,
            plugins=pyblish.plugin.discover,  # <- Callable
            context=context):  # <- Callable

        if isinstance(result, pyblish.logic.TestFailed):
            break

        if isinstance(result, Exception):
            assert False  # This would be a bug

    assert_equals(count["#"], 2)


@with_setup(lib.setup_empty, lib.teardown)
def test_repair():
    """Repairing with DI works well"""

    _data = {}

    class SelectInstance(pyblish.api.Selector):
        def process(self, context):
            context.create_instance("MyInstance")

    class ValidateInstance(pyblish.api.Validator):
        def process(self, instance):
            _data["broken"] = True
            assert False, "Broken"

        def repair(self, instance):
            _data["broken"] = False

    context = pyblish.api.Context()

    results = list()
    for result in pyblish.logic.process(
            func=pyblish.util.process,
            plugins=[SelectInstance, ValidateInstance],
            context=context):

        if isinstance(result, pyblish.logic.TestFailed):
            assert str(result) == "Broken"

        results.append(result)

    assert_true(_data["broken"])

    repair = list()
    for result in results:
        if result["error"]:
            repair.append(result["plugin"])

    for result in pyblish.logic.process(
            func=pyblish.util.repair,
            plugins=repair,
            context=context):
        print result

    assert_false(_data["broken"])
