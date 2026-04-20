"""
Scraper for myneta.info — Lok Sabha election data.

Strategy:
1. Search → find Lok Sabha candidate URLs
2. For each profile page → grab "Other Elections" table → find compare_profile link
3. compare_profile page → clean multi-election table (assets, liabilities, criminal cases)
4. Individual profile pages → detailed criminal case descriptions
"""

import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
BASE_URL = "https://myneta.info"

LOK_SABHA_SLUGS = {
    "loksabha2024": "2024",
    "loksabha2019": "2019",
    "ls2014": "2014",
    "ls2009": "2009",
    "ls2004": "2004",
    "ls1999": "1999",
    "ls1998": "1998",
}

LOK_SABHA_KEYWORDS = ["lok sabha", "loksabha"]


def _get(url: str, retries: int = 3) -> requests.Response:
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(1.5)


def _year_from_url(url: str) -> str:
    url_lower = url.lower()
    for slug, year in LOK_SABHA_SLUGS.items():
        if slug in url_lower:
            return year
    m = re.search(r"20\d{2}", url)
    return m.group() if m else "Unknown"


def _is_loksabha_url(url: str) -> bool:
    url_lower = url.lower()
    return any(slug in url_lower for slug in LOK_SABHA_SLUGS)


def _parse_rupees_from_text(text: str) -> int:
    """
    Extract the first pure integer (removing commas) from text like
    '3,02,06,889~ 3 Crore+' → 30206889
    '2,51,36,119~ 2 Crore+' → 25136119
    """
    # Take text before any tilde or ~
    text = text.split("~")[0].split("Rs")[-1]
    # Remove everything except digits and commas
    raw = re.sub(r"[^0-9,]", "", text).replace(",", "")
    return int(raw) if raw else 0


# ─── Public API ──────────────────────────────────────────────────────────────

def search_politician(query: str) -> list[dict]:
    """
    Search myneta.info and return Lok Sabha candidate results.
    Each result: {name, party, constituency, election, year, has_criminal, profile_url}
    """
    url = f"{BASE_URL}/search_myneta.php?q={requests.utils.quote(query)}"
    r = _get(url)
    soup = BeautifulSoup(r.text, "lxml")

    tables = soup.find_all("table")
    if len(tables) < 3:
        return []

    result_table = tables[2]
    rows = result_table.find_all("tr")

    seen_urls = set()
    results = []

    for row in rows:
        link = row.find("a", href=True)
        if not link or "candidate.php" not in link.get("href", ""):
            continue

        href = link["href"]
        profile_url = href if href.startswith("http") else f"{BASE_URL}/{href.lstrip('/')}"

        if not _is_loksabha_url(profile_url):
            continue
        if profile_url in seen_urls:
            continue
        seen_urls.add(profile_url)

        # Parse row columns: [name_link, '', name_text, party, constituency, election, criminal_yn]
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        name = link.get_text(strip=True)
        # Remove empty and duplicate-name entries
        meaningful = [c for c in cols if c and c != name]

        party = meaningful[0] if len(meaningful) > 0 else ""
        constituency = meaningful[1] if len(meaningful) > 1 else ""
        election = meaningful[2] if len(meaningful) > 2 else ""
        criminal_yn = meaningful[3] if len(meaningful) > 3 else ""

        results.append({
            "name": name,
            "party": party,
            "constituency": constituency,
            "election": election,
            "year": _year_from_url(profile_url),
            "has_criminal": criminal_yn.strip().upper() == "Y",
            "profile_url": profile_url,
        })

    return results


def get_elections_from_url(profile_url: str, display_name: str = "") -> list[dict]:
    """
    Full pipeline starting directly from a known candidate profile URL.
    Finds the compare_profile link → scrapes all election data for that politician.
    This avoids re-searching by name (which fails for no-space names like 'RahulGandhi').
    """
    # Collect compare_profile URLs: start from this URL, then also try other Lok Sabha
    # URLs for the same candidate found via the Other Elections table
    compare_urls = set()
    try:
        cmp_url = _get_compare_profile_url(profile_url)
        if cmp_url:
            compare_urls.add(cmp_url)
    except Exception:
        pass

    # Also search using display_name (with spaces added between words) to find more URLs
    if display_name:
        # "RahulGandhi" → "Rahul Gandhi"
        spaced = re.sub(r"([A-Z])", r" \1", display_name).strip()
        try:
            candidates = search_politician(spaced)
            for c in candidates:
                try:
                    cmp = _get_compare_profile_url(c["profile_url"])
                    if cmp:
                        compare_urls.add(cmp)
                except Exception:
                    continue
        except Exception:
            pass

    if not compare_urls:
        return []

    all_profiles: dict[tuple, dict] = {}
    for compare_url in compare_urls:
        try:
            for p in _scrape_compare_profile(compare_url):
                key = (p.get("year"), p.get("election_label"))
                if key not in all_profiles:
                    all_profiles[key] = p
        except Exception:
            continue

    profiles = list(all_profiles.values())
    profiles = [p for p in profiles if _is_loksabha_entry(p.get("election_label", ""))]
    profiles.sort(key=lambda x: x.get("year", "0"))
    if display_name and profiles:
        # Set a clean display name on all profiles
        spaced = re.sub(r"([A-Z])", r" \1", display_name).strip()
        for p in profiles:
            if not p.get("name"):
                p["name"] = spaced
    return profiles


