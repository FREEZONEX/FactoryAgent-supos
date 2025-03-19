# 工厂生产模拟系统文档

## 目录

1. [系统概述](#系统概述)
2. [技术架构](#技术架构)
3. [核心概念](#核心概念)
4. [模拟参数设置](#模拟参数设置)
5. [系统功能模块](#系统功能模块)
6. [适应性策略](#适应性策略)
7. [干扰事件](#干扰事件)
8. [MQTT通信](#mqtt通信)
9. [指标监控与日志](#指标监控与日志)
10. [系统运行指南](#系统运行指南)
11. [扩展与定制](#扩展与定制)

## 系统概述

工厂生产模拟系统是一个基于SimPy的离散事件模拟框架，结合MQTT通信协议的工业生产环境模拟系统。该系统模拟了一个制造工厂的完整生产流程，包括原材料供应、零部件生产、产品组装、质量控制以及订单处理等环节。系统内置了多种随机干扰事件和适应性策略，用于模拟真实工厂环境中的不确定性和应对措施。

### 主要特点

- **完整生产流程模拟**：从原材料到成品的全流程模拟
- **实时监控与交互**：通过MQTT实现数据发布和控制指令接收
- **多种干扰事件**：模拟设备故障、订单波动、供应链中断等真实场景
- **适应性策略**：提供多种应对干扰的战略和战术选择
- **详细指标追踪**：全面监控生产、质量、能源、财务等关键指标
- **可视化接口准备**：提供结构化数据输出，便于外部系统构建可视化界面

## 技术架构

### 核心技术栈

- **SimPy**：离散事件模拟框架，用于模拟工厂生产流程
- **MQTT**：轻量级消息发布/订阅协议，用于系统通信
- **Python**：系统实现语言，包含各种功能模块
- **Paho-MQTT**：MQTT客户端库，用于MQTT通信实现

### 系统架构图

```
+---------------------------+
|      模拟环境管理器        |
|   MQTTSimulationManager   |
+---------------------------+
              |
              v
+---------------------------+       +------------------+
|        工厂模拟核心        | <---> |   MQTT通信模块   |
|      MQTTValueFactory     |       +------------------+
+---------------------------+              |
              |                            |
  +-----------+-----------+                |
  |           |           |                v
+-------+ +-------+ +------------+  +----------------+
| 生产线 | | 物流链 | | 质量控制链 |  | 外部监控/控制 |
+-------+ +-------+ +------------+  +----------------+
```

### 模块关系

1. **模拟环境管理器**：管理整个模拟环境的生命周期，包含时间推进和异常处理
2. **工厂模拟核心**：实现工厂各个功能模块和流程，管理资源分配和状态转换
3. **MQTT通信模块**：负责数据发布和指令接收，实现系统与外部的交互
4. **生产线**：CNC机器和组装站模拟，处理零部件和产品生产
5. **物流链**：原材料订购、库存管理和订单处理
6. **质量控制链**：产品检验和质量指标计算

## 核心概念

### 资源(Resources)

系统模拟了四种关键资源，这些资源的可用性直接影响生产能力：

1. **CNC机器(cnc_machines)**：用于零部件加工的数控机床
2. **组装站(assembly_stations)**：用于将零部件组装成成品的工作站
3. **质检站(qc_stations)**：用于产品质量检测的工作站
4. **工人(workers)**：操作各种设备的工人

### 库存(Inventory)

系统跟踪三种库存类型：

1. **原材料(raw_materials)**：用于加工零部件的原始材料
2. **零部件库存(parts_inventory)**：已加工但尚未组装的零部件
3. **成品(finished_products)**：已完成质检可交付的成品

### 订单(Orders)

订单管理包含以下指标：

1. **总订单(total_orders)**：接收的所有订单总数
2. **已完成订单(fulfilled_orders)**：已交付的订单数量
3. **积压订单(backlog)**：待处理的订单数量
4. **已取消订单(cancelled_orders)**：被取消的订单数量

### 财务(Finances)

系统跟踪多种财务指标：

1. **收入(revenue)**：产品销售收入
2. **成本(costs)**：生产成本、维护成本等
3. **库存持有成本(inventory_holding_costs)**：存储库存的财务成本
4. **能源成本(energy_costs)**：工厂能源消耗成本
5. **清算收入(liquidation_revenue)**：库存清算产生的收入

## 模拟参数设置

### 模拟常量

```python
# 模拟常量
SIMULATION_DAYS = 60                 # 模拟天数
REAL_TIME_FACTOR = 100               # 现实与模拟时间比例(5分钟模拟=1分钟现实)
MQTT_UPDATE_INTERVAL = 1             # MQTT数据发布间隔(秒)
MQTT_MIN_PUBLISH_INTERVAL = 1        # 同一主题最小发布间隔(秒)
```

### 工厂设置

```python
# 工厂设置
NUM_CNC_MACHINES = 5                 # CNC机器数量
NUM_ASSEMBLY_STATIONS = 4            # 组装站数量
NUM_QC_STATIONS = 3                  # 质检站数量
NUM_WORKERS = 12                     # 工人数量
INITIAL_INVENTORY = 80               # 初始零部件库存
INITIAL_RAW_MATERIALS = 500          # 初始原材料数量
```

### 生产参数

```python
# 生产参数
CNC_PROCESSING_TIME = 45             # 每个零部件加工时间(分钟)
ASSEMBLY_TIME = 30                   # 每个产品组装时间(分钟)
QC_INSPECTION_TIME = 15              # 每批产品质检时间(分钟)
PARTS_PER_PRODUCT = 3                # 每个产品所需零部件数量
NORMAL_ORDER_RATE = 15               # 正常订单量(每天产品数)
DELIVERY_TIME = 2 * 24 * 60          # 原材料交付时间(分钟)
```

### 成本参数

```python
# 工人薪资成本
WORKER_HOURLY_WAGE = 25              # 工人小时工资($25/小时)
WORKER_SHIFT_HOURS = 8               # 标准班次时长(8小时)
WORKER_SHIFTS_PER_DAY = 3            # 每天班次数(3班制覆盖24小时)
WORKER_BENEFITS_FACTOR = 1.3         # 福利因子(工资的30%)

# 库存成本
RAW_MATERIAL_COST = 70               # 原材料单位成本($)
INVENTORY_HOLDING_COST_RATE = 0.002  # 每日库存持有成本率(0.2%)
PARTS_VALUE = 120                    # 加工零部件价值($)
FINISHED_PRODUCT_VALUE = 550         # 成品价值($，售价前)

# 能源成本
ENERGY_COST_PER_KWH = 0.6            # 能源成本($/kWh)
CNC_ENERGY_USAGE = 35.5              # CNC机器能耗(kWh/小时)
ASSEMBLY_ENERGY_USAGE = 10.0         # 组装站能耗(kWh/小时)
QC_ENERGY_USAGE = 10.5               # 质检站能耗(kWh/小时)
FACILITY_BASE_ENERGY = 35.0          # 基础设施能耗(kWh/小时)
```

### 事件频率

```python
# 事件频率(每天概率)
CNC_FAILURE_CHANCE = 0.15            # CNC机器故障概率
SUDDEN_ORDER_SPIKE_CHANCE = 0.05     # 订单突增概率
SUPPLY_CHAIN_ISSUE_CHANCE = 0.08     # 供应链问题概率
WORKER_ABSENCE_CHANCE = 0.08         # 工人缺勤概率
QUALITY_ISSUE_CHANCE = 0.07          # 质量问题概率
POWER_OUTAGE_CHANCE = 0.1            # 断电概率
ORDER_CANCELLATION_CHANCE = 0.1      # 订单取消概率
```

## 系统功能模块

### 1. 生产流程模块

#### 零部件生产(produce_parts)

```python
def produce_parts(self):
    """从原材料生产零部件的流程"""
    while True:
        # 检查是否停电
        if self.power_outage:
            yield self.env.timeout(10)  # 10分钟后再检查
            continue
            
        # 检查资源可用性
        if self.raw_materials <= 0 or self.operational_cnc_machines <= 0 or self.available_workers <= 0:
            yield self.env.timeout(10)
            continue
        
        # 请求CNC机器和工人资源
        with self.cnc_machines.request() as cnc_req:
            yield cnc_req
            with self.workers.request() as worker_req:
                yield worker_req
                
                # 更新资源请求计数
                self.active_cnc_requests += 1
                self.active_worker_requests += 1
                
                # 计算批量大小
                batch_size = min(15, self.raw_materials)
                
                if batch_size <= 0:
                    self.active_cnc_requests -= 1
                    self.active_worker_requests -= 1
                    continue
                
                # 消耗原材料
                self.raw_materials -= batch_size
                
                # 计算处理时间
                process_time = CNC_PROCESSING_TIME * batch_size
                
                # 精益生产优化
                if AdaptationStrategy.LEAN_MANUFACTURING in self.adaptation_strategies:
                    process_time *= 0.8  # 节省20%时间
                
                # 生产过程
                yield self.env.timeout(process_time)
                
                # 零部件入库
                self.parts_inventory += batch_size
                
                # 添加生产成本
                self.costs += batch_size * 30
                
                # 释放资源计数
                self.active_cnc_requests -= 1
                self.active_worker_requests -= 1
```

#### 产品组装(assemble_products)

```python
def assemble_products(self):
    """将零部件组装成产品的流程"""
    while True:
        # 检查条件
        if self.power_outage:
            yield self.env.timeout(10)
            continue
            
        if self.parts_inventory < PARTS_PER_PRODUCT or self.available_workers <= 0:
            yield self.env.timeout(60)
            continue
        
        # 跟踪工人请求
        self.active_worker_requests += 1
        
        if self.active_worker_requests > self.available_workers:
            self.active_worker_requests -= 1
            yield self.env.timeout(60)
            continue
        
        # 请求组装站和工人
        with self.assembly_stations.request() as assembly_req, self.workers.request() as worker_req:
            yield assembly_req & worker_req
            
            # 计算批量大小
            max_products = self.parts_inventory // PARTS_PER_PRODUCT
            batch_size = min(5, max_products)
            
            # 消耗零部件
            self.parts_inventory -= batch_size * PARTS_PER_PRODUCT
            
            # 计算组装时间
            assembly_time = ASSEMBLY_TIME * batch_size
            
            # 精益生产优化
            if AdaptationStrategy.LEAN_MANUFACTURING in self.adaptation_strategies:
                assembly_time *= 0.8
            
            # 组装过程
            yield self.env.timeout(assembly_time)
            
            # 考虑质量问题
            if self.has_quality_issue and random.random() < 0.3:
                # 缺陷产品
                good_products = int(batch_size * 0.7)
                assembled_products = good_products
            else:
                assembled_products = batch_size
            
            # 添加组装成本
            self.costs += batch_size * 50
            
            # 产品送去质检
            for i in range(assembled_products):
                self.env.process(self.product_to_qc())
            
            # 释放工人
            self.active_worker_requests -= 1
```

#### 质量控制(product_to_qc, quality_control)

```python
def product_to_qc(self):
    """单个产品质量控制流程"""
    # 质检站请求
    if self.power_outage:
        yield self.env.timeout(10)
        return
        
    self.active_qc_requests += 1
    
    with self.qc_stations.request() as qc_req, self.workers.request() as worker_req:
        yield qc_req & worker_req
        
        # 质检时间
        inspection_time = QC_INSPECTION_TIME
        yield self.env.timeout(inspection_time)
        
        # 更新质检指标
        self.total_inspected += 1
        
        # 判断产品质量
        is_defective = random.random() < self.defect_rate
        defect_detected = False
        
        # 缺陷检测逻辑
        if is_defective:
            # 检测真实缺陷的概率
            detection_chance = 0.9
            if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                detection_chance = 0.98
            
            if random.random() < detection_chance:
                defect_detected = True
                self.defects_found += 1
            else:
                # 漏检(假阴性)
                self.false_negatives += 1
        else:
            # 误判(假阳性)概率
            false_positive_chance = 0.05
            if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                false_positive_chance = 0.02
            
            if random.random() < false_positive_chance:
                defect_detected = True
                self.false_positives += 1
        
        # 合格产品入库
        if not defect_detected:
            self.finished_products += 1
        
        # 释放资源
        self.active_qc_requests -= 1
        
        # 处理积压订单
        self.process_backlog()
```

### 2. 订单处理模块

#### 订单生成(generate_orders)

```python
def generate_orders(self):
    """按当前速率生成客户订单"""
    while True:
        # 等待一天
        yield self.env.timeout(24 * 60)
        
        # 重置每日生产计数
        self.daily_production = 0
        
        # 基于当前速率计算每日订单
        daily_orders = int(self.current_order_rate)
        
        # 添加随机变化(±40%)
        daily_orders = int(daily_orders * random.uniform(0.6, 1.4))
        
        # 记录新订单
        self.total_orders += daily_orders
        self.backlog += daily_orders
        
        # 处理积压订单
        self.process_backlog()
        
        # 根据需要订购原材料
        if self.raw_materials < 200 and not self.supply_chain_disrupted:
            self.env.process(self.order_raw_materials())
```

#### 订单处理(process_backlog)

```python
def process_backlog(self):
    """处理积压订单"""
    # 计算可供交付的产品数量
    available_products = min(self.finished_products, self.backlog)
    
    # 履行订单
    if available_products > 0:
        self.finished_products -= available_products
        self.backlog -= available_products
        self.fulfilled_orders += available_products
        self.daily_production += available_products
        
        # 计算收入
        product_price = 1500
        batch_revenue = available_products * product_price
        self.revenue += batch_revenue
        
        if available_products >= 10:
            self.log(LogLevel.INFO, "Sales", 
                    f"出货 {available_products} 产品，收入 ${batch_revenue:,}")
```

#### 原材料订购(order_raw_materials)

```python
def order_raw_materials(self):
    """订购新原材料"""
    # 订购500单位原材料
    order_amount = 500
    
    # 即时补货优化
    if AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT in self.adaptation_strategies:
        # 基于积压和生产率计算需求
        backlog_demand = self.backlog * PARTS_PER_PRODUCT
        daily_part_demand = (self.current_order_rate * PARTS_PER_PRODUCT)
        
        # 计算智能订单量
        safety_factor = 1.15
        needed_parts = max(0, backlog_demand - self.parts_inventory) + (daily_part_demand * 5)
        needed_raw = needed_parts * safety_factor
        
        # 调整订单量，最小500，最大1000
        order_amount = max(500, min(1000, int(needed_raw)))
        
        self.log(LogLevel.INFO, "Inventory", 
                f"JIT系统优化订单: 基于需求分析订购{order_amount}原材料")
    
    # 添加原材料成本
    self.costs += order_amount * RAW_MATERIAL_COST
    
    # 计算交付时间
    delivery_time = DELIVERY_TIME
    
    # JIT系统减少交付时间
    if AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT in self.adaptation_strategies:
        delivery_time *= 0.7
    
    # 如果供应链中断，交付时间延长
    if self.supply_chain_disrupted:
        delivery_time *= 2
    
    # 等待交付
    yield self.env.timeout(delivery_time)
    
    # 接收原材料
    self.raw_materials += order_amount
```

### 3. 监控与计算模块

#### 能源使用计算(calculate_energy_usage)

```python
def calculate_energy_usage(self):
    """计算和累积能源使用与成本"""
    while True:
        # 每小时计算一次
        yield self.env.timeout(60)
        
        # 停电期间跳过
        if self.power_outage:
            continue
            
        # 计算每小时能源使用
        hourly_cnc_energy = (self.operational_cnc_machines * CNC_ENERGY_USAGE * 
                            (self.cnc_utilization / 100))
        
        hourly_assembly_energy = (NUM_ASSEMBLY_STATIONS * ASSEMBLY_ENERGY_USAGE * 
                                 (self.assembly_utilization / 100))
        
        hourly_qc_energy = (NUM_QC_STATIONS * QC_ENERGY_USAGE * 
                           (self.qc_utilization / 100))
        
        hourly_facility_energy = FACILITY_BASE_ENERGY
        
        # 峰值负载优化
        if AdaptationStrategy.PEAK_LOAD_OPTIMIZATION in self.adaptation_strategies:
            peak_hours = self.current_time % (24 * 60) >= 8 * 60 and self.current_time % (24 * 60) <= 17 * 60
            
            if peak_hours:
                energy_reduction = 0.15  # 高峰期减少15%
                hourly_cnc_energy *= (1 - energy_reduction)
                hourly_assembly_energy *= (1 - energy_reduction)
                hourly_qc_energy *= (1 - energy_reduction)
            else:
                energy_reduction = 0.05  # 非高峰期减少5%
                hourly_facility_energy *= (1 - energy_reduction)
        
        # 更新能源使用指标
        self.cnc_energy_usage += hourly_cnc_energy
        self.assembly_energy_usage += hourly_assembly_energy
        self.qc_energy_usage += hourly_qc_energy
        self.facility_energy_usage += hourly_facility_energy
        
        # 计算总能源和成本
        hourly_total_energy = hourly_cnc_energy + hourly_assembly_energy + hourly_qc_energy + hourly_facility_energy
        self.total_energy_usage += hourly_total_energy
        self.energy_costs += hourly_total_energy * ENERGY_COST_PER_KWH
```

#### OEE计算(calculate_oee)

```python
def calculate_oee(self):
    """计算设备综合效率(OEE)指标"""
    while True:
        # 每小时计算一次
        yield self.env.timeout(60)
        
        # 停电期间跳过
        if self.power_outage:
            continue
        
        # 计算可用性
        # 设备计划时间内可使用的百分比
        total_machines = NUM_CNC_MACHINES
        if total_machines > 0:
            self.availability = self.operational_cnc_machines / total_machines
        else:
            self.availability = 0
        
        # 计算性能
        # 实际生产速率与最大能力速率的百分比
        max_daily_production = (24 * 60) / CNC_PROCESSING_TIME * self.operational_cnc_machines / PARTS_PER_PRODUCT
        if max_daily_production > 0:
            self.performance = min(1.0, self.daily_production / max_daily_production)
        else:
            self.performance = 0
        
        # 计算质量
        # 生产的优质产品百分比
        self.quality = 1.0 - self.defect_rate
        
        # 计算总体OEE
        self.oee = self.availability * self.performance * self.quality
```

#### 传感器数据更新(update_sensor_data)

```python
def update_sensor_data(self):
    """定期更新传感器读数"""
    while True:
        # 每10分钟更新一次
        yield self.env.timeout(10)
        
        # 停电期间跳过
        if self.power_outage:
            continue
        
        # 更新环境条件(轻微随机变化)
        self.ambient_temperature = max(15, min(30, 
            self.ambient_temperature + random.uniform(-0.5, 0.5)))
        self.ambient_humidity = max(30, min(70, 
            self.ambient_humidity + random.uniform(-1, 1)))
        
        # 更新CNC机器温度和振动
        for i in range(NUM_CNC_MACHINES):
            # 仅更新运行中的机器
            if i < self.operational_cnc_machines:
                # 温度随使用率增加并有随机变化
                base_temp = 20 + (self.cnc_utilization / 100) * 40  # 闲置20°C，满载最高60°C
                
                # 机器长时间运行温度升高
                operation_factor = 1.0
                
                # 高振动可能表示即将故障
                failure_warning = 1.0
                
                # 如果此机器即将故障，显示警告信号
                if (i == 0 and random.random() < CNC_FAILURE_CHANCE/50 and 
                    AdaptationStrategy.PREVENTIVE_MAINTENANCE not in self.adaptation_strategies):
                    operation_factor = 1.2  # 温度高20%
                    failure_warning = 2.0   # 振动高2倍
                
                # 计算所有因素下的温度
                self.cnc_temperatures[i] = base_temp * operation_factor + random.uniform(-3, 3)
                
                # 计算振动(随使用率增加)
                base_vibration = 0.1 + (self.cnc_utilization / 100) * 1.5  # 闲置0.1，满载最高1.6
                self.cnc_vibrations[i] = base_vibration * failure_warning + random.uniform(-0.1, 0.1)
            else:
                # 已关闭的机器降温至环境温度
                if self.cnc_temperatures[i] > self.ambient_temperature:
                    self.cnc_temperatures[i] = max(self.ambient_temperature, 
                                                self.cnc_temperatures[i] - random.uniform(0.5, 1.5))
                # 关机状态无振动
                self.cnc_vibrations[i] = 0.0
```

### 4. MQTT通信模块

#### MQTT连接设置(setup_mqtt)

```python
def setup_mqtt(self):
    """设置MQTT客户端连接和订阅"""
    self.mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    
    # 设置认证(如需要)
    if MQTT_USERNAME and MQTT_PASSWORD:
        self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # 设置回调
    self.mqtt_client.on_connect = self.on_mqtt_connect
    self.mqtt_client.on_message = self.on_mqtt_message
    
    # 连接到代理
    try:
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.mqtt_client.loop_start()
        print(f"已连接到MQTT代理 {MQTT_BROKER}:{MQTT_PORT}")
        self.log(LogLevel.INFO, "System", f"已连接到MQTT代理 {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        error_msg = f"连接MQTT代理错误: {e}"
        print(error_msg)
        self.log(LogLevel.ERROR, "System", error_msg)
        sys.exit(1)
```

#### MQTT数据发布(publish_mqtt_updates)

```python
def publish_mqtt_updates(self):
    """定期发布工厂数据到MQTT主题"""
    while True:
        # 非暂停状态下发布
        if not self.paused:
            # 库存数据
            self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/rawMaterials", 
                                    json.dumps({"value": self.raw_materials}))
            self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/partsInventory", 
                                    json.dumps({"value": self.parts_inventory}))
            # ... 其他数据发布
            
            # 订单数据
            self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/totalOrders", 
                                    json.dumps({"value": self.total_orders}))
            # ... 其他数据发布
            
            # 计算实际可用工人数量
            actual_available_workers = max(0, NUM_WORKERS - self.workers.count)
            
            # 资源数据
            self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/operationalCncMachines", 
                                    json.dumps({"value": self.operational_cnc_machines}))
            # ... 其他数据发布
            
            # 财务数据
            self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/revenue", 
                                    json.dumps({"value": self.revenue}))
            # ... 其他数据发布
            
            # 生产数据、质量数据、能源数据、OEE数据等各类数据发布
            # ... 其他数据发布
        
        # 等待下次更新
        yield self.env.timeout(MQTT_UPDATE_INTERVAL * 60 / REAL_TIME_FACTOR)
```

### 5. 干扰事件模块

系统实现了七类干扰事件模拟：

#### CNC机器故障(cnc_machine_failure)

```python
def cnc_machine_failure(self):
    """模拟CNC机器故障"""
    # 只有在有运行中的机器时才发生故障
    if self.operational_cnc_machines > 0:
        # 记录干扰事件
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.CNC_FAILURE.value,
            "description": "CNC机器发生故障"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰事件
        self.publish_disruption(DisruptionType.CNC_FAILURE.value, "CNC机器发生故障")
        
        # 记录维护指标
        self.maintenance_events += 1
        # 更新故障间隔时间指标
        if self.last_failure_time > 0:
            time_between_failures = self.env.now - self.last_failure_time
            # 更新MTBF为滚动平均值
            if self.maintenance_events > 1:
                self.mtbf = (self.mtbf * (self.maintenance_events - 1) + time_between_failures) / self.maintenance_events
            else:
                self.mtbf = time_between_failures
        self.last_failure_time = self.env.now
        
        # 将机器从服务中移除
        self.operational_cnc_machines -= 1
        
        # 确定修复时间 - 8至36小时
        repair_time = random.randint(8, 36) * 60  # 分钟
        repair_cost_base = 5000  # 基础修复成本
        
        # 模块化维修工具包策略可加快修复
        if AdaptationStrategy.MODULAR_REPAIR_KITS in self.adaptation_strategies:
            repair_time *= 0.6  # 缩短40%修复时间
            self.log(LogLevel.INFO, "Maintenance", 
                    "模块化维修工具包加快了修复速度")
        
        # KPI监控更快
        if AdaptationStrategy.KPI_MONITORING in self.adaptation_strategies:
            repair_time *= 0.85  # 额外减少15%
            repair_cost_base *= 0.9  # 降低10%修复成本
            self.log(LogLevel.INFO, "Maintenance", 
                    "实时KPI监控实现了早期问题检测")
        
        # 计算总修复成本(基础+小时)
        hourly_rate = 250  # 小时服务费率
        repair_cost = repair_cost_base + (repair_time / 60) * hourly_rate
        
        # 添加修复成本
        self.costs += repair_cost
        
        self.log(LogLevel.INFO, "Maintenance", 
                f"CNC修复将花费{repair_time/60:.1f}小时，成本${repair_cost:,.2f}")
        
        # 更新维护指标
        self.total_downtime += repair_time
        self.repair_times.append(repair_time)
        # 更新MTTR为滚动平均值
        self.mttr = sum(self.repair_times) / len(self.repair_times)
        
        # 等待修复时间
        yield self.env.timeout(repair_time)
        
        # 将机器恢复服务
        self.operational_cnc_machines += 1
        self.log(LogLevel.INFO, "Maintenance", "CNC机器修复完成并恢复服务")
```

#### 订单突增(order_spike)

```python
def order_spike(self):
    """模拟订单突然增加"""
    global ASSEMBLY_TIME, CNC_PROCESSING_TIME
    
    # 记录干扰
    disruption_data = {
        "time": self.env.now,
        "type": DisruptionType.ORDER_SPIKE.value,
        "description": "收到订单突增"
    }
    self.disruptions_history.append(disruption_data)
    
    # 通过MQTT发布干扰
    self.publish_disruption(DisruptionType.ORDER_SPIKE.value, "收到订单突增")
    
    # 计算峰值大小 - 正常速率的2-4倍
    spike_multiplier = random.uniform(2.0, 4.0)
    original_rate = self.current_order_rate
    self.current_order_rate = original_rate * spike_multiplier
    
    # 确定峰值持续时间 - 1至3天
    spike_duration = random.randint(1, 3) * 24 * 60
    
    # 计算峰值中的额外订单
    additional_orders = int((self.current_order_rate - original_rate) * (spike_duration / (24 * 60)))
    
    self.log(LogLevel.INFO, "Orders", 
            f"订单峰值: {additional_orders}额外订单，持续{spike_duration/60/24:.1f}天")
    
    # 如果外包策略激活，将更多订单外部处理
    if AdaptationStrategy.OUTSOURCING in self.adaptation_strategies:
        # 外包60%的额外订单
        outsourced_orders = int(additional_orders * 0.6)
        self.fulfilled_orders += outsourced_orders
        
        # 计算收入和成本
        outsource_revenue = outsourced_orders * 1500  # 每产品收入
        outsource_cost = outsourced_orders * 1200    # 每产品外包成本
        
        self.revenue += outsource_revenue
        self.costs += outsource_cost
        
        self.log(LogLevel.INFO, "Production", 
                f"外包{outsourced_orders}订单，收入${outsource_revenue:,}，成本${outsource_cost:,}")
    
    # 如果加班政策激活，增加生产能力
    if AdaptationStrategy.OVERTIME_POLICY in self.adaptation_strategies:
        # 临时提高工人效率
        overtime_factor = 1.3  # 加班效率提高30%
        old_assembly_time = ASSEMBLY_TIME
        old_cnc_time = CNC_PROCESSING_TIME
        
        ASSEMBLY_TIME /= overtime_factor
        CNC_PROCESSING_TIME /= overtime_factor
        
        # 计算加班成本
        overtime_hours = spike_duration / 60  # 转换为小时
        overtime_workers = min(NUM_WORKERS, NUM_CNC_MACHINES + NUM_ASSEMBLY_STATIONS)
        overtime_rate = 50  # $50/小时加班费率
        overtime_cost = overtime_hours * overtime_workers * overtime_rate * 0.5  # 假设50%的时间是加班
        
        self.costs += overtime_cost
        
        self.log(LogLevel.INFO, "Workforce", 
                f"实施加班政策，成本${overtime_cost:,.2f}")
        
        # 等待峰值持续时间
        yield self.env.timeout(spike_duration)
        
        # 恢复原始处理时间
        ASSEMBLY_TIME = old_assembly_time
        CNC_PROCESSING_TIME = old_cnc_time
    else:
        # 等待峰值持续时间
        yield self.env.timeout(spike_duration)
    
    # 恢复正常订单速率
    self.current_order_rate = original_rate
    self.log(LogLevel.INFO, "Orders", "订单速率恢复正常")
```

#### 供应链中断(supply_chain_disruption)

```python
def supply_chain_disruption(self):
    """模拟供应链中断"""
    if not self.supply_chain_disrupted:
        # 记录干扰
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.SUPPLY_CHAIN.value,
            "description": "影响原材料交付的供应链中断"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰
        self.publish_disruption(DisruptionType.SUPPLY_CHAIN.value, 
                              "影响原材料交付的供应链中断")
        
        self.supply_chain_disrupted = True
        
        # 确定中断持续时间 - 2至7天
        disruption_duration = random.randint(2, 7) * 24 * 60
        
        # 如果供应商多样化策略激活，减轻严重性
        if AdaptationStrategy.SUPPLIER_DIVERSIFICATION in self.adaptation_strategies:
            disruption_duration *= 0.5  # 缩短50%中断时间
        
        # 等待中断持续时间
        yield self.env.timeout(disruption_duration)
        
        self.supply_chain_disrupted = False
```

#### 工人缺勤(worker_absence)

```python
def worker_absence(self, max_absent=3):
    """模拟工人缺勤"""
    # 确定缺勤工人数量
    num_absent = random.randint(1, max_absent)
    num_absent = min(num_absent, self.available_workers)  # 不能有负数工人
    
    if num_absent > 0:
        # 记录干扰
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.WORKER_ABSENCE.value,
            "description": f"{num_absent}工人缺勤"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰
        self.publish_disruption(DisruptionType.WORKER_ABSENCE.value, f"{num_absent}工人缺勤")
        
        # 记录工人缺勤
        self.available_workers -= num_absent
        
        # 确定缺勤持续时间 - 1至3天
        absence_duration = random.randint(1, 3) * 24 * 60
        
        # 如果加班政策激活，添加加班成本
        if AdaptationStrategy.OVERTIME_POLICY in self.adaptation_strategies:
            # 加班补偿部分缺勤工人
            effective_absent = num_absent * 0.6
            # 添加加班成本
            self.costs += absence_duration / 60 * effective_absent * 30  # $30/小时/补偿工人
        
        # 等待缺勤持续时间
        yield self.env.timeout(absence_duration)
        
        # 工人返回工作
        self.available_workers += num_absent
```

#### 质量控制问题(quality_control_issue)

```python
def quality_control_issue(self, duration=8*60):  # 默认8小时
    """模拟质量控制问题"""
    if not self.has_quality_issue:
        # 记录干扰
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.QUALITY_ISSUE.value,
            "description": "生产中检测到质量控制问题"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰
        self.publish_disruption(DisruptionType.QUALITY_ISSUE.value, 
                              "生产中检测到质量控制问题")
        
        self.has_quality_issue = True
        
        # 确定有多少有缺陷的产品
        defective_rate = 0.4  # 问题期间40%缺陷率
        
        # 如果质量监控激活，减轻严重性
        if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
            defective_rate = 0.15  # 有监控时15%缺陷率
        
        # 计算当前库存的影响
        defective_products = int(self.finished_products * defective_rate)
        self.finished_products -= defective_products
        
        # 更新质量指标
        self.defect_rate = defective_rate
        self.defects_found += defective_products
        
        # 添加废品和返工成本
        self.costs += defective_products * 300  # 每个缺陷产品成本
        
        # 等待问题解决
        yield self.env.timeout(duration)
        
        self.has_quality_issue = False
        # 重置缺陷率为基准值
        self.defect_rate = 0.02
```

#### 停电事件(power_outage_event)

```python
def power_outage_event(self):
    """模拟影响整个工厂的停电"""
    if not self.power_outage:
        # 记录干扰
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.POWER_OUTAGE.value,
            "description": "影响整个工厂的停电"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰
        self.publish_disruption(DisruptionType.POWER_OUTAGE.value, 
                              "影响整个工厂的停电")
        
        self.power_outage = True
        
        # 确定停电持续时间 - 45分钟至6小时
        outage_duration = random.randint(45, 360)
        
        # 计算生产影响
        hourly_production_rate = self.current_order_rate / 24  # 近似小时速率
        estimated_lost_production = hourly_production_rate * (outage_duration / 60)
        
        # 峰值负载优化减轻停电影响
        if AdaptationStrategy.PEAK_LOAD_OPTIMIZATION in self.adaptation_strategies:
            original_duration = outage_duration
            outage_duration *= 0.6  # 减少40%
            
            self.log(LogLevel.INFO, "Power", 
                    f"峰值负载优化将停电从{original_duration}减少到{outage_duration}分钟")
        
        # 计算停电成本
        restart_cost = 5000  # 基础重启成本
        lost_production_cost = estimated_lost_production * FINISHED_PRODUCT_VALUE
        equipment_stress_cost = 250 * self.operational_cnc_machines  # 突然关机的设备磨损
        
        total_outage_cost = restart_cost + lost_production_cost + equipment_stress_cost
        self.costs += total_outage_cost
        
        self.log(LogLevel.WARNING, "Power", 
                f"停电将持续{outage_duration}分钟，预计成本${total_outage_cost:,.2f}")
        
        # 更新维护指标
        self.total_downtime += outage_duration
        
        # 等待电力恢复
        yield self.env.timeout(outage_duration)
        
        self.power_outage = False
        self.log(LogLevel.INFO, "Power", "电力已恢复，重启生产")
```

#### 订单取消(order_cancellation)

```python
def order_cancellation(self):
    """模拟现有订单取消"""
    if not self.order_cancellation_active and self.backlog > 0:
        # 记录干扰
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.ORDER_CANCELLATION.value,
            "description": "客户取消了大量订单"
        }
        self.disruptions_history.append(disruption_data)
        
        # 通过MQTT发布干扰
        self.publish_disruption(DisruptionType.ORDER_CANCELLATION.value, 
                              "客户取消了大量订单")
        
        self.order_cancellation_active = True
        
        # 计算将被取消的订单数(积压的20-50%)
        cancellation_rate = random.uniform(0.2, 0.5)
        orders_to_cancel = int(self.backlog * cancellation_rate)
        
        # 如果库存清算策略激活，减轻影响
        if AdaptationStrategy.INVENTORY_LIQUIDATION in self.adaptation_strategies:
            # 如果有快速清算能力，只有60%的订单被取消
            orders_to_cancel = int(orders_to_cancel * 0.6)
            self.log(LogLevel.INFO, "Inventory", 
                    f"快速库存清算减轻了订单取消影响")
            
            # 触发立即清算尝试
            self.env.process(self.liquidate_inventory())
        
        # 更新订单指标
        self.backlog -= orders_to_cancel
        self.cancelled_orders += orders_to_cancel
        
        self.log(LogLevel.WARNING, "Orders", 
                f"订单取消: {orders_to_cancel}订单被取消({cancellation_rate*100:.1f}%的积压)")
        
        # 计算财务影响(取消费用，如有)
        cancellation_fee_rate = 0.1  # 客户支付10%取消订单费用
        cancellation_revenue = orders_to_cancel * 1500 * cancellation_fee_rate
        self.revenue += cancellation_revenue
        
        if cancellation_revenue > 0:
            self.log(LogLevel.INFO, "Finance", 
                    f"收到${cancellation_revenue:,.2f}取消费用")
        
        # 干扰持续时间
        disruption_duration = random.randint(4, 12) * 60  # 4-12小时
        
        # 等待干扰结束
        yield self.env.timeout(disruption_duration)
        
        self.order_cancellation_active = False
        self.log(LogLevel.INFO, "Orders", "订单取消事件结束")
```

### 干扰事件生成器

```python
def generate_disruptions(self):
    """根据定义的概率生成随机干扰"""
    while True:
        # 每6小时检查一次干扰
        yield self.env.timeout(6 * 60)
        
        # 检查每种类型的干扰
        
        # 1. CNC机器故障
        if random.random() < CNC_FAILURE_CHANCE / 4:  # 将每日概率转换为6小时概率
            # 如果预防性维护激活且运气好，则跳过
            if (AdaptationStrategy.PREVENTIVE_MAINTENANCE in self.adaptation_strategies and 
                random.random() < 0.7):
                pass  # 故障预防
            else:
                # 为用户创建干扰通知
                self.disruption_notification = "警报: 检测到CNC机器故障!"
                self.disruption_notification_time = self.env.now
                
                # 执行干扰
                self.env.process(self.cnc_machine_failure())
        
        # 2. 订单突增
        if random.random() < SUDDEN_ORDER_SPIKE_CHANCE / 4:
            self.disruption_notification = "警报: 检测到订单突增!"
            self.disruption_notification_time = self.env.now
            self.env.process(self.order_spike())
        
        # ... 其他干扰检查 ...
```

## 适应性策略

系统提供了两类适应性策略来应对各种干扰：持续性策略和一次性策略。

### 1. 持续性策略

这些策略实施后会在一段时间内持续生效，每周产生维护成本。

| 策略ID | 策略名称 | 描述 | 实施成本($) | 周维护成本($) | 默认持续时间(天) |
|--------|---------|------|------------|--------------|---------------|
| PREVENTIVE_MAINTENANCE | 实施预防性维护计划 | 降低设备故障几率 | 25,000 | 625 | 14 |
| FLEXIBLE_WORKFORCE | 维持灵活的员工培训 | 提高工人生产效率 | 18,000 | 300 | 21 |
| JUST_IN_TIME_REPLENISHMENT | 即时补货系统 | 优化库存水平和交付时间 | 20,000 | 300 | 30 |
| SUPPLIER_DIVERSIFICATION | 多元化供应商网络 | 减轻供应链中断风险 | 35,000 | 450 | 45 |
| OVERTIME_POLICY | 战略性加班政策 | 在高需求期间增加产能 | 5,000 | 0 | 5 |
| QUALITY_MONITORING | 增强质量监控系统 | 减少缺陷和提高检测率 | 42,000 | 550 | 30 |
| KPI_MONITORING | 实时KPI监控系统 | 提高整体运营效率 | 25,000 | 400 | 30 |
| MODULAR_REPAIR_KITS | 模块化维修工具包系统 | 加快维修速度 | 18,000 | 250 | 60 |
| OUTSOURCING | 临时生产外包 | 在高需求期间增加产能 | 30,000 | 250 | 10 |
| LEAN_MANUFACTURING | 实施精益生产原则 | 提高整体生产效率 | 38,000 | 450 | 60 |
| PEAK_LOAD_OPTIMIZATION | 峰值负载优化系统 | 减少能源成本和停电影响 | 15,000 | 350 | 14 |
| INVENTORY_LIQUIDATION | 快速库存清算系统 | 降低库存成本和应对订单取消 | 8,000 | 200 | 7 |

### 2. 一次性策略(战术行动)

这些策略是立即执行的单次行动，无需持续维护成本。

| 策略ID | 策略名称 | 描述 | 实施成本($) |
|--------|---------|------|------------|
| PURCHASE_CNC_MACHINE | 购买额外CNC机器 | 增加生产能力 | 150,000 |
| SELL_CNC_MACHINE | 出售闲置CNC机器 | 产生现金流 | 5,000 |
| HIRE_WORKERS | 雇佣额外工人 | 增加劳动力 | 15,000 |
| REDUCE_WORKFORCE | 减少劳动力规模 | 降低人工成本 | 30,000 |
| EMERGENCY_MATERIALS | 订购紧急原材料 | 快速补充原材料 | 40,000 |
| UPGRADE_ASSEMBLY | 升级组装站 | 提高组装效率 | 75,000 |
| INSTALL_BACKUP_GENERATOR | 安装应急备用发电机 | 减轻停电影响 | 55,000 |
| EXPEDITE_MAINTENANCE | 加速机器维护 | 快速修复故障设备 | 25,000 |
| BULK_ORDER_MATERIALS | 批量订购原材料 | 获得批量折扣 | 80,000 |
| CANCEL_PENDING_ORDERS | 取消低优先级订单 | 减轻生产压力 | 20,000 |
| REALLOCATE_WORKERS | 重新分配部门间工人 | 临时提高效率 | 5,000 |
| SCHEDULE_OVERTIME | 安排周末加班 | 临时增加产能 | 18,000 |

### 策略实施和效果

当策略被激活或停用时，系统会应用或移除相应的效果。以下是一些主要策略效果的示例：

#### 预防性维护(PREVENTIVE_MAINTENANCE)
- 激活时: CNC故障概率降低80%
- 停用时: 恢复正常故障概率

#### 即时补货系统(JUST_IN_TIME_REPLENISHMENT)
- 激活时: 增加50%的原材料和零部件，减少30%的交付时间
- 优化订货量: 基于积压订单和生产率智能计算订购量

#### 灵活员工培训(FLEXIBLE_WORKFORCE)
- 激活时: 减少30%的加工和组装时间
- 停用时: 恢复正常加工和组装时间

#### 供应商多样化(SUPPLIER_DIVERSIFICATION)
- 激活时: 供应链中断概率降低75%
- 中断持续时间缩短50%

#### 质量监控增强(QUALITY_MONITORING)
- 激活时: 质量问题概率降低80%，缺陷率降低60%
- 检测率提高: 真实缺陷检测率从90%提高到98%，误判率从5%降低到2%

#### 策略修改方法

```python
def modify_strategy(self, strategy_idx, activate, custom_duration=None):
    """在模拟期间添加或删除策略"""
    strategies = list(AdaptationStrategy)
    if 0 <= strategy_idx < len(strategies):
        strategy = strategies[strategy_idx]
        
        # 检查这是否是一次性策略
        is_one_time = strategy in ONE_TIME_STRATEGIES
        
        if activate:
            # 对于一次性策略，只执行一次而不添加到活动策略中
            if is_one_time:
                # 检查我们是否能负担这个策略
                implementation_cost = StrategyCosts.IMPLEMENTATION[strategy]
                revenue = self.revenue + self.liquidation_revenue
                costs = self.costs + self.inventory_holding_costs + self.energy_costs
                current_profit = revenue - costs
                
                if implementation_cost > (current_profit + 10000):  # 允许一些赤字
                    warning_msg = f"警告: 策略'{strategy.value}'成本${implementation_cost:,}" + \
                                f"超过当前利润${current_profit:,}，但仍然实施"
                    self.log(LogLevel.WARNING, "Strategy", warning_msg)
                
                # 执行一次性策略操作
                self.costs += implementation_cost
                self.execute_one_time_strategy(strategy)
                
                # 跟踪我们执行了此策略(用于报告)
                self.strategy_changes_history.append({
                    "time": self.env.now,
                    "strategy": strategy.value,
                    "action": "执行(一次性)"
                })
                
                return f"执行了一次性策略: {strategy.value}"
            
            # 对于具有持续时间的常规策略
            elif strategy not in self.adaptation_strategies:
                # ...策略实施逻辑...
                return f"策略已激活: {strategy.value}"
            
            return "无变化(策略已激活)"
        
        # 停用仅与持续性策略相关
        elif not is_one_time and strategy in self.adaptation_strategies:
            # ...策略停用逻辑...
            return f"策略已停用: {strategy.value}"
        
        return "无需更改"
    
    return "无效的策略索引"
```

## MQTT通信

系统使用MQTT协议进行通信，实现数据发布和命令接收。

### MQTT主题结构

```python
class MQTTTopics:
    # 发布数据的基本主题
    INVENTORY_BASE = "factory/inventory"        # 库存相关数据
    ORDERS_BASE = "factory/orders"              # 订单相关数据
    PRODUCTION_BASE = "factory/production"      # 生产相关数据
    RESOURCES_BASE = "factory/resources"        # 资源相关数据
    FINANCIAL_BASE = "factory/financial"        # 财务相关数据
    DISRUPTION_BASE = "factory/disruption"      # 干扰事件相关数据
    STRATEGIES_BASE = "factory/strategies"      # 策略相关数据
    TIME_BASE = "factory/time"                  # 时间相关数据
    ENERGY_BASE = "factory/energy"              # 能源相关数据
    QUALITY_BASE = "factory/quality"            # 质量相关数据
    EQUIPMENT_BASE = "factory/equipment"        # 设备相关数据
    SENSORS_BASE = "factory/sensors"            # 传感器相关数据
    OEE_BASE = "factory/oee"                    # OEE相关数据
    MAINTENANCE_BASE = "factory/maintenance"    # 维护相关数据
    LOGS_BASE = "factory/logs"                  # 日志相关数据
    
    # 命令主题(工厂订阅这些)
    STRATEGY_COMMAND = "factory/command/strategy"       # 策略命令
    SIMULATION_COMMAND = "factory/command/simulation"   # 模拟控制命令
```

### 命令格式

#### 策略命令

用于激活策略（动作）。

向factory/command/{STRATEGY_NAME}
发送 JSON 格式的命令。
```json
{
      // 策略ID（整数）
    "trigger": true }
```

#### 模拟控制命令

用于控制模拟运行状态。

```json
{
    "command": "pause"     // 可选值: "pause", "resume", "stop"
}
```

### 发布数据示例

系统会定期将各类数据发布到对应主题。以下是一些示例：

#### 库存数据

```json
// 主题: factory/inventory/rawMaterials
{"value": 450}

// 主题: factory/inventory/partsInventory
{"value": 65}

// 主题: factory/inventory/finishedProducts
{"value": 24}
```

#### 订单数据

```json
// 主题: factory/orders/totalOrders
{"value": 320}

// 主题: factory/orders/fulfilledOrders
{"value": 290}

// 主题: factory/orders/backlog
{"value": 30}

// 主题: factory/orders/fulfillmentRate
{"value": 90.6}
```

#### 财务数据

```json
// 主题: factory/financial/revenue
{"value": 435000}

// 主题: factory/financial/costs
{"value": 290000}

// 主题: factory/financial/profit
{"value": 145000}

// 主题: factory/financial/profitMargin
{"value": 33.3}
```

## 指标监控与日志

系统会监控和记录各种指标和事件，以便分析和可视化。

### 监控指标

系统记录以下类别的关键指标：

1. **库存指标**：原材料、零部件、成品数量和价值
2. **订单指标**：总订单、已完成订单、取消订单、积压订单
3. **资源指标**：CNC机器、工人、组装站和质检站的数量和利用率
4. **财务指标**：收入、成本、利润、利润率
5. **生产指标**：日产量、每小时零部件数
6. **质量指标**：缺陷率、发现的缺陷、误判率
7. **能源指标**：总能耗、各设备能耗、能源成本
8. **OEE指标**：可用性、性能、质量和总体OEE
9. **维护指标**：维护事件、停机时间、MTBF、MTTR

```python
def monitor_metrics(self):
    """每小时记录关键指标"""
    while True:
        # 记录当前指标
        self.current_time = self.env.now
        self.current_simulated_min = int(self.env.now)
        
        self.metrics_history["time"].append(self.env.now)
        self.metrics_history["raw_materials"].append(self.raw_materials)
        self.metrics_history["parts_inventory"].append(self.parts_inventory)
        self.metrics_history["finished_products"].append(self.finished_products)
        self.metrics_history["backlog"].append(self.backlog)
        self.metrics_history["operational_cnc_machines"].append(self.operational_cnc_machines)
        self.metrics_history["available_workers"].append(self.available_workers)
        self.metrics_history["order_rate"].append(self.current_order_rate)
        self.metrics_history["revenue"].append(self.revenue)
        self.metrics_history["costs"].append(self.costs)
        self.metrics_history["inventory_holding_costs"].append(self.inventory_holding_costs)
        self.metrics_history["energy_costs"].append(self.energy_costs)
        self.metrics_history["profit"].append(
            self.revenue + self.liquidation_revenue - 
            self.costs - self.inventory_holding_costs - self.energy_costs
        )
        self.metrics_history["oee"].append(self.oee * 100)  # 存储为百分比
        
        # ...其他指标监控逻辑...
        
        # 等待1小时
        yield self.env.timeout(60)
```

### 日志系统

系统实现了分级日志系统，记录各种事件和状态变化。日志等级包括：

```python
class LogLevel(Enum):
    INFO = "INFO"           # 一般信息
    WARNING = "WARNING"     # 警告信息
    ERROR = "ERROR"         # 错误信息
    STRATEGY = "STRATEGY"   # 策略相关信息
    DISRUPTION = "DISRUPTION" # 干扰事件信息
```

日志记录方法：

```python
def log(self, level, component, message):
    """记录消息到控制台和MQTT"""
    timestamp = self.format_time(self.current_time) if self.current_time > 0 else "启动"
    
    # 打印到控制台
    print(f"[{timestamp}] [{level.value}] [{component}] {message}")
    
    # 发布到MQTT(如果客户端已连接且速率限制允许)
    if self.mqtt_client:
        log_topic = f"{MQTTTopics.LOGS_BASE}/{level.value.lower()}"
        
        # 将日志消息扁平化为单层JSON
        log_payload = json.dumps({
            "timestamp": timestamp,
            "simulationTime": self.current_time,
            "component": component,
            "message": message
        })
        
        self.rate_limited_publish(log_topic, log_payload)
        
    # 无论是否发布都添加到本地日志
    self.logs.append({
        "timestamp": timestamp,
        "simulationTime": self.current_time,
        "level": level.value,
        "component": component,
        "message": message
    })
```

## 系统运行指南

### 启动系统

系统主入口点在`main()`函数中：

```python
def main():
    """运行模拟的主函数"""
    print("=== 启用MQTT的工厂模拟 ===")
    print("\n此模拟将运行具有MQTT集成的工厂:")
    print("1. 所有工厂数据将发布到MQTT主题")
    print("2. 通过MQTT命令进行策略选择和模拟控制")
    print("3. 随机干扰将在整个模拟过程中发生")
    print("4. 系统日志和事件将发布到MQTT主题")
    print("\n可用策略:")
    
    # 打印策略及其成本
    strategies = list(AdaptationStrategy)
    for i, strategy in enumerate(strategies):
        imp_cost = StrategyCosts.IMPLEMENTATION[strategy]
        weekly = StrategyCosts.WEEKLY[strategy]
        print(f"{i}. {strategy.value}")
        print(f"   成本: ${imp_cost:,}前期 + ${weekly:,}/周")
    
    print("\n按Ctrl+C停止模拟")
    
    # 创建并运行模拟
    manager = MQTTSimulationManager()
    manager.run_simulation()
```

### 运行参数设置

通过调整顶部的常量来配置模拟：

```python
# 模拟常量
SIMULATION_DAYS = 60                 # 模拟天数
REAL_TIME_FACTOR = 100               # 现实与模拟时间比例(5分钟模拟=1分钟现实)
MQTT_UPDATE_INTERVAL = 1             # MQTT数据发布间隔(秒)
MQTT_MIN_PUBLISH_INTERVAL = 1        # 同一主题最小发布间隔(秒)

# MQTT配置
MQTT_BROKER = "office.unibutton.com" # MQTT代理地址
MQTT_PORT = 11483                     # MQTT端口
MQTT_CLIENT_ID = "value_factory_sim"  # 客户端ID
MQTT_USERNAME = None                  # 代理认证用户名(如需要)
MQTT_PASSWORD = None                  # 代理认证密码(如需要)
```

### 模拟运行

模拟运行由`MQTTSimulationManager`类管理：

```python
def run_simulation(self):
    """运行具有MQTT交互的模拟"""
    self.running = True
    print("启动带有MQTT集成的工厂模拟")
    print(f"连接到MQTT代理 {MQTT_BROKER}:{MQTT_PORT}")
    print(f"模拟将运行最多{SIMULATION_DAYS}天")
    
    # 发布初始策略状态
    self.factory.publish_strategy_status()
    
    # 跟踪模拟时间
    next_sim_step = 0
    start_time = time.time()
    
    try:
        # 运行模拟直到结束时间或用户退出
        while self.env.now < self.simulation_end_time and self.running:
            current_time = time.time()
            
            # 如果暂停，等待
            if self.factory.paused:
                time.sleep(0.1)
                continue
            
            # 计算应该经过多少模拟时间
            elapsed_real_seconds = current_time - start_time
            target_sim_minutes = elapsed_real_seconds * REAL_TIME_FACTOR
            
            # 运行模拟步骤
            if target_sim_minutes > next_sim_step:
                # 运行到下一个目标时间
                self.env.run(until=next_sim_step + 1)
                next_sim_step += 1
            
            # 小睡避免CPU占用过高
            time.sleep(0.01)
        
        # 显示最终状态
        # ...最终状态输出...
        
    except KeyboardInterrupt:
        self.running = False
        print("\n模拟中断")
    except Exception as e:
        print(f"模拟错误: {e}")
    finally:
        # 清理MQTT连接
        if self.factory.mqtt_client:
            self.factory.mqtt_client.loop_stop()
            self.factory.mqtt_client.disconnect()
            print("MQTT连接已关闭")
```

## 扩展与定制

本系统设计为可扩展和可定制。以下是一些可以修改的关键方面：

### 添加新的干扰类型

1. 在`DisruptionType`枚举中添加新类型
2. 实现处理函数
3. 在`generate_disruptions`中添加检查逻辑

```python
# 添加新的干扰类型
class DisruptionType(Enum):
    # 现有类型...
    NEW_DISRUPTION = "新的干扰类型"

# 实现处理函数
def handle_new_disruption(self):
    """处理新类型的干扰"""
    # 干扰实现逻辑...

# 在generate_disruptions中添加
if random.random() < NEW_DISRUPTION_CHANCE / 4:
    self.disruption_notification = "警报: 检测到新干扰!"
    self.disruption_notification_time = self.env.now
    self.env.process(self.handle_new_disruption())
```

### 添加新的适应性策略

1. 在`AdaptationStrategy`枚举中添加新策略
2. 在`StrategyCosts`和`StrategyDurations`中设置成本和持续时间
3. 确定策略是一次性的还是持续性的
4. 在`apply_strategy_effects`或`execute_one_time_strategy`中实现策略效果

```python
# 添加新策略
class AdaptationStrategy(Enum):
    # 现有策略...
    NEW_STRATEGY = "新策略描述"

# 设置成本
class StrategyCosts:
    IMPLEMENTATION = {
        # 现有策略...
        AdaptationStrategy.NEW_STRATEGY: 30000,
    }
    
    WEEKLY = {
        # 现有策略...
        AdaptationStrategy.NEW_STRATEGY: 400,
    }

# 设置持续时间
class StrategyDurations:
    DURATION = {
        # 现有策略...
        AdaptationStrategy.NEW_STRATEGY: 20 * 24 * 60,  # 20天
    }

# 确定是否为一次性策略
ONE_TIME_STRATEGIES = {
    # 现有一次性策略...
    # 如果是一次性策略，添加:
    # AdaptationStrategy.NEW_STRATEGY,
}

# 实现策略效果
def apply_strategy_effects(self, strategy, activate=True):
    # 现有策略处理...
    elif strategy == AdaptationStrategy.NEW_STRATEGY:
        if activate:
            # 激活效果
            pass
        else:
            # 停用效果
            pass
```

### 修改生产参数

通过调整顶部的常量来修改工厂生产参数：

```python
# 工厂设置
NUM_CNC_MACHINES = 10                # 增加CNC机器数量
NUM_ASSEMBLY_STATIONS = 8            # 增加组装站数量
NUM_QC_STATIONS = 5                  # 增加质检站数量
NUM_WORKERS = 24                     # 增加工人数量

# 生产参数
CNC_PROCESSING_TIME = 30             # 减少加工时间
ASSEMBLY_TIME = 20                   # 减少组装时间
```

### 自定义MQTT集成

可以修改MQTT主题结构和通信行为：

```python
# 修改MQTT主题
class MQTTTopics:
    # 自定义主题结构...
    CUSTOM_BASE = "factory/custom"   # 添加新的主题基础

# 添加新的MQTT发布内容
def publish_custom_data(self):
    """发布自定义数据"""
    self.rate_limited_publish(f"{MQTTTopics.CUSTOM_BASE}/metric", 
                            json.dumps({"value": custom_value}))

# 添加新的命令处理
def on_mqtt_message(self, client, userdata, msg):
    # 现有处理...
    elif topic == "factory/command/custom":
        self.handle_custom_command(payload)
```

---

通过本文档，您应该能够理解工厂生产模拟系统的架构、功能和使用方法。该系统可以模拟真实工厂环境中的各种场景，帮助用户理解不同干扰对生产的影响，以及各种适应性策略的效果。