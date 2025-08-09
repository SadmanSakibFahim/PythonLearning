# WebPT QA Screenshot Tool

Automates login to WebPT, navigates to patient pages, captures screenshots of specific fields, and saves them under a per-patient folder, using Selenium.

## Setup

1. Python >= 3.9 required.
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Create a config file (see `config.sample.yaml`) and update selectors, URLs, and templates for your WebPT environment.
4. Provide credentials via environment variables or `.env`:
   - `WEBPT_USERNAME`
   - `WEBPT_PASSWORD`

## Usage

Run the CLI:

```
python -m webpt_qa.cli capture \
  --config /absolute/path/to/config.yaml \
  --output-dir /absolute/path/to/output \
  --patient-ids 12345 67890 \
  --pages patient_profile scheduler
```

You can also pass a file of IDs (one per line):

```
python -m webpt_qa.cli capture \
  --config /absolute/path/to/config.yaml \
  --output-dir /absolute/path/to/output \
  --patient-id-file /absolute/path/to/patient_ids.txt
```

Screenshots are saved as:

```
<output-dir>/<patient_id>/<page_key>/<field_key>.png
```

If an element cannot be located, a small `.error.txt` file is emitted and the page source is saved for debugging.

## Notes

- All selectors in the sample config are placeholders; you must update them for your tenant/version of WebPT.
- Consider running without headless for initial selector tuning by setting `SELENIUM_HEADLESS=0` in your environment.
- Two login modes are supported: username/password or existing session cookies (via `cookies_path` in config). MFA flows may require manual cookie export.