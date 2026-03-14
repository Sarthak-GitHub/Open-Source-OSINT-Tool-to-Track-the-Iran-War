# Test Fixtures

Fixtures are **static mock API responses** used by the test suite.
They let tests run without any real API calls, API keys, or internet access.

```
tests/fixtures/
├── ioda_normal.json          ← Normal connectivity (baseline week)
├── ioda_outage.json          ← Severe outage (Feb 28 scenario)
├── acled_quiet.json          ← Low conflict activity
├── acled_conflict.json       ← High conflict activity
├── newsapi_baseline.json     ← Normal news volume
├── newsapi_spike.json        ← 9x news spike
└── adsb_normal.json          ← Normal flight activity
```

## How to Use in Tests

```python
import json
from pathlib import Path

def load_fixture(name: str) -> dict:
    path = Path(__file__).parent / "fixtures" / name
    with open(path) as f:
        return json.load(f)

# In your test:
def test_internet_outage_detected():
    fixture = load_fixture("ioda_outage.json")
    collector = InternetCollector(REGION, START, END)
    result = collector._parse_response(fixture, "IR")
    assert result["outage_score"] > 0.8
```

## Updating Fixtures

When the API response format changes, update the fixture files to match.
Keep them realistic — copy-paste from actual API responses, then anonymise
any sensitive fields.

## Adding New Fixtures

1. Make a real API call (with your keys configured)
2. Save the response to `data/raw/` (happens automatically)
3. Copy the relevant file to `tests/fixtures/`
4. Rename it descriptively: `ioda_<scenario>.json`
5. Add a test that uses it
