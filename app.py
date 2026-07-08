import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and select your target date to generate the report.")

# 1. User Input for the Date Column
target_date = st.text_input("Target Date Column Name:", value="July 3")

# 2. File Uploaders
req_file = st.file_uploader("Upload DS_requests.csv", type=["csv"])
reg_file = st.file_uploader("Upload DS_registrations.csv", type=["csv"])
ns_file = st.file_uploader("Upload DS_noshows.csv", type=["csv"])

def has_been_sub_pct(player, registered, reg_weeks, date_to_skip):
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
        
        # Clean up user input string (remove accidental leading/trailing spaces)
        clean_target_date = target_date.strip()
        
        # Read the uploaded files from memory using "utf-8-sig" to strip Excel BOM symbols
        req_text = io.StringIO(req_file.getvalue().decode("utf-8-sig"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8-sig"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8-sig"))

        credits = {}

        requests = list(csv.DictReader(req_text))
        reg_rows = list(csv.DictReader(reg_text))
        
        # Guard clause: Verify column header match case-sensitively
        if requests and clean_target_date not in requests[0].keys():
            st.error(f"❌ Error: Column '{clean_target_date}' not found in DS_requests.csv.")
            st.write("Available columns found:", list(requests[0].keys()))
            st.stop()

        registered = {row["player"]: row for row in reg_rows}
        noshows = {row["player"]: row for row in csv.DictReader(ns_text)}

        # FIXED line: Targets the first item of the list of dictionaries safely
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Find eligible players matching the dynamic date column
        eligible = {
            row["player"]
            for row in requests
            if row[clean_target_date].startswith("*")
        }

        # Calculate credits
        for row in requests:
            player = row["player"]
            credits[player] = 0

            for week in row:
                if week in ("player", clean_target_date):
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
        
        # FIXED: restored sorting key index to `x[1]` to correctly pull the score
        written_rows_count = 0
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks, clean_target_date)])
                written_rows_count += 1

        if written_rows_count == 0:
            st.warning("⚠️ The data processed successfully, but 0 eligible players were found matching those conditions.")
        else:
            st.success(f"🎉 Processing complete! Found {written_rows_count} eligible players.")

        # Clean up file name formatting
        safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"

        # Provide the Download Button
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
