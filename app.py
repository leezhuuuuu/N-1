from flask import Flask, request, Response, jsonify
import requests
import json
import threading
import time
import queue
import yaml
from typing import Dict, List, Tuple, Optional, Union

app = Flask(__name__)

# 加载配置文件
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

API_BEARER_TOKEN = config.get('api_bearer_token')
STREAM_STATUS_FEEDBACK = config.get('stream_status_feedback', True)

class ImageProcessor:
    @staticmethod
    def process_vision_messages(messages: List[Dict]) -> List[Dict]:
        """处理视觉消息，支持URL和base64格式"""
        processed_messages = []
        for message in messages:
            if isinstance(message.get('content'), list):
                new_content = []
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        url = item['image_url'].get('url', '')
                        if ImageProcessor.validate_image_url(url):
                            if url.startswith('data:image/'):
                                # 处理base64片
                                new_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": url,
                                        "detail": item['image_url'].get('detail', 'auto')
                                    }
                                })
                            else:
                                # 处理HTTP(S)图片URL
                                new_content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": url,
                                        "detail": item['image_url'].get('detail', 'auto')
                                    }
                                })
                    else:
                        new_content.append(item)
                message['content'] = new_content
            processed_messages.append(message)
        return processed_messages

    @staticmethod
    def validate_image_url(url: str) -> bool:
        """验证图片URL格式，支持base64和HTTP(S)链接"""
        if url.startswith('data:image/'):
            try:
                # 验证base64格式
                header, base64_data = url.split(',', 1)
                format_type = header.split(';')[0].split('/')[1]
                # 可以添加支持的图片格式验证
                supported_formats = {'jpeg', 'png', 'gif', 'webp'}
                if format_type not in supported_formats:
                    print(f"不支持的图片格式: {format_type}")
                    return False
                return True
            except Exception as e:
                print(f"Base64图片格式验证失败: {str(e)}")
                return False
        elif url.startswith(('http://', 'https://')):
            # 可以添加URL格式的其他验证
            return True
        return False

    @staticmethod
    def is_vision_request(messages: List[Dict]) -> bool:
        """检查是否为视觉请求"""
        for message in messages:
            if isinstance(message.get('content'), list):
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        return True
        return False

class ModelManager:
    def __init__(self, config: Dict):
        self.config = config
        self.combinations = {combo['name']: combo for combo in config.get('combinations', [])}
        self.default_combination = config.get('default_combination', 'parallel')

    def get_combination_config(self, model_name: Optional[str] = None) -> Dict:
        """获取指定组合的配置"""
        combination_name = model_name or self.default_combination
        return self.combinations.get(combination_name, self.combinations[self.default_combination])

    def get_models_config(self, is_vision: bool, model_name: Optional[str] = None) -> Tuple[List[Dict], Dict, Dict]:
        """获取对应类型的模型配置、总结模型和组合配置"""
        combination = self.get_combination_config(model_name)
        
        if is_vision:
            return (
                combination.get('vision_models', []),
                combination.get('vision_summary_model', {}),
                combination
            )
        return (
            combination.get('text_models', []),
            combination.get('text_summary_model', {}),
            combination
        )

    @staticmethod
    def get_headers(model_config: Dict) -> Dict:
        """获取请求头"""
        return {
            'Authorization': f"Bearer {model_config['bearer_token']}",
            'Content-Type': 'application/json'
        }

    @staticmethod
    def get_payload(model_config: Dict, messages: Union[List, str], stream: bool) -> Dict:
        """获取请求负载"""
        return {
            "model": model_config['model_name'],
            "messages": messages if isinstance(messages, list) else [
                {"role": "user", "content": messages}
            ],
            "stream": stream,
            "temperature": model_config.get('temperature', 0.7)
        }

def debug_print(message: str, data: Optional[Dict] = None, debug_mode: bool = False) -> None:
    """调试信息打印"""
    if debug_mode:
        print(f"\n[DEBUG] {message}")
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        print("-" * 50)

def request_model(model_config: Dict, messages: List[Dict], result_queue: queue.Queue, debug_mode: bool) -> None:
    """请求单个模型"""
    headers = ModelManager.get_headers(model_config)
    payload = ModelManager.get_payload(model_config, messages, False)
    
    debug_print(f"Requesting {model_config['model_name']}", {
        "endpoint": model_config['endpoint'],
        "headers": headers,
        "payload": payload
    }, debug_mode)
    
    max_retries = model_config.get('max_retries', 3)
    timeout = model_config.get('timeout', 120)
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                model_config['endpoint'], 
                headers=headers, 
                json=payload, 
                timeout=timeout
            )
            response.raise_for_status()
            
            debug_print(f"Response from {model_config['model_name']}", response.json(), debug_mode)
            result_queue.put((model_config['model_name'], response))
            return
        except (requests.RequestException, requests.Timeout) as e:
            if attempt == max_retries - 1:
                print(f"Error requesting model {model_config['model_name']} after {max_retries} attempts: {e}")
                result_queue.put((model_config['model_name'], None))
            time.sleep(1)

