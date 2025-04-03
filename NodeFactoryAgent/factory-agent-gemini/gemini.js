module.exports = function(RED) {
    function FactoryAgentGemini(config) {
        RED.nodes.createNode(this, config);
        const node = this;
        const axios = require('axios');

        this.on('input', function(msg, send, done) {
            // Use the original message object if send is available (Node-RED 1.0+)
            send = send || function() { node.send.apply(node, arguments); };

            // Get model from config or use default
            const model = config.model || "gemini-2.0-flash";
            
            // Prepare user text content
            let userText = "";
            
            // Add system prompt as part of user text if available
            if (msg.sysPrompt) {
                userText += `Instructions: ${msg.sysPrompt}\n\n`;
            }
            
            // Check if msg.payload exists
            if (msg.hasOwnProperty('payload')) {
                // If payload exists, append it to the user message
                if (userText) {
                    userText += "User Input: ";
                }
                userText += typeof msg.payload === 'string' ? msg.payload : JSON.stringify(msg.payload);
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
                
                // Append environment context
                if (envPrompt) {
                    userText += `Environment Context: ${envPrompt}\n\n`;
                }
                
                // Append state information
                if (state) {
                    userText += `Current State: ${state}\n\n`;
                }
                
                // Append action information
                if (action) {
                    // userText += `Action: ${action}\n\n`;
                    //Action load fail fixed: Use JSON.stringify to convert the action object to a string
                    userText += `Action: ${JSON.stringify(action)}\n\n`;

                }
                
                // If there's no content after processing, provide a default
                if (!userText.trim()) {
                    userText = "Please provide a response.";
                }
            }
            
            // Prepare the request payload - only using "user" role
            const payload = {
                contents: [
                    {
                        role: "user",
                        parts: [{ text: userText }]
                    }
                ],
                generationConfig: {}
            };

            // Add temperature if configured
            if (config.temperature) {
                payload.generationConfig.temperature = parseFloat(config.temperature);
            }

            // Add max_tokens if configured
            if (config.maxTokens) {
                payload.generationConfig.maxOutputTokens = parseInt(config.maxTokens);
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
            
            // Construct the URL with the API key and model
            const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
            
            // Make the request to Gemini API
            axios({
                method: 'post',
                url: url,
                headers: {
                    'Content-Type': 'application/json'
                },
                data: payload
            })
            .then(response => {
                // Set flow.agentstate to 'received'
                node.context().flow.set('agentstate', 'received');
                
                // Send the complete API response in msg.payload
                msg.payload = response.data;
                msg.geminiRequest = payload;
                
                // Extract message content
                if (response.data && 
                    response.data.candidates && 
                    response.data.candidates.length > 0 && 
                    response.data.candidates[0].content) {
                    
                    // Get the content from the response (join all parts)
                    const parts = response.data.candidates[0].content.parts;
                    msg.result = parts.map(part => part.text).join("");
                    
                    // Store any additional useful information
                    if (response.data.candidates[0].finishReason) {
                        msg.finishReason = response.data.candidates[0].finishReason;
                    }
                }
                
                node.status({fill:"green", shape:"dot", text:"Success"});
                send(msg);
                if (done) done();
            })
            .catch(error => {
                // Handle errors
                node.error("Gemini API error: " + (error.response ? JSON.stringify(error.response.data) : error.message), msg);
                msg.payload = error.response ? error.response.data : error.message;
                msg.geminiError = error.message;
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

    RED.nodes.registerType("factory-agent-gemini", FactoryAgentGemini, {
        credentials: {
            apiKey: {type: "password"}
        }
    });
}