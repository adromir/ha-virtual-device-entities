# Universal Virtual Device Entities Helper for Home Assistant

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repo-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/adromir/ha-virtual-device-entities)](https://github.com/adromir/ha-virtual-device-entities/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A universal Home Assistant custom integration and helper (`integration_type: helper`) that turns any device into an **Enhanced Virtual Device**. Create custom states with dynamic icons and custom colors, map proxy entities from external smart plugs or sensors, and calculate live metrics (e.g. battery lifetime estimation) using reactive Jinja2 templates!

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=adromir&repository=ha-virtual-device-entities&category=integration)

---

## 💡 The Problem & The Solution

In standard Home Assistant:
- Physical devices are locked to the entities their native integration creates.
- Standard entities **cannot** have different icons and colors per state.
- Smart appliances often lack built-in power or energy metering, requiring separate smart plugs whose entities are detached from the appliance.
- Calculating metrics (such as battery discharge estimation from a replacement date) usually required scattered Jinja2 YAML template sensors.

**Virtual Device Entities** solves this by creating an **Enhanced Virtual Device** in Home Assistant that groups all custom entities, external mapped sensors, custom state machines, and calculations together on one unified device page!

---

## ✨ 4 Powerful Entity Modes

### 1. 🎨 State & Color Machine
Define custom states with **individual icons and colors per state** that change dynamically at runtime:
- **Dynamic `@property def icon`**: The icon updates in real time based on the active state.
- **State Colors**: Exposes `icon_color`, `state_color`, `rgb_color`, and `color` in entity attributes for Lovelace Tile Cards, Vision Glass, Mushroom, and custom cards.
- **Rule Engine**: Evaluates numeric thresholds (`< 3.5`, `3.5 - 200`, `> 200`) or string matches (`cleaning`, `docked`, `error`, `contains fehler`).

**Example: Washing Machine Status from Smart Plug Power**
```text
< 3.5 | Standby | mdi:washing-machine-off | #9e9e9e
3.5 - 200 | Spülen | mdi:washing-machine | #2196f3
> 200 | Schleudern | mdi:washing-machine-alert | #ff9800
```

### 2. 🔌 Mirror / Proxy Entities (External Devices)
Map any entity from any other device directly onto your virtual device!
- **Example**: If your washing machine has no power sensor, select `sensor.smartplug_waschmaschine_power`. The helper creates `sensor.waschmaschine_leistung` directly on the washer's device page!

### 3. 🧮 Reactive Template Calculations
Calculate states and metrics on the fly using Jinja2 expressions:
- Automatically recalculates whenever any referenced entity updates.
- **Example: Estimated Battery Level from Replacement Date & Spec Consumption**:
```jinja2
{{ 100 - ((as_timestamp(now()) - as_timestamp(states('sensor.waschmaschine_akku_gewechselt_am'))) / 86400 * 1.5) | round(0) }}
```
- **Example: Remaining Battery Runtime in Days**:
```jinja2
{{ ((states('sensor.waschmaschine_batterie') | float(0)) / 1.5) | round(1) }}
```

### 4. ✍️ Manual Writable Helpers
Attach input helpers directly to the device:
- Maintenance timestamps (e.g. `Akku gewechselt am`, `Letzter Filterwechsel`).
- Action triggers & Reset buttons (e.g. "Filter zurücksetzen").
- Freeform text notes, serial numbers, or threshold numbers.
- State persistence across reboots via `RestoreEntity`.

---

## 📦 Installation

### Option 1: Via HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Click the badge below:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=adromir&repository=ha-virtual-device-entities&category=integration)

3. Alternatively, in Home Assistant go to **HACS** > **Integrations** > **Three dots (top right)** > **Custom repositories**.
4. Add repository URL: `https://github.com/adromir/ha-virtual-device-entities`
5. Category: **Integration**.
6. Click **Download**, then restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release from the [Releases page](https://github.com/adromir/ha-virtual-device-entities/releases).
2. Copy `custom_components/virtual_device_entities` into `<config>/custom_components/`.
3. Restart Home Assistant.

---

## ⚙️ How to Create & Configure

1. Go to **Settings** > **Devices & Services** > **Helpers**.
2. Click **Create Helper** (+ button).
3. Select **Virtual Device Entities**.
4. **Step 1: Device Setup**:
   - **Device Name**: e.g. *Virtuelle Waschmaschine*.
   - **Base Device (optional)**: Pick an existing physical device, or leave blank for a standalone device.
   - **Initial Entity Type**: Select State Machine, Mirror, Template, or Manual Helper.
5. **Step 2: Configure Entity**:
   - Set up your state rules, source entity, or template.
   - Click **Submit**.
6. **Add More Entities Anytime**:
   - In **Settings** > **Devices & Services** > **Helpers**, click on your Virtual Device and choose **Configure** (⚙️) to add more entities (e.g. power mirrors, battery calculations, maintenance buttons)!

---

## 🛠️ Automation Services

### Set Value

```yaml
action: virtual_device_entities.set_value
target:
  entity_id: sensor.waschmaschine_wartungsstatus
data:
  value: "Reinigung erforderlich"
```

### Reset Entity / Update Timestamp

```yaml
action: virtual_device_entities.reset
target:
  entity_id: sensor.waschmaschine_akku_gewechselt_am
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Author: **Adromir** (<https://github.com/adromir>)
