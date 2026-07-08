import csv
import io
import streamlit as st

st.set_page_config(page_title="DS Credit Calculator")

st.title("DS Credit Calculator")


def read_csv(uploaded_file):
    """Read a CSV uploaded to Streamlit, automatically detecting the delimiter."""
    text = uploaded_file.getvalue().decode("utf-8-sig")

    try:
        dialect = csv.Sniffer().sniff(text[:5000], delimiters=",;\t")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    rows = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))

    return rows, delimiter


requests_file = st.file_uploader(
    "Upload DS_requests.csv",
    type="csv",
)

registrations_file = st.file_uploader(
    "Upload DS_registrations.csv",
    type="csv",
)

noshows_file = st.file_uploader(
    "Upload DS_noshows.csv",
    type="csv",
)

if requests_file and registrations_file and noshows_file:

    requests, req_delim = read_csv(requests_file)
    reg_rows, reg_delim = read_csv(registrations_file)
    noshow_rows, ns_delim = read_csv(noshows_file)

    if not requests:
        st.error("DS_requests.csv appears to be empty.")
        st.stop()

    st.write("Detected delimiters:")
    st.write(
        {
            "Requests": req_delim,
            "Registrations": reg_delim,
            "No Shows": ns_delim,
        }
    )

    st.write("First row of requests:")
    st.write(requests[0])

    week_columns = [
        c.strip()
        for c in requests[0].keys()
        if c.strip().lower() != "player"
    ]

    week = st.selectbox(
        "Week",
        week_columns,
        index=len(week_columns) - 1,
    )

    registered = {
        row["player"].strip(): row
        for row in reg_rows
    }

    noshows = {
        row["player"].strip(): row
        for row in noshow_rows
    }

    reg_weeks = [
        c.strip()
        for c in reg_rows[0].keys()
        if c.strip().lower() != "player"
    ]

    credits = {}

    eligible = set()

    for row in requests:
        player = row["player"].strip()

        if row.get(week, "").strip().startswith("*"):
            eligible.add(player)

    st.write(f"Eligible players: {len(eligible)}")

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

        reg = registered.get(player, {})

        subs = sum(
            1
            for w in weeks
            if reg.get(w, "").strip().startswith("**")
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
    rows_written = 0

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

        rows_written += 1

    st.write(f"Rows written: {rows_written}")

    if preview:
        st.dataframe(preview, use_container_width=True)

    st.download_button(
        "Download CSV",
        output.getvalue(),
        file_name=f"DS_{week.replace(' ', '-')}.csv",
        mime="text/csv",
    )
