# If you dont give a shit about agent, u can throw msg.payload to this node and it will send it to deepseek.

# Node-RED factory-agent-deepseek

A Node-RED node for interacting with Deepseek's AI API to create agent-based systems. This node is designed to simplify the process of sending prompts to Deepseek's models and handling responses within Node-RED flows.


## Features

- Compose and send requests to Deepseek API with minimal configuration
- Support for both deepseek-chat and deepseek-reasoner models
- Combines environment, state, and action data into JSON format for user messages
- Configurable temperature and max tokens settings
- Secure API key storage

## Installation

Install via Node-RED's Manage Palette:

1. In Node-RED, navigate to the menu → Manage palette
2. Go to the "Install" tab
3. Search for "factory-agent-deepseek"
4. Click install

Or install via npm:

```bash
cd ~/.node-red
npm install factory-agent-deepseek
```

## Usage

### Node Configuration

1. Drag the `factory-agent-deepseek` node from the factory category in the palette to your flow
2. Double-click the node to open the configuration panel
3. Enter your Deepseek API key directly in the node configuration
4. Select the model (deepseek-reasoner or deepseek-chat)
5. Adjust temperature and max tokens settings if needed
6. Click Done to save

### Input

The node expects the following input properties:

- `msg.sysPrompt` (string): The system prompt to send to Deepseek's system role
- `msg.envPrompt` (string): Environment prompt to be combined with state and action
- `msg.state` (string): State information to be combined with envPrompt and action
- `global.action` (string): Action information from global context

### Output

The node outputs:

- `msg.payload` (object): The complete response from Deepseek API
- `msg.deepseekRequest` (object): The request that was sent to Deepseek API
- `msg.result` (string): The content from the Deepseek response message
- `msg.reasoning_content` (string): The reasoning_content from the Deepseek response (if available)

### Flow Context

The node manages a flow context variable:

- `flow.agentstate`: Tracks the request status
  - `processing`: Set when the request is sent to Deepseek API
  - `received`: Set when a successful response is received

### Example Flow

```json
[{"id":"f6f2187d.f17ca8","type":"factory-agent-deepseek","z":"34de40b2.eb705","name":"Deepseek Agent","model":"deepseek-reasoner","temperature":"0.7","maxTokens":"2048","x":450,"y":300,"wires":[["c234a454.0cb648"]],"credentials":{"apiKey":"YOUR_API_KEY_HERE"}},{"id":"5a35c1ae.5e231","type":"inject","z":"34de40b2.eb705","name":"Test Input","props":[{"p":"sysPrompt","v":"You are a helpful assistant.","vt":"str"},{"p":"envPrompt","v":"Current time: 14:30","vt":"str"},{"p":"state","v":"User asked about weather.","vt":"str"}],"repeat":"","crontab":"","once":false,"onceDelay":0.1,"topic":"","x":270,"y":300,"wires":[["f6f2187d.f17ca8"]]},{"id":"c234a454.0cb648","type":"debug","z":"34de40b2.eb705","name":"Response","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","statusVal":"","statusType":"auto","x":640,"y":300,"wires":[]}]
```

## Files

The node includes the following files:

1. `factory-agent-deepseek.js` - Main implementation
2. `factory-agent-deepseek.html` - Configuration UI and help documentation
3. `package.json` - Node-RED package information
4. `README.md` - Documentation

## License

MIT