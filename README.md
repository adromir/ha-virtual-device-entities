# Universal Virtual Device Entities Helper for Home Assistant

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repo-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/adromir/ha-virtual-device-entities)](https://github.com/adromir/ha-virtual-device-entities/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A universal Home Assistant custom integration and helper (`integration_type: helper`) that allows you to attach arbitrary readable and writable virtual entities directly to existing physical devices, or create standalone virtual devices.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=adromir&repository=ha-virtual-device-entities&category=integration)

---

## 💡 Why Virtual Device Entities?

In standard Home Assistant:
- Physical devices are locked to the entities their native integration creates.
- Adding custom metadata, maintenance timestamps (e.g. filter changes, battery replacement dates), manual operating hours, or custom virtual switches required cumbersome template sensors or disparate helpers scattered across the dashboard.
- **Virtual Device Entities** solves this by binding custom virtual entities **directly into the Home Assistant Device Registry** of the chosen hardware!
- When you open the device page under **Settings -> Devices & Services -> Devices -> [Your Device]**, your new virtual entities appear directly on the device card alongside its native sensors!

---

## ✨ Features

- **Direct Device Registry Binding**:
  - Attach entities directly to any existing hardware device (smart locks, vacuum robots, washing machines, thermostats, etc.).
  - Or create standalone virtual devices if no physical device is selected.
- **6 Supported Platform Types**:
  - `sensor`: Text values, custom state status, numeric measurements, or timestamps.
  - `binary_sensor`: Custom conditions, maintenance warning flags, or boolean states.
  - `switch`: Virtual on/off toggles attached to your device.
  - `number`: Configurable sliders, limits, or setpoints.
  - `button`: Action triggers and instant reset buttons (e.g., "Reset Filter").
  - `text`: Freeform notes, serial numbers, manuals, or instructions.
- **Persistent State Across Restarts**:
  - All entities implement Home Assistant's `RestoreEntity` architecture so values survive reboots.
- **Dedicated Automation Services**:
  - `virtual_device_entities.set_value`: Easily update the value of any virtual entity via automations or dashboard scripts.
  - `virtual_device_entities.reset`: Reset entities to their initial state or set timestamp sensors to current time.
- **100% UI Config Flow & Options Flow**:
  - Set up and adjust entities directly in the Home Assistant UI under Helpers.
- **Bilingual Support**:
  - English and German translations included out of the box.

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
2. Copy the `custom_components/virtual_device_entities` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## ⚙️ How to Use

1. In Home Assistant, go to **Settings** > **Devices & Services** > **Helpers**.
2. Click **Create Helper** (+ button).
3. Select **Virtual Device Entities**.
4. Configure your entity:
   - **Entity Name**: Name of the entity (e.g. *Letzter Filterwechsel*).
   - **Platform Type**: Choose `Sensor`, `Binary Sensor`, `Switch`, `Number`, `Button`, or `Text`.
   - **Base Device (optional)**: Pick the physical device you want this entity to be attached to!
   - **Initial Value**: Default value or state.
   - **Icon**: Any Material Design Icon (e.g. `mdi:air-filter`).
   - **Unit of Measurement**: (Optional, e.g. `days`, `°C`, `kWh`).
   - **Device Class**: (Optional, e.g. `timestamp`, `battery`, `duration`).
5. Click **Submit**. Your new virtual entity is immediately created and visible on your device page!

---

## 🛠️ Service Examples

### Update a Virtual Entity via Automation

```yaml
action: virtual_device_entities.set_value
target:
  entity_id: sensor.waschmaschine_wartungsstatus
data:
  value: "Reinigung erforderlich"
```

### Reset a Timestamp / Counter

```yaml
action: virtual_device_entities.reset
target:
  entity_id: sensor.waschmaschine_letzter_filterwechsel
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Author: **Adromir** (<https://github.com/adromir>)
