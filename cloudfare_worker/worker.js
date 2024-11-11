// 配置对象
const CONFIG = {
  defaultCombination: "direct",
  combinations: [
    {
      name: "parallel",
      apiBearerToken: "NewBearerToken123", 
      streamStatusFeedback: false,
      useParallelAnalysis: true,
      debugMode: false,
      textModels: [
        {
          endpoint: "https://new.endpoint.com/v1/chat/completions",
          bearerToken: "new-bearer-token-1",
          modelName: "new-model-1",
          temperature: 0.5,
          maxRetries: 5,
          timeout: 200
        },
        {
          endpoint: "https://new.endpoint.com/v1/chat/completions", 
          bearerToken: "new-bearer-token-2",
          modelName: "new-model-2",
          temperature: 0.5,
          maxRetries: 5,
          timeout: 200
        }
      ],
      visionModels: [
        {
          endpoint: "https://new.endpoint.com/v1/chat/completions",
          bearerToken: "new-bearer-token-3",
          modelName: "new-vision-model-1",
          temperature: 0.8,
          maxRetries: 5,
          timeout: 200
        }
      ],
      textSummaryModel: {
        endpoint: "https://new.endpoint.com/v1/chat/completions",
        bearerToken: "new-bearer-token-4",
        modelName: "new-summary-model-1",
        temperature: 0.3,
        keepHistory: false,
        summaryPrompt: "请生成一个简洁的总结。",
        timeout: 200
      },
      visionSummaryModel: {
        endpoint: "https://new.endpoint.com/v1/chat/completions",
        bearerToken: "new-bearer-token-5",
        modelName: "new-vision-summary-model-1",
        temperature: 0.3,
        keepHistory: false,
        summaryPrompt: "请生成一个简洁的视觉总结。",
        timeout: 200
      }
    },
    {
      name: "direct",
      apiBearerToken: "NewBearerToken123",
      streamStatusFeedback: false,
      useParallelAnalysis: false,
      debugMode: false,
      textSummaryModel: {
        endpoint: "https://new.endpoint.com/v1/chat/completions",
        bearerToken: "new-bearer-token-6",
        modelName: "new-summary-model-2",
        temperature: 0.3,
        keepHistory: false,
        summaryPrompt: "请生成一个简洁的总结。",
        timeout: 200
      },
      visionSummaryModel: {
        endpoint: "https://new.endpoint.com/v1/chat/completions",
        bearerToken: "new-bearer-token-7",
        modelName: "new-vision-summary-model-2",
        temperature: 0.3,
        keepHistory: false,
        summaryPrompt: "请生成一个简洁的视觉总结。",
        timeout: 200
      }
    }
  ]
};
// 图片处理类
class ImageProcessor {
  static processVisionMessages(messages) {
    const processedMessages = [];
    for (const message of messages) {
      if (Array.isArray(message.content)) {
        const newContent = [];
        for (const item of message.content) {
          if (item?.type === 'image_url') {
            const url = item.image_url?.url || '';
            if (this.validateImageUrl(url)) {
              newContent.push({
                type: "image_url",
                image_url: {
                  url: url,
                  detail: item.image_url?.detail || 'auto'
                }
              });
            }
          } else {
            newContent.push(item);
          }
        }
        message.content = newContent;
      }
      processedMessages.push(message);
    }
    return processedMessages;
  }

  static validateImageUrl(url) {
    if (url.startsWith('data:image/')) {
      try {
        const [header] = url.split(',', 1);
        const formatType = header.split(';')[0].split('/')[1];
        const supportedFormats = new Set(['jpeg', 'png', 'gif', 'webp']);
        return supportedFormats.has(formatType);
      } catch (e) {
        console.error(`Base64图片格式验证失败: ${e}`);
        return false;
      }
    }
    return url.startsWith('http://') || url.startsWith('https://');
  }

  static isVisionRequest(messages) {
    return messages.some(message => 
      Array.isArray(message.content) && 
      message.content.some(item => item?.type === 'image_url')
    );
  }
}

// 模型管理类
class ModelManager {
  constructor(config) {
    this.config = config;
    this.combinations = {};
    for (const combo of config.combinations) {
      this.combinations[combo.name] = combo;
    }
    this.defaultCombination = config.defaultCombination;
  }

