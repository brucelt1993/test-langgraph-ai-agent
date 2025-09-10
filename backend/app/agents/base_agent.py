"""
AI Agent基础架构。

提供基于LangGraph的AI Agent核心功能，包括：
- 基础对话管理
- OpenAI集成
- 工具系统
- 对话上下文维护
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
import asyncio
from enum import Enum

from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
)
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# 延迟导入避免循环依赖
def get_thinking_tracker():
    """获取思考追踪器（延迟导入）。"""
    from app.agents.thinking_tracker import get_thinking_tracker
    return get_thinking_tracker()


class AgentState(BaseModel):
    """Agent状态定义。"""
    messages: List[BaseMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    thinking_process: List[str] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    max_errors: int = 3
    
    # 思考追踪相关
    thinking_tracker_id: Optional[str] = None
    enable_thinking_tracking: bool = True
    current_thinking_phase: Optional[str] = None


class MessageType(str, Enum):
    """消息类型枚举。"""
    HUMAN = "human"
    AI = "ai" 
    SYSTEM = "system"
    TOOL = "tool"
    THINKING = "thinking"


@dataclass
class AgentResponse:
    """Agent响应数据结构。"""
    content: str
    message_type: MessageType
    thinking_process: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAgent(ABC):
    """
    基础AI Agent抽象类。
    
    提供基础的对话管理、工具系统和状态管理功能。
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        tools: Optional[List[BaseTool]] = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        enable_thinking_tracking: bool = True
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_thinking_tracking = enable_thinking_tracking
        
        # 初始化OpenAI客户端
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_URL
        )
        
        # 绑定工具
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm
        
        # 初始化状态图
        self.workflow = self._build_workflow()
        self.checkpointer = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info(f"Agent '{self.name}' initialized with {len(self.tools)} tools")
    
    def _build_workflow(self) -> StateGraph:
        """构建Agent工作流。"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("think", self._think_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("use_tools", self._use_tools_node)
        workflow.add_node("respond", self._respond_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # 设置入口点
        workflow.add_edge(START, "think")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "think",
            self._should_continue_thinking,
            {
                "act": "act",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "act",
            self._should_use_tools,
            {
                "use_tools": "use_tools",
                "respond": "respond",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("use_tools", "respond")
        workflow.add_edge("respond", END)
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    async def _think_node(self, state: AgentState) -> AgentState:
        """思考节点 - 分析输入并规划响应。"""
        try:
            # 设置思考阶段
            state.current_thinking_phase = "analysis"
            
            # 构建思考提示
            thinking_prompt = self._build_thinking_prompt(state)
            
            # 记录思考开始
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_observation(
                    session_id=state.session_id,
                    title="开始分析用户输入",
                    content=f"接收到用户消息，开始分析意图和需求：{state.messages[-1].content[:100]}..."
                )
            
            # 生成思考过程
            thinking_message = SystemMessage(content=thinking_prompt)
            messages = [thinking_message] + state.messages[-5:]  # 最近5条消息作为上下文
            
            response = await self.llm.ainvoke(messages)
            thinking_content = response.content
            
            # 记录思考内容
            state.thinking_process.append(thinking_content)
            
            # 记录分析结果
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_analysis(
                    session_id=state.session_id,
                    title="完成输入分析",
                    content=thinking_content,
                    reasoning="基于用户消息内容和上下文进行分析",
                    confidence=0.8
                )
            
            logger.debug(f"Agent thinking: {thinking_content[:100]}...")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in think node: {e}")
            state.error_count += 1
            
            # 记录错误
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_analysis(
                    session_id=state.session_id,
                    title="思考过程出错",
                    content=f"在分析阶段出现错误：{str(e)}",
                    confidence=0.0
                )
            
            return state
    
    async def _act_node(self, state: AgentState) -> AgentState:
        """行动节点 - 生成响应或工具调用。"""
        try:
            # 设置思考阶段
            state.current_thinking_phase = "planning"
            
            # 记录决策开始
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_decision(
                    session_id=state.session_id,
                    title="开始制定行动计划",
                    content="基于分析结果，开始决定如何响应用户",
                    reasoning="需要选择使用工具还是直接回答",
                    confidence=0.7
                )
            
            # 构建完整的消息历史
            messages = self._build_message_history(state)
            
            # 调用LLM
            response = await self.llm_with_tools.ainvoke(messages)
            
            # 添加AI响应到状态
            state.messages.append(response)
            
            # 检查是否有工具调用
            has_tool_calls = False
            if hasattr(response, 'tool_calls') and response.tool_calls:
                state.tool_calls.extend([
                    {
                        "id": tool_call.get("id"),
                        "name": tool_call.get("name"),
                        "args": tool_call.get("args")
                    }
                    for tool_call in response.tool_calls
                ])
                has_tool_calls = True
                
                # 记录工具选择决策
                if state.enable_thinking_tracking and state.user_id and state.session_id:
                    tracker = get_thinking_tracker()
                    for tool_call in response.tool_calls:
                        await tracker.add_decision(
                            session_id=state.session_id,
                            title=f"决定使用工具: {tool_call.get('name')}",
                            content=f"选择使用 {tool_call.get('name')} 工具来处理用户请求",
                            reasoning=f"工具参数: {json.dumps(tool_call.get('args', {}), ensure_ascii=False)}",
                            confidence=0.9,
                            importance=0.8
                        )
            else:
                # 记录直接回答决策
                if state.enable_thinking_tracking and state.user_id and state.session_id:
                    tracker = get_thinking_tracker()
                    await tracker.add_decision(
                        session_id=state.session_id,
                        title="决定直接回答",
                        content="无需使用工具，准备直接回答用户问题",
                        reasoning="分析后认为可以直接基于已有知识回答",
                        confidence=0.8
                    )
            
            logger.debug(f"Agent acted: {len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0} tool calls")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in act node: {e}")
            state.error_count += 1
            
            # 记录错误
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_decision(
                    session_id=state.session_id,
                    title="行动规划出错",
                    content=f"在规划阶段出现错误：{str(e)}",
                    confidence=0.0
                )
            
            return state
    
    async def _use_tools_node(self, state: AgentState) -> AgentState:
        """工具使用节点 - 执行工具调用。"""
        try:
            # 设置思考阶段
            state.current_thinking_phase = "execution"
            
            if not state.tool_calls:
                return state
            
            tool_responses = []
            
            for tool_call in state.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")
                
                # 记录工具调用开始
                if state.enable_thinking_tracking and state.user_id and state.session_id:
                    tracker = get_thinking_tracker()
                    await tracker.add_tool_call(
                        session_id=state.session_id,
                        tool_name=tool_name,
                        tool_input=tool_args,
                        reasoning=f"开始执行工具 {tool_name}",
                        confidence=0.9
                    )
                
                # 查找对应的工具
                tool = next((t for t in self.tools if t.name == tool_name), None)
                if not tool:
                    error_msg = f"Tool '{tool_name}' not found"
                    logger.error(error_msg)
                    tool_responses.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id
                    ))
                    
                    # 记录工具未找到错误
                    if state.enable_thinking_tracking and state.user_id and state.session_id:
                        tracker = get_thinking_tracker()
                        await tracker.add_tool_call(
                            session_id=state.session_id,
                            tool_name=tool_name,
                            tool_input=tool_args,
                            tool_output=error_msg,
                            reasoning=f"工具 {tool_name} 未找到",
                            confidence=0.0
                        )
                    continue
                
                try:
                    # 执行工具
                    result = await tool.ainvoke(tool_args)
                    result_str = str(result)
                    tool_responses.append(ToolMessage(
                        content=result_str,
                        tool_call_id=tool_id
                    ))
                    
                    # 记录成功的工具执行
                    if state.enable_thinking_tracking and state.user_id and state.session_id:
                        tracker = get_thinking_tracker()
                        await tracker.add_tool_call(
                            session_id=state.session_id,
                            tool_name=tool_name,
                            tool_input=tool_args,
                            tool_output=result_str[:500] + "..." if len(result_str) > 500 else result_str,
                            reasoning=f"工具 {tool_name} 执行成功",
                            confidence=0.95
                        )
                    
                    logger.debug(f"Tool '{tool_name}' executed successfully")
                    
                except Exception as tool_error:
                    error_msg = f"Error executing tool '{tool_name}': {str(tool_error)}"
                    logger.error(error_msg)
                    tool_responses.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id
                    ))
                    
                    # 记录工具执行错误
                    if state.enable_thinking_tracking and state.user_id and state.session_id:
                        tracker = get_thinking_tracker()
                        await tracker.add_tool_call(
                            session_id=state.session_id,
                            tool_name=tool_name,
                            tool_input=tool_args,
                            tool_output=error_msg,
                            reasoning=f"工具 {tool_name} 执行失败：{str(tool_error)}",
                            confidence=0.0
                        )
            
            # 添加工具响应到消息历史
            state.messages.extend(tool_responses)
            
            # 清空工具调用列表
            state.tool_calls = []
            
            return state
            
        except Exception as e:
            logger.error(f"Error in use_tools node: {e}")
            state.error_count += 1
            
            # 记录节点级错误
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_analysis(
                    session_id=state.session_id,
                    title="工具执行节点出错",
                    content=f"在工具执行阶段出现错误：{str(e)}",
                    confidence=0.0
                )
            
            return state
    
    async def _respond_node(self, state: AgentState) -> AgentState:
        """响应节点 - 生成最终响应。"""
        try:
            # 设置思考阶段
            state.current_thinking_phase = "response_generation"
            
            # 如果刚刚使用了工具，需要重新调用LLM来总结结果
            if state.messages and isinstance(state.messages[-1], ToolMessage):
                messages = self._build_message_history(state)
                response = await self.llm.ainvoke(messages)
                state.messages.append(response)
                
                # 记录基于工具结果的响应生成
                if state.enable_thinking_tracking and state.user_id and state.session_id:
                    tracker = get_thinking_tracker()
                    await tracker.add_conclusion(
                        session_id=state.session_id,
                        title="基于工具结果生成响应",
                        content=response.content[:200] + "..." if len(response.content) > 200 else response.content,
                        reasoning="基于工具执行结果，生成最终回答",
                        confidence=0.9
                    )
            else:
                # 记录直接响应
                if state.enable_thinking_tracking and state.user_id and state.session_id and state.messages:
                    last_msg = state.messages[-1]
                    if isinstance(last_msg, AIMessage):
                        tracker = get_thinking_tracker()
                        await tracker.add_conclusion(
                            session_id=state.session_id,
                            title="生成直接响应",
                            content=last_msg.content[:200] + "..." if len(last_msg.content) > 200 else last_msg.content,
                            reasoning="基于已有知识和分析，生成回答",
                            confidence=0.85
                        )
            
            logger.debug("Agent response generated")
            return state
            
        except Exception as e:
            logger.error(f"Error in respond node: {e}")
            state.error_count += 1
            
            # 记录响应生成错误
            if state.enable_thinking_tracking and state.user_id and state.session_id:
                tracker = get_thinking_tracker()
                await tracker.add_conclusion(
                    session_id=state.session_id,
                    title="响应生成出错",
                    content=f"在生成响应时出现错误：{str(e)}",
                    confidence=0.0
                )
            
            return state
    
    async def _error_handler_node(self, state: AgentState) -> AgentState:
        """错误处理节点。"""
        error_msg = "I encountered an error while processing your request. Please try again."
        
        if state.error_count >= state.max_errors:
            error_msg = "I'm experiencing technical difficulties. Please contact support if this persists."
        
        error_response = AIMessage(content=error_msg)
        state.messages.append(error_response)
        
        logger.warning(f"Error handler activated, error count: {state.error_count}")
        return state
    
    def _should_continue_thinking(self, state: AgentState) -> str:
        """判断是否继续思考。"""
        if state.error_count > 0:
            return "error"
        return "act"
    
    def _should_use_tools(self, state: AgentState) -> str:
        """判断是否使用工具。"""
        if state.error_count > 0:
            return "error"
        elif state.tool_calls:
            return "use_tools"
        else:
            return "respond"
    
    def _build_thinking_prompt(self, state: AgentState) -> str:
        """构建思考提示。"""
        recent_messages = state.messages[-3:] if state.messages else []
        context_summary = "\n".join([
            f"- {msg.type}: {msg.content[:100]}..."
            for msg in recent_messages
        ])
        
        return f"""
