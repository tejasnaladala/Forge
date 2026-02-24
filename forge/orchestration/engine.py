from __future__ import annotations

import asyncio
from typing import Any

import structlog

from forge.core.runtime import AgentRuntime

logger = structlog.get_logger()


class OrchestrationEngine:
    def __init__(self) -> None:
        self._runtimes: dict[str, AgentRuntime] = {}

    def register_runtime(self, name: str, runtime: AgentRuntime) -> None:
        self._runtimes[name] = runtime

    def get_runtime(self, name: str) -> AgentRuntime | None:
        return self._runtimes.get(name)

    def list_agents(self) -> list[str]:
        return list(self._runtimes.keys())

    async def run_agent(self, agent_name: str, input_text: str, metadata: dict | None = None) -> dict:
        runtime = self._runtimes.get(agent_name)
        if runtime is None:
            raise ValueError(f"Agent not found: {agent_name}")

        session = await runtime.create_session(metadata=metadata)
        response = await runtime.run(session.id, input_text, stream=False)

        return {
            "agent": agent_name,
            "session_id": session.id,
            "output": response.content or "",
            "cost": session.total_cost,
            "tokens": session.total_tokens,
            "steps": len(session.steps),
        }

    async def run_workflow(self, workflow_dict: dict, user_input: str) -> dict:
        workflow_type = workflow_dict.get("type", "sequential")

        if workflow_type == "sequential":
            return await self._run_sequential(workflow_dict, user_input)
        elif workflow_type == "parallel":
            return await self._run_parallel(workflow_dict, user_input)
        elif workflow_type == "supervisor":
            return await self._run_supervisor(workflow_dict, user_input)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

    async def _run_sequential(self, workflow: dict, initial_input: str) -> dict:
        steps_config = workflow.get("steps", [])
        current_input = initial_input
        results: list[dict] = []
        total_cost = 0.0

        for step in steps_config:
            agent_name = step.get("agent", step.get("name", ""))
            result = await self.run_agent(agent_name, current_input)
            results.append(result)
            current_input = result["output"]
            total_cost += result["cost"]

        return {
            "workflow": workflow.get("name", "sequential"),
            "type": "sequential",
            "steps": results,
            "final_output": current_input,
            "total_cost": total_cost,
        }

    async def _run_parallel(self, workflow: dict, input_text: str) -> dict:
        steps_config = workflow.get("steps", [])

        tasks = []
        for step in steps_config:
            agent_name = step.get("agent", step.get("name", ""))
            tasks.append(self.run_agent(agent_name, input_text))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        total_cost = 0.0
        outputs = []

        for r in results:
            if isinstance(r, Exception):
                valid_results.append({"error": str(r)})
            else:
                valid_results.append(r)
                outputs.append(r["output"])
                total_cost += r["cost"]

        merged_output = "\n\n---\n\n".join(outputs)

        return {
            "workflow": workflow.get("name", "parallel"),
            "type": "parallel",
            "steps": valid_results,
            "merged_output": merged_output,
            "total_cost": total_cost,
        }

    async def _run_supervisor(self, workflow: dict, input_text: str) -> dict:
        supervisor_name = workflow.get("supervisor", workflow.get("agent", ""))
        result = await self.run_agent(supervisor_name, input_text)
        return result
