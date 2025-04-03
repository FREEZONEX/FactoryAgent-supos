module.exports = function(RED) {
    function FactoryAgentDeepseek(config) {
        RED.nodes.createNode(this, config);
        const node = this;
        const axios = require('axios');

        this.on('input', function(msg, send, done) {
            // Use the original message object if send is available (Node-RED 1.0+)
            send = send || function() { node.send.apply(node, arguments); };

            // Get model from config or use default
            const model = config.model || "deepseek-reasoner";
            let systemPrompt = msg.sysPrompt || "You are a helpful assistant.";
            
            // Prepare the messages array
            const messages = [
                {
                    role: "system",
                    content: systemPrompt
                }
            ];
            
            // Check if msg.payload exists
            if (msg.hasOwnProperty('payload')) {
                // If payload exists, use it directly as user message content
                messages.push({
                    role: "user",
                    content: typeof msg.payload === 'string' ? msg.payload : JSON.stringify(msg.payload)
                });
            } else {
                // If no payload, use the original logic with envPrompt, state, and action
                let envPrompt = msg.envPrompt || "";
                let state = msg.state || "";

                const globalContext = node.context().global;
                // 首先尝试获取节点特定的 actions
                const nodeSpecificKey = 'action.' + node.id;
                let action = globalContext.get(nodeSpecificKey);
                if (!action) {
                    action = globalContext.get("action.all") || "";
                    node.debug("No actions found for node, Using global actions");
                } else {
                    node.debug("Using node-specific actions");
                }

                // Create a JSON for user content by combining envPrompt, state, and action
                const userContentObj = {
                    envPrompt: envPrompt,
                    state: state,
                    action: action
                };

                // Convert the combined content to a string
                const userContent = JSON.stringify(userContentObj);
                
                messages.push({
                    role: "user",
                    content: userContent
                });
            }

            // Prepare the request payload
            const payload = {
                model: model,
                messages: messages,
                stream: false
            };

            // Add temperature if configured
            if (config.temperature) {
                payload.temperature = parseFloat(config.temperature);
            }

            // Add max_tokens if configured
            if (config.maxTokens) {
                payload.max_tokens = parseInt(config.maxTokens);
            }

            // Get API key from credentials
            const apiKey = node.credentials.apiKey;
            
            if (!apiKey) {
                node.error("No API key provided", msg);
                node.status({fill:"red", shape:"ring", text:"No API key"});
                if (done) done("No API key provided");
                return;
            }

            node.status({fill:"blue", shape:"dot", text:"Requesting..."});
            
            // Set flow.agentstate to 'processing'
            node.context().flow.set('agentstate', 'processing');
            
            // Make the request to Deepseek API
            axios({
                method: 'post',
                url: 'https://api.deepseek.com/chat/completions',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                data: payload
            })
            .then(response => {
                // Set flow.agentstate to 'received'
                node.context().flow.set('agentstate', 'received');
                
                // Send the complete API response in msg.payload
                msg.payload = response.data;
                msg.deepseekRequest = payload;
                
                // Extract message content and reasoning content
                if (response.data && 
                    response.data.choices && 
                    response.data.choices.length > 0 && 
                    response.data.choices[0].message) {
                    
                    // Get the content from the response
                    msg.result = response.data.choices[0].message.content;
                    
                    // Get the reasoning_content if available
                    if (response.data.choices[0].message.reasoning_content) {
                        msg.reasoning_content = response.data.choices[0].message.reasoning_content;
                    }
                }
                
                node.status({fill:"green", shape:"dot", text:"Success"});
                send(msg);
                if (done) done();
            })
            .catch(error => {
                // Handle errors
                node.error("Deepseek API error: " + (error.response ? JSON.stringify(error.response.data) : error.message), msg);
                msg.payload = error.response ? error.response.data : error.message;
                msg.deepseekError = error.message;
                node.status({fill:"red", shape:"dot", text:"Error: " + error.message});
                send(msg);
                if (done) done(error);
            });
        });

        this.on('close', function() {
            // Clean up when node is removed or redeployed
            node.status({});
        });
    }

    RED.nodes.registerType("factory-agent-deepseek", FactoryAgentDeepseek, {
        credentials: {
            apiKey: {type: "password"}
        }
    });
}