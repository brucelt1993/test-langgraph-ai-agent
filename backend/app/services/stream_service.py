"""
SSE流式响应服务。

提供Server-Sent Events流式数据传输、连接管理和错误恢复机制。
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, AsyncGenerator, Optional, Set, Callable, Union, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import weakref
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class StreamEventType(str, Enum):
    """流式事件类型枚举。"""
    MESSAGE = "message"
    THINKING = "thinking"  
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    CONNECTION_STATUS = "connection_status"
    STREAM_START = "stream_start"
    STREAM_END = "stream_end"
    CHUNK = "chunk"


class ConnectionStatus(str, Enum):
    """连接状态枚举。"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class StreamMessage:
    """流式消息数据类。"""
    event_type: StreamEventType
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence: Optional[int] = None
    
    def to_sse_format(self) -> str:
        """转换为SSE格式。"""
        lines = []
        
        # 添加事件ID
        if self.id:
            lines.append(f"id: {self.id}")
            
        # 添加重试间隔
        if self.retry:
            lines.append(f"retry: {self.retry}")
            
        # 添加事件类型
        lines.append(f"event: {self.event_type.value}")
        
        # 添加数据
        data_dict = {
            **self.data,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence
        }
        data_json = json.dumps(data_dict, ensure_ascii=False, default=str)
        lines.append(f"data: {data_json}")
        
        # SSE格式要求以两个换行符结束
        return "\n".join(lines) + "\n\n"


@dataclass  
class StreamConnection:
    """流式连接数据类。"""
    connection_id: str
    user_id: str
    session_id: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def next_sequence(self) -> int:
        """获取下一个序列号。"""
        self.sequence_number += 1
        return self.sequence_number


