import csv
import io
import streamlit as st

st.title("Player Credits & Eligibility Processor")
st.write("Upload your CSV files and select your target date to generate the report.")

# 1. User Input for the Target Column
target_date = st.text_input("Target Date Column (Checks eligibility & gets skipped in loops):", value="July 10")

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

def process_data(req_bytes, reg_bytes, ns_bytes, clean_target_date):
    # Decode bytes securely using utf-8-sig to clear Excel artifacts
    req_text = io.StringIO(req_bytes.decode("utf-8-sig"))
    reg_text = io.StringIO(reg_bytes.decode("utf-8-sig"))
    ns_text = io.StringIO(ns_bytes.decode("utf-8-sig"))

    requests = list(csv.DictReader(req_text))
    reg_rows = list(csv.DictReader(reg_text))
    
    # Guard clause: verify structural match safely
    if requests:
        headers = list(requests[0].keys())
        if clean_target_date not in headers:
            st.error(f"❌ '{clean_target_date}' not found in requests file headers: {headers}")
            return None

    registered = {row["player"]: row for row in reg_rows}
    noshows = {row["player"]: row for row in csv.DictReader(ns_text)}
    
    # Grab columns safely using index 0 on the list
    reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

    # Find eligible players matching the user input column
    eligible = {
        row["player"]
        for row in requests
        if row.get(clean_target_date, "").startswith("*")
    }

    credits = {}
    # Calculate credits while ignoring player and the target column
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

    # Build output buffer string
    output_buffer = io.StringIO()
    writer = csv.writer(output_buffer)
    writer.writerow(["player", "credits", "hasBeenSub"])
    
    written_rows_count = 0
    # Strict matching of original lambda sorting key
    for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
        if player in eligible:
            writer.writerow([player, score, has_been_sub_pct(player, registered, reg_weeks, clean_target_date)])
            written_rows_count += 1

    return output_buffer.getvalue(), written_rows_count

# Main application step
if req_file and reg_file and ns_file and target_date:
    
    clean_target_date = target_date.strip()
    
    # Run data logic instantly inside the main layout block
    result = process_data(req_file.getvalue(), reg_file.getvalue(), ns_file.getvalue(), clean_target_date)
    
    if result:
        csv_data, written_rows_count = result
        
        if written_rows_count == 0:
            st.warning(f"⚠️ Processed data successfully, but 0 players had an asterisk in the '{clean_target_date}' column.")
        else:
            st.success(f"🎉 Success! Processed {written_rows_count} eligible players from the '{clean_target_date}' column.")

        safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"

        st.download_button(
            label=f"⬇️ Download {safe_filename}",
            data=csv_data,
            file_name=safe_filename,
            mime="text/csv"
        )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