def get_all_elections_for_politician(name: str) -> list[dict]:
    """
    Full pipeline: search → compare_profile → structured multi-election data.
    Returns list of election dicts sorted by year (Lok Sabha only).
    """
    # Add spaces between CamelCase words so search works on myneta.info
    spaced_name = re.sub(r"([A-Z])", r" \1", name).strip()

    candidates = search_politician(spaced_name)
    if not candidates:
        candidates = search_politician(name)
    if not candidates:
        return []

    name_key = spaced_name.lower().replace(" ", "")
    matched = [c for c in candidates if name_key in c["name"].lower().replace(" ", "")]
    if not matched:
        matched = candidates

    # Collect compare_profile URLs from ALL Lok Sabha candidate pages
    compare_urls = set()
    for candidate in matched:
        try:
            cmp_url = _get_compare_profile_url(candidate["profile_url"])
            if cmp_url:
                compare_urls.add(cmp_url)
        except Exception:
            continue

    if not compare_urls:
        return _build_profiles_from_search(matched)

    # Scrape all compare_profile pages and merge unique election entries
    all_profiles: dict[tuple, dict] = {}
    for compare_url in compare_urls:
        try:
            for p in _scrape_compare_profile(compare_url):
                key = (p.get("year"), p.get("election_label"))
                if key not in all_profiles:
                    all_profiles[key] = p
        except Exception:
            continue

    profiles = list(all_profiles.values())

    # Filter to Lok Sabha only
    profiles = [
        p for p in profiles
        if _is_loksabha_entry(p.get("election_label", ""))
    ]

    # Try to enrich with detailed criminal case info (best-effort)
    for candidate in matched:
        year = candidate.get("year")
        matching = [p for p in profiles if p.get("year") == year]
        if matching and matching[0].get("num_criminal_cases", 0) > 0:
            try:
                cases = _get_criminal_case_details(candidate["profile_url"])
                matching[0]["criminal_cases"] = cases
            except Exception:
                pass

    profiles.sort(key=lambda x: x.get("year", "0"))
    return profiles


# ─── Internal helpers ────────────────────────────────────────────────────────

def _get_compare_profile_url(profile_url: str) -> Optional[str]:
    """
    From a candidate profile page, find the compare_profile link
    in the 'Other Elections' table.
    """
    r = _get(profile_url)
    soup = BeautifulSoup(r.text, "lxml")
    for a in soup.find_all("a", href=True):
        if "compare_profile.php" in a["href"]:
            href = a["href"]
            return href if href.startswith("http") else f"{BASE_URL}/{href.lstrip('/')}"
    return None


