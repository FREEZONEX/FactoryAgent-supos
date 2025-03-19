import simpy
import random
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import time
import threading
import os
import json
from enum import Enum
import sys
import paho.mqtt.client as mqtt

# Simulation constants
SIMULATION_DAYS = 40
REAL_TIME_FACTOR = 100  # 5 minutes in simulation = 1 minute in real life
MQTT_UPDATE_INTERVAL = 1  # Publish data every 1 second
MQTT_MIN_PUBLISH_INTERVAL = 1  # Minimum interval between publishes to same topic (seconds)

# Logging levels
class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STRATEGY = "STRATEGY"
    DISRUPTION = "DISRUPTION"

# MQTT Configuration
MQTT_BROKER = "your mqtt broker"  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_CLIENT_ID = "factory_sim"
MQTT_USERNAME = 'admin'  # Set if your broker requires authentication
MQTT_PASSWORD = 'public'  # Set if your broker requires authentication

# Factory settings
NUM_CNC_MACHINES = 5
NUM_ASSEMBLY_STATIONS = 4
NUM_QC_STATIONS = 3  # New: Quality Control stations
NUM_WORKERS = 12
INITIAL_INVENTORY = 80
INITIAL_RAW_MATERIALS = 500

# Production parameters
CNC_PROCESSING_TIME = 45  # minutes per part
ASSEMBLY_TIME = 30  # minutes per product
QC_INSPECTION_TIME = 15  # minutes per product batch
PARTS_PER_PRODUCT = 3
NORMAL_ORDER_RATE = 25  # products per day
DELIVERY_TIME = 2 * 24 * 60  # 2 days in minutes for raw material delivery

# Worker salary costs (realistic industrial wages)
WORKER_HOURLY_WAGE = 25  # $25 per hour per worker
WORKER_SHIFT_HOURS = 8   # Standard 8-hour shift
WORKER_SHIFTS_PER_DAY = 3  # 3 shifts to cover 24 hours
WORKER_BENEFITS_FACTOR = 1.3  # Benefits add 30% to base salary

# Inventory costs (updated to be more realistic)
RAW_MATERIAL_COST = 70  # $ per unit (industrial grade metals)
INVENTORY_HOLDING_COST_RATE = 0.002  # 0.2% daily holding cost (finance + storage)
PARTS_VALUE = 120  # $ per processed part (raw material + processing)
FINISHED_PRODUCT_VALUE = 590  # $ per finished valve (before markup)

# Energy costs (updated to be more realistic)
ENERGY_COST_PER_KWH = 0.6  # $ per kWh (industrial electricity rate)
CNC_ENERGY_USAGE = 35.5  # kWh per hour (industrial CNC machines)
ASSEMBLY_ENERGY_USAGE = 10.0  # kWh per hour (assembly stations)
QC_ENERGY_USAGE = 10.5  # kWh per hour (QC equipment)
FACILITY_BASE_ENERGY = 35.0  # kWh per hour (lighting, HVAC, compressors, etc.)

# Event frequencies (chance per day)
CNC_FAILURE_CHANCE = 0.15
SUDDEN_ORDER_SPIKE_CHANCE = 0.05
SUPPLY_CHAIN_ISSUE_CHANCE = 0.08
WORKER_ABSENCE_CHANCE = 0.08
QUALITY_ISSUE_CHANCE = 0.07
POWER_OUTAGE_CHANCE = 0.1
ORDER_CANCELLATION_CHANCE = 0.1  # New: order cancellation events

# MQTT Topics - Simplified to use only one level of hierarchy
class MQTTTopics:
    # Base topics for publishing data
    INVENTORY_BASE = "factory/inventory"
    ORDERS_BASE = "factory/orders"
    PRODUCTION_BASE = "factory/production" 
    RESOURCES_BASE = "factory/resources"
    FINANCIAL_BASE = "factory/financial"
    DISRUPTION_BASE = "factory/disruption"
    STRATEGIES_BASE = "factory/strategies"
    TIME_BASE = "factory/time"
    ENERGY_BASE = "factory/energy"
    QUALITY_BASE = "factory/quality"
    EQUIPMENT_BASE = "factory/equipment"
    SENSORS_BASE = "factory/sensors"
    OEE_BASE = "factory/oee"
    MAINTENANCE_BASE = "factory/maintenance"
    LOGS_BASE = "factory/logs"
    
    # Command topics (factory subscribes to these)
    STRATEGY_COMMAND = "factory/command/strategy"
    SIMULATION_COMMAND = "factory/command/simulation"

class DisruptionType(Enum):
    CNC_FAILURE = "CNC Machine Failure"
    ORDER_SPIKE = "Sudden Order Spike"
    SUPPLY_CHAIN = "Supply Chain Disruption"
    WORKER_ABSENCE = "Worker Absence"
    QUALITY_ISSUE = "Quality Control Issue"
    POWER_OUTAGE = "Power Outage"
    ORDER_CANCELLATION = "Order Cancellation"  # New disruption type

class AdaptationStrategy(Enum):
    # Existing high-level strategies (with durations)
    PREVENTIVE_MAINTENANCE = "Implement Preventive Maintenance Schedule"
    FLEXIBLE_WORKFORCE = "Maintain Flexible Workforce Training"
    JUST_IN_TIME_REPLENISHMENT = "Just-In-Time Replenishment System"
    SUPPLIER_DIVERSIFICATION = "Diversify Supplier Network"
    OVERTIME_POLICY = "Strategic Overtime Policy"
    QUALITY_MONITORING = "Enhanced Quality Monitoring System"
    KPI_MONITORING = "Real-time KPI Monitoring System"
    MODULAR_REPAIR_KITS = "Modular Repair Kits System"
    OUTSOURCING = "Temporary Production Outsourcing"
    LEAN_MANUFACTURING = "Implement Lean Manufacturing Principles"
    PEAK_LOAD_OPTIMIZATION = "Peak Load Optimization System"
    INVENTORY_LIQUIDATION = "Rapid Inventory Liquidation System"
    
    # New low-level strategies (one-time actions without durations)
    PURCHASE_CNC_MACHINE = "Purchase Additional CNC Machine"
    SELL_CNC_MACHINE = "Sell Underutilized CNC Machine"
    HIRE_WORKERS = "Hire Additional Workers"
    REDUCE_WORKFORCE = "Reduce Workforce Size"
    EMERGENCY_MATERIALS = "Order Emergency Raw Materials"
    UPGRADE_ASSEMBLY = "Upgrade Assembly Stations"
    INSTALL_BACKUP_GENERATOR = "Install Emergency Backup Generator"
    EXPEDITE_MAINTENANCE = "Expedite Machine Maintenance"
    BULK_ORDER_MATERIALS = "Place Bulk Materials Order"
    CANCEL_PENDING_ORDERS = "Cancel Low-Priority Orders"
    REALLOCATE_WORKERS = "Reallocate Workers Between Departments"
    SCHEDULE_OVERTIME = "Schedule Weekend Overtime Shift"

# Flag for which strategies are one-time actions
ONE_TIME_STRATEGIES = {
    AdaptationStrategy.PURCHASE_CNC_MACHINE,
    AdaptationStrategy.SELL_CNC_MACHINE,
    AdaptationStrategy.HIRE_WORKERS,
    AdaptationStrategy.REDUCE_WORKFORCE,
    AdaptationStrategy.EMERGENCY_MATERIALS,
    AdaptationStrategy.UPGRADE_ASSEMBLY,
    AdaptationStrategy.INSTALL_BACKUP_GENERATOR,
    AdaptationStrategy.EXPEDITE_MAINTENANCE,
    AdaptationStrategy.BULK_ORDER_MATERIALS,
    AdaptationStrategy.CANCEL_PENDING_ORDERS,
    AdaptationStrategy.REALLOCATE_WORKERS,
    AdaptationStrategy.SCHEDULE_OVERTIME,
}

# Strategy implementation costs and maintenance costs
class StrategyCosts:
    # Implementation costs (one-time)
    IMPLEMENTATION = {
        # Existing strategies
        AdaptationStrategy.PREVENTIVE_MAINTENANCE: 25000,
        AdaptationStrategy.FLEXIBLE_WORKFORCE: 18000,
        AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT: 20000,
        AdaptationStrategy.SUPPLIER_DIVERSIFICATION: 35000,
        AdaptationStrategy.OVERTIME_POLICY: 5000,
        AdaptationStrategy.QUALITY_MONITORING: 42000,
        AdaptationStrategy.KPI_MONITORING: 25000,
        AdaptationStrategy.MODULAR_REPAIR_KITS: 18000,
        AdaptationStrategy.OUTSOURCING: 30000,
        AdaptationStrategy.LEAN_MANUFACTURING: 38000,
        AdaptationStrategy.PEAK_LOAD_OPTIMIZATION: 15000,
        AdaptationStrategy.INVENTORY_LIQUIDATION: 8000,
        
        # New one-time strategies
        AdaptationStrategy.PURCHASE_CNC_MACHINE: 150000,  # Cost for new industrial CNC machine
        AdaptationStrategy.SELL_CNC_MACHINE: 5000,        # Cost for decommissioning
        AdaptationStrategy.HIRE_WORKERS: 15000,           # Recruitment and training costs for 3 workers
        AdaptationStrategy.REDUCE_WORKFORCE: 30000,       # Severance and legal costs for 3 workers
        AdaptationStrategy.EMERGENCY_MATERIALS: 40000,    # Premium for immediate 1000 units
        AdaptationStrategy.UPGRADE_ASSEMBLY: 75000,       # Hardware and installation costs
        AdaptationStrategy.INSTALL_BACKUP_GENERATOR: 55000, # Generator for critical systems
        AdaptationStrategy.EXPEDITE_MAINTENANCE: 25000,    # Rush service fees
        AdaptationStrategy.BULK_ORDER_MATERIALS: 80000,    # Large prepaid order (2000 units)
        AdaptationStrategy.CANCEL_PENDING_ORDERS: 20000,   # Cancellation penalties
        AdaptationStrategy.REALLOCATE_WORKERS: 5000,       # Training and administration
        AdaptationStrategy.SCHEDULE_OVERTIME: 18000,       # Weekend overtime for all workers
    }
    
    # Weekly maintenance costs (only for strategies with durations)
    WEEKLY = {
        AdaptationStrategy.PREVENTIVE_MAINTENANCE: 625,
        AdaptationStrategy.FLEXIBLE_WORKFORCE: 300,
        AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT: 300,
        AdaptationStrategy.SUPPLIER_DIVERSIFICATION: 450,
        AdaptationStrategy.OVERTIME_POLICY: 0,
        AdaptationStrategy.QUALITY_MONITORING: 550,
        AdaptationStrategy.KPI_MONITORING: 400,
        AdaptationStrategy.MODULAR_REPAIR_KITS: 250,
        AdaptationStrategy.OUTSOURCING: 250,
        AdaptationStrategy.LEAN_MANUFACTURING: 450,
        AdaptationStrategy.PEAK_LOAD_OPTIMIZATION: 350,
        AdaptationStrategy.INVENTORY_LIQUIDATION: 200,
        
        # One-time strategies have no weekly costs
        AdaptationStrategy.PURCHASE_CNC_MACHINE: 0,
        AdaptationStrategy.SELL_CNC_MACHINE: 0,
        AdaptationStrategy.HIRE_WORKERS: 0,
        AdaptationStrategy.REDUCE_WORKFORCE: 0,
        AdaptationStrategy.EMERGENCY_MATERIALS: 0,
        AdaptationStrategy.UPGRADE_ASSEMBLY: 0,
        AdaptationStrategy.INSTALL_BACKUP_GENERATOR: 0,
        AdaptationStrategy.EXPEDITE_MAINTENANCE: 0,
        AdaptationStrategy.BULK_ORDER_MATERIALS: 0,
        AdaptationStrategy.CANCEL_PENDING_ORDERS: 0,
        AdaptationStrategy.REALLOCATE_WORKERS: 0,
        AdaptationStrategy.SCHEDULE_OVERTIME: 0,
    }

