from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from backend.api.routes import optimization as optimization_route
from backend.models.schemas import OptimizationRequest
from backend.netgenix.services import optimization


class _StructuredLLM:
    def invoke(self, _messages):
        return optimization.LLMOptimizationResponse(
            issue="Site is healthy",
            risk_score=0,
        )


class _LLM:
    def with_structured_output(self, schema):
        assert schema is optimization.LLMOptimizationResponse
        return _StructuredLLM()


class OptimizationRuntimeTests(unittest.TestCase):
    def test_gemini_budget_leaves_room_for_reasoning_and_structured_json(self):
        context = {
            "current_kpis": {"network_access_success": 99.0},
            "history": {"network_access_success": [{"date": "2026-08-26", "value": 99.0}]},
            "baselines": {"network_access_success": {"value": 98.0, "lower_is_better": False}},
            "parameters": {},
        }
        with (
            patch.object(optimization, "_collect_llm_context", return_value=context),
            patch("utils.llm_factory.get_llm_client", return_value=_LLM()) as factory,
            patch("backend.netgenix.services.database.log_optimization_query"),
        ):
            result = optimization._run_real_llm_optimization("SITE-001", 1, "Check health")

        factory.assert_called_once_with(temperature=0.2, max_tokens=8192, timeout=120)
        self.assertEqual(result["status"], "success")

    def test_api_runs_blocking_database_and_llm_work_in_threadpool(self):
        calls = []

        async def run_in_threadpool(func, *args, **kwargs):
            calls.append(func)
            return func(*args, **kwargs)

        request = OptimizationRequest(site_name="SITE-001", cell_id=1, query="Check health")
        with (
            patch.object(optimization_route, "run_in_threadpool", side_effect=run_in_threadpool),
            patch.object(
                optimization_route,
                "get_site_info",
                return_value={"site_name": "SITE-001"},
            ) as get_site_info,
            patch.object(
                optimization_route,
                "run_optimization",
                return_value={"status": "error", "error_message": "test response"},
            ) as run_optimization,
        ):
            response = asyncio.run(optimization_route.run_optimization_api(request))

        self.assertEqual(calls, [get_site_info, run_optimization])
        self.assertEqual(response.status, "error")
        self.assertEqual(response.error_message, "test response")


if __name__ == "__main__":
    unittest.main()