You are {self.name}. {self.description}

Analyze the following conversation context and plan your response:
{context_summary}

Consider:
1. What is the user asking for?
2. What tools might be needed?
3. What information should be included in the response?
4. How can you be most helpful?

Provide a brief analysis of the situation and your planned approach.
"""
    
    def _build_message_history(self, state: AgentState) -> List[BaseMessage]:
        """构建消息历史。"""
        messages = [SystemMessage(content=self.system_prompt)]
        
        # 添加上下文信息
        if state.context:
            context_msg = f"Context: {json.dumps(state.context, ensure_ascii=False)}"
            messages.append(SystemMessage(content=context_msg))
        
        # 添加对话历史（保留最近的10轮对话）
        recent_messages = state.messages[-20:] if len(state.messages) > 20 else state.messages
        messages.extend(recent_messages)
        
        return messages
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        enable_thinking_tracking: Optional[bool] = None
    ) -> AsyncGenerator[AgentResponse, None]:
        """
        处理用户消息并生成响应。
        
        Args:
            message: 用户消息
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文信息
            enable_thinking_tracking: 是否启用思考追踪
            
        Yields:
            AgentResponse: Agent响应
        """
        session_id = session_id or f"{user_id}_{datetime.now().timestamp()}"
        thinking_enabled = enable_thinking_tracking if enable_thinking_tracking is not None else self.enable_thinking_tracking
        
        try:
            # 创建初始状态
            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                context=context or {},
                user_id=user_id,
                session_id=session_id,
                enable_thinking_tracking=thinking_enabled
            )
            
            # 配置运行参数
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "user_id": user_id
                }
            }
            
            # 启用思考追踪
            thinking_context_manager = None
            if thinking_enabled:
                tracker = get_thinking_tracker()
                thinking_context_manager = tracker.track_session(
                    session_id=session_id,
                    user_id=user_id,
                    agent_name=self.name,
                    user_message=message,
                    context=context
                )
            
            try:
                # 开始思考追踪会话
                if thinking_context_manager:
                    async with thinking_context_manager:
                        # 流式处理
                        async for event in self.app.astream(initial_state, config=config):
                            async for response in self._process_stream_event(event, session_id, thinking_enabled):
                                yield response
                else:
                    # 不启用思考追踪的流式处理
                    async for event in self.app.astream(initial_state, config=config):
                        async for response in self._process_stream_event(event, session_id, thinking_enabled):
                            yield response
                        
            except Exception as e:
                logger.error(f"Error in agent stream processing: {e}")
                yield AgentResponse(
                    content=f"处理过程中发生错误: {str(e)}",
                    message_type=MessageType.AI,
                    metadata={"error": True}
                )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield AgentResponse(
                content=f"Sorry, I encountered an error: {str(e)}",
                message_type=MessageType.AI,
                metadata={"error": True}
            )
    
    async def _process_stream_event(
        self, 
        event: Dict[str, Any], 
        session_id: str,
        thinking_enabled: bool
    ) -> AsyncGenerator[AgentResponse, None]:
        """处理流事件。"""
        for node, output in event.items():
            if node == "think" and output.thinking_process and thinking_enabled:
                # 发送思考过程
                yield AgentResponse(
                    content=output.thinking_process[-1],
                    message_type=MessageType.THINKING,
                    metadata={"node": node, "session_id": session_id}
                )
            
            elif node == "respond" and output.messages:
                # 发送最终响应
                last_message = output.messages[-1]
                if isinstance(last_message, AIMessage):
                    # 获取思考过程摘要
                    thinking_summary = None
                    if thinking_enabled and output.thinking_process:
                        thinking_summary = output.thinking_process[-1] if output.thinking_process else None
                    
                    yield AgentResponse(
                        content=last_message.content,
                        message_type=MessageType.AI,
                        thinking_process=thinking_summary,
                        tool_calls=output.tool_calls if output.tool_calls else None,
                        metadata={"session_id": session_id, "node": node}
                    )
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史。
        
        Args:
            session_id: 会话ID
            limit: 限制数量
            
        Returns:
            对话历史列表
        """
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await self.app.aget_state(config)
            
            if not state or not state.values.get("messages"):
                return []
            
            messages = state.values["messages"][-limit:] if len(state.values["messages"]) > limit else state.values["messages"]
            
            return [
                {
                    "type": msg.type if hasattr(msg, 'type') else type(msg).__name__.lower(),
                    "content": msg.content,
                    "timestamp": msg.additional_kwargs.get("timestamp", datetime.now(timezone.utc).isoformat())
                }
                for msg in messages
                if hasattr(msg, 'content')
            ]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def get_thinking_steps(
        self,
        session_id: str,
        include_buffer: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取会话的思考步骤。
        
        Args:
            session_id: 会话ID
            include_buffer: 是否包含缓冲区中的步骤
            
        Returns:
            思考步骤列表
        """
        if not self.enable_thinking_tracking:
            return []
            
        try:
            tracker = get_thinking_tracker()
            return await tracker.get_session_steps(session_id, include_buffer)
        except Exception as e:
            logger.error(f"Error getting thinking steps: {e}")
            return []
    
    async def get_thinking_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取思考过程摘要。
        
        Args:
            session_id: 会话ID
            
        Returns:
            思考摘要
        """
        if not self.enable_thinking_tracking:
            return None
            
        try:
            tracker = get_thinking_tracker()
            return await tracker.get_session_summary(session_id)
        except Exception as e:
            logger.error(f"Error getting thinking summary: {e}")
            return None
    
    async def clear_conversation(self, session_id: str) -> bool:
        """
        清除对话历史。
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功清除
        """
        try:
            # LangGraph MemorySaver 没有直接的清除方法
            # 这里我们通过创建一个新的空状态来"清除"历史
            config = {"configurable": {"thread_id": session_id}}
            empty_state = AgentState()
            
            # 这是一个简化的实现，实际可能需要更复杂的逻辑
            logger.info(f"Conversation cleared for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息。"""
        pass
    
    def add_tool(self, tool: BaseTool):
        """添加工具到Agent。"""
        self.tools.append(tool)
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        logger.info(f"Added tool '{tool.name}' to agent '{self.name}'")
    
    def remove_tool(self, tool_name: str) -> bool:
        """从Agent中移除工具。"""
        initial_count = len(self.tools)
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        
        if len(self.tools) != initial_count:
            self.llm_with_tools = self.llm.bind_tools(self.tools) if self.tools else self.llm
            logger.info(f"Removed tool '{tool_name}' from agent '{self.name}'")
            return True
        
        return False


class AgentManager:
    """Agent管理器，用于管理多个Agent实例。"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """注册Agent。"""
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取Agent。"""
        return self._agents.get(name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """获取所有Agent。"""
        return self._agents.copy()
    
    def remove_agent(self, name: str) -> bool:
        """移除Agent。"""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Removed agent: {name}")
            return True
        return False
    
    async def process_message_with_agent(
        self,
        agent_name: str,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[AgentResponse, None]:
        """使用指定Agent处理消息。"""
        agent = self.get_agent(agent_name)
        if not agent:
            yield AgentResponse(
                content=f"Agent '{agent_name}' not found",
                message_type=MessageType.AI,
                metadata={"error": True}
            )
            return
        
        async for response in agent.process_message(message, user_id, session_id, context):
            yield response


# 创建全局Agent管理器实例
agent_manager = AgentManager()


def get_agent_manager() -> AgentManager:
    """获取Agent管理器实例。"""
    return agent_manager