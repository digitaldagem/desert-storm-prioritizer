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

# 3. Process Only on Click
if req_file and reg_file and ns_file and target_date:
    
    if st.button("Process Data", type="primary"):
        clean_target_date = target_date.strip()
        
        # Read from memory with utf-8-sig to clear hidden Excel symbols
        req_text = io.StringIO(req_file.getvalue().decode("utf-8-sig"))
        reg_text = io.StringIO(reg_file.getvalue().decode("utf-8-sig"))
        ns_text = io.StringIO(ns_file.getvalue().decode("utf-8-sig"))

        # Parse CSVs immediately into standard lists of dictionaries
        requests = list(csv.DictReader(req_text))
        reg_rows = list(csv.DictReader(reg_text))
        noshows_rows = list(csv.DictReader(ns_text))
        
        # Safely extract headers using your exact syntax strategy
        req_headers = [k.strip() for k in requests[0].keys()] if requests else []
        reg_weeks = [col for col in reg_rows[0].keys() if col != "player"] if reg_rows else []

        # Map players cleanly
        registered = {row["player"].strip(): row for row in reg_rows if "player" in row}
        noshows = {row["player"].strip(): row for row in noshows_rows if "player" in row}

        # Find eligible players matching the target column 
        eligible = set()
        for row in requests:
            if "player" in row:
                player_name = row["player"].strip()
                # Clean keys on the fly to avoid trailing spaces matching failures
                row_cleaned = {k.strip(): v.strip() for k, v in row.items() if v}
                if row_cleaned.get(clean_target_date, "").startswith("*"):
                    eligible.add(player_name)

        credits = {}
        # Calculate credits mirroring your exact original desktop loop logic
        for row in requests:
            if "player" not in row:
                continue
            player = row["player"].strip()
            credits[player] = 0

            # Normalize keys for the inner loop evaluation
            row_cleaned = {k.strip(): v.strip() for k, v in row.items() if v}

            for week in row_cleaned:
                if week in ("player", clean_target_date):
                    continue

                requested = row_cleaned[week].startswith("*")
                was_registered = registered.get(player, {}).get(week, "").startswith("*")
                was_noshow = noshows.get(player, {}).get(week, "").startswith("*")

                if requested and not was_registered:
                    credits[player] += 1

                if was_registered and was_noshow:
                    credits[player] -= 1

        # Build output structure
        output_rows = []
        
        # Exact lambda value tracking syntax from original local terminal file
        for player, score in sorted(credits.items(), key=lambda x: x[1], reverse=True):
            if player in eligible:
                sub_pct = has_been_sub_pct(player, registered, reg_weeks, clean_target_date)
                output_rows.append([player, score, sub_pct])

        # Render outputs directly onto web UI
        if not output_rows:
            st.warning(f"⚠️ Processed data successfully, but 0 rows matched. Let's trace why:")
            st.write(f"**Target Column Looked For:** `{clean_target_date}`")
            st.write(f"**Actual Headers Found in Requests CSV:** {req_headers}")
            st.write(f"**Total unique players found in file:** {len(credits)}")
        else:
            st.success(f"🎉 Success! Found {len(output_rows)} eligible players.")
            
            # Show a data preview table right on the website screen!
            st.subheader("👀 Data Preview")
            st.table([{"Player": r[0], "Credits": r[1], "hasBeenSub": r[2]} for r in output_rows[:20]])
            if len(output_rows) > 20:
                st.caption(f"...and {len(output_rows) - 20} more rows.")

            # Create final downloadable file
            output_buffer = io.StringIO()
            writer = csv.writer(output_buffer)
            writer.writerow(["player", "credits", "hasBeenSub"])
            writer.writerows(output_rows)

            safe_filename = f"DS_{clean_target_date.replace(' ', '-')}.csv"

            # Render Download button safely
            st.download_button(
                label=f"⬇️ Download {safe_filename}",
                data=output_buffer.getvalue(),
                file_name=safe_filename,
                mime="text/csv"
            )
else:
    st.info("Please fill out the target column field and upload all three CSV files to begin.")
