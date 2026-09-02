import sqlite3
from datetime import datetime
import streamlit as st

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
# 1. ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ (SQLite Setup)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS port_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port_name TEXT NOT NULL,
            country TEXT NOT NULL,
            signer_type TEXT NOT NULL,
            nationality TEXT NOT NULL,
            role TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            required_docs TEXT,
            agent_details TEXT,
            contact_email TEXT,
            date_logged TEXT NOT NULL
        )
    """
    )

    # Έλεγχος & Αυτόματη Αναβάθμιση Πεδίων
    cursor.execute("PRAGMA table_info(port_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if "signer_type" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN signer_type TEXT DEFAULT 'Και τα δύο'")

    conn.commit()
    conn.close()


def add_log(
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
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        INSERT INTO port_logs 
        (port_name, country, signer_type, nationality, role, issue_type, severity, description, required_docs, agent_details, contact_email, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            port_name.strip().upper(),
            country.strip().upper(),
            signer_type,
            nationality,
            role,
            issue_type,
            severity,
            description,
            required_docs,
            agent_details,
            contact_email,
            today_str,
        ),
    )
    conn.commit()
    conn.close()


def fetch_all_logs():
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM port_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_logs(query_text, nationality=None, role=None):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    sql = "SELECT * FROM port_logs WHERE 1=1"
    params = []

    if query_text:
        search_pattern = f"%{query_text.strip().upper()}%"
        sql += """ AND (
            UPPER(port_name) LIKE ? 
            OR UPPER(country) LIKE ? 
            OR UPPER(description) LIKE ? 
            OR UPPER(agent_details) LIKE ? 
            OR UPPER(required_docs) LIKE ?
        )"""
        params.extend([search_pattern] * 5)

    if nationality and nationality != "Όλες":
        sql += " AND (nationality = ? OR nationality = 'Όλες')"
        params.append(nationality)

    if role and role != "Όλοι":
        sql += " AND (role = ? OR role = 'Όλοι')"
        params.append(role)

    sql += " ORDER BY id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# 2. HELPER FUNCTION ΓΙΑ ΕΜΦΑΝΙΣΗ ΚΑΡΤΕΛΩΝ (CARDS)
# ---------------------------------------------------------
def render_log_cards(logs_list):
    if not logs_list:
        st.info("Δεν υπάρχουν καταχωρημένες σημειώσεις για αυτή την κατηγορία.")
        return

    for log in logs_list:
        (
            log_id,
            p_name,
            country,
            s_type,
            nat,
            role,
            i_type,
            severity,
            desc,
            req_docs,
            agent,
            c_email,
            date_logged,
        ) = log

        st.markdown("---")
        header_badge = (
            f"🔴 **[Σοβαρότητα: {severity}]**"
            if severity in ["High", "Critical"]
            else f"🟡 **[Σοβαρότητα: {severity}]**"
            if severity == "Medium"
            else f"🔵 **[Σοβαρότητα: {severity}]**"
        )

        st.markdown(
            f"### {header_badge} - {p_name} ({country}) | Κατηγορία: {i_type}"
        )
        st.caption(
            f"📅 Ημερομηνία: **{date_logged}** | 👥 Αφορά: **{nat}** ({role}) | 🚢 Τύπος: **{s_type}**"
        )

        st.markdown(f"**📝 Περιγραφή / Οδηγίες:**\n{desc}")

        if req_docs and req_docs.strip():
            st.markdown("##### 📋 Απαιτούμενα Έγγραφα / Checklist:")
            docs_list = [d.strip() for d in req_docs.split(",") if d.strip()]
            for doc in docs_list:
                st.markdown(f"- 📄 {doc}")

        if (agent and agent.strip()) or (c_email and c_email.strip()):
            st.markdown("##### 📞 Πράκτορας & Επικοινωνία:")
            if agent and agent.strip():
                st.write(f"**Σημειώσεις Πράκτορα:** {agent}")
            if c_email and c_email.strip():
                st.write(f"**Email / Contact:** `{c_email}`")


# ---------------------------------------------------------
# 3. STREAMLIT INTERFACE
# ---------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Crew Operations & Port Intelligence", layout="wide"
    )

    if not check_password():
        return

    init_db()

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
            if search_query:
                logs = search_logs(search_query, search_nat, search_role)

                if logs:
                    st.success(
                        f"⚠️ Βρέθηκαν {len(logs)} καταγεγραμμένες σημειώσεις για '{search_query.upper()}'."
                    )

                    sub_on, sub_off, sub_all = st.tabs(
                        [
                            "🟢 On-signers (Επιβίβαση)",
                            "🔴 Off-signers (Αποβίβαση)",
                            "📋 Όλα τα αποτελέσματα",
                        ]
                    )

                    with sub_on:
                        logs_on = [
                            l for l in logs if l[3] in ["On-signer", "Και τα δύο"]
                        ]
                        render_log_cards(logs_on)

                    with sub_off:
                        logs_off = [
                            l for l in logs if l[3] in ["Off-signer", "Και τα δύο"]
                        ]
                        render_log_cards(logs_off)

                    with sub_all:
                        render_log_cards(logs)

                else:
                    st.info("Δεν βρέθηκαν αποτελέσματα στη βάση.")
            else:
                st.info("Παρακαλώ πληκτρολογήστε όνομα λιμανιού, χώρας ή λέξη-κλειδί.")

    # -----------------------------------------------------
    # TAB 2: ΕΥΡΕΤΗΡΙΟ ΧΩΡΩΝ (COUNTRY DIRECTORY)
    # -----------------------------------------------------
    with tab2:
        st.subheader("🌍 Κατάλογος Χωρών & Συγκεντρωτικοί Κανόνες")
        all_logs = fetch_all_logs()

        if all_logs:
            # Δημιουργία μοναδικής λίστας χωρών
            countries = sorted(list(set([l[2] for l in all_logs if l[2]])))

            if countries:
                selected_country = st.selectbox(
                    "📌 Επιλέξτε Χώρα για προβολή όλων των λιμανιών & κανόνων:",
                    countries,
                )

                if selected_country:
                    country_logs = [l for l in all_logs if l[2] == selected_country]
                    ports_in_country = sorted(list(set([l[1] for l in country_logs])))

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
                        c_logs_on = [
                            l for l in country_logs if l[3] in ["On-signer", "Και τα δύο"]
                        ]
                        render_log_cards(c_logs_on)

                    with c_tab_off:
                        c_logs_off = [
                            l for l in country_logs if l[3] in ["Off-signer", "Και τα δύο"]
                        ]
                        render_log_cards(c_logs_off)

                    with c_tab_all:
                        render_log_cards(country_logs)

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
                    "Επίπεδο Σοβαρότητας*",
                    [
                        "Low (Απλή πληροφορία)",
                        "Medium (Προσοχή)",
                        "High (Μεγάλη δυσκολία)",
                        "Critical (Απαγόρευση)",
                    ],
                )
                severity_clean = input_severity.split()[0]

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
                    add_log(
                        input_port,
                        input_country,
                        input_signer,
                        input_nat,
                        input_role,
                        types_str,
                        severity_clean,
                        input_desc,
                        input_docs,
                        input_agent,
                        input_email,
                    )
                    st.success("Η εγγραφή αποθηκεύτηκε επιτυχώς στη βάση!")
                else:
                    st.error("Συμπληρώστε τα υποχρεωτικά πεδία (*).")


if __name__ == "__main__":
    main()