def prepare_summary_input(results: List[requests.Response], messages: List[Dict], summary_model: Dict) -> List[Dict]:
    """准备总结模型的输入"""
    debug_print("Preparing summary input", {
        "messages": messages,
        "results_count": len(results)
    })
    
    summary_messages = []
    
    # 1. 首先添加历史消息（如果启用）
    if summary_model.get('keep_history', False):
        summary_messages.extend(messages[:-1])
    
    # 2. 添加参考回答
    for i, result in enumerate(results):
        try:
            content = result.json()['choices'][0]['message']['content']
            summary_messages.append({
                "role": "assistant",
                "content": f"参考回答{i+1}: {content}"
            })
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error processing result from model {i+1}: {e}")
            continue
    
    # 3. 添加总结提示
    summary_messages.append({
        "role": "user",
        "content": summary_model['summary_prompt']
    })
    
    # 4. 最后添加当前问题（保持原始格式，包括图片）
    summary_messages.append(messages[-1])
    
    debug_print("Summary messages prepared", summary_messages)
    return summary_messages

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """主要处理入口"""
    debug_print("Received request", {
        "headers": dict(request.headers),
        "body": request.json
    })
    
    # 获取请求数据
    data = request.json
    messages = data['messages']
    stream = data.get('stream', False)
    model_name = data.get('model')  # 获取请求的模型名称
    
    # 检查是否为视觉请求
    is_vision = ImageProcessor.is_vision_request(messages)
    
    # 获取对应的模型配置和组合配置
    model_manager = ModelManager(config)
    models, summary_model, combination_config = model_manager.get_models_config(is_vision, model_name)
    
    # 使用组合特定的配置
    api_token = combination_config.get('api_bearer_token')
    stream_feedback = combination_config.get('stream_status_feedback', True)
    use_parallel = combination_config.get('use_parallel_analysis', True)
    debug_mode = combination_config.get('debug_mode', False)
    
    # Token验证
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "未提供有效的 bearer token"}), 401
    
    token = auth_header.split(' ')[1]
    if token != api_token:
        return jsonify({"error": "无效的 bearer token"}), 401

    # 修改这里：只在并行模式下检查models
    if use_parallel and not models:
        return jsonify({"error": "No available models for this request type"}), 400

    if stream:
        return handle_stream_request(messages, models, summary_model, use_parallel, stream_feedback, debug_mode)
    else:
        return handle_normal_request(messages, models, summary_model, use_parallel, debug_mode)

def handle_stream_request(messages: List[Dict], models: List[Dict], summary_model: Dict, 
                        use_parallel: bool, stream_feedback: bool, debug_mode: bool) -> Response:
    """处理流式请求"""
    def generate():
        debug_print("Starting stream response", debug_mode=debug_mode)
        yield 'data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n'
        
        if use_parallel:
            result_queue = queue.Queue()
            threads = []
            results = []
            
            for model_config in models:
                thread = threading.Thread(
                    target=request_model, 
                    args=(model_config, messages, result_queue, debug_mode)
                )
                threads.append(thread)
                thread.start()
            
            for _ in range(len(models)):
                model_name, result = result_queue.get()
                if result is not None:
                    results.append(result)
                    if stream_feedback:
                        yield f'data: {{"choices":[{{"delta":{{"content":"{model_name} ✅\\n"}},"index":0}}]}}\n\n'
                elif stream_feedback:
                    yield f'data: {{"choices":[{{"delta":{{"content":"{model_name} ❌\\n"}},"index":0}}]}}\n\n'
            
            for thread in threads:
                thread.join()
            
            summary_messages = prepare_summary_input(results, messages, summary_model)
        else:
            summary_messages = messages if summary_model.get('keep_history', False) else [messages[-1]]
        
        try:
            response = requests.post(
                summary_model['endpoint'],
                headers=ModelManager.get_headers(summary_model),
                json=ModelManager.get_payload(summary_model, summary_messages, True),
                stream=True,
                timeout=summary_model.get('timeout', 300)
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

def handle_normal_request(messages: List[Dict], models: List[Dict], summary_model: Dict, 
                        use_parallel: bool, debug_mode: bool) -> Union[Dict, Tuple[Dict, int]]:
    """处理普通请求"""
    if use_parallel:
        result_queue = queue.Queue()
        threads = []
        results = []
        
        for model_config in models:
            thread = threading.Thread(
                target=request_model, 
                args=(model_config, messages, result_queue, debug_mode)
            )
            threads.append(thread)
            thread.start()
        
        for _ in range(len(models)):
            _, result = result_queue.get()
            if result is not None:
                results.append(result)
        
        for thread in threads:
            thread.join()
        
        summary_messages = prepare_summary_input(results, messages, summary_model)
    else:
        summary_messages = messages if summary_model.get('keep_history', False) else [messages[-1]]
    
    try:
        response = requests.post(
            summary_model['endpoint'],
            headers=ModelManager.get_headers(summary_model),
            json=ModelManager.get_payload(summary_model, summary_messages, False),
            timeout=summary_model.get('timeout', 300)
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