# pickup-db

An open database of measured guitar and bass pickups: DC resistance, inductance, eddy-current loss and coil
capacitance of the bare pickup, averaged over every capture the community shares.

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-support-yellow?logo=buymeacoffee)](https://buymeacoffee.com/tlabcustom)

If this database saves you time, you can support it on [Buy Me a Coffee](https://buymeacoffee.com/tlabcustom).

## What is in it
- `pickups/<brand>/<model>/<id>.json`: one capture each (schema `schema/pickup.schema.json`).
- `guitars/`: whole guitars measured at the output jack (pickups + pots + tone cap + cable).
- `index.json`: rebuilt automatically on every change. One entry per brand + model + position + type + wiring, with
  the average, spread and count of each parameter, and `profile`, the values a simulator uses.

RackNAM (NAM amp rack) and Coil of Duty (pickup X-ray jig) download `index.json` when they start, so every
shared capture becomes a pickup you can simulate.

## Measuring
Follow [CAPTURE.md](CAPTURE.md): calibrated jig, room temperature written down, three scans, no steel nearby.
Repeatable captures are what make the averages trustworthy.

## Sharing
Coil of Duty (`cod share`) and RackNAM open a pre-filled **Pickup capture** issue. A bot validates the profile and opens a
pull request; once merged, the index updates and everyone has it at the next start. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licences
Data (`pickups/`, `guitars/`, `index.json`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code (`tools/`, `schema/`, workflows): MIT, see [LICENSE](LICENSE). Brand and model names belong to their owners and
are used only to identify the pickup measured.
