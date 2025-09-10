#!/usr/bin/env python3
"""
调试消息过滤问题 - 检查为什么获取到消息但没有识别为相关
"""

import sys
import os
import json
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))

class DebugMessageFilter:
    """调试消息过滤器"""
    
    def __init__(self):
        self.group_id = "753075035"
        self.keyword = "报错"
        
    def _expand_keyword_variants(self, keyword: str):
        """关键词扩展"""
        keyword = keyword.lower().strip()
        variants = [keyword]
        
        # 扩展列表
        extensions = [
            "错误", "异常", "bug", "故障", "问题", "error", "exception", "崩溃", "出错",
            "怎么办", "怎么解决", "求助", "帮帮我", "救命", "急", "在线等",
            "坏了", "不行了", "出问题了", "崩了", "挂了", "死机了",
            "打不开", "无法启动", "运行不了", "闪退了", "无响应"
        ]
        
        variants.extend(extensions)
        return list(set(variants))
    
    def _is_semantically_related(self, text: str, keyword_variants: list) -> bool:
        """检查文本是否与关键词相关"""
        text = text.lower().strip()
        if not text:
            return False
        
        print(f"\n🔍 检查消息: '{text}'")
        print(f"关键词变体: {keyword_variants}")
        
        # 1. 直接包含检查
        for variant in keyword_variants:
            if variant in text:
                print(f"✅ 直接匹配: '{variant}' 在消息中")
                return True
        
        # 2. 字符相似度检查
        import difflib
        for variant in keyword_variants:
            similarity = difflib.SequenceMatcher(None, text, variant).ratio()
            if similarity >= 0.3:  # 降低阈值
                print(f"⚠️ 字符相似度: '{variant}' (相似度: {similarity:.2f})")
                if similarity >= 0.5:
                    return True
        
        # 3. 分词检查
        def simple_tokenize(text: str):
            import re
            return re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text.lower())
        
        text_tokens = simple_tokenize(text)
        keyword_tokens = []
        for variant in keyword_variants:
            keyword_tokens.extend(simple_tokenize(variant))
        
        for kw_token in keyword_tokens:
            for text_token in text_tokens:
                if kw_token in text_token or text_token in kw_token:
                    if len(kw_token) >= 2:
                        print(f"✅ 分词匹配: '{kw_token}' ~ '{text_token}'")
                        return True
        
        print("❌ 无匹配")
        return False
    
    def debug_filtering(self):
        """调试消息过滤"""
        print("🎯 调试消息过滤问题")
        print("=" * 50)
        
        # 模拟群消息
        mock_messages = [
            "服务器突然崩了，怎么办？",
            "程序报错了，有人能帮忙吗？",
            "这个bug怎么解决？",
            "系统出问题了，在线等！",
            "报错信息看不懂，求助",
            "软件异常退出，急！",
            "运行不了，帮帮忙",
            "出现错误代码，大佬救急",
            "服务器挂了，救命啊！",
            "程序打不开，崩了",
            "这啥情况啊，一直报错",
            "有人遇到过这个问题吗？",
            "求大佬帮忙看看这个错误",
            "程序运行不了，急死了",
            "系统崩了，怎么修复？"
        ]
        
        keyword_variants = self._expand_keyword_variants("报错")
        print(f"关键词扩展结果: {keyword_variants}")
        
        matched_count = 0
        for i, msg in enumerate(mock_messages, 1):
            print(f"\n--- 消息 {i} ---")
            is_related = self._is_semantically_related(msg, keyword_variants)
            if is_related:
                matched_count += 1
                print(f"🎯 匹配成功: {msg}")
        
        print(f"\n📊 统计结果:")
        print(f"总消息数: {len(mock_messages)}")
        print(f"匹配成功: {matched_count}")
        print(f"匹配率: {matched_count/len(mock_messages)*100:.1f}%")
        
        # 检查可能的问题
        print(f"\n🔧 可能的问题:")
        print("1. 关键词扩展是否完整？")
        print("2. 相似度阈值是否过高？")
        print("3. 消息内容是否被预处理？")
        print("4. 时间范围是否合适？")
        
        return matched_count > 0

if __name__ == "__main__":
    debugger = DebugMessageFilter()
    debugger.debug_filtering()