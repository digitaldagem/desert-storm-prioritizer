import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and click 'Process Data' to generate your report.")

# 1. User Input for the Target Column
target_date = st.text_input("Target Date Column:", value="July 10")

# 2. File Uploaders
req_file = st.file_uploader("Upload DS_requests.csv", type=["csv"])
reg_file = st.file_uploader("Upload DS_registrations.csv", type=["csv"])
ns_file = st.file_uploader("Upload DS_noshows.csv", type=["csv"])

def has_been_sub_pct(player, registered, reg_weeks, date_to_skip):
    """Percentage of weeks where the player has '**' in DS_registrations.csv."""
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

# 3. Only show the processing button if all files are uploaded
if req_file and reg_file and ns_file and target_date:
    
    # Restored the primary process button
    if st.button("Process Data", type="primary"):
        clean_target_date = target_date.strip()
        
        # Read from memory with utf-8-sig to clear hidden Excel symbols
        req_text = io.StringIO(req_file.getvalue().decode("utf-8-sig"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8-sig"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8-sig"))

        # --- DATA HARDENING: Strip spaces from all keys/values inside the CSV data ---
        raw_requests = list(csv.DictReader(req_text))
        raw_reg_rows = list(csv.DictReader(reg_text))
        raw_noshows_rows = list(csv.DictReader(ns_text))
        
        # Normalize headers and spaces to prevent "0 matches found" errors
        requests = [{k.strip(): v.strip() if v else "" for k, v in row.items()} for row in raw_requests]
        reg_rows = [{k.strip(): v.strip() if v else "" for k, v in row.items()} for row in raw_reg_rows]
        noshows_list = [{k.strip(): v.strip() if v else "" for k, v in row.items()} for row in raw_noshows_rows]
        # -----------------------------------------------------------------------------

        credits = {}

        # Guard clause: verify structural match safely
        if requests:
            headers = list(requests[0].keys())
            if clean_target_date not in headers:
                st.error(f"❌ '{clean_target_date}' not found in requests headers. Found columns: {headers}")
                st.stop()

        # Build structural dictionaries using your exact matching keys
        registered = {row["player"]: row for row in reg_rows if "player" in row}
        noshows = {row["player"]: row for row in noshows_list if "player" in row}
        
        # Pull registration weeks matrix safely using first index element
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Find eligible players matching the dynamic date column
        eligible = {
            row["player"]
            for row in requests
            if "player" in row and row.get(clean_target_date, "").startswith("*")
        }

        # Calculate player credit structures
        for row in requests:
            if "player" not in row:
                continue
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

        # Write calculations into data buffer
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(["player", "credits", "hasBeenSub"])
        
        written_rows_count = 0
        # Strict matching of your original lambda tuple index sorting logic
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks, clean_target_date)])
                written_rows_count += 1

        # Render explicit state results to the browser window
        if written_rows_count == 0:
            st.warning(f"⚠️ Successfully calculated credits, but 0 players had a '*' in the '{clean_target_date}' column.")
            st.write("**Debugging Info:** Check if your players actually have an asterisk under that column header in the uploaded file.")
        else:
            st.success(f"🎉 Success! Processed {written_rows_count} eligible players from the '{clean_target_date}' column.")
            
            # Save the layout variables directly inside Streamlit's session memory 
            # so clicking download does not clear the page state!
            st.session_state['csv_output'] = output_buffer.getvalue()
            st.session_state['filename'] = f"DS_{clean_target_date.replace(' ', '-')}.csv"

    # 4. If data has been processed, render the download button safely outside the processing script execution loop
    if 'csv_output' in st.session_state:
        st.download_button(
            label=f"⬇️ Download {st.session_state['filename']}",
            data=st.session_state['csv_output'],
            file_name=st.session_state['filename'],
            mime="text/csv"
        )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
