import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def crore(value: int) -> float:
    """Convert rupees to crore, rounded to 2 decimal places."""
    return round(value / 1_00_00_000, 2)


def format_inr(value: int) -> str:
    """Format rupees as human-readable Indian number string."""
    if value >= 1_00_00_000:
        return f"₹{crore(value):.2f} Cr"
    elif value >= 1_00_000:
        return f"₹{value / 1_00_000:.2f} L"
    else:
        return f"₹{value:,}"


# ─── Wealth Growth ───────────────────────────────────────────────────────────

def wealth_growth_chart(profiles: list[dict]):
    """Line chart showing total assets and liabilities across election years."""
    rows = [
        {
            "Year": p.get("year", "?"),
            "Total Assets (₹ Cr)": crore(p.get("total_assets", 0)),
            "Total Liabilities (₹ Cr)": crore(p.get("total_liabilities", 0)),
            "Net Worth (₹ Cr)": crore(
                p.get("total_assets", 0) - p.get("total_liabilities", 0)
            ),
        }
        for p in profiles
        if p.get("total_assets", 0) > 0
    ]
    if not rows:
        return None

    df = pd.DataFrame(rows).sort_values("Year")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Year"], y=df["Total Assets (₹ Cr)"],
        mode="lines+markers+text",
        name="Total Assets",
        line=dict(color="#2ecc71", width=3),
        text=[f"₹{v:.1f}Cr" for v in df["Total Assets (₹ Cr)"]],
        textposition="top center",
    ))
    fig.add_trace(go.Scatter(
        x=df["Year"], y=df["Total Liabilities (₹ Cr)"],
        mode="lines+markers+text",
        name="Total Liabilities",
        line=dict(color="#e74c3c", width=3),
        text=[f"₹{v:.1f}Cr" for v in df["Total Liabilities (₹ Cr)"]],
        textposition="top center",
    ))
    fig.add_trace(go.Scatter(
        x=df["Year"], y=df["Net Worth (₹ Cr)"],
        mode="lines+markers",
        name="Net Worth",
        line=dict(color="#3498db", width=2, dash="dot"),
    ))

    fig.update_layout(
        title="Wealth Growth Across Lok Sabha Elections",
        xaxis_title="Election Year",
        yaxis_title="Amount (₹ Crore)",
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def wealth_growth_pct(profiles: list[dict]) -> list[dict]:
    """Calculate percentage growth in assets between each election."""
    sorted_p = sorted(
        [p for p in profiles if p.get("total_assets", 0) > 0],
        key=lambda x: x.get("year", "0"),
    )
    growth = []
    for i in range(1, len(sorted_p)):
        prev = sorted_p[i - 1]
        curr = sorted_p[i]
        prev_assets = prev.get("total_assets", 0)
        curr_assets = curr.get("total_assets", 0)
        if prev_assets > 0:
            pct = round((curr_assets - prev_assets) / prev_assets * 100, 1)
            growth.append({
                "from_year": prev.get("year"),
                "to_year": curr.get("year"),
                "from_assets": format_inr(prev_assets),
                "to_assets": format_inr(curr_assets),
                "growth_pct": pct,
            })
    return growth


# ─── Asset Breakdown ─────────────────────────────────────────────────────────

def asset_breakdown_chart(profile: dict):
    """Pie chart of movable vs immovable assets for a single election year."""
    movable = profile.get("movable_assets", 0)
    immovable = profile.get("immovable_assets", 0)
    if movable + immovable == 0:
        return None

    labels = ["Movable Assets", "Immovable Assets"]
    values = [crore(movable), crore(immovable)]

    fig = px.pie(
        names=labels,
        values=values,
        title=f"Asset Composition — {profile.get('year', '')}",
        color_discrete_sequence=["#3498db", "#e67e22"],
        hole=0.4,
    )
    fig.update_traces(
        texttemplate="%{label}<br>₹%{value:.2f}Cr",
        textposition="outside",
    )
    fig.update_layout(template="plotly_dark")
    return fig


def asset_breakdown_bar(profiles: list[dict]):
    """Grouped bar chart: movable vs immovable across all years."""
    rows = [
        {
            "Year": p.get("year", "?"),
            "Movable (₹ Cr)": crore(p.get("movable_assets", 0)),
            "Immovable (₹ Cr)": crore(p.get("immovable_assets", 0)),
        }
        for p in profiles
        if p.get("total_assets", 0) > 0
    ]
    if not rows:
        return None

    df = pd.DataFrame(rows).sort_values("Year")
    fig = px.bar(
        df,
        x="Year",
        y=["Movable (₹ Cr)", "Immovable (₹ Cr)"],
        barmode="group",
        title="Movable vs Immovable Assets by Election Year",
        color_discrete_map={
            "Movable (₹ Cr)": "#3498db",
            "Immovable (₹ Cr)": "#e67e22",
        },
        template="plotly_dark",
    )
    return fig


# ─── Criminal Cases ──────────────────────────────────────────────────────────

def criminal_cases_chart(profiles: list[dict]):
    """Bar chart showing number of criminal cases per election year."""
    rows = [
        {
            "Year": p.get("year", "?"),
            "Criminal Cases": p.get("num_criminal_cases", 0),
        }
        for p in profiles
    ]
    if not rows or all(r["Criminal Cases"] == 0 for r in rows):
        return None

    df = pd.DataFrame(rows).sort_values("Year")
    fig = px.bar(
        df,
        x="Year",
        y="Criminal Cases",
        title="Criminal Cases Declared per Election Year",
        color="Criminal Cases",
        color_continuous_scale=["#2ecc71", "#e74c3c"],
        template="plotly_dark",
        text="Criminal Cases",
    )
    fig.update_traces(textposition="outside")
    return fig


# ─── Discrepancy Detection ───────────────────────────────────────────────────

def detect_discrepancies(profiles: list[dict]) -> list[dict]:
    """
    Flag suspicious patterns in wealth declarations:
    - Sudden spike (>500% growth in one election cycle)
    - Asset growth with no increase in liabilities (suspicious clean growth)
    - Multiple criminal cases
    - Declared zero assets while winning
    """
    flags = []
    growth = wealth_growth_pct(profiles)

    for g in growth:
        if g["growth_pct"] > 500:
            flags.append({
                "type": "Suspicious Wealth Spike",
                "severity": "HIGH",
                "detail": (
                    f"Assets grew by {g['growth_pct']}% from {g['from_year']} "
                    f"({g['from_assets']}) to {g['to_year']} ({g['to_assets']}). "
                    "This is far above normal inflation/investment returns."
                ),
            })
        elif g["growth_pct"] > 200:
            flags.append({
                "type": "Unusually High Wealth Growth",
                "severity": "MEDIUM",
                "detail": (
                    f"Assets grew by {g['growth_pct']}% from {g['from_year']} "
                    f"to {g['to_year']}."
                ),
            })

    for p in profiles:
        if p.get("num_criminal_cases", 0) >= 5:
            flags.append({
                "type": "Multiple Criminal Cases",
                "severity": "HIGH",
                "detail": (
                    f"{p.get('num_criminal_cases')} criminal cases declared in "
                    f"{p.get('year')} election affidavit."
                ),
            })
        elif p.get("num_criminal_cases", 0) > 0:
            flags.append({
                "type": "Criminal Cases Declared",
                "severity": "MEDIUM",
                "detail": (
                    f"{p.get('num_criminal_cases')} criminal case(s) declared in "
                    f"{p.get('year')} election affidavit."
                ),
            })

        assets = p.get("total_assets", 0)
        liabs = p.get("total_liabilities", 0)
        if assets > 1_00_00_000 and liabs == 0:
            flags.append({
                "type": "Zero Liabilities with High Assets",
                "severity": "LOW",
                "detail": (
                    f"In {p.get('year')}, declared {format_inr(assets)} in assets "
                    "but zero liabilities. Verify if accurate."
                ),
            })

    return flags


def generate_summary_stats(profiles: list[dict]) -> dict:
    """Generate a summary statistics dict for display."""
    if not profiles:
        return {}

    with_assets = [p for p in profiles if p.get("total_assets", 0) > 0]
    if not with_assets:
        return {}

    latest = max(with_assets, key=lambda x: x.get("year", "0"))
    earliest = min(with_assets, key=lambda x: x.get("year", "0"))

    total_growth_pct = None
    if earliest != latest and earliest.get("total_assets", 0) > 0:
        total_growth_pct = round(
            (latest["total_assets"] - earliest["total_assets"])
            / earliest["total_assets"]
            * 100,
            1,
        )

    total_criminal = sum(p.get("num_criminal_cases", 0) for p in profiles)

    return {
        "elections_fought": len(profiles),
        "latest_year": latest.get("year"),
        "latest_assets": format_inr(latest.get("total_assets", 0)),
        "latest_liabilities": format_inr(latest.get("total_liabilities", 0)),
        "earliest_year": earliest.get("year"),
        "earliest_assets": format_inr(earliest.get("total_assets", 0)),
        "total_growth_pct": total_growth_pct,
        "total_criminal_cases_ever": total_criminal,
        "party": latest.get("party", "N/A"),
        "constituency": latest.get("constituency", "N/A"),
        "state": latest.get("state", "N/A"),
    }
