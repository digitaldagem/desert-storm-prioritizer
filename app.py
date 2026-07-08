import csv
import io
import streamlit as st

st.title("DS Credits Calculator")

st.write("Upload the three CSV files and select the target week.")

target_week = st.text_input("Week column", value="July 10")

requests_file = st.file_uploader(
    "Upload DS_requests.csv",
    type="csv"
)

registrations_file = st.file_uploader(
    "Upload DS_registrations.csv",
    type="csv"
)

noshows_file = st.file_uploader(
    "Upload DS_noshows.csv",
    type="csv"
)


def has_been_sub_pct(player, registered, reg_weeks, target_week):
    """Percentage of weeks where the player has '**' in registrations."""
    weeks_to_check = [w for w in reg_weeks if w != target_week]

    if not weeks_to_check:
        return "0.0%"

    player_reg = registered.get(player, {})

    double_star_count = sum(
        1
        for week in weeks_to_check
        if player_reg.get(week, "").startswith("**")
    )

    pct = (double_star_count / len(weeks_to_check)) * 100
    return f"{pct:.1f}%"


if (
    requests_file is not None
    and registrations_file is not None
    and noshows_file is not None
):

    requests = list(
        csv.DictReader(io.StringIO(requests_file.getvalue().decode("utf-8")))
    )

    reg_rows = list(
        csv.DictReader(io.StringIO(registrations_file.getvalue().decode("utf-8")))
    )

    noshow_rows = list(
        csv.DictReader(io.StringIO(noshows_file.getvalue().decode("utf-8")))
    )

    registered = {row["player"]: row for row in reg_rows}
    noshows = {row["player"]: row for row in noshow_rows}

    reg_weeks = [
        col
        for col in reg_rows[0].keys()
        if col != "player"
    ] if reg_rows else []

    if target_week not in requests[0]:
        st.error(f'"{target_week}" is not a column in DS_requests.csv')
        st.stop()

    credits = {}

    eligible = {
        row["player"]
        for row in requests
        if row[target_week].startswith("*")
    }

    for row in requests:

        player = row["player"]
        credits[player] = 0

        for week in row:

            if week in ("player", target_week):
                continue

            requested = row[week].startswith("*")

            was_registered = (
                registered.get(player, {})
                .get(week, "")
                .startswith("*")
            )

            was_noshow = (
                noshows.get(player, {})
                .get(week, "")
                .startswith("*")
            )

            if requested and not was_registered:
                credits[player] += 1

            if was_registered and was_noshow:
                credits[player] -= 1

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["player", "credits", "hasBeenSub"])

    for player, score in sorted(
        credits.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        if player in eligible:
            writer.writerow(
                [
                    player,
                    score,
                    has_been_sub_pct(
                        player,
                        registered,
                        reg_weeks,
                        target_week,
                    ),
                ]
            )

    st.success("Done!")

    st.download_button(
        label="Download Results CSV",
        data=output.getvalue(),
        file_name=f"DS_{target_week.replace(' ', '-')}.csv",
        mime="text/csv",
    )
