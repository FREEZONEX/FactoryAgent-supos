# Factory Simulation with MQTT
## User Guide

This document provides instructions for using the MQTT-enabled factory simulation system, which allows you to simulate a manufacturing facility with real-time data publishing and strategic decision-making capabilities.

## Overview

The Factory Simulation is a digital twin of a manufacturing facility that:
- Simulates production processes, disruptions, and resource allocation
- Publishes real-time factory data to MQTT topics
- Allows external control through MQTT commands
- Provides opportunities to implement and test adaptation strategies

## Setup Requirements

Before running the simulation, ensure you have:

1. Python 3.6+ installed
2. The following Python packages:
   - simpy
   - matplotlib
   - pandas
   - paho-mqtt

3. Access to an MQTT broker (update the `MQTT_BROKER` and related variables in the script)

## Basic Configuration

The main configuration parameters are at the top of the script:

```python
# Simulation constants
SIMULATION_DAYS = 40  # Total simulation duration
REAL_TIME_FACTOR = 100  # Simulation speed (higher = faster)
MQTT_BROKER = "your mqtt broker"  # Change to your broker address
MQTT_PORT = 1883
MQTT_USERNAME = 'admin'  # Set if authentication is required
MQTT_PASSWORD = 'public'  # Set if authentication is required
```

Update these values to match your environment before running the simulation.

## Running the Simulation

To start the simulation:

1. Open a terminal
2. Navigate to the directory containing the script
3. Run: `python factory_simulation.py`

The simulation will connect to the MQTT broker and begin publishing factory data in real-time.

## MQTT Topic Structure

The simulation publishes data to the following MQTT topic hierarchy:

- `factory/inventory/*` - Raw materials, parts, finished products
- `factory/orders/*` - Orders, backlog, fulfillment rates
- `factory/production/*` - Production rates, supply chain status
- `factory/resources/*` - Equipment, workers, utilization
- `factory/financial/*` - Revenue, costs, profit 
- `factory/disruption/*` - Current disruption events
- `factory/time/*` - Simulation time information
- `factory/energy/*` - Energy usage and efficiency
- `factory/quality/*` - Defect rates and quality metrics
- `factory/equipment/*` - Equipment status
- `factory/sensors/*` - Sensor data (temperature, vibration)
- `factory/oee/*` - Overall Equipment Effectiveness
- `factory/maintenance/*` - Maintenance events and metrics
- `factory/logs/*` - System logs

## Controlling the Simulation

You can control the simulation by publishing commands to the following MQTT topics:

### Simulation Control

Topic: `factory/command/simulation`

Payload format:
```json
{
  "command": "pause|resume|stop"
}
```

Example to pause the simulation:
```json
{
  "command": "pause"
}
```

### Implementing Strategies

There are two ways to implement adaptation strategies:

#### 1. Using the general strategy command

Topic: `factory/command/strategy`

Payload format:
```json
{
  "strategyIndex": 0,
  "activate": true,
  "duration": 14
}
```

Parameters:
- `strategyIndex`: Index of the strategy (0-23) as listed in the console when starting
- `activate`: `true` to activate, `false` to deactivate
- `duration`: Optional, custom duration in days (for strategies with durations)

#### 2. Using direct strategy commands

Topic: `factory/command/{STRATEGY_NAME}`

Example: `factory/command/PREVENTIVE_MAINTENANCE`

Payload format:
```json
{
  "trigger": true,
  "duration": 14
}
```

Parameters:
- `trigger`: `true` to activate, `false` to deactivate
- `duration`: Optional, custom duration in days

## Available Adaptation Strategies

The simulation offers both ongoing strategies (with durations) and one-time actions:

### Ongoing Strategies
- `PREVENTIVE_MAINTENANCE`: Reduces machine failures
- `FLEXIBLE_WORKFORCE`: Improves worker efficiency
- `JUST_IN_TIME_REPLENISHMENT`: Optimizes inventory levels
- `SUPPLIER_DIVERSIFICATION`: Reduces supply chain disruptions
- `OVERTIME_POLICY`: Handles demand spikes
- `QUALITY_MONITORING`: Reduces defect rates
- `KPI_MONITORING`: Improves overall performance
- `MODULAR_REPAIR_KITS`: Speeds up repairs
- `OUTSOURCING`: Handles extra capacity needs
- `LEAN_MANUFACTURING`: Improves efficiency
- `PEAK_LOAD_OPTIMIZATION`: Reduces energy costs
- `INVENTORY_LIQUIDATION`: Liquidates excess inventory

### One-Time Actions
- `PURCHASE_CNC_MACHINE`: Adds a new CNC machine
- `SELL_CNC_MACHINE`: Sells an underutilized machine
- `HIRE_WORKERS`: Adds workers to the workforce
- `REDUCE_WORKFORCE`: Reduces workforce size
- `EMERGENCY_MATERIALS`: Orders immediate materials
- `UPGRADE_ASSEMBLY`: Improves assembly stations
- `INSTALL_BACKUP_GENERATOR`: Mitigates power outages
- `EXPEDITE_MAINTENANCE`: Performs immediate repairs
- `BULK_ORDER_MATERIALS`: Orders large material batch
- `CANCEL_PENDING_ORDERS`: Cancels low-priority orders
- `REALLOCATE_WORKERS`: Optimizes worker allocation
- `SCHEDULE_OVERTIME`: Schedules weekend shift

## Handling Disruptions

The simulation randomly generates various disruptions:

- Machine failures
- Order spikes
- Supply chain issues
- Worker absences
- Quality control problems
- Power outages
- Order cancellations

When a disruption occurs, a notification is published to `factory/disruption/*` topics with details about the type and impact of the disruption.

## Monitoring Factory Performance

To monitor factory performance:

1. Connect an MQTT client to the broker
2. Subscribe to relevant topics (e.g., `factory/#` for all topics)
3. Visualize or analyze the data as needed

Key performance indicators include:
- Profit and revenue (`factory/financial/profit`, `factory/financial/revenue`)
- Order fulfillment rate (`factory/orders/fulfillmentRate`)
- Resource utilization (`factory/resources/cncUtilization`, etc.)
- Overall Equipment Effectiveness (`factory/oee/oee`)
- Energy efficiency (`factory/energy/energyEfficiency`)

## Example: Responding to a Machine Failure

When a CNC machine failure occurs:

1. A notification is published to `factory/disruption/type` with value "CNC Machine Failure"
2. Performance metrics will begin to deteriorate
3. You can respond by:
   - Implementing `EXPEDITE_MAINTENANCE` for immediate repair
   - Activating `PREVENTIVE_MAINTENANCE` to prevent future failures
   - Purchasing a new machine with `PURCHASE_CNC_MACHINE` if budgetary constraints allow

## Conclusion

This simulation provides a realistic testbed for industrial control strategies and MQTT-based industrial monitoring systems. By monitoring the data and implementing appropriate strategies, you can optimize factory performance and respond effectively to disruptions.