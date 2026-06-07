from __future__ import annotations

import html
import re
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================================
# App paths and visual constants
# ============================================================================
# Keeping project-relative paths in one place makes it obvious that the
# dashboard only reads local artifacts created by the daily scraper run.
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "lucky.db"
LOG_DIR = BASE_DIR / "logs"

COLORS = {
    "background": "#0a0e1a",
    "surface": "#0f1929",
    "cyan": "#00d4ff",
    "purple": "#7b2fff",
    "green": "#00ff88",
    "amber": "#ffb300",
    "red": "#ff4040",
    "text": "#e0e8f8",
    "muted": "#5a7090",
    "border": "rgba(0, 212, 255, 0.2)",
}

st.set_page_config(
    page_title="LUCKY // INTELLIGENCE SYSTEM",
    page_icon="⚡",
    layout="wide",
)


def inject_styles() -> None:
    """Install the JARVIS-style look across Streamlit's generated markup."""
    st.markdown(
        f"""
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {{
            background: {COLORS["background"]};
            color: {COLORS["text"]};
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            background-image:
                repeating-linear-gradient(
                    0deg,
                    rgba(0, 212, 255, 0.035) 0,
                    rgba(0, 212, 255, 0.035) 1px,
                    transparent 1px,
                    transparent 42px
                ),
                repeating-linear-gradient(
                    90deg,
                    rgba(0, 212, 255, 0.03) 0,
                    rgba(0, 212, 255, 0.03) 1px,
                    transparent 1px,
                    transparent 42px
                );
        }}

        [data-testid="stSidebar"] {{
            background: #08101d;
            border-right: 1px solid {COLORS["border"]};
        }}

        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, rgba(15,25,41,0.96), rgba(8,16,29,0.96));
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 0 22px rgba(0, 212, 255, 0.08);
        }}

        [data-testid="stMetricLabel"] p,
        [data-testid="stMetricValue"] {{
            color: {COLORS["cyan"]} !important;
            text-shadow: 0 0 8px {COLORS["cyan"]};
            font-family: "Consolas", "SFMono-Regular", monospace;
            letter-spacing: 0;
        }}

        [data-testid="stMetricDelta"] {{
            color: {COLORS["text"]} !important;
        }}

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            font-family: "Consolas", "SFMono-Regular", monospace;
        }}

        .lucky-header {{
            border: 1px solid {COLORS["border"]};
            background:
                linear-gradient(100deg, rgba(0,212,255,0.13), rgba(123,47,255,0.08) 52%, rgba(15,25,41,0.82)),
                {COLORS["surface"]};
            border-radius: 8px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 0 28px rgba(0, 212, 255, 0.12);
        }}

        .lucky-title {{
            color: {COLORS["cyan"]};
            font-size: clamp(2rem, 5vw, 4.7rem);
            font-weight: 900;
            line-height: 0.9;
            text-shadow: 0 0 16px rgba(0, 212, 255, 0.85);
            font-family: "Consolas", "SFMono-Regular", monospace;
        }}

        .lucky-subtitle,
        .panel-title,
        .muted-label {{
            color: {COLORS["muted"]};
            font-family: "Consolas", "SFMono-Regular", monospace;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        .status-line {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100%;
            gap: 0.6rem;
            color: {COLORS["text"]};
            font-family: "Consolas", "SFMono-Regular", monospace;
            font-weight: 700;
        }}

        .status-dot {{
            width: 0.85rem;
            height: 0.85rem;
            border-radius: 50%;
            display: inline-block;
            animation: pulse 1.4s infinite;
        }}

        .online {{ background: {COLORS["green"]}; box-shadow: 0 0 14px {COLORS["green"]}; }}
        .offline {{ background: {COLORS["red"]}; box-shadow: 0 0 14px {COLORS["red"]}; }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.45; transform: scale(0.82); }}
        }}

        .sync-panel {{
            text-align: right;
            font-family: "Consolas", "SFMono-Regular", monospace;
            color: {COLORS["text"]};
        }}

        .sync-value {{
            color: {COLORS["cyan"]};
            text-shadow: 0 0 8px rgba(0, 212, 255, 0.7);
            font-weight: 800;
            margin-top: 0.25rem;
        }}

        .event-feed {{
            max-height: 760px;
            overflow-y: auto;
            padding-right: 0.3rem;
        }}

        .event-card {{
            background: rgba(15, 25, 41, 0.88);
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.85rem;
            box-shadow: inset 0 0 18px rgba(0, 212, 255, 0.035);
        }}

        .event-card a {{
            color: {COLORS["text"]};
            text-decoration: none;
            font-size: 1.05rem;
            font-weight: 800;
        }}

        .event-card a:hover {{ color: {COLORS["cyan"]}; }}

        .badge-row, .meta-row, .tag-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            align-items: center;
            margin-top: 0.7rem;
        }}

        .badge, .tag {{
            border: 1px solid {COLORS["border"]};
            color: {COLORS["cyan"]};
            border-radius: 999px;
            padding: 0.16rem 0.52rem;
            font-size: 0.72rem;
            font-family: "Consolas", "SFMono-Regular", monospace;
        }}

        .new-badge {{
            border-color: rgba(0, 255, 136, 0.45);
            color: {COLORS["green"]};
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.16);
        }}

        .score-row {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.8rem;
            align-items: start;
            margin-top: 0.85rem;
        }}

        .score-number {{
            min-width: 3.4rem;
            font-size: 1.75rem;
            font-weight: 900;
            font-family: "Consolas", "SFMono-Regular", monospace;
            text-shadow: 0 0 10px currentColor;
        }}

        .reasoning {{
            color: {COLORS["muted"]};
            font-style: italic;
            line-height: 1.45;
        }}

        .meta-row {{
            color: {COLORS["text"]};
            font-family: "Consolas", "SFMono-Regular", monospace;
            font-size: 0.82rem;
        }}

        .empty-card, .error-card {{
            background: rgba(15, 25, 41, 0.9);
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            color: {COLORS["text"]};
            font-family: "Consolas", "SFMono-Regular", monospace;
        }}

        .error-card {{
            border-color: rgba(255, 64, 64, 0.65);
            box-shadow: 0 0 24px rgba(255, 64, 64, 0.14);
        }}

        .footer {{
            color: {COLORS["muted"]};
            text-align: center;
            margin-top: 1.5rem;
            font-family: "Consolas", "SFMono-Regular", monospace;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_latest_log() -> dict[str, str | int]:
    """Parse the latest Lucky log for header stats without needing a DB write."""
    latest_logs = sorted(LOG_DIR.glob("lucky_*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not latest_logs:
        return {"last_sync": "-", "tiles": 0, "new": 0, "errors": 0}

    log_text = latest_logs[0].read_text(encoding="utf-8", errors="replace")
    timestamps = re.findall(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", log_text, flags=re.MULTILINE)

    # A daily log can contain multiple runs. Stats should represent the most
    # recent completed summary, so only parse the text after the last finish line.
    last_summary_start = log_text.rfind("Run finished")
    summary_text = log_text[last_summary_start:] if last_summary_start != -1 else log_text
    tiles_match = re.findall(r"Tiles found\s*:\s*(\d+)\s*\((\d+)\s+new\)", summary_text)
    errors_match = re.findall(r"Errors\s*:\s*(.+)$", summary_text, flags=re.MULTILINE)
    failed_match = re.findall(r"Failed\s*:\s*(.+)$", summary_text, flags=re.MULTILINE)

    errors = 0
    if failed_match:
        errors = len([item for item in failed_match[-1].split(",") if item.strip()])
    elif errors_match and errors_match[-1].strip().lower() != "none":
        errors = 1

    return {
        "last_sync": timestamps[-1] if timestamps else "-",
        "tiles": int(tiles_match[-1][0]) if tiles_match else 0,
        "new": int(tiles_match[-1][1]) if tiles_match else 0,
        "errors": errors,
    }


@st.cache_data(ttl=300)
def load_events() -> pd.DataFrame:
    """Read the SQLite database in URI read-only mode for dashboard safety."""
    db_uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        df = pd.read_sql_query("SELECT * FROM events", connection)

    # Normalize columns once after loading so filters, charts, and cards can
    # share the same typed values without repeating conversions.
    df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce")
    df["is_new"] = pd.to_numeric(df["is_new"], errors="coerce").fillna(0).astype(int)
    df["deadline_date"] = pd.to_datetime(df["deadline"], format="%d/%m/%Y", errors="coerce")
    df["start_date_parsed"] = pd.to_datetime(df["start_date"], format="%d/%m/%Y", errors="coerce")
    return df


def score_color(score: float | int | None) -> str:
    """Return the dashboard color used anywhere an event score appears."""
    if pd.isna(score):
        return COLORS["muted"]
    if score >= 8:
        return COLORS["green"]
    if score >= 5:
        return COLORS["amber"]
    return COLORS["red"]


def score_gradient(score: int) -> str:
    """Blend bar/point color from red at score 1 to cyan at score 10."""
    start = (255, 64, 64)
    end = (0, 212, 255)
    ratio = max(0, min(score - 1, 9)) / 9
    rgb = tuple(round(start[index] + (end[index] - start[index]) * ratio) for index in range(3))
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def split_themes(raw_themes: str | None) -> list[str]:
    """Turn stored theme text into compact chips for event cards."""
    if not raw_themes:
        return []
    return [part.strip() for part in re.split(r"[,;|]", str(raw_themes)) if part.strip()]


def truncate_title(title: str, limit: int = 30) -> str:
    """Short chart labels keep the right-side timeline readable."""
    if len(title) <= limit:
        return title
    return f"{title[: limit - 1]}..."


def render_database_missing() -> None:
    """Show a full-page offline state when the scraper has not created lucky.db."""
    st.markdown(
        """
        <div class="error-card">
            <h1>DATABASE NOT FOUND</h1>
            <p>run <code>python run.py</code> first</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(log_stats: dict[str, str | int], database_online: bool) -> None:
    """Render the three-part system banner at the top of the dashboard."""
    status_class = "online" if database_online else "offline"
    status_label = "SYSTEM ONLINE" if database_online else "DATABASE OFFLINE"

    left, center, right = st.columns([3, 2, 3])
    with left:
        st.markdown(
            """
            <div class="lucky-header">
                <div class="lucky-title">LUCKY</div>
                <div class="lucky-subtitle">INTELLIGENCE SYSTEM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with center:
        st.markdown(
            f"""
            <div class="lucky-header status-line">
                <span class="status-dot {status_class}"></span>
                <span>{status_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="lucky-header sync-panel">
                <div class="muted-label">LAST SYNC</div>
                <div class="sync-value">{html.escape(str(log_stats["last_sync"]))}</div>
                <div>{int(log_stats["tiles"])} tiles / {int(log_stats["new"])} new / {int(log_stats["errors"])} errors</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_metrics(df: pd.DataFrame) -> None:
    """Calculate and display the five top-level intelligence metrics."""
    scored = df[df["score_status"].eq("ok") & df["relevance_score"].notna()]
    total_events = len(df)
    new_today = int(df["is_new"].eq(1).sum())
    avg_score = scored["relevance_score"].mean()
    pending = int(df["relevance_score"].isna().sum())

    columns = st.columns(5)
    columns[0].metric("TOTAL EVENTS", total_events)
    columns[1].metric("NEW TODAY", new_today, delta=f"+{new_today} since last run")
    columns[2].metric("AVG SCORE", "-" if pd.isna(avg_score) else f"{avg_score:.1f}")
    columns[3].metric("SCORED", len(scored))
    columns[4].metric("PENDING SCORE", pending, delta="attention required" if pending else "clear")


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Collect sidebar controls and return the filtered event dataframe."""
    st.sidebar.markdown("### SYSTEM FILTERS")
    if st.sidebar.button("Refresh telemetry"):
        st.cache_data.clear()
        st.rerun()

    score_range = st.sidebar.slider("Score range", 0, 10, (0, 10))
    sources = sorted(source for source in df["source"].dropna().unique() if source)
    selected_sources = st.sidebar.multiselect("Source", sources, default=sources)
    show_new_only = st.sidebar.toggle("Show new only", value=False)
    sort_order = st.sidebar.selectbox("Sort order", ["Score ↓", "Score ↑", "Deadline soonest"])

    filtered = df.copy()
    score_for_filter = filtered["relevance_score"].fillna(0)
    filtered = filtered[score_for_filter.between(score_range[0], score_range[1])]

    if selected_sources:
        filtered = filtered[filtered["source"].isin(selected_sources)]
    if show_new_only:
        filtered = filtered[filtered["is_new"].eq(1)]

    # The helper column gives NULL scores predictable placement at the end when
    # sorting by score, while still letting pending events appear in the feed.
    filtered = filtered.assign(_score_missing=filtered["relevance_score"].isna())
    if sort_order == "Score ↓":
        filtered = filtered.sort_values(["_score_missing", "relevance_score"], ascending=[True, False])
    elif sort_order == "Score ↑":
        filtered = filtered.sort_values(["_score_missing", "relevance_score"], ascending=[True, True])
    else:
        filtered = filtered.sort_values(["deadline_date", "_score_missing"], ascending=[True, True], na_position="last")

    return filtered.drop(columns=["_score_missing"])


def render_event_cards(df: pd.DataFrame) -> None:
    """Render event records as custom HTML cards instead of a dataframe."""
    if df.empty:
        st.markdown('<div class="empty-card">NO EVENTS MATCH CURRENT FILTERS</div>', unsafe_allow_html=True)
        return

    cards = ['<div class="event-feed">']
    for _, event in df.iterrows():
        title = html.escape(str(event.get("title") or "Untitled event"))
        url = html.escape(str(event.get("url") or "#"))
        source = html.escape(str(event.get("source") or "unknown").upper())
        deadline = html.escape(str(event.get("deadline") or "-"))
        start_date = html.escape(str(event.get("start_date") or "-"))
        reasoning = html.escape(str(event.get("relevance_reasoning") or "Awaiting scoring telemetry."))
        score = event.get("relevance_score")
        score_text = "PENDING" if pd.isna(score) else f"{int(score)}/10"
        new_badge = '<span class="badge new-badge">NEW</span>' if int(event.get("is_new") or 0) == 1 else ""
        tags = "".join(f'<span class="tag">{html.escape(theme)}</span>' for theme in split_themes(event.get("themes")))

        cards.append(
            (
                '<div class="event-card">'
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
                '<div class="badge-row">'
                f'<span class="badge">{source}</span>{new_badge}'
                "</div>"
                '<div class="score-row">'
                f'<div class="score-number" style="color: {score_color(score)};">{score_text}</div>'
                f'<div class="reasoning">{reasoning}</div>'
                "</div>"
                f'<div class="meta-row">◷ Deadline {deadline} &nbsp;|&nbsp; Start {start_date}</div>'
                f'<div class="tag-row">{tags}</div>'
                "</div>"
            )
        )
    cards.append("</div>")
    st.html("".join(cards))


def make_score_distribution(df: pd.DataFrame) -> go.Figure:
    """Build the score bucket chart from scores 1 through 10."""
    counts = (
        df["relevance_score"]
        .dropna()
        .astype(int)
        .clip(1, 10)
        .value_counts()
        .reindex(range(1, 11), fill_value=0)
        .sort_index()
    )

    figure = go.Figure(
        data=[
            go.Bar(
                x=list(counts.index),
                y=list(counts.values),
                marker_color=[score_gradient(score) for score in counts.index],
                hovertemplate="Score %{x}: %{y} event(s)<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title="SCORE DISTRIBUTION",
        height=280,
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font={"color": COLORS["text"], "family": "Consolas"},
        margin={"l": 30, "r": 15, "t": 45, "b": 30},
        xaxis={"title": "", "dtick": 1, "gridcolor": "rgba(0,212,255,0.1)"},
        yaxis={"title": "", "gridcolor": "rgba(0,212,255,0.1)"},
    )
    return figure


def make_deadline_timeline(df: pd.DataFrame) -> go.Figure:
    """Build the deadline chart from parseable future and current deadlines."""
    timeline = df[df["deadline_date"].notna()].copy()
    today = pd.Timestamp(date.today())
    timeline = timeline[timeline["deadline_date"] >= today]
    timeline = timeline.sort_values("deadline_date").head(18)

    if timeline.empty:
        figure = go.Figure()
    else:
        scores = timeline["relevance_score"].fillna(1).clip(1, 10)
        figure = go.Figure(
            data=[
                go.Scatter(
                    x=timeline["deadline_date"],
                    y=[truncate_title(str(title)) for title in timeline["title"].fillna("Untitled")],
                    mode="markers",
                    marker={
                        "size": scores * 2.3 + 8,
                        "color": [score_gradient(int(score)) for score in scores],
                        "line": {"color": COLORS["cyan"], "width": 1},
                    },
                    text=timeline["title"],
                    hovertemplate="%{text}<br>Deadline %{x|%d %b %Y}<extra></extra>",
                )
            ]
        )

    max_deadline = timeline["deadline_date"].max() if not timeline.empty else today
    figure.update_layout(
        title="DEADLINE TIMELINE",
        height=320,
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font={"color": COLORS["text"], "family": "Consolas"},
        margin={"l": 10, "r": 15, "t": 45, "b": 30},
        xaxis={
            "range": [today, max_deadline + pd.Timedelta(days=2)],
            "gridcolor": "rgba(0,212,255,0.1)",
        },
        yaxis={"title": "", "gridcolor": "rgba(0,212,255,0.1)", "autorange": "reversed"},
    )
    return figure


def render_analytics(df: pd.DataFrame) -> None:
    """Render the right-side chart panel using the currently filtered events."""
    st.plotly_chart(make_score_distribution(df), use_container_width=True)
    st.plotly_chart(make_deadline_timeline(df), use_container_width=True)


def main() -> None:
    """Coordinate page setup, data loading, filtering, and rendering."""
    inject_styles()
    log_stats = read_latest_log()
    render_header(log_stats, DB_PATH.exists())

    if not DB_PATH.exists():
        render_database_missing()
        return

    events = load_events()
    render_metrics(events)
    filtered_events = apply_sidebar_filters(events)

    feed_column, analytics_column = st.columns([0.65, 0.35], gap="large")
    with feed_column:
        st.markdown('<div class="panel-title">EVENT FEED</div>', unsafe_allow_html=True)
        render_event_cards(filtered_events)
    with analytics_column:
        render_analytics(filtered_events)

    st.markdown(
        '<div class="footer">LUCKY runs daily at 07:00 · powered by Playwright · Gemini · SQLite</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
