# Node-RED Gemini Agent

A Node-RED node for interacting with Google's Gemini AI models.

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## English

### Overview

The Factory Agent Gemini node provides a simple way to integrate Google's Gemini AI capabilities into your Node-RED flows. This node lets you send prompts to Gemini models and receive AI-generated responses that can be used for various automation and processing tasks.

### Features

- Support for `gemini-2.0-flash` and `gemini-2.0-flash-lite` models
- Configurable temperature and max token parameters
- System prompt customization
- Detailed response information including full API response
- Flow state tracking via `flow.agentstate`

### Installation

```bash
cd ~/.node-red
npm install factory-agent-gemini
```

Alternatively, you can use the Node-RED Palette Manager to install the node.

### Configuration

![Node Configuration](https://placeholder-for-configuration-screenshot.png)

- **Name**: Optional name for the node instance
- **API Key**: Your Google Gemini API key (required)
- **Model**: Select the Gemini model to use
- **Temperature**: Controls randomness in generation (0.0-1.0)
- **Max Tokens**: Maximum output tokens in the response

### Input Properties

The node accepts the following message properties:

| Property    | Type          | Description                                      |
|-------------|---------------|--------------------------------------------------|
| `payload`   | string/object | Main content to send to Gemini                   |
| `sysPrompt` | string        | System prompt to guide Gemini's behavior         |
| `envPrompt` | string        | Environment context (used if payload not present)|
| `state`     | string        | Current state info (used if payload not present) |

### Output Properties

The node outputs a message with these properties:

| Property        | Type   | Description                               |
|-----------------|--------|-------------------------------------------|
| `payload`       | object | Complete API response                     |
| `result`        | string | Extracted text response from Gemini       |
| `geminiRequest` | object | Request object that was sent to the API   |
| `finishReason`  | string | Reason why generation stopped (if provided)|

### Example Flow

```json
[
    {
        "id": "5b913f59.14274",
        "type": "inject",
        "z": "2a1c7b.4e05694",
        "name": "Ask a question",
        "props": [
            {
                "p": "payload"
            }
        ],
        "repeat": "",
        "crontab": "",
        "once": false,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "Explain how Node-RED works in simple terms",
        "payloadType": "str",
        "x": 190,
        "y": 240,
        "wires": [
            [
                "7f98bab4.c8a524"
            ]
        ]
    },
    {
        "id": "7f98bab4.c8a524",
        "type": "factory-agent-gemini",
        "z": "2a1c7b.4e05694",
        "name": "Gemini Agent",
        "model": "gemini-2.0-flash",
        "temperature": "0.7",
        "maxTokens": "2048",
        "x": 390,
        "y": 240,
        "wires": [
            [
                "e92c9966.763208"
            ]
        ]
    },
    {
        "id": "e92c9966.763208",
        "type": "debug",
        "z": "2a1c7b.4e05694",
        "name": "Result",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "result",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 570,
        "y": 240,
        "wires": []
    }
]
```

### License

MIT

---

<a name="chinese"></a>
## 中文

### 概述

Factory Agent Gemini节点提供了一种将Google的Gemini AI功能集成到Node-RED流程中的简单方法。该节点让您能够向Gemini模型发送提示，并接收AI生成的响应，可用于各种自动化和处理任务。

### 功能特点

- 支持`gemini-2.0-flash`和`gemini-2.0-flash-lite`模型
- 可配置的温度和最大令牌参数
- 系统提示自定义
- 详细的响应信息，包括完整的API响应
- 通过`flow.agentstate`跟踪流程状态

### 安装

```bash
cd ~/.node-red
npm install factory-agent-gemini
```

或者，您可以使用Node-RED调色板管理器安装节点。

### 配置

![节点配置](https://placeholder-for-configuration-screenshot.png)

- **名称**: 节点实例的可选名称
- **API密钥**: 您的Google Gemini API密钥（必填）
- **模型**: 选择要使用的Gemini模型
- **温度**: 控制生成的随机性（0.0-1.0）
- **最大令牌数**: 响应中的最大输出令牌数

### 输入属性

节点接受以下消息属性：

| 属性        | 类型          | 描述                              |
|-------------|---------------|----------------------------------|
| `payload`   | 字符串/对象   | 发送给Gemini的主要内容            |
| `sysPrompt` | 字符串        | 引导Gemini行为的系统提示          |
| `envPrompt` | 字符串        | 环境上下文（在payload不存在时使用）|
| `state`     | 字符串        | 当前状态信息（在payload不存在时使用）|

### 输出属性

节点输出具有以下属性的消息：

| 属性            | 类型    | 描述                           |
|-----------------|---------|--------------------------------|
| `payload`       | 对象    | 完整的API响应                  |
| `result`        | 字符串  | 从Gemini提取的文本响应         |
| `geminiRequest` | 对象    | 发送到API的请求对象            |
| `finishReason`  | 字符串  | 生成停止的原因（如果提供）      |

### 示例流程

```json
[
    {
        "id": "5b913f59.14274",
        "type": "inject",
        "z": "2a1c7b.4e05694",
        "name": "提问",
        "props": [
            {
                "p": "payload"
            }
        ],
        "repeat": "",
        "crontab": "",
        "once": false,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "用简单的术语解释Node-RED是如何工作的",
        "payloadType": "str",
        "x": 190,
        "y": 240,
        "wires": [
            [
                "7f98bab4.c8a524"
            ]
        ]
    },
    {
        "id": "7f98bab4.c8a524",
        "type": "factory-agent-gemini",
        "z": "2a1c7b.4e05694",
        "name": "Gemini智能体",
        "model": "gemini-2.0-flash",
        "temperature": "0.7",
        "maxTokens": "2048",
        "x": 390,
        "y": 240,
        "wires": [
            [
                "e92c9966.763208"
            ]
        ]
    },
    {
        "id": "e92c9966.763208",
        "type": "debug",
        "z": "2a1c7b.4e05694",
        "name": "结果",
        "active": true,
        "tosidebar": true,
        "console": false,
        "tostatus": false,
        "complete": "result",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 570,
        "y": 240,
        "wires": []
    }
]
```

### 使用方法

1. 在Node-RED流程中添加Factory Agent Gemini节点
2. 配置您的Gemini API密钥和所需参数
3. 连接输入节点（如inject节点）来提供prompt
4. 连接输出节点（如debug节点）来查看结果
5. 部署您的流程并测试

### 许可证

MIT