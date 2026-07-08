import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and select your target date to generate the report.")

# 1. User Input for the Target Column
target_date = st.text_input("Target Date Column:", value="July 10")

# 2. File Uploaders
req_file = st.file_uploader("Upload DS_requests.csv", type=["csv"])
reg_file = st.file_uploader("Upload DS_registrations.csv", type=["csv"])
ns_file = st.file_uploader("Upload DS_noshows.csv", type=["csv"])

def has_been_sub_pct(player, registered, reg_weeks):
    """Percentage of weeks where the player has '**' in DS_registrations.csv."""
    weeks_to_check = [w for w in reg_weeks if w != "July 10"]
    if not weeks_to_check:
        return "0.0%"
    player_reg = registered.get(player, {})
    double_star_count = sum(
        1 for week in weeks_to_check
        if player_reg.get(week, "").startswith("**")
    )
    pct = (double_star_count / len(weeks_to_check)) * 100
    return f"{pct:.1f}%"

# 3. Process Data
if req_file and reg_file and ns_file and target_date:
    
    if st.button("Process Data", type="primary"):
        clean_target_date = target_date.strip()
        
        # Split lines cleanly to clear raw OS carriage returns (\r, \n)
        req_lines = req_file.getvalue().decode("utf-8-sig").splitlines()
        reg_lines = reg_file.getvalue().decode("utf-8-sig").splitlines()
        ns_lines = ns_file.getvalue().decode("utf-8-sig").splitlines()

        credits = {}

        # ORIGINAL FILE READING MAPPING
        requests = list(csv.DictReader(req_lines))
        reg_rows = list(csv.DictReader(reg_lines))
        registered = {row["player"]: row for row in reg_rows if "player" in row}
        noshows = {row["player"]: row for row in csv.DictReader(ns_lines) if "player" in row}

        # Get week columns from registrations (excluding 'player')
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Players with '*' in the user-specified column
        eligible = {
            row["player"]
            for row in requests
            if row.get(clean_target_date, "").startswith("*")
        }

        for row in requests:
            player = row["player"]
            credits[player] = 0

            for week in row:
                if week in ("player", clean_target_date):
                    continue

                requested = row[week].startswith("*")
                was_registered = (
                    registered.get(player, {}).get(week, "").startswith("*")
                )
                was_noshow = (
                    noshows.get(player, {}).get(week, "").startswith("*")
                )

                if requested and not was_registered:
                    credits[player] += 1

                if was_registered and was_noshow:
                    credits[player] -= 1

        # WRITE TO IN-MEMORY STRING INSTEAD OF LOCAL HARD DRIVE
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(["player", "credits", "hasBeenSub"])
        
        written_count = 0
        # FIXED: Enforced strict index 1 integer target matching for python 3 tuple sorting
        for player, score in sorted(
            credits.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if player in eligible:
                writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks)])
                written_count += 1

        if written_count == 0:
            st.warning(f"⚠️ 0 rows generated. Check if column headers match exactly.")
        else:
            st.success(f"🎉 Success! Found {written_count} eligible players matching '{clean_target_date}'.")
            
            safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"
            st.download_button(
                label=f"⬇️ Download {safe_filename}",
                data=output_buffer.getvalue(),
                file_name=safe_filename,
                mime="text/csv"
            )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
