import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and select your target date to generate the report.")

# 1. Single User Input for the Target Column
target_date = st.text_input("Target Date Column (Checks eligibility & gets skipped in loops):", value="July 10")

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

# Run if everything is filled out
if req_file and reg_file and ns_file and target_date:
    
    if st.button("Process Data", type="primary"):
        clean_target_date = target_date.strip()
        
        # Read from memory with UTF-8-SIG to avoid Excel encoding artifacts
        req_text = io.StringIO(req_file.getvalue().decode("utf-8-sig"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8-sig"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8-sig"))

        credits = {}

        requests = list(csv.DictReader(req_text))
        reg_rows = list(csv.DictReader(reg_text))
        
        # Guard clause: verify structural match
        if requests:
            headers = list(requests.keys())
            if clean_target_date not in headers:
                st.error(f"❌ '{clean_target_date}' not found in requests file headers: {headers}")
                st.stop()

        registered = {row["player"]: row for row in reg_rows}
        noshows = {row["player"]: row for row in csv.DictReader(ns_text)}
        reg_weeks = [col for col in reg_rows.keys() if col != "player"] if reg_rows else []

        # Find eligible players matching the specific target column (e.g., July 10)
        eligible = {
            row["player"]
            for row in requests
            if row[clean_target_date].startswith("*")
        }

        # Calculate credits while ignoring player and the target column
        for row in requests:
            player = row["player"]
            credits[player] = 0

            for week in row:
                # Dynamically ignores 'player' and whatever date was input (e.g., 'July 10')
                if week in ("player", clean_target_date):
                    continue

                requested = row[week].startswith("*")
                was_registered = registered.get(player, {}).get(week, "").startswith("*")
                was_noshow = noshows.get(player, {}).get(week, "").startswith("*")

                if requested and not was_registered:
                    credits[player] += 1

                if was_registered and was_noshow:
                    credits[player] -= 1

        # Build output buffer
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(["player", "credits", "hasBeenSub"])
        
        written_rows_count = 0
        # Tracks the index [1] (the credit score) to properly sort highest to lowest
        for player, score in sorted(credits.items(), key=lambda x: x, reverse=True):
            if player in eligible:
                writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks, clean_target_date)])
                written_rows_count += 1

        if written_rows_count == 0:
            st.warning(f"⚠️ Successfully calculated credits, but 0 players had a '*' in the '{clean_target_date}' column.")
        else:
            st.success(f"🎉 Success! Processed {written_rows_count} eligible players from the '{clean_target_date}' column.")

        safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"

        st.download_button(
            label=f"⬇️ Download {safe_filename}",
            data=output_buffer.getvalue(),
            file_name=safe_filename,
            mime="text/csv"
        )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
