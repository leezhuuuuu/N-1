# N-1: 多模型组合式聊天完成 API 🚀

[中文](README.md) | [English](README_EN.md) | [Go](go/README.md) | [JavaScript](js/README.md) | [CF_worker](cloudfare_worker/README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## 概述 🌟

N-1 是一个基于 Flask 的 Web 应用程序，提供强大的 API 接口用于处理聊天完成请求。该项目支持多种组合模式，可以根据需求选择并行分析或直接处理模式。在并行模式下，系统能够同时查询多个大语言模型，并使用专门的摘要模型综合这些响应，提供全面而准确的答案。项目支持文本和视觉多模态处理，是 AI 开发者和研究人员的理想工具。

## Demo API 🎮

您可以使用以下 Demo API 地址进行测试:
```
https://n_1.leez.tech/v1/chat/completions
```

### 单模型调用示例
```bash
curl --location --request POST 'https://n_1.leez.tech/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer ilovelinuxdo' \
--header 'Accept: */*' \
--header 'Connection: keep-alive' \
--data-raw '{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "这是什么图片？"},
        {"type": "image_url", "image_url": {"url": "https://global.discourse-cdn.com/openai1/original/4X/f/9/5/f95edd5d0d8848f9322525341bbfc3bf01a48057.png"}}
      ]
    }
  ],
  "max_tokens": 300,
  "model": "Qwen2.5-VL-72B",
  "stream": false
}'
```

### 多模型组合调用示例
```bash
curl --location --request POST 'https://n_1.leez.tech/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer ilovelinuxdo' \
--header 'Accept: */*' \
--header 'Connection: keep-alive' \
--data-raw '{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "这是什么图片？"},
        {"type": "image_url", "image_url": {"url": "https://global.discourse-cdn.com/openai1/original/4X/f/9/5/f95edd5d0d8848f9322525341bbfc3bf01a48057.png"}}
      ]
    }
  ],
  "max_tokens": 300,
  "model": "N-1",
  "stream": false
}'
```

## 技术栈 🛠️

- **后端框架**：Flask (Python)
- **并发处理**：threading, queue
- **外部请求**：requests
- **配置管理**：YAML
- **流式输出**：Server-Sent Events (SSE)

## 特性 🌈

- **组合式配置**
  - 支持多种预设组合模式
  - 每个组合可独立配置所有参数
  - 灵活切换处理模式
  
- **多模型并行分析**
  - 同时调用多个语言模型
  - 支持文本和视觉处理
  - 专业的摘要模型整合结果

- **视觉处理能力**
  - 支持图片 URL 和 base64 格式
  - 专门的视觉模型处理
  - 可配置图片细节级别

- **系统功能**
  - 流式和非流式输出
  - Bearer Token 认证
  - 错误重试机制
  - 超时控制
  - 实时状态反馈
  - 调试模式支持

## 运行环境 🖥️

- Python 3.7+

## 快速开始 🚀

### 1. 克隆项目

```bash
git clone https://github.com/leezhuuuuu/N-1.git
cd N-1
```

### 2. 安装依赖

```bash
pip install flask requests pyyaml
```

### 3. 配置文件

编辑 `config.yaml` 文件，配置您的组合参数。示例配置如下：

```yaml
# 全局默认配置
default_combination: "parallel"  # 默认使用的组合名称

# 模型组合配置
combinations:
  - name: "parallel"  # 并行分析组合
    api_bearer_token: YOUR_API_BEARER_TOKEN
    stream_status_feedback: true
    use_parallel_analysis: true
    debug_mode: true
    text_models:
      - endpoint: https://api.example.com/v1/chat/completions
        bearer_token: MODEL_BEARER_TOKEN
        model_name: ExampleModel
        temperature: 0.7
        max_retries: 3
        timeout: 150
    # ... 其他配置
```

### 4. 启动项目

```bash
python app.py
```

服务将在 `http://0.0.0.0:18888` 上启动。

## 使用指南 📖

### 发送聊天完成请求

向 `/v1/chat/completions` 端点发送 POST 请求：

```json
{
    "model": "parallel",  // 可选，不填则使用默认组合
    "messages": [
        {"role": "user", "content": "你的问题"}
    ],
    "stream": true或false
}
```

### 视觉请求示例

```json
{
    "model": "parallel",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这张图片是什么？"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "auto"
                    }
                }
            ]
        }
    ],
    "stream": true
}
```

## 预设组合说明 📋

### parallel 组合
- 并行调用多个模型
- 综合分析结果
- 适合需要全面答案的场景

### direct 组合
- 智能组合模式：
  - 文本请求：使用高性能大语言模型（如 Qwen2.5-72B-Instruct）
  - 视觉请求：自动切换到视觉模型（如 Qwen2-VL-7B-Instruct）
- 特点：
  - 单一模型处理，响应速度快
  - 智能识别请求类型
  - 通过组合实现高性能多模态能力
- 使用场景：
  - 日常对话和咨询
  - 图片分析和理解
  - 需要快速响应的业务场景

### 组合模式对比

| 特性 | parallel 模式 | direct 模式 |
|------|--------------|------------|
| 处理方式 | 多模型并行 | 单模型智能切换 |
| 响应速度 | 较慢 | 快速 |
| 答案质量 | 全面、多角度 | 精准、简洁 |
| 资源消耗 | 较高 | 低 |
| 适用场景 | 需要深度分析 | 日常对话和图片分析 |

### direct 模式示例

#### 文本请求
```json
{
    "model": "direct",
    "messages": [
        {"role": "user", "content": "什么是量子计算？"}
    ],
    "stream": true
}
```

#### 视觉请求
```json
{
    "model": "direct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这张图片里有什么？"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "auto"
                    }
                }
            ]
        }
    ],
    "stream": true
}
```

## 错误处理 🚨

- **401 Unauthorized**：无效的 Bearer Token
- **500 Internal Server Error**：服务器内部错误

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