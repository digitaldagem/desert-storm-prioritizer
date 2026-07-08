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
        
        # Stream text exactly how open() handles local files
        req_text = io.StringIO(req_file.getvalue().decode("utf-8-sig"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8-sig"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8-sig"))

        credits = {}

        # Parse data files into lists
        requests = list(csv.DictReader(req_text))
        reg_rows = list(csv.DictReader(reg_text))
        registered = {row["player"]: row for row in reg_rows}
        noshows = {row["player"]: row for row in csv.DictReader(ns_text)}

        # FIXED SYNTAX: Restored your exact bracket lookup to access row dictionaries
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Find eligible players matching the dynamic target column selection
        eligible = {
            row["player"]
            for row in requests
            if row.get(clean_target_date, "").startswith("*")
        }

        # Calculate credits matching your exact desktop loop logic
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

        # Build output matrix list
        output_rows = []
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                output_rows.append([player, score, has_been_sub_pct(player, registered, reg_weeks)])

        # Display outcome status or preview to the web screen
        if not output_rows:
            st.warning(f"⚠️ 0 players had a '*' in the '{clean_target_date}' column.")
            # Quick troubleshooting debug log visible only if it misfires
            if requests:
                st.write("**Debug Info - First row columns:**", list(requests[0].keys()))
                st.write("**Debug Info - First row values:**", requests[0])
        else:
            st.success(f"🎉 Success! Found {len(output_rows)} eligible players.")
            
            # Show interactive data preview table right on the browser screen
            st.subheader("👀 Generated Data Preview")
            st.table([{"Player": r[0], "Credits": r[1], "hasBeenSub": r[2]} for r in output_rows[:20]])

            # Create final downloadable file stream string
            output_buffer = io.StringIO()
            writer = csv.writer(output_buffer)
            writer.writerow(["player", "credits", "hasBeenSub"])
            writer.writerows(output_rows)

            safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"

            # Render Download button safely outside internal loops
            st.download_button(
                label=f"⬇️ Download {safe_filename}",
                data=output_buffer.getvalue(),
                file_name=safe_filename,
                mime="text/csv"
            )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