class StrategyDurations:
    """每个策略的持续时间（单位：分钟）"""
    # 持续时间定义（默认值，单位：分钟）
    DURATION = {
        AdaptationStrategy.PREVENTIVE_MAINTENANCE: 14 * 24 * 60,  # 14天
        AdaptationStrategy.FLEXIBLE_WORKFORCE: 21 * 24 * 60,      # 21天
        AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT: 30 * 24 * 60,  # 30天
        AdaptationStrategy.SUPPLIER_DIVERSIFICATION: 45 * 24 * 60,    # 45天
        AdaptationStrategy.OVERTIME_POLICY: 5 * 24 * 60,          # 5天
        AdaptationStrategy.QUALITY_MONITORING: 30 * 24 * 60,      # 30天
        AdaptationStrategy.KPI_MONITORING: 30 * 24 * 60,          # 30天
        AdaptationStrategy.MODULAR_REPAIR_KITS: 60 * 24 * 60,     # 60天
        AdaptationStrategy.OUTSOURCING: 10 * 24 * 60,             # 10天
        AdaptationStrategy.LEAN_MANUFACTURING: 60 * 24 * 60,      # 90天
        AdaptationStrategy.PEAK_LOAD_OPTIMIZATION: 14 * 24 * 60,  # 14天
        AdaptationStrategy.INVENTORY_LIQUIDATION: 7 * 24 * 60,    # 7天
                # One-time strategies (no duration)
        AdaptationStrategy.PURCHASE_CNC_MACHINE: 0,
        AdaptationStrategy.SELL_CNC_MACHINE: 0,
        AdaptationStrategy.HIRE_WORKERS: 0,
        AdaptationStrategy.REDUCE_WORKFORCE: 0,
        AdaptationStrategy.EMERGENCY_MATERIALS: 0,
        AdaptationStrategy.UPGRADE_ASSEMBLY: 0,
        AdaptationStrategy.INSTALL_BACKUP_GENERATOR: 0,
        AdaptationStrategy.EXPEDITE_MAINTENANCE: 0,
        AdaptationStrategy.BULK_ORDER_MATERIALS: 0,
        AdaptationStrategy.CANCEL_PENDING_ORDERS: 0,
        AdaptationStrategy.REALLOCATE_WORKERS: 0,
        AdaptationStrategy.SCHEDULE_OVERTIME: 0,
    }