class StreamService:
    """
    SSE流式响应服务。
    
    提供连接管理、消息传输、错误恢复等功能。
    """
    
    def __init__(self):
        self.connections: Dict[str, StreamConnection] = {}
        self.connection_queues: Dict[str, asyncio.Queue] = {}
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.connection_timeout = 300  # 连接超时（秒）
        self.max_queue_size = 1000  # 最大队列大小
        self.retry_interval = 1000  # 重试间隔（毫秒）
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """启动服务。"""
        if self._running:
            return
            
        self._running = True
        
        # 启动心跳任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("SSE流式响应服务已启动")
        
    async def stop(self):
        """停止服务。"""
        if not self._running:
            return
            
        self._running = False
        
        # 取消后台任务
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
                
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # 关闭所有连接
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
            
        logger.info("SSE流式响应服务已停止")
        
    async def create_connection(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建新的流式连接。
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            metadata: 连接元数据
            
        Returns:
            连接ID
        """
        connection_id = str(uuid.uuid4())
        
        # 创建连接对象
        connection = StreamConnection(
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            status=ConnectionStatus.CONNECTING
        )
        
        # 创建消息队列
        queue = asyncio.Queue(maxsize=self.max_queue_size)
        
        # 存储连接
        self.connections[connection_id] = connection
        self.connection_queues[connection_id] = queue
        
        # 发送连接状态消息
        await self.send_message(
            connection_id,
            StreamMessage(
                event_type=StreamEventType.CONNECTION_STATUS,
                data={
                    "status": ConnectionStatus.CONNECTED.value,
                    "connection_id": connection_id,
                    "message": "连接建立成功"
                },
                id=connection_id
            )
        )
        
        # 更新连接状态
        connection.status = ConnectionStatus.CONNECTED
        
        logger.info(f"创建SSE连接: {connection_id} (用户: {user_id})")
        
        return connection_id
        
    async def disconnect(self, connection_id: str):
        """
        断开连接。
        
        Args:
            connection_id: 连接ID
        """
        if connection_id not in self.connections:
            return
            
        # 发送断开连接消息
        try:
            await self.send_message(
                connection_id,
                StreamMessage(
                    event_type=StreamEventType.CONNECTION_STATUS,
                    data={
                        "status": ConnectionStatus.DISCONNECTED.value,
                        "connection_id": connection_id,
                        "message": "连接已断开"
                    }
                )
            )
        except Exception:
            pass  # 忽略发送错误
            
        # 清理连接
        self.connections.pop(connection_id, None)
        queue = self.connection_queues.pop(connection_id, None)
        
        if queue:
            # 清空队列
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
        logger.info(f"断开SSE连接: {connection_id}")
        
    async def send_message(
        self,
        connection_id: str,
        message: StreamMessage
    ) -> bool:
        """
        发送消息到指定连接。
        
        Args:
            connection_id: 连接ID
            message: 流式消息
            
        Returns:
            是否发送成功
        """
        if connection_id not in self.connections:
            logger.warning(f"尝试向不存在的连接发送消息: {connection_id}")
            return False
            
        connection = self.connections[connection_id]
        queue = self.connection_queues.get(connection_id)
        
        if not queue:
            logger.warning(f"连接队列不存在: {connection_id}")
            return False
            
        try:
            # 设置序列号
            message.sequence = connection.next_sequence()
            
            # 尝试放入队列（非阻塞）
            queue.put_nowait(message)
            
            logger.debug(f"消息已发送到连接 {connection_id}: {message.event_type.value}")
            return True
            
        except asyncio.QueueFull:
            logger.error(f"连接 {connection_id} 队列已满，丢弃消息")
            
            # 发送错误消息
            error_message = StreamMessage(
                event_type=StreamEventType.ERROR,
                data={
                    "error": "队列满",
                    "message": "消息队列已满，部分消息可能丢失",
                    "connection_id": connection_id
                }
            )
            
            # 尝试发送错误消息（可能也会失败）
            try:
                queue.get_nowait()  # 移除一个消息为错误消息腾出空间
                queue.put_nowait(error_message)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"发送消息到连接 {connection_id} 时出错: {str(e)}")
            return False
            
    async def broadcast_message(
        self,
        message: StreamMessage,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        广播消息到匹配的连接。
        
        Args:
            message: 流式消息
            user_id: 目标用户ID（可选）
            session_id: 目标会话ID（可选）
        """
        target_connections = []
        
        for connection_id, connection in self.connections.items():
            # 检查用户ID匹配
            if user_id and connection.user_id != user_id:
                continue
                
            # 检查会话ID匹配
            if session_id and connection.session_id != session_id:
                continue
                
            target_connections.append(connection_id)
            
        # 并发发送消息
        tasks = [
            self.send_message(connection_id, message)
            for connection_id in target_connections
        ]
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.debug(f"广播消息成功发送到 {success_count}/{len(tasks)} 个连接")
            
    async def get_event_stream(
        self,
        connection_id: str
    ) -> AsyncGenerator[str, None]:
        """
        获取连接的事件流。
        
        Args:
            connection_id: 连接ID
            
        Yields:
            SSE格式的事件数据
        """
        if connection_id not in self.connections:
            logger.error(f"连接不存在: {connection_id}")
            return
            
        connection = self.connections[connection_id]
        queue = self.connection_queues[connection_id]
        
        logger.info(f"开始SSE事件流: {connection_id}")
        
        try:
            # 发送流开始事件
            start_message = StreamMessage(
                event_type=StreamEventType.STREAM_START,
                data={
                    "connection_id": connection_id,
                    "message": "事件流开始"
                },
                id=f"{connection_id}-start"
            )
            
            yield start_message.to_sse_format()
            
            # 持续发送队列中的消息
            while connection_id in self.connections:
                try:
                    # 等待消息（带超时）
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.heartbeat_interval
                    )
                    
                    # 更新最后心跳时间
                    connection.last_heartbeat = datetime.now(timezone.utc)
                    
                    # 发送消息
                    yield message.to_sse_format()
                    
                except asyncio.TimeoutError:
                    # 发送心跳
                    heartbeat_message = StreamMessage(
                        event_type=StreamEventType.HEARTBEAT,
                        data={
                            "connection_id": connection_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    
                    yield heartbeat_message.to_sse_format()
                    
                except Exception as e:
                    logger.error(f"获取队列消息时出错: {str(e)}")
                    
                    error_message = StreamMessage(
                        event_type=StreamEventType.ERROR,
                        data={
                            "error": "队列错误",
                            "message": str(e),
                            "connection_id": connection_id
                        }
                    )
                    
                    yield error_message.to_sse_format()
                    break
                    
        except Exception as e:
            logger.error(f"SSE事件流异常: {str(e)}")
            
            error_message = StreamMessage(
                event_type=StreamEventType.ERROR,
                data={
                    "error": "流异常",
                    "message": str(e),
                    "connection_id": connection_id
                }
            )
            
            yield error_message.to_sse_format()
            
        finally:
            # 发送流结束事件
            end_message = StreamMessage(
                event_type=StreamEventType.STREAM_END,
                data={
                    "connection_id": connection_id,
                    "message": "事件流结束"
                },
                id=f"{connection_id}-end"
            )
            
            yield end_message.to_sse_format()
            
            # 清理连接
            await self.disconnect(connection_id)
            
            logger.info(f"SSE事件流结束: {connection_id}")
            
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        获取连接信息。
        
        Args:
            connection_id: 连接ID
            
        Returns:
            连接信息字典
        """
        if connection_id not in self.connections:
            return None
            
        connection = self.connections[connection_id]
        queue = self.connection_queues.get(connection_id)
        
        return {
            "connection_id": connection.connection_id,
            "user_id": connection.user_id,
            "session_id": connection.session_id,
            "status": connection.status.value,
            "created_at": connection.created_at.isoformat(),
            "last_heartbeat": connection.last_heartbeat.isoformat(),
            "sequence_number": connection.sequence_number,
            "queue_size": queue.qsize() if queue else 0,
            "metadata": connection.metadata
        }
        
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """
        获取所有连接信息。
        
        Returns:
            连接信息列表
        """
        return [
            self.get_connection_info(connection_id)
            for connection_id in self.connections.keys()
        ]
        
    async def _heartbeat_loop(self):
        """心跳循环任务。"""
        while self._running:
            try:
                current_time = datetime.now(timezone.utc)
                
                for connection_id, connection in list(self.connections.items()):
                    # 检查连接超时
                    time_since_heartbeat = (current_time - connection.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.connection_timeout:
                        logger.info(f"连接超时，断开连接: {connection_id}")
                        await self.disconnect(connection_id)
                        
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"心跳循环出错: {str(e)}")
                await asyncio.sleep(5)  # 错误时短暂休眠
                
    async def _cleanup_loop(self):
        """清理循环任务。"""
        while self._running:
            try:
                # 每5分钟清理一次
                await asyncio.sleep(300)
                
                # 清理断开的连接
                disconnected_connections = [
                    connection_id
                    for connection_id, connection in self.connections.items()
                    if connection.status == ConnectionStatus.DISCONNECTED
                ]
                
                for connection_id in disconnected_connections:
                    await self.disconnect(connection_id)
                    
                logger.debug(f"清理了 {len(disconnected_connections)} 个断开的连接")
                
            except Exception as e:
                logger.error(f"清理循环出错: {str(e)}")


# 全局服务实例
_stream_service = None


async def get_stream_service() -> StreamService:
    """获取全局流式服务实例。"""
    global _stream_service
    
    if _stream_service is None:
        _stream_service = StreamService()
        await _stream_service.start()
        
    return _stream_service


@asynccontextmanager
async def stream_connection(
    user_id: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    流式连接上下文管理器。
    
    Args:
        user_id: 用户ID
        session_id: 会话ID
        metadata: 连接元数据
        
    Yields:
        连接ID
    """
    stream_service = await get_stream_service()
    connection_id = await stream_service.create_connection(
        user_id=user_id,
        session_id=session_id,
        metadata=metadata
    )
    
    try:
        yield connection_id
    finally:
        await stream_service.disconnect(connection_id)