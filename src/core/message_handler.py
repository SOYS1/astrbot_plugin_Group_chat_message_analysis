"""
消息处理模块
负责从QQ群获取历史消息
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from astrbot.api import logger


class MessageHandler:
    def __init__(self):
        pass

    async def fetch_group_messages(self, bot, group_id: str, days: int, keyword: str = "") -> List[Dict]:
        """
        获取群聊历史消息
        
        Args:
            bot: QQ机器人实例
            group_id: 群号
            days: 获取最近几天的消息
            keyword: 关键词过滤（可选）
            
        Returns:
            包含消息的列表
        """
        try:
            if not bot or not group_id:
                logger.error(f"群 {group_id} 无效的客户端或群组ID")
                return []

            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            messages = []
            message_seq = 0
            query_rounds = 0
            max_rounds = 10  # 最大查询轮数
            max_messages = 500  # 最大消息数
            consecutive_failures = 0
            max_failures = 3

            logger.info(f"开始获取群 {group_id} 近 {days} 天的消息记录")
            logger.info(f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            while len(messages) < max_messages and query_rounds < max_rounds:
                try:
                    payloads = {
                        "group_id": int(group_id),
                        "message_seq": message_seq,
                        "count": 100,  # 每次获取100条消息
                        "reverseOrder": True,
                    }
                    
                    result = await bot.api.call_action("get_group_msg_history", **payloads)
                    
                    if not result or "messages" not in result:
                        logger.warning(f"群 {group_id} API返回无效结果: {result}")
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            break
                        continue

                    round_messages = result.get("messages", [])
                    
                    if not round_messages:
                        logger.info(f"群 {group_id} 没有更多消息，结束获取")
                        break

                    # 重置失败计数
                    consecutive_failures = 0

                    # 过滤时间范围内的消息
                    valid_messages_in_round = 0
                    oldest_msg_time = None

                    for msg in round_messages:
                        try:
                            msg_time = datetime.fromtimestamp(msg.get("time", 0))
                            oldest_msg_time = msg_time

                            # 过滤时间范围
                            if msg_time < start_time or msg_time > end_time:
                                continue

                            # 如果提供了关键词，过滤包含关键词的消息
                            if keyword:
                                # 检查消息是否包含文本并且包含关键词
                                msg_texts = [
                                    content.get("data", {}).get("text", "")
                                    for content in msg.get("message", [])
                                    if content.get("type") == "text"
                                ]
                                
                                # 如果有任何文本段包含关键词，则保留该消息
                                if not any(keyword in text for text in msg_texts if text):
                                    continue

                            messages.append(msg)
                            valid_messages_in_round += 1
                        except Exception as msg_error:
                            logger.warning(f"群 {group_id} 处理单条消息失败: {msg_error}")
                            continue

                    # 如果最老的消息时间已经超出范围，停止获取
                    if oldest_msg_time and oldest_msg_time < start_time:
                        logger.info(f"群 {group_id} 已获取到时间范围外的消息，停止获取。共获取 {len(messages)} 条消息")
                        break

                    if valid_messages_in_round == 0:
                        logger.warning(f"群 {group_id} 本轮未获取到有效消息")
                        break

                    message_seq = round_messages[0]["message_id"]
                    query_rounds += 1

                    # 添加延迟避免请求过快
                    if query_rounds % 5 == 0:
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"群 {group_id} 获取消息失败 (第{query_rounds+1}轮): {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        logger.error(f"群 {group_id} 连续失败 {max_failures} 次，停止获取")
                        break
                    await asyncio.sleep(1)

            logger.info(f"群 {group_id} 消息获取完成，共获取 {len(messages)} 条消息，查询轮数: {query_rounds}")
            return messages

        except Exception as e:
            logger.error(f"群 {group_id} 获取群聊消息记录失败: {e}", exc_info=True)
            return []