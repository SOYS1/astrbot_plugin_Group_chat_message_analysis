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
            keyword: 关键词过滤（支持语义相关匹配）
            
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

            # 关键词扩展
            keyword_variants = []
            if keyword:
                keyword_variants = self._expand_keyword_variants(keyword)
                logger.info(f"关键词 '{keyword}' 扩展为: {keyword_variants}")

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

                            # 如果提供了关键词，使用语义相关匹配
                            if keyword:
                                if not self._is_semantically_related(msg, keyword_variants):
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

                except Exception as e:
                    logger.error(f"群 {group_id} 获取消息失败: {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        break
                    await asyncio.sleep(1)

            logger.info(f"群 {group_id} 最终获取 {len(messages)} 条相关消息")
            return messages

        except Exception as e:
            logger.error(f"获取群 {group_id} 消息时发生错误: {e}")
            return []

    def _expand_keyword_variants(self, keyword: str) -> List[str]:
        """
        扩展关键词变体，支持语义相关匹配
        
        Args:
            keyword: 原始关键词
            
        Returns:
            关键词变体列表（包含原始关键词）
        """
        keyword = keyword.lower().strip()
        variants = [keyword]
        
        # 关键词映射表 - 可以扩展更多语义关联
        keyword_mappings = {
            "吃饭": ["吃饭", "吃饭饭", "干饭", "用餐", "午饭", "晚饭", "早饭", "早餐", "午餐", "晚餐", "夜宵", "外卖", "点餐", "食堂", "餐厅", "聚餐", "请客", "下馆子", "吃火锅", "吃烧烤", "吃大餐"],
            "游戏": ["游戏", "打游戏", "玩游戏", "开黑", "上分", "吃鸡", "王者", "LOL", "英雄联盟", "原神", "崩铁", "崩坏", "米哈游", "腾讯游戏", "网易游戏"],
            "学习": ["学习", "读书", "看书", "写作业", "复习", "考试", "考研", "四六级", "雅思", "托福", "背单词", "做题", "上课", "网课", "作业"],
            "工作": ["工作", "上班", "下班", "加班", "摸鱼", "打工", "996", "老板", "同事", "项目", "开会", "PPT", "汇报", "绩效", "工资", "跳槽"],
            "睡觉": ["睡觉", "睡觉觉", "午休", "午睡", "熬夜", "早起", "赖床", "起床", "失眠", "做梦", "打瞌睡", "困了", "困了困了"],
            "天气": ["天气", "下雨", "下雪", "刮风", "雾霾", "晴天", "阴天", "气温", "温度", "冷", "热", "降温", "升温", "天气预报"],
            "购物": ["购物", "买东西", "淘宝", "京东", "拼多多", "下单", "快递", "包邮", "秒杀", "双11", "618", "购物车", "付款", "退款"],
            "旅游": ["旅游", "旅行", "出去玩", "度假", "酒店", "机票", "高铁", "自驾", "景点", "打卡", "拍照", "美食", "攻略"],
            "电影": ["电影", "看电影", "影院", "电影院", "新片", "上映", "票房", "评分", "烂片", "神作", "导演", "演员", "剧情"],
            "音乐": ["音乐", "听歌", "演唱会", "专辑", "单曲", "歌手", "乐队", "网易云", "QQ音乐", "歌单", "推荐", "循环"]
        }
        
        # 查找匹配的语义组
        for base_keyword, related_words in keyword_mappings.items():
            if keyword == base_keyword or keyword in related_words:
                variants.extend(related_words)
                break
        
        # 添加一些通用变体
        common_variants = []
        for variant in variants:
            # 添加重复字变体
            if len(variant) <= 3:
                common_variants.append(variant + variant)
                if len(variant) == 2:
                    common_variants.append(variant[0] + variant + variant[1])
            
            # 添加语气词变体
            common_variants.append(variant + "了")
            common_variants.append(variant + "了")
            common_variants.append("在" + variant)
            common_variants.append("去" + variant)
            
        variants.extend(common_variants)
        
        # 去重并保持顺序
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        return unique_variants

    def _is_semantically_related(self, message: Dict, keyword_variants: List[str]) -> bool:
        """
        判断消息是否与关键词语义相关
        
        Args:
            message: 消息字典
            keyword_variants: 关键词变体列表
            
        Returns:
            是否相关
        """
        try:
            # 获取消息文本内容
            msg_texts = []
            for content in message.get("message", []):
                if content.get("type") == "text":
                    text = content.get("data", {}).get("text", "")
                    if text:
                        msg_texts.append(text.lower())
            
            if not msg_texts:
                return False
            
            # 检查是否包含任何关键词变体
            for text in msg_texts:
                for keyword in keyword_variants:
                    if keyword in text:
                        return True
            
            # 检查更灵活的匹配（部分匹配）
            for text in msg_texts:
                text_words = text.replace("，", " ").replace(",", " ").replace("。", " ").split()
                for keyword in keyword_variants:
                    # 检查关键词是否在文本单词中
                    for word in text_words:
                        if keyword in word or word in keyword:
                            return True
                    
                    # 检查相似度（简单的包含关系）
                    if len(keyword) >= 2:
                        # 检查关键词的每个字是否都在文本中出现
                        keyword_chars = set(keyword)
                        text_chars = set(text)
                        if keyword_chars.issubset(text_chars):
                            return True
            
            return False
            
        except Exception as e:
            logger.warning(f"语义相关匹配出错: {e}")
            return False
