const axios = require('axios');
const { ModelManager } = require('./models');

async function requestModel(modelConfig, messages, debugMode) {
  const headers = ModelManager.getHeaders(modelConfig);
  const payload = ModelManager.getPayload(modelConfig, messages, false);
  
  if (debugMode) {
    console.log(`\n[DEBUG] Requesting ${modelConfig.model_name}`, {
      endpoint: modelConfig.endpoint,
      headers,
      payload
    });
    console.log("-".repeat(50));
  }

  const maxRetries = modelConfig.max_retries || 3;
  const timeout = modelConfig.timeout || 120;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await axios.post(
        modelConfig.endpoint,
        payload,
        { 
          headers, 
          timeout: timeout * 1000,
          validateStatus: status => status === 200
        }
      );
      
      if (debugMode) {
        console.log(`Response from ${modelConfig.model_name}`, response.data);
        console.log("-".repeat(50));
      }
      
      return response;
    } catch (error) {
      console.error(`Attempt ${attempt + 1} failed for ${modelConfig.model_name}:`, error.message);
      if (attempt === maxRetries - 1) {
        console.error(`Error requesting model ${modelConfig.model_name} after ${maxRetries} attempts:`, error);
        return null;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}

function prepareSummaryInput(results, messages, summaryModel) {
  const summaryMessages = [];

  if (summaryModel.keep_history) {
    summaryMessages.push(...messages.slice(0, -1));
  }

  results.forEach((result, i) => {
    try {
      const content = result.data.choices[0].message.content;
      summaryMessages.push({
        role: "assistant",
        content: `参考回答${i + 1}: ${content}`
      });
    } catch (error) {
      console.error(`Error processing result from model ${i + 1}:`, error);
    }
  });

  summaryMessages.push({
    role: "user",
    content: summaryModel.summary_prompt
  });

  summaryMessages.push(messages[messages.length - 1]);

  return summaryMessages;
}

async function handleStreamRequest(req, res, options) {
  const { messages, models, summaryModel, useParallel, streamFeedback, debugMode } = options;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Transfer-Encoding', 'chunked');

  res.write('data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n');

  let summaryMessages = messages;
  
  if (useParallel) {
    const modelResults = await Promise.all(
      models.map(async modelConfig => {
        const result = await requestModel(modelConfig, messages, debugMode);
        if (streamFeedback) {
          const status = result ? '✅' : '❌';
          res.write(`data: {"choices":[{"delta":{"content":"${modelConfig.model_name} ${status}\\n"},"index":0}]}\n\n`);
        }
        return result;
      })
    );

    const validResults = modelResults.filter(Boolean);
    summaryMessages = prepareSummaryInput(validResults, messages, summaryModel);
  }

  try {
    const response = await axios({
      method: 'post',
      url: summaryModel.endpoint,
      headers: ModelManager.getHeaders(summaryModel),
      data: ModelManager.getPayload(summaryModel, summaryMessages, true),
      responseType: 'stream'
    });

    response.data.on('data', chunk => {
      const text = chunk.toString();
      if (text.includes('[DONE]')) return;
      res.write(text);
    });

    response.data.on('end', () => {
      res.write('data: {"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n');
      res.write('data: [DONE]\n\n');
      res.end();
    });

    response.data.on('error', error => {
      console.error('Stream error:', error);
      res.write(`data: {"choices":[{"delta":{"content":"Error: ${error.message}"},"index":0}]}\n\n`);
      res.write('data: [DONE]\n\n');
      res.end();
    });
  } catch (error) {
    console.error('Error in streaming summary:', error);
    res.write(`data: {"choices":[{"delta":{"content":"Error: Summary generation failed - ${error.message}"},"index":0}]}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  }
}

async function handleNormalRequest(req, res, options) {
  const { messages, models, summaryModel, useParallel, debugMode } = options;

  let summaryMessages = messages;

  if (useParallel) {
    const modelResults = await Promise.all(
      models.map(modelConfig => requestModel(modelConfig, messages, debugMode))
    );
    const validResults = modelResults.filter(Boolean);
    summaryMessages = prepareSummaryInput(validResults, messages, summaryModel);
  }

  try {
    const response = await axios.post(
      summaryModel.endpoint,
      ModelManager.getPayload(summaryModel, summaryMessages, false),
      {
        headers: ModelManager.getHeaders(summaryModel),
        timeout: (summaryModel.timeout || 300) * 1000,
        validateStatus: status => status === 200
      }
    );

    if (debugMode) {
      console.log('Final response', response.data);
    }

    return res.json(response.data);
  } catch (error) {
    console.error('Error in normal request:', error);
    return res.status(500).json({ 
      error: `Summary generation failed: ${error.message}`,
      details: error.response?.data
    });
  }
}

module.exports = {
  handleStreamRequest,
  handleNormalRequest
}; 