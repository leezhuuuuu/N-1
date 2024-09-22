# N-1: 多合一模型 API 🚀

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## 概述 🌟

N-1 是一个基于 Flask 的 Web 应用程序，旨在提供一个强大的 API 接口，用于处理聊天完成请求。该项目的独特之处在于它能够并行查询多个语言模型，然后使用一个摘要模型来综合这些响应，从而提供一个全面而准确的答案。这种创新方法使得 N-1 成为 AI 开发者和研究人员的理想工具，特别是在需要综合多个模型观点的场景中。

## 技术栈 🛠️

- **后端框架**：Flask (Python)
- **并发处理**：threading
- **外部请求**：requests
- **事件流**：flask-sse
- **配置管理**：JSON

## 特性 🌈

- **多模型并行查询**：同时向多个语言模型发送请求，提高效率和多样性。
- **摘要模型整合**：使用专门的摘要模型综合多个模型的回答。
- **流式和非流式输出**：根据客户端需求支持两种输出模式。
- **可配置的模型参数**：通过 JSON 配置文件轻松管理多个模型的参数。
- **Server-Sent Events 支持**：实现实时的流式数据传输。

## 运行环境 🖥️

- Python 3.7+
- Redis（用于 SSE 功能）

## 快速开始 🚀

### 1. 克隆项目

```bash
git clone https://github.com/leezhuuuuu/N-1.git
cd N-1
```

### 2. 安装依赖

```bash
pip install flask requests flask-sse
```

### 3. 配置文件

编辑 `config.json` 文件，配置您的模型参数：

```json
{
    "models": [
        {
            "endpoint": "https://api.example.com/v1/chat/completions",
            "bearer_token": "your_bearer_token_here",
            "model_name": "model_1",
            "temperature": 0.7
        },
        // 添加更多模型...
    ],
    "summary_model": {
        "endpoint": "https://api.example.com/v1/chat/completions",
        "bearer_token": "your_bearer_token_here",
        "model_name": "summary_model",
        "temperature": 0.7,
        "summary_prompt": "请根据以上多个模型的回答，综合分析并给出一个全面、准确的回答。注意要考虑到所有模型的观点，并给出一个平衡的总结。"
    }
}
```

### 4. 启动项目

```bash
python app.py
```

服务将在 `http://0.0.0.0:8888` 上启动。

## 使用指南 📖

### 发送聊天完成请求

向 `/v1/chat/completions` 端点发送 POST 请求：

```json
{
    "messages": [
        {"role": "user", "content": "你的问题"}
    ],
    "stream": true或false
}
```

## API 端点 🌐

### `POST /v1/chat/completions`

处理聊天完成请求。

#### 请求

```json
{
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
```

#### 响应

```json
{
    "choices": [
        {
            "message": {
                "content": "The capital of France is Paris. Paris is not only the political capital but also the cultural and economic center of France. It is known for its iconic landmarks such as the Eiffel Tower, the Louvre Museum, and Notre-Dame Cathedral. Paris has a rich history dating back to ancient times and has played a significant role in European art, fashion, and cuisine."
            }
        }
    ]
}
```

## 错误处理 🚨

应用程序返回适当的 HTTP 状态码和错误消息：

- **400 Bad Request**：无效的 JSON 或参数。
- **500 Internal Server Error**：服务器内部错误。

## 并发管理 🔄

应用程序使用线程处理多个并发请求，确保高效的性能。

## 许可证 📄

本项目基于 MIT 许可证。详见 `LICENSE` 文件。

## 贡献 🤝

欢迎贡献！请提交问题或拉取请求。

## 作者 ✍️

- leezhuuuuu

## 致谢 🙏

- Flask
- Requests
- Flask-SSE

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/N-1&type=Date)](https://star-history.com/#leezhuuuuu/N-1&Date)