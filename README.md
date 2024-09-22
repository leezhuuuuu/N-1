以下是为您的程序编写的全面 Markdown 文档：

# 多模型聊天完成 API

## 简介

这是一个基于 Flask 的 Web 应用程序，它提供了一个 API 端点来处理聊天完成请求。该程序的主要特点是并行查询多个语言模型，然后使用一个摘要模型来综合这些响应，提供一个全面的答案。

## 功能特点

1. 并行查询多个语言模型
2. 使用摘要模型综合多个模型的回答
3. 支持流式和非流式输出
4. 可配置的模型参数和端点

## 安装

1. 确保您已安装 Python 3.7+
2. 克隆此仓库到本地
3. 安装所需依赖：

```bash
pip install flask requests flask-sse
```

## 配置

程序使用 `config.json` 文件进行配置。该文件应包含以下结构：

```json
{
    "models": [
        {
            "endpoint": "模型API端点",
            "bearer_token": "认证令牌",
            "model_name": "模型名称",
            "temperature": 温度值
        },
        // 可以添加多个模型配置
    ],
    "summary_model": {
        "endpoint": "摘要模型API端点",
        "bearer_token": "认证令牌",
        "model_name": "摘要模型名称",
        "temperature": 温度值,
        "summary_prompt": "摘要提示词"
    }
}
```

## 使用方法

1. 运行程序：

```bash
python app.py
```

2. 程序将在 `http://0.0.0.0:8888` 上启动

3. 发送 POST 请求到 `/v1/chat/completions` 端点，请求体格式如下：

```json
{
    "messages": [
        {"role": "user", "content": "用户问题"}
    ],
    "stream": true或false
}
```

## API 端点

### POST /v1/chat/completions

处理聊天完成请求。

#### 请求参数

- `messages`: 聊天消息数组
- `stream`: 布尔值，指定是否使用流式输出

#### 响应

- 如果 `stream` 为 `false`，返回 JSON 格式的完整响应
- 如果 `stream` 为 `true`，返回 Server-Sent Events 格式的流式响应

## 工作流程

1. 接收客户端请求
2. 并行查询配置的多个语言模型
3. 收集并整合所有模型的响应
4. 将整合的响应和用户问题发送给摘要模型
5. 根据请求的 `stream` 参数，以流式或非流式方式返回摘要模型的响应

## 错误处理

程序包含基本的错误处理机制，主要处理 JSON 解析错误和 API 请求异常。

## 注意事项

- 确保 `config.json` 文件使用 UTF-8 编码保存
- 需要有可用的 Redis 服务器用于 SSE 功能
- 请确保所有 API 端点和认证令牌都是有效的

## 扩展性

- 可以通过修改 `config.json` 文件轻松添加或更改模型
- 可以通过调整代码来增加更多的错误处理和日志记录

## 贡献

欢迎提交 issues 和 pull requests 来改进这个项目。

## 许可证

[在此处添加您的许可证信息]