# factory-agent-actions

[English](#english) | [中文](#中文)

## English

A Node-RED node that allows users to create multiple actions with descriptions and parameters, storing them in the global context for use by other nodes.

### Features

- Add multiple actions with descriptions
- Each action can have multiple parameters with type and description
- Parameter types support all JSON data types (string, number, boolean, object, array, null)
- Elegant interface to add and remove actions and parameters
- **Configuration-only node with no inputs or outputs**
- **Automatically stores all actions in `global.action` upon deployment**
- Suitable for factory automation and process control scenarios

### Installation

Install using npm:

```bash
npm install factory-agent-actions
```

Or through the Node-RED Palette Manager:

1. Open Node-RED
2. Navigate to Menu -> Manage Palette
3. Search for "factory-agent-actions"
4. Click Install

### Usage

1. Drag the node from the "Factory Agent" category to your workspace
2. Double-click the node to open the configuration panel
3. Click the "Add Action" button to create new actions
4. Enter a name and description for each action
5. Add parameters to each action as needed
6. Click "Done" to save the configuration
7. Deploy your flow

When the node is deployed, all configured actions are automatically stored in the global context variable `global.action`. This makes the actions accessible to other nodes in your flow.

This is a configuration-only node that doesn't have inputs or outputs. It doesn't process messages but serves as a central repository for action definitions.

### Accessing Actions from Other Nodes

You can access the actions from any function node in your flow:

```javascript
// In a function node
const actions = global.get('action');

// Access a specific action description
const actionDescription = actions.actions.MyAction.description;

// Access a specific parameter
const paramType = actions.actions.MyAction.parameters.myParam.type;
```

### License

MIT

---

## 中文

一个允许用户创建多个操作（Actions）及其描述和参数的Node-RED节点，并将它们存储在全局上下文中供其他节点使用。

### 功能

- 允许用户定义多个操作和描述
- 每个操作可以包含多个带有类型和描述的参数
- 参数类型支持所有JSON数据类型（字符串、数字、布尔值、对象、数组、空值）
- 优雅的界面用于添加和删除操作与参数
- **纯配置节点，无输入和输出端口**
- **部署节点时自动将所有操作信息存储到`global.action`全局变量中**
- 适用于工厂自动化和流程控制场景

### 安装

使用npm安装:

```bash
npm install factory-agent-actions
```

或者通过Node-RED的面板管理器安装:

1. 打开Node-RED
2. 导航到菜单 -> 管理面板
3. 搜索 "factory-agent-actions"
4. 点击安装

### 使用方法

1. 从"Factory Agent"类别中拖动节点到工作区
2. 双击节点打开配置面板
3. 点击"添加Action"按钮创建新操作
4. 为每个操作填写名称和描述
5. 根据需要为每个操作添加参数
6. 点击"完成"保存配置
7. 部署您的流程

当节点部署时，所有配置的操作会自动存储到全局上下文变量`global.action`中。这使得这些操作可以被流程中的其他节点访问。

这是一个纯配置节点，没有输入或输出端口。它不处理消息，而是作为操作定义的中央存储库。

### 从其他节点访问操作

您可以从流程中的任何函数节点访问这些操作：

```javascript
// 在函数节点中
const actions = global.get('action');

// 访问特定操作的描述
const actionDescription = actions.actions.MyAction.description;

// 访问特定参数
const paramType = actions.actions.MyAction.parameters.myParam.type;
```

### 许可证

MIT