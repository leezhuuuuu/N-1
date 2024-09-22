# N-1: Multi-Model Chat Completion API 🚀

[English](README_EN.md) | [中文](README.md)

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## Overview 🌟

N-1 is a Flask-based web application that provides a powerful API for handling chat completion requests. The project's uniqueness lies in its ability to query multiple language models in parallel and then synthesize these responses using a summary model, providing comprehensive and accurate answers. This innovative approach makes N-1 an ideal tool for AI developers and researchers, particularly suitable for scenarios requiring the synthesis of multiple model perspectives.

## Tech Stack 🛠️

- **Backend Framework**: Flask (Python)
- **Concurrent Processing**: threading
- **External Requests**: requests
- **Configuration Management**: YAML
- **Streaming Output**: Server-Sent Events (SSE)

## Features 🌈

- **Multi-Model Parallel Querying**: Simultaneously send requests to multiple language models, improving efficiency and diversity.
- **Summary Model Integration**: Use a dedicated summary model to synthesize responses from multiple models.
- **Streaming and Non-Streaming Output**: Support for both output modes to meet different needs.
- **Configurable Model Parameters**: Easily manage parameters for multiple models through a YAML configuration file.
- **Bearer Token Authentication**: Ensure secure API access.
- **Error Retry Mechanism**: Improve system stability and reliability.
- **Timeout Control**: Prevent long-running requests from affecting system performance.
- **Streaming Status Feedback**: Real-time feedback on the response status of each model.

## Environment Requirements 🖥️

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

Edit the `config.yaml` file to configure your model parameters and API token. Example configuration:

```yaml
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
```

### 4. Start the Project

```bash
python app.py
```

The service will start on `http://0.0.0.0:18888`.

## Usage Guide 📖

### Sending Chat Completion Requests

Send a POST request to the `/v1/chat/completions` endpoint with the following JSON data:

```json
{
    "messages": [
        {"role": "user", "content": "Your question"}
    ],
    "stream": true or false
}
```

Make sure to include the correct Bearer Token in the request header.

## API Endpoint 🌐

### `POST /v1/chat/completions`

Handles chat completion requests.

#### Request Headers

```
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

#### Request Body

```json
{
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
```

#### Response

For non-streaming requests, returns a JSON format response.
For streaming requests, returns data in SSE format.

## Error Handling 🚨

- **401 Unauthorized**: Invalid Bearer Token.
- **500 Internal Server Error**: Server internal error.

## Concurrency Management 🔄

The application uses a thread pool to handle multiple concurrent requests, ensuring efficient performance.

## License 📄

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributions 🤝

Contributions are welcome! Please submit issues or pull requests.

## Author ✍️

- leezhuuuuu

## Acknowledgements 🙏

- Flask
- Requests
- PyYAML

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/N-1&type=Date)](https://star-history.com/#leezhuuuuu/N-1&Date)