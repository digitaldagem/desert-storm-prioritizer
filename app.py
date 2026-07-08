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

def has_been_sub_pct(player, registered, reg_weeks, date_to_skip):
    """Percentage of weeks where the player has '**' in DS_registrations.csv."""
    weeks_to_check = [w for w in reg_weeks if w != date_to_skip]
    if not weeks_to_check:
        return "0.0%"
    player_reg = registered.get(player, {})
    double_star_count = sum(
        1 for week in weeks_to_check
        if str(player_reg.get(week, "")).startswith("**")
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

        # Parse CSV records into memory dict lists
        raw_requests = list(csv.DictReader(req_lines))
        raw_reg_rows = list(csv.DictReader(reg_lines))
        raw_ns_rows = list(csv.DictReader(ns_lines))

        # --- DATA CLEANING BANNER: Strip hidden spaces from ALL columns and values ---
        requests = []
        for row in raw_requests:
            requests.append({k.strip(): v.strip() if v else "" for k, v in row.items() if k is not None})
            
        reg_rows = []
        for row in raw_reg_rows:
            reg_rows.append({k.strip(): v.strip() if v else "" for k, v in row.items() if k is not None})
            
        ns_rows = []
        for row in raw_ns_rows:
            ns_rows.append({k.strip(): v.strip() if v else "" for k, v in row.items() if k is not None})
        # -----------------------------------------------------------------------------

        # Verify header validation match
        if requests:
            req_headers = list(requests[0].keys())
            if clean_target_date not in req_headers:
                st.error(f"❌ '{clean_target_date}' not found in file headers. Available cleaned headers are: {req_headers}")
                st.stop()

        # Map lookups securely
        registered = {row["player"]: row for row in reg_rows if "player" in row}
        noshows = {row["player"]: row for row in ns_rows if "player" in row}
        
        # Grab target columns matrix cleanly
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Target players meeting asterisk criteria
        eligible = {
            row["player"]
            for row in requests
            if "player" in row and row.get(clean_target_date, "").startswith("*")
        }

        credits = {}
        # Calculate credits mirroring your exact original desktop loop logic
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

        # Build final output matrix list
        output_rows = []
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                sub_pct = has_been_sub_pct(player, registered, reg_weeks, clean_target_date)
                output_rows.append([player, score, sub_pct])

        # Display results
        if not output_rows:
            st.warning(f"⚠️ 0 players had a '*' in the '{clean_target_date}' column.")
        else:
            st.success(f"🎉 Success! Found {len(output_rows)} eligible players.")
            
            # Show interactive data preview table right on the browser screen
            st.subheader("👀 Generated Data Preview")
            st.table([{"Player": r[0], "Credits": r[1], "hasBeenSub": r[2]} for r in output_rows[:20]])
            if len(output_rows) > 20:
                st.caption(f"...and {len(output_rows) - 20} more rows.")

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
