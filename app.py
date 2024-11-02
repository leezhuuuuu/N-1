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

def debug_print(message, data=None):
    """调试信息打印函数"""
    if config.get('debug_mode', False):
        print(f"\n[DEBUG] {message}")
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        print("-" * 50)

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
    
    debug_print(f"Requesting {model_config['model_name']}", {
        "endpoint": model_config['endpoint'],
        "headers": headers,
        "payload": payload
    })
    
    max_retries = model_config.get('max_retries', 3)
    timeout = model_config.get('timeout', 120)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(model_config['endpoint'], headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            debug_print(f"Response from {model_config['model_name']}", response.json())
            
            result_queue.put((model_config['model_name'], response))
            return
        except (requests.RequestException, requests.Timeout) as e:
            if attempt == max_retries - 1:
                print(f"Error requesting model {model_config['model_name']} after {max_retries} attempts: {e}")
                result_queue.put((model_config['model_name'], None))
            time.sleep(1)

def prepare_summary_input(results, messages):
    debug_print("Preparing summary input", {
        "messages": messages,
        "results_count": len(results)
    })
    
    # 1. 保留历史消息（如果启用）
    summary_messages = messages[:-1] if config['summary_model'].get('keep_history', False) else []
    
    # 2. 收集所有模型的回答，放入一个 assistant 消息中
    reference_answers = []
    for i, result in enumerate(results):
        try:
            content = result.json()['choices'][0]['message']['content']
            reference_answers.append(f"参考回答{i+1}: {content}")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error processing result from model {i+1}: {e}")
            continue
    
    # 添加参考回答作为 assistant 消息
    summary_messages.append({
        "role": "assistant",
        "content": "\n\n".join(reference_answers)
    })
    
    # 3. 添加当前问题和总结提示词作为 user 消息
    summary_messages.append({
        "role": "user",
        "content": f"当前问题：{messages[-1]['content']}\n\n{config['summary_model']['summary_prompt']}"
    })
    
    debug_print("Summary messages prepared", summary_messages)
    return summary_messages

def get_headers(model_config):
    return {
        'Authorization': f"Bearer {model_config['bearer_token']}",
        'Content-Type': 'application/json'
    }

def get_payload(model_config, messages, stream):
    """修改后的 get_payload 函数"""
    return {
        "model": model_config['model_name'],
        "messages": messages if isinstance(messages, list) else [
            {"role": "user", "content": messages}
        ],
        "stream": stream,
        "temperature": model_config.get('temperature', 0.7)
    }

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    debug_print("Received request", {
        "headers": dict(request.headers),
        "body": request.json
    })
    
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
            debug_print("Starting stream response")
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
                summary_messages = prepare_summary_input(results, messages)
                summary_model_config = config['summary_model']
                
                payload = get_payload(summary_model_config, summary_messages, True)
                debug_print("Summary model request", {
                    "endpoint": summary_model_config['endpoint'],
                    "headers": get_headers(summary_model_config),
                    "payload": payload
                })
                
                response = requests.post(
                    summary_model_config['endpoint'], 
                    headers=get_headers(summary_model_config), 
                    json=payload, 
                    stream=True, 
                    timeout=summary_model_config.get('timeout', 300)
                )
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.strip() == "data: [DONE]":
                            continue
                        yield f"{decoded_line}\n\n"
                
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
        
        # 准备总结输入
        summary_messages = prepare_summary_input(results, messages)
        
        # 请求总结模型
        summary_model_config = config['summary_model']
        try:
            payload = get_payload(summary_model_config, summary_messages, False)
            debug_print("Summary model request", {
                "endpoint": summary_model_config['endpoint'],
                "headers": get_headers(summary_model_config),
                "payload": payload
            })
            
            response = requests.post(
                summary_model_config['endpoint'], 
                headers=get_headers(summary_model_config), 
                json=payload, 
                timeout=summary_model_config.get('timeout', 300)
            )
            response.raise_for_status()
            
            result = response.json()
            debug_print("Final response", result)
            return result
        except (requests.RequestException, requests.Timeout) as e:
            error_msg = f"Summary generation failed: {str(e)}"
            debug_print("Error", {"error": error_msg})
            return {"error": error_msg}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888)