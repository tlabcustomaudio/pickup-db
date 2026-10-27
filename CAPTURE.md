# Capture protocol `capture/1`

How to measure a pickup so that two people, on two benches, years apart, get the same numbers.
Every capture that follows it says so (`context.protocol = "capture/1"`), and the database trusts it more.

What we measure is the **bare pickup**: DC resistance `Rdc`, inductance `L`, eddy-current loss `Re` and coil
capacitance `Cp`. These belong to the pickup alone. Pots, tone cap and cable change the sound, but they are the
guitar, not the pickup: the simulators add them back as knobs (RackNAM: Cable, Your pots, Their pots).

## 1. Before you start

| Check | Why |
|---|---|
| Room between 18 and 25 °C, write down the temperature | copper Rdc changes 0.39 % per °C; the database corrects it to 20 °C |
| Pickup at room temperature for 30 min (not just out of a cold car or off a hot amp) | the coil must be at the temperature you write down |
| Audio interface on for 10 min | gain and converters drift while warming up |
| Bench free of steel and iron within 30 cm: no steel desk frame, no monitor, phone, laptop, tools, other pickups | steel near the poles raises L and losses |
| Same jig, same short lead (30 cm max) for the calibration and the capture | the lead's capacitance is part of the calibration |

## 2. Calibrate (every session)

1. `cod rec thru`: CAL THRU on, nothing plugged in.
2. `cod rec open`: CAL THRU off, nothing plugged in.

Redo both if you move the jig, change cable or interface, or change the input gain. **Never touch the interface
gain or the output level between calibration and captures** (the sweep level is fixed at -20 dBFS: the magnet pole
pieces are slightly non-linear and a louder sweep reads a different L).

## 3. Connect the pickup

**Bare (preferred, `mode: bare`).** The pickup out of the guitar, or its leads unsoldered from the switch/pots and
taken straight to the jig's GUITAR input with clips:
- humbuckers with 4 conductors: series (the normal humbucker sound) is the default; a split or parallel capture is a
  separate entry: write `wiring`.
- bare metal braid / cover to ground (the jig's sleeve), as in the guitar.
- the pickup lies on a wooden or plastic surface, poles up, nothing on top.

**In the guitar (`mode: in_guitar`).** When the pickup can't come out: the X-ray (`cod rec xray`) measures at the
output jack and separates the pots and cable from the pickup. Strings off, or muted with foam (write `strings`).
Write the pot values and tone cap if you measured them out of circuit (they become locked values in the fit).

## 4. Capture three times

1. `cod rec scan NAME-1` (or `xray`), then unplug and plug the pickup back.
2. `NAME-2`, unplug and plug back.
3. `NAME-3`.

`cod fit` takes the median of the three and writes the spread in `context.repeats`. A good capture has the
resonance within **1 %** and Rdc within **0.5 %** across the three. Over **2 %** the database keeps the capture but leaves
it out of the averages: find what moved (a clip, the lead, something metal) and do it again.

## 5. Cross-check with a meter (recommended)

- Rdc with a multimeter or LCR meter, leads clipped where the jig's were, after the capture.
- L with an LCR meter at its lowest test frequency (100 Hz or 120 Hz is closest to what the jig fits; 1 kHz reads
  higher because of Cp and losses: write `freq_hz`).

Give them to the fit as locked values (`--rdc`, `--L`) only if your meter is better than the jig; otherwise put them in
`context.lcr`: the database uses them to spot a jig that reads wrong.

## 6. Describe it

| Field | Example | Notes |
|---|---|---|
| brand, model | Seymour Duncan, JB SH-4 | exactly as on the pickup or its box, no abbreviations |
| position | bridge | neck / middle / bridge / other |
| type | humbucker | single, humbucker, p90, mini_humbucker, active, bass_single, bass_humbucker |
| wiring | series | humbuckers only |
| magnet | A5 | if known |
| cover | true | cover on or off is a different eddy loss |
| serial | 2019-03 / SN | date code or serial: tells a second capture of the same unit from a new unit |
| temp_c | 21.5 | room temperature |
| interface | Focusrite Saffire 6 USB | |

## 7. Share it

- **Coil of Duty:** `cod share NAME` opens a pre-filled submission on GitHub (you need a free GitHub account).
- **RackNAM:** PICKUP block > your profile > Share.
- **By hand:** open an issue with the "Pickup capture" form and paste the profile JSON.

A maintainer merges it; the index is rebuilt by itself, and every RackNAM and Coil of Duty picks it up at its next start.

## Why the averages get better with more captures

Each pickup model is an entry; every capture of it adds to its average and narrows its spread (`sd`, `n` in
index.json). Units of the same model really differ (winding machines, magnet batches): with enough captures the
spread tells you how much. Captures that follow this protocol, agree with themselves (step 4) and are not outliers
(more than 3 robust sigmas from the others) are the ones averaged.
