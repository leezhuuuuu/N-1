package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"
	
	"gopkg.in/yaml.v2"
)

// 配置结构
type Config struct {
	DefaultCombination string        `yaml:"default_combination"`
	Combinations      []Combination  `yaml:"combinations"`
}

type Combination struct {
	Name                string         `yaml:"name"`
	APIBearerToken     string         `yaml:"api_bearer_token"`
	StreamStatusFeedback bool         `yaml:"stream_status_feedback"`
	UseParallelAnalysis bool         `yaml:"use_parallel_analysis"`
	DebugMode          bool          `yaml:"debug_mode"`
	TextModels         []ModelConfig  `yaml:"text_models"`
	VisionModels       []ModelConfig  `yaml:"vision_models"`
	TextSummaryModel   SummaryModel   `yaml:"text_summary_model"`
	VisionSummaryModel SummaryModel   `yaml:"vision_summary_model"`
}

type ModelConfig struct {
	Endpoint     string  `yaml:"endpoint"`
	BearerToken  string  `yaml:"bearer_token"`
	ModelName    string  `yaml:"model_name"`
	Temperature  float64 `yaml:"temperature"`
	MaxRetries   int     `yaml:"max_retries"`
	Timeout      int     `yaml:"timeout"`
}

type SummaryModel struct {
	Endpoint      string  `yaml:"endpoint"`
	BearerToken   string  `yaml:"bearer_token"`
	ModelName     string  `yaml:"model_name"`
	Temperature   float64 `yaml:"temperature"`
	KeepHistory   bool    `yaml:"keep_history"`
	SummaryPrompt string  `yaml:"summary_prompt"`
	Timeout       int     `yaml:"timeout"`
}

// 消息结构
type Message struct {
	Role    string      `json:"role"`
	Content interface{} `json:"content"`
}

type ImageURL struct {
	URL    string `json:"url"`
	Detail string `json:"detail"`
}

type ImageContent struct {
	Type     string   `json:"type"`
	ImageURL ImageURL `json:"image_url"`
}

// 请求和响应结构
type ChatRequest struct {
	Messages []Message `json:"messages"`
	Stream   bool      `json:"stream"`
	Model    string    `json:"model"`
}

type ChatResponse struct {
	Choices []Choice `json:"choices"`
}

type Choice struct {
	Message      Message `json:"message,omitempty"`
	Delta        Delta   `json:"delta,omitempty"`
	Index        int     `json:"index"`
	FinishReason string `json:"finish_reason,omitempty"`
}

type Delta struct {
	Content string `json:"content,omitempty"`
}

// 全局配置变量
var config Config

func init() {
	// 读取配置文件
	data, err := ioutil.ReadFile("config.yaml")
	if err != nil {
		log.Fatalf("Error reading config file: %v", err)
	}

	err = yaml.Unmarshal(data, &config)
	if err != nil {
		log.Fatalf("Error parsing config file: %v", err)
	}
}

// ImageProcessor 结构体及方法
type ImageProcessor struct{}

func (ip *ImageProcessor) ProcessVisionMessages(messages []Message) []Message {
	processedMessages := make([]Message, 0, len(messages))
	
	for _, msg := range messages {
		if content, ok := msg.Content.([]interface{}); ok {
			newContent := make([]interface{}, 0, len(content))
			for _, item := range content {
				if itemMap, ok := item.(map[string]interface{}); ok {
					if itemMap["type"] == "image_url" {
						if imageURL, ok := itemMap["image_url"].(map[string]interface{}); ok {
							url := imageURL["url"].(string)
							if ip.ValidateImageURL(url) {
								newContent = append(newContent, map[string]interface{}{
									"type": "image_url",
									"image_url": map[string]interface{}{
										"url":    url,
										"detail": imageURL["detail"].(string),
									},
								})
							}
						}
					} else {
						newContent = append(newContent, item)
					}
				}
			}
			msg.Content = newContent
		}
		processedMessages = append(processedMessages, msg)
	}
	return processedMessages
}

