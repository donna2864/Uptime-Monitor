import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def open_edit_monitor(monitor_id):
    st.session_state.edit_monitor_id = monitor_id


st.set_page_config(
    page_title="Uptime Monitor",
    page_icon="⚙️",
    layout="wide"
)

# --------------------------------------------------
# Page Header
# --------------------------------------------------

st.title("⚙️ Uptime Monitor")
st.caption("Monitor your APIs and websites in one place")


st.divider()

# --------------------------------------------------
# Add Monitor
# --------------------------------------------------

st.subheader("Add a Monitor")

with st.form("add_monitor_form"):

    col1, col2, col3 = st.columns([2, 4, 2])

    with col1:
        name = st.text_input(
            "Monitor Name",
            placeholder="My API"
        )

    with col2:
        url = st.text_input(
            "URL",
            placeholder="https://example.com"
        )

    with col3:
        interval = st.number_input(
            "Check Interval (seconds)",
            min_value=10,
            value=60,
            step=10
        )

    submitted = st.form_submit_button(
        "➕ Add Monitor",
        use_container_width=True
    )

    if submitted:
        if not name or not url:
            st.warning("Please enter both a name and URL.")

        else:
            try:
                create_response = requests.post(
                    f"{API_URL}/monitors",
                    json={
                        "name": name,
                        "url": url,
                        "interval_seconds": interval
                    },
                    timeout=5
                )

                if create_response.status_code == 200:
                    st.success("Monitor added successfully.")
                    st.rerun()

                else:
                    st.error(
                        f"Could not create monitor: "
                        f"{create_response.text}"
                    )

            except requests.RequestException as error:
                st.error(
                    f"Could not connect to the FastAPI backend: "
                    f"{error}"
                )

st.divider()

# --------------------------------------------------
# Monitors
# --------------------------------------------------

st.subheader("Monitors")

