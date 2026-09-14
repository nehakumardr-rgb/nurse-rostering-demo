import streamlit as st
import pandas as pd
from io import BytesIO
from ortools.sat.python import cp_model

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

st.sidebar.write(
    "Enter the minimum number of nurses required "
    "for each shift."
)

staffing_requirements = []

for day in days:

    st.sidebar.subheader(day)

    morning = st.sidebar.number_input(
        f"{day} - Morning",
        min_value=0,
        max_value=20,
        value=4,
        key=f"staff_morning_{day}"
    )

    evening = st.sidebar.number_input(
        f"{day} - Evening",
        min_value=0,
        max_value=20,
        value=3,
        key=f"staff_evening_{day}"
    )

    night = st.sidebar.number_input(
        f"{day} - Night",
        min_value=0,
        max_value=20,
        value=2,
        key=f"staff_night_{day}"
    )

    staffing_requirements.append(
        {
            "Day": day,
            "Morning": morning,
            "Evening": evening,
            "Night": night
        }
    )

shift_requirements_df = pd.DataFrame(staffing_requirements)
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


# ---------------------------------------------------------
# NURSE AVAILABILITY
# ---------------------------------------------------------

st.header("📋 Nurse Availability")

st.write(
    "Select the shifts each nurse is available to work. "
    "A nurse will only be assigned to shifts marked as available."
)

shifts = ["Morning", "Evening", "Night"]

availability_data = []

for nurse in nurses:

    st.subheader(nurse)

    nurse_availability = {
        "Nurse": nurse
    }

    for day in days:

        selected_shifts = st.multiselect(
            f"{day} availability",
            shifts,
            default=shifts,
            key=f"availability_{nurse}_{day}"
        )

        nurse_availability[day] = selected_shifts

    availability_data.append(nurse_availability)

availability_df = pd.DataFrame(availability_data)

# ---------------------------------------------------------
# NURSE PREFERENCES
# ---------------------------------------------------------

st.header("⭐ Nurse Preferences")

st.write(
    "Enter each nurse's preferred shift and maximum number "
    "of shifts for the week."
)

preferences_data = []

for nurse in nurses:

    col1, col2 = st.columns(2)

    with col1:
        preferred_shift = st.selectbox(
            f"{nurse} - Preferred shift",
            ["No preference", "Morning", "Evening", "Night"],
            key=f"preferred_shift_{nurse}"
        )

    with col2:
        max_shifts = st.number_input(
            f"{nurse} - Maximum shifts",
            min_value=1,
            max_value=7,
            value=5,
            key=f"max_shifts_{nurse}"
        )

    preferences_data.append(
        {
            "Nurse": nurse,
            "Preferred Shift": preferred_shift,
            "Max Shifts": max_shifts
        }
    )

preferences_df = pd.DataFrame(preferences_data)

# ---------------------------------------------------------
# CP-SAT ROSTER OPTIMIZER
# ---------------------------------------------------------

def generate_roster(
    nurses,
    days,
    availability_df,
    preferences_df,
    shift_requirements_df
):

    shifts = ["Morning", "Evening", "Night"]

    model = cp_model.CpModel()

    # -----------------------------------------------------
    # DECISION VARIABLES
    # -----------------------------------------------------

    x = {}

    for nurse in nurses:
        for day in days:
            for shift in shifts:

                x[nurse, day, shift] = model.NewBoolVar(
                    f"{nurse}_{day}_{shift}"
                )

    # -----------------------------------------------------
    # CONSTRAINT 1:
    # MAXIMUM ONE SHIFT PER NURSE PER DAY
    # -----------------------------------------------------

    for nurse in nurses:
        for day in days:

            model.Add(
                sum(
                    x[nurse, day, shift]
                    for shift in shifts
                ) <= 1
            )

    # -----------------------------------------------------
    # CONSTRAINT 2:
    # NURSE AVAILABILITY
    # -----------------------------------------------------

    for nurse in nurses:

        nurse_row = availability_df[
            availability_df["Nurse"] == nurse
        ].iloc[0]

        for day in days:

            available_shifts = nurse_row[day]

            for shift in shifts:

                if shift not in available_shifts:

                    model.Add(
                        x[nurse, day, shift] == 0
                    )

    # -----------------------------------------------------
    # CONSTRAINT 3:
    # MINIMUM STAFFING REQUIREMENT
    # -----------------------------------------------------

    for _, row in shift_requirements_df.iterrows():

        day = row["Day"]

        for shift in shifts:

            required = int(row[shift])

            model.Add(
                sum(
                    x[nurse, day, shift]
                    for nurse in nurses
                ) >= required
            )

    # -----------------------------------------------------
    # CONSTRAINT 4:
    # MAXIMUM SHIFTS PER NURSE
    # -----------------------------------------------------

    for nurse in nurses:

        preference_row = preferences_df[
            preferences_df["Nurse"] == nurse
        ].iloc[0]

        max_shifts = int(
            preference_row["Max Shifts"]
        )

        model.Add(
            sum(
                x[nurse, day, shift]
                for day in days
                for shift in shifts
            ) <= max_shifts
        )

    # -----------------------------------------------------
    # OBJECTIVE:
    # PREFER NURSES' PREFERRED SHIFTS
    # -----------------------------------------------------

    preference_variables = []

    for nurse in nurses:

        preference_row = preferences_df[
            preferences_df["Nurse"] == nurse
        ].iloc[0]

        preferred_shift = preference_row[
            "Preferred Shift"
        ]

        if preferred_shift != "No preference":

            for day in days:

                preference_variables.append(
                    x[nurse, day, preferred_shift]
                )

    if preference_variables:

        model.Maximize(
            sum(preference_variables)
        )

    # -----------------------------------------------------
    # SOLVE
    # -----------------------------------------------------

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    # -----------------------------------------------------
    # CHECK SOLUTION
    # -----------------------------------------------------

    if status not in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ]:

        return None

    # -----------------------------------------------------
    # CREATE ROSTER
    # -----------------------------------------------------

    roster = []

    for nurse in nurses:

        nurse_schedule = {
            "Nurse": nurse
        }

        for day in days:

            assigned_shift = "Off"

            for shift in shifts:

                if solver.Value(
                    x[nurse, day, shift]
                ):

                    assigned_shift = shift
                    break

            nurse_schedule[day] = assigned_shift

        roster.append(nurse_schedule)

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