func (ip *ImageProcessor) ValidateImageURL(url string) bool {
	if strings.HasPrefix(url, "data:image/") {
		parts := strings.Split(url, ",")
		if len(parts) != 2 {
			return false
		}
		header := parts[0]
		format := strings.Split(strings.Split(header, ";")[0], "/")[1]
		supportedFormats := map[string]bool{
			"jpeg": true,
			"png":  true,
			"gif":  true,
			"webp": true,
		}
		return supportedFormats[format]
	}
	return strings.HasPrefix(url, "http://") || strings.HasPrefix(url, "https://")
}

func (ip *ImageProcessor) IsVisionRequest(messages []Message) bool {
	for _, msg := range messages {
		if content, ok := msg.Content.([]interface{}); ok {
			for _, item := range content {
				if itemMap, ok := item.(map[string]interface{}); ok {
					if itemMap["type"] == "image_url" {
						return true
					}
				}
			}
		}
	}
	return false
}

// ModelManager 结构体及方法
type ModelManager struct {
	config Config
}

func NewModelManager(config Config) *ModelManager {
	return &ModelManager{config: config}
}

func (mm *ModelManager) GetModelsConfig(isVision bool, modelName string) ([]ModelConfig, SummaryModel, Combination) {
	combination := mm.getCombinationConfig(modelName)
	
	if isVision {
		return combination.VisionModels,
			combination.VisionSummaryModel,
			combination
	}
	return combination.TextModels,
		combination.TextSummaryModel,
		combination
}

func (mm *ModelManager) getCombinationConfig(modelName string) Combination {
	if modelName == "" {
		modelName = mm.config.DefaultCombination
	}
	
	for _, combo := range mm.config.Combinations {
		if combo.Name == modelName {
			return combo
		}
	}
	
	// 如果找不到指定的组合，返回默认组合
	for _, combo := range mm.config.Combinations {
		if combo.Name == mm.config.DefaultCombination {
			return combo
		}
	}
	
	// 如果连默认组合都找不到，返回第一个组合
	return mm.config.Combinations[0]
}

func main() {
	// 设置路由
	http.HandleFunc("/v1/chat/completions", handleChatCompletions)
	http.HandleFunc("/", handleCatchAll)

	// 启动服务器
	log.Printf("Server starting on :18888")
	if err := http.ListenAndServe(":18888", nil); err != nil {
		log.Fatal(err)
	}
}

// 处理函数
func handleChatCompletions(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 验证 Bearer Token
	authHeader := r.Header.Get("Authorization")
	if !validateBearerToken(authHeader) {
		http.Error(w, "Invalid bearer token", http.StatusUnauthorized)
		return
	}

	// 解析请求体
	var chatReq ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&chatReq); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// 创建 ImageProcessor 和 ModelManager 实例
	ip := &ImageProcessor{}
	mm := NewModelManager(config)

	// 检查是否为视觉请求
	isVision := ip.IsVisionRequest(chatReq.Messages)

	// 获取模型配置
	models, summaryModel, combinationConfig := mm.GetModelsConfig(isVision, chatReq.Model)

	if chatReq.Stream {
		handleStreamRequest(w, chatReq, models, summaryModel, combinationConfig, ip)
	} else {
		handleNormalRequest(w, chatReq, models, summaryModel, combinationConfig, ip)
	}
}

