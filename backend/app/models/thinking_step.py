"""
AI思考过程相关的数据模型。

用于存储和管理AI的思考步骤、推理过程等信息。
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import enum

from app.core.database import Base


class ThinkingPhase(str, enum.Enum):
    """思考阶段枚举。"""
    ANALYSIS = "analysis"          # 分析阶段
    PLANNING = "planning"          # 规划阶段
    EXECUTION = "execution"        # 执行阶段
    REFLECTION = "reflection"      # 反思阶段
    TOOL_SELECTION = "tool_selection"  # 工具选择
    RESPONSE_GENERATION = "response_generation"  # 响应生成


class ThinkingStepType(str, enum.Enum):
    """思考步骤类型枚举。"""
    OBSERVATION = "observation"    # 观察
    ANALYSIS = "analysis"          # 分析
    HYPOTHESIS = "hypothesis"      # 假设
    DECISION = "decision"          # 决策
    ACTION_PLAN = "action_plan"    # 行动计划
    TOOL_CALL = "tool_call"        # 工具调用
    EVALUATION = "evaluation"      # 评估
    CONCLUSION = "conclusion"      # 结论


class ThinkingSession(Base):
    """
    思考会话模型。
    
    代表一次完整的AI思考过程会话。
    """
    __tablename__ = "thinking_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # 输入信息
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 思考结果
    final_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_thinking_time: Mapped[Optional[float]] = mapped_column(nullable=True)  # 秒
    
    # 元数据
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 统计信息
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="thinking_sessions")
    thinking_steps: Mapped[List["ThinkingStep"]] = relationship("ThinkingStep", back_populates="session", cascade="all, delete-orphan")


class ThinkingStep(Base):
    """
    思考步骤模型。
    
    代表AI思考过程中的单个步骤。
    """
    __tablename__ = "thinking_steps"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("thinking_sessions.id"), nullable=False)
    
    # 步骤信息
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[ThinkingPhase] = mapped_column(String(50), nullable=False)
    step_type: Mapped[ThinkingStepType] = mapped_column(String(50), nullable=False)
    
    # 思考内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 工具相关
    tool_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tool_input: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 置信度和重要性
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0-1
    importance: Mapped[Optional[float]] = mapped_column(nullable=True)  # 0-1
    
    # 时间信息
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(nullable=True)  # 秒
    
    # 状态
    is_successful: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 元数据
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # 关系
    session: Mapped["ThinkingSession"] = relationship("ThinkingSession", back_populates="thinking_steps")


class ThinkingInsight(Base):
    """
    思考洞察模型。
    
    存储从思考过程中提取的洞察和模式。
    """
    __tablename__ = "thinking_insights"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 基本信息
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("thinking_sessions.id"), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pattern, improvement, error, etc.
    
    # 洞察内容
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 评分
    relevance_score: Mapped[float] = mapped_column(default=0.5)  # 0-1
    actionability_score: Mapped[float] = mapped_column(default=0.5)  # 0-1
    
    # 元数据
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    extracted_by: Mapped[str] = mapped_column(String(50), default="system")
    
    # 额外数据
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 关系
    session: Mapped["ThinkingSession"] = relationship("ThinkingSession")


# 更新User模型以添加思考会话关系
def add_thinking_sessions_to_user():
    """
    添加思考会话关系到User模型。
    这个函数应该在User模型定义后调用。
    """
    from app.models.user import User
    
    # 添加关系（如果尚未存在）
    if not hasattr(User, 'thinking_sessions'):
        User.thinking_sessions = relationship("ThinkingSession", back_populates="user", cascade="all, delete-orphan")