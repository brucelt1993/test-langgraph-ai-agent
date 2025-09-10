"""
AI Agent模块。

提供基于LangGraph的AI Agent系统，包括：
- 基础Agent框架
- 天气查询Agent
- 工具系统
- Agent管理器
"""

from app.agents.base_agent import BaseAgent, AgentManager, agent_manager, AgentResponse, MessageType
from app.agents.weather_agent import WeatherAgent, WeatherAssistantService, weather_service
from app.agents.tools.weather_tool import WeatherTool, MockWeatherTool

__all__ = [
    "BaseAgent",
    "AgentManager", 
    "agent_manager",
    "AgentResponse",
    "MessageType",
    "WeatherAgent",
    "WeatherAssistantService", 
    "weather_service",
    "WeatherTool",
    "MockWeatherTool"
]

# 注册默认的天气Agent到管理器
weather_agent_instance = WeatherAgent()
agent_manager.register_agent(weather_agent_instance)