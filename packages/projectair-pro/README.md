# projectair-pro

Commercial extension on top of the Apache-2.0-licensed [`projectair`](https://pypi.org/project/projectair/).

This package adds licensed Pro features to the open-source AIR forensic SDK:

- AIR Cloud client transport (push Signed Intent Capsules to a hosted workspace)
- Premium compliance reports (NIST AI RMF, SOC2-AI; OSS ships Article 72 only)
- Premium detector additions as they land
- License gate via locally-verified Ed25519-signed tokens (no phone-home, works air-gapped)

## Install

```bash
pip install projectair-pro
```

You also need a license token. Buy one at <https://vindicara.io/pricing>, then:

```bash
air login --license <your-token>
air status
```

The free OSS detectors and exports continue to work without a license. Pro features that require a license refuse to run without one and tell you what to do.

## License (this package)

Source-available, commercial use requires a paid Vindicara subscription. See [LICENSE](LICENSE) for the full text. The OSS `projectair` package this depends on remains Apache-2.0-licensed and unchanged.
