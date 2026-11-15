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

## Gateway and wiring

- Any RS485 to Ethernet gateway that offers a **transparent (raw) TCP server** on one port works; the integration is its only client. Use the gateway's TCP port in the config above (for example `4196` or `8899`).
- *To confirm: the serial settings the unit needs on the gateway (baud rate, data bits, parity, stop bits) and how A/B are wired to the unit's RS485 connector. They are set on the gateway, not in this integration, and are not documented here yet.*
- The unit answers each command frame with a 74-byte status reply, from which the integration reads the two fan power factors and the four temperatures.

## If the unit or the gateway is off, or starts late

The entities exist from the start and show **unavailable** until the first valid status reply arrives. If the unit or gateway stops answering for 15 seconds they go unavailable again and recover on their own. The TCP connection is retried with back-off (1 s doubling up to 30 s), so after a power outage no reload or restart is needed, whichever device comes up first.

## Development

```
pip install -r requirements_test.txt
pytest
```

`requirements_test.txt` pulls in `pytest-homeassistant-custom-component`, which needs a recent Python (3.14 at the time of writing). CI runs hassfest, the HACS check and the tests.

## Notes
- The integration polls the unit once per second from a background thread and sends the fixed command frames for the selected mode and fan level.
- Only one client should talk to the unit's RS485 bus at a time; point the gateway at Home Assistant only.
