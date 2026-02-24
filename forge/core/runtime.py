from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

import structlog

from forge.core.events import event_bus as _default_event_bus
from forge.core.types import (
    AgentConfig,
    AgentStatus,
    ForgeEvent,
    Message,
    Session,
    Step,
    StepType,
    ToolCall,
)
from forge.memory.manager import MemoryManager
from forge.models.router import ModelRouter
from forge.tools.executor import ToolExecutor

logger = structlog.get_logger()


class AgentRuntime:
    def __init__(
        self,
        config: AgentConfig,
        model_router: ModelRouter,
        tool_executor: ToolExecutor,
        memory_manager: MemoryManager,
        event_bus=None,
    ) -> None:
        self.config = config
        self.model_router = model_router
        self.tool_executor = tool_executor
        self.memory_manager = memory_manager
        self.event_bus = event_bus or _default_event_bus
        self._sessions: dict[str, Session] = {}

    async def create_session(self, metadata: dict | None = None) -> Session:
        session = Session(agent_name=self.config.name, metadata=metadata or {})

        if self.config.system_prompt:
            session.messages.append(Message(role="system", content=self.config.system_prompt))

        self._sessions[session.id] = session

        await self.event_bus.emit(ForgeEvent(
            type="session.created",
            session_id=session.id,
            agent_name=self.config.name,
        ))

        return session

    async def run(
        self,
        session_id: str,
        user_input: str,
        stream: bool = False,
    ) -> AsyncIterator[Step] | Message:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.status = AgentStatus.RUNNING
        session.messages.append(Message(role="user", content=user_input))

        await self.event_bus.emit(ForgeEvent(
            type="session.started",
            session_id=session.id,
            agent_name=self.config.name,
            data={"input": user_input},
        ))

        if stream:
            return self._run_loop_stream(session)

        # Non-streaming: collect all steps, return final message
        final_message = Message(role="assistant", content="")
        try:
            async for step in self._run_loop_stream(session):
                if step.type == StepType.RESPOND:
                    final_message = Message(role="assistant", content=str(step.output or ""))
        except Exception as e:
            session.status = AgentStatus.FAILED
            await self.event_bus.emit(ForgeEvent(
                type="session.error",
                session_id=session.id,
                agent_name=self.config.name,
                data={"error": str(e)},
            ))
            raise

        session.status = AgentStatus.COMPLETED
        return final_message

    async def _run_loop_stream(self, session: Session) -> AsyncIterator[Step]:
        for iteration in range(self.config.max_iterations):
            # 1. Check cost limit
            if session.total_cost >= self.config.cost_limit:
                step = Step(
                    type=StepType.RESPOND,
                    output=f"Cost limit reached (${session.total_cost:.2f} >= ${self.config.cost_limit:.2f}). Stopping.",
                )
                session.steps.append(step)
                session.status = AgentStatus.COMPLETED
                yield step
                return

            # 2. Retrieve memories
            memory_context = await self._retrieve_memories(session)

            # 3. Build messages
            messages = self._build_messages(session, memory_context)

            # 4. Think
            think_step = await self._think(session, messages)
            session.steps.append(think_step)
            yield think_step

            if think_step.error:
                error_step = Step(type=StepType.RESPOND, output=f"Error: {think_step.error}")
                session.steps.append(error_step)
                session.status = AgentStatus.FAILED
                yield error_step
                return

            # 5. Check for tool calls
            think_output = think_step.metadata.get("raw_response", {})
            tool_calls_raw = think_output.get("tool_calls")

            if not tool_calls_raw:
                # Final response
                content = str(think_step.output or "")
                respond_step = Step(type=StepType.RESPOND, output=content)
                session.steps.append(respond_step)
                session.messages.append(Message(role="assistant", content=content))

                await self.memory_manager.store(session.id, content)
                session.status = AgentStatus.COMPLETED
                yield respond_step
                return

            # 6. Execute tools
            for tc_data in tool_calls_raw:
                tool_call = ToolCall(
                    id=tc_data.get("id", ""),
                    name=tc_data.get("name", ""),
                    arguments=tc_data.get("arguments", {}),
                )

                act_step = await self._act(session, tool_call)
                session.steps.append(act_step)
                yield act_step

                # 7. Add tool result to session messages
                session.messages.append(Message(
                    role="tool",
                    content=str(act_step.output or act_step.error or ""),
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                ))

        # Max iterations reached
        limit_step = Step(
            type=StepType.RESPOND,
            output=f"Maximum iterations reached ({self.config.max_iterations}). Stopping.",
        )
        session.steps.append(limit_step)
        session.status = AgentStatus.COMPLETED
        yield limit_step

    async def _think(self, session: Session, messages: list[dict]) -> Step:
        await self.event_bus.emit(ForgeEvent(
            type="step.think.started",
            session_id=session.id,
            agent_name=self.config.name,
        ))

        start = time.time()
        try:
            tools = self.tool_executor.get_tool_schemas(
                allowed=self.config.allowed_tools,
                blocked=self.config.blocked_tools,
            )

            response = await self.model_router.complete(
                model_config=self.config.model,
                messages=messages,
                tools=tools if tools else None,
            )

            duration_ms = (time.time() - start) * 1000
            tokens_in = response.get("tokens_in", 0)
            tokens_out = response.get("tokens_out", 0)
            cost = response.get("cost", 0.0)

            session.total_cost += cost
            session.total_tokens += tokens_in + tokens_out

            # Add assistant message with tool_calls if present
            if response.get("tool_calls"):
                tc_objects = [
                    ToolCall(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                    for tc in response["tool_calls"]
                ]
                session.messages.append(Message(
                    role="assistant",
                    content=response.get("content", ""),
                    tool_calls=tc_objects,
                ))

            step = Step(
                type=StepType.THINK,
                output=response.get("content", ""),
                model_used=response.get("model"),
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                duration_ms=duration_ms,
                metadata={"raw_response": response},
            )

            await self.event_bus.emit(ForgeEvent(
                type="step.think.completed",
                session_id=session.id,
                agent_name=self.config.name,
                data={"tokens_in": tokens_in, "tokens_out": tokens_out, "cost": cost},
            ))

            return step

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error("think_error", error=str(e), exc_info=True)
            return Step(
                type=StepType.THINK,
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _act(self, session: Session, tool_call: ToolCall) -> Step:
        await self.event_bus.emit(ForgeEvent(
            type="step.tool.started",
            session_id=session.id,
            agent_name=self.config.name,
            data={"tool": tool_call.name, "arguments": tool_call.arguments},
        ))

        start = time.time()
        try:
            result = await self.tool_executor.execute(
                tool_name=tool_call.name,
                arguments=tool_call.arguments,
                session_id=session.id,
            )
            duration_ms = (time.time() - start) * 1000

            step = Step(
                type=StepType.TOOL_CALL,
                input={"tool": tool_call.name, "arguments": tool_call.arguments},
                output=result,
                duration_ms=duration_ms,
            )

            await self.event_bus.emit(ForgeEvent(
                type="step.tool.completed",
                session_id=session.id,
                agent_name=self.config.name,
                data={"tool": tool_call.name, "duration_ms": duration_ms},
            ))

            return step

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error("tool_error", tool=tool_call.name, error=str(e))

            return Step(
                type=StepType.TOOL_CALL,
                input={"tool": tool_call.name, "arguments": tool_call.arguments},
                error=str(e),
                duration_ms=duration_ms,
            )

    async def _retrieve_memories(self, session: Session) -> str:
        try:
            last_user_msg = ""
            for msg in reversed(session.messages):
                if msg.role == "user" and msg.content:
                    last_user_msg = msg.content
                    break

            if not last_user_msg:
                return ""

            memories = await self.memory_manager.retrieve(session.id, last_user_msg)
            if memories:
                return "\n\nRelevant context from memory:\n" + "\n".join(f"- {m}" for m in memories)
            return ""
        except Exception:
            logger.warning("memory_retrieval_error", exc_info=True)
            return ""

    def _build_messages(self, session: Session, memory_context: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []

        for msg in session.messages:
            m: dict[str, Any] = {"role": msg.role, "content": msg.content or ""}

            # Inject memory into system prompt
            if msg.role == "system" and memory_context:
                m["content"] = (msg.content or "") + memory_context

            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": str(tc.arguments)},
                    }
                    for tc in msg.tool_calls
                ]

            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id

            if msg.name and msg.role == "tool":
                m["name"] = msg.name

            messages.append(m)

        # Trim to max_working_memory
        max_msgs = self.config.memory.max_working_memory
        if len(messages) > max_msgs:
            system_msgs = [m for m in messages if m["role"] == "system"]
            other_msgs = [m for m in messages if m["role"] != "system"]
            keep = max_msgs - len(system_msgs)
            messages = system_msgs + other_msgs[-keep:]

        return messages

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        return list(self._sessions.values())

    async def terminate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.status = AgentStatus.TERMINATED
            await self.event_bus.emit(ForgeEvent(
                type="session.terminated",
                session_id=session.id,
                agent_name=self.config.name,
            ))
            return True
        return False
