const express = require('express');
const router = express.Router();
const { handleStreamRequest, handleNormalRequest } = require('./handlers');
const { ImageProcessor, ModelManager, config } = require('./models');

router.post('/v1/chat/completions', async (req, res) => {
  const { messages, stream = false, model } = req.body;
  
  // 验证 bearer token
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: "未提供有效的 bearer token" });
  }

  const token = authHeader.split(' ')[1];
  const modelManager = new ModelManager(config);
  const isVision = ImageProcessor.isVisionRequest(messages);
  const [models, summaryModel, combinationConfig] = modelManager.getModelsConfig(isVision, model);

  if (token !== combinationConfig.api_bearer_token) {
    return res.status(401).json({ error: "无效的 bearer token" });
  }

  const useParallel = combinationConfig.use_parallel_analysis;
  if (useParallel && !models?.length) {
    return res.status(400).json({ error: "No available models for this request type" });
  }

  try {
    if (stream) {
      return handleStreamRequest(req, res, {
        messages,
        models,
        summaryModel,
        useParallel,
        streamFeedback: combinationConfig.stream_status_feedback,
        debugMode: combinationConfig.debug_mode
      });
    } else {
      return handleNormalRequest(req, res, {
        messages,
        models,
        summaryModel,
        useParallel,
        debugMode: combinationConfig.debug_mode
      });
    }
  } catch (error) {
    console.error('Request handling error:', error);
    return res.status(500).json({ error: error.message });
  }
});

// 捕获所有其他路由并重定向
router.get('*', (req, res) => {
  res.redirect('https://github.com/leezhuuuuu/N-1');
});

module.exports = router; 