func handleStreamRequest(w http.ResponseWriter, req ChatRequest, models []ModelConfig, 
	summaryModel SummaryModel, combinationConfig Combination, ip *ImageProcessor) {
	
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}

	// 发送初始空白内容
	fmt.Fprintf(w, "data: {\"choices\":[{\"delta\":{\"content\":\" \"},\"index\":0}]}\n\n")
	flusher.Flush()

	if combinationConfig.UseParallelAnalysis {
		results := make(chan *http.Response, len(models))
		var wg sync.WaitGroup

		// 并行请求所有模型
		for _, model := range models {
			wg.Add(1)
			go func(mc ModelConfig) {
				defer wg.Done()
				if resp := requestModel(mc, req.Messages); resp != nil {
					results <- resp
					if combinationConfig.StreamStatusFeedback {
						fmt.Fprintf(w, "data: {\"choices\":[{\"delta\":{\"content\":\"%s ✅\\n\"},\"index\":0}]}\n\n", mc.ModelName)
						flusher.Flush()
					}
				} else if combinationConfig.StreamStatusFeedback {
					fmt.Fprintf(w, "data: {\"choices\":[{\"delta\":{\"content\":\"%s ❌\\n\"},\"index\":0}]}\n\n", mc.ModelName)
					flusher.Flush()
				}
			}(model)
		}

		// 等待所有请求完成
		go func() {
			wg.Wait()
			close(results)
		}()

		// 收集结果
		var modelResponses []*http.Response
		for resp := range results {
			modelResponses = append(modelResponses, resp)
		}

		// 准备总结输入
		summaryMessages := prepareSummaryInput(modelResponses, req.Messages, summaryModel)
		streamSummaryResponse(w, summaryModel, summaryMessages, flusher)
	} else {
		// 直接模式
		summaryMessages := req.Messages
		if summaryModel.KeepHistory {
			summaryMessages = req.Messages
		} else {
			summaryMessages = []Message{req.Messages[len(req.Messages)-1]}
		}
		streamSummaryResponse(w, summaryModel, summaryMessages, flusher)
	}
}

func handleNormalRequest(w http.ResponseWriter, req ChatRequest, models []ModelConfig,
	summaryModel SummaryModel, combinationConfig Combination, ip *ImageProcessor) {
	
	var finalResponse *ChatResponse

	if combinationConfig.UseParallelAnalysis {
		results := make(chan *http.Response, len(models))
		var wg sync.WaitGroup

		// 并行请求所有模型
		for _, model := range models {
			wg.Add(1)
			go func(mc ModelConfig) {
				defer wg.Done()
				if resp := requestModel(mc, req.Messages); resp != nil {
					results <- resp
				}
			}(model)
		}

		// 等待所有请求完成
		go func() {
			wg.Wait()
			close(results)
		}()

		// 收集结果
		var modelResponses []*http.Response
		for resp := range results {
			modelResponses = append(modelResponses, resp)
		}

		// 准备总结输入
		summaryMessages := prepareSummaryInput(modelResponses, req.Messages, summaryModel)
		finalResponse = requestSummary(summaryModel, summaryMessages)
	} else {
		// 直接模式
		summaryMessages := req.Messages
		if !summaryModel.KeepHistory {
			summaryMessages = []Message{req.Messages[len(req.Messages)-1]}
		}
		finalResponse = requestSummary(summaryModel, summaryMessages)
	}

	// 返回响应
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(finalResponse)
}

// 辅助函数
func validateBearerToken(authHeader string) bool {
	if !strings.HasPrefix(authHeader, "Bearer ") {
		return false
	}
	token := strings.TrimPrefix(authHeader, "Bearer ")
	return token == config.Combinations[0].APIBearerToken
}

func requestModel(model ModelConfig, messages []Message) *http.Response {
	client := &http.Client{
		Timeout: time.Duration(model.Timeout) * time.Second,
	}
	
	payload := map[string]interface{}{
		"model":       model.ModelName,
		"messages":    messages,
		"temperature": model.Temperature,
		"stream":      false,
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshaling payload: %v", err)
		return nil
	}
	
	for i := 0; i < model.MaxRetries; i++ {
		req, err := http.NewRequest("POST", model.Endpoint, bytes.NewBuffer(jsonData))
		if err != nil {
			log.Printf("Error creating request: %v", err)
			continue
		}
		
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", model.BearerToken))
		req.Header.Set("Content-Type", "application/json")
		
		resp, err := client.Do(req)
		if err != nil {
			log.Printf("Error making request (attempt %d): %v", i+1, err)
			time.Sleep(time.Second)
			continue
		}
		
		if resp.StatusCode == http.StatusOK {
			return resp
		}
		
		resp.Body.Close()
		time.Sleep(time.Second)
	}
	
	return nil
}

