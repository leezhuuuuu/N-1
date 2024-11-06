const yaml = require('js-yaml');
const fs = require('fs');

// 加载配置文件
const config = yaml.load(fs.readFileSync('config.yaml', 'utf8'));

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
                type: 'image_url',
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
        if (!supportedFormats.has(formatType)) {
          console.log(`不支持的图片格式: ${formatType}`);
          return false;
        }
        return true;
      } catch (e) {
        console.log(`Base64图片格式验证失败: ${e.message}`);
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

class ModelManager {
  constructor(config) {
    this.config = config;
    this.combinations = Object.fromEntries(
      config.combinations.map(combo => [combo.name, combo])
    );
    this.defaultCombination = config.default_combination;
  }

  getCombinationConfig(modelName) {
    return this.combinations[modelName] || this.combinations[this.defaultCombination];
  }

  getModelsConfig(isVision, modelName) {
    const combination = this.getCombinationConfig(modelName);
    
    if (isVision) {
      return [
        combination.vision_models || [],
        combination.vision_summary_model || {},
        combination
      ];
    }
    return [
      combination.text_models || [],
      combination.text_summary_model || {},
      combination
    ];
  }

  static getHeaders(modelConfig) {
    return {
      'Authorization': `Bearer ${modelConfig.bearer_token}`,
      'Content-Type': 'application/json'
    };
  }

  static getPayload(modelConfig, messages, stream) {
    return {
      model: modelConfig.model_name,
      messages: Array.isArray(messages) ? messages : [
        { role: "user", content: messages }
      ],
      stream,
      temperature: modelConfig.temperature || 0.7
    };
  }
}

module.exports = {
  ImageProcessor,
  ModelManager,
  config
}; 