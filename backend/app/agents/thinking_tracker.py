"""
AI思考过程追踪系统。

提供AI思考过程的捕获、结构化存储和分析功能。
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from datetime import datetime, timezone, timedelta
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from app.models.thinking_step import (
    ThinkingSession, ThinkingStep, ThinkingInsight,
    ThinkingPhase, ThinkingStepType
)
from app.repositories.factory import get_repository_factory

logger = logging.getLogger(__name__)


@dataclass
class ThinkingContext:
    """思考上下文数据结构。"""
    session_id: str
    user_id: str
    agent_name: str
    user_message: str
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ThinkingStepData:
    """思考步骤数据结构。"""
    title: str
    content: str
    phase: ThinkingPhase
    step_type: ThinkingStepType
    reasoning: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    confidence: Optional[float] = None
    importance: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ThinkingTracker:
    """
    AI思考过程追踪器。
    
    负责捕获、记录和管理AI的思考过程。
    """
    
    def __init__(self):
        self._active_sessions: Dict[str, ThinkingContext] = {}
        self._step_buffers: Dict[str, List[ThinkingStepData]] = {}
    
    @asynccontextmanager
    async def track_session(
        self,
        session_id: str,
        user_id: str,
        agent_name: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        追踪一个完整的思考会话。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            agent_name: Agent名称
            user_message: 用户消息
            context: 上下文信息
        """
        thinking_context = ThinkingContext(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            user_message=user_message,
            context=context or {}
        )
        
        # 初始化会话
        self._active_sessions[session_id] = thinking_context
        self._step_buffers[session_id] = []
        
        try:
            # 创建数据库记录
            await self._create_thinking_session(thinking_context)
            
            logger.info(f"Started thinking session: {session_id}")
            yield self
            
        finally:
            # 完成会话
            await self._finalize_thinking_session(session_id)
            
            # 清理
            self._active_sessions.pop(session_id, None)
            self._step_buffers.pop(session_id, None)
            
            logger.info(f"Finalized thinking session: {session_id}")
    
    async def add_thinking_step(
        self,
        session_id: str,
        step_data: ThinkingStepData,
        auto_flush: bool = False
    ):
        """
        添加思考步骤。
        
        Args:
            session_id: 会话ID
            step_data: 步骤数据
            auto_flush: 是否自动刷新到数据库
        """
        if session_id not in self._active_sessions:
            logger.warning(f"No active thinking session for ID: {session_id}")
            return
        
        # 添加到缓冲区
        self._step_buffers[session_id].append(step_data)
        
        logger.debug(f"Added thinking step to session {session_id}: {step_data.title}")
        
        # 自动刷新到数据库
        if auto_flush:
            await self._flush_steps(session_id)
    
    async def add_observation(
        self,
        session_id: str,
        title: str,
        content: str,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加观察步骤。"""
        step_data = ThinkingStepData(
            title=title,
            content=content,
            phase=ThinkingPhase.ANALYSIS,
            step_type=ThinkingStepType.OBSERVATION,
            confidence=confidence,
            metadata=metadata or {}
        )
        await self.add_thinking_step(session_id, step_data)
    
    async def add_analysis(
        self,
        session_id: str,
        title: str,
        content: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加分析步骤。"""
        step_data = ThinkingStepData(
            title=title,
            content=content,
            phase=ThinkingPhase.ANALYSIS,
            step_type=ThinkingStepType.ANALYSIS,
            reasoning=reasoning,
            confidence=confidence,
            metadata=metadata or {}
        )
        await self.add_thinking_step(session_id, step_data)
    
    async def add_decision(
        self,
        session_id: str,
        title: str,
        content: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        importance: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加决策步骤。"""
        step_data = ThinkingStepData(
            title=title,
            content=content,
            phase=ThinkingPhase.PLANNING,
            step_type=ThinkingStepType.DECISION,
            reasoning=reasoning,
            confidence=confidence,
            importance=importance,
            metadata=metadata or {}
        )
        await self.add_thinking_step(session_id, step_data)
    
    async def add_tool_call(
        self,
        session_id: str,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Optional[str] = None,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加工具调用步骤。"""
        step_data = ThinkingStepData(
            title=f"调用工具: {tool_name}",
            content=f"使用工具 {tool_name} 处理: {json.dumps(tool_input, ensure_ascii=False)}",
            phase=ThinkingPhase.EXECUTION,
            step_type=ThinkingStepType.TOOL_CALL,
            reasoning=reasoning,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            confidence=confidence,
            metadata=metadata or {}
        )
        await self.add_thinking_step(session_id, step_data)
    
    async def add_conclusion(
        self,
        session_id: str,
        title: str,
        content: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加结论步骤。"""
        step_data = ThinkingStepData(
            title=title,
            content=content,
            phase=ThinkingPhase.RESPONSE_GENERATION,
            step_type=ThinkingStepType.CONCLUSION,
            reasoning=reasoning,
            confidence=confidence,
            metadata=metadata or {}
        )
        await self.add_thinking_step(session_id, step_data)
    
    async def get_session_steps(
        self,
        session_id: str,
        include_buffer: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取会话的所有思考步骤。
        
        Args:
            session_id: 会话ID
            include_buffer: 是否包含缓冲区中的步骤
            
        Returns:
            思考步骤列表
        """
        try:
            async with get_repository_factory() as repo_factory:
                # 从数据库获取已保存的步骤
                session = repo_factory.session
                steps = await session.query(ThinkingStep)\
                    .filter(ThinkingStep.session_id == session_id)\
                    .order_by(ThinkingStep.step_number)\
                    .all()
                
                step_list = [
                    {
                        "id": step.id,
                        "step_number": step.step_number,
                        "phase": step.phase,
                        "step_type": step.step_type,
                        "title": step.title,
                        "content": step.content,
                        "reasoning": step.reasoning,
                        "tool_name": step.tool_name,
                        "tool_input": step.tool_input,
                        "tool_output": step.tool_output,
                        "confidence": step.confidence,
                        "importance": step.importance,
                        "duration": step.duration,
                        "is_successful": step.is_successful,
                        "error_message": step.error_message,
                        "metadata": step.metadata,
                        "created_at": step.created_at
                    }
                    for step in steps
                ]
                
                # 添加缓冲区中的步骤
                if include_buffer and session_id in self._step_buffers:
                    buffer_steps = self._step_buffers[session_id]
                    start_number = len(step_list) + 1
                    
                    for i, step_data in enumerate(buffer_steps):
                        step_list.append({
                            "id": f"buffer_{i}",
                            "step_number": start_number + i,
                            "phase": step_data.phase,
                            "step_type": step_data.step_type,
                            "title": step_data.title,
                            "content": step_data.content,
                            "reasoning": step_data.reasoning,
                            "tool_name": step_data.tool_name,
                            "tool_input": step_data.tool_input,
                            "tool_output": step_data.tool_output,
                            "confidence": step_data.confidence,
                            "importance": step_data.importance,
                            "duration": None,
                            "is_successful": True,
                            "error_message": None,
                            "metadata": step_data.metadata,
                            "created_at": datetime.now(timezone.utc),
                            "from_buffer": True
                        })
                
                return step_list
                
        except Exception as e:
            logger.error(f"Error getting session steps: {e}")
            return []
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要。
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要
        """
        try:
            async with get_repository_factory() as repo_factory:
                session = repo_factory.session
                thinking_session = await session.query(ThinkingSession)\
                    .filter(ThinkingSession.session_id == session_id)\
                    .first()
                
                if not thinking_session:
                    return None
                
                # 获取步骤统计
                steps = await self.get_session_steps(session_id, include_buffer=True)
                
                phase_counts = {}
                step_type_counts = {}
                total_confidence = 0
                confidence_count = 0
                
                for step in steps:
                    phase = step["phase"]
                    step_type = step["step_type"]
                    
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
                    step_type_counts[step_type] = step_type_counts.get(step_type, 0) + 1
                    
                    if step["confidence"] is not None:
                        total_confidence += step["confidence"]
                        confidence_count += 1
                
                avg_confidence = total_confidence / confidence_count if confidence_count > 0 else None
                
                return {
                    "session_id": thinking_session.session_id,
                    "user_id": thinking_session.user_id,
                    "agent_name": thinking_session.agent_name,
                    "user_message": thinking_session.user_message,
                    "final_response": thinking_session.final_response,
                    "total_steps": len(steps),
                    "total_thinking_time": thinking_session.total_thinking_time,
                    "tool_calls_count": thinking_session.tool_calls_count,
                    "average_confidence": avg_confidence,
                    "phase_distribution": phase_counts,
                    "step_type_distribution": step_type_counts,
                    "created_at": thinking_session.created_at,
                    "updated_at": thinking_session.updated_at
                }
                
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return None
    
    async def _create_thinking_session(self, thinking_context: ThinkingContext):
        """创建思考会话记录。"""
        try:
            async with get_repository_factory() as repo_factory:
                session = repo_factory.session
                
                thinking_session = ThinkingSession(
                    user_id=thinking_context.user_id,
                    session_id=thinking_context.session_id,
                    agent_name=thinking_context.agent_name,
                    user_message=thinking_context.user_message,
                    context=thinking_context.context
                )
                
                session.add(thinking_session)
                await repo_factory.commit()
                
        except Exception as e:
            logger.error(f"Error creating thinking session: {e}")
    
    async def _flush_steps(self, session_id: str):
        """将缓冲区中的步骤刷新到数据库。"""
        if session_id not in self._step_buffers or not self._step_buffers[session_id]:
            return
        
        try:
            async with get_repository_factory() as repo_factory:
                session = repo_factory.session
                
                # 获取当前步骤数量
                current_count = await session.query(ThinkingStep)\
                    .filter(ThinkingStep.session_id == session_id)\
                    .count()
                
                # 保存缓冲区中的步骤
                for i, step_data in enumerate(self._step_buffers[session_id]):
                    thinking_step = ThinkingStep(
                        session_id=session_id,
                        step_number=current_count + i + 1,
                        phase=step_data.phase,
                        step_type=step_data.step_type,
                        title=step_data.title,
                        content=step_data.content,
                        reasoning=step_data.reasoning,
                        tool_name=step_data.tool_name,
                        tool_input=step_data.tool_input,
                        tool_output=step_data.tool_output,
                        confidence=step_data.confidence,
                        importance=step_data.importance,
                        metadata=step_data.metadata
                    )
                    
                    session.add(thinking_step)
                
                await repo_factory.commit()
                
                # 清空缓冲区
                self._step_buffers[session_id] = []
                
        except Exception as e:
            logger.error(f"Error flushing thinking steps: {e}")
    
    async def _finalize_thinking_session(self, session_id: str):
        """完成思考会话。"""
        try:
            # 刷新剩余步骤
            await self._flush_steps(session_id)
            
            # 更新会话统计信息
            async with get_repository_factory() as repo_factory:
                session = repo_factory.session
                
                thinking_session = await session.query(ThinkingSession)\
                    .filter(ThinkingSession.session_id == session_id)\
                    .first()
                
                if thinking_session:
                    # 计算统计信息
                    steps_count = await session.query(ThinkingStep)\
                        .filter(ThinkingStep.session_id == session_id)\
                        .count()
                    
                    tool_calls_count = await session.query(ThinkingStep)\
                        .filter(
                            ThinkingStep.session_id == session_id,
                            ThinkingStep.step_type == ThinkingStepType.TOOL_CALL
                        )\
                        .count()
                    
                    # 计算总思考时间
                    total_time = (datetime.now(timezone.utc) - thinking_session.created_at).total_seconds()
                    
                    # 更新会话
                    thinking_session.total_steps = steps_count
                    thinking_session.tool_calls_count = tool_calls_count
                    thinking_session.total_thinking_time = total_time
                    thinking_session.updated_at = datetime.now(timezone.utc)
                    
                    await repo_factory.commit()
                
        except Exception as e:
            logger.error(f"Error finalizing thinking session: {e}")


class ThinkingAnalyzer:
    """思考过程分析器。"""
    
    async def analyze_thinking_patterns(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        分析用户的思考模式。
        
        Args:
            user_id: 用户ID
            days: 分析天数
            
        Returns:
            分析结果
        """
        try:
            async with get_repository_factory() as repo_factory:
                session = repo_factory.session
                
                # 获取最近的思考会话
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                thinking_sessions = await session.query(ThinkingSession)\
                    .filter(
                        ThinkingSession.user_id == user_id,
                        ThinkingSession.created_at >= cutoff_date
                    )\
                    .all()
                
                if not thinking_sessions:
                    return {"message": "No thinking sessions found"}
                
                # 分析统计
                total_sessions = len(thinking_sessions)
                total_steps = sum(s.total_steps for s in thinking_sessions)
                total_tool_calls = sum(s.tool_calls_count for s in thinking_sessions)
                
                avg_steps_per_session = total_steps / total_sessions if total_sessions > 0 else 0
                avg_thinking_time = sum(
                    s.total_thinking_time for s in thinking_sessions if s.total_thinking_time
                ) / total_sessions if total_sessions > 0 else 0
                
                # 获取详细步骤统计
                step_types = {}
                phases = {}
                
                for thinking_session in thinking_sessions:
                    steps = await session.query(ThinkingStep)\
                        .filter(ThinkingStep.session_id == thinking_session.id)\
                        .all()
                    
                    for step in steps:
                        step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
                        phases[step.phase] = phases.get(step.phase, 0) + 1
                
                return {
                    "user_id": user_id,
                    "analysis_period_days": days,
                    "total_sessions": total_sessions,
                    "total_steps": total_steps,
                    "total_tool_calls": total_tool_calls,
                    "average_steps_per_session": avg_steps_per_session,
                    "average_thinking_time_seconds": avg_thinking_time,
                    "step_type_distribution": step_types,
                    "phase_distribution": phases,
                    "most_common_step_type": max(step_types.items(), key=lambda x: x[1])[0] if step_types else None,
                    "most_common_phase": max(phases.items(), key=lambda x: x[1])[0] if phases else None
                }
                
        except Exception as e:
            logger.error(f"Error analyzing thinking patterns: {e}")
            return {"error": str(e)}


# 创建全局实例
thinking_tracker = ThinkingTracker()
thinking_analyzer = ThinkingAnalyzer()


def get_thinking_tracker() -> ThinkingTracker:
    """获取思考追踪器实例。"""
    return thinking_tracker


def get_thinking_analyzer() -> ThinkingAnalyzer:
    """获取思考分析器实例。"""
    return thinking_analyzer