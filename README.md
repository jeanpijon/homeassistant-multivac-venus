# MultiVac Venus Heat Exchanger (IP)

Home Assistant custom integration for the **MultiVac Venus** heat-recovery ventilation unit (MultiVac Pardubice).

The unit speaks RS485. This integration talks to it through an **RS485 ↔ Ethernet gateway** in raw TCP mode (it opens `socket://<host>:<port>` with pyserial), so Home Assistant does not need to sit next to the unit.

## Entities

| Platform | Entity | Notes |
|---|---|---|
| `climate` | Venus Heat Exchanger | HVAC modes `off` (idle), `auto`, `cool`; fan levels `0`–`3` (`0` = stopped) |
| `sensor` | Temperature out/in ingress and egress | °C |
| `sensor` | Fan power factor ingress / egress | % |

## Installation

### HACS (recommended)
1. HACS → Integrations → ⋮ → **Custom repositories**.
2. Add `https://github.com/jeanpijon/homeassistant-multivac-venus`, category **Integration**.
3. Install **MultiVac Venus Heat Exchanger (IP)** and restart Home Assistant.

### Manual
Copy `custom_components/heat_exchanger` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

Add the integration from **Settings → Devices & services**.

| Field | Description |
|---|---|
| Host | IP address or hostname of the RS485 gateway |
| Port | TCP port of the gateway's serial channel (default `8899`) |
| Name | Optional title (default `MultiVac Venus`) |

Host and port can be changed later from the integration's options. The domain is `heat_exchanger`.

## Notes
- The integration polls the unit once per second from a background thread and sends the fixed command frames for the selected mode and fan level.
- Only one client should talk to the unit's RS485 bus at a time; point the gateway at Home Assistant only.
