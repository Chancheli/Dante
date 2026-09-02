from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# 0. ΑΣΦΑΛΕΙΑ / PASSWORD CHECK
# ---------------------------------------------------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔒 Πρόσβαση στο Σύστημα Crew Operations")
    st.write("Παρακαλώ εισάγετε τον κωδικό πρόσβασης για να συνεχίσετε.")

    CORRECT_PASSWORD = "crew2026"

    user_password = st.text_input("Κωδικός Πρόσβασης:", type="password")

    if st.button("Είσοδος"):
        if user_password == CORRECT_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("❌ Λάθος κωδικός πρόσβασης! Προσπαθήστε ξανά.")

    return False


# ---------------------------------------------------------
# 1. ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
# ---------------------------------------------------------
def get_data_from_gsheets(conn):
    """Διαβάζει τα δεδομένα από το Google Sheet."""
    return conn.read(ttl=0)


def add_log_to_gsheets(
    conn,
    port_name,
    country,
    signer_type,
    nationality,
    role,
    issue_type,
    severity,
    description,
    required_docs,
    agent_details,
    contact_email,
):
    """Προσθέτει μια νέα γραμμή στο Google Sheet."""
    df = get_data_from_gsheets(conn)

    new_row = {
        "Port": port_name.strip().upper(),
        "Country": country.strip().upper(),
        "Signer_Type": signer_type,  # On-signer / Off-signer / Και τα δύο
        "Nationality": nationality,
        "Role": role,
        "Issue_Type": issue_type,
        "Severity": severity,
        "Description": description,
        "Required_Docs": required_docs,
        "Agent_Details": agent_details,
        "Contact_Email": contact_email,
        "Date": datetime.now().strftime("%Y-%m-%d"),
    }

    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    conn.update(data=updated_df)


# ---------------------------------------------------------
# 2. HELPER FUNCTION ΓΙΑ ΕΜΦΑΝΙΣΗ ΚΑΡΤΕΛΩΝ (CARDS)
# ---------------------------------------------------------
def render_log_cards(df_to_show):
    if df_to_show.empty:
        st.info("Δεν υπάρχουν καταχωρημένες σημειώσεις για αυτή την κατηγορία.")
        return

    for _, row in df_to_show.iterrows():
        st.markdown("---")
        severity = row.get("Severity", "Low")
        header_badge = (
            f"🔴 **[Σοβαρότητα: {severity}]**"
            if severity in ["High", "Critical"]
            else f"🟡 **[Σοβαρότητα: {severity}]**"
            if severity == "Medium"
            else f"🔵 **[Σοβαρότητα: {severity}]**"
        )

        st.markdown(
            f"### {header_badge} - {row['Port']} ({row['Country']}) | Κατηγορία: {row['Issue_Type']}"
        )
        st.caption(
            f"📅 Ημερομηνία: **{row['Date']}** | 👥 Αφορά: **{row['Nationality']}** ({row['Role']}) | 🚢 Τύπος: **{row.get('Signer_Type', 'Όλοι')}**"
        )

        st.markdown(f"**📝 Περιγραφή / Οδηγίες:**\n{row['Description']}")

        if pd.notna(row.get("Required_Docs")) and str(row["Required_Docs"]).strip():
            st.markdown("##### 📋 Απαιτούμενα Έγγραφα / Checklist:")
            docs_list = [d.strip() for d in str(row["Required_Docs"]).split(",") if d.strip()]
            for doc in docs_list:
                st.markdown(f"- 📄 {doc}")

        if (pd.notna(row.get("Agent_Details")) and str(row["Agent_Details"]).strip()) or (
            pd.notna(row.get("Contact_Email")) and str(row["Contact_Email"]).strip()
        ):
            st.markdown("##### 📞 Πράκτορας & Επικοινωνία:")
            if pd.notna(row.get("Agent_Details")) and str(row["Agent_Details"]).strip():
                st.write(f"**Σημειώσεις Πράκτορα:** {row['Agent_Details']}")
            if pd.notna(row.get("Contact_Email")) and str(row["Contact_Email"]).strip():
                st.write(f"**Email / Contact:** `{row['Contact_Email']}`")


