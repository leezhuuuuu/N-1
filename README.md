# N-1: 多模型聊天完成 API 🚀

[English](README_EN.md) | [中文](README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## 概述 🌟

N-1 是一个基于 Flask 的 Web 应用程序，提供强大的 API 接口用于处理聊天完成请求。该项目的独特之处在于能够并行查询多个语言模型，然后使用摘要模型综合这些响应，提供全面而准确的答案。这种创新方法使 N-1 成为 AI 开发者和研究人员的理想工具，特别适用于需要综合多个模型观点的场景。

## 技术栈 🛠️

- **后端框架**：Flask (Python)
- **并发处理**：threading
- **外部请求**：requests
- **配置管理**：YAML
- **流式输出**：Server-Sent Events (SSE)

## 特性 🌈

- **多模型并行查询**：同时向多个语言模型发送请求，提高效率和多样性。
- **摘要模型整合**：使用专门的摘要模型综合多个模型的回答。
- **流式和非流式输出**：支持两种输出模式，满足不同需求。
- **可配置的模型参数**：通过 YAML 配置文件轻松管理多个模型的参数。
- **Bearer Token 认证**：确保 API 的安全访问。
- **错误重试机制**：提高系统的稳定性和可靠性。
- **超时控制**：防止长时间运行的请求影响系统性能。
- **流式状态反馈**：实时反馈每个模型的响应状态。

## 运行环境 🖥️

- Python 3.7+

## 快速开始 🚀

### 1. 克隆项目

```bash
git clone https://github.com/leezhuuuuu/N-1.git
cd N-1
````

### 2. 安装依赖

````bash
pip install flask requests pyyaml
````

### 3. 配置文件

编辑 `config.yaml` 文件，配置您的模型参数和 API 令牌。示例配置如下：

````yaml
api_bearer_token: YOUR_API_BEARER_TOKEN
models:
  - endpoint: https://api.example.com/v1/chat/completions
    bearer_token: MODEL_BEARER_TOKEN
    model_name: ExampleModel
    temperature: 0.7
    max_retries: 3
    timeout: 150
summary_model:
  endpoint: https://api.example.com/v1/chat/completions
  bearer_token: SUMMARY_MODEL_BEARER_TOKEN
  model_name: SummaryModel
  temperature: 0.1
  summary_prompt: "Your summary prompt here"
  timeout: 150
stream_status_feedback: true
````

### 4. 启动项目

````bash
python app.py
````

服务将在 `http://0.0.0.0:18888` 上启动。

## 使用指南 📖

### 发送聊天完成请求

向 `/v1/chat/completions` 端点发送 POST 请求，包含以下 JSON 数据：

````json
{
    "messages": [
        {"role": "user", "content": "你的问题"}
    ],
    "stream": true或false
}
````

请确保在请求头中包含正确的 Bearer Token。

## API 端点 🌐

### `POST /v1/chat/completions`

处理聊天完成请求。

#### 请求头

````
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
````

#### 请求体

````json
{
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
````

#### 响应

对于非流式请求，返回JSON格式的响应。
对于流式请求，返回 SSE 格式的数据流。

## 错误处理 🚨

- **401 Unauthorized**：无效的 Bearer Token。
- **500 Internal Server Error**：服务器内部错误。

## 并发管理 🔄

应用程序使用线程池处理多个并发请求，确保高效的性能。

## 许可证 📄

本项目基于 MIT 许可证。详见 `LICENSE` 文件。

## 贡献 🤝

欢迎贡献！请提交问题或拉取请求。

## 作者 ✍️

- leezhuuuuu

## 致谢 🙏

- Flask
- Requests
- PyYAML

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/N-1&type=Date)](https://star-history.com/#leezhuuuuu/N-1&Date)
