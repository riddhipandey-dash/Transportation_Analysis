import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).parent / "VEETADAY 2025 TRANSPORATION RECORD.xlsx"

# City keyword to state mapping (uppercase keys for match).
CITY_STATE = {
    # Assam
    "SIVSAGAR": "Assam",
    "SIBSAGAR": "Assam",
    "SILAPATHAR": "Assam",
    "JORHAT": "Assam",
    "DIBRUGARH": "Assam",
    "TINSUKIA": "Assam",
    "GUWAHATI": "Assam",
    # Bihar
    "PATNA": "Bihar",
    "GAYA": "Bihar",
    "ARA": "Bihar",
    "BIHARSHARIF": "Bihar",
    "MUZAFFARPUR": "Bihar",
    "DARBHANGA": "Bihar",
    "BHAGALPUR": "Bihar",
    # Delhi
    "DELHI": "Delhi",
    "NEW DELHI": "Delhi",
    # Haryana
    "GURUGRAM": "Haryana",
    "GURGAON": "Haryana",
    "FARIDABAD": "Haryana",
    "HISAR": "Haryana",
    "ROHTAK": "Haryana",
    "PANIPAT": "Haryana",
    "KARNAL": "Haryana",
    "AMBALA": "Haryana",
    "KURUKSHETRA": "Haryana",
    "BHIWANI": "Haryana",
    # Himachal Pradesh   "SOLAN": "Himachal Pradesh",
    "KANGRA": "Himachal Pradesh",
    # Jharkhand
    "RANCHI": "Jharkhand",
    "JAMSHEDPUR": "Jharkhand",
    "DHANBAD": "Jharkhand",
    # Madhya Pradesh
    "BHOPAL": "Madhya Pradesh",
    "INDORE": "Madhya Pradesh",
    "GWALIOR": "Madhya Pradesh",
    "JABALPUR": "Madhya Pradesh",
    # Maharashtra
    "MUMBAI": "Maharashtra",
    "PUNE": "Maharashtra",
    "NAGPUR": "Maharashtra",
    "NASHIK": "Maharashtra",
    "AURANGABAD": "Maharashtra",
    "THANE": "Maharashtra",
    # Odisha
    "BHUBANESWAR": "Odisha",
    "CUTTACK": "Odisha",
    "BERHAMPUR": "Odisha",
    # Punjab
    "LUDHIANA": "Punjab",
    "AMRITSAR": "Punjab",
    "JALANDHAR": "Punjab",
    "BATALA": "Punjab",
    "PATIALA": "Punjab",
    "BHATINDA": "Punjab",
    "BATHINDA": "Punjab",
    "FARIDKOT": "Punjab",
    "FIROZEPUR": "Punjab",
    "KHARAR": "Punjab",
    "KURALI": "Punjab",
    "BHAWANIGARH": "Punjab",
    # Rajasthan
    "JAIPUR": "Rajasthan",
    "ALWAR": "Rajasthan",
    "BHARATPUR": "Rajasthan",
    "KOTA": "Rajasthan",
    "BARMER": "Rajasthan",
    "JAISALMER": "Rajasthan",
    "AJMER": "Rajasthan",
    # Uttar Pradesh
    "LUCKNOW": "Uttar Pradesh",
    "LKO": "Uttar Pradesh",
    "KANPUR": "Uttar Pradesh",
    "AGRA": "Uttar Pradesh",
    "ALIGARH": "Uttar Pradesh",
    "PRAYAGRAJ": "Uttar Pradesh",
    "ALLAHABAD": "Uttar Pradesh",
    "VARANASI": "Uttar Pradesh",
    "GHAZIPUR": "Uttar Pradesh",
    "GONDA": "Uttar Pradesh",
    "BAHRAICH": "Uttar Pradesh",
    "AYODHYA": "Uttar Pradesh",
    "AMBEDKAR NAGAR": "Uttar Pradesh",
    "AMBEDKARNAGAR": "Uttar Pradesh",
    "BALLIA": "Uttar Pradesh",
    "BALIYA": "Uttar Pradesh",
    "BALRAMPUR": "Uttar Pradesh",
    "ETAWAH": "Uttar Pradesh",
    "ETAWA": "Uttar Pradesh",
    "BULANDSHAHR": "Uttar Pradesh",
    "BULANDSAHAR": "Uttar Pradesh",
    "SIKOHABAD": "Uttar Pradesh",
    "BELTHARA": "Uttar Pradesh",
    # Uttarakhand
    "DEHRADUN": "Uttarakhand",
    "HARIDWAR": "Uttarakhand",
    "RUDRAPUR": "Uttarakhand",
    # West Bengal
    "KOLKATA": "West Bengal",
    "HOWRAH": "West Bengal",
    "SILIGURI": "West Bengal",
}


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    frames = []

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]

        rename_map = {}
        for col in df.columns:
            col_upper = col.strip().upper()
            if col_upper in {"DATE", "DATE."}:
                rename_map[col] = "DATE"
            elif col_upper in {"STATION"}:
                rename_map[col] = "STATION"
            elif col_upper in {"TRANSPORT NAME", "TRANSPORT"}:
                rename_map[col] = "TRANSPORT NAME"
            elif col_upper in {"FREIGHT"}:
                rename_map[col] = "FREIGHT"
            elif col_upper in {"CASH ADVANCE", "ADVANCE"}:
                rename_map[col] = "CASH ADVANCE"
            elif col_upper in {"NET TRANSFER", "NET"}:
                rename_map[col] = "NET TRANSFER"
            elif col_upper in {"DRIVER"}:
                rename_map[col] = "DRIVER"

        df = df.rename(columns=rename_map)

        if "DATE" not in df.columns:
            # Try to discover a date-like column.
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df = df.rename(columns={col: "DATE"})
                    break

        if "DATE" not in df.columns and len(df.columns) > 0:
            first_col = df.columns[0]
            df["DATE"] = pd.to_datetime(df[first_col], errors="coerce")

        df["SHEET_MONTH"] = sheet
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)

    if "DATE" in data.columns:
        data["DATE"] = pd.to_datetime(data["DATE"], errors="coerce")
        data["MONTH"] = data["DATE"].dt.month_name()
    else:
        data["MONTH"] = data["SHEET_MONTH"]

    for col in ["FREIGHT", "CASH ADVANCE", "NET TRANSFER"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    for col in ["STATION", "TRANSPORT NAME", "DRIVER"]:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip()

    return data


def normalize_station(station: str) -> str:
    station = station.upper().strip()
    station = re.sub(r"\s+", " ", station)
    return station


def infer_state(station: str) -> str:
    station_clean = normalize_station(station)
    # Replace separators with space to improve keyword match.
    station_clean = re.sub(r"[+&/(),.-]", " ", station_clean)
    station_clean = re.sub(r"\s+", " ", station_clean)

    matched_states = set()
    for key, state in CITY_STATE.items():
        if key in station_clean:
            matched_states.add(state)

    if len(matched_states) == 1:
        return next(iter(matched_states))
    if len(matched_states) > 1:
        return "Mixed"
    return "Unknown"


def normalize_filter_text(value: str) -> str:
    value = str(value).upper().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_text(value: str) -> str:
    value = str(value).upper().strip()
    value = re.sub(r"\s+", " ", value)
    return value


st.set_page_config(page_title="Transportation Dashboard", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg: #0f111a;
            --surface: #171a24;
            --surface-muted: #1f2433;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --accent: #8b5cf6;
            --accent-2: #22d3ee;
            --accent-3: #f472b6;
            --border: #2a3142;
            --shadow: 0 16px 32px rgba(0, 0, 0, 0.35);
        }

        .stApp {
            background: radial-gradient(circle at top, rgba(139, 92, 246, 0.18), transparent 55%),
                        linear-gradient(180deg, #0f111a 0%, #141826 45%, #0f111a 100%);
            color: var(--text);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at top left, rgba(139, 92, 246, 0.22), transparent 45%),
                        radial-gradient(circle at bottom right, rgba(34, 211, 238, 0.18), transparent 45%),
                        radial-gradient(circle at 60% 80%, rgba(244, 114, 182, 0.16), transparent 48%);
            pointer-events: none;
            z-index: 0;
        }

        .stApp > div {
            position: relative;
            z-index: 1;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .dashboard-hero {
            padding: 1.1rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(120deg, #1a1f2e 0%, rgba(139, 92, 246, 0.18) 55%, rgba(34, 211, 238, 0.18) 100%);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        .dashboard-hero h1 {
            font-family: "Trebuchet MS", "Segoe UI", sans-serif;
            letter-spacing: 0.5px;
            margin-bottom: 0.2rem;
        }

        .dashboard-hero p {
            margin-top: 0.1rem;
            color: var(--muted);
        }

        [data-testid="stMetric"] {
            background: var(--surface);
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        [data-testid="stMetric"] label {
            color: var(--muted) !important;
        }

        [data-testid="stMetric"] div {
            color: var(--text) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #151924 0%, #1a1f2e 60%, #141826 100%);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stMultiSelect {
            color: var(--text);
        }

        .block-container {
            padding-top: 1.4rem;
        }

        .stPlotlyChart {
            background: var(--surface);
            border-radius: 16px;
            padding: 0.4rem 0.6rem;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        .stPlotlyChart:hover {
            border-color: rgba(139, 92, 246, 0.55);
            box-shadow: 0 16px 32px rgba(139, 92, 246, 0.2);
            transition: 0.2s ease;
        }

        .stDataFrame {
            background: var(--surface);
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }

        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            color: var(--muted);
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent) !important;
        }

        .stTabs [data-baseweb="tab"]::after {
            content: "";
            display: block;
            height: 3px;
            margin-top: 6px;
            border-radius: 999px;
            background: transparent;
        }

        .stTabs [aria-selected="true"]::after {
            background: linear-gradient(90deg, var(--accent), var(--accent-2));
        }

        [data-testid="stMetricValue"] {
            color: var(--text) !important;
            font-size: 1.15rem !important;
        }

        .summary-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1rem 1.2rem;
            box-shadow: var(--shadow);
        }

        .summary-card b {
            color: var(--accent);
        }

        .stButton > button {
            background: linear-gradient(90deg, var(--accent), var(--accent-2));
            color: #0b1120;
            border: none;
            border-radius: 999px;
            padding: 0.4rem 1.1rem;
            box-shadow: 0 10px 20px rgba(139, 92, 246, 0.25);
        }

        .stButton > button:hover {
            filter: brightness(1.05);
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(23, 26, 36, 0.85);
            box-shadow: var(--shadow);
        }

        .summary-card ul {
            margin: 0;
            padding-left: 1.2rem;
            color: var(--text);
        }

        .summary-card li {
            margin-bottom: 0.4rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


if not DATA_PATH.exists():
    st.error(f"Data file not found: {DATA_PATH}")
    st.stop()

raw_data = load_data(DATA_PATH)

if "STATION" not in raw_data.columns:
    st.error("No STATION column found in the data.")
    st.stop()

if "TRANSPORT NAME" in raw_data.columns:
    raw_data["TRANSPORT_NAME_NORM"] = raw_data["TRANSPORT NAME"].apply(normalize_text)
else:
    raw_data["TRANSPORT_NAME_NORM"] = ""

with st.expander("Manual Mapping (optional)"):
    st.caption("Paste one mapping per line: STATION,STATE")
    mapping_text = st.text_area(
        "Manual Mapping",
        value="",
        placeholder="Example:\nSIVSAGAR,Assam\nSILAPATHAR,Assam",
        height=160,
    )


def parse_manual_mapping(text: str) -> dict:
    mapping = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," not in line:
            continue
        station, state = line.split(",", 1)
        station = normalize_station(station)
        state = state.strip()
        if station and state:
            mapping[station] = state
    return mapping


manual_mapping = parse_manual_mapping(mapping_text)


def resolve_state(station: str) -> str:
    station_key = normalize_station(station)
    if station_key in manual_mapping:
        return manual_mapping[station_key]

    station_clean = re.sub(r"[+&/(),.-]", " ", station_key)
    station_clean = re.sub(r"\s+", " ", station_clean)
    matched_manual = set()
    for key, state in manual_mapping.items():
        if key and key in station_clean:
            matched_manual.add(state)

    if len(matched_manual) == 1:
        return next(iter(matched_manual))
    if len(matched_manual) > 1:
        return "Mixed"

    return infer_state(station)


raw_data["STATE"] = raw_data["STATION"].apply(resolve_state)

year_label = "2025"
chart_suffix = f" ({year_label})" if year_label else ""

header_title = "Transportation Dashboard"
if year_label:
    header_title = f"Transportation Dashboard ({year_label})"

st.markdown(
    f"""
    <div class="dashboard-hero">
        <h1>{header_title}</h1>
        <p>State is inferred from station name keywords. Multi-city stations in different states are marked as Mixed.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def format_si(value: float, unit: str = "") -> str:
    if pd.isna(value):
        return "0"
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B{unit}"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M{unit}"
    if abs_value >= 1_000:
        return f"{value / 1_000:.2f}K{unit}"
    return f"{value:.0f}{unit}"

st.subheader("Filters")
filter_row = st.columns([1, 2])

state_options = [s for s in raw_data["STATE"].dropna().unique()]
state_select = filter_row[0].multiselect(
    "State",
    sorted(state_options),
    default=sorted(state_options),
)

transport_base = raw_data
if state_select:
    transport_base = transport_base[transport_base["STATE"].isin(state_select)]

transport_display = (
    transport_base.loc[
        transport_base["TRANSPORT_NAME_NORM"].astype(bool),
        ["TRANSPORT_NAME_NORM", "TRANSPORT NAME"],
    ]
    .assign(
        **{
            "TRANSPORT NAME": lambda df: df["TRANSPORT NAME"].astype(str).str.strip(),
        }
    )
)
display_counts = (
    transport_display.groupby(["TRANSPORT_NAME_NORM", "TRANSPORT NAME"])  # type: ignore
    .size()
    .reset_index(name="count")
)
display_choice = (
    display_counts.loc[
        display_counts.groupby("TRANSPORT_NAME_NORM")["count"].idxmax()
    ]
    .set_index("TRANSPORT_NAME_NORM")["TRANSPORT NAME"]
    .to_dict()
)
display_frequency = (
    pd.Series(list(display_choice.values()))
    .value_counts()
    .to_dict()
)

transport_label_map = {}
for norm, display in display_choice.items():
    if display_frequency.get(display, 0) > 1:
        label = f"{display} [{norm}]"
    else:
        label = display
    transport_label_map[label] = norm

transport_options = sorted(transport_label_map.keys())

transport_key = "transport_select"
if transport_key not in st.session_state:
    st.session_state[transport_key] = transport_options
else:
    st.session_state[transport_key] = [
        item for item in st.session_state[transport_key] if item in transport_options
    ]

transport_controls = filter_row[1].columns([1, 1, 3])
if transport_controls[0].button("Select all"):
    st.session_state[transport_key] = transport_options
if transport_controls[1].button("Clear all"):
    st.session_state[transport_key] = []

transport_multiselect_args = {
    "label": "Transport Name",
    "options": transport_options,
    "key": transport_key,
}
if transport_key not in st.session_state:
    transport_multiselect_args["default"] = transport_options

transport_select = transport_controls[2].multiselect(**transport_multiselect_args)

filtered = raw_data.copy()
if state_select:
    filtered = filtered[filtered["STATE"].isin(state_select)]
if transport_select:
    selected_norms = [transport_label_map[label] for label in transport_select]
    filtered = filtered[filtered["TRANSPORT_NAME_NORM"].isin(selected_norms)]

tab_suffix = f" ({year_label})" if year_label else ""
overview_tab, state_tab, transport_tab = st.tabs([
    f"Overview{tab_suffix}",
    f"State and Finance{tab_suffix}",
    f"Transport and Drivers{tab_suffix}",
])

palette_light = px.colors.qualitative.Dark24
chart_template = "plotly_white"

with overview_tab:
    station_unique = filtered["STATION"].dropna().apply(normalize_text).nunique()
    driver_unique = filtered["DRIVER"].dropna().apply(normalize_text).nunique()

    summary_state = (
        filtered.groupby("STATE")["FREIGHT"].sum().sort_values(ascending=False)
    )
    top_state = summary_state.index[0] if not summary_state.empty else "N/A"
    top_state_freight = summary_state.iloc[0] if not summary_state.empty else 0
    bottom_state = summary_state.index[-1] if not summary_state.empty else "N/A"
    bottom_state_freight = summary_state.iloc[-1] if not summary_state.empty else 0

    summary_transport = (
        filtered.groupby("TRANSPORT NAME")["FREIGHT"].sum().sort_values(ascending=False)
    )
    top_transport = summary_transport.index[0] if not summary_transport.empty else "N/A"
    top_transport_freight = summary_transport.iloc[0] if not summary_transport.empty else 0
    bottom_transport = summary_transport.index[-1] if not summary_transport.empty else "N/A"
    bottom_transport_freight = summary_transport.iloc[-1] if not summary_transport.empty else 0

    metric_cols = st.columns(6)
    metric_cols[0].metric("Total Stations", format_si(station_unique))
    metric_cols[1].metric("Total Transport Names", format_si(filtered["TRANSPORT NAME"].nunique()))
    metric_cols[2].metric("Total Drivers", format_si(driver_unique))
    metric_cols[3].metric("Total Freight", f"₹ {format_si(filtered['FREIGHT'].sum())}")
    metric_cols[4].metric("Total Advance", f"₹ {format_si(filtered['CASH ADVANCE'].sum())}")
    metric_cols[5].metric("Total Net Transfer", f"₹ {format_si(filtered['NET TRANSFER'].sum())}")

    st.divider()

    st.subheader(f"Summary{chart_suffix}")
    st.markdown(
        """
        <div class="summary-card">
            <ul>
                <li><b>Top state by freight:</b> {top_state} (₹ {top_state_freight:,.0f})</li>
                <li><b>Bottom state by freight:</b> {bottom_state} (₹ {bottom_state_freight:,.0f})</li>
                <li><b>Top transport by freight:</b> {top_transport} (₹ {top_transport_freight:,.0f})</li>
                <li><b>Bottom transport by freight:</b> {bottom_transport} (₹ {bottom_transport_freight:,.0f})</li>
                <li><b>Active stations:</b> {station_unique} &nbsp;|&nbsp; <b>Active drivers:</b> {driver_unique}</li>
            </ul>
        </div>
        """.format(
            top_state=top_state,
            top_state_freight=top_state_freight,
            bottom_state=bottom_state,
            bottom_state_freight=bottom_state_freight,
            top_transport=top_transport,
            top_transport_freight=top_transport_freight,
            bottom_transport=bottom_transport,
            bottom_transport_freight=bottom_transport_freight,
            station_unique=station_unique,
            driver_unique=driver_unique,
        ),
        unsafe_allow_html=True,
    )

    # Monthwise-statewise station count
    month_state_counts = (
        filtered.groupby(["MONTH", "STATE"]) ["STATION"]
        .count()
        .reset_index(name="Station Count")
    )
    month_state_counts["MONTH"] = pd.Categorical(
        month_state_counts["MONTH"],
        categories=[
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        ordered=True,
    )
    month_state_counts = month_state_counts.sort_values("MONTH")

    fig_month_state = px.bar(
        month_state_counts,
        x="MONTH",
        y="Station Count",
        color="STATE",
        barmode="stack",
        title=f"Monthwise Statewise Station Count{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_month_state.update_layout(
        xaxis_title="Month",
        yaxis_title="Station Count (Trips)",
        template=chart_template,
    )

    # Monthwise freight trend
    month_freight = (
        filtered.groupby("MONTH")["FREIGHT"]
        .sum()
        .reindex([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ])
        .reset_index(name="Freight Sum")
    )
    fig_month_freight = px.line(
        month_freight,
        x="MONTH",
        y="Freight Sum",
        markers=True,
        title=f"Monthwise Freight Trend{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_month_freight.update_layout(
        xaxis_title="Month",
        yaxis_title="Freight Sum (₹)",
        template=chart_template,
    )
    fig_month_freight.update_yaxes(tickformat=".2s")

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_month_state, use_container_width=True)
    col1.caption("Shows how station count is distributed across states each month.")
    col2.plotly_chart(fig_month_freight, use_container_width=True)
    col2.caption("Highlights seasonality and overall movement of freight charges.")

    st.subheader(f"Financial Trends{chart_suffix}")
    month_finance = (
        filtered.groupby("MONTH")[["FREIGHT", "CASH ADVANCE", "NET TRANSFER"]]
        .sum()
        .reindex([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ])
        .reset_index()
        .melt(id_vars="MONTH", var_name="Type", value_name="Amount")
    )
    fig_month_finance = px.line(
        month_finance,
        x="MONTH",
        y="Amount",
        color="Type",
        markers=True,
        title=f"Monthly Freight, Advance, and Net Transfer{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_month_finance.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        template=chart_template,
    )
    fig_month_finance.update_yaxes(tickformat=".2s")

    top_transports = (
        filtered.groupby("TRANSPORT NAME")["FREIGHT"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index(name="Freight Sum")
    )
    bottom_transports = (
        filtered.groupby("TRANSPORT NAME")["FREIGHT"]
        .sum()
        .sort_values(ascending=True)
        .head(10)
        .reset_index(name="Freight Sum")
    )
    fig_top_transports = px.bar(
        top_transports,
        x="Freight Sum",
        y="TRANSPORT NAME",
        orientation="h",
        title=f"Top 10 Transports by Freight{chart_suffix}",
        color="Freight Sum",
        color_continuous_scale="Blues",
    )
    fig_top_transports.update_layout(
        xaxis_title="Freight Sum (₹)",
        yaxis_title="Transport Name",
        template=chart_template,
    )
    fig_top_transports.update_xaxes(tickformat=".2s")

    fig_bottom_transports = px.bar(
        bottom_transports,
        x="Freight Sum",
        y="TRANSPORT NAME",
        orientation="h",
        title=f"Bottom 10 Transports by Freight{chart_suffix}",
        color="Freight Sum",
        color_continuous_scale="Reds",
    )
    fig_bottom_transports.update_layout(
        xaxis_title="Freight Sum (₹)",
        yaxis_title="Transport Name",
        template=chart_template,
    )
    fig_bottom_transports.update_xaxes(tickformat=".2s")

    col7, col8 = st.columns(2)
    col7.plotly_chart(fig_month_finance, use_container_width=True)
    col7.caption("Tracks cash flow patterns across freight, advance, and net transfer.")
    col8.plotly_chart(fig_top_transports, use_container_width=True)
    col8.caption("Highlights the most active transport partners by freight value.")

    st.plotly_chart(fig_bottom_transports, use_container_width=True)
    st.caption("Highlights transport partners with the lowest freight totals.")

    st.subheader(f"Freight Mix{chart_suffix}")
    freight_by_state = (
        filtered.groupby("STATE")["FREIGHT"].sum().sort_values(ascending=False)
    )
    top_state_share = freight_by_state.head(8)
    other_share = freight_by_state.iloc[8:].sum() if len(freight_by_state) > 8 else 0
    if other_share > 0:
        top_state_share = pd.concat(
            [top_state_share, pd.Series({"Other": other_share})]
        )
    share_df = top_state_share.reset_index(name="Freight Sum").rename(columns={"index": "STATE"})
    fig_state_share = px.pie(
        share_df,
        names="STATE",
        values="Freight Sum",
        hole=0.45,
        title=f"Freight Share by State{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_state_share.update_traces(textposition="inside", textinfo="percent+label")
    fig_state_share.update_layout(template=chart_template)

    st.plotly_chart(fig_state_share, use_container_width=True)
    st.caption("Shows how total freight is distributed across states.")

    st.subheader("Filtered Data Table")
    table_columns = [
        "DATE", "MONTH", "STATION", "STATE", "TRANSPORT NAME",
        "FREIGHT", "CASH ADVANCE", "NET TRANSFER", "DRIVER",
    ]
    available_columns = [c for c in table_columns if c in filtered.columns]
    st.dataframe(
        filtered[available_columns].sort_values("DATE", ascending=False),
        use_container_width=True,
        height=420,
    )

    unknown_stations = (
        raw_data.loc[raw_data["STATE"] == "Unknown", "STATION"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
    )

    with st.expander("Unknown Stations for Mapping"):
        st.caption(f"Unknown stations: {len(unknown_stations)}")
        st.dataframe(
            pd.DataFrame({"STATION": unknown_stations}),
            use_container_width=True,
            height=320,
        )

with state_tab:
    # Statewise count of transport names
    state_transport_count = (
        filtered.groupby("STATE")["TRANSPORT NAME"]
        .nunique()
        .reset_index(name="Transport Name Count")
        .sort_values("Transport Name Count", ascending=False)
    )
    fig_state_transport = px.bar(
        state_transport_count,
        x="STATE",
        y="Transport Name Count",
        color="STATE",
        title=f"Statewise Count of Transport Names{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_state_transport.update_layout(
        xaxis_title="State",
        yaxis_title="Transport Name Count",
        template=chart_template,
    )
    fig_state_transport.update_yaxes(tickformat=".2s")

    # Statewise freight charges
    state_freight = (
        filtered.groupby("STATE")["FREIGHT"]
        .sum()
        .reset_index(name="Freight Sum")
        .sort_values("Freight Sum", ascending=False)
    )
    fig_state_freight = px.bar(
        state_freight,
        x="STATE",
        y="Freight Sum",
        color="STATE",
        title=f"Statewise Freight Charges{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_state_freight.update_layout(
        xaxis_title="State",
        yaxis_title="Freight Sum (₹)",
        template=chart_template,
    )
    fig_state_freight.update_yaxes(tickformat=".2s")

    # Statewise advance vs net transfer
    state_transfer = (
        filtered.groupby("STATE")[["CASH ADVANCE", "NET TRANSFER"]]
        .sum()
        .reset_index()
        .melt(id_vars="STATE", var_name="Type", value_name="Amount")
    )
    fig_state_transfer = px.bar(
        state_transfer,
        x="STATE",
        y="Amount",
        color="Type",
        barmode="group",
        title=f"Statewise Advance vs Net Transfer{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_state_transfer.update_layout(
        xaxis_title="State",
        yaxis_title="Amount (₹)",
        template=chart_template,
    )
    fig_state_transfer.update_yaxes(tickformat=".2s")

    col3, col4 = st.columns(2)
    col3.plotly_chart(fig_state_transport, use_container_width=True)
    col3.caption("Compares the diversity of transport vendors by state.")
    col4.plotly_chart(fig_state_freight, use_container_width=True)
    col4.caption("Ranks states by total freight charges for the selected filters.")

    st.plotly_chart(fig_state_transfer, use_container_width=True)
    st.caption("Advance and net transfer together show cash flow distribution by state.")

    st.subheader(f"State vs Month Heatmap{chart_suffix}")
    state_month_freight = filtered.pivot_table(
        index="STATE",
        columns="MONTH",
        values="FREIGHT",
        aggfunc="sum",
        fill_value=0,
    )
    state_month_freight = state_month_freight.reindex(
        columns=[
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
    )
    fig_state_month = px.imshow(
        state_month_freight,
        aspect="auto",
        color_continuous_scale="Blues",
        title=f"Freight Heatmap by State and Month{chart_suffix}",
    )
    fig_state_month.update_layout(
        xaxis_title="Month",
        yaxis_title="State",
        template=chart_template,
    )
    st.plotly_chart(fig_state_month, use_container_width=True)
    st.caption("Quickly spot seasonal peaks across states.")

    st.subheader(f"Freight Distribution by State{chart_suffix}")
    top_state_list = state_freight.head(8)["STATE"].tolist()
    freight_dist = filtered[filtered["STATE"].isin(top_state_list)]
    fig_freight_box = px.box(
        freight_dist,
        x="STATE",
        y="FREIGHT",
        color="STATE",
        title=f"Freight Distribution (Top 8 States){chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_freight_box.update_layout(
        xaxis_title="State",
        yaxis_title="Freight (₹)",
        template=chart_template,
    )
    fig_freight_box.update_yaxes(tickformat=".2s")
    st.plotly_chart(fig_freight_box, use_container_width=True)
    st.caption("Shows variability in freight amounts across leading states.")

with transport_tab:
    # Transport name - freight - statewise (top 15 transport names)
    transport_freight = (
        filtered.groupby(["TRANSPORT NAME", "STATE"]) ["FREIGHT"]
        .sum()
        .reset_index()
    )
    transport_totals = (
        transport_freight.groupby("TRANSPORT NAME")["FREIGHT"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .index
    )
    transport_freight = transport_freight[transport_freight["TRANSPORT NAME"].isin(transport_totals)]
    fig_transport_freight = px.bar(
        transport_freight,
        x="TRANSPORT NAME",
        y="FREIGHT",
        color="STATE",
        title=f"Transport Name vs Freight (Statewise){chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_transport_freight.update_layout(
        xaxis_title="Transport Name",
        yaxis_title="Freight (₹)",
        template=chart_template,
    )
    fig_transport_freight.update_yaxes(tickformat=".2s")

    # Total driver vs transport name, statewise (top 15 transport names)
    transport_driver_state = (
        filtered.groupby(["TRANSPORT NAME", "STATE"]) ["DRIVER"]
        .nunique()
        .reset_index(name="Driver Count")
    )
    transport_driver_state = transport_driver_state[transport_driver_state["TRANSPORT NAME"].isin(transport_totals)]
    fig_driver_transport = px.bar(
        transport_driver_state,
        x="TRANSPORT NAME",
        y="Driver Count",
        color="STATE",
        title=f"Total Drivers vs Transport Name (Statewise){chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_driver_transport.update_layout(
        xaxis_title="Transport Name",
        yaxis_title="Driver Count",
        template=chart_template,
    )
    fig_driver_transport.update_yaxes(tickformat=".2s")

    # Top stations by count
    top_stations = (
        filtered.groupby(["STATION", "STATE"]) ["STATION"]
        .count()
        .reset_index(name="Trips")
        .sort_values("Trips", ascending=False)
        .head(15)
    )
    fig_top_stations = px.bar(
        top_stations,
        x="STATION",
        y="Trips",
        color="STATE",
        title=f"Top Stations by Trip Count{chart_suffix}",
        color_discrete_sequence=palette_light,
    )
    fig_top_stations.update_layout(
        xaxis_title="Station",
        yaxis_title="Trips (Count)",
        template=chart_template,
    )

    col5, col6 = st.columns(2)
    col5.plotly_chart(fig_transport_freight, use_container_width=True)
    col5.caption("Top transport names by freight, split by state.")
    col6.plotly_chart(fig_driver_transport, use_container_width=True)
    col6.caption("Driver count indicates manpower per transport vendor.")

    st.plotly_chart(fig_top_stations, use_container_width=True)
    st.caption("Shows the busiest stations under the current filters.")

    st.subheader(f"Transport Performance Map{chart_suffix}")
    transport_summary = (
        filtered.groupby("TRANSPORT NAME")
        .agg(
            Freight_Sum=("FREIGHT", "sum"),
            Net_Transfer_Sum=("NET TRANSFER", "sum"),
            Trips=("STATION", "count"),
        )
        .reset_index()
    )
    transport_summary = transport_summary.sort_values("Freight_Sum", ascending=False).head(25)
    fig_transport_bubble = px.scatter(
        transport_summary,
        x="Freight_Sum",
        y="Net_Transfer_Sum",
        size="Trips",
        color="Freight_Sum",
        hover_name="TRANSPORT NAME",
        title=f"Freight vs Net Transfer (Top 25 Transports){chart_suffix}",
        color_continuous_scale="Teal",
    )
    fig_transport_bubble.update_layout(
        xaxis_title="Freight Sum (₹)",
        yaxis_title="Net Transfer Sum (₹)",
        template=chart_template,
    )
    fig_transport_bubble.update_xaxes(tickformat=".2s")
    fig_transport_bubble.update_yaxes(tickformat=".2s")
    st.plotly_chart(fig_transport_bubble, use_container_width=True)
    st.caption("Bubble size reflects trip volume; color intensity reflects freight value.")

st.caption("Tip: refine the city-state mapping in app.py if you need more precise state detection.")
