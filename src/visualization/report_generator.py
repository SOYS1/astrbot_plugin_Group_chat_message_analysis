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

    def generate_text_report(self, analysis_result: Dict) -> str:
        """
        生成文本格式的报告
        """
        report = f"""
=== 群聊话题分析报告 ===
关键词: {analysis_result['keyword']}
群号: {analysis_result['group_id']}
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

📊 统计信息:
- 相关消息数: {analysis_result['total_messages']}
- 参与人数: {len(analysis_result['participants'])}
- 活跃用户: {len(analysis_result['top_contributors'])}
- 讨论会话: {len(analysis_result['discussion_sessions'])}

🏆 主要贡献者:
        """
        
        for name, count in list(analysis_result['top_contributors'].items())[:10]:
            report += f"- {name}: {count}条消息\n"
        
        report += f"\n📋 话题总结:\n{analysis_result.get('topic_summary', '暂无智能分析结果')}"
        
        report += "\n\n💬 关键讨论内容:\n"
        for i, discussion in enumerate(analysis_result['key_discussions'][:8], 1):
            time_str = datetime.fromtimestamp(discussion['time']).strftime('%m-%d %H:%M')
            report += f"{i}. {discussion['sender']} ({time_str}): {discussion['content']}\n"
        
        report += "\n🔗 讨论会话:\n"
        for i, session in enumerate(analysis_result['discussion_sessions'][:5], 1):
            start_time = datetime.fromtimestamp(session['start_time']).strftime('%m-%d %H:%M')
            end_time = datetime.fromtimestamp(session['end_time']).strftime('%H:%M')
            status = "已完成" if session['status']['is_completed'] else "未完成"
            result = session['status']['result_summary']
            
            report += f"会话 {i} ({session['message_count']}条消息, {start_time}-{end_time}, {status}):\n"
            report += f"  结果: {result}\n"
            
            for j, msg in enumerate(session['messages'][:5], 1):
                time_str = datetime.fromtimestamp(msg['time']).strftime('%H:%M')
                report += f"  {j}. {msg['sender']} ({time_str}): {msg['content']}\n"
            report += "\n"
        
        return report                        logger.warning(f"群 {group_id} API返回无效结果: {result}")
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
        智能语义扩展系统 - 无需预定义词典
        基于字符相似度、网络用语变形、上下文模式识别
        
        Args:
            keyword: 任意关键词
            
        Returns:
            动态生成的语义相关词汇列表
        """
        keyword = keyword.lower().strip()
        if not keyword:
            return []
        
        variants = [keyword]
        
        # 1. 字符级智能变形
        variants.extend(self._generate_char_variants(keyword))
        
        # 2. 网络用语智能识别
        variants.extend(self._generate_internet_variants(keyword))
        
        # 3. 语义场动态扩展
        variants.extend(self._generate_semantic_variants(keyword))
        
        # 4. 上下文模式匹配
        variants.extend(self._generate_contextual_variants(keyword))
        
        # 5. 模糊匹配变体
        variants.extend(self._generate_fuzzy_variants(keyword))
        
        # 去重并排序（按相关度）
        seen = set()
        unique_variants = []
        for variant in variants:
            variant = variant.strip()
            if variant and variant != keyword and variant not in seen:
                seen.add(variant)
                # 计算相关度分数用于排序
                score = self._calculate_relevance_score(keyword, variant)
                unique_variants.append((variant, score))
        
        # 按相关度排序，取前30个
        unique_variants.sort(key=lambda x: x[1], reverse=True)
        final_variants = [keyword] + [item[0] for item in unique_variants[:30]]
        
        logger.info(f"智能扩展 '{keyword}' → {len(final_variants)}个变体: {final_variants}")
        return final_variants

    def _generate_char_variants(self, keyword: str) -> List[str]:
        """字符级智能变形"""
        variants = []
        
        # 重复字变体
        if len(keyword) <= 4:
            variants.append(keyword + keyword)
            if len(keyword) >= 2:
                variants.append(keyword[0] + keyword)
                variants.append(keyword + keyword[-1])
        
        # 前后缀
        prefixes = ["大", "小", "老", "新", "超级", "真的", "假的"]
        suffixes = ["了", "的", "一下", "了", "了", "啊", "呀", "呢"]
        
        for prefix in prefixes:
            variants.append(prefix + keyword)
        
        for suffix in suffixes:
            variants.append(keyword + suffix)
        
        return variants

    def _generate_internet_variants(self, keyword: str) -> List[str]:
        """网络用语智能识别"""
        variants = []
        
        # 数字替换
        num_replacements = {
            'o': '0', 'i': '1', 'l': '1', 'z': '2', 'e': '3', 'a': '4', 
            's': '5', 't': '7', 'b': '6', 'g': '9', 'q': '9'
        }
        
        # 网络流行语模式
        internet_patterns = {
            "孙笑川": ["抽象", "带师", "nm$l", "新津", "恶俗", "狗粉丝", "6324", "嗨粉"],
            "蔡徐坤": ["鸡哥", "鸡你太美", "篮球", "练习生", "两年半", "小黑子"],
            "丁真": ["珍珠", "理塘", "电子烟", "锐刻5", "纯真", "一眼真"],
            "马保国": ["耗子尾汁", "年轻人不讲武德", "传统功夫", "接化发", "闪电五连鞭"],
            "李赣": ["6324", "抽象", "嗨粉", "狗粉丝", "带明星", "带秀"]
        }
        
        # 检查是否是网络人物
        for person, related in internet_patterns.items():
            if keyword in person or person in keyword:
                variants.extend(related)
        
        # 谐音梗
        if "笑" in keyword:
            variants.extend(["孝", "校", "效", "啸"])
        if "川" in keyword:
            variants.extend(["穿", "传", "船", "喘"])
        if "坤" in keyword:
            variants.extend(["鲲", "昆", "捆", "困"])
        
        # 网络缩写
        abbreviations = {
            "yyds": ["永远的神", "永远滴神"],
            "xswl": ["笑死我了"],
            "zqsg": ["真情实感"],
            "u1s1": ["有一说一"],
            "dddd": ["懂的都懂"]
        }
        
        for abbr, full in abbreviations.items():
            if keyword == abbr:
                variants.extend(full)
            elif keyword in str(full):
                variants.append(abbr)
        
        return variants

    def _generate_semantic_variants(self, keyword: str) -> List[str]:
        """语义场动态扩展"""
        variants = []
        
        # 基于关键词类型的语义扩展
        if len(keyword) <= 3:
            # 短词扩展
            if keyword.endswith("哥"):
                variants.extend(["哥哥", "大哥", "老哥", "哥儿", "哥子"])
            elif keyword.endswith("姐"):
                variants.extend(["姐姐", "大姐", "老姐", "姐儿"])
            elif keyword.endswith("弟"):
                variants.extend(["弟弟", "小弟", "老弟", "弟儿"])
            elif keyword.endswith("妹"):
                variants.extend(["妹妹", "小妹", "老妹", "妹儿"])
        
        # 情感词扩展
        emotion_words = ["喜欢", "讨厌", "爱", "恨", "想", "念", "烦", "愁", "开心", "难过"]
        for emotion in emotion_words:
            variants.append(emotion + keyword)
            variants.append(keyword + emotion)
        
        # 动作词扩展
        action_words = ["看", "听", "说", "想", "做", "玩", "学", "吃", "喝", "买"]
        for action in action_words:
            variants.append(action + keyword)
            variants.append(keyword + action)
        
        return variants

    def _generate_contextual_variants(self, keyword: str) -> List[str]:
        """上下文模式匹配"""
        variants = []
        
        # 基于使用场景的上下文词
        contexts = {
            "人名": ["这个人", "这位", "大佬", "老师", "哥", "姐", "兄弟", "朋友"],
            "地点": ["在", "去", "到", "从", "来", "回", "路过", "经过"],
            "时间": ["今天", "昨天", "明天", "刚才", "刚刚", "现在", "以后", "以前"],
            "评价": ["真的", "假的", "太", "很", "超级", "特别", "非常", "有点", "稍微"]
        }
        
        # 根据关键词特征添加上下文
        for context_type, context_words in contexts.items():
            for context in context_words:
                variants.append(context + keyword)
                variants.append(keyword + context)
        
        return variants

    def _generate_fuzzy_variants(self, keyword: str) -> List[str]:
        """模糊匹配变体"""
        variants = []
        
        # 编辑距离1的变体（插入、删除、替换）
        if len(keyword) >= 2:
            # 删除一个字符
            for i in range(len(keyword)):
                variants.append(keyword[:i] + keyword[i+1:])
            
            # 插入常见字符
            common_chars = ["的", "了", "子", "儿", "啊", "呀", "呢", "吧"]
            for char in common_chars:
                for i in range(len(keyword) + 1):
                    variants.append(keyword[:i] + char + keyword[i:])
            
            # 替换相似字符
            similar_chars = {
                '笑': '孝', '川': '穿', '孙': '损', '坤': '鲲',
                '蔡': '菜', '徐': '许', '丁': '钉', '真': '针'
            }
            for original, similar in similar_chars.items():
                if original in keyword:
                    variants.append(keyword.replace(original, similar))
        
        return variants

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
        
        return previous_row[-1]            'topic_summary': analysis_result.get('topic_summary', f'关于"{keyword}"话题的分析结果'),
            'top_contributors_html': top_contributors_html,
            'key_discussions_html': key_discussions_html,
            'discussion_sessions_html': discussion_sessions_html
        }

    def _get_image_template(self) -> str:
        """
        获取图片报告的HTML模板（使用{{ }}占位符）
        """
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>群聊话题分析报告 - {{ keyword }}</title>
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
            <div class="date">{{ current_date }}</div>
        </div>
        <div class="content">
            <div class="section">
                <h2 class="section-title">📈 基础统计</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{{ total_messages }}</div>
                        <div class="stat-label">相关消息数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ participant_count }}</div>
                        <div class="stat-label">参与人数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ contributor_count }}</div>
                        <div class="stat-label">活跃用户</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ session_count }}</div>
                        <div class="stat-label">讨论会话</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">🏆 主要贡献者</h2>
                <div class="contributors">
                    {{ top_contributors_html | safe }}
                </div>
            </div>
            
            <div class="summary-box">
                <div class="summary-title">📋 话题总结</div>
                <div class="summary-content">
                    {{ topic_summary }}
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">💬 关键讨论内容</h2>
                {{ key_discussions_html | safe }}
            </div>
            
            <div class="section">
                <h2 class="section-title">🔗 讨论会话</h2>
                <div class="sessions-container">
                    {{ discussion_sessions_html | safe }}
                </div>
            </div>
        </div>
        <div class="footer">
            由 AstrBot 群聊话题分析插件 生成 | {{ current_date }} {{ current_time }}<br>
            群号: {{ group_id }} | 关键词: {{ keyword }}
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

    def generate_text_report(self, analysis_result: Dict) -> str:
        """
        生成文本格式的报告
        """
        report = f"""
