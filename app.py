from flask import Flask, request, Response, jsonify
import requests
import json
import threading
from flask_sse import sse
import time

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

# 加载配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

API_BEARER_TOKEN = config.get('api_bearer_token')

def verify_token(token):
    return token == API_BEARER_TOKEN

def request_model(model_config, messages):
    headers = {
        'Authorization': f"Bearer {model_config['bearer_token']}",
        'Content-Type': 'application/json'
    }
    payload = {
        "model": model_config['model_name'],
        "messages": messages,
        "stream": False,
        "temperature": model_config.get('temperature', 0.7)
    }
    
    max_retries = model_config.get('max_retries', 3)
    for attempt in range(max_retries):
        try:
            response = requests.post(model_config['endpoint'], headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response
        except (requests.RequestException, requests.Timeout) as e:
            if attempt == max_retries - 1:
                print(f"Error requesting model {model_config['model_name']} after {max_retries} attempts: {e}")
                return None
            time.sleep(1)  # 在重试之前等待1秒

    return None

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # 验证 bearer token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "未提供有效的 bearer token"}), 401
    
    token = auth_header.split(' ')[1]
    if not verify_token(token):
        return jsonify({"error": "无效的 bearer token"}), 401

    data = request.json
    messages = data['messages']
    stream = data.get('stream', False)
    
    threads = []
    results = []
    
    def fetch_model_response(model_config):
        result = request_model(model_config, messages)
        if result is not None:
            results.append(result)
    
    # 并行请求多个模型
    for model_config in config['models']:
        thread = threading.Thread(target=fetch_model_response, args=(model_config,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # 整合结果
    combined_content = []
    for i, result in enumerate(results):
        try:
            content = result.json()['choices'][0]['message']['content']
            combined_content.append(f"LLM {i+1}的回答: {content}")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error processing result from model {i+1}: {e}")
            continue
    
    user_question = messages[-1]['content']
    combined_content.append(f"用户的问题是：{user_question}")
    
    # 添加总结提示词
    combined_content.append(config['summary_model']['summary_prompt'])
    
    summary_input = "\n".join(combined_content)
    
    # 请求总结模型
    summary_model_config = config['summary_model']
    summary_headers = {
        'Authorization': f"Bearer {summary_model_config['bearer_token']}",
        'Content-Type': 'application/json'
    }
    summary_payload = {
        "model": summary_model_config['model_name'],
        "messages": [{"role": "user", "content": summary_input}],
        "stream": stream,
        "temperature": summary_model_config.get('temperature', 0.7)
    }
    
    if stream:
        # 流式输出总结结果
        def generate():
            try:
                response = requests.post(summary_model_config['endpoint'], headers=summary_headers, json=summary_payload, stream=True, timeout=300)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.strip() == 'data: [DONE]':
                            continue  # 跳过上游 API 的 [DONE] 信号
                        yield f"{decoded_line}\n\n"
                yield "data: [DONE]\n\n"
            except (requests.RequestException, requests.Timeout) as e:
                print(f"Error in streaming summary: {e}")
                yield f"data: {{\"error\": \"Summary generation failed: {str(e)}\"}}\n\n"
                yield "data: [DONE]\n\n"
        
        return Response(generate(), content_type='text/event-stream')
    else:
        # 非流式输出
        try:
            response = requests.post(summary_model_config['endpoint'], headers=summary_headers, json=summary_payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, requests.Timeout) as e:
            print(f"Error in non-streaming summary: {e}")
            return {"error": f"Summary generation failed: {str(e)}"}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888)