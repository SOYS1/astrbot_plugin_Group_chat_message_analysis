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
        精准关键词扩展 - 针对技术/日常场景优化
        减少无效扩展，增加实际相关词汇
        """
        keyword = keyword.lower().strip()
        if not keyword:
            return []
        
        variants = [keyword]
        
        # 1. 技术词汇扩展（针对报错、bug等）
        tech_keywords = {
            "报错": ["错误", "异常", "bug", "故障", "问题", "error", "exception", "崩溃", "出错"],
            "错误": ["报错", "异常", "bug", "故障", "问题"],
            "异常": ["报错", "错误", "bug", "故障", "异常退出"],
            "bug": ["漏洞", "缺陷", "问题", "报错", "错误"],
            "崩溃": ["闪退", "崩溃", "卡死", "无响应", "死机"],
            "代码": ["程序", "脚本", "项目", "工程"],
            "运行": ["执行", "启动", "调用", "运行中"],
            "服务器": ["服务", "后端", "接口", "api"],
            "网络": ["网卡", "断网", "连接", "超时"]
        }
        
        # 2. 日常词汇扩展
        daily_keywords = {
            "吃饭": ["用餐", "就餐", "吃饭饭", "吃点", "吃饭了吗"],
            "睡觉": ["休息", "就寝", "睡吧", "困了", "晚安"],
            "工作": ["上班", "干活", "加班", "下班", "摸鱼"],
            "学习": ["看书", "复习", "考试", "作业", "学习ing"]
        }
        
        # 3. 网络用语扩展（精选）
        internet_keywords = {
            "笑死": ["xswl", "笑死我了", "哈哈哈", "笑不活了"],
            "厉害": ["牛逼", "nb", "太强了", "牛啊"],
            "无语": ["emmmm", "无语子", "裂开", "麻了"]
        }
        
        # 合并所有扩展
        all_extensions = {**tech_keywords, **daily_keywords, **internet_keywords}
        
        # 查找匹配的关键词扩展
        for base_word, extensions in all_extensions.items():
            if base_word in keyword or keyword in base_word:
                variants.extend(extensions)
        
        # 4. 智能后缀扩展（仅对2-4字关键词）
        if 2 <= len(keyword) <= 4:
            smart_suffixes = ["了", "的", "了", "一下", "了", "吗"]
            for suffix in smart_suffixes:
                if len(keyword + suffix) <= 6:  # 限制总长度
                    variants.append(keyword + suffix)
        
        # 5. 同义词扩展（基于实际使用场景）
        synonyms = {
            "问题": ["毛病", "状况", "情况", "现象"],
            "解决": ["修复", "搞定", "处理", "搞定它"],
            "着急": ["焦虑", "烦躁", "上火", "急死"]
        }
        
        for word, syns in synonyms.items():
            if word in keyword:
                variants.extend(syns)
        
        # 去重并按相关度排序
        seen = set()
        unique_variants = []
        
        for variant in variants:
            variant = variant.strip()
            if variant and variant != keyword and variant not in seen:
                seen.add(variant)
                # 计算相关度（越短越相关，包含关系更相关）
                score = 100 - len(variant) * 2  # 长度惩罚
                
                # 包含关系加分
                if keyword in variant or variant in keyword:
                    score += 50
                
                # 技术词汇加分
                tech_bonus_words = ["error", "bug", "异常", "错误", "故障"]
                if any(tech in variant.lower() for tech in tech_bonus_words):
                    score += 30
                
                unique_variants.append((variant, score))
        
        # 按分数排序，取前10个最相关的
        unique_variants.sort(key=lambda x: x[1], reverse=True)
        final_variants = [keyword] + [item[0] for item in unique_variants[:10]]
        
        logger.info(f"精准扩展 '{keyword}' → {len(final_variants)}个相关变体: {final_variants}")
        return final_variants

    def _generate_char_variants(self, keyword: str) -> List[str]:
        """简化的字符变形 - 仅保留实用的"了"和"的"后缀"""
        variants = []
        if 2 <= len(keyword) <= 4:
            variants.extend([keyword + "了", keyword + "的"])
        return variants

    def _generate_internet_variants(self, keyword: str) -> List[str]:
        """网络用语扩展 - 仅针对特定网络人物"""
        return []  # 简化掉，避免过度扩展

    def _generate_semantic_variants(self, keyword: str) -> List[str]:
        """语义扩展 - 简化"""
        return []

    def _generate_contextual_variants(self, keyword: str) -> List[str]:
        """上下文扩展 - 简化"""
        return []

    def _generate_fuzzy_variants(self, keyword: str) -> List[str]:
        """模糊匹配 - 简化"""
        return []

    def _calculate_relevance_score(self, original: str, variant: str) -> float:
        """计算词汇相关度分数"""
        if original == variant:
            return 100.0
        
        score = 0.0
        
        # 编辑距离分数
        import difflib
        similarity = difflib.SequenceMatcher(None, original, variant).ratio()
        score += similarity * 50
        
        # 包含关系分数
        if original in variant or variant in original:
            score += 30
        
        # 字符重叠分数
        original_chars = set(original)
        variant_chars = set(variant)
        overlap = len(original_chars.intersection(variant_chars))
        if overlap > 0:
            score += (overlap / len(original_chars)) * 20
        
        return min(score, 100.0)

    def _is_semantically_related(self, message: Dict, keyword_variants: List[str]) -> bool:
        """
        智能语义关联判断 - 无需词典的动态理解
        支持字符相似度、网络用语、上下文理解
        
        Args:
            message: 消息字典
            keyword_variants: 关键词变体列表
            
        Returns:
            是否语义相关
        """
        try:
            text = message.get('content', '').lower().strip()
            if not text or not keyword_variants:
                return False
            
            original_keyword = keyword_variants[0].lower()
            
            # 1. 直接包含匹配（最高优先级）
            for variant in keyword_variants:
                if variant in text:
                    logger.info(f"直接匹配: '{variant}' 在消息中")
                    return True
            
            # 2. 字符级相似度匹配
            similarity_threshold = 0.6
            for variant in keyword_variants:
                similarity = self._calculate_text_similarity(text, variant)
                if similarity >= similarity_threshold:
                    logger.info(f"字符相似度匹配: '{variant}' (相似度: {similarity:.2f})")
                    return True
            
            # 3. 分词模糊匹配
            if self._fuzzy_word_match(text, keyword_variants):
                return True
            
            # 4. 网络用语模式匹配
            if self._internet_pattern_match(text, original_keyword):
                return True
            
            # 5. 上下文语义关联
            if self._contextual_semantic_match(text, original_keyword):
                return True
            
            # 6. 拼音相似度匹配
            if self._pinyin_similarity_match(text, original_keyword):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"语义匹配出错: {e}")
            # 回退到简单包含匹配
            return any(variant in str(message.get('content', '')).lower() 
                      for variant in keyword_variants)

    def _calculate_text_similarity(self, text: str, keyword: str) -> float:
        """计算文本相似度"""
        import difflib
        
        # 子串相似度
        max_similarity = 0.0
        text_len = len(text)
        keyword_len = len(keyword)
        
        if keyword_len == 0:
            return 0.0
        
        # 滑动窗口计算最大相似度
        for i in range(text_len - keyword_len + 1):
            substring = text[i:i+keyword_len]
            similarity = difflib.SequenceMatcher(None, substring, keyword).ratio()
            max_similarity = max(max_similarity, similarity)
        
        # 字符重叠度
        text_chars = set(text)
        keyword_chars = set(keyword)
        char_overlap = len(text_chars.intersection(keyword_chars))
        char_similarity = char_overlap / len(keyword_chars) if keyword_chars else 0
        
        return max(max_similarity, char_similarity * 0.8)

    def _fuzzy_word_match(self, text: str, keyword_variants: List[str]) -> bool:
        """分词模糊匹配"""
        # 简单的分词实现
        def simple_tokenize(text: str) -> List[str]:
            # 按空格和标点分词
            import re
            tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text)
            return [token.lower() for token in tokens]
        
        text_tokens = simple_tokenize(text)
        
        for keyword in keyword_variants:
            keyword_tokens = simple_tokenize(keyword)
            
            # 检查每个关键词token
            for keyword_token in keyword_tokens:
                for text_token in text_tokens:
                    # 编辑距离检查
                    if self._levenshtein_distance(keyword_token, text_token) <= 1:
                        logger.info(f"分词模糊匹配: '{keyword_token}' ~ '{text_token}'")
                        return True
                    
                    # 包含关系检查
                    if keyword_token in text_token or text_token in keyword_token:
                        if len(keyword_token) >= 2 and len(text_token) >= 2:
                            logger.info(f"分词包含匹配: '{keyword_token}' in '{text_token}'")
                            return True
        
        return False

    def _internet_pattern_match(self, text: str, keyword: str) -> bool:
        """网络用语模式匹配"""
        # 网络用语映射（动态识别）
        internet_patterns = {
            "孙笑川": {
                "patterns": ["抽象", "带师", "nm", "新津", "恶俗", "狗粉丝", "6324", "嗨粉", "带明星"],
                "keywords": ["孙笑川", "笑川", "孙笑", "笑川"]
            },
            "蔡徐坤": {
                "patterns": ["鸡哥", "鸡你太美", "篮球", "练习生", "两年半", "小黑子", "唱跳rap"],
                "keywords": ["蔡徐坤", "徐坤", "蔡徐", "坤坤"]
            },
            "丁真": {
                "patterns": ["珍珠", "理塘", "电子烟", "锐刻", "纯真", "一眼真", "丁真珍珠"],
                "keywords": ["丁真", "珍珠", "理塘"]
            }
        }
        
        # 检查是否是网络人物相关
        for person, data in internet_patterns.items():
            if any(kw in keyword for kw in data["keywords"]):
                for pattern in data["patterns"]:
                    if pattern.lower() in text.lower():
                        logger.info(f"网络用语匹配: '{person}' 相关 '{pattern}'")
                        return True
        
        return False

    def _contextual_semantic_match(self, text: str, keyword: str) -> bool:
        """上下文语义关联"""
        # 上下文关键词映射
        context_keywords = {
            "人名": ["这个人", "这位", "大佬", "老师", "哥", "姐", "兄弟", "朋友", "主播", "up主"],
            "事件": ["发生", "出现", "看到", "听说", "知道", "了解", "看到", "遇到"],
            "评价": ["觉得", "认为", "感觉", "好像", "似乎", "可能", "应该", "确实"]
        }
        
        # 如果关键词是人名，检查上下文
        if len(keyword) <= 4 and any(char in keyword for char in ["孙", "李", "张", "王", "刘", "陈", "杨", "赵", "黄", "周"]):
            for category, keywords in context_keywords.items():
                for context_kw in keywords:
                    if context_kw in text:
                        # 检查文本中是否包含人名特征
                        name_patterns = ["[\u4e00-\u9fff]{2,4}", "[A-Z][a-z]+"]
                        import re
                        for pattern in name_patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                if self._calculate_text_similarity(match.lower(), keyword) > 0.5:
                                    logger.info(f"上下文人名匹配: '{keyword}' ~ '{match}'")
                                    return True
        
        return False

    def _pinyin_similarity_match(self, text: str, keyword: str) -> bool:
        """拼音相似度匹配"""
        try:
            # 简单的拼音转换（实际项目中可以使用pypinyin库）
            def simple_pinyin(text: str) -> str:
                # 这里用简化的方式，实际应该使用pypinyin
                pinyin_map = {
                    '孙': 'sun', '笑': 'xiao', '川': 'chuan',
                    '蔡': 'cai', '徐': 'xu', '坤': 'kun',
                    '丁': 'ding', '真': 'zhen'
                }
                result = ""
                for char in text:
                    result += pinyin_map.get(char, char)
                return result
            
            text_pinyin = simple_pinyin(text)
            keyword_pinyin = simple_pinyin(keyword)
            
            similarity = difflib.SequenceMatcher(None, text_pinyin, keyword_pinyin).ratio()
            if similarity >= 0.7:
                logger.info(f"拼音相似度匹配: '{keyword}' (拼音相似度: {similarity:.2f})")
                return True
                
        except Exception as e:
            logger.debug(f"拼音匹配出错: {e}")
        
        return False

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]