import asyncio
import signal
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch


common_utils = types.ModuleType("mantis.utils.common_utils")
common_utils.CommonUtils = object
args_model = types.ModuleType("mantis.models.args_model")
args_model.ArgsModel = object
sys.modules[common_utils.__name__] = common_utils
sys.modules[args_model.__name__] = args_model

from mantis.tool_base_classes.toolScanner import ToolScanner


class TestScanner(ToolScanner):
    def parse_report(self, outfile):
        raise AssertionError("a timed-out command must not be parsed")

    async def db_operations(self, tool_output_dict, asset=None):
        raise AssertionError("a timed-out command must not update the database")


class ToolScannerTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_terminates_the_process_group_and_returns_a_failure(self):
        scanner = TestScanner()
        scanner.command_timeout_seconds = 0.01

        async def wait_forever():
            await asyncio.sleep(60)

        process = Mock(pid=123, returncode=None)
        process.communicate = AsyncMock(side_effect=wait_forever)
        process.wait = AsyncMock(return_value=-signal.SIGTERM)

        with patch(
            "mantis.tool_base_classes.toolScanner.asyncio.create_subprocess_shell",
            new=AsyncMock(return_value=process),
        ) as create_process, patch(
            "mantis.tool_base_classes.toolScanner.os.killpg"
        ) as kill_group:
            result = await scanner.execute(
                (scanner, "long-running-tool", "/tmp/output.json", "example.com")
            )

        create_process.assert_awaited_once_with(
            "long-running-tool",
            stderr=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            shell=True,
            start_new_session=True,
        )
        kill_group.assert_called_once_with(123, signal.SIGTERM)
        self.assertEqual(-signal.SIGTERM, result["code"])
        self.assertEqual(0, result["success"])
        self.assertEqual(1, result["failure"])
        self.assertIn("timed out", result["exception"])


if __name__ == "__main__":
    unittest.main()
