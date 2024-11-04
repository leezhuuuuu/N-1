# N-1: Multi-Model Combination Chat Completion API 🚀

[English](README_EN.md) | [中文](README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## Overview 🌟

N-1 is a Flask-based web application that provides a powerful API for handling chat completion requests. The project supports multiple combination modes, allowing you to choose between parallel analysis or direct processing based on your needs. In parallel mode, the system can query multiple large language models simultaneously and use a dedicated summary model to synthesize these responses, providing comprehensive and accurate answers. The project supports both text and visual multimodal processing, making it an ideal tool for AI developers and researchers.

## Tech Stack 🛠️

- **Backend Framework**: Flask (Python)
- **Concurrent Processing**: threading, queue
- **External Requests**: requests
- **Configuration Management**: YAML
- **Streaming Output**: Server-Sent Events (SSE)

## Features 🌈

- **Combination Configuration**
  - Supports multiple preset combination modes
  - Each combination can independently configure all parameters
  - Flexible switching of processing modes
  
- **Multi-Model Parallel Analysis**
  - Simultaneously invoke multiple language models
  - Supports text and visual processing
  - Professional summary model to integrate results

- **Visual Processing Capability**
  - Supports image URLs and base64 formats
  - Dedicated visual model processing
  - Configurable image detail levels

- **System Functions**
  - Streaming and non-streaming output
  - Bearer Token authentication
  - Error retry mechanism
  - Timeout control
  - Real-time status feedback
  - Debug mode support

## Environment 🖥️

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

The service will start at `http://0.0.0.0:18888`.

## Usage Guide 📖

### Send a Chat Completion Request

Send a POST request to the `/v1/chat/completions` endpoint:

```json
{
    "model": "parallel",  // Optional, defaults to the default combination
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
                    "text": "What is in this image?"
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

## Preset Combination Descriptions 📋

### parallel Combination
- Invokes multiple models in parallel
- Integrates results comprehensively
- Suitable for scenarios requiring comprehensive answers

### direct Combination
- Intelligent combination mode:
  - Text requests: Use high-performance large language models (e.g., Qwen2.5-72B-Instruct)
  - Visual requests: Automatically switch to visual models (e.g., Qwen2-VL-7B-Instruct)
- Features:
  - Single model processing, fast response
  - Intelligent request type recognition
  - Achieves high-performance multimodal capability through combination
- Use Cases:
  - Daily conversations and inquiries
  - Image analysis and understanding
  - Business scenarios requiring quick responses

### Combination Mode Comparison

| Feature | parallel Mode | direct Mode |
|---------|---------------|-------------|
| Processing Method | Multi-model parallel | Single model intelligent switch |
| Response Speed | Slower | Fast |
| Answer Quality | Comprehensive, multi-angle | Precise, concise |
| Resource Consumption | Higher | Low |
| Suitable Scenarios | Requires deep analysis | Daily conversations and image analysis |

### direct Mode Example

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
                    "text": "What is in this image?"
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
- **500 Internal Server Error**: Internal server error

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