"""
天气查询工具。

提供天气查询功能的工具实现。
"""

from typing import Optional, Dict, Any
import httpx
import asyncio
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class WeatherQueryInput(BaseModel):
    """天气查询输入参数。"""
    city: str = Field(description="要查询天气的城市名称")
    days: Optional[int] = Field(default=1, description="查询天数，默认1天")


class WeatherTool(BaseTool):
    """天气查询工具。"""
    
    name: str = "weather_query"
    description: str = "查询指定城市的天气信息"
    args_schema: type[BaseModel] = WeatherQueryInput
    api_key: Optional[str] = Field(default=None, description="天气API密钥")
    base_url: str = Field(default="http://wttr.in", description="天气API基础URL")
    
    def __init__(self, api_key: Optional[str] = None, **data):
        """
        初始化天气工具。
        
        Args:
            api_key: 天气API密钥（如果需要）
        """
        super().__init__(api_key=api_key, **data)
    
    async def _arun(self, city: str, days: int = 1) -> str:
        """
        异步查询天气信息。
        
        Args:
            city: 城市名称
            days: 查询天数
            
        Returns:
            天气信息字符串
        """
        try:
            # 构建请求URL
            # wttr.in 是一个免费的天气服务，支持中文城市名
            url = f"{self.base_url}/{city}"
            
            params = {
                "format": "j1",  # JSON格式
                "lang": "zh"     # 中文
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                return self._format_weather_response(data, city, days)
                
        except httpx.TimeoutException:
            logger.error(f"Weather query timeout for city: {city}")
            return f"抱歉，查询{city}的天气信息超时了，请稍后再试。"
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API error for city {city}: {e}")
            return f"抱歉，无法获取{city}的天气信息，请检查城市名称是否正确。"
            
        except Exception as e:
            logger.error(f"Unexpected error querying weather for {city}: {e}")
            return f"查询{city}的天气时发生了意外错误：{str(e)}"
    
    def _run(self, city: str, days: int = 1) -> str:
        """
        同步查询天气信息（通过异步实现）。
        
        Args:
            city: 城市名称
            days: 查询天数
            
        Returns:
            天气信息字符串
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(city, days))
    
    def _format_weather_response(self, data: Dict[str, Any], city: str, days: int) -> str:
        """
        格式化天气响应数据。
        
        Args:
            data: API返回的天气数据
            city: 城市名称  
            days: 查询天数
            
        Returns:
            格式化后的天气信息
        """
        try:
            current = data.get("current_condition", [{}])[0]
            weather_desc = current.get("lang_zh", [{}])
            if weather_desc:
                weather_desc = weather_desc[0].get("value", "未知")
            else:
                weather_desc = current.get("weatherDesc", [{}])[0].get("value", "未知")
            
            temp_c = current.get("temp_C", "未知")
            feels_like_c = current.get("FeelsLikeC", "未知")
            humidity = current.get("humidity", "未知")
            wind_speed = current.get("windspeedKmph", "未知")
            wind_dir = current.get("winddir16Point", "未知")
            
            result = f"🌤️ {city}当前天气：\n"
            result += f"天气状况：{weather_desc}\n"
            result += f"温度：{temp_c}°C（体感温度：{feels_like_c}°C）\n"
            result += f"湿度：{humidity}%\n"
            result += f"风速：{wind_speed} km/h，风向：{wind_dir}\n"
            
            # 如果有多天预报
            if days > 1 and "weather" in data:
                result += f"\n📅 {days}天天气预报：\n"
                for i, day_data in enumerate(data["weather"][:days]):
                    if i == 0:
                        continue  # 跳过今天（已显示当前天气）
                    
                    date = day_data.get("date", "未知")
                    max_temp = day_data.get("maxtempC", "未知")
                    min_temp = day_data.get("mintempC", "未知")
                    
                    hourly = day_data.get("hourly", [{}])
                    if hourly:
                        desc = hourly[0].get("lang_zh", [{}])
                        if desc:
                            desc = desc[0].get("value", "未知")
                        else:
                            desc = hourly[0].get("weatherDesc", [{}])[0].get("value", "未知")
                    else:
                        desc = "未知"
                    
                    result += f"{date}：{desc}，{min_temp}°C - {max_temp}°C\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return f"获取到了{city}的天气数据，但格式化时出现问题：{str(e)}"


class MockWeatherTool(BaseTool):
    """模拟天气查询工具（用于测试）。"""
    
    name: str = "weather_query" 
    description: str = "查询指定城市的天气信息（模拟数据）"
    args_schema: type[BaseModel] = WeatherQueryInput
    
    async def _arun(self, city: str, days: int = 1) -> str:
        """模拟异步天气查询。"""
        # 模拟网络延迟
        await asyncio.sleep(1)
        
        # 模拟天气数据
        mock_data = {
            "北京": {"temp": 15, "desc": "晴", "humidity": 45},
            "上海": {"temp": 20, "desc": "多云", "humidity": 60},
            "广州": {"temp": 25, "desc": "阴", "humidity": 75},
            "深圳": {"temp": 24, "desc": "小雨", "humidity": 80},
            "杭州": {"temp": 18, "desc": "晴", "humidity": 50},
        }
        
        weather = mock_data.get(city, {"temp": 22, "desc": "晴", "humidity": 55})
        
        result = f"🌤️ {city}当前天气（模拟数据）：\n"
        result += f"天气状况：{weather['desc']}\n"
        result += f"温度：{weather['temp']}°C\n" 
        result += f"湿度：{weather['humidity']}%\n"
        result += f"风速：5 km/h，风向：东南\n"
        
        if days > 1:
            result += f"\n📅 未来{days-1}天预报（模拟）：\n"
            for i in range(1, days):
                result += f"第{i+1}天：晴，{weather['temp']-2}°C - {weather['temp']+3}°C\n"
        
        return result
    
    def _run(self, city: str, days: int = 1) -> str:
        """同步版本。"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._arun(city, days))