=== 群聊话题分析报告 ===
关键词: {analysis_result['keyword']}
群号: {analysis_result['group_id']}
生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

📊 统计信息:
- 相关消息数: {analysis_result['total_messages']}
- 参与人数: {len(analysis_result['participants'])}
- 活跃用户: {len(analysis_result['top_contributors'])}
- 讨论会话: {len(analysis_result['discussion_sessions'])}

🏆 主要贡献者:
        """
        
        for name, count in list(analysis_result['top_contributors'].items())[:10]:
            report += f"- {name}: {count}条消息\n"
        
        report += f"\n📋 话题总结:\n{analysis_result.get('topic_summary', '暂无智能分析结果')}"
        
        report += "\n\n💬 关键讨论内容:\n"
        for i, discussion in enumerate(analysis_result['key_discussions'][:8], 1):
            time_str = datetime.fromtimestamp(discussion['time']).strftime('%m-%d %H:%M')
            report += f"{i}. {discussion['sender']} ({time_str}): {discussion['content']}\n"
        
        report += "\n🔗 讨论会话:\n"
        for i, session in enumerate(analysis_result['discussion_sessions'][:5], 1):
            start_time = datetime.fromtimestamp(session['start_time']).strftime('%m-%d %H:%M')
            end_time = datetime.fromtimestamp(session['end_time']).strftime('%H:%M')
            status = "已完成" if session['status']['is_completed'] else "未完成"
            result = session['status']['result_summary']
            
            report += f"会话 {i} ({session['message_count']}条消息, {start_time}-{end_time}, {status}):\n"
            report += f"  结果: {result}\n"
            
            for j, msg in enumerate(session['messages'][:5], 1):
                time_str = datetime.fromtimestamp(msg['time']).strftime('%H:%M')
                report += f"  {j}. {msg['sender']} ({time_str}): {msg['content']}\n"
            report += "\n"
        
        return report
