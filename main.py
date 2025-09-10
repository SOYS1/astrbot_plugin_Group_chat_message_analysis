"""
群聊消息关键词分析插件
根据指定关键词分析群聊中相关话题的讨论内容，并生成可视化报告
"""

import asyncio
from typing import Optional
from pathlib import Path
import sys

from astrbot.api.event import filter
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

# 动态添加当前目录到Python路径
plugin_dir = Path(__file__).parent
sys.path.insert(0, str(plugin_dir))

# 导入模块化组件
from src.core.message_handler import MessageHandler
from src.analysis.topic_analyzer import TopicAnalyzer
from src.visualization.report_generator import ReportGenerator


class GroupChatMessageAnalysis(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 初始化模块化组件
        self.message_handler = MessageHandler()
        self.topic_analyzer = TopicAnalyzer(config)
        self.report_generator = ReportGenerator()
        
        # 初始化HTML渲染器
        self.html_render = context.html_render
        
        logger.info("群聊消息关键词分析插件已初始化")

    @filter.command("分析")
    async def analyze_topic(self, event: AiocqhttpMessageEvent, keyword: str = "", days: int = 2):
        """
        根据关键词分析群聊消息内容
        用法: /分析 [关键词] [天数]
        """
        if not isinstance(event, AiocqhttpMessageEvent):
            yield event.plain_result("❌ 此功能仅支持QQ群聊")
            return

        group_id = event.get_group_id()
        if not group_id:
            yield event.plain_result("❌ 请在群聊中使用此命令")
            return

        if not keyword:
            yield event.plain_result("❌ 请提供要分析的关键词，例如: /分析 吃饭")
            return

        # 设置分析天数
        analysis_days = days if 1 <= days <= 7 else self.config.get("analysis_days", 2)

        yield event.plain_result(f"🔍 开始分析群聊中关于'{keyword}'的话题，请稍候...")

        try:
            # 获取群聊消息
            messages = await self.message_handler.fetch_group_messages(
                event.bot, group_id, analysis_days, keyword
            )
            
            if not messages:
                yield event.plain_result(f"❌ 未找到包含'{keyword}'的群聊记录")
                return

            yield event.plain_result(f"📊 已获取{len(messages)}条相关消息，正在进行智能分析...")

            # 进行话题分析
            analysis_result = await self.topic_analyzer.analyze_topic_messages(
                messages, keyword, group_id
            )

            # 生成图片报告
            image_url = await self.report_generator.generate_topic_analysis_image(
                analysis_result, keyword, group_id, self.html_render
            )
            
            if image_url:
                yield event.image_result(image_url)
            else:
                # 如果图片生成失败，回退到文本报告
                logger.warning("图片报告生成失败，回退到文本报告")
                text_report = self.report_generator.generate_text_report(analysis_result)
                yield event.plain_result(f"⚠️ 图片报告生成失败，以下是文本版本：\n\n{text_report}")

        except Exception as e:
            logger.error(f"话题分析失败: {e}", exc_info=True)
            yield event.plain_result(f"❌ 分析失败: {str(e)}")