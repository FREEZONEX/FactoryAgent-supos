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
            let systemPrompt = msg.sysPrompt || "You are a helpful assistant.";
            
            // Prepare the contents array
            const contents = [];
            
            // Add system message as a role
            if (systemPrompt) {
                contents.push({
                    role: "system",
                    parts: [{ text: systemPrompt }]
                });
            }
            
            // Check if msg.payload exists
            if (msg.hasOwnProperty('payload')) {
                // If payload exists, use it directly as user message content
                contents.push({
                    role: "user",
                    parts: [{ 
                        text: typeof msg.payload === 'string' ? msg.payload : JSON.stringify(msg.payload) 
                    }]
                });
            } else {
                // If no payload, use the original logic with envPrompt, state, and action
                let envPrompt = msg.envPrompt || "";
                let state = msg.state || "";
                const globalContext = node.context().global;
                const action = globalContext.get("action") || "";
                
                // Create a JSON for user content by combining envPrompt, state, and action
                const userContentObj = {
                    envPrompt: envPrompt,
                    state: state,
                    action: action
                };

                // Convert the combined content to a string
                const userContent = JSON.stringify(userContentObj);
                
                contents.push({
                    role: "user",
                    parts: [{ text: userContent }]
                });
            }

            // Prepare the request payload
            const payload = {
                contents: contents,
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