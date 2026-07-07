import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and select your target date to generate the report.")

# 1. New User Input for the Date Column
target_date = st.text_input("Target Date Column Name:", value="July 3")

# 2. File Uploaders
req_file = st.file_uploader("Upload DS_requests.csv", type=["csv"])
reg_file = st.file_uploader("Upload DS_registrations.csv", type=["csv"])
ns_file = st.file_uploader("Upload DS_noshows.csv", type=["csv"])

def has_been_sub_pct(player, registered, reg_weeks, date_to_skip):
    # Uses the dynamic target_date to skip instead of a hardcoded "July 3"
    weeks_to_check = [w for w in reg_weeks if w != date_to_skip]
    if not weeks_to_check:
        return "0.0%"
    player_reg = registered.get(player, {})
    double_star_count = sum(
        1 for week in weeks_to_check
        if player_reg.get(week, "").startswith("**")
    )
    pct = (double_star_count / len(weeks_to_check)) * 100
    return f"{pct:.1f}%"

# Only run if all three files are uploaded and the date isn't empty
if req_file and reg_file and ns_file and target_date:
    
    if st.button("Process Data", type="primary"):
        
        # Read the uploaded files from memory
        req_text = io.StringIO(req_file.getvalue().decode("utf-8"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8"))

        credits = {}

        requests = list(csv.DictReader(req_text))
        reg_rows = list(csv.DictReader(reg_text))
        
        # Guard clause: check if the user-inputted date actually exists in the uploaded file
        if requests and target_date not in requests[0].keys():
            st.error(f"Error: The column '{target_date}' was not found in DS_requests.csv. Please check your spelling.")
            st.stop()

        registered = {row["player"]: row for row in reg_rows}
        noshows = {row["player"]: row for row in csv.DictReader(ns_text)}

        reg_weeks = [col for col in reg_rows.keys() if col != "player"] if reg_rows else []

        # Players with '*' in the user-specified date column
        eligible = {
            row["player"]
            for row in requests
            if row[target_date].startswith("*")
        }

        for row in requests:
            player = row["player"]
            credits[player] = 0

            for week in row:
                # Dynamic check for the input target_date
                if week in ("player", target_date):
                    continue

                requested = row[week].startswith("*")
                was_registered = registered.get(player, {}).get(week, "").startswith("*")
                was_noshow = noshows.get(player, {}).get(week, "").startswith("*")

                if requested and not was_registered:
                    credits[player] += 1

                if was_registered and was_noshow:
                    credits[player] -= 1

        # Write output to memory buffer
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(["player", "credits", "hasBeenSub"])
        
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks, target_date)])

        # Clean up file name formatting (replace spaces with hyphens for clean downloading)
        safe_filename = f"DS_{target_date.replace(' ', '-')}.csv"

        # 3. Provide the Download Button with dynamic name
        st.success("Processing complete!")
        st.download_button(
            label=f"⬇️ Download {safe_filename}",
            data=output_buffer.getvalue(),
            file_name=safe_filename,
            mime="text/csv"
        )
else:
    if not target_date:
        st.warning("Please enter a target date column name.")
    else:
        st.info("Please upload all three CSV files to begin.")
