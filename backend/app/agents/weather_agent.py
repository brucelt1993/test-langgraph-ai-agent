"""
天气查询AI Agent。

专门用于天气查询和相关对话的智能代理。
"""

from typing import Dict, Any, List, Optional
import logging

from app.agents.base_agent import BaseAgent
from app.agents.tools.weather_tool import WeatherTool, MockWeatherTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherAgent(BaseAgent):
    """
    天气查询AI Agent。
    
    专门处理天气相关的查询和对话，具备：
    - 天气信息查询
    - 天气趋势分析
    - 出行建议
    - 穿衣建议
    """
    
    def __init__(self, use_mock: bool = False):
        """
        初始化天气Agent。
        
        Args:
            use_mock: 是否使用模拟天气数据
        """
        
        # 系统提示词
        system_prompt = """你是一个专业的天气助手，名叫小天。你的主要职责是：

1. **天气查询**：准确查询用户指定城市的天气信息
2. **友好交流**：用温暖、友好的语气与用户交流
3. **实用建议**：根据天气情况提供穿衣、出行建议
4. **安全提醒**：在恶劣天气时提醒用户注意安全

**交流风格**：
- 语气亲切友好，使用中文交流
- 回答简洁明了，重点突出
- 主动提供实用的生活建议
- 适当使用表情符号让对话更生动

**能力范围**：
- 查询全球主要城市的天气信息
- 提供未来几天的天气预报
- 根据天气给出穿衣建议
- 根据天气给出出行建议
- 解答天气相关的问题

如果用户询问非天气相关的问题，请礼貌地引导用户回到天气相关话题。"""

        # 选择天气工具
        weather_tool = MockWeatherTool() if use_mock else WeatherTool()
        
        # 初始化基础Agent
        super().__init__(
            name="weather_agent",
            description="专业的天气查询助手，提供准确的天气信息和实用建议",
            system_prompt=system_prompt,
            tools=[weather_tool],
            model_name=settings.OPENAI_MODEL,
            temperature=0.7,
            max_tokens=1500
        )
        
        self.use_mock = use_mock
        logger.info(f"WeatherAgent initialized with {'mock' if use_mock else 'real'} weather data")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息。"""
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "capabilities": [
                "天气查询",
                "天气预报",
                "穿衣建议", 
                "出行建议",
                "天气趋势分析"
            ],
            "supported_cities": "全球主要城市",
            "languages": ["中文"],
            "tools": [tool.name for tool in self.tools],
            "use_mock_data": self.use_mock
        }
    
    def _build_thinking_prompt(self, state) -> str:
        """构建天气Agent专用的思考提示。"""
        recent_messages = state.messages[-3:] if state.messages else []
        context_summary = "\n".join([
            f"- {msg.type}: {msg.content[:100]}..."
            for msg in recent_messages
        ])
        
        return f"""
你是小天，一个专业而友好的天气助手。分析以下对话并规划你的响应：

对话上下文：
{context_summary}

思考要点：
1. 用户是否在询问天气信息？如果是，需要查询哪个城市？
2. 是否需要使用天气查询工具？
3. 除了天气信息，还能提供什么实用建议？
4. 如何让回答更加友好和有用？
5. 是否需要提醒用户任何安全注意事项？

记住：
- 保持友好亲切的语气
- 主动提供实用建议
- 如果不是天气相关问题，礼貌地引导回到天气话题
- 使用适当的表情符号
"""
    
    async def get_weather_for_city(self, city: str, days: int = 1) -> str:
        """
        直接获取城市天气信息。
        
        Args:
            city: 城市名称
            days: 查询天数
            
        Returns:
            天气信息字符串
        """
        try:
            weather_tool = self.tools[0]  # 第一个工具应该是天气工具
            result = await weather_tool._arun(city=city, days=days)
            return result
        except Exception as e:
            logger.error(f"Error getting weather for {city}: {e}")
            return f"抱歉，获取{city}的天气信息时出现错误。"
    
    def add_clothing_suggestion(self, weather_info: str, temperature: int) -> str:
        """
        根据天气添加穿衣建议。
        
        Args:
            weather_info: 原始天气信息
            temperature: 温度
            
        Returns:
            包含穿衣建议的完整信息
        """
        suggestions = []
        
        if temperature <= 0:
            suggestions.append("🧥 建议穿着厚羽绒服、毛衣和保暖内衣")
        elif temperature <= 10:
            suggestions.append("🧥 建议穿着外套、毛衣或厚卫衣")  
        elif temperature <= 20:
            suggestions.append("👕 建议穿着长袖衬衫或薄外套")
        elif temperature <= 30:
            suggestions.append("👕 建议穿着短袖或薄长袖")
        else:
            suggestions.append("🩱 建议穿着清爽的夏装，注意防晒")
        
        if suggestions:
            return weather_info + f"\n\n👔 穿衣建议：\n" + "\n".join(suggestions)
        
        return weather_info
    
    def add_activity_suggestion(self, weather_info: str, weather_desc: str) -> str:
        """
        根据天气添加活动建议。
        
        Args:
            weather_info: 原始天气信息
            weather_desc: 天气描述
            
        Returns:
            包含活动建议的完整信息
        """
        suggestions = []
        
        if "晴" in weather_desc:
            suggestions.append("☀️ 天气很好，适合户外活动和运动")
        elif "雨" in weather_desc:
            suggestions.append("☔ 出门记得带伞，注意路面湿滑")
            suggestions.append("🏠 适合在家读书或看电影")
        elif "雪" in weather_desc:
            suggestions.append("❄️ 路面可能结冰，出行要小心")
            suggestions.append("⛄ 可以和家人一起堆雪人")
        elif "风" in weather_desc:
            suggestions.append("💨 风力较大，注意保暖防风")
        elif "雾" in weather_desc or "霾" in weather_desc:
            suggestions.append("😷 能见度较低，出行注意安全")
        
        if suggestions:
            return weather_info + f"\n\n🎯 活动建议：\n" + "\n".join(suggestions)
        
        return weather_info


class WeatherAssistantService:
    """天气助手服务。"""
    
    def __init__(self, use_mock: bool = False):
        self.agent = WeatherAgent(use_mock=use_mock)
        self.use_mock = use_mock
    
    async def query_weather(
        self,
        city: str,
        days: int = 1,
        user_id: str = "default",
        include_suggestions: bool = True
    ) -> str:
        """
        查询天气信息。
        
        Args:
            city: 城市名称
            days: 查询天数
            user_id: 用户ID
            include_suggestions: 是否包含建议
            
        Returns:
            天气信息字符串
        """
        try:
            weather_info = await self.agent.get_weather_for_city(city, days)
            
            if include_suggestions and not self.use_mock:
                # 这里可以添加更智能的建议生成逻辑
                # 由于我们使用的是文本格式的天气信息，暂时保持原样
                pass
            
            return weather_info
            
        except Exception as e:
            logger.error(f"Error in weather query service: {e}")
            return f"抱歉，查询{city}的天气时出现了问题。"
    
    async def chat_with_weather_assistant(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        与天气助手对话。
        
        Args:
            message: 用户消息
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文信息
            
        Returns:
            异步生成器，产生Agent响应
        """
        async for response in self.agent.process_message(
            message=message,
            user_id=user_id,
            session_id=session_id,
            context=context
        ):
            yield response
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """获取Agent能力信息。"""
        return self.agent.get_agent_info()


# 创建全局天气助手服务实例
weather_service = WeatherAssistantService(use_mock=settings.DEBUG)


def get_weather_service() -> WeatherAssistantService:
    """获取天气助手服务实例。"""
    return weather_service