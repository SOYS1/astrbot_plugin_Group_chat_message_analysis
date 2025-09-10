"""
报告生成器模块
负责生成话题分析的可视化报告
"""

from typing import Dict, Any, List
import base64
from datetime import datetime
from astrbot.api import logger


class ReportGenerator:
    def __init__(self):
        pass

    async def generate_topic_analysis_image(self, analysis_result: Dict, keyword: str, group_id: str, html_render_func) -> str:
        """
        生成话题分析的图片报告
        
        Args:
            analysis_result: 分析结果
            keyword: 分析的关键词
            group_id: 群号
            html_render_func: HTML渲染函数
            
        Returns:
            图片URL
        """
        try:
            # 准备渲染数据
            render_data = self._prepare_render_data(analysis_result, keyword, group_id)
            
            # 使用AstrBot内置的HTML渲染服务（传递模板和数据）
            # 修复API调用方式，确保传递data参数
            template_content = self._get_image_template()
            image_url = await html_render_func(template_content, data=render_data)
            
            return image_url
            
        except Exception as e:
            logger.error(f"生成图片报告失败: {e}")
            return ""

    def _prepare_render_data(self, analysis_result: Dict, keyword: str, group_id: str) -> Dict:
        """
        准备渲染数据
        """
        current_date = datetime.now().strftime('%Y年%m月%d日')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 生成主要贡献者HTML
        top_contributors_html = self._generate_top_contributors_for_template(analysis_result['top_contributors'])
        
        # 生成关键讨论内容HTML
        key_discussions_html = self._generate_key_discussions_for_template(analysis_result['key_discussions'])
        
        # 生成讨论会话HTML
        discussion_sessions_html = self._generate_discussion_sessions_for_template(analysis_result['discussion_sessions'])
        
        return {
            'current_date': current_date,
            'current_time': current_time,
            'keyword': keyword,
            'group_id': group_id,
            'total_messages': analysis_result['total_messages'],
            'participant_count': len(analysis_result['participants']),
            'contributor_count': len(analysis_result['top_contributors']),
            'session_count': len(analysis_result['discussion_sessions']),
            'topic_summary': analysis_result.get('topic_summary', f'关于"{keyword}"话题的分析结果'),
            'top_contributors_html': top_contributors_html,
            'key_discussions_html': key_discussions_html,
            'discussion_sessions_html': discussion_sessions_html
        }

    def _get_image_template(self) -> str:
        """
        获取图片报告的HTML模板（使用AstrBot兼容的模板语法）
        """
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>群聊话题分析报告</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Noto Sans SC', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh; padding: 20px; line-height: 1.6; color: #1a1a1a;
        }
        .container { max-width: 1200px; margin: 0 auto; background: #ffffff; border-radius: 16px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08); overflow: hidden; }
        .header { background: linear-gradient(135deg, #4299e1 0%, #667eea 100%); color: #ffffff; padding: 48px 40px; text-align: center; border-radius: 24px 24px 0 0; }
        .header h1 { font-size: 2.5em; font-weight: 300; margin-bottom: 12px; letter-spacing: -1px; }
        .header .date { font-size: 1em; opacity: 0.8; font-weight: 300; letter-spacing: 0.5px; }
        .content { padding: 32px; }
        .section { margin-bottom: 40px; }
        .section-title { font-size: 1.5em; font-weight: 600; margin-bottom: 24px; color: #4a5568; letter-spacing: -0.3px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 32px; }
        .stat-card { background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); padding: 32px 24px; text-align: center; border-radius: 20px; border: 1px solid #e2e8f0; transition: all 0.3s ease; }
        .stat-card:hover { background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); transform: translateY(-4px); box-shadow: 0 12px 32px rgba(102, 126, 234, 0.15); }
        .stat-number { font-size: 2.5em; font-weight: 300; color: #4299e1; margin-bottom: 8px; display: block; letter-spacing: -1px; }
        .stat-label { font-size: 0.9em; color: #666666; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
        .contributors { display: flex; flex-wrap: wrap; gap: 12px; }
        .contributor { background: linear-gradient(135deg, #e9f5ff 0%, #d1e7ff 100%); padding: 12px 20px; border-radius: 24px; font-size: 0.9em; font-weight: 500; box-shadow: 0 2px 8px rgba(66, 153, 225, 0.15); }
        .discussion-item { background: #ffffff; padding: 16px; margin-bottom: 12px; border-radius: 12px; border: 1px solid #e5e5e5; transition: all 0.3s ease; }
        .discussion-item:hover { background: #f8f9fa; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); }
        .discussion-sender { font-weight: 600; color: #4299e1; margin-bottom: 8px; }
        .discussion-content { margin: 8px 0; color: #333; line-height: 1.5; font-size: 0.95em; }
        .discussion-time { font-size: 0.8em; color: #999; }
        
        /* 双排并列布局样式 */
        .sessions-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .session-item { background: #ffffff; padding: 20px; margin-bottom: 20px; border-radius: 12px; border: 1px solid #e5e5e5; transition: all 0.3s ease; }
        .session-item:hover { background: #f8f9fa; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); }
        .session-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #eee; }
        .session-title { font-weight: 600; color: #4299e1; font-size: 1.1em; }
        .session-duration { background: #4299e1; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
        .session-message { background: #f8f9fa; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 3px solid #4299e1; }
        .session-sender { font-weight: 600; color: #4299e1; font-size: 0.9em; }
        .session-text { margin: 8px 0; color: #333; font-size: 0.95em; }
        .session-time { font-size: 0.8em; color: #999; }
        .session-status { margin-top: 16px; padding: 12px; border-radius: 8px; font-size: 0.9em; }
        .session-completed { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #bbf7d0; color: #166534; }
        .session-incomplete { background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); border: 1px solid #fdba74; color: #c2410c; }
        .session-result { font-weight: 500; margin-top: 8px; }
        
        .summary-box { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 24px; border-radius: 16px; border: 1px solid #bae6fd; margin: 24px 0; }
        .summary-title { font-size: 1.2em; font-weight: 600; color: #0369a1; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
        .summary-content { color: #0891b2; line-height: 1.7; }
        .footer { background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%); color: #ffffff; text-align: center; padding: 32px; font-size: 0.8em; font-weight: 300; letter-spacing: 0.5px; opacity: 0.9; }
        
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container { margin: 0; max-width: 100%; }
            .header { padding: 24px 20px; }
            .header h1 { font-size: 1.8em; }
            .content { padding: 20px; }
            .stats-grid { grid-template-columns: 1fr 1fr; gap: 12px; }
            .stat-card { padding: 20px 16px; }
            .sessions-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 群聊话题分析报告</h1>
            <div class="date">{current_date}</div>
        </div>
        <div class="content">
            <div class="section">
                <h2 class="section-title">📈 基础统计</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_messages}</div>
                        <div class="stat-label">相关消息数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{participant_count}</div>
                        <div class="stat-label">参与人数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{contributor_count}</div>
                        <div class="stat-label">活跃用户</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{session_count}</div>
                        <div class="stat-label">讨论会话</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏆 主要贡献者</h2>
                <div class="contributors">
                    {top_contributors_html}
                </div>
            </div>
            
            <div class="summary-box">
                <div class="summary-title">📋 话题总结</div>
                <div class="summary-content">
                    {topic_summary}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">💬 关键讨论内容</h2>
                {key_discussions_html}
            </div>
            
            <div class="section">
                <h2 class="section-title">🔗 讨论会话</h2>
                <div class="sessions-container">
                    {discussion_sessions_html}
                </div>
            </div>
        </div>
        <div class="footer">
            由 AstrBot 群聊话题分析插件 生成 | {current_date} {current_time}<br>
            群号: {group_id} | 关键词: {keyword}
        </div>
    </div>
</body>
</html>"""

    def _generate_top_contributors_for_template(self, top_contributors: Dict) -> str:
        """
        为模板生成主要贡献者HTML
        """
        if not top_contributors:
            return "<div style='color: #666;'>暂无贡献者数据</div>"
        
        contributors_html = ""
        for i, (name, count) in enumerate(list(top_contributors.items())[:15]):
            contributors_html += f'<div class="contributor">{name} ({count}条)</div>'
        
        return contributors_html

    def _generate_key_discussions_for_template(self, key_discussions: List[Dict]) -> str:
        """
        为模板生成关键讨论内容HTML
        """
        if not key_discussions:
            return "<div style='color: #666; text-align: center; padding: 20px;'>暂无讨论内容</div>"
        
        discussions_html = ""
        for i, discussion in enumerate(key_discussions[:15]):
            # 格式化时间
            time_str = datetime.fromtimestamp(discussion['time']).strftime('%m-%d %H:%M')
            
            discussions_html += f"""
            <div class="discussion-item">
                <div class="discussion-sender">{discussion['sender']}</div>
                <div class="discussion-content">{discussion['content']}</div>
                <div class="discussion-time">{time_str}</div>
            </div>
            """
        
        return discussions_html

    def _generate_discussion_sessions_for_template(self, discussion_sessions: List[Dict]) -> str:
        """
        为模板生成讨论会话HTML
        """
        if not discussion_sessions:
            return "<div style='color: #666; text-align: center; padding: 20px; grid-column: 1 / -1;'>暂无讨论会话</div>"
        
        sessions_html = ""
        for i, session in enumerate(discussion_sessions[:10]):
            messages_html = ""
            for msg in session['messages'][:8]:  # 限制每个会话的消息数
                time_str = datetime.fromtimestamp(msg['time']).strftime('%H:%M')
                messages_html += f"""
                <div class="session-message">
                    <div class="session-sender">{msg['sender']}</div>
                    <div class="session-text">{msg['content']}</div>
                    <div class="session-time">{time_str}</div>
                </div>
                """
            
            # 会话状态显示
            status_class = "session-completed" if session['status']['is_completed'] else "session-incomplete"
            status_text = "已完成" if session['status']['is_completed'] else "未完成"
            result_text = session['status']['result_summary']
            
            sessions_html += f"""
            <div class="session-item">
                <div class="session-header">
                    <div class="session-title">会话 #{i+1}</div>
                    <div class="session-duration">{session['message_count']}条消息</div>
                </div>
                {messages_html}
                <div class="session-status {status_class}">
                    状态: {status_text}
                    <div class="session-result">结果: {result_text}</div>
                </div>
            </div>
            """
        
        return sessions_html

    def _generate_text_report(self, analysis: Dict) -> str:
        """生成文本报告"""
        keyword = analysis.get('keyword', '未知')
        messages = analysis.get('messages', [])
        
        if not messages:
            return f"📊 关于'{keyword}'的分析报告\n\n没有找到相关的聊天记录。"
        
        # 基础统计
        total_messages = len(messages)
        participants = list(set([msg.get('sender', {}).get('nickname', '未知') for msg in messages]))
        
        # 构建报告
        report = f"📊 关于'{keyword}'的话题分析\n"
        report += f"{'=' * 30}\n\n"
        
        # 参与统计
        report += f"💬 对话概况：\n"
        report += f"   • 参与人数：{len(participants)}人\n"
        report += f"   • 消息数量：{total_messages}条\n"
        report += f"   • 主要参与者：{', '.join(participants[:3])}\n\n"
        
        # 时间分布
        if messages:
            times = [msg.get('time', 0) for msg in messages]
            if times:
                start_time = datetime.fromtimestamp(min(times)).strftime('%m-%d %H:%M')
                end_time = datetime.fromtimestamp(max(times)).strftime('%m-%d %H:%M')
                report += f"📅 讨论时段：{start_time} 至 {end_time}\n\n"
        
        # 使用新的语义化总结
        summary = self._generate_meaningful_summary(messages, keyword)
        report += f"📝 话题总结：\n{summary}\n\n"
        
        # 关键内容展示
        key_contents = []
        for msg in messages:
            content = msg.get('content', '').strip()
            if content and len(content) > 5:  # 过滤过短内容
                key_contents.append(content)
        
        if key_contents:
            unique_contents = list(set(key_contents))[:5]
            report += f"💡 精彩观点：\n"
            for i, content in enumerate(unique_contents, 1):
                truncated = content[:60] + '...' if len(content) > 60 else content
                report += f"   {i}. {truncated}\n"
        
        return report

    def _generate_meaningful_summary(self, messages: list, keyword: str) -> str:
        """生成有意义的对话总结"""
        if not messages:
            return "暂无相关讨论"
        
        # 获取参与者信息
        participants = list(set([msg.get('sender', {}).get('nickname', '未知') for msg in messages]))
        participant_names = '、'.join(participants[:3])
        if len(participants) > 3:
            participant_names += f'等{len(participants)}人'
        
        # 提取有效内容
        valid_contents = []
        for msg in messages:
            content = msg.get('content', '').strip()
            if content and len(content) > 3:  # 过滤过短内容
                valid_contents.append(content)
        
        if not valid_contents:
            return f"{participant_names}进行了简短交流"
        
        # 识别对话类型
        combined_text = ' '.join(valid_contents).lower()
        
        # 根据内容类型生成总结
        if any(q in combined_text for q in ['什么', '哪里', '怎么', '为什么', '如何', '？']):
            # 问答讨论
            key_points = [c[:50] + '...' if len(c) > 50 else c for c in valid_contents[:2]]
            if len(key_points) > 1:
                return f"{participant_names}围绕'{keyword}'展开问答讨论，主要关注：{'；'.join(key_points)}"
            else:
                return f"{participant_names}围绕'{keyword}'进行问答交流"
        
        elif any(word in combined_text for word in ['建议', '推荐', '试试', '可以考虑']):
            # 建议分享
            key_points = [c[:50] + '...' if len(c) > 50 else c for c in valid_contents[:2]]
            if len(key_points) > 1:
                return f"{participant_names}分享关于'{keyword}'的实用建议，包括：{'；'.join(key_points)}"
            else:
                return f"{participant_names}为'{keyword}'提供建议"
        
        elif any(word in combined_text for word in ['经验', '经历', '试过', '之前', '以前']):
            # 经验交流
            key_points = [c[:50] + '...' if len(c) > 50 else c for c in valid_contents[:2]]
            if len(key_points) > 1:
                return f"{participant_names}交流'{keyword}'相关经验，分享：{'；'.join(key_points)}"
            else:
                return f"{participant_names}分享'{keyword}'相关经历"
        
        else:
            # 自由讨论
            key_points = [c[:50] + '...' if len(c) > 50 else c for c in valid_contents[:2]]
            if len(key_points) > 1:
                return f"{participant_names}围绕'{keyword}'展开讨论，内容包括：{'；'.join(key_points)}"
            else:
                return f"{participant_names}讨论'{keyword}'相关内容"