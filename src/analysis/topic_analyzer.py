"""
话题分析器模块
负责分析包含特定关键词的群聊消息
"""

from typing import List, Dict, Any
from collections import defaultdict
from astrbot.api import logger
import asyncio
from datetime import datetime


class TopicAnalyzer:
    def __init__(self, config):
        self.config = config
        self.enable_llm = config.get("enable_llm_analysis", True)
        # 默认中断时间阈值为30分钟，可以通过配置修改
        self.interrupt_threshold = config.get("interrupt_threshold", 1800)  # 30分钟 = 1800秒
        
    async def analyze_topic_messages(self, messages: List[Dict], keyword: str, group_id: str) -> Dict:
        """
        分析包含特定关键词的消息
        
        Args:
            messages: 消息列表
            keyword: 分析的关键词
            group_id: 群号
            
        Returns:
            分析结果字典
        """
        analysis_result = {
            "keyword": keyword,
            "group_id": group_id,
            "total_messages": len(messages),
            "participants": set(),
            "top_contributors": {},   # 主要参与者
            "key_discussions": [],    # 关键讨论内容
            "sentiment_summary": "",  # 情感分析摘要
            "topic_summary": "",      # 话题总结
            "discussion_sessions": [] # 讨论会话（按中断分类）
        }
        
        # 统计参与者
        for msg in messages:
            sender_id = str(msg["sender"]["user_id"])
            sender_name = msg["sender"].get("card") or msg["sender"].get("nickname", sender_id)
            analysis_result["participants"].add(sender_id)
            
            # 统计发送者贡献
            analysis_result["top_contributors"][sender_name] = analysis_result["top_contributors"].get(sender_name, 0) + 1
            
            # 收集关键讨论内容
            if len(analysis_result["key_discussions"]) < 20:  # 限制收集数量
                # 获取消息中的所有文本内容
                text_contents = [
                    content.get("data", {}).get("text", "")
                    for content in msg.get("message", [])
                    if content.get("type") == "text"
                ]
                full_text = " ".join(text_contents)
                
                analysis_result["key_discussions"].append({
                    "sender": sender_name,
                    "content": full_text,
                    "time": msg["time"],
                    "message_id": msg.get("message_id", "")
                })
        
        # 转换参与者的集合为列表
        analysis_result["participants"] = list(analysis_result["participants"])
        
        # 排序主要贡献者
        analysis_result["top_contributors"] = dict(
            sorted(analysis_result["top_contributors"].items(), key=lambda x: x[1], reverse=True)[:15]
        )
        
        # 识别讨论会话（按时间中断分类）
        analysis_result["discussion_sessions"] = self._identify_discussion_sessions(messages, keyword)
        
        # 如果启用LLM分析，则进行智能分析
        if self.enable_llm:
            try:
                analysis_result["topic_summary"] = await self._generate_topic_summary(messages, keyword)
            except Exception as e:
                logger.error(f"LLM话题总结生成失败: {e}")
                analysis_result["topic_summary"] = f"关于'{keyword}'话题的分析结果"
        
        return analysis_result
    
    def _identify_discussion_sessions(self, messages: List[Dict], keyword: str) -> List[Dict]:
        """
        识别讨论会话，根据时间中断进行分类
        """
        # 按时间排序消息
        sorted_messages = sorted(messages, key=lambda x: x["time"])
        
        sessions = []
        current_session = []
        
        for msg in sorted_messages:
            # 获取消息中的所有文本内容
            text_contents = [
                content.get("data", {}).get("text", "")
                for content in msg.get("message", [])
                if content.get("type") == "text"
            ]
            full_text = " ".join(text_contents)
            
            if not current_session:
                # 开始新会话
                current_session.append({
                    "sender": msg["sender"].get("card") or msg["sender"].get("nickname", str(msg["sender"]["user_id"])),
                    "content": full_text,
                    "time": msg["time"]
                })
            else:
                # 检查是否属于当前会话
                time_diff = msg["time"] - current_session[-1]["time"]
                if time_diff <= self.interrupt_threshold:
                    # 属于当前会话
                    current_session.append({
                        "sender": msg["sender"].get("card") or msg["sender"].get("nickname", str(msg["sender"]["user_id"])),
                        "content": full_text,
                        "time": msg["time"]
                    })
                else:
                    # 时间中断，开始新会话
                    if len(current_session) > 1:  # 只保存包含多条消息的会话
                        # 分析会话状态
                        session_status = self._analyze_session_status(current_session)
                        sessions.append({
                            "messages": current_session,
                            "start_time": current_session[0]["time"],
                            "end_time": current_session[-1]["time"],
                            "duration": current_session[-1]["time"] - current_session[0]["time"],
                            "message_count": len(current_session),
                            "status": session_status
                        })
                    current_session = [{
                        "sender": msg["sender"].get("card") or msg["sender"].get("nickname", str(msg["sender"]["user_id"])),
                        "content": full_text,
                        "time": msg["time"]
                    }]
        
        # 添加最后一个会话
        if current_session and len(current_session) > 1:
            # 分析会话状态
            session_status = self._analyze_session_status(current_session)
            sessions.append({
                "messages": current_session,
                "start_time": current_session[0]["time"],
                "end_time": current_session[-1]["time"],
                "duration": current_session[-1]["time"] - current_session[0]["time"],
                "message_count": len(current_session),
                "status": session_status
            })
        
        # 按开始时间排序会话
        sessions.sort(key=lambda x: x["start_time"])
        
        return sessions
    
    def _analyze_session_status(self, session: List[Dict]) -> Dict:
        """
        分析会话状态（是否讨论完成，结果是什么）
        """
        # 简单的状态分析逻辑
        # 实际应用中可以使用更复杂的LLM分析
        messages = [msg["content"] for msg in session]
        full_text = " ".join(messages)
        
        # 检查是否包含结束性词汇
        completion_keywords = ["决定", "确定", "搞定", "完成", "结束", "定了", "就这样", "行了"]
        is_completed = any(keyword in full_text for keyword in completion_keywords)
        
        # 简单的结果提取（实际应用中可以使用LLM进行更准确的分析）
        result_summary = ""
        if is_completed:
            # 尝试提取可能的结果
            sentences = full_text.split("。")
            for sentence in sentences:
                if any(keyword in sentence for keyword in completion_keywords):
                    result_summary = sentence
                    break
            if not result_summary:
                result_summary = "讨论已完成"
        else:
            result_summary = "讨论未完成"
        
        return {
            "is_completed": is_completed,
            "result_summary": result_summary
        }
    
    async def _generate_topic_summary(self, messages: List[Dict], keyword: str) -> str:
        """
        生成话题总结
        """
        # 构造上下文
        contexts = []
        for msg in messages[:30]:  # 限制上下文数量
            # 获取消息中的所有文本内容
            text_contents = [
                content.get("data", {}).get("text", "")
                for content in msg.get("message", [])
                if content.get("type") == "text"
            ]
            full_text = " ".join(text_contents)
            
            contexts.append({"role": "user", "content": full_text})
        
        # 简单的总结逻辑（实际应用中可以调用LLM）
        if contexts:
            # 统计关键词出现频率
            keyword_count = 0
            total_messages = len(contexts)
            for ctx in contexts:
                if keyword in ctx["content"]:
                    keyword_count += 1
            
            # 识别主要参与者
            participants = {}
            for msg in messages[:30]:
                sender = msg["sender"].get("card") or msg["sender"].get("nickname", str(msg["sender"]["user_id"]))
                participants[sender] = participants.get(sender, 0) + 1
            
            top_participants = sorted(participants.items(), key=lambda x: x[1], reverse=True)[:3]
            top_participants_str = "、".join([name for name, count in top_participants])
            
            summary = f"在最近的讨论中，大家主要围绕'{keyword}'这个话题进行了交流。共有{keyword_count}条消息提到了这个关键词，主要参与者包括：{top_participants_str}。"
            return summary
        else:
            return f"关于'{keyword}'话题的分析结果"