# ---------------------------------------------------------
# 3. STREAMLIT INTERFACE
# ---------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Crew Operations & Port Intelligence", layout="wide"
    )

    if not check_password():
        return

    conn = st.connection("gsheets", type=GSheetsConnection)

    with st.sidebar:
        st.write("👤 Συνδεδεμένος Χρήστης")
        if st.button("Αποσύνδεση (Logout)"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.title("⚓ Crew Operations & Port Intelligence System")
    st.write(
        "Σύστημα παρακολούθησης κανόνων λιμανιών, ταξιδιωτικών απαιτήσεων & ιστορικού συμβάντων."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🔍 Αναζήτηση & Alerts (Internal)",
            "🌍 Ευρετήριο Χωρών (Country Directory)",
            "➕ Καταχώρηση Νέας Εμπειρίας / Δυσκολίας",
        ]
    )

    # -----------------------------------------------------
    # TAB 1: ΑΝΑΖΗΤΗΣΗ & ON/OFF SIGNERS SUBTABS
    # -----------------------------------------------------
    with tab1:
        st.subheader("Εσωτερικός Έλεγχος & Ιστορικό Εταιρείας")

        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input(
                "🔍 Λιμάνι, Χώρα ή Λέξη-Κλειδί:",
                placeholder="e.g. USA, Garyville, Ploutos",
            )
        with col2:
            search_nat = st.selectbox(
                "Εθνικότητα:", ["Όλες", "Έλληνας", "Φιλιππινέζος"]
            )
        with col3:
            search_role = st.selectbox(
                "Ιδιότητα:", ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"]
            )

        if st.button("Έλεγχος Ιστορικού"):
            df = get_data_from_gsheets(conn)

            if not df.empty and search_query:
                query = search_query.strip().upper()
                filtered_df = df[
                    df["Port"].astype(str).str.contains(query, case=False, na=False)
                    | df["Country"].astype(str).str.contains(query, case=False, na=False)
                    | df["Description"].astype(str).str.contains(query, case=False, na=False)
                    | df["Agent_Details"].astype(str).str.contains(query, case=False, na=False)
                ]

                if search_nat != "Όλες":
                    filtered_df = filtered_df[
                        (filtered_df["Nationality"] == search_nat)
                        | (filtered_df["Nationality"] == "Όλες")
                    ]

                if search_role != "Όλοι":
                    filtered_df = filtered_df[
                        (filtered_df["Role"] == search_role)
                        | (filtered_df["Role"] == "Όλοι")
                    ]

                if not filtered_df.empty:
                    st.success(
                        f"⚠️ Βρέθηκαν {len(filtered_df)} καταγεγραμμένες σημειώσεις για '{query}'."
                    )

                    # Υποκαρτέλες On-signers / Off-signers
                    sub_on, sub_off, sub_all = st.tabs(
                        ["🟢 On-signers (Επιβίβαση)", "🔴 Off-signers (Αποβίβαση)", "📋 Όλα τα αποτελέσματα"]
                    )

                    with sub_on:
                        df_on = filtered_df[
                            filtered_df["Signer_Type"].isin(["On-signer", "Και τα δύο", "Όλοι"])
                        ]
                        render_log_cards(df_on)

                    with sub_off:
                        df_off = filtered_df[
                            filtered_df["Signer_Type"].isin(["Off-signer", "Και τα δύο", "Όλοι"])
                        ]
                        render_log_cards(df_off)

                    with sub_all:
                        render_log_cards(filtered_df)

                else:
                    st.info("Δεν βρέθηκαν αποτελέσματα.")
            else:
                st.info("Παρακαλώ πληκτρολογήστε όνομα λιμανιού ή χώρας.")

    # -----------------------------------------------------
    # TAB 2: ΕΥΡΕΤΗΡΙΟ ΧΩΡΩΝ (COUNTRY DIRECTORY)
    # -----------------------------------------------------
    with tab2:
        st.subheader("🌍 Κατάλογος Χωρών & Συγκεντρωτικοί Κανόνες")
        df = get_data_from_gsheets(conn)

        if not df.empty and "Country" in df.columns:
            available_countries = sorted([c for c in df["Country"].dropna().unique() if str(c).strip() != ""])

            if available_countries:
                selected_country = st.selectbox(
                    "📌 Επιλέξτε Χώρα για προβολή όλων των λιμανιών & κανόνων:",
                    available_countries,
                )

                if selected_country:
                    country_df = df[df["Country"] == selected_country]
                    
                    ports_in_country = country_df["Port"].unique()
                    st.markdown(
                        f"### 📍 Χώρα: **{selected_country}** ({len(ports_in_country)} Λιμάνια: {', '.join(ports_in_country)})"
                    )

                    c_tab_on, c_tab_off, c_tab_all = st.tabs(
                        [
                            "🟢 On-signers (Επιβίβαση)",
                            "🔴 Off-signers (Αποβίβαση)",
                            "📋 Όλα τα Λιμάνια Χώρας",
                        ]
                    )

                    with c_tab_on:
                        df_c_on = country_df[
                            country_df["Signer_Type"].isin(["On-signer", "Και τα δύο", "Όλοι"])
                        ]
                        render_log_cards(df_c_on)

                    with c_tab_off:
                        df_c_off = country_df[
                            country_df["Signer_Type"].isin(["Off-signer", "Και τα δύο", "Όλοι"])
                        ]
                        render_log_cards(df_c_off)

                    with c_tab_all:
                        render_log_cards(country_df)

            else:
                st.info("Δεν έχουν καταχωρηθεί ακόμη χώρες στη βάση.")
        else:
            st.info("Η βάση δεδομένων είναι κενή.")

    # -----------------------------------------------------
    # TAB 3: ΚΑΤΑΧΩΡΗΣΗ ΝΕΟΥ ΣΥΜΒΑΝΤΟΣ
    # -----------------------------------------------------
    with tab3:
        st.subheader("Καταχώρηση Νέας Σημείωσης / Δυσκολίας")

        with st.form("add_log_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                input_port = st.text_input("Όνομα Λιμανιού* (π.χ. Garyville)")
                input_country = st.text_input("Χώρα* (π.χ. USA)")
                input_signer = st.selectbox(
                    "Τύπος Μετακίνησης*",
                    ["On-signer", "Off-signer", "Και τα δύο"],
                )
                input_nat = st.selectbox(
                    "Εθνικότητα*", ["Όλες", "Έλληνας", "Φιλιππινέζος"]
                )

            with f_col2:
                input_role = st.selectbox(
                    "Ιδιότητα*",
                    ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"],
                )
                input_types = st.multiselect(
                    "Κατηγορίες Θέματος*",
                    [
                        "OK to Board Issue",
                        "Visa / Schengen / US C1-D",
                        "Seaman's Book / Transit",
                        "Shore Leave Restriction",
                        "Customs / Technical Equipment",
                        "Agent Negligence / Delay",
                        "Άλλο",
                    ],
                )
                input_severity = st.selectbox(
                    "Επίπεδο Σοβαρότητας*", ["Low", "Medium", "High", "Critical"]
                )

            st.markdown("---")
            input_desc = st.text_area("Περιγραφή Συμβάντος / Οδηγίες*")
            input_docs = st.text_input(
                "📋 Απαιτούμενα Έγγραφα (διαχωρίστε με κόμμα)",
                placeholder="π.χ. US C1/D Visa, ESTA, Guarantee Letter",
            )

            col_agent1, col_agent2 = st.columns(2)
            with col_agent1:
                input_agent = st.text_area("Στοιχεία Πράκτορα / Σημειώσεις")
            with col_agent2:
                input_email = st.text_input("📧 Contact Email")

            submitted = st.form_submit_button("Αποθήκευση στη Βάση")

            if submitted:
                if input_port and input_country and input_desc and input_types:
                    types_str = ", ".join(input_types)
                    add_log_to_gsheets(
                        conn,
                        input_port,
                        input_country,
                        input_signer,
                        input_nat,
                        input_role,
                        types_str,
                        input_severity,
                        input_desc,
                        input_docs,
                        input_agent,
                        input_email,
                    )
                    st.success("Η εγγραφή αποθηκεύτηκε μόνιμα στο Google Sheet!")
                else:
                    st.error("Συμπληρώστε τα υποχρεωτικά πεδία (*).")


if __name__ == "__main__":
    main()
