import csv
import io
import streamlit as st

st.set_page_config(page_title="DS Credit Calculator")

st.title("DS Credit Calculator")

st.write(
    "Upload the three CSV files, choose the target week, then download the results."
)

requests_file = st.file_uploader(
    "DS_requests.csv",
    type="csv",
    key="requests",
)

registrations_file = st.file_uploader(
    "DS_registrations.csv",
    type="csv",
    key="registrations",
)

noshows_file = st.file_uploader(
    "DS_noshows.csv",
    type="csv",
    key="noshows",
)

if requests_file and registrations_file and noshows_file:

    # -----------------------------
    # Read CSVs
    # -----------------------------
    requests = list(
        csv.DictReader(
            io.StringIO(requests_file.getvalue().decode("utf-8-sig"))
        )
    )

    reg_rows = list(
        csv.DictReader(
            io.StringIO(registrations_file.getvalue().decode("utf-8-sig"))
        )
    )

    noshow_rows = list(
        csv.DictReader(
            io.StringIO(noshows_file.getvalue().decode("utf-8-sig"))
        )
    )

    if not requests:
        st.error("DS_requests.csv is empty.")
        st.stop()

    week_columns = [
        c for c in requests[0].keys()
        if c != "player"
    ]

    week = st.selectbox(
        "Select week",
        week_columns,
        index=len(week_columns) - 1,
    )

    # -----------------------------
    # Validate columns
    # -----------------------------
    for name, rows in [
        ("Registrations", reg_rows),
        ("No Shows", noshow_rows),
    ]:
        if not rows:
            st.error(f"{name} file is empty.")
            st.stop()

        missing = [
            c for c in week_columns
            if c not in rows[0]
        ]

        if missing:
            st.error(
                f"{name} CSV is missing columns: {missing}"
            )
            st.stop()

    registered = {
        row["player"]: row
        for row in reg_rows
    }

    noshows = {
        row["player"]: row
        for row in noshow_rows
    }

    reg_weeks = [
        c for c in reg_rows[0].keys()
        if c != "player"
    ]

    # -----------------------------
    # Eligible players
    # -----------------------------
    eligible = {
        row["player"]
        for row in requests
        if row.get(week, "").strip().startswith("*")
    }

    st.success(f"{len(eligible)} eligible players found.")

    # -----------------------------
    # Calculate credits
    # -----------------------------
    credits = {}

    for row in requests:

        player = row["player"]
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

    # -----------------------------
    # Sub percentage
    # -----------------------------
    def has_been_sub_pct(player):

        weeks_to_check = [
            w for w in reg_weeks
            if w != week
        ]

        if not weeks_to_check:
            return "0.0%"

        player_reg = registered.get(player, {})

        double_star_count = sum(
            1
            for w in weeks_to_check
            if player_reg.get(w, "").strip().startswith("**")
        )

        pct = (
            double_star_count
            / len(weeks_to_check)
        ) * 100

        return f"{pct:.1f}%"

    # -----------------------------
    # Create output
    # -----------------------------
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

    st.write(f"Rows written: **{rows_written}**")

    if rows_written == 0:
        st.warning(
            "No players matched the selected week. Check that the uploaded CSVs contain the expected data."
        )
    else:
        st.dataframe(preview, use_container_width=True)

        st.download_button(
            "📥 Download CSV",
            output.getvalue(),
            file_name=f"DS_{week.replace(' ', '-')}.csv",
            mime="text/csv",
        )
