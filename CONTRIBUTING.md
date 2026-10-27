# Contributing a capture

1. Measure following [CAPTURE.md](CAPTURE.md).
2. Share it:
   - from Coil of Duty: `cod share NAME`, or from RackNAM: PICKUP > your profile > Share. Both open the
     **Pickup capture** issue already filled in;
   - by hand: New issue > Pickup capture, paste the profile JSON.
3. The bot checks the profile against the schema and opens a pull request (or comments on the issue with what is wrong).
4. A maintainer merges it; `index.json` is rebuilt by itself.

Rules
- One capture = one pickup unit, measured once (the median of its three scans). Measuring the same unit again on another
  day is welcome: write the same `serial`.
- Brand and model exactly as on the pickup or its box. Leave them empty to keep a capture private (it never reaches the index).
- No personal data in `author` beyond the name or nickname you want shown.
- By sharing you publish the capture under CC BY 4.0.

Developers: `pip install jsonschema && python3 tools/build_index.py --selftest && python3 tools/build_index.py --check`.
