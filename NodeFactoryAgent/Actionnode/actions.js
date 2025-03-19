// actions.js - 修复参数保存问题
module.exports = function(RED) {
    function ActionsNode(config) {
        RED.nodes.createNode(this, config);
        const node = this;
        
        // Get actions array from config
        this.actions = config.actions || [];
        
        // Create JSON object for global context
        const actionsJson = {
            actions: {}
        };
        
        // Debug: 检查传入的配置
        node.debug("Actions config data: " + JSON.stringify(this.actions));
        
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
        
        // Debug: 记录最终结果
        node.debug("Saving actions to global.action: " + JSON.stringify(actionsJson));
        
        // Store actions in global.action
        const global = node.context().global;
        global.set('action', actionsJson);
        
        // Register node status update
        this.status({fill:"green", shape:"dot", text:"Actions: " + Object.keys(actionsJson.actions).length});
    }
    
    // Register node with RED
    RED.nodes.registerType("actions", ActionsNode);
}