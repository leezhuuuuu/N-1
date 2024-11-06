# N-1: Multi-Model Composite Chat Completion API 🚀

[中文](README.md) | [English](README_EN.md) | [Go](go/README.md) | [JavaScript](js/README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## Overview 🌟

N-1 is a Flask-based web application that provides powerful API interfaces for handling chat completion requests. The project supports multiple combination modes and allows users to choose between parallel analysis or direct processing modes. In parallel mode, the system can simultaneously query multiple large language models and use dedicated summary models to synthesize these responses, providing comprehensive and accurate answers. The project supports both text and visual multimodal processing, making it an ideal tool for AI developers and researchers.

## Demo API 🎮

You can test using the following Demo API address:
```
https://n_1.leez.tech/v1/chat/completions
```

### Single Model Call Example
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
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://global.discourse-cdn.com/openai1/original/4X/f/9/5/f95edd5d0d8848f9322525341bbfc3bf01a48057.png"}}
      ]
    }
  ],
  "max_tokens": 300,
  "model": "Qwen2.5-VL-72B",
  "stream": false
}'
```

### Multi-Model Combination Call Example
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
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://global.discourse-cdn.com/openai1/original/4X/f/9/5/f95edd5d0d8848f9322525341bbfc3bf01a48057.png"}}
      ]
    }
  ],
  "max_tokens": 300,
  "model": "N-1",
  "stream": false
}'
```

## Tech Stack 🛠️

- **Backend Framework**: Flask (Python)
- **Concurrent Processing**: threading, queue
- **External Requests**: requests
- **Configuration Management**: YAML
- **Streaming Output**: Server-Sent Events (SSE)

## Features 🌈

- **Composite Configuration**
  - Support for multiple preset combination modes
  - Independent parameter configuration for each combination
  - Flexible processing mode switching
  
- **Multi-Model Parallel Analysis**
  - Simultaneous calls to multiple language models
  - Support for text and visual processing
  - Professional summary model for result integration

- **Visual Processing Capabilities**
  - Support for image URLs and base64 format
  - Dedicated visual model processing
  - Configurable image detail levels

- **System Features**
  - Streaming and non-streaming output
  - Bearer Token authentication
  - Error retry mechanism
  - Timeout control
  - Real-time status feedback
  - Debug mode support

## Requirements 🖥️

- Python 3.7+

## Quick Start 🚀

### 1. Clone the Project

```bash
git clone https://github.com/leezhuuuuu/N-1.git
cd N-1
```

### 2. Install Dependencies

```bash
pip install flask requests pyyaml
```

### 3. Configuration File

Edit the `config.yaml` file to configure your combination parameters. Example configuration:

```yaml
# Global default configuration
default_combination: "parallel"  # Default combination name

# Model combination configuration
combinations:
  - name: "parallel"  # Parallel analysis combination
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
    # ... other configurations
```

### 4. Start the Project

```bash
python app.py
```

The service will start on `http://0.0.0.0:18888`.

## Usage Guide 📖

### Send Chat Completion Request

Send a POST request to the `/v1/chat/completions` endpoint:

```json
{
    "model": "parallel",  // Optional, uses default combination if not specified
    "messages": [
        {"role": "user", "content": "Your question"}
    ],
    "stream": true or false
}
```

### Visual Request Example

```json
{
    "model": "parallel",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
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

## Preset Combinations 📋

### Parallel Combination
- Parallel calls to multiple models
- Comprehensive result analysis
- Suitable for scenarios requiring comprehensive answers

### Direct Combination
- Smart combination mode:
  - Text requests: Uses high-performance LLM (e.g., Qwen2.5-72B-Instruct)
  - Visual requests: Automatically switches to vision model (e.g., Qwen2-VL-7B-Instruct)
- Features:
  - Single model processing, fast response
  - Intelligent request type recognition
  - High-performance multimodal capabilities through combination
- Use cases:
  - Daily conversations and consultations
  - Image analysis and understanding
  - Business scenarios requiring quick responses

### Combination Mode Comparison

| Feature | Parallel Mode | Direct Mode |
|---------|--------------|-------------|
| Processing Method | Multiple Models in Parallel | Single Model Smart Switch |
| Response Speed | Slower | Fast |
| Answer Quality | Comprehensive, Multi-perspective | Precise, Concise |
| Resource Consumption | Higher | Low |
| Suitable Scenarios | Deep Analysis Required | Daily Chat and Image Analysis |

### Direct Mode Examples

#### Text Request
```json
{
    "model": "direct",
    "messages": [
        {"role": "user", "content": "What is quantum computing?"}
    ],
    "stream": true
}
```

#### Visual Request
```json
{
    "model": "direct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
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

## Error Handling 🚨

- **401 Unauthorized**: Invalid Bearer Token
- **500 Internal Server Error**: Server Internal Error

## License 📄

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing 🤝

Contributions are welcome! Please submit issues or pull requests.

## Author ✍️

- leezhuuuuu

## Acknowledgments 🙏

- Flask
- Requests
- PyYAML

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/N-1&type=Date)](https://star-history.com/#leezhuuuuu/N-1&Date)