class MQTTValueFactory:
    def __init__(self, env):
        # Initialize SimPy environment
        self.env = env
        
        # Status tracking for resource availability
        self.operational_cnc_machines = NUM_CNC_MACHINES
        self.available_workers = NUM_WORKERS
        
        # Create resources with fixed capacity
        self.cnc_machines = simpy.Resource(env, capacity=NUM_CNC_MACHINES)
        self.assembly_stations = simpy.Resource(env, capacity=NUM_ASSEMBLY_STATIONS)
        self.qc_stations = simpy.Resource(env, capacity=NUM_QC_STATIONS)
        self.workers = simpy.Resource(env, capacity=NUM_WORKERS)
        
        # Inventory and raw materials
        self.raw_materials = INITIAL_RAW_MATERIALS
        self.parts_inventory = INITIAL_INVENTORY
        self.finished_products = 0
        self.backlog = 0
        
        # Order tracking
        self.total_orders = 0
        self.fulfilled_orders = 0
        self.cancelled_orders = 0  # New: track cancelled orders
        
        # Financial metrics
        self.revenue = 0
        self.costs = 0
        self.inventory_holding_costs = 0
        self.energy_costs = 0
        self.liquidation_revenue = 0  # New: track revenue from liquidation
        self.worker_salary_costs = 0
        # Status tracking
        self.current_order_rate = NORMAL_ORDER_RATE
        self.supply_chain_disrupted = False
        self.has_quality_issue = False
        self.power_outage = False
        self.order_cancellation_active = False  # New: track order cancellation status
        
        # Production metrics
        self.daily_production = 0
        self.cnc_utilization = 0
        self.assembly_utilization = 0
        self.qc_utilization = 0
        
        # Quality metrics
        self.defect_rate = 0.02  # Base defect rate (2%)
        self.defects_found = 0
        self.total_inspected = 0
        self.false_positives = 0
        self.false_negatives = 0
        
        # Energy metrics
        self.total_energy_usage = 0
        self.cnc_energy_usage = 0
        self.assembly_energy_usage = 0
        self.qc_energy_usage = 0
        self.facility_energy_usage = 0
        
        # OEE metrics (Overall Equipment Effectiveness)
        self.availability = 1.0
        self.performance = 1.0
        self.quality = 1.0
        self.oee = 1.0
        
        # Maintenance metrics
        self.maintenance_events = 0
        self.total_downtime = 0
        self.mtbf = 0
        self.mttr = 0
        self.last_failure_time = 0
        self.repair_times = []
        
        # Sensor data
        self.cnc_temperatures = [20.0] * NUM_CNC_MACHINES
        self.cnc_vibrations = [0.1] * NUM_CNC_MACHINES
        self.ambient_temperature = 22.0
        self.ambient_humidity = 45.0
        
        # Active requests tracking
        self.active_cnc_requests = 0
        self.active_worker_requests = 0
        self.active_qc_requests = 0
        
        # Adaptation strategies
        self.adaptation_strategies = set()
        self.strategy_implementation_dates = {}
        self.strategy_expiration_times = {}
        self.strategy_weekly_costs = 0
        
        # Monitoring data
        self.metrics_history = defaultdict(list)
        self.disruptions_history = []
        self.strategy_changes_history = []
        self.logs = []
        
        # Simulation control
        self.paused = False
        self.current_time = 0
        self.last_refresh_time = 0
        self.current_simulated_min = 0
        self.disruption_notification = None
        self.disruption_notification_time = 0
        
        # MQTT connection and rate limiting
        self.mqtt_client = None
        self.last_publish_time = {}  # Track last publish time for each topic
        self.setup_mqtt()
        
        # Start processes
        self.env.process(self.generate_orders())
        self.env.process(self.calculate_worker_costs())
        self.env.process(self.monitor_metrics())
        self.env.process(self.generate_disruptions())
        for _ in range(NUM_CNC_MACHINES):
            self.env.process(self.produce_parts())
        for _ in range(NUM_ASSEMBLY_STATIONS):
            self.env.process(self.assemble_products())
        self.env.process(self.quality_control())
        self.env.process(self.publish_mqtt_updates())
        self.env.process(self.calculate_inventory_costs())
        self.env.process(self.update_sensor_data())
        self.env.process(self.calculate_energy_usage())
        self.env.process(self.calculate_oee())
    
    def setup_mqtt(self):
        """Setup MQTT client connection and subscriptions"""
        self.mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        
        # Set authentication if needed
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Setup callbacks
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        # Connect to broker
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.log(LogLevel.INFO, "System", f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            error_msg = f"Error connecting to MQTT broker: {e}"
            print(error_msg)
            self.log(LogLevel.ERROR, "System", error_msg)
            sys.exit(1)

    def can_publish(self, topic):
        """Check if we can publish to a topic based on rate limiting"""
        current_time = time.time()
        
        # If topic hasn't been published to before, allow it
        if topic not in self.last_publish_time:
            self.last_publish_time[topic] = current_time
            return True
        
        # Check if enough time has passed since last publish
        if current_time - self.last_publish_time[topic] >= MQTT_MIN_PUBLISH_INTERVAL:
            self.last_publish_time[topic] = current_time
            return True
        
        return False
    
    def rate_limited_publish(self, topic, payload):
        """Publish to MQTT with rate limiting"""
        if self.can_publish(topic):
            self.mqtt_client.publish(topic, payload)
            return True
        return False
    
    def log(self, level, component, message):
        """Log a message to the console and MQTT"""
        timestamp = self.format_time(self.current_time) if self.current_time > 0 else "Startup"
        
        # Print to console
        print(f"[{timestamp}] [{level.value}] [{component}] {message}")
        
        # Publish to MQTT if client is connected and rate limiting allows
        if self.mqtt_client:
            log_topic = f"{MQTTTopics.LOGS_BASE}/{level.value.lower()}"
            
            # Flatten the log message into single-layer JSON
            log_payload = json.dumps({
                "timestamp": timestamp,
                "simulationTime": self.current_time,
                "component": component,
                "message": message
            })
            
            self.rate_limited_publish(log_topic, log_payload)
            
        # Add to local logs regardless of publishing
        self.logs.append({
            "timestamp": timestamp,
            "simulationTime": self.current_time,
            "level": level.value,
            "component": component,
            "message": message
        })
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        print(f"Connected to MQTT broker with result code {rc}")
        
        # Subscribe to original command topics
        client.subscribe(MQTTTopics.STRATEGY_COMMAND)
        client.subscribe(MQTTTopics.SIMULATION_COMMAND)
        
        # Subscribe to individual strategy command topics
        strategies = list(AdaptationStrategy)
        for strategy in strategies:
            strategy_topic = f"factory/command/{strategy.name}"
            client.subscribe(strategy_topic)
            
        # Log successful connection and subscriptions
        self.log(LogLevel.INFO, "MQTT", f"Connected to broker with result code {rc}, subscribed to command topics")

    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Handle original command topics
            if topic == MQTTTopics.STRATEGY_COMMAND:
                self.handle_strategy_command(payload)
            elif topic == MQTTTopics.SIMULATION_COMMAND:
                self.handle_simulation_command(payload)
            # Handle individual strategy command topics
            elif topic.startswith("factory/command/"):
                self.handle_direct_strategy_command(topic, payload)
        except json.JSONDecodeError:
            print(f"Error decoding MQTT message on topic {msg.topic}, payload: {msg.payload.decode()}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            print(f"Topic: {msg.topic}, Payload: {msg.payload.decode()}")

    def handle_direct_strategy_command(self, topic, payload):
        """Handle direct strategy activation commands via factory/command/{StrategyName} topics"""
        try:
            # Extract strategy name from topic
            strategy_name = topic.split('/')[-1]
            
            # Check if trigger is present and true
            if 'trigger' in payload and payload['trigger'] is True:
                # Find the strategy enum by name
                matching_strategies = [s for s in AdaptationStrategy if s.name == strategy_name]
                
                if matching_strategies:
                    strategy = matching_strategies[0]
                    strategy_idx = list(AdaptationStrategy).index(strategy)
                    
                    # Get custom duration if provided
                    custom_duration = None
                    if "duration" in payload:
                        try:
                            days = float(payload["duration"])
                            custom_duration = int(days * 24 * 60)  # Convert to minutes
                        except (ValueError, TypeError):
                            self.log(LogLevel.WARNING, "Strategy", 
                                    f"Invalid duration value: {payload['duration']}. Using default duration.")
                    
                    # Activate the strategy
                    result = self.modify_strategy(strategy_idx, True, custom_duration)
                    self.log(LogLevel.STRATEGY, "Command", 
                            f"Strategy {strategy.name} activated via direct command: {result}")
                    
                    # Publish updated strategy status
                    self.publish_strategy_status()
                else:
                    self.log(LogLevel.ERROR, "Strategy", 
                            f"Unknown strategy name in topic: {strategy_name}")
            elif 'trigger' in payload and payload['trigger'] is False:
                # Find the strategy enum by name
                matching_strategies = [s for s in AdaptationStrategy if s.name == strategy_name]
                
                if matching_strategies:
                    strategy = matching_strategies[0]
                    strategy_idx = list(AdaptationStrategy).index(strategy)
                    
                    # Deactivate the strategy
                    result = self.modify_strategy(strategy_idx, False)
                    self.log(LogLevel.STRATEGY, "Command", 
                            f"Strategy {strategy.name} deactivated via direct command: {result}")
                    
                    # Publish updated strategy status
                    self.publish_strategy_status()
                else:
                    self.log(LogLevel.ERROR, "Strategy", 
                            f"Unknown strategy name in topic: {strategy_name}")
            else:
                self.log(LogLevel.WARNING, "Strategy", 
                        f"Missing or invalid 'trigger' field in strategy command: {payload}")
        except Exception as e:
            error_msg = f"Error processing direct strategy command: {e}, Topic: {topic}, Payload: {payload}"
            self.log(LogLevel.ERROR, "Strategy", error_msg)

    def handle_simulation_command(self, payload):
        """Process simulation control commands"""
        try:
            if "command" in payload:
                command = str(payload["command"]).lower()
                
                if command == "pause":
                    self.paused = True
                    self.log(LogLevel.INFO, "Simulation", "Simulation paused via MQTT command")
                elif command == "resume":
                    self.paused = False
                    self.log(LogLevel.INFO, "Simulation", "Simulation resumed via MQTT command")
                elif command == "stop":
                    self.log(LogLevel.INFO, "Simulation", "Simulation stop requested via MQTT command")
                    self.mqtt_client.loop_stop()
                    sys.exit(0)
                else:
                    self.log(LogLevel.WARNING, "Simulation", f"Unknown simulation command: {command}")
            else:
                self.log(LogLevel.ERROR, "Simulation", "Missing 'command' field in simulation command payload")
        except Exception as e:
            error_msg = f"Error processing simulation command: {e}, Payload: {payload}"
            self.log(LogLevel.ERROR, "Simulation", error_msg)
    
    def publish_mqtt_updates(self):
        """Process to regularly publish factory data to MQTT topics"""
        while True:
            # Only publish when not paused
            if not self.paused:
                # Inventory data - flattened
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/rawMaterials", 
                                        json.dumps({"value": self.raw_materials}))
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/partsInventory", 
                                        json.dumps({"value": self.parts_inventory}))
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/finishedProducts", 
                                        json.dumps({"value": self.finished_products}))
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/rawMaterialsValue", 
                                        json.dumps({"value": self.raw_materials * RAW_MATERIAL_COST}))
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/partsValue", 
                                        json.dumps({"value": self.parts_inventory * PARTS_VALUE}))
                self.rate_limited_publish(f"{MQTTTopics.INVENTORY_BASE}/finishedProductsValue", 
                                        json.dumps({"value": self.finished_products * FINISHED_PRODUCT_VALUE}))
                
                # Order data - flattened
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/totalOrders", 
                                        json.dumps({"value": self.total_orders}))
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/fulfilledOrders", 
                                        json.dumps({"value": self.fulfilled_orders}))
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/backlog", 
                                        json.dumps({"value": self.backlog}))
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/currentOrderRate", 
                                        json.dumps({"value": self.current_order_rate}))
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/cancelledOrders", 
                                        json.dumps({"value": self.cancelled_orders}))
                
                fulfillment_rate = (self.fulfilled_orders / self.total_orders * 100) if self.total_orders > 0 else 0
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/fulfillmentRate", 
                                        json.dumps({"value": fulfillment_rate}))
                self.rate_limited_publish(f"{MQTTTopics.ORDERS_BASE}/leadTime", 
                                        json.dumps({"value": 48}))  # Estimated lead time in hours
                
                # 计算实际可用工人数量 = 总数 - 正在使用的
                actual_available_workers = max(0, NUM_WORKERS - self.workers.count)
                
                # 仅在工人缺勤事件中修改self.available_workers，表示总共有多少工人
                # 但是实际可用工人数量需要考虑当前正在使用的工人
                
                # Resource data - flattened
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/operationalCncMachines", 
                                        json.dumps({"value": self.operational_cnc_machines}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/totalCncMachines", 
                                        json.dumps({"value": NUM_CNC_MACHINES}))
                # 使用实际计算的可用工人数量
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/availableWorkers", 
                                        json.dumps({"value": actual_available_workers}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/totalWorkers", 
                                        json.dumps({"value": self.available_workers}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/totalWorkerCapacity", 
                                        json.dumps({"value": NUM_WORKERS}))
                
                # 计算CNC实际使用量
                cnc_in_use = self.cnc_machines.count
                cnc_usage_percent = (cnc_in_use / max(1, self.operational_cnc_machines)) * 100
                # 计算装配站实际使用量
                assembly_in_use = self.assembly_stations.count
                assembly_usage_percent = (assembly_in_use / max(1, NUM_ASSEMBLY_STATIONS)) * 100
                # 计算质检站实际使用量
                qc_in_use = self.qc_stations.count
                qc_usage_percent = (qc_in_use / max(1, NUM_QC_STATIONS)) * 100
                
                # 发布实际资源使用量
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/cncInUse", 
                                        json.dumps({"value": cnc_in_use}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/assemblyInUse", 
                                        json.dumps({"value": assembly_in_use}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/qcInUse", 
                                        json.dumps({"value": qc_in_use}))
                
                # 更新利用率指标
                self.cnc_utilization = cnc_usage_percent
                self.assembly_utilization = assembly_usage_percent
                self.qc_utilization = qc_usage_percent
                
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/assemblyStations", 
                                        json.dumps({"value": NUM_ASSEMBLY_STATIONS}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/qcStations", 
                                        json.dumps({"value": NUM_QC_STATIONS}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/cncUtilization", 
                                        json.dumps({"value": self.cnc_utilization}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/assemblyUtilization", 
                                        json.dumps({"value": self.assembly_utilization}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/qcUtilization", 
                                        json.dumps({"value": self.qc_utilization}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/powerStatus", 
                                        json.dumps({"value": "Outage" if self.power_outage else "Normal"}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/workersInUse", 
                                        json.dumps({"value": self.workers.count}))
                self.rate_limited_publish(f"{MQTTTopics.RESOURCES_BASE}/workerUtilization", 
                                        json.dumps({"value": (self.workers.count / max(1, self.available_workers) * 100)}))
                
                # Financial data - flattened
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/revenue", 
                                        json.dumps({"value": self.revenue}))
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/costs", 
                                        json.dumps({"value": self.costs}))
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/inventoryHoldingCosts", 
                                        json.dumps({"value": self.inventory_holding_costs}))
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/energyCosts", 
                                        json.dumps({"value": self.energy_costs}))
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/liquidationRevenue", 
                                        json.dumps({"value": self.liquidation_revenue}))
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/workerSalaryCosts", 
                                        json.dumps({"value": self.worker_salary_costs}))
                total_costs = self.costs + self.inventory_holding_costs + self.energy_costs
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/totalCosts", 
                                        json.dumps({"value": total_costs}))
                
                profit = self.revenue + self.liquidation_revenue - total_costs
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/profit", 
                                        json.dumps({"value": profit}))
                
                profit_margin = (profit / max(1, self.revenue + self.liquidation_revenue) * 100)
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/profitMargin", 
                                        json.dumps({"value": profit_margin}))
                
                # Production data - flattened
                self.rate_limited_publish(f"{MQTTTopics.PRODUCTION_BASE}/dailyProduction", 
                                        json.dumps({"value": self.daily_production}))
                
                parts_per_hour = self.daily_production * PARTS_PER_PRODUCT / 24 if self.daily_production > 0 else 0
                self.rate_limited_publish(f"{MQTTTopics.PRODUCTION_BASE}/partsPerHour", 
                                        json.dumps({"value": parts_per_hour}))
                
                self.rate_limited_publish(f"{MQTTTopics.PRODUCTION_BASE}/supplyChainDisrupted", 
                                        json.dumps({"value": self.supply_chain_disrupted}))
                self.rate_limited_publish(f"{MQTTTopics.PRODUCTION_BASE}/hasQualityIssue", 
                                        json.dumps({"value": self.has_quality_issue}))
                
                work_in_progress = self.parts_inventory // PARTS_PER_PRODUCT
                self.rate_limited_publish(f"{MQTTTopics.PRODUCTION_BASE}/workInProgress", 
                                        json.dumps({"value": work_in_progress}))
                
                # Quality data - flattened
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/defectRate", 
                                        json.dumps({"value": self.defect_rate * 100}))
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/defectsFound", 
                                        json.dumps({"value": self.defects_found}))
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/totalInspected", 
                                        json.dumps({"value": self.total_inspected}))
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/falsePositives", 
                                        json.dumps({"value": self.false_positives}))
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/falseNegatives", 
                                        json.dumps({"value": self.false_negatives}))
                
                inspection_accuracy = (1 - (self.false_positives + self.false_negatives) / max(1, self.total_inspected)) * 100
                self.rate_limited_publish(f"{MQTTTopics.QUALITY_BASE}/inspectionAccuracy", 
                                        json.dumps({"value": inspection_accuracy}))
                
                # Energy data - flattened
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/totalEnergyUsage", 
                                        json.dumps({"value": self.total_energy_usage}))
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/cncEnergyUsage", 
                                        json.dumps({"value": self.cnc_energy_usage}))
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/assemblyEnergyUsage", 
                                        json.dumps({"value": self.assembly_energy_usage}))
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/qcEnergyUsage", 
                                        json.dumps({"value": self.qc_energy_usage}))
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/facilityEnergyUsage", 
                                        json.dumps({"value": self.facility_energy_usage}))
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/energyCosts", 
                                        json.dumps({"value": self.energy_costs}))
                
                energy_efficiency = self.daily_production / max(1, self.total_energy_usage)
                self.rate_limited_publish(f"{MQTTTopics.ENERGY_BASE}/energyEfficiency", 
                                        json.dumps({"value": energy_efficiency}))
                
                # OEE data - flattened
                self.rate_limited_publish(f"{MQTTTopics.OEE_BASE}/availability", 
                                        json.dumps({"value": self.availability * 100}))
                self.rate_limited_publish(f"{MQTTTopics.OEE_BASE}/performance", 
                                        json.dumps({"value": self.performance * 100}))
                self.rate_limited_publish(f"{MQTTTopics.OEE_BASE}/quality", 
                                        json.dumps({"value": self.quality * 100}))
                self.rate_limited_publish(f"{MQTTTopics.OEE_BASE}/oee", 
                                        json.dumps({"value": self.oee * 100}))
                
                # Maintenance data - flattened
                self.rate_limited_publish(f"{MQTTTopics.MAINTENANCE_BASE}/maintenanceEvents", 
                                        json.dumps({"value": self.maintenance_events}))
                self.rate_limited_publish(f"{MQTTTopics.MAINTENANCE_BASE}/totalDowntime", 
                                        json.dumps({"value": self.total_downtime}))
                self.rate_limited_publish(f"{MQTTTopics.MAINTENANCE_BASE}/mtbf", 
                                        json.dumps({"value": self.mtbf}))
                self.rate_limited_publish(f"{MQTTTopics.MAINTENANCE_BASE}/mttr", 
                                        json.dumps({"value": self.mttr}))
                
                planned_maintenance = AdaptationStrategy.PREVENTIVE_MAINTENANCE in self.adaptation_strategies
                self.rate_limited_publish(f"{MQTTTopics.MAINTENANCE_BASE}/plannedMaintenance", 
                                        json.dumps({"value": planned_maintenance}))
                
                # Sensor data - publish individual values
                for i in range(NUM_CNC_MACHINES):
                    self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/cncTemperature/{i}", 
                                            json.dumps({"value": self.cnc_temperatures[i]}))
                    self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/cncVibration/{i}", 
                                            json.dumps({"value": self.cnc_vibrations[i]}))
                
                self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/ambientTemperature", 
                                        json.dumps({"value": self.ambient_temperature}))
                self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/ambientHumidity", 
                                        json.dumps({"value": self.ambient_humidity}))
                
                temp_alert = any(temp > 75 for temp in self.cnc_temperatures)
                self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/temperatureAlert", 
                                        json.dumps({"value": temp_alert}))
                
                vib_alert = any(vib > 5.0 for vib in self.cnc_vibrations)
                self.rate_limited_publish(f"{MQTTTopics.SENSORS_BASE}/vibrationAlert", 
                                        json.dumps({"value": vib_alert}))
                
                # Equipment status data - flattened
                for i in range(NUM_CNC_MACHINES):
                    status = "Operational" if i < self.operational_cnc_machines else "Down"
                    self.rate_limited_publish(f"{MQTTTopics.EQUIPMENT_BASE}/cnc/{i}/status", 
                                            json.dumps({"value": status}))
                    self.rate_limited_publish(f"{MQTTTopics.EQUIPMENT_BASE}/cnc/{i}/temperature", 
                                            json.dumps({"value": self.cnc_temperatures[i]}))
                    self.rate_limited_publish(f"{MQTTTopics.EQUIPMENT_BASE}/cnc/{i}/vibration", 
                                            json.dumps({"value": self.cnc_vibrations[i]}))
                
                for i in range(NUM_ASSEMBLY_STATIONS):
                    self.rate_limited_publish(f"{MQTTTopics.EQUIPMENT_BASE}/assembly/{i}/status", 
                                            json.dumps({"value": "Operational"}))
                
                for i in range(NUM_QC_STATIONS):
                    self.rate_limited_publish(f"{MQTTTopics.EQUIPMENT_BASE}/qc/{i}/status", 
                                            json.dumps({"value": "Operational"}))
                
                # Time data - flattened
                self.rate_limited_publish(f"{MQTTTopics.TIME_BASE}/currentTime", 
                                        json.dumps({"value": self.current_time}))
                
                day = int(self.current_time / (24 * 60))
                self.rate_limited_publish(f"{MQTTTopics.TIME_BASE}/day", 
                                        json.dumps({"value": day}))
                
                hour = int((self.current_time % (24 * 60)) / 60)
                self.rate_limited_publish(f"{MQTTTopics.TIME_BASE}/hour", 
                                        json.dumps({"value": hour}))
                
                minute = int(self.current_time % 60)
                self.rate_limited_publish(f"{MQTTTopics.TIME_BASE}/minute", 
                                        json.dumps({"value": minute}))
                
                formatted_time = self.format_time(self.current_time)
                self.rate_limited_publish(f"{MQTTTopics.TIME_BASE}/formattedTime", 
                                        json.dumps({"value": formatted_time}))
            
            # Wait before next update
            yield self.env.timeout(MQTT_UPDATE_INTERVAL * 60 / REAL_TIME_FACTOR)  # Convert seconds to simulation minutes
    
    def format_time(self, minutes):
        """Convert minutes to days, hours, minutes format"""
        days = minutes // (24 * 60)
        hours = (minutes % (24 * 60)) // 60
        mins = minutes % 60
        return f"Day {days}, {hours:02d}:{mins:02d}"
    
    def publish_strategy_status(self):
        """发布所有策略的当前状态"""
        strategies = list(AdaptationStrategy)
        
        # 为每个策略发布单独的消息
        for i, strategy in enumerate(strategies):
            status = strategy in self.adaptation_strategies
            
            # 计算剩余时间（如果适用）
            remaining_time = 0
            if status and strategy in self.strategy_expiration_times:
                remaining_time = max(0, self.strategy_expiration_times[strategy] - self.env.now)
            
            # 使用速率限制发布
            self.rate_limited_publish(f"{MQTTTopics.STRATEGIES_BASE}/{i}/name", 
                                    json.dumps({"value": strategy.value}))
            self.rate_limited_publish(f"{MQTTTopics.STRATEGIES_BASE}/{i}/active", 
                                    json.dumps({"value": status}))
            self.rate_limited_publish(f"{MQTTTopics.STRATEGIES_BASE}/{i}/remainingTime", 
                                    json.dumps({"value": remaining_time}))
            
            # 发布格式化的剩余时间（例如"3天12小时"）
            if remaining_time > 0:
                days = int(remaining_time / (24 * 60))
                hours = int((remaining_time % (24 * 60)) / 60)
                formatted_time = f"{days}天{hours}小时"
                self.rate_limited_publish(f"{MQTTTopics.STRATEGIES_BASE}/{i}/formattedRemainingTime", 
                                        json.dumps({"value": formatted_time}))

    def publish_disruption(self, disruption_type, description):
        """Publish disruption event to MQTT"""
        # Flattened disruption data
        self.rate_limited_publish(f"{MQTTTopics.DISRUPTION_BASE}/time", 
                                json.dumps({"value": self.current_time}))
        self.rate_limited_publish(f"{MQTTTopics.DISRUPTION_BASE}/formattedTime", 
                                json.dumps({"value": self.format_time(self.current_time)}))
        self.rate_limited_publish(f"{MQTTTopics.DISRUPTION_BASE}/type", 
                                json.dumps({"value": disruption_type}))
        self.rate_limited_publish(f"{MQTTTopics.DISRUPTION_BASE}/description", 
                                json.dumps({"value": description}))
        
        # Also log the disruption
        self.log(LogLevel.DISRUPTION, disruption_type, description)

    def calculate_worker_costs(self):
        """Calculate and accumulate daily worker salary costs"""
        while True:
            # Wait for 1 day (24 hours)
            yield self.env.timeout(24 * 60)
            
            # Calculate worker salary costs
            daily_worker_hours = WORKER_SHIFT_HOURS * WORKER_SHIFTS_PER_DAY  # Total hours covered per day
            total_worker_hours = self.available_workers * daily_worker_hours
            
            # Apply benefits multiplier to base salary
            daily_worker_cost = total_worker_hours * WORKER_HOURLY_WAGE * WORKER_BENEFITS_FACTOR
            self.costs += daily_worker_cost
            
            # Keep track of worker costs separately if needed
            if not hasattr(self, 'worker_salary_costs'):
                self.worker_salary_costs = 0
            self.worker_salary_costs += daily_worker_cost
            
            # Log the worker costs
            self.log(LogLevel.INFO, "Finance", 
                    f"Applied daily worker costs: ${daily_worker_cost:,.2f} for {self.available_workers} workers")
            
            # Publish worker costs via MQTT
            if hasattr(self, 'mqtt_client') and self.mqtt_client:
                self.rate_limited_publish(f"{MQTTTopics.FINANCIAL_BASE}/workerCosts", 
                                        json.dumps({"value": self.worker_salary_costs}))


    def calculate_inventory_costs(self):
        """Calculate and accumulate inventory holding costs"""
        while True:
            # Wait for 1 day (24 hours)
            yield self.env.timeout(24 * 60)
            
            # Calculate daily inventory holding costs
            raw_materials_cost = self.raw_materials * RAW_MATERIAL_COST * INVENTORY_HOLDING_COST_RATE
            parts_cost = self.parts_inventory * PARTS_VALUE * INVENTORY_HOLDING_COST_RATE
            finished_goods_cost = self.finished_products * FINISHED_PRODUCT_VALUE * INVENTORY_HOLDING_COST_RATE
            
            daily_holding_cost = raw_materials_cost + parts_cost + finished_goods_cost
            self.inventory_holding_costs += daily_holding_cost
    
    def calculate_energy_usage(self):
        """Calculate and accumulate energy usage and costs"""
        while True:
            # Wait for 1 hour
            yield self.env.timeout(60)
            
            # Skip during power outages
            if self.power_outage:
                continue
                
            # Calculate hourly energy usage
            hourly_cnc_energy = (self.operational_cnc_machines * CNC_ENERGY_USAGE * 
                                (self.cnc_utilization / 100))
            
            hourly_assembly_energy = (NUM_ASSEMBLY_STATIONS * ASSEMBLY_ENERGY_USAGE * 
                                     (self.assembly_utilization / 100))
            
            hourly_qc_energy = (NUM_QC_STATIONS * QC_ENERGY_USAGE * 
                               (self.qc_utilization / 100))
            
            hourly_facility_energy = FACILITY_BASE_ENERGY
            
            # Apply peak load optimization
            if AdaptationStrategy.PEAK_LOAD_OPTIMIZATION in self.adaptation_strategies:
                peak_hours = self.current_time % (24 * 60) >= 8 * 60 and self.current_time % (24 * 60) <= 17 * 60
                
                if peak_hours:
                    energy_reduction = 0.15  # 15% during peak hours
                    hourly_cnc_energy *= (1 - energy_reduction)
                    hourly_assembly_energy *= (1 - energy_reduction)
                    hourly_qc_energy *= (1 - energy_reduction)
                else:
                    energy_reduction = 0.05  # 5% during off-peak
                    hourly_facility_energy *= (1 - energy_reduction)
            
            # Update energy usage metrics
            self.cnc_energy_usage += hourly_cnc_energy
            self.assembly_energy_usage += hourly_assembly_energy
            self.qc_energy_usage += hourly_qc_energy
            self.facility_energy_usage += hourly_facility_energy
            
            # Calculate total energy and cost
            hourly_total_energy = hourly_cnc_energy + hourly_assembly_energy + hourly_qc_energy + hourly_facility_energy
            self.total_energy_usage += hourly_total_energy
            self.energy_costs += hourly_total_energy * ENERGY_COST_PER_KWH
    
    def update_sensor_data(self):
        """Update sensor readings periodically"""
        while True:
            # Wait for 10 minutes
            yield self.env.timeout(10)
            
            # Skip during power outages
            if self.power_outage:
                continue
            
            # Update ambient conditions (slight random variations)
            self.ambient_temperature = max(15, min(30, 
                self.ambient_temperature + random.uniform(-0.5, 0.5)))
            self.ambient_humidity = max(30, min(70, 
                self.ambient_humidity + random.uniform(-1, 1)))
            
            # Update CNC machine temperatures and vibrations
            for i in range(NUM_CNC_MACHINES):
                # Only update operational machines
                if i < self.operational_cnc_machines:
                    # Temperature increases with utilization and has some random variation
                    base_temp = 20 + (self.cnc_utilization / 100) * 40  # 20°C idle, up to 60°C at full load
                    
                    # Machines get hotter over their operation time
                    operation_factor = 1.0
                    
                    # High vibration can indicate pending failure
                    failure_warning = 1.0
                    
                    # If this machine is about to fail, show warning signs
                    if (i == 0 and random.random() < CNC_FAILURE_CHANCE/50 and 
                        AdaptationStrategy.PREVENTIVE_MAINTENANCE not in self.adaptation_strategies):
                        operation_factor = 1.2  # 20% hotter
                        failure_warning = 2.0  # 2x more vibration
                    
                    # Calculate temperature with all factors
                    self.cnc_temperatures[i] = base_temp * operation_factor + random.uniform(-3, 3)
                    
                    # Calculate vibration (higher with utilization)
                    base_vibration = 0.1 + (self.cnc_utilization / 100) * 1.5  # 0.1 idle, up to 1.6 at full load
                    self.cnc_vibrations[i] = base_vibration * failure_warning + random.uniform(-0.1, 0.1)
                else:
                    # Powered down machines cool down towards ambient
                    if self.cnc_temperatures[i] > self.ambient_temperature:
                        self.cnc_temperatures[i] = max(self.ambient_temperature, 
                                                    self.cnc_temperatures[i] - random.uniform(0.5, 1.5))
                    # No vibration when powered down
                    self.cnc_vibrations[i] = 0.0
    
    def calculate_oee(self):
        """Calculate Overall Equipment Effectiveness metrics"""
        while True:
            # Wait for 1 hour
            yield self.env.timeout(60)
            
            # Skip during power outages
            if self.power_outage:
                continue
            
            # Calculate Availability
            # Percentage of scheduled time equipment is available to operate
            total_machines = NUM_CNC_MACHINES
            if total_machines > 0:
                self.availability = self.operational_cnc_machines / total_machines
            else:
                self.availability = 0
            
            # Calculate Performance
            # Percentage of actual production rate compared to maximum capable rate
            max_daily_production = (24 * 60) / CNC_PROCESSING_TIME * self.operational_cnc_machines / PARTS_PER_PRODUCT
            if max_daily_production > 0:
                self.performance = min(1.0, self.daily_production / max_daily_production)
            else:
                self.performance = 0
            
            # Calculate Quality
            # Percentage of good units produced vs total units started
            self.quality = 1.0 - self.defect_rate
            
            # Calculate overall OEE
            self.oee = self.availability * self.performance * self.quality
    
    def apply_strategy_effects(self, strategy, activate=True):
        """Apply or remove the effects of an adaptation strategy"""
        global CNC_FAILURE_CHANCE, SUPPLY_CHAIN_ISSUE_CHANCE, QUALITY_ISSUE_CHANCE
        global ASSEMBLY_TIME, CNC_PROCESSING_TIME, POWER_OUTAGE_CHANCE
        
        # Record the strategy change
        self.strategy_changes_history.append({
            "time": self.env.now,
            "strategy": strategy.value,
            "action": "Activated" if activate else "Deactivated"
        })
        
        # Apply or remove implementation costs
        if activate:
            # Apply one-time implementation cost
            implementation_cost = StrategyCosts.IMPLEMENTATION[strategy]
            self.costs += implementation_cost
            
            # Record implementation date
            self.strategy_implementation_dates[strategy] = self.env.now

            # 设置策略过期时间
            duration = StrategyDurations.DURATION[strategy]
            expiration_time = self.env.now + duration
            self.strategy_expiration_times[strategy] = expiration_time

            # Log the implementation
            self.log(LogLevel.STRATEGY, "Implementation", 
                    f"Strategy '{strategy.value}' implemented at a cost of ${implementation_cost:,}, will expire after {duration/(24*60):.1f} days")
            
            # Add weekly cost to recurring costs
            self.strategy_weekly_costs += StrategyCosts.WEEKLY[strategy]
        else:
            # When deactivating, remove weekly costs
            self.strategy_weekly_costs -= StrategyCosts.WEEKLY[strategy]
            # 移除过期时间记录
            if strategy in self.strategy_expiration_times:
                del self.strategy_expiration_times[strategy]
            self.log(LogLevel.STRATEGY, "Deactivation", 
                    f"Strategy '{strategy.value}' deactivated, weekly savings of ${StrategyCosts.WEEKLY[strategy]:,}")

        # Apply or remove effects based on the strategy
        if strategy == AdaptationStrategy.PREVENTIVE_MAINTENANCE:
            factor = 0.2 if activate else 5.0  # Reduce by 80% or restore (multiply by 5)
            CNC_FAILURE_CHANCE *= factor
        
        elif strategy == AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT:
            if activate:
                additional_raw = int(INITIAL_RAW_MATERIALS * 0.5)
                additional_parts = int(INITIAL_INVENTORY * 0.5)
                self.raw_materials += additional_raw
                self.parts_inventory += additional_parts
                
                self.log(LogLevel.INFO, "Inventory", 
                        f"JIT system added {additional_raw} raw materials and {additional_parts} parts")
        
        elif strategy == AdaptationStrategy.FLEXIBLE_WORKFORCE:
            factor = 0.7 if activate else (1/0.7)
            ASSEMBLY_TIME *= factor
            CNC_PROCESSING_TIME *= factor
        
        elif strategy == AdaptationStrategy.SUPPLIER_DIVERSIFICATION:
            factor = 0.25 if activate else 4.0
            SUPPLY_CHAIN_ISSUE_CHANCE *= factor
        
        elif strategy == AdaptationStrategy.QUALITY_MONITORING:
            factor = 0.2 if activate else 5.0
            QUALITY_ISSUE_CHANCE *= factor
            
            # Also improve defect detection
            if activate:
                self.defect_rate *= 0.4
            else:
                self.defect_rate /= 0.4
        
        elif strategy == AdaptationStrategy.PEAK_LOAD_OPTIMIZATION:
            if activate:
                POWER_OUTAGE_CHANCE *= 0.6
            else:
                POWER_OUTAGE_CHANCE /= 0.6
        
        elif strategy == AdaptationStrategy.INVENTORY_LIQUIDATION:
            # This strategy allows selling off excess inventory at a discount
            # Effects are implemented in the liquidate_inventory() method
            if activate:
                # Immediately try to liquidate some inventory if activated
                self.env.process(self.liquidate_inventory())
                
        elif strategy == AdaptationStrategy.KPI_MONITORING:
            if activate:
                CNC_FAILURE_CHANCE *= 0.85
                QUALITY_ISSUE_CHANCE *= 0.85
            else:
                CNC_FAILURE_CHANCE /= 0.85
                QUALITY_ISSUE_CHANCE /= 0.85
        
        # Other strategies' effects are implemented in their respective disruption handlers
    def check_strategy_expiration(self):
        """检查并停用任何已过期的策略"""
        current_time = self.env.now
        expired_strategies = []
        
        # 查找所有已过期的策略
        for strategy, expiration_time in self.strategy_expiration_times.items():
            if current_time >= expiration_time and strategy in self.adaptation_strategies:
                expired_strategies.append(strategy)
        
        # 停用过期的策略
        for strategy in expired_strategies:
            self.log(LogLevel.STRATEGY, "Expiration", 
                    f"Strategy '{strategy.value}' has expired after {StrategyDurations.DURATION[strategy]/(24*60):.1f} days")
            
            # 从激活策略集合中移除
            self.adaptation_strategies.remove(strategy)
            
            # 取消策略效果
            self.apply_strategy_effects(strategy, activate=False)
            
            # 发布更新的策略状态
            self.publish_strategy_status()
    def liquidate_inventory(self):
        """Process that sells excess inventory at a discount when needed"""
        if AdaptationStrategy.INVENTORY_LIQUIDATION not in self.adaptation_strategies:
            return
            
        # Identify excess inventory to liquidate
        excess_finished_products = max(0, self.finished_products - self.backlog - 10)  # Keep minimum 10 in stock
        
        if excess_finished_products <= 0:
            return
            
        # Sell at discount (65% of normal price)
        discount_factor = 0.65
        product_price = 1500  # Regular price
        discount_price = product_price * discount_factor
        liquidation_revenue = excess_finished_products * discount_price
        
        # Update inventory and financials
        self.finished_products -= excess_finished_products
        self.liquidation_revenue += liquidation_revenue
        
        self.log(LogLevel.INFO, "Inventory", 
                f"Liquidated {excess_finished_products} finished products at discount, generating ${liquidation_revenue:,.2f}")
                
        # Check again after a delay
        yield self.env.timeout(12 * 60)  # Check twice daily
        
        # Recursively check again if strategy is still active
        if AdaptationStrategy.INVENTORY_LIQUIDATION in self.adaptation_strategies:
            self.env.process(self.liquidate_inventory())
    
    def modify_strategy(self, strategy_idx, activate, custom_duration=None):
        """Add or remove a strategy during simulation"""
        strategies = list(AdaptationStrategy)
        if 0 <= strategy_idx < len(strategies):
            strategy = strategies[strategy_idx]
            
            # Check if this is a one-time strategy
            is_one_time = strategy in ONE_TIME_STRATEGIES
            
            if activate:
                # For one-time strategies, just execute them once and don't add to active strategies
                if is_one_time:
                    # Check if we can afford this strategy
                    implementation_cost = StrategyCosts.IMPLEMENTATION[strategy]
                    revenue = self.revenue + self.liquidation_revenue
                    costs = self.costs + self.inventory_holding_costs + self.energy_costs
                    current_profit = revenue - costs
                    
                    if implementation_cost > (current_profit + 10000):  # Allow some deficit
                        warning_msg = f"WARNING: Strategy '{strategy.value}' costs ${implementation_cost:,} " + \
                                    f"which exceeds current profit of ${current_profit:,}, but implementing anyway"
                        self.log(LogLevel.WARNING, "Strategy", warning_msg)
                    
                    # Execute one-time strategy action
                    self.costs += implementation_cost
                    self.execute_one_time_strategy(strategy)
                    
                    # Track that we executed this strategy (for reporting)
                    self.strategy_changes_history.append({
                        "time": self.env.now,
                        "strategy": strategy.value,
                        "action": "Executed (one-time)"
                    })
                    
                    return f"One-time strategy executed: {strategy.value}"
                
                # For regular strategies with duration
                elif strategy not in self.adaptation_strategies:
                    # Check if we can afford this strategy
                    implementation_cost = StrategyCosts.IMPLEMENTATION[strategy]
                    revenue = self.revenue + self.liquidation_revenue
                    costs = self.costs + self.inventory_holding_costs + self.energy_costs
                    current_profit = revenue - costs
                    
                    if implementation_cost > (current_profit + 10000):  # Allow some deficit
                        warning_msg = f"WARNING: Strategy '{strategy.value}' costs ${implementation_cost:,} " + \
                                    f"which exceeds current profit of ${current_profit:,}, but implementing anyway"
                        self.log(LogLevel.WARNING, "Strategy", warning_msg)
                    
                    # Activate ongoing strategy
                    self.adaptation_strategies.add(strategy)
                    
                    # If custom duration was provided, temporarily save it
                    original_duration = None
                    if custom_duration is not None and custom_duration > 0:
                        original_duration = StrategyDurations.DURATION[strategy]
                        StrategyDurations.DURATION[strategy] = custom_duration
                        duration_days = custom_duration / (24 * 60)
                        self.log(LogLevel.INFO, "Strategy", 
                                f"Using custom duration of {duration_days:.1f} days for strategy '{strategy.value}'")
                    
                    # Apply strategy effect
                    self.apply_strategy_effects(strategy, activate=True)
                    
                    # If we modified the duration, restore original value (to avoid affecting future strategy activations)
                    if original_duration is not None:
                        StrategyDurations.DURATION[strategy] = original_duration
                    
                    return f"Strategy activated: {strategy.value}"
                
                return "No change (strategy already active)"
            
            # Deactivation is only relevant for ongoing strategies
            elif not is_one_time and strategy in self.adaptation_strategies:
                # Calculate how long the strategy has been active (in hours)
                implementation_time = self.env.now - self.strategy_implementation_dates.get(strategy, 0)
                implementation_hours = implementation_time / 60
                
                if implementation_hours < 24:  # Less than 1 day
                    warning_msg = f"Strategy '{strategy.value}' deactivated after only {implementation_hours:.1f} hours"
                    self.log(LogLevel.WARNING, "Strategy", warning_msg)
                
                self.adaptation_strategies.remove(strategy)
                self.apply_strategy_effects(strategy, activate=False)
                return f"Strategy deactivated: {strategy.value}"
            
            return "No change needed"
        
        return "Invalid strategy index"
    
    def execute_one_time_strategy(self, strategy):
        """Execute the actions for a one-time strategy"""
        global NUM_CNC_MACHINES, NUM_ASSEMBLY_STATIONS, NUM_WORKERS
        global CNC_PROCESSING_TIME, ASSEMBLY_TIME
        global POWER_OUTAGE_CHANCE, WORKER_ABSENCE_CHANCE
        
        self.log(LogLevel.STRATEGY, "Execution", f"Executing one-time strategy: {strategy.value}")
        
        if strategy == AdaptationStrategy.PURCHASE_CNC_MACHINE:
            # Add a new CNC machine to the factory
            NUM_CNC_MACHINES += 1
            self.operational_cnc_machines += 1
            
            # Update the resource capacity
            old_cnc = self.cnc_machines
            new_cnc = simpy.Resource(self.env, capacity=NUM_CNC_MACHINES)
            self.cnc_machines = new_cnc
            
            # Initialize sensors for the new machine
            self.cnc_temperatures.append(20.0)  # Initial temperature
            self.cnc_vibrations.append(0.1)     # Initial vibration level
            
            self.log(LogLevel.INFO, "Equipment", 
                    f"New CNC machine purchased and installed. Total now: {NUM_CNC_MACHINES}")
        
        elif strategy == AdaptationStrategy.SELL_CNC_MACHINE:
            if NUM_CNC_MACHINES > 1:  # Don't sell the last machine
                # Remove a CNC machine
                NUM_CNC_MACHINES -= 1
                
                # If all machines are operational, reduce the count
                if self.operational_cnc_machines > 0:
                    self.operational_cnc_machines -= 1
                
                # Update the resource capacity
                old_cnc = self.cnc_machines
                new_cnc = simpy.Resource(self.env, capacity=NUM_CNC_MACHINES)
                self.cnc_machines = new_cnc
                
                # Remove sensor entries for the sold machine
                if len(self.cnc_temperatures) > 0:
                    self.cnc_temperatures.pop()
                if len(self.cnc_vibrations) > 0:
                    self.cnc_vibrations.pop()
                
                # Generate revenue from machine sale
                sale_revenue = 75000  # Resale value of a used CNC machine
                self.revenue += sale_revenue
                
                self.log(LogLevel.INFO, "Equipment", 
                        f"CNC machine sold for ${sale_revenue:,}. Total remaining: {NUM_CNC_MACHINES}")
            else:
                self.log(LogLevel.WARNING, "Equipment", 
                        "Cannot sell the last CNC machine. Sale cancelled.")
        
        elif strategy == AdaptationStrategy.HIRE_WORKERS:
            # Hire 3 new workers
            new_workers = 3
            NUM_WORKERS += new_workers
            self.available_workers += new_workers
            
            # Update worker resource
            old_workers = self.workers
            new_workers_resource = simpy.Resource(self.env, capacity=NUM_WORKERS)
            self.workers = new_workers_resource
            
            self.log(LogLevel.INFO, "Workforce", 
                    f"Hired {new_workers} new workers. Total workforce now: {NUM_WORKERS}")
        
        elif strategy == AdaptationStrategy.REDUCE_WORKFORCE:
            if NUM_WORKERS > 3:  # Maintain minimum workforce
                # Calculate workers to lay off (3 or maintain minimum of 3)
                workers_to_layoff = min(3, NUM_WORKERS - 3)
                NUM_WORKERS -= workers_to_layoff
                
                # Update available workers
                self.available_workers = min(self.available_workers, NUM_WORKERS)
                
                # Update worker resource
                old_workers = self.workers
                new_workers_resource = simpy.Resource(self.env, capacity=NUM_WORKERS)
                self.workers = new_workers_resource
                
                self.log(LogLevel.INFO, "Workforce", 
                        f"Reduced workforce by {workers_to_layoff} workers. Total workforce now: {NUM_WORKERS}")
            else:
                self.log(LogLevel.WARNING, "Workforce", 
                        "Cannot reduce workforce below minimum required staffing. Action cancelled.")
        
        elif strategy == AdaptationStrategy.EMERGENCY_MATERIALS:
            # Immediate raw materials delivery
            emergency_materials = 1000  # Large batch of emergency materials
            self.raw_materials += emergency_materials
            
            self.log(LogLevel.INFO, "Inventory", 
                    f"Emergency raw materials order arrived: +{emergency_materials} units")
        
        elif strategy == AdaptationStrategy.UPGRADE_ASSEMBLY:
            # Improve assembly efficiency permanently
            factor = 0.7  # 30% faster assembly
            ASSEMBLY_TIME *= factor
            
            # Add an additional assembly station
            NUM_ASSEMBLY_STATIONS += 1
            
            # Update assembly station resource
            old_assembly = self.assembly_stations
            new_assembly = simpy.Resource(self.env, capacity=NUM_ASSEMBLY_STATIONS)
            self.assembly_stations = new_assembly
            
            self.log(LogLevel.INFO, "Equipment", 
                    f"Assembly stations upgraded: {NUM_ASSEMBLY_STATIONS} total stations, " +
                    f"assembly time reduced to {ASSEMBLY_TIME:.1f} minutes")
        
        elif strategy == AdaptationStrategy.INSTALL_BACKUP_GENERATOR:
            # Immediately recover from any current power outage
            if self.power_outage:
                self.power_outage = False
                self.log(LogLevel.INFO, "Infrastructure", 
                        "Backup generator restored power to the facility")
            
            # Reduce impact of future power outages for next 24 hours
            old_chance = POWER_OUTAGE_CHANCE
            POWER_OUTAGE_CHANCE *= 0.1  # 90% temporary reduction
            
            # Schedule return to normal after 24 hours
            def restore_power_risk():
                global POWER_OUTAGE_CHANCE
                yield self.env.timeout(24 * 60)  # 24 hours
                POWER_OUTAGE_CHANCE = old_chance
                self.log(LogLevel.INFO, "Infrastructure", 
                        "Temporary backup generator removed. Power outage risk returns to normal.")
            
            self.env.process(restore_power_risk())
            
            self.log(LogLevel.INFO, "Infrastructure", 
                    f"Emergency backup generator installed for 24 hours. Power outage chance reduced from " +
                    f"{old_chance:.3f} to {POWER_OUTAGE_CHANCE:.3f}")
        
        elif strategy == AdaptationStrategy.EXPEDITE_MAINTENANCE:
            # Immediately repair any broken machines
            if self.operational_cnc_machines < NUM_CNC_MACHINES:
                machines_repaired = NUM_CNC_MACHINES - self.operational_cnc_machines
                self.operational_cnc_machines = NUM_CNC_MACHINES
                
                self.log(LogLevel.INFO, "Maintenance", 
                        f"Emergency maintenance completed. {machines_repaired} CNC machines repaired.")
            else:
                # If no machines are down, improve all machine conditions and reduce failure chance for 48 hours
                old_failure_chance = CNC_FAILURE_CHANCE
                CNC_FAILURE_CHANCE *= 0.3  # 70% temporary reduction
                
                # Reset all machine temperatures and vibrations to good values
                for i in range(NUM_CNC_MACHINES):
                    self.cnc_temperatures[i] = 20.0 + random.uniform(0, 2)
                    self.cnc_vibrations[i] = 0.1 + random.uniform(0, 0.1)
                
                # Schedule return to normal after 48 hours
                def restore_failure_chance():
                    global CNC_FAILURE_CHANCE
                    yield self.env.timeout(48 * 60)  # 48 hours
                    CNC_FAILURE_CHANCE = old_failure_chance
                    self.log(LogLevel.INFO, "Maintenance", 
                            "Preventive maintenance effect ended. Machine failure risk returns to normal.")
                
                self.env.process(restore_failure_chance())
                
                self.log(LogLevel.INFO, "Maintenance", 
                        f"Preventive maintenance performed on all machines. Failure chance temporarily reduced from " +
                        f"{old_failure_chance:.3f} to {CNC_FAILURE_CHANCE:.3f} for 48 hours.")
        
        elif strategy == AdaptationStrategy.BULK_ORDER_MATERIALS:
            # Schedule a large materials delivery
            bulk_order_size = 2000  # Units of raw materials
            
            # Delivery will arrive in batches over the next 3 days
            def bulk_delivery():
                # First batch arrives immediately
                first_batch = bulk_order_size // 3
                self.raw_materials += first_batch
                self.log(LogLevel.INFO, "Inventory", 
                        f"First bulk materials batch arrived: +{first_batch} units")
                
                # Second batch after 1 day
                yield self.env.timeout(24 * 60)
                second_batch = bulk_order_size // 3
                self.raw_materials += second_batch
                self.log(LogLevel.INFO, "Inventory", 
                        f"Second bulk materials batch arrived: +{second_batch} units")
                
                # Third batch after another day
                yield self.env.timeout(24 * 60)
                third_batch = bulk_order_size - first_batch - second_batch
                self.raw_materials += third_batch
                self.log(LogLevel.INFO, "Inventory", 
                        f"Final bulk materials batch arrived: +{third_batch} units")
                
            self.env.process(bulk_delivery())
            
            self.log(LogLevel.INFO, "Inventory", 
                    f"Placed bulk order for {bulk_order_size} raw material units. Will arrive in 3 batches over 3 days.")
        
        elif strategy == AdaptationStrategy.CANCEL_PENDING_ORDERS:
            # Cancel part of the backlog to reduce pressure
            if self.backlog > 10:
                cancellation_rate = 0.4  # Cancel 40% of backlog
                orders_to_cancel = int(self.backlog * cancellation_rate)
                
                # Update order metrics
                self.backlog -= orders_to_cancel
                self.cancelled_orders += orders_to_cancel
                
                # Calculate financial impact (some cancellation fees recovered)
                cancellation_fee_rate = 0.15  # Customers pay 15% fee on cancelled orders
                cancellation_revenue = orders_to_cancel * 1500 * cancellation_fee_rate
                self.revenue += cancellation_revenue
                
                self.log(LogLevel.INFO, "Orders", 
                        f"Cancelled {orders_to_cancel} pending orders, received ${cancellation_revenue:,.2f} in fees")
            else:
                self.log(LogLevel.INFO, "Orders", 
                        "Backlog too small to cancel orders effectively")
        
        elif strategy == AdaptationStrategy.REALLOCATE_WORKERS:
            # Temporarily improve efficiency by optimizing worker allocation
            # Speed boost for 8 hours
            old_assembly_time = ASSEMBLY_TIME
            old_cnc_time = CNC_PROCESSING_TIME
            
            # 20% speed improvement on both processes
            ASSEMBLY_TIME *= 0.8
            CNC_PROCESSING_TIME *= 0.8
            
            # Schedule return to normal after 8 hours
            def restore_process_times():
                global ASSEMBLY_TIME, CNC_PROCESSING_TIME
                yield self.env.timeout(8 * 60)  # 8 hours
                ASSEMBLY_TIME = old_assembly_time
                CNC_PROCESSING_TIME = old_cnc_time
                self.log(LogLevel.INFO, "Workforce", 
                        "Worker reallocation shift ended. Processing times return to normal.")
            
            self.env.process(restore_process_times())
            
            self.log(LogLevel.INFO, "Workforce", 
                    "Workers reallocated for optimal efficiency. Processing times reduced by 20% for 8 hours.")
        
        elif strategy == AdaptationStrategy.SCHEDULE_OVERTIME:
            # Schedule a weekend overtime shift (24 hours of increased production)
            # All workers come in for a full day at 1.5x productivity
            old_assembly_time = ASSEMBLY_TIME
            old_cnc_time = CNC_PROCESSING_TIME
            
            # 33% speed improvement on all processes
            ASSEMBLY_TIME *= 0.67
            CNC_PROCESSING_TIME *= 0.67
            
            # Schedule return to normal after 24 hours
            def end_overtime():
                global ASSEMBLY_TIME, CNC_PROCESSING_TIME
                yield self.env.timeout(24 * 60)  # 24 hours
                ASSEMBLY_TIME = old_assembly_time
                CNC_PROCESSING_TIME = old_cnc_time
                self.log(LogLevel.INFO, "Workforce", 
                        "Overtime shift completed. Processing times return to normal.")
            
            self.env.process(end_overtime())
            
            self.log(LogLevel.INFO, "Workforce", 
                    "Weekend overtime shift scheduled. Processing times reduced by 33% for 24 hours.")
    def monitor_metrics(self):
        """Record key metrics every hour"""
        while True:
            # Record current metrics
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
            self.metrics_history["oee"].append(self.oee * 100)  # Store as percentage
            
            # Calculate resource utilization (updated hourly)
            active_cnc_ratio = min(1.0, self.active_cnc_requests / max(1, self.operational_cnc_machines))
            self.cnc_utilization = active_cnc_ratio * 100
            
            assembly_utilization = min(1.0, self.active_worker_requests / max(1, self.available_workers))
            self.assembly_utilization = assembly_utilization * 100
            
            qc_utilization = min(1.0, self.active_qc_requests / max(1, NUM_QC_STATIONS))
            self.qc_utilization = qc_utilization * 100
            
            # Check if it's time to apply weekly strategy costs (every 7 days)
            if self.current_time > 0 and self.current_time % (7 * 24 * 60) < 60:  # First hour of each 7-day period
                if self.strategy_weekly_costs > 0:
                    self.costs += self.strategy_weekly_costs
                    self.log(LogLevel.INFO, "Finance", 
                            f"Applied weekly strategy maintenance costs: ${self.strategy_weekly_costs:,}")
            
            # Log critical conditions
            self.check_critical_conditions()
            self.check_strategy_expiration()
            # Wait for 1 hour
            yield self.env.timeout(60)
    
    def check_critical_conditions(self):
        """Check for and log critical conditions"""
        # Check raw materials
        if self.raw_materials < 100:
            self.log(LogLevel.WARNING, "Inventory", 
                    f"Low raw materials: {self.raw_materials} units")
        
        # Check backlog
        if self.backlog > self.current_order_rate * 5:  # More than 5 days of orders
            self.log(LogLevel.WARNING, "Production", 
                    f"High backlog: {self.backlog} orders waiting")
        
        # Check profit trend
        if len(self.metrics_history["profit"]) >= 24:  # At least 24 hours of data
            # Check if last 24 hours have been negative
            recent_profits = self.metrics_history["profit"][-24:]
            if all(p < 0 for p in recent_profits):
                self.log(LogLevel.WARNING, "Finance", 
                        "Negative profits for 24 consecutive hours")
        
        # Check equipment status
        if self.operational_cnc_machines < NUM_CNC_MACHINES / 2:
            self.log(LogLevel.WARNING, "Equipment", 
                    f"Critical equipment shortage: only {self.operational_cnc_machines}/{NUM_CNC_MACHINES} CNC machines operational")
        
        # Check worker availability
        if self.available_workers < NUM_WORKERS / 2:
            self.log(LogLevel.WARNING, "Workforce", 
                    f"Critical worker shortage: only {self.available_workers}/{NUM_WORKERS} workers available")
    
    def generate_disruptions(self):
        """Generate random disruptions based on defined probabilities"""
        while True:
            # Wait for 6 hours before checking for disruptions
            yield self.env.timeout(6 * 60)
            
            # Check for each type of disruption
            
            # 1. CNC Machine Failure
            if random.random() < CNC_FAILURE_CHANCE / 4:  # Convert daily chance to 6-hour chance
                # Skip if preventive maintenance is active and luck is on our side
                if (AdaptationStrategy.PREVENTIVE_MAINTENANCE in self.adaptation_strategies and 
                    random.random() < 0.7):
                    pass  # Failure prevented
                else:
                    # Create disruption notification for user
                    self.disruption_notification = "ALERT: CNC Machine Failure detected!"
                    self.disruption_notification_time = self.env.now
                    
                    # Execute the disruption
                    self.env.process(self.cnc_machine_failure())
            
            # 2. Sudden Order Spike
            if random.random() < SUDDEN_ORDER_SPIKE_CHANCE / 4:
                self.disruption_notification = "ALERT: Sudden order spike detected!"
                self.disruption_notification_time = self.env.now
                self.env.process(self.order_spike())
            
            # 3. Supply Chain Issue
            if random.random() < SUPPLY_CHAIN_ISSUE_CHANCE / 4:
                # Skip if supplier diversification is active and luck is on our side
                if (AdaptationStrategy.SUPPLIER_DIVERSIFICATION in self.adaptation_strategies and 
                    random.random() < 0.8):
                    pass  # Supply chain issue avoided
                else:
                    self.disruption_notification = "ALERT: Supply chain disruption detected!"
                    self.disruption_notification_time = self.env.now
                    self.env.process(self.supply_chain_disruption())
            
            # 4. Worker Absence
            if random.random() < WORKER_ABSENCE_CHANCE / 4:
                self.disruption_notification = "ALERT: Worker absence reported!"
                self.disruption_notification_time = self.env.now
                
                # Less severe if flexible workforce is active
                if AdaptationStrategy.FLEXIBLE_WORKFORCE in self.adaptation_strategies:
                    self.env.process(self.worker_absence(max_absent=1))
                else:
                    self.env.process(self.worker_absence(max_absent=3))
            
            # 5. Quality Issue
            if random.random() < QUALITY_ISSUE_CHANCE / 4:
                self.disruption_notification = "ALERT: Quality control issue detected!"
                self.disruption_notification_time = self.env.now
                
                # Less severe if quality monitoring is active
                if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                    self.env.process(self.quality_control_issue(duration=4*60))  # 4 hours
                else:
                    self.env.process(self.quality_control_issue(duration=12*60))  # 12 hours
            
            # 6. Power Outage
            if random.random() < POWER_OUTAGE_CHANCE / 4:
                self.disruption_notification = "ALERT: Power outage detected!"
                self.disruption_notification_time = self.env.now
                self.env.process(self.power_outage_event())
            
            # 7. NEW: Order Cancellation
            if random.random() < ORDER_CANCELLATION_CHANCE / 4:
                self.disruption_notification = "ALERT: Bulk order cancellation received!"
                self.disruption_notification_time = self.env.now
                self.env.process(self.order_cancellation())
    
    def order_cancellation(self):
        """Simulate cancellation of existing orders"""
        if not self.order_cancellation_active and self.backlog > 0:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.ORDER_CANCELLATION.value,
                "description": "Customer cancelled significant portion of orders"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.ORDER_CANCELLATION.value, 
                                  "Customer cancelled significant portion of orders")
            
            self.order_cancellation_active = True
            
            # Calculate how many orders will be cancelled (20-50% of backlog)
            cancellation_rate = random.uniform(0.2, 0.5)
            orders_to_cancel = int(self.backlog * cancellation_rate)
            
            # If inventory liquidation strategy is active, reduce the impact
            if AdaptationStrategy.INVENTORY_LIQUIDATION in self.adaptation_strategies:
                # Only 60% as many orders get cancelled if we have quick liquidation ability
                orders_to_cancel = int(orders_to_cancel * 0.6)
                self.log(LogLevel.INFO, "Inventory", 
                        f"Rapid Inventory Liquidation reduced order cancellation impact")
                
                # Trigger immediate liquidation attempt
                self.env.process(self.liquidate_inventory())
            
            # Update order metrics
            self.backlog -= orders_to_cancel
            self.cancelled_orders += orders_to_cancel
            
            self.log(LogLevel.WARNING, "Orders", 
                    f"Order Cancellation: {orders_to_cancel} orders cancelled ({cancellation_rate*100:.1f}% of backlog)")
            
            # Calculate financial impact (cancellation fees, if any)
            cancellation_fee_rate = 0.1  # Customers pay 10% fee on cancelled orders
            cancellation_revenue = orders_to_cancel * 1500 * cancellation_fee_rate
            self.revenue += cancellation_revenue
            
            if cancellation_revenue > 0:
                self.log(LogLevel.INFO, "Finance", 
                        f"Received ${cancellation_revenue:,.2f} in cancellation fees")
            
            # Duration of disruption
            disruption_duration = random.randint(4, 12) * 60  # 4-12 hours
            
            # Wait for disruption to end
            yield self.env.timeout(disruption_duration)
            
            self.order_cancellation_active = False
            self.log(LogLevel.INFO, "Orders", "Order cancellation event ended")
    
    def cnc_machine_failure(self):
        """Simulate a CNC machine failure"""
        # Only fail an operational machine
        if self.operational_cnc_machines > 0:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.CNC_FAILURE.value,
                "description": "A CNC machine has broken down"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.CNC_FAILURE.value, "A CNC machine has broken down")
            
            # Record for maintenance metrics
            self.maintenance_events += 1
            if self.last_failure_time > 0:
                time_between_failures = self.env.now - self.last_failure_time
                # Update MTBF as running average
                if self.maintenance_events > 1:
                    self.mtbf = (self.mtbf * (self.maintenance_events - 1) + time_between_failures) / self.maintenance_events
                else:
                    self.mtbf = time_between_failures
            self.last_failure_time = self.env.now
            
            # Remove machine from service
            self.operational_cnc_machines -= 1
            
            # Determine repair time - between 8 and 36 hours
            repair_time = random.randint(8, 36) * 60  # in minutes
            repair_cost_base = 5000  # Base repair cost
            
            # Faster repairs if modular repair kits strategy is active
            if AdaptationStrategy.MODULAR_REPAIR_KITS in self.adaptation_strategies:
                repair_time *= 0.6  # 40% shorter repair time
                self.log(LogLevel.INFO, "Maintenance", 
                        "Modular repair kits enabled faster repairs")
            
            # Even faster with KPI monitoring
            if AdaptationStrategy.KPI_MONITORING in self.adaptation_strategies:
                repair_time *= 0.85  # Additional 15% reduction
                repair_cost_base *= 0.9  # 10% lower repair costs
                self.log(LogLevel.INFO, "Maintenance", 
                        "Real-time KPI monitoring enabled early issue detection")
            
            # Calculate total repair cost (base + hourly)
            hourly_rate = 250  # Hourly service rate
            repair_cost = repair_cost_base + (repair_time / 60) * hourly_rate
            
            # Add repair costs
            self.costs += repair_cost
            
            self.log(LogLevel.INFO, "Maintenance", 
                    f"CNC repair will take {repair_time/60:.1f} hours and cost ${repair_cost:,.2f}")
            
            # Update maintenance metrics
            self.total_downtime += repair_time
            self.repair_times.append(repair_time)
            # Update MTTR as running average
            self.mttr = sum(self.repair_times) / len(self.repair_times)
            
            # Wait for repair time
            yield self.env.timeout(repair_time)
            
            # Return machine to service
            self.operational_cnc_machines += 1
            self.log(LogLevel.INFO, "Maintenance", "CNC machine repair completed and returned to service")
    
    def order_spike(self):
        """Simulate a sudden increase in orders"""
        global ASSEMBLY_TIME, CNC_PROCESSING_TIME
        
        # Record the disruption
        disruption_data = {
            "time": self.env.now,
            "type": DisruptionType.ORDER_SPIKE.value,
            "description": "Received a sudden surge in orders"
        }
        self.disruptions_history.append(disruption_data)
        
        # Publish disruption via MQTT
        self.publish_disruption(DisruptionType.ORDER_SPIKE.value, "Received a sudden surge in orders")
        
        # Calculate spike magnitude - 2x to 4x normal rate
        spike_multiplier = random.uniform(2.0, 4.0)
        original_rate = self.current_order_rate
        self.current_order_rate = original_rate * spike_multiplier
        
        # Determine spike duration - 1 to 3 days
        spike_duration = random.randint(1, 3) * 24 * 60
        
        # Calculate approximate size of the spike
        additional_orders = int((self.current_order_rate - original_rate) * (spike_duration / (24 * 60)))
        
        self.log(LogLevel.INFO, "Orders", 
                f"Order spike: {additional_orders} additional orders over {spike_duration/60/24:.1f} days")
        
        # If outsourcing strategy is active, handle more orders externally
        if AdaptationStrategy.OUTSOURCING in self.adaptation_strategies:
            # Outsource 60% of the additional orders
            outsourced_orders = int(additional_orders * 0.6)
            self.fulfilled_orders += outsourced_orders
            
            # Calculate revenue and costs
            outsource_revenue = outsourced_orders * 1500  # Revenue per product
            outsource_cost = outsourced_orders * 1200    # Outsourcing cost per product
            
            self.revenue += outsource_revenue
            self.costs += outsource_cost
            
            self.log(LogLevel.INFO, "Production", 
                    f"Outsourced {outsourced_orders} orders for revenue of ${outsource_revenue:,} and cost of ${outsource_cost:,}")
        
        # If overtime policy is active, increase production capacity
        if AdaptationStrategy.OVERTIME_POLICY in self.adaptation_strategies:
            # Temporarily increase worker efficiency
            overtime_factor = 1.3  # 30% more efficient with overtime
            old_assembly_time = ASSEMBLY_TIME
            old_cnc_time = CNC_PROCESSING_TIME
            
            ASSEMBLY_TIME /= overtime_factor
            CNC_PROCESSING_TIME /= overtime_factor
            
            # Calculate overtime costs
            overtime_hours = spike_duration / 60  # Convert minutes to hours
            overtime_workers = min(NUM_WORKERS, NUM_CNC_MACHINES + NUM_ASSEMBLY_STATIONS)
            overtime_rate = 50  # $50/hour overtime rate
            overtime_cost = overtime_hours * overtime_workers * overtime_rate * 0.5  # Assume 50% of time is overtime
            
            self.costs += overtime_cost
            
            self.log(LogLevel.INFO, "Workforce", 
                    f"Implemented overtime policy at cost of ${overtime_cost:,.2f}")
            
            # Wait for spike duration
            yield self.env.timeout(spike_duration)
            
            # Restore original processing times
            ASSEMBLY_TIME = old_assembly_time
            CNC_PROCESSING_TIME = old_cnc_time
        else:
            # Wait for spike duration
            yield self.env.timeout(spike_duration)
        
        # Return to normal order rate
        self.current_order_rate = original_rate
        self.log(LogLevel.INFO, "Orders", "Order rate returned to normal")
    
    def supply_chain_disruption(self):
        """Simulate a disruption in the supply chain"""
        if not self.supply_chain_disrupted:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.SUPPLY_CHAIN.value,
                "description": "Supply chain disruption affecting raw material delivery"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.SUPPLY_CHAIN.value, 
                                  "Supply chain disruption affecting raw material delivery")
            
            self.supply_chain_disrupted = True
            
            # Determine disruption duration - 2 to 7 days
            disruption_duration = random.randint(2, 7) * 24 * 60
            
            # If supplier diversification is active, reduce severity
            if AdaptationStrategy.SUPPLIER_DIVERSIFICATION in self.adaptation_strategies:
                disruption_duration *= 0.5  # 50% shorter disruption
            
            # Wait for disruption duration
            yield self.env.timeout(disruption_duration)
            
            self.supply_chain_disrupted = False
    
    def worker_absence(self, max_absent=3):
        """Simulate worker absences"""
        # Determine number of absent workers
        num_absent = random.randint(1, max_absent)
        num_absent = min(num_absent, self.available_workers)  # Can't have negative workers
        
        if num_absent > 0:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.WORKER_ABSENCE.value,
                "description": f"{num_absent} workers absent"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.WORKER_ABSENCE.value, f"{num_absent} workers absent")
            
            # Record worker absence
            self.available_workers -= num_absent
            
            # Determine absence duration - 1 to 3 days
            absence_duration = random.randint(1, 3) * 24 * 60
            
            # If overtime policy is active, add overtime costs
            if AdaptationStrategy.OVERTIME_POLICY in self.adaptation_strategies:
                # Overtime compensates for some of the missing workforce
                effective_absent = num_absent * 0.6
                # Add overtime costs
                self.costs += absence_duration / 60 * effective_absent * 30  # $30/hour per compensated worker
            
            # Wait for absence duration
            yield self.env.timeout(absence_duration)
            
            # Return workers to duty
            self.available_workers += num_absent
    
    def quality_control_issue(self, duration=8*60):  # Default 8 hours
        """Simulate a quality control issue"""
        if not self.has_quality_issue:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.QUALITY_ISSUE.value,
                "description": "Quality control issue detected in production"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.QUALITY_ISSUE.value, 
                                  "Quality control issue detected in production")
            
            self.has_quality_issue = True
            
            # Determine how many defective products
            defective_rate = 0.4  # 40% defect rate during the issue
            
            # If quality monitoring is active, reduce severity
            if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                defective_rate = 0.15  # 15% defect rate with monitoring
            
            # Calculate impact on current inventory
            defective_products = int(self.finished_products * defective_rate)
            self.finished_products -= defective_products
            
            # Update quality metrics
            self.defect_rate = defective_rate
            self.defects_found += defective_products
            
            # Add costs for waste and rework
            self.costs += defective_products * 300  # Cost per defective product
            
            # Wait for issue resolution
            yield self.env.timeout(duration)
            
            self.has_quality_issue = False
            # Reset defect rate to baseline
            self.defect_rate = 0.02
    
    def power_outage_event(self):
        """Simulate a power outage affecting the entire factory"""
        if not self.power_outage:
            # Record the disruption
            disruption_data = {
                "time": self.env.now,
                "type": DisruptionType.POWER_OUTAGE.value,
                "description": "Power outage affecting entire factory"
            }
            self.disruptions_history.append(disruption_data)
            
            # Publish disruption via MQTT
            self.publish_disruption(DisruptionType.POWER_OUTAGE.value, 
                                  "Power outage affecting entire factory")
            
            self.power_outage = True
            
            # Determine outage duration - 45 minutes to 6 hours
            outage_duration = random.randint(45, 360)
            
            # Calculate production impact
            hourly_production_rate = self.current_order_rate / 24  # Approx hourly rate
            estimated_lost_production = hourly_production_rate * (outage_duration / 60)
            
            # Peak load optimization reduces outage impact
            if AdaptationStrategy.PEAK_LOAD_OPTIMIZATION in self.adaptation_strategies:
                original_duration = outage_duration
                outage_duration *= 0.6  # Reduce by 40%
                
                self.log(LogLevel.INFO, "Power", 
                        f"Peak load optimization reduced outage from {original_duration} to {outage_duration} minutes")
            
            # Calculate outage costs
            restart_cost = 5000  # Base restart cost
            lost_production_cost = estimated_lost_production * FINISHED_PRODUCT_VALUE
            equipment_stress_cost = 250 * self.operational_cnc_machines  # Equipment wear from sudden shutdown
            
            total_outage_cost = restart_cost + lost_production_cost + equipment_stress_cost
            self.costs += total_outage_cost
            
            self.log(LogLevel.WARNING, "Power", 
                    f"Power outage will last {outage_duration} minutes with estimated cost of ${total_outage_cost:,.2f}")
            
            # Update maintenance metrics
            self.total_downtime += outage_duration
            
            # Wait for power to be restored
            yield self.env.timeout(outage_duration)
            
            self.power_outage = False
            self.log(LogLevel.INFO, "Power", "Power has been restored, restarting production")
    
    def generate_orders(self):
        """Generate customer orders at the current rate"""
        while True:
            # Wait for a day
            yield self.env.timeout(24 * 60)
            
            # Reset daily production counter
            self.daily_production = 0
            
            # Calculate daily orders based on current rate
            daily_orders = int(self.current_order_rate)
            
            # Add random variation (±40%)
            daily_orders = int(daily_orders * random.uniform(0.6, 1.4))
            
            # Record new orders
            self.total_orders += daily_orders
            self.backlog += daily_orders
            
            # Process as many orders as possible
            self.process_backlog()
            
            # Order new raw materials if needed
            if self.raw_materials < 200 and not self.supply_chain_disrupted:
                self.env.process(self.order_raw_materials())
    
    def process_backlog(self):
        """Process as many backlogged orders as possible"""
        # Calculate how many products we can make
        available_products = min(self.finished_products, self.backlog)
        
        # Fulfill orders
        if available_products > 0:
            self.finished_products -= available_products
            self.backlog -= available_products
            self.fulfilled_orders += available_products
            self.daily_production += available_products
            
            # Calculate revenue
            product_price = 1500  # $1500 per industrial valve
            batch_revenue = available_products * product_price
            self.revenue += batch_revenue
            
            if available_products >= 10:
                self.log(LogLevel.INFO, "Sales", 
                        f"Shipped {available_products} products for revenue of ${batch_revenue:,}")
    
    def order_raw_materials(self):
        """Order new raw materials"""
        # Order 500 units of raw materials
        order_amount = 500
        
        # JIT Replenishment optimization
        if AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT in self.adaptation_strategies:
            # Calculate demand based on backlog and production rate
            backlog_demand = self.backlog * PARTS_PER_PRODUCT  # Parts needed for backlog
            daily_part_demand = (self.current_order_rate * PARTS_PER_PRODUCT)  # Daily parts demand
            
            # Calculate smart order amount
            safety_factor = 1.15  # Safety factor
            needed_parts = max(0, backlog_demand - self.parts_inventory) + (daily_part_demand * 5)  # Current gap + 5 days demand
            needed_raw = needed_parts * safety_factor
            
            # Adjust order amount, minimum 500, maximum 1000
            order_amount = max(500, min(1000, int(needed_raw)))
            
            self.log(LogLevel.INFO, "Inventory", 
                    f"JIT system optimized order: {order_amount} raw materials based on demand analysis")
        
        # Add costs for raw materials
        self.costs += order_amount * RAW_MATERIAL_COST
        
        # Calculate delivery time
        delivery_time = DELIVERY_TIME
        
        # JIT system reduces delivery time
        if AdaptationStrategy.JUST_IN_TIME_REPLENISHMENT in self.adaptation_strategies:
            delivery_time *= 0.7  # Reduce delivery time by 30%
        
        # If supply chain is disrupted, delivery takes longer
        if self.supply_chain_disrupted:
            delivery_time *= 2
        
        # Wait for delivery
        yield self.env.timeout(delivery_time)
        
        # Receive raw materials
        self.raw_materials += order_amount
    
    def produce_parts(self):
        """Process to produce parts from raw materials"""
        while True:
            # Check if we have power
            if self.power_outage:
                yield self.env.timeout(10)  # Check again in 10 minutes
                continue
                
            # Check if we have raw materials and available machines/workers
            if self.raw_materials <= 0 or self.operational_cnc_machines <= 0 or self.available_workers <= 0:
                yield self.env.timeout(10)  # Wait and check again in 10 minutes
                continue
            
            # We'll use atomic requests for resources to avoid deadlocks
            with self.cnc_machines.request() as cnc_req:
                # Try to get a CNC machine first
                yield cnc_req
                
                # Then try to get a worker
                with self.workers.request() as worker_req:
                    yield worker_req
                    
                    # Update tracking counters once resources are secured
                    self.active_cnc_requests += 1
                    self.active_worker_requests += 1
                    
                    # We have both resources, start production
                    
                    # Calculate batch size (process up to 10 at once, limited by available raw materials)
                    batch_size = min(15, self.raw_materials)
                    
                    # Check if we actually have materials left (might have been claimed by another process)
                    if batch_size <= 0:
                        # Release tracking counters and try again later
                        self.active_cnc_requests -= 1
                        self.active_worker_requests -= 1
                        continue
                    
                    # Consume raw materials - make this atomic to avoid negative values
                    self.raw_materials -= batch_size
                    
                    # Calculate processing time
                    process_time = CNC_PROCESSING_TIME * batch_size
                    
                    # If lean manufacturing is active, reduce processing time
                    if AdaptationStrategy.LEAN_MANUFACTURING in self.adaptation_strategies:
                        process_time *= 0.8  # 20% faster with lean principles
                    
                    # Wait for production to complete
                    yield self.env.timeout(process_time)
                    
                    # Add to parts inventory
                    self.parts_inventory += batch_size
                    
                    # Add production costs
                    self.costs += batch_size * 30  # $30 per part processing cost
                    
                    # Release tracking counters
                    self.active_cnc_requests -= 1
                    self.active_worker_requests -= 1

    def assemble_products(self):
        """Process to assemble parts into finished products"""
        while True:
            # Check if we have power
            if self.power_outage:
                yield self.env.timeout(10)  # Check again in 10 minutes
                continue
                
            # Check if we have enough parts and available workers
            if self.parts_inventory < PARTS_PER_PRODUCT or self.available_workers <= 0:
                yield self.env.timeout(60)  # Wait and check again in an hour
                continue
            
            # Track active worker requests
            self.active_worker_requests += 1
            
            # Check if we'd exceed available workers
            if self.active_worker_requests > self.available_workers:
                self.active_worker_requests -= 1
                yield self.env.timeout(60)  # Wait and try again
                continue
            
            # Request an assembly station and a worker
            with self.assembly_stations.request() as assembly_req, self.workers.request() as worker_req:
                yield assembly_req & worker_req
                
                # We have both resources, start assembly
                
                # Calculate batch size (assemble up to 5 products at once, limited by available parts)
                max_products = self.parts_inventory // PARTS_PER_PRODUCT
                batch_size = min(5, max_products)
                
                # Consume parts
                self.parts_inventory -= batch_size * PARTS_PER_PRODUCT
                
                # Calculate assembly time
                assembly_time = ASSEMBLY_TIME * batch_size
                
                # If lean manufacturing is active, reduce assembly time
                if AdaptationStrategy.LEAN_MANUFACTURING in self.adaptation_strategies:
                    assembly_time *= 0.8  # 20% faster with lean principles
                
                # Wait for assembly to complete
                yield self.env.timeout(assembly_time)
                
                # Account for quality issues during assembly
                if self.has_quality_issue and random.random() < 0.3:
                    # Defective products - only add some to assembled products
                    good_products = int(batch_size * 0.7)
                    assembled_products = good_products
                else:
                    # All products good at assembly stage
                    assembled_products = batch_size
                
                # Add assembly costs
                self.costs += batch_size * 50  # $50 per product assembly cost
                
                # Products need to go through quality control
                for i in range(assembled_products):
                    self.env.process(self.product_to_qc())
                
                # Release worker
                self.active_worker_requests -= 1
    
    def product_to_qc(self):
        """Move a single product through quality control"""
        # New process for quality control station
        
        # Wait until QC station is available
        if self.power_outage:
            # Can't do QC during power outage
            yield self.env.timeout(10)
            return
            
        self.active_qc_requests += 1
        
        # Request a QC station and a worker
        with self.qc_stations.request() as qc_req, self.workers.request() as worker_req:
            yield qc_req & worker_req
            
            # Calculate inspection time per product
            inspection_time = QC_INSPECTION_TIME
            
            # Wait for inspection to complete
            yield self.env.timeout(inspection_time)
            
            # Update QC metrics
            self.total_inspected += 1
            
            # Determine if product passes inspection
            # Base chance of detection based on actual defect
            is_defective = random.random() < self.defect_rate
            defect_detected = False
            
            if is_defective:
                # Chance to detect the defect
                detection_chance = 0.9  # 90% chance to detect real defects
                if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                    detection_chance = 0.98  # 98% with enhanced monitoring
                
                if random.random() < detection_chance:
                    defect_detected = True
                    self.defects_found += 1
                else:
                    # False negative - defect missed
                    self.false_negatives += 1
            else:
                # False positive chance - good product rejected
                false_positive_chance = 0.05  # 5% chance to reject good products
                if AdaptationStrategy.QUALITY_MONITORING in self.adaptation_strategies:
                    false_positive_chance = 0.02  # 2% with enhanced monitoring
                
                if random.random() < false_positive_chance:
                    defect_detected = True
                    self.false_positives += 1
            
            # Add product to finished goods if it passes inspection
            if not defect_detected:
                self.finished_products += 1
            
            # Release resources
            self.active_qc_requests -= 1
            
            # Process backlog immediately after new products are finished
            self.process_backlog()
    
    def quality_control(self):
        """Separate process to continuously calculate quality metrics"""
        while True:
            # Update every hour
            yield self.env.timeout(60)
            
            # Update quality score for OEE calculation
            if self.total_inspected > 0:
                rejection_rate = (self.defects_found + self.false_positives) / self.total_inspected
                self.quality = 1.0 - rejection_rate
            else:
                self.quality = 1.0


class MQTTSimulationManager:
    """Manages the real-time simulation with MQTT interactions"""
    def __init__(self):
        # Create SimPy environment
        self.env = simpy.Environment()
        
        # Create factory
        self.factory = MQTTValueFactory(self.env)
        
        # Simulation control
        self.running = False
        self.paused = False
        self.simulation_end_time = SIMULATION_DAYS * 24 * 60  # convert days to minutes
        
        # Set random seed for reproducibility
        random.seed(42)
    
    def run_simulation(self):
        """Run the simulation with MQTT interactions"""
        self.running = True
        print("Starting Value Factory Simulation with MQTT integration")
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Simulation will run for up to {SIMULATION_DAYS} days")
        
        # Publish initial strategy status
        self.factory.publish_strategy_status()
        
        # Track simulation time
        next_sim_step = 0
        start_time = time.time()
        
        try:
            # Run the simulation until end time or user quits
            while self.env.now < self.simulation_end_time and self.running:
                current_time = time.time()
                
                # If paused, wait
                if self.factory.paused:
                    time.sleep(0.1)
                    continue
                
                # Calculate how much simulation time should have elapsed
                elapsed_real_seconds = current_time - start_time
                target_sim_minutes = elapsed_real_seconds * REAL_TIME_FACTOR
                
                # Run simulation steps
                if target_sim_minutes > next_sim_step:
                    # Run until next target time
                    self.env.run(until=next_sim_step + 1)
                    next_sim_step += 1
                
                # Small sleep to avoid CPU hogging
                time.sleep(0.01)
            
            # Display final status
            day_count = int(self.env.now / (24 * 60))
            hour_count = int((self.env.now % (24 * 60)) / 60)
            minute_count = int(self.env.now % 60)
            
            print("\n=== SIMULATION COMPLETE ===")
            print(f"Simulation ran for: {day_count} days, {hour_count} hours, {minute_count} minutes")
            print(f"Total Orders: {self.factory.total_orders}")
            print(f"Orders Fulfilled: {self.factory.fulfilled_orders}")
            print(f"Orders Cancelled: {self.factory.cancelled_orders}")
            print(f"Fulfillment Rate: {self.factory.fulfilled_orders / self.factory.total_orders * 100:.1f}%")
            
            # Calculate final profit
            total_revenue = self.factory.revenue + self.factory.liquidation_revenue
            total_costs = self.factory.costs + self.factory.inventory_holding_costs + self.factory.energy_costs
            profit = total_revenue - total_costs
            print(f"Final Profit: ${profit:,.2f}")
            
            print(f"Overall Equipment Effectiveness (OEE): {self.factory.oee * 100:.1f}%")
            print(f"Energy Usage: {self.factory.total_energy_usage:.1f} kWh")
            print(f"Energy Costs: ${self.factory.energy_costs:.2f}")
            
        except KeyboardInterrupt:
            self.running = False
            print("\nSimulation interrupted")
        except Exception as e:
            print(f"Simulation error: {e}")
        finally:
            # Clean up MQTT connection
            if self.factory.mqtt_client:
                self.factory.mqtt_client.loop_stop()
                self.factory.mqtt_client.disconnect()
                print("MQTT connection closed")


def main():
    """Main function to run the simulation"""
    print("=== MQTT-ENABLED VALUE FACTORY SIMULATION ===")
    print("\nThis simulation will run a factory with MQTT integration:")
    print("1. All factory data will be published to MQTT topics")
    print("2. Strategy selection and simulation control via MQTT commands")
    print("3. Random disruptions will occur throughout the simulation")
    print("4. System logs and events will be published to MQTT topic")
    print("\nAvailable strategies:")
    
    # Print strategies with costs
    strategies = list(AdaptationStrategy)
    for i, strategy in enumerate(strategies):
        imp_cost = StrategyCosts.IMPLEMENTATION[strategy]
        weekly = StrategyCosts.WEEKLY[strategy]
        print(f"{i}. {strategy.value}")
        print(f"   Cost: ${imp_cost:,} upfront + ${weekly:,}/week")
    
    print("\nPress Ctrl+C to stop the simulation")
    
    # Create and run simulation
    manager = MQTTSimulationManager()
    manager.run_simulation()


if __name__ == "__main__":
    main()