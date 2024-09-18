from flask import Flask, request, Response
import requests
import json
import threading
from flask_sse import sse

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')

# 加载配置文件
with open('config.json') as f:
    config = json.load(f)

def request_model(model_config, messages):
    headers = {
        'Authorization': f"Bearer {model_config['bearer_token']}",
        'Content-Type': 'application/json'
    }
    payload = {
        "model": model_config['model_name'],
        "messages": messages,
        "stream": True,  # 设置为True以启用流式输出
        "temperature": model_config.get('temperature', 0.7)
    }
    response = requests.post(model_config['endpoint'], headers=headers, json=payload, stream=True)
    return response

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    messages = data['messages']
    
    threads = []
    results = []
    
    def fetch_model_response(model_config):
        result = request_model(model_config, messages)
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
        for line in result.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    print(f"Decoded line: {decoded_line}")  # 打印每一行内容
                    content = json.loads(decoded_line)['choices'][0]['delta'].get('content', '')
                    combined_content.append(f"LLM {i+1}的回答: {content}")
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}")
                    continue
    
    user_question = messages[-1]['content']
    combined_content.append(f"用户的问题是：{user_question}")
    
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
        "stream": True,
        "temperature": summary_model_config.get('temperature', 0.7)
    }
    
    # 流式输出总结结果
    def generate():
        response = requests.post(summary_model_config['endpoint'], headers=summary_headers, json=summary_payload, stream=True)
        for line in response.iter_lines():
            if line:
                yield f"data: {line.decode('utf-8')}\n\n"
        yield "data: [DONE]\n\n"
    
    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)