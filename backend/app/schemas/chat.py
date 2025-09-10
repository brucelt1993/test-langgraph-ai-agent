"""
聊天相关的数据模式定义。
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举。"""
    USER = "user"
    ASSISTANT = "assistant" 
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    THINKING = "thinking"


class ChatSessionCreate(BaseModel):
    """创建聊天会话的请求模式。"""
    title: Optional[str] = Field(None, description="会话标题")
    agent_name: str = Field(..., description="使用的Agent名称")
    context: Optional[Dict[str, Any]] = Field(None, description="初始上下文")


class ChatSessionUpdate(BaseModel):
    """更新聊天会话的请求模式。"""
    title: Optional[str] = Field(None, description="会话标题")
    is_active: Optional[bool] = Field(None, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ChatSessionResponse(BaseModel):
    """聊天会话的响应模式。"""
    id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="会话标题")
    agent_name: str = Field(..., description="Agent名称")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    message_count: int = Field(0, description="消息数量")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """创建消息的请求模式。"""
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(MessageType.USER, description="消息类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class MessageUpdate(BaseModel):
    """更新消息的请求模式。"""
    content: Optional[str] = Field(None, description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class MessageResponse(BaseModel):
    """消息的响应模式。"""
    id: str = Field(..., description="消息ID")
    session_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="消息内容")
    message_type: MessageType = Field(..., description="消息类型")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")
    
    # 思考过程相关字段
    thinking_process: Optional[Dict[str, Any]] = Field(None, description="思考过程数据")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用信息")
    confidence_score: Optional[float] = Field(None, description="置信度评分")

    class Config:
        from_attributes = True
        
    @validator('message_type', pre=True)
    def validate_message_type(cls, v):
        """验证消息类型。"""
        if isinstance(v, DBMessageType):
            return v.value
        return v


class SendMessageRequest(BaseModel):
    """发送消息的请求模式。"""
    content: str = Field(..., min_length=1, max_length=10000, description="消息内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="消息元数据")
    
    @validator('content')
    def validate_content(cls, v):
        """验证消息内容。"""
        if not v.strip():
            raise ValueError("消息内容不能为空")
        return v.strip()


class StreamingResponse(BaseModel):
    """流式响应的数据模式。"""
    type: str = Field(..., description="响应类型")
    content: Optional[str] = Field(None, description="响应内容")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")
    timestamp: datetime = Field(..., description="时间戳")
    
    # 思考过程相关字段
    thinking_step: Optional[Dict[str, Any]] = Field(None, description="思考步骤")
    tool_call: Optional[Dict[str, Any]] = Field(None, description="工具调用")
    
    # 流式控制字段
    is_partial: bool = Field(False, description="是否为部分内容")
    sequence_id: Optional[int] = Field(None, description="序列ID")


class ChatSessionListResponse(BaseModel):
    """聊天会话列表的响应模式。"""
    sessions: List[ChatSessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="页大小")
    pages: int = Field(..., description="总页数")


class ChatSessionStatsResponse(BaseModel):
    """聊天会话统计信息的响应模式。"""
    session_id: str = Field(..., description="会话ID")
    message_count: int = Field(..., description="消息总数")
    user_message_count: int = Field(..., description="用户消息数")
    assistant_message_count: int = Field(..., description="AI消息数")
    thinking_step_count: int = Field(..., description="思考步骤数")
    tool_call_count: int = Field(..., description="工具调用数")
    average_response_time: Optional[float] = Field(None, description="平均响应时间(秒)")
    total_conversation_time: Optional[float] = Field(None, description="总对话时间(秒)")
    first_message_at: Optional[datetime] = Field(None, description="首次消息时间")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    context_rounds: int = Field(..., description="上下文轮数")


class ThinkingStepResponse(BaseModel):
    """思考步骤的响应模式。"""
    id: str = Field(..., description="步骤ID")
    session_id: str = Field(..., description="思考会话ID")
    step_number: int = Field(..., description="步骤序号")
    phase: str = Field(..., description="思考阶段")
    step_type: str = Field(..., description="步骤类型")
    title: str = Field(..., description="步骤标题")
    content: str = Field(..., description="思考内容")
    reasoning: Optional[str] = Field(None, description="推理过程")
    confidence: Optional[float] = Field(None, description="置信度")
    importance: Optional[float] = Field(None, description="重要性")
    duration: Optional[float] = Field(None, description="持续时间")
    is_successful: bool = Field(..., description="是否成功")
    tool_name: Optional[str] = Field(None, description="工具名称")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="工具输入")
    tool_output: Optional[str] = Field(None, description="工具输出")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ContextMessage(BaseModel):
    """上下文消息模式。"""
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")
    timestamp: datetime = Field(..., description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationContextResponse(BaseModel):
    """对话上下文响应模式。"""
    session_id: str = Field(..., description="会话ID")
    context_messages: List[ContextMessage] = Field(..., description="上下文消息列表")
    context_rounds: int = Field(..., description="上下文轮数")
    max_rounds: int = Field(..., description="最大上下文轮数")
    timestamp: datetime = Field(..., description="获取时间戳")


class AgentCapability(BaseModel):
    """Agent能力描述模式。"""
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    tools: List[str] = Field(default_factory=list, description="支持的工具")


class AgentInfo(BaseModel):
    """Agent信息模式。"""
    name: str = Field(..., description="Agent名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="Agent描述")
    capabilities: List[AgentCapability] = Field(..., description="Agent能力列表")
    is_available: bool = Field(True, description="是否可用")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class AvailableAgentsResponse(BaseModel):
    """可用Agent列表响应模式。"""
    agents: List[AgentInfo] = Field(..., description="Agent列表")
    default_agent: str = Field(..., description="默认Agent名称")
    total: int = Field(..., description="总数")


class ChatHealthResponse(BaseModel):
    """聊天服务健康状态响应模式。"""
    service_status: str = Field(..., description="服务状态")
    agent_status: Dict[str, str] = Field(..., description="Agent状态")
    database_status: str = Field(..., description="数据库状态")
    active_sessions: int = Field(..., description="活跃会话数")
    total_messages_today: int = Field(..., description="今日消息总数")
    timestamp: datetime = Field(..., description="检查时间戳")