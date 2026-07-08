import csv
import io
import streamlit as st

st.title("DS Credit Calculator")

st.write("Upload the three CSV files and select the week.")

week = st.text_input("Week column", value="July 10")

requests_file = st.file_uploader(
    "DS_requests.csv",
    type="csv",
    key="requests"
)

registrations_file = st.file_uploader(
    "DS_registrations.csv",
    type="csv",
    key="registrations"
)

noshows_file = st.file_uploader(
    "DS_noshows.csv",
    type="csv",
    key="noshows"
)

if requests_file and registrations_file and noshows_file:

    requests = list(csv.DictReader(io.StringIO(requests_file.getvalue().decode("utf-8"))))
    reg_rows = list(csv.DictReader(io.StringIO(registrations_file.getvalue().decode("utf-8"))))
    noshow_rows = list(csv.DictReader(io.StringIO(noshows_file.getvalue().decode("utf-8"))))

    registered = {row["player"]: row for row in reg_rows}
    noshows = {row["player"]: row for row in noshow_rows}

    credits = {}

    reg_weeks = [
        col for col in reg_rows[0].keys()
        if col != "player"
    ] if reg_rows else []

    if week not in requests[0]:
        st.error(f"'{week}' is not a column in DS_requests.csv")
        st.stop()

    eligible = {
        row["player"]
        for row in requests
        if row.get(week, "").startswith("*")
    }

    for row in requests:

        player = row["player"]
        credits[player] = 0

        for current_week in row:

            if current_week in ("player", week):
                continue

            requested = row[current_week].startswith("*")
            was_registered = (
                registered.get(player, {}).get(current_week, "").startswith("*")
            )
            was_noshow = (
                noshows.get(player, {}).get(current_week, "").startswith("*")
            )

            if requested and not was_registered:
                credits[player] += 1

            if was_registered and was_noshow:
                credits[player] -= 1

    def has_been_sub_pct(player):
        weeks_to_check = [w for w in reg_weeks if w != week]

        if not weeks_to_check:
            return "0.0%"

        player_reg = registered.get(player, {})

        double_star_count = sum(
            1
            for w in weeks_to_check
            if player_reg.get(w, "").startswith("**")
        )

        pct = (double_star_count / len(weeks_to_check)) * 100
        return f"{pct:.1f}%"

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["player", "credits", "hasBeenSub"])

    for player, score in sorted(
        credits.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        if player in eligible:
            writer.writerow([
                player,
                score,
                has_been_sub_pct(player)
            ])

    st.success("Calculation complete!")

    st.download_button(
        label="Download Results CSV",
        data=output.getvalue(),
        file_name=f"DS_{week.replace(' ', '-')}.csv",
        mime="text/csv",
    )
