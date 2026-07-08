import csv
import io
import streamlit as st

st.set_page_config(page_title="DS Credit Calculator", page_icon="⚽")

st.title("⚽ DS Credit Calculator")

st.write(
    """
Upload these three files (in any order):

- **DS_requests.csv**
- **DS_registrations.csv**
- **DS_noshows.csv**
"""
)


def read_csv(uploaded_file):
    """Read an uploaded CSV, automatically detecting delimiter."""
    text = uploaded_file.getvalue().decode("utf-8-sig")

    try:
        dialect = csv.Sniffer().sniff(text[:5000], delimiters=",;\t")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))


# -----------------------
# Upload files
# -----------------------

uploaded_files = st.file_uploader(
    "Upload the three CSV files",
    type="csv",
    accept_multiple_files=True,
)

if not uploaded_files:
    st.stop()

files = {f.name: f for f in uploaded_files}

required = [
    "DS_requests.csv",
    "DS_registrations.csv",
    "DS_noshows.csv",
]

missing = [f for f in required if f not in files]

if missing:
    st.warning(
        "Still waiting for:\n\n" +
        "\n".join(f"- {m}" for m in missing)
    )
    st.stop()

st.success("All required files uploaded.")

requests = read_csv(files["DS_requests.csv"])
reg_rows = read_csv(files["DS_registrations.csv"])
noshow_rows = read_csv(files["DS_noshows.csv"])

if not requests:
    st.error("DS_requests.csv is empty.")
    st.stop()

registered = {
    row["player"].strip(): row
    for row in reg_rows
}

noshows = {
    row["player"].strip(): row
    for row in noshow_rows
}

week_columns = [
    c.strip()
    for c in requests[0].keys()
    if c.strip() != "player"
]

week = st.selectbox(
    "Select the week",
    week_columns,
    index=len(week_columns) - 1,
)

credits = {}

eligible = {
    row["player"].strip()
    for row in requests
    if row.get(week, "").strip().startswith("*")
}

st.info(f"{len(eligible)} eligible players")

reg_weeks = [
    c.strip()
    for c in reg_rows[0].keys()
    if c.strip() != "player"
]

for row in requests:

    player = row["player"].strip()
    credits[player] = 0

    for current_week in week_columns:

        if current_week == week:
            continue

        requested = row.get(current_week, "").strip().startswith("*")

        was_registered = (
            registered.get(player, {})
            .get(current_week, "")
            .strip()
            .startswith("*")
        )

        was_noshow = (
            noshows.get(player, {})
            .get(current_week, "")
            .strip()
            .startswith("*")
        )

        if requested and not was_registered:
            credits[player] += 1

        if was_registered and was_noshow:
            credits[player] -= 1


def has_been_sub_pct(player):

    weeks = [
        w
        for w in reg_weeks
        if w != week
    ]

    if not weeks:
        return "0.0%"

    player_reg = registered.get(player, {})

    subs = sum(
        1
        for w in weeks
        if player_reg.get(w, "").strip().startswith("**")
    )

    return f"{100 * subs / len(weeks):.1f}%"


output = io.StringIO()
writer = csv.writer(output)

writer.writerow(
    [
        "player",
        "credits",
        "hasBeenSub",
    ]
)

preview = []

for player, score in sorted(
    credits.items(),
    key=lambda x: x[1],
    reverse=True,
):

    if player not in eligible:
        continue

    pct = has_been_sub_pct(player)

    writer.writerow(
        [
            player,
            score,
            pct,
        ]
    )

    preview.append(
        {
            "player": player,
            "credits": score,
            "hasBeenSub": pct,
        }
    )

st.success(f"Generated {len(preview)} rows.")

if preview:
    st.dataframe(preview, use_container_width=True)

    st.download_button(
        "📥 Download Results CSV",
        output.getvalue(),
        file_name=f"DS_{week.replace(' ', '-')}.csv",
        mime="text/csv",
    )
else:
    st.warning("No eligible players were found for the selected week.")