func prepareSummaryInput(responses []*http.Response, messages []Message, summaryModel SummaryModel) []Message {
	summaryMessages := make([]Message, 0)
	
	if summaryModel.KeepHistory {
		// 保留历史消息，除了最后一条
		summaryMessages = append(summaryMessages, messages[:len(messages)-1]...)
	}
	
	// 添加参考回答
	for i, resp := range responses {
		var result struct {
			Choices []struct {
				Message struct {
					Content string `json:"content"`
				} `json:"message"`
			} `json:"choices"`
		}
		
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			log.Printf("Error decoding response: %v", err)
			continue
		}
		resp.Body.Close()
		
		if len(result.Choices) > 0 {
			summaryMessages = append(summaryMessages, Message{
				Role:    "assistant",
				Content: fmt.Sprintf("参考回答%d: %s", i+1, result.Choices[0].Message.Content),
			})
		}
	}
	
	// 添加总结提示
	summaryMessages = append(summaryMessages, Message{
		Role:    "user",
		Content: summaryModel.SummaryPrompt,
	})
	
	// 添加当前问题
	summaryMessages = append(summaryMessages, messages[len(messages)-1])
	
	return summaryMessages
}

func streamSummaryResponse(w http.ResponseWriter, summaryModel SummaryModel, messages []Message, flusher http.Flusher) {
	client := &http.Client{
		Timeout: time.Duration(summaryModel.Timeout) * time.Second,
	}
	
	payload := map[string]interface{}{
		"model":       summaryModel.ModelName,
		"messages":    messages,
		"temperature": summaryModel.Temperature,
		"stream":      true,
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshaling payload: %v", err)
		return
	}
	
	req, err := http.NewRequest("POST", summaryModel.Endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return
	}
	
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", summaryModel.BearerToken))
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error making request: %v", err)
		return
	}
	defer resp.Body.Close()
	
	reader := bufio.NewReader(resp.Body)
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			if err != io.EOF {
				log.Printf("Error reading stream: %v", err)
			}
			break
		}
		
		if strings.TrimSpace(line) == "" {
			continue
		}
		
		if strings.TrimSpace(line) == "data: [DONE]" {
			fmt.Fprintf(w, "data: {\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\n")
			fmt.Fprintf(w, "data: [DONE]\n\n")
			flusher.Flush()
			break
		}
		
		fmt.Fprintf(w, "%s\n", line)
		flusher.Flush()
	}
}

func requestSummary(summaryModel SummaryModel, messages []Message) *ChatResponse {
	client := &http.Client{
		Timeout: time.Duration(summaryModel.Timeout) * time.Second,
	}
	
	payload := map[string]interface{}{
		"model":       summaryModel.ModelName,
		"messages":    messages,
		"temperature": summaryModel.Temperature,
		"stream":      false,
	}
	
	jsonData, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshaling payload: %v", err)
		return nil
	}
	
	req, err := http.NewRequest("POST", summaryModel.Endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Error creating request: %v", err)
		return nil
	}
	
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", summaryModel.BearerToken))
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error making request: %v", err)
		return nil
	}
	defer resp.Body.Close()
	
	var result ChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		log.Printf("Error decoding response: %v", err)
		return nil
	}
	
	return &result
}

// 处理所有其他路由的函数
func handleCatchAll(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/v1/chat/completions" {
		http.Redirect(w, r, "https://github.com/leezhuuuuu/N-1", http.StatusTemporaryRedirect)
	}
}
