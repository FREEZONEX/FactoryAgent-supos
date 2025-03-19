# node-red-contrib-factory-agent-states

A Node-RED node for factory agent systems that collects and manages state information from multiple MQTT topics.

## Overview

The `factory-agent-states` node is designed to work within factory automation systems using agents. It provides a way to:

- Cache incoming messages from different MQTT topics
- Store system prompts and environment descriptions for agents
- Output collected states when triggered by a specific signal
- Clear the cache after output for the next cycle

## Installation

You can install this node directly from the Node-RED palette manager, or via npm:

```bash
npm install node-red-contrib-factory-agent-states
```

## Features

- **Caching system**: Stores the latest message from each topic until triggered
- **Configurable fields**: Allows setting System Prompt and Environment Description
- **Initial delay**: Automatically sends the first state after a configurable delay upon receiving the first message
- **Trigger mechanism**: After the first automatic trigger, constantly monitors the flow context variable `agentstate` and outputs cached states when it equals "recieved"
- **Automatic cache clearing**: Clears the topic cache after sending out the state

## Node Configuration

The node provides a simple configuration interface with the following options:

- **Name**: Optional name for the node instance
- **System Prompt**: Text to be stored in `msg.sysPrompt`
- **Environment Description**: Text to be stored in `msg.envPrompt`

## Input

The node accepts messages with payloads that will be cached based on their topics.

## Flow Context Variables

The node monitors a flow context variable:

- **agentstate**: When this variable is set to "recieved", the node will output all cached states and then reset the variable

## Output

When triggered, the node will output a message containing:

- `msg.sysPrompt`: The System Prompt configured in the node
- `msg.envPrompt`: The Environment Description configured in the node
- `msg.state`: An object containing all cached topic payloads, with topics as keys

## Usage Example

1. Add MQTT input nodes for various factory sensors/data sources
2. Connect these to the `factory-agent-states` node
3. Configure the node with appropriate prompts and descriptions
4. Set up a trigger mechanism (e.g., a function node that sets the flow context variable: `flow.set("agentstate", "recieved")`)
5. Connect the output to your agent processing node

## Example Flow

```json
[
    {
        "id": "mqtt1",
        "type": "mqtt in",
        "topic": "factory/temperature",
        "wires": [["factory-states"]]
    },
    {
        "id": "mqtt2",
        "type": "mqtt in",
        "topic": "factory/pressure",
        "wires": [["factory-states"]]
    },
    {
        "id": "factory-states",
        "type": "factory-agent-states",
        "name": "Factory States",
        "systemPrompt": "You are a factory optimization agent",
        "environmentDescription": "Factory with temperature and pressure sensors",
        "wires": [["agent-processor"]]
    },
    {
        "id": "trigger",
        "type": "function",
        "payload": "",
        "payloadType": "str",
        "repeat": "300",
        "func": "flow.set('agentstate', 'recieved');\nreturn msg;",
        "wires": [["factory-states"]]
    }
]
```

## License

MIT