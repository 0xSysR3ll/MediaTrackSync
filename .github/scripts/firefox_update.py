#!/usr/bin/env python3
import re
from pathlib import Path

import requests

# Fetch latest GeckoDriver version from GitHub
gecko_api = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
gecko_response = requests.get(gecko_api)
gecko_response.raise_for_status()
gecko_version = gecko_response.json()["tag_name"]

# Fetch latest Firefox ESR version from Mozilla's API
firefox_esr_url = (
    "https://product-details.mozilla.org/1.0/firefox_versions.json"
)
firefox_response = requests.get(firefox_esr_url)
firefox_response.raise_for_status()
firefox_esr = firefox_response.json()["FIREFOX_ESR"]

print(f"Latest GeckoDriver: {gecko_version}")
print(f"Latest Firefox ESR: {firefox_esr}")

ci_file = Path(".github/workflows/ci.yml")
if ci_file.exists():
    content = ci_file.read_text()

    # Update GECKODRIVER_VERSION
    content = re.sub(
        r'(GECKODRIVER_VERSION\s*=\s*")[^"]+(")',
        f"\\1{gecko_version}\\2",
        content,
    )

    # Update FIREFOX_ESR_VERSION
    content = re.sub(
        r'(FIREFOX_ESR_VERSION\s*=\s*")[^"]+(")',
        f"\\1{firefox_esr}\\2",
        content,
    )

    ci_file.write_text(content)
    print("Updated environment variables in ci.yml")
else:
    print("ci.yml file not found.")
