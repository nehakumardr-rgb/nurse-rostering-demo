import streamlit as st
import pandas as pd
from io import BytesIO

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Nurse Rostering",
    page_icon="🏥",
    layout="wide"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🏥 AI Nurse Rostering System")

st.markdown(
    """
    **Generate an optimized weekly nurse roster while considering
    staffing requirements, nurse availability, working hours and preferences.**
    """
)

st.divider()

# ---------------------------------------------------------
# SIDEBAR - STAFFING REQUIREMENTS
# ---------------------------------------------------------

st.sidebar.header("⚙️ Staffing Requirements")

morning_required = st.sidebar.number_input(
    "Morning nurses required",
    min_value=1,
    max_value=20,
    value=4
)

evening_required = st.sidebar.number_input(
    "Evening nurses required",
    min_value=1,
    max_value=20,
    value=3
)

night_required = st.sidebar.number_input(
    "Night nurses required",
    min_value=1,
    max_value=20,
    value=2
)

st.sidebar.divider()

st.sidebar.info(
    "This first version uses sample nurse data. "
    "Your actual CP-SAT optimization model will be connected later."
)

# ---------------------------------------------------------
# SAMPLE NURSE DATA
# ---------------------------------------------------------

# ---------------------------------------------------------
# NURSE INPUT
# ---------------------------------------------------------

st.header("👩‍⚕️ Nurse Information")

st.write("Enter the nurses who will be included in this week's roster.")

number_of_nurses = st.number_input(
    "Number of nurses",
    min_value=1,
    max_value=50,
    value=12,
    step=1
)

nurses = []

for i in range(number_of_nurses):

    nurse_name = st.text_input(
        f"Nurse {i + 1}",
        value=f"Nurse {i + 1}",
        key=f"nurse_{i}"
    )

    nurses.append(nurse_name)

days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# ---------------------------------------------------------
# SAMPLE ROSTER GENERATOR
# ---------------------------------------------------------

def generate_sample_roster():

    shifts = ["Morning", "Evening", "Night", "Off"]

    roster = []

    for i, nurse in enumerate(nurses):

        nurse_schedule = {}

        for j, day in enumerate(days):

            # Create a simple rotating sample roster
            pattern = (i + j) % 4

            if pattern == 0:
                shift = "Morning"
            elif pattern == 1:
                shift = "Evening"
            elif pattern == 2:
                shift = "Night"
            else:
                shift = "Off"

            nurse_schedule[day] = shift

        roster.append(
            {
                "Nurse": nurse,
                **nurse_schedule
            }
        )

    return pd.DataFrame(roster)


# ---------------------------------------------------------
# GENERATE ROSTER BUTTON
# ---------------------------------------------------------

st.header("📅 Weekly Nurse Roster")

if st.button(
    "🚀 Generate Roster",
    type="primary",
    use_container_width=True
):

    roster_df = generate_sample_roster()

    st.session_state["roster"] = roster_df

# ---------------------------------------------------------
# DISPLAY ROSTER
# ---------------------------------------------------------

if "roster" in st.session_state:

    roster_df = st.session_state["roster"]

    st.dataframe(
        roster_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # -----------------------------------------------------
    # VALIDATION SUMMARY
    # -----------------------------------------------------

    st.header("✅ Roster Validation")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Nurses",
            len(nurses)
        )

    with col2:
        st.metric(
            "Morning Required",
            morning_required
        )

    with col3:
        st.metric(
            "Evening Required",
            evening_required
        )

    with col4:
        st.metric(
            "Night Required",
            night_required
        )

    st.success("Roster generated successfully.")

    st.info(
        "The current roster is a demonstration roster. "
        "In the final version, the Generate Roster button will run "
        "your CP-SAT optimization model."
    )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    csv = roster_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Roster",
        data=csv,
        file_name="nurse_roster.csv",
        mime="text/csv"
    )

else:

    st.info(
        "👈 Set the staffing requirements and click "
        "**Generate Roster** to create the weekly roster."
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Healthcare AI Portfolio Project | Nurse Workforce Planning & Rostering"
)