def _scrape_compare_profile(compare_url: str) -> list[dict]:
    """
    Scrape compare_profile.php page.
    Table 2 has: Name | Constituency | Age | Party | Criminal Cases(Y/N) |
                 Number of Cases | Education | Total Assets | Total Liabilities | PAN Given
    """
    r = _get(compare_url)
    soup = BeautifulSoup(r.text, "lxml")
    tables = soup.find_all("table")

    profiles = []
    data_table = None
    for t in tables:
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if "Total Assets" in headers or "Declared Assets" in headers:
            data_table = t
            break
        # Also check first row td headers
        rows = t.find_all("tr")
        if rows:
            first_row_cols = [c.get_text(strip=True) for c in rows[0].find_all("td")]
            if "Total Assets" in first_row_cols:
                data_table = t
                break

    if data_table is None and len(tables) >= 3:
        data_table = tables[2]

    if not data_table:
        return profiles

    rows = data_table.find_all("tr")
    headers = []

    for row in rows:
        ths = row.find_all("th")
        tds = row.find_all("td")

        if ths and not headers:
            headers = [th.get_text(strip=True) for th in ths]
            continue

        if not tds:
            continue

        col_values = [td.get_text(strip=True) for td in tds]
        if len(col_values) < 3:
            continue

        # Build row dict using headers if available
        row_dict = {}
        if headers:
            for i, h in enumerate(headers):
                row_dict[h] = col_values[i] if i < len(col_values) else ""
        else:
            # Positional parsing based on known column order
            # Name | Constituency | Age | Party | Criminal(Y/N) | Num Cases | Education | Assets | Liabilities | PAN
            keys = ["Name", "Constituency", "Age", "Party Code", "Criminal Cases",
                    "Number of Cases", "Education Level", "Total Assets", "Total Liabilities", "PAN Given(Y or N)"]
            for i, k in enumerate(keys):
                row_dict[k] = col_values[i] if i < len(col_values) else ""

        name_field = row_dict.get("Name", "")
        if not name_field:
            continue

        # Extract year and election label from name field
        # e.g. "Narendra Modi in Lok Sabha 2019"
        election_label = ""
        year = "Unknown"
        in_match = re.search(r"\bin\b(.+)$", name_field, re.IGNORECASE)
        if in_match:
            election_label = in_match.group(1).strip()
            year_match = re.search(r"(20\d{2}|19\d{2})", election_label)
            if year_match:
                year = year_match.group(1)
            # Clean name
            candidate_name = name_field[: in_match.start()].strip()
        else:
            candidate_name = name_field

        assets = _parse_rupees_from_text(row_dict.get("Total Assets", "0"))
        liabilities = _parse_rupees_from_text(row_dict.get("Total Liabilities", "0"))
        num_cases = 0
        num_cases_str = row_dict.get("Number of Cases", "0")
        try:
            num_cases = int(re.sub(r"\D", "", num_cases_str)) if num_cases_str else 0
        except ValueError:
            num_cases = 0

        profiles.append({
            "name": candidate_name,
            "election_label": election_label,
            "year": year,
            "constituency": row_dict.get("Constituency", ""),
            "party": row_dict.get("Party Code", ""),
            "education": row_dict.get("Education Level", ""),
            "age": row_dict.get("Age", ""),
            "total_assets": assets,
            "total_liabilities": liabilities,
            "movable_assets": 0,
            "immovable_assets": 0,
            "num_criminal_cases": num_cases,
            "criminal_cases": [],
            "winner": False,
            "state": "",
        })

    return profiles


def _get_criminal_case_details(profile_url: str) -> list[dict]:
    """
    Try to extract detailed criminal case descriptions from a profile page.
    The section lives between 'Details of Criminal Cases' h3 and the next h3.
    """
    r = _get(profile_url)
    soup = BeautifulSoup(r.text, "lxml")

    criminal_h3 = None
    next_h3 = None
    h3s = soup.find_all("h3")
    for i, h3 in enumerate(h3s):
        if "criminal" in h3.get_text(strip=True).lower() and "details" in h3.get_text(strip=True).lower():
            criminal_h3 = h3
            if i + 1 < len(h3s):
                next_h3 = h3s[i + 1]
            break

    if not criminal_h3:
        return []

    cases = []
    node = criminal_h3.next_sibling
    while node:
        if node == next_h3:
            break
        if hasattr(node, "name"):
            if node.name == "table":
                rows = node.find_all("tr")
                hdrs = []
                for row in rows:
                    ths = row.find_all("th")
                    tds = row.find_all("td")
                    if ths and not hdrs:
                        hdrs = [th.get_text(strip=True) for th in ths]
                    elif tds:
                        case = {}
                        for i, td in enumerate(tds):
                            key = hdrs[i] if i < len(hdrs) else f"col_{i}"
                            val = td.get_text(strip=True)
                            if val and val.lower() not in ("nil", ""):
                                case[key] = val
                        if case:
                            cases.append(case)
            elif node.name in ("div", "p"):
                text = node.get_text(strip=True)
                if text and "nil" not in text.lower() and len(text) > 10:
                    cases.append({"description": text})
        node = node.next_sibling

    return cases


def _is_loksabha_entry(election_label: str) -> bool:
    label_lower = election_label.lower()
    return any(kw in label_lower for kw in LOK_SABHA_KEYWORDS)


def _build_profiles_from_search(candidates: list[dict]) -> list[dict]:
    """Fallback when no compare_profile URL found — use search data only."""
    seen = set()
    profiles = []
    for c in candidates:
        key = (c["name"], c["year"])
        if key in seen:
            continue
        seen.add(key)
        profiles.append({
            "name": c["name"],
            "election_label": c["election"],
            "year": c["year"],
            "constituency": c["constituency"],
            "party": c["party"],
            "education": "",
            "age": "",
            "total_assets": 0,
            "total_liabilities": 0,
            "movable_assets": 0,
            "immovable_assets": 0,
            "num_criminal_cases": 1 if c.get("has_criminal") else 0,
            "criminal_cases": [],
            "winner": False,
            "state": "",
        })
    return profiles
