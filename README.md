# Factory Agent 

![Factory Agent Logo](/assets/Factoryagent.jpg)

Factory Agent is a collection of custom NodeRED nodes that communicate with your MQTT broker to obtain real-time information about OT/IT data sources and feed it to LLMs for analysis. This enables LLMs to perform user-defined feedback actions, such as controlling device operations, modifying workshop schedules, or clearing inventory.

![Architecture Diagram](/assets/arc.svg)

The method of using an MQ Broker to aggregate industrial data is also known as Unified Namespace, a simple and efficient industrial DataOps methodology considered to be the true industrial data integration solution for the post-OPCUA era. Factory Agent relies on this methodology to establish bidirectional real-time connections with the factory. You can implement this using our open-source software supOS.

## How it works

> Each Factory Agent Node comes with detailed documentation. You can find more detailed designs for advanced usage in NodeRED or in the node's README.

1. Connect factory data to the MQTT Broker through NodeRED, ensuring each data Topic expresses actual meaning, such as `Finance/Profit/RealtimeCost`, `Warehouse/Staging/AMR1`, rather than `oed02skj/http01/key292987`. Similarly, Payloads should be input in KV format like `{"Temp":"1"}` to express actual factory information.

   ![Step 1](/assets/1.jpg)

2. Connect the MQTT Topics representing the factory's actual conditions to the Factory Agent State Node via the MQTT in Node. Input system prompts and example Action return structures in the System Prompt field.

   ![Step 2](/assets/2.jpg)

3. Connect to the Factory Agent Deepseek node (or another LLM), and use a function node to capture `msg.result` and parse it as JSON (this variable stores the actions determined by the LLM; if your system prompt is effective, this will be pure JSON).

   ![Step 3](/assets/3.jpg)

4. Send back to a specific MQTT Topic. You'll write programs or use NodeRED to receive the actions the LLM wants to execute from this Topic, then parse and connect to actual devices or systems.

   ![Step 4](/assets/4.jpg)

## Installation

### Installing supOS:
<TBD>

### Installing Factory Agent nodes:
- If you have a NodeRED instance connected to the internet, you can directly search for "factory agent" in the palette manager and download it
- You can also find the [Factory Agent nodes collection in the NodeRED community](https://flows.nodered.org/collection/q64dJIkwmP0z)