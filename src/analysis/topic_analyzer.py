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
        生成话题总结，避免机械化表述
        """
        if not messages:
            return "暂无相关讨论"
        
        # 获取参与者信息
        participants = list(set([msg.get('sender', {}).get('nickname', '未知') for msg in messages]))
        participant_names = '、'.join(participants[:3])
        if len(participants) > 3:
            participant_names += f'等{len(participants)}人'
        
        # 识别对话类型
        combined_text = ' '.join([msg.get('content', '') for msg in messages]).lower()
        
        # 提取关键信息
        key_contents = []
        for msg in messages:
            content = msg.get('content', '').strip()
            if content and len(content) > 3:  # 过滤过短的回复
                key_contents.append(content)
        
        # 去除重复内容
        unique_contents = list(set(key_contents))[:3]
        
        # 生成语义化总结
        if len(unique_contents) == 0:
            return f"{participant_names}进行了简短交流"
        
        # 根据对话内容类型生成总结
        if any(q in combined_text for q in ['什么', '哪里', '怎么', '为什么', '如何', '？']):
            # 问答讨论
            key_points = [c[:40] + '...' if len(c) > 40 else c for c in unique_contents[:2]]
            if len(unique_contents) == 1:
                return f"{participant_names}围绕'{keyword}'展开讨论"
            else:
                key_info = '；'.join([c[:40] + '...' if len(c) > 40 else c for c in unique_contents[:2]])
                return f"{participant_names}围绕'{keyword}'交流，主要涉及：{key_info}"
        
        elif any(word in combined_text for word in ['建议', '推荐', '试试', '可以考虑', '建议']):
            # 建议分享
            key_info = '；'.join([c[:40] + '...' if len(c) > 40 else c for c in unique_contents[:2]])
            return f"{participant_names}分享关于'{keyword}'的实用建议，包括：{key_info}"
        
        elif any(word in combined_text for word in ['经验', '经历', '试过', '之前', '以前']):
            # 经验交流
            key_info = '；'.join([c[:40] + '...' if len(c) > 40 else c for c in unique_contents[:2]])
            return f"{participant_names}交流'{keyword}'相关经验，分享：{key_info}"
        
        else:
            # 自由讨论
            key_info = '；'.join([c[:40] + '...' if len(c) > 40 else c for c in unique_contents[:2]])
            if len(unique_contents) == 1:
                return f"{participant_names}讨论'{keyword}'相关内容"
            else:
                return f"{participant_names}围绕'{keyword}'展开讨论，内容包括：{key_info}"
        
        # 构造上下文
        contexts = []
        for msg in messages:
            content = msg.get('content', '').strip()
            if content:
                contexts.append(content)
        
        # 使用新的语义化总结
        return self._generate_topic_summary(messages, keyword)
    
    def _analyze_discussion_sessions(self, messages: List[Dict], keyword: str) -> List[Dict]:
        """
        分析讨论会话，改进总结逻辑，避免机械化表述
        """
        sessions = []
        if not messages:
            return sessions

        # 按时间排序
        messages.sort(key=lambda x: x['time'])
        
        current_session = {
            'messages': [],
            'start_time': messages[0]['time'],
            'end_time': messages[0]['time'],
            'keywords_found': set(),
            'natural_interactions': []  # 记录自然交流
        }
        
        for msg in messages:
            time_gap = msg['time'] - current_session['end_time']
            
            # 如果间隔超过10分钟，创建新会话
            if time_gap > 600 and current_session['messages']:
                sessions.append(self._finalize_session(current_session))
                current_session = {
                    'messages': [],
                    'start_time': msg['time'],
                    'end_time': msg['time'],
                    'keywords_found': set(),
                    'natural_interactions': []
                }
            
            current_session['messages'].append(msg)
            current_session['end_time'] = msg['time']
            
            # 识别关键词（包括语义扩展）
            if self._is_semantically_related(msg['content'], keyword):
                current_session['keywords_found'].add(keyword)
            
            # 识别自然交流互动
            if self._is_natural_interaction(msg['content']):
                current_session['natural_interactions'].append(msg)
        
        # 处理最后一个会话
        if current_session['messages']:
            sessions.append(self._finalize_session(current_session))
        
        return sessions

    def _is_natural_interaction(self, text: str) -> bool:
        """
        识别自然交流互动，不局限于特定关键词
        """
        text = text.lower().strip()
        
        # 问答模式
        qa_patterns = [
            r'什么.*[？?]',
            r'哪里.*[？?]',
            r'怎么.*[？?]',
            r'为什么.*[？?]',
            r'如何.*[？?]',
            r'[？?]',
            r'.*[回答|回复|说|讲].*[？?]'
        ]
        
        # 日常交流
        daily_patterns = [
            r'[吃饭|吃啥|吃什么|晚餐|午餐|早餐]',
            r'[去哪里|去哪儿|去干嘛|干嘛]',
            r'[好的|可以|行|不行|不要|要]',
            r'[谢谢|感谢|不客气|客气]',
            r'[哈哈|呵呵|嘿嘿|笑死|有趣]',
            r'[同意|反对|支持|不支持|赞成]'
        ]
        
        import re
        for pattern in qa_patterns + daily_patterns:
            if re.search(pattern, text):
                return True
        
        # 简短回复也视为有效互动
        short_responses = ['好', '行', '可以', '不行', '不要', '要', '嗯', '哦', '哈哈']
        if text in short_responses or len(text) <= 5:
            return True
            
        return False

    def _finalize_session(self, session: Dict) -> Dict:
        """
        完成会话分析，生成有意义的总结
        """
        messages = session['messages']
        if not messages:
            return None
        
        # 分析会话主题和走向
        content_analysis = self._analyze_conversation_flow(messages)
        
        # 生成有意义的总结
        summary = self._generate_meaningful_summary(messages, content_analysis)
        
        return {
            'messages': messages,
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'message_count': len(messages),
            'status': {
                'summary': summary,  # 用有意义的总结替代状态
                'key_points': content_analysis['key_points'],
                'interaction_type': content_analysis['type'],
                'participants': list(set([msg['sender'] for msg in messages]))
            }
        }

    def _analyze_conversation_flow(self, messages: List[Dict]) -> Dict:
        """
        分析对话流向和主题
        """
        if not messages:
            return {'type': '无内容', 'key_points': [], 'summary': '无对话内容'}
        
        # 提取关键信息
        contents = [msg['content'] for msg in messages]
        senders = [msg['sender'] for msg in messages]
        
        # 识别对话类型
        conversation_type = self._identify_conversation_type(contents)
        
        # 提取关键点
        key_points = self._extract_key_points(contents)
        
        return {
            'type': conversation_type,
            'key_points': key_points,
            'participant_count': len(set(senders)),
            'turn_count': len(messages)
        }

    def _identify_conversation_type(self, contents: List[str]) -> str:
        """
        识别对话类型
        """
        combined_text = ' '.join(contents).lower()
        
        # 问答讨论
        if any(q in combined_text for q in ['什么', '哪里', '怎么', '为什么', '如何', '？', '?']):
            return '问答讨论'
        
        # 建议分享
        if any(word in combined_text for word in ['建议', '推荐', '试试', '可以考虑', '不如']):
            return '建议分享'
        
        # 经验交流
        if any(word in combined_text for word in ['经验', '经历', '试过', '之前', '上次']):
            return '经验交流'
        
        # 日常闲聊
        if len(contents) <= 3 and any(word in combined_text for word in ['好', '行', '可以', '嗯', '哈哈']):
            return '简短回应'
        
        return '自由讨论'

    def _extract_key_points(self, contents: List[str]) -> List[str]:
        """
        提取对话关键点
        """
        key_points = []
        
        for content in contents:
            content = content.strip()
            if len(content) > 10:  # 较长的内容可能是重点
                key_points.append(content[:50] + '...' if len(content) > 50 else content)
            elif content and content not in ['好', '行', '可以', '嗯', '哦', '哈哈', '谢谢']:
                key_points.append(content)
        
        # 去重并限制数量
        unique_points = list(set(key_points))
        return unique_points[:5]

    def _generate_meaningful_summary(self, messages: List[Dict], analysis: Dict) -> str:
        """
        生成有意义的对话总结
        """
        if not messages:
            return '对话内容为空'
        
        participants = list(set([msg['sender'] for msg in messages]))
        participant_names = '、'.join(participants[:3])
        if len(participants) > 3:
            participant_names += f'等{len(participants)}人'
        
        conv_type = analysis['type']
        key_points = analysis['key_points']
        
        # 根据对话类型生成总结
        if conv_type == '问答讨论':
            if key_points:
                summary = f"{participant_names}围绕话题展开讨论，主要关注：{'；'.join(key_points[:2])}"
            else:
                summary = f"{participant_names}进行了问答交流"
        
        elif conv_type == '建议分享':
            if key_points:
                summary = f"{participant_names}分享实用建议，包括：{'；'.join(key_points[:2])}"
            else:
                summary = f"{participant_names}互相提供建议"
        
        elif conv_type == '经验交流':
            if key_points:
                summary = f"{participant_names}交流相关经验，涉及：{'；'.join(key_points[:2])}"
            else:
                summary = f"{participant_names}分享个人经历"
        
        elif conv_type == '简短回应':
            summary = f"{participant_names}进行简短交流"
        
        else:  # 自由讨论
            if key_points:
                summary = f"{participant_names}自由讨论，内容包括：{'；'.join(key_points[:2])}"
            else:
                summary = f"{participant_names}参与话题讨论"
        
        return summary
