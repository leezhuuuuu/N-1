# N-1: Multi-Model Chat Completion API 🚀

[![](https://img.shields.io/github/license/leezhuuuuu/N-1.svg)](LICENSE)
![](https://img.shields.io/github/stars/leezhuuuuu/N-1.svg)
![](https://img.shields.io/github/forks/leezhuuuuu/N-1.svg)

## Overview 🌟

N-1 is a Flask-based web application designed to provide a powerful API interface for handling chat completion requests. The project's uniqueness lies in its ability to query multiple language models in parallel and then use a summary model to synthesize these responses, delivering a comprehensive and accurate answer. This innovative approach makes N-1 an ideal tool for AI developers and researchers, especially in scenarios requiring the synthesis of multiple model perspectives.

## Tech Stack 🛠️

- **Backend Framework**: Flask (Python)
- **Concurrent Processing**: threading
- **External Requests**: requests
- **Event Streaming**: flask-sse
- **Configuration Management**: JSON

## Features 🌈

- **Multi-Model Parallel Querying**: Simultaneously send requests to multiple language models, improving efficiency and diversity.
- **Summary Model Integration**: Use a dedicated summary model to synthesize responses from multiple models.
- **Streaming and Non-Streaming Output**: Support both output modes based on client requirements.
- **Configurable Model Parameters**: Easily manage parameters for multiple models through a JSON configuration file.
- **Server-Sent Events Support**: Implement real-time streaming data transmission.

## Runtime Environment 🖥️

- Python 3.7+
- Redis (for SSE functionality)

## Quick Start 🚀

### 1. Clone the Project

```bash
git clone https://github.com/leezhuuuuu/N-1.git
cd N-1
```

### 2. Install Dependencies

```bash
pip install flask requests flask-sse
```

### 3. Configuration File

Edit the `config.json` file to configure your model parameters:

```json
{
    "models": [
        {
            "endpoint": "https://api.example.com/v1/chat/completions",
            "bearer_token": "your_bearer_token_here",
            "model_name": "model_1",
            "temperature": 0.7
        },
        // Add more models...
    ],
    "summary_model": {
        "endpoint": "https://api.example.com/v1/chat/completions",
        "bearer_token": "your_bearer_token_here",
        "model_name": "summary_model",
        "temperature": 0.7,
        "summary_prompt": "Based on the responses from multiple models above, please provide a comprehensive and accurate answer. Consider all model perspectives and give a balanced summary."
    }
}
```

### 4. Launch the Project

```bash
python app.py
```

The service will start on `http://0.0.0.0:8888`.

## Usage Guide 📖

### Sending Chat Completion Requests

Send a POST request to the `/v1/chat/completions` endpoint:

```json
{
    "messages": [
        {"role": "user", "content": "Your question"}
    ],
    "stream": true or false
}
```

## API Endpoints 🌐

### `POST /v1/chat/completions`

Handles chat completion requests.

#### Request

```json
{
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "stream": false
}
```

#### Response

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

## Error Handling 🚨

The application returns appropriate HTTP status codes and error messages:

- **400 Bad Request**: Invalid JSON or parameters.
- **500 Internal Server Error**: Server-side error.

## Concurrency Management 🔄

The application uses threads to handle multiple concurrent requests, ensuring efficient performance.

## License 📄

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributions 🤝

Contributions are welcome! Please submit issues or pull requests.

## Author ✍️

- leezhuuuuu

## Acknowledgements 🙏

- Flask
- Requests
- Flask-SSE

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=leezhuuuuu/N-1&type=Date)](https://star-history.com/#leezhuuuuu/N-1&Date)