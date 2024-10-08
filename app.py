from flask import Flask, request, Response, jsonify
import requests
import json
import threading
import time
import queue
import yaml

app = Flask(__name__)

# 加载配置文件
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

API_BEARER_TOKEN = config.get('api_bearer_token')

STREAM_STATUS_FEEDBACK = config.get('stream_status_feedback', True)

def verify_token(token):
    return token == API_BEARER_TOKEN

def request_model(model_config, messages, result_queue):
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
    timeout = model_config.get('timeout', 120)  # 新增，默认超时时间为120秒
    
    for attempt in range(max_retries):
        try:
            response = requests.post(model_config['endpoint'], headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            result_queue.put((model_config['model_name'], response))
            return
        except (requests.RequestException, requests.Timeout) as e:
            if attempt == max_retries - 1:
                print(f"Error requesting model {model_config['model_name']} after {max_retries} attempts: {e}")
                result_queue.put((model_config['model_name'], None))
            time.sleep(1)  # 在重试之前等待1秒

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
    
    if stream:
        def generate():
            yield 'data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n'
            
            result_queue = queue.Queue()
            threads = []
            results = []
            
            for model_config in config['models']:
                thread = threading.Thread(target=request_model, args=(model_config, messages, result_queue))
                threads.append(thread)
                thread.start()
            
            models_count = len(config['models'])
            for _ in range(models_count):
                model_name, result = result_queue.get()
                if result is not None:
                    results.append(result)
                    if STREAM_STATUS_FEEDBACK:
                        yield f'data: {{"choices":[{{"delta":{{"content":"{model_name} ✅\\n"}},"index":0}}]}}\n\n'
                elif STREAM_STATUS_FEEDBACK:
                    yield f'data: {{"choices":[{{"delta":{{"content":"{model_name} ❌\\n"}},"index":0}}]}}\n\n'
            
            for thread in threads:
                thread.join()
            
            # 处理总结模型的输出
            try:
                summary_input = prepare_summary_input(results, messages[-1]['content'])
                summary_model_config = config['summary_model']
                
                response = requests.post(summary_model_config['endpoint'], 
                                         headers=get_headers(summary_model_config), 
                                         json=get_payload(summary_model_config, summary_input, True), 
                                         stream=True, 
                                         timeout=300)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.strip() == "data: [DONE]":
                            continue  # 跳过总结模型返回的 [DONE]
                        yield f"{decoded_line}\n\n"
                
                # 添加额外的数据块
                yield 'data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
            except Exception as e:
                print(f"Error in streaming summary: {e}")
                yield f'data: {{"choices":[{{"delta":{{"content":"Error: Summary generation failed - {str(e)}"}},"index":0}}]}}\n\n'
            
            yield "data: [DONE]\n\n"
        
        return Response(generate(), content_type='text/event-stream')
    else:
        # 非流式输出
        result_queue = queue.Queue()
        threads = []
        results = []
        
        for model_config in config['models']:
            thread = threading.Thread(target=request_model, args=(model_config, messages, result_queue))
            threads.append(thread)
            thread.start()
        
        models_count = len(config['models'])
        for _ in range(models_count):
            _, result = result_queue.get()
            if result is not None:
                results.append(result)
        
        for thread in threads:
            thread.join()
        
        # 整合结果
        summary_input = prepare_summary_input(results, messages[-1]['content'])
        
        # 请求总结模型
        summary_model_config = config['summary_model']
        try:
            response = requests.post(summary_model_config['endpoint'], 
                                     headers=get_headers(summary_model_config), 
                                     json=get_payload(summary_model_config, summary_input, False), 
                                     timeout=300)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, requests.Timeout) as e:
            print(f"Error in non-streaming summary: {e}")
            return {"error": f"Summary generation failed: {str(e)}"}, 500

def prepare_summary_input(results, user_question):
    combined_content = []
    for i, result in enumerate(results):
        try:
            content = result.json()['choices'][0]['message']['content']
            combined_content.append(f"参考回答{i+1}: {content} \n\n")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error processing result from model {i+1}: {e}")
            continue
    
    combined_content.append(f"用户的问题是：{user_question} \n\n")
    combined_content.append(config['summary_model']['summary_prompt'])
    return "\n".join(combined_content)

def get_headers(model_config):
    return {
        'Authorization': f"Bearer {model_config['bearer_token']}",
        'Content-Type': 'application/json'
    }

def get_payload(model_config, content, stream):
    return {
        "model": model_config['model_name'],
        "messages": [{"role": "user", "content": content}],
        "stream": stream,
        "temperature": model_config.get('temperature', 0.7)
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888)