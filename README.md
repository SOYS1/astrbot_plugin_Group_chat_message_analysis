# AstrBot 群聊消息关键词分析插件

根据指定关键词分析群聊中相关话题的讨论内容，并生成可视化报告。

## 功能

- 根据关键词筛选群聊消息
- 分析话题参与者的活跃度
- 统计消息的时间分布
- 生成可视化图片报告
- 支持智能话题总结（需要LLM支持）

## 安装

1. 将此插件文件夹复制到 AstrBot 的 plugins 目录
2. 重启 AstrBot

## 使用

在群聊中发送命令：
```
/分析 [关键词] [天数]
```

例如：
- `/分析 吃饭` - 分析最近2天关于"吃饭"的讨论
- `/分析 电影 3` - 分析最近3天关于"电影"的讨论

## 配置

插件支持以下配置项：

- `analysis_days`: 默认分析天数（默认：2）
- `max_messages`: 最大分析消息数量（默认：500）
- `enable_llm_analysis`: 启用LLM分析（默认：true）
- `max_query_rounds`: 最大消息查询轮数（默认：10）

## 开发

插件采用模块化设计，包含以下模块：

- `core/message_handler.py`: 消息处理模块
- `analysis/topic_analyzer.py`: 话题分析模块
- `visualization/report_generator.py`: 报告生成模块