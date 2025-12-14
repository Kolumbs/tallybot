"""Unit test package for workers."""

from agents import RunContextWrapper

from tallybot import workers
from tests import base


class TestCase(base.TestCase):
    """Base class for workers tests."""

    @base.add_clean_memory
    @base.add_memory
    def setUp(self):
        """Enable memory interface."""

    def tearDown(self):
        """Remove temp files."""
        base.remove_temps()

    def create_context(self, package):
        """Prepare context for function tools."""
        return RunContextWrapper(
            workers.TallybotContext(
                conf=self.config["tallybot"],
                memory=self.memory,
                package=package,
            )
        )

    async def run_function_tool(self, tool, package, text):
        """Run function tool with prepared context."""
        ctx = self.create_context(package)
        return await tool.on_invoke_tool(ctx, text)
