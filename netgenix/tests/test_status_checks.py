import asyncio
import unittest
from unittest.mock import MagicMock, patch

from backend.api.routes import status as status_route
from backend.netgenix.services.database import check_api_status


class ProductionStatusChecksTest(unittest.TestCase):
    @patch("backend.netgenix.services.db_timescale.is_timescale_available", return_value=True)
    @patch("socket.socket")
    def test_production_status_uses_timescale_and_access_nbi(self, socket_factory, _db_check):
        socket_instance = MagicMock()
        socket_instance.connect_ex.return_value = 0
        socket_factory.return_value = socket_instance

        with patch.dict(
            "os.environ",
            {
                "DATABASE_URL": "postgresql://example.invalid/netgenix",
                "NETGENIX_HUAWEI_ACCESS_NBI_URL": "https://mae-edge:33127",
                "NETGENIX_HUAWEI_USERNAME": "configured-user",
            },
            clear=False,
        ):
            result = check_api_status()

        self.assertEqual(result["api"], "✅ Access NBI Connected")
        self.assertEqual(result["ne"], "✅ NEs Connected")
        self.assertEqual(result["db"], "✅ DB Connected")

    def test_api_status_does_not_depend_on_evaluation_browser_session(self):
        connected = {
            "api": "✅ Access NBI Connected",
            "ne": "✅ NEs Connected",
            "db": "✅ DB Connected",
        }
        with patch.object(status_route, "check_api_status", return_value=connected):
            result = asyncio.run(status_route.get_system_status())

        self.assertTrue(result.api_connected)
        self.assertTrue(result.ne_connected)
        self.assertTrue(result.db_connected)
        self.assertEqual(result.api_status, "✅ Access NBI Connected")


if __name__ == "__main__":
    unittest.main()