  getCombinationConfig(modelName) {
    const combinationName = modelName || this.defaultCombination;
    return this.combinations[combinationName] || this.combinations[this.defaultCombination];
  }

  getModelsConfig(isVision, modelName) {
    const combination = this.getCombinationConfig(modelName);
    if (isVision) {
      return [
        combination.visionModels || [],
        combination.visionSummaryModel || {},
        combination
      ];
    }
    return [
      combination.textModels || [],
      combination.textSummaryModel || {},
      combination
    ];
  }

  static getHeaders(modelConfig) {
    return {
      'Authorization': `Bearer ${modelConfig.bearerToken}`,
      'Content-Type': 'application/json'
    };
  }

  static getPayload(modelConfig, messages, stream) {
    return {
      model: modelConfig.modelName,
      messages: Array.isArray(messages) ? messages : [
        { role: "user", content: messages }
      ],
      stream,
      temperature: modelConfig.temperature || 0.7
    };
  }
}

// 调试打印函数
function debugPrint(message, data, debugMode) {
  if (debugMode) {
    console.log(`[DEBUG] ${message}`);
    if (data) {
      console.log(JSON.stringify(data, null, 2));
    }
    console.log("-".repeat(50));
  }
}

// 请求模型函数
async function requestModel(modelConfig, messages, debugMode) {
  const headers = ModelManager.getHeaders(modelConfig);
  const payload = ModelManager.getPayload(modelConfig, messages, false);

  debugPrint(`Requesting ${modelConfig.modelName}`, {
    endpoint: modelConfig.endpoint,
    headers,
    payload
  }, debugMode);

  const maxRetries = modelConfig.maxRetries || 3;
  const timeout = modelConfig.timeout || 120;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout * 1000);

      const response = await fetch(modelConfig.endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      debugPrint(`Response from ${modelConfig.modelName}`, result, debugMode);
      return { modelName: modelConfig.modelName, response: result };
    } catch (e) {
      if (attempt === maxRetries - 1) {
        console.error(`Error requesting model ${modelConfig.modelName} after ${maxRetries} attempts: ${e}`);
        return { modelName: modelConfig.modelName, response: null };
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}

// 准备总结输入
function prepareSummaryInput(results, messages, summaryModel) {
  const summaryMessages = [];

  if (summaryModel.keepHistory) {
    summaryMessages.push(...messages.slice(0, -1));
  }

  results.forEach((result, i) => {
    try {
      const content = result.response.choices[0].message.content;
      summaryMessages.push({
        role: "assistant",
        content: `参考回答${i + 1}: ${content}`
      });
    } catch (e) {
      console.error(`Error processing result from model ${i + 1}: ${e}`);
    }
  });

  summaryMessages.push({
    role: "user",
    content: summaryModel.summaryPrompt
  });

  summaryMessages.push(messages[messages.length - 1]);

  return summaryMessages;
}
// 处理流式请求
async function handleStreamRequest(messages, models, summaryModel, useParallel, streamFeedback, debugMode) {
  const encoder = new TextEncoder();
  const stream = new TransformStream();
  const writer = stream.writable.getWriter();

  // 写入流数据的辅助函数
  async function writeToStream(data) {
    await writer.write(encoder.encode(data));
  }

  // 主处理逻辑
  (async () => {
    try {
      await writeToStream('data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n');

      let results = [];
      if (useParallel) {
        // 并行处理所有模型请求
        const pendingRequests = models.map(model => {
          return (async () => {
            const response = await requestModel(model, messages, debugMode);
            if (streamFeedback) {
              const status = response.response ? '✅' : '❌';
              await writeToStream(`data: {"choices":[{"delta":{"content":"${model.modelName} ${status}\\n"},"index":0}]}\n\n`);
            }
            return response;
          })();
        });

        // 等待所有请求完成并收集结果
        const responses = await Promise.all(pendingRequests);
        results = responses.filter(r => r.response !== null);
      }

      // 准备总结消息
      const summaryMessages = useParallel ? 
        prepareSummaryInput(results, messages, summaryModel) :
        (summaryModel.keepHistory ? messages : [messages[messages.length - 1]]);

      // 请求总结模型
      const response = await fetch(summaryModel.endpoint, {
        method: 'POST',
        headers: ModelManager.getHeaders(summaryModel),
        body: JSON.stringify(ModelManager.getPayload(summaryModel, summaryMessages, true))
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
          
          if (trimmedLine === 'data: [DONE]' || trimmedLine.includes('"[DONE]"')) continue;
          
          try {
            const jsonData = JSON.parse(trimmedLine.slice(6));
            if (jsonData.choices?.[0]?.delta?.content) {
              await writeToStream(`${trimmedLine}\n\n`);
            }
          } catch (e) {
            console.error('Error parsing JSON:', e);
          }
        }
      }

      if (buffer) {
        const trimmedBuffer = buffer.trim();
        if (trimmedBuffer && trimmedBuffer.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(trimmedBuffer.slice(6));
            if (jsonData.choices?.[0]?.delta?.content) {
              await writeToStream(`${trimmedBuffer}\n\n`);
            }
          } catch (e) {
            console.error('Error parsing remaining buffer:', e);
          }
        }
      }

      await writeToStream('data: [DONE]\n\n');
    } catch (e) {
      console.error(`Error in streaming summary: ${e}`);
      await writeToStream(`data: {"error":"Summary generation failed - ${e}"}\n\n`);
      await writeToStream('data: [DONE]\n\n');
    } finally {
      await writer.close();
    }
  })();

  return new Response(stream.readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
// 处理通请求
async function handleNormalRequest(messages, models, summaryModel, useParallel, debugMode) {
  let results = [];
  
  if (useParallel) {
    const modelPromises = models.map(model => requestModel(model, messages, debugMode));
    const responses = await Promise.all(modelPromises);
    results = responses.filter(r => r.response !== null);
  }

  const summaryMessages = useParallel ?
    prepareSummaryInput(results, messages, summaryModel) :
    (summaryModel.keepHistory ? messages : [messages[messages.length - 1]]);

  try {
    const response = await fetch(summaryModel.endpoint, {
      method: 'POST',
      headers: ModelManager.getHeaders(summaryModel),
      body: JSON.stringify(ModelManager.getPayload(summaryModel, summaryMessages, false))
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    debugPrint("Final response", result, debugMode);
    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    const error = { error: `Summary generation failed: ${e}` };
    debugPrint("Error", error, debugMode);
    return new Response(JSON.stringify(error), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// 在 handleRequest 函数前添加图片处理中间件
async function processImages(messages) {
  // 处理视觉消息
  if (ImageProcessor.isVisionRequest(messages)) {
    return ImageProcessor.processVisionMessages(messages);
  }
  return messages;
}

// 修改 handleRequest 函数
async function handleRequest(request) {
  const url = new URL(request.url);
  
  // 重定向非API请求到GitHub
  if (url.pathname !== '/v1/chat/completions') {
    return Response.redirect('https://github.com/leezhuuuuu/N-1', 301);
  }

  // 验证请求方法
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  // 获取并验证授权头
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return new Response(JSON.stringify({ error: '缺少有效的授权头' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  try {
    const data = await request.json();
    // 添加图片处理
    const processedMessages = await processImages(data.messages);
    const stream = data.stream || false;
    const modelName = data.model;

    const isVision = ImageProcessor.isVisionRequest(processedMessages);
    const modelManager = new ModelManager(CONFIG);
    const [models, summaryModel, combinationConfig] = modelManager.getModelsConfig(isVision, modelName);

    const token = authHeader.split(' ')[1];
    if (token !== combinationConfig.apiBearerToken) {
      return new Response(JSON.stringify({ error: '无效的 bearer token' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (combinationConfig.useParallelAnalysis && !models.length) {
      return new Response(JSON.stringify({ error: 'No available models for this request type' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return stream ?
      handleStreamRequest(
        processedMessages, // 使用处理后的消息
        models,
        summaryModel,
        combinationConfig.useParallelAnalysis,
        combinationConfig.streamStatusFeedback,
        combinationConfig.debugMode
      ) :
      handleNormalRequest(
        processedMessages, // 使用处理后的消息
        models,
        summaryModel,
        combinationConfig.useParallelAnalysis,
        combinationConfig.debugMode
      );

  } catch (error) {
    return new Response(JSON.stringify({ error: `Invalid request: ${error.message}` }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// 注册Worker
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
