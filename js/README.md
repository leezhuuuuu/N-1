# N-1 JavaScript 版本

## 安装

- 安装依赖：
   ```bash
   npm install
   ```

## 使用

1. 运行程序：
   ```bash
   npm start
   ```

2. 访问服务：
   - 通过浏览器访问`http://localhost:18888`

## 配置

- 确保在js程序目录下有一个`config.yaml`文件，格式如下：
  ```yaml
  default_combination: "default"
  combinations:
    - name: "default"
      api_bearer_token: "your_token"
      stream_status_feedback: true
      use_parallel_analysis: true
      debug_mode: true
      text_models:
        - endpoint: "YOUR_API_ENDPOINT"
          bearer_token: "YOUR_MODEL_TOKEN"
          model_name: "model-1"
          temperature: 0.2
          max_retries: 3
          timeout: 150
      vision_models:
        - endpoint: "YOUR_API_ENDPOINT"
          bearer_token: "YOUR_MODEL_TOKEN"
          model_name: "vision-model-1"
          temperature: 0.7
          max_retries: 3
          timeout: 150
      text_summary_model:
        endpoint: "YOUR_API_ENDPOINT"
        bearer_token: "YOUR_MODEL_TOKEN"
        model_name: "summary-model"
        temperature: 0.1
        keep_history: true
        timeout: 150
        #...
  ```