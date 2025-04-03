// actions.js
// 3rd April 2025: 
// Now it can specify the target agent node dynamically where to store the actions defined.
// When the target agent node is not specified, it will be stored in global.action.
// Otherwise, it will be stored in global.action.<node_id>
// When this action node is deleted or disabled, it will clean up all the actions stored before.

module.exports = function(RED) {
    function ActionsNode(config) {
        RED.nodes.createNode(this, config);
        const node = this;
        
        // Get actions array from config
        this.actions = config.actions || [];
        this.agentNode = config.agentNode || "global";

        // Create JSON object for global context
        const actionsJson = {
            actions: {}
        };
        
        // Debug: 检查传入的配置
        node.debug("Actions config data: " + JSON.stringify(this.actions));
        node.debug("Target agent node: " + this.agentNode);

        // Add each action with nested parameters to global context
        this.actions.forEach(action => {
            const actionName = action.name;
            const params = {};
            
            // Add parameters if available
            if (Array.isArray(action.parameters) && action.parameters.length > 0) {
                action.parameters.forEach(param => {
                    if (param.name && param.name.trim() !== '') {
                        params[param.name] = {
                            type: param.type || 'string',
                            description: param.description || ''
                        };
                    }
                });
            }
            
            // Add action to JSON
            actionsJson.actions[actionName] = {
                description: action.description || '',
                parameters: params
            };
        });
        node.debug("Prepared actions JSON: " + JSON.stringify(actionsJson));

        
        if (this.agentNode === "global") {
            // If global is selected, save to global.action
            node.debug("Saving actions to global.action");
            const global = node.context().global;
            global.set('action.all', actionsJson);
            this.status({fill:"green", shape:"dot", text:"Actions: " + Object.keys(actionsJson.actions).length + " (Global)"});
        } else {
            // If a specific node is selected, try to save to that node
            try {
                const global = node.context().global;
                const nodeSpecificKey = 'action.' + this.agentNode;
                node.debug("Saving actions to " + nodeSpecificKey);
                global.set(nodeSpecificKey, actionsJson);


                this.status({fill:"green", shape:"dot", text:"Actions: " + 
                Object.keys(actionsJson.actions).length + " (For " + this.agentNode + ")"});

            } catch (error) {
                node.error("Error saving actions to specific node: " + error.message);
                const global = node.context().global;
                global.set('action', actionsJson);
                this.status({fill:"yellow", shape:"dot", text:"Error: " + error.message});
            }
        }

        // Close event to clean up
        this.on('close', function(removed, done) {
            // This node has been disabled/deleted or is being restarted
            const global = node.context().global;
            if (node.agentNode === "global") {
                // Clean up global action
                node.debug("Node closing, cleaning up global action");
                global.set('action', undefined);
            } else {
                // Clean up specific node action
                const nodeSpecificKey = 'action.' + node.agentNode;
                node.debug("Node closing, cleaning up: " + nodeSpecificKey);
                global.set(nodeSpecificKey, undefined);
            }
            if (done) {
                done();
            }
        });

    }

    // Register node with RED
    RED.nodes.registerType("actions", ActionsNode);
}