try:
    response = requests.get(
        f"{API_URL}/monitors",
        timeout=5
    )
    response.raise_for_status()
    monitors = response.json()

    if not monitors:
        st.info("No monitors loaded yet. Add a monitor above to get started.")

    else:
        for monitor in monitors:
            # ------------------------------------------
            # Get monitor status
            # ------------------------------------------
            status_response = requests.get(
                f"{API_URL}/monitors/{monitor['id']}/status",
                timeout=5
            )
            status_response.raise_for_status()
            status = status_response.json()

            # ------------------------------------------
            # Monitor Header + Actions
            # ------------------------------------------

            name_col, action_col, pause_col, delete_col = st.columns([5, 1.2, 1.5, 1.2])

            with name_col:
                st.markdown(f"### {monitor['name']}")
                st.caption(monitor["url"])

            with action_col:
                edit_clicked = st.button(
                    "✏️ Edit",
                    key=f"edit_{monitor['id']}",
                    use_container_width=True,
                    on_click=open_edit_monitor,
                    args=(monitor["id"],)
                )
            with pause_col:
                if monitor["active"]:
                    pause_clicked = st.button(
                        "⏸ Pause",
                        key=f"pause_{monitor['id']}",
                        use_container_width=True
                    )

                    if pause_clicked:
                        try:
                            pause_response = requests.put(
                                f"{API_URL}/monitors/{monitor['id']}",
                                json={
                                    "active": False
                                },
                                timeout=5
                            )

                            if pause_response.status_code == 200:
                                st.success("Monitor paused.")
                                st.rerun()
                            else:
                                st.error( f"Could not pause monitor: "
                                    f"{pause_response.text}"
                                )

                        except requests.RequestException as error:
                            st.error(
                                f"Could not connect to the "
                                f"FastAPI backend: {error}"
                            )

                else:
                    resume_clicked = st.button(
                        "▶ Resume",
                        key=f"resume_{monitor['id']}",
                        use_container_width=True
                    )

                    if resume_clicked:
                        try:
                            resume_response = requests.put(
                                f"{API_URL}/monitors/{monitor['id']}",
                                json={
                                    "active": True
                                },
                                timeout=5
                            )

                            if resume_response.status_code == 200:
                                st.success("Monitor resumed.")
                                st.rerun()
                            else:
                                st.error(
                                    f"Could not resume monitor: "
                                    f"{resume_response.text}"
                                )

                        except requests.RequestException as error:
                            st.error(
                                f"Could not connect to the "
                                f"FastAPI backend: {error}"
                            )

            with delete_col:
                delete_clicked = st.button(
                    "🗑 Delete",
                    key=f"delete_{monitor['id']}",
                    use_container_width=True
                )

                if delete_clicked:
                    try:
                        delete_response = requests.delete(
                            f"{API_URL}/monitors/{monitor['id']}",
                            timeout=5
                        )

                        if delete_response.status_code == 200:
                            st.success("Monitor deleted successfully.")
                            st.rerun()
                        else:
                            st.error(
                                f"Could not delete monitor: "
                                f"{delete_response.text}"
                            )

                    except requests.RequestException as error:
                        st.error(
                            f"Could not connect to the "
                            f"FastAPI backend: {error}"
                        )

            # ------------------------------------------
            # Edit Monitor
            # ------------------------------------------

            if st.session_state.get("edit_monitor_id") == monitor["id"]:
                with st.expander("✏️ Edit Monitor", expanded=True):
                    with st.form( f"edit_monitor_form_{monitor['id']}"):
                        edit_col1, edit_col2, edit_col3 = st.columns( [2, 4, 2])

                        with edit_col1:
                            edit_name = st.text_input( "Monitor Name", value=monitor["name"])

                        with edit_col2:
                            edit_url = st.text_input("URL", value=monitor["url"] )

                        with edit_col3:
                            edit_interval = st.number_input(
                                "Check Interval (seconds)",
                                min_value=10,
                                value=monitor["interval_seconds"],
                                step=10
                            )

                        save_changes = st.form_submit_button(
                            "Save Changes",
                            use_container_width=True
                        )
                        
                        if save_changes:
                            
                            try:
                                update_response = requests.put(
                                    f"{API_URL}/monitors/{monitor['id']}",
                                    json={
                                        "name": edit_name,
                                        "url": edit_url,
                                        "interval_seconds": edit_interval
                                    },
                                    timeout=5
                                )

                                if update_response.status_code == 200:
                                    st.session_state.pop("edit_monitor_id", None)
                                    st.rerun()
                                else:
                                    st.error(
                                        f"Could not update monitor: "
                                        f"{update_response.text}"
                                    )

                            except requests.RequestException as error:
                                st.error(
                                    f"Could not connect to the "
                                    f"FastAPI backend: {error}"
                                )

            # ------------------------------------------
            # Monitor Metrics
            # ------------------------------------------

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                if monitor["active"]:
                    if status["current_status"] == "UP":
                        st.metric( "Status", "🟢 UP"  )
                    else:
                        st.metric( "Status", "🔴 DOWN" )
                else:
                    st.metric( "Status","⏸ PAUSED" )


            with metric_col2:
                st.metric("Uptime",  f"{status['uptime_percentage']}%" )

            with metric_col3:
                response_time = status["average_response_time_ms" ]

                if response_time is not None:
                    st.metric("Avg Response", f"{response_time} ms" )
                else:
                    st.metric( "Avg Response","N/A" )

            with metric_col4:
                st.metric( "Failed Checks", status["failed_checks"])

            st.caption(
                f"Total checks: {status['total_checks']} "
                f"• Check interval: "
                f"{monitor['interval_seconds']} seconds"
            )

            # ------------------------------------------
            # Check History
            # ------------------------------------------

            with st.expander( "📊 View Check History" ):
                history_response = requests.get(
                    f"{API_URL}/monitors/{monitor['id']}/history",
                    timeout=5
                )

                history_response.raise_for_status()

                history = history_response.json()
                if not history:
                    st.info( "No check history available.")

                else:
                    for check in history:
                        if check["is_up"]:
                            status_label = "🟢 UP"
                        else:
                            status_label = "🔴 DOWN"

                        st.markdown(
                            f"**{status_label}** — "
                            f"{check['checked_at']}"
                        )

                        history_col1, history_col2, history_col3 = st.columns(3)
                        with history_col1:
                            st.write(
                                f"Status Code: "
                                f"{check['status_code'] or 'N/A'}"
                            )

                        with history_col2:
                            response_time = check["response_time_ms"]
                            if response_time is not None:
                                st.write(f"Response Time:{response_time} ms")
                            else:
                                st.write("Response Time: N/A")

                        with history_col3:
                            if check["error_message"]:
                                st.write(f"Error: {check['error_message']}")
                            else:
                                st.write("No error")

                        st.divider()

            # ------------------------------------------
            # Incidents
            # ------------------------------------------

            with st.expander("🚨 View Incidents"):

                incidents_response = requests.get(
                    f"{API_URL}/monitors/{monitor['id']}/incidents",
                    timeout=5
                )

                incidents_response.raise_for_status()

                incidents = incidents_response.json()
                if not incidents:
                    st.success("No incidents recorded." )

                else:
                    for incident in incidents:
                        if incident["resolved_at"]:
                            st.success("✅ Resolved")

                        else:
                            st.error("🚨 Active Incident")

                        incident_col1, incident_col2 = st.columns(2)

                        with incident_col1:
                            st.write(
                                f"**Started:** "
                                f"{incident['started_at']}"
                            )

                        with incident_col2:
                            if incident["resolved_at"]:
                                st.write(
                                    f"**Resolved:** "
                                    f"{incident['resolved_at']}"
                                )
                            else:
                                st.write(
                                    "**Resolved:** "
                                    "Still active"
                                )

                        st.write(
                            f"**Reason:** "
                            f"{incident['reason']}"
                        )

                        st.divider()

            st.divider()

except requests.RequestException:
    st.error( "Couldn't connect to Backend :(")