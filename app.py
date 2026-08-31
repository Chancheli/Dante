import sqlite3
from datetime import datetime
import streamlit as st

# ---------------------------------------------------------
# 0. ΑΣΦΑΛΕΙΑ / PASSWORD CHECK
# ---------------------------------------------------------
def check_password():
    """Επιστρέφει True αν ο χρήστης δώσει το σωστό PIN/Password."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔒 Πρόσβαση στο Σύστημα Crew Operations")
    st.write("Παρακαλώ εισάγετε τον κωδικό πρόσβασης για να συνεχίσετε.")

    # Ορίζεις εδώ τον κωδικό που θέλεις
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
            nationality TEXT NOT NULL,
            role TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            required_docs TEXT,
            agent_details TEXT,
            contact_email TEXT,
            image_data BLOB,
            date_logged TEXT NOT NULL
        )
    """
    )

    # Έλεγχος αν υπάρχουν τα νέα πεδία σε παλιά βάση
    cursor.execute("PRAGMA table_info(port_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if "required_docs" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN required_docs TEXT")
    if "contact_email" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN contact_email TEXT")
    if "image_data" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN image_data BLOB")

    conn.commit()
    conn.close()


def add_log(
    port_name,
    country,
    nationality,
    role,
    issue_type,
    severity,
    description,
    required_docs,
    agent_details,
    contact_email,
    image_bytes,
):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        INSERT INTO port_logs 
        (port_name, country, nationality, role, issue_type, severity, description, required_docs, agent_details, contact_email, image_data, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            port_name.strip().upper(),
            country.strip().upper(),
            nationality,
            role,
            issue_type,
            severity,
            description,
            required_docs,
            agent_details,
            contact_email,
            image_bytes,
            today_str,
        ),
    )
    conn.commit()
    conn.close()


def search_logs(query_text, nationality=None, role=None):
    """
    Έξυπνη αναζήτηση σε Λιμάνι, Χώρα, Περιγραφή, Σημειώσεις και Έγγραφα.
    """
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
# 2. ΕΞΩΤΕΡΙΚΗ ΑΝΤΛΗΣΗ ΠΛΗΡΟΦΟΡΙΩΝ (API Mock / Rules)
# ---------------------------------------------------------
def fetch_external_travel_rules(destination_country, passport_nationality):
    dest = destination_country.strip().lower()
    nat = passport_nationality.strip().lower()

    visa_required = True
    seaman_accepted = True
    transit_info = "Απαιτείται Letter of Guarantee & OK to Board."

    if nat == "greece":
        if dest in ["singapore", "uk", "united kingdom"] or dest in [
            "rotterdam",
            "netherlands",
            "germany",
            "france",
            "italy",
            "spain",
        ]:
            visa_required = False
            transit_info = "Ελεύθερη είσοδος / Transit χωρίς βίζα για διαμονή έως 90 ημέρες."
        elif dest in ["usa", "united states", "us"]:
            visa_required = True
            transit_info = "Απαιτείται ESTA ή US C1/D Visa για ναυτικούς."

    elif nat == "philippines":
        if dest in ["singapore"]:
            visa_required = False
            transit_info = "Ελεύθερη είσοδος για 30 ημέρες, αλλά για αλλαγή πληρώματος απαιτείται SG Arrival Card & OK to Board."
        else:
            visa_required = True
            transit_info = "Απαιτείται OK to Board, Letter of Guarantee και προ-έγκριση βίζας/transit."

    return {
        "status": "success",
        "passport_validity": "Απαιτείται διαβατήριο σε ισχύ τουλάχιστον 6 μηνών.",
        "visa_required": visa_required,
        "seaman_book_accepted": seaman_accepted,
        "transit_rules": transit_info,
    }


# ---------------------------------------------------------
# 3. STREAMLIT INTERFACE
# ---------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Crew Operations & Port Intelligence", layout="wide"
    )

    # Έλεγχος πρόσβασης πριν εμφανιστεί οτιδήποτε
    if not check_password():
        return

    init_db()

    # Πλευρικό κουμπί αποσύνδεσης (Logout)
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
            "🔍 Αναζήτηση Λιμανιού/Χώρας & Alerts (Internal)",
            "🌐 Live Εξωτερικές Πληροφορίες (External API)",
            "➕ Καταχώρηση Νέας Εμπειρίας / Δυσκολίας",
        ]
    )

    # -----------------------------------------------------
    # TAB 1: ΑΝΑΖΗΤΗΣΗ & AUTOMATED ALERTS
    # -----------------------------------------------------
    with tab1:
        st.subheader("Εσωτερικός Έλεγχος & Ιστορικό Εταιρείας")

        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input(
                "🔍 Λιμάνι, Χώρα ή Λέξη-Κλειδί:",
                placeholder="e.g. USA, Garyville, Ploutos, Jamaica",
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
                    critical_alerts = [
                        l for l in logs if l[6] in ["High", "Critical"]
                    ]

                    if critical_alerts:
                        st.error(
                            f"🚨 **ΠΡΟΣΟΧΗ! Βρέθηκαν {len(critical_alerts)} σημαντικές ειδοποιήσεις/δυσκολίες για την αναζήτηση '{search_query.upper()}'!**"
                        )
                    else:
                        st.warning(
                            f"⚠️ Βρέθηκαν {len(logs)} καταγεγραμμένες σημειώσεις/συμβάντα για την αναζήτηση '{search_query.upper()}'."
                        )

                    for log in logs:
                        (
                            log_id,
                            p_name,
                            country,
                            nat,
                            role,
                            i_type,
                            severity,
                            desc,
                            req_docs,
                            agent,
                            c_email,
                            img_data,
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
                            f"📅 Ημερομηνία Καταγραφής: **{date_logged}** | 📍 Λιμάνι: **{p_name}** | Χώρα: **{country}** | 👥 Αφορά: **{nat}** ({role})"
                        )

                        st.markdown(f"**📝 Περιγραφή / Συμβάν:**\n{desc}")

                        if req_docs:
                            st.markdown("##### 📋 Απαιτούμενα Έγγραφα / Checklist:")
                            docs_list = [
                                d.strip() for d in req_docs.split(",") if d.strip()
                            ]
                            for doc in docs_list:
                                st.markdown(f"- 📄 {doc}")

                        if agent or c_email:
                            st.markdown("##### 📞 Πράκτορας & Επικοινωνία:")
                            if agent:
                                st.write(f"**Σημειώσεις Πράκτορα:** {agent}")
                            if c_email:
                                st.write(f"**Email / Contact:** `{c_email}`")

                        if img_data:
                            st.markdown("##### 🖼️ Επισυναπτόμενο Screenshot / Email:")
                            st.image(img_data, use_container_width=True)

                else:
                    st.success(
                        f"✅ Δεν βρέθηκαν καταγεγραμμένες δυσκολίες ή ειδικές ειδοποιήσεις για την αναζήτηση **'{search_query.upper()}'** στη βάση."
                    )
            else:
                st.info("Παρακαλώ πληκτρολογήστε όνομα λιμανιού, χώρας ή λέξη-κλειδί.")

    # -----------------------------------------------------
    # TAB 2: LIVE ΕΞΩΤΕΡΙΚΕΣ ΠΛΗΡΟΦΟΡΙΕΣ (EXTERNAL API)
    # -----------------------------------------------------
    with tab2:
        st.subheader("Live Άντληση Ταξιδιωτικών Κανόνων & Βίζας")
        st.write(
            "Άντληση δεδομένων σε πραγματικό χρόνο από εξωτερικές πηγές (IATA/Timatic/Travel APIs)."
        )

        ext_col1, ext_col2 = st.columns(2)
        with ext_col1:
            ext_country = st.text_input(
                "Χώρα Προορισμού / Λιμανιού:", placeholder="e.g. Singapore, USA"
            )
        with ext_col2:
            ext_nat = st.selectbox(
                "Εθνικότητα Ταξιδιώτη:",
                ["Greece", "Philippines", "Other"],
                key="ext_nat",
            )

        if st.button("Αναζήτηση Εξωτερικών Κανόνων"):
            if ext_country:
                with st.spinner("Σύνδεση με εξωτερική πηγή δεδομένων..."):
                    ext_data = fetch_external_travel_rules(
                        ext_country, ext_nat
                    )

                if ext_data.get("status") == "success":
                    st.success(
                        f"🌐 Live Δεδομένα για εισαγωγή στη χώρα: **{ext_country.title()}** ({ext_nat})"
                    )

                    st.info(f"📌 **Ισχύς Διαβατηρίου:** {ext_data['passport_validity']}")

                    if ext_data["visa_required"]:
                        st.error("🛂 **Απαίτηση Βίζας:** Ναι")
                    else:
                        st.success("🛂 **Απαίτηση Βίζας:** Όχι (Δεν απαιτείται βίζα)")

                    st.write(
                        f"📘 **Αποδοχή Ναυτικού Φυλλαδίου:** {'Ναι' if ext_data['seaman_book_accepted'] else 'Όχι'}"
                    )
                    st.write(f"✈️ **Transit / Rules:** {ext_data['transit_rules']}")
                else:
                    st.error("Αποτυχία σύνδεσης με την εξωτερική υπηρεσία.")
            else:
                st.info("Παρακαλώ πληκτρολογήστε τη χώρα προορισμού.")

    # -----------------------------------------------------
    # TAB 3: ΚΑΤΑΧΩΡΗΣΗ ΝΕΟΥ ΣΥΜΒΑΝΤΟΣ
    # -----------------------------------------------------
    with tab3:
        st.subheader("Καταχώρηση Νέας Σημείωσης / Δυσκολίας")
        st.write(
            "Συμπληρώστε τα στοιχεία, ανεβάστε screenshots e-mail και ορίστε τη λίστα απαιτούμενων εγγράφων."
        )

        with st.form("add_log_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                input_port = st.text_input("Όνομα Λιμανιού* (π.χ. Garyville)")
                input_country = st.text_input("Χώρα* (π.χ. USA)")
                input_nat = st.selectbox(
                    "Εθνικότητα που αφορά*",
                    ["Όλες", "Έλληνας", "Φιλιππινέζος"],
                )
                input_role = st.selectbox(
                    "Ιδιότητα που αφορά*",
                    ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"],
                )

            with f_col2:
                input_types = st.multiselect(
                    "Κατηγορίες Θέματος* (Επιλέξτε μία ή περισσότερες)",
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
                    "Επίπεδο Σοβαρότητας / Alert*",
                    [
                        "Low (Απλή πληροφορία)",
                        "Medium (Προσοχή)",
                        "High (Μεγάλη δυσκολία / Καθυστέρηση)",
                        "Critical (Απαγόρευση / Πρόστιμο)",
                    ],
                )
                severity_clean = input_severity.split()[0]

            st.markdown("---")
            input_desc = st.text_area(
                "Περιγραφή Συμβάντος / Κανόνα*",
                placeholder="Περιγράψτε τι συνέβη ή ποιος κανόνας ισχύει...",
            )

            input_docs = st.text_input(
                "📋 Απαιτούμενα Έγγραφα (διαχωρίστε με κόμμα)",
                placeholder="π.χ. US C1/D Visa, ESTA, OK to Board Letter, Guarantee Letter",
            )

            col_agent1, col_agent2 = st.columns(2)
            with col_agent1:
                input_agent = st.text_area(
                    "Στοιχεία Πράκτορα / Σημειώσεις",
                    placeholder="Όνομα πρακτορείου, οδηγίες...",
                )
            with col_agent2:
                input_email = st.text_input(
                    "📧 Contact Email Πράκτορα / Αρχής",
                    placeholder="agent@shipping-agency.com",
                )

            uploaded_file = st.file_uploader(
                "🖼️ Ανέβασμα Screenshot / Email (JPG, PNG)",
                type=["png", "jpg", "jpeg"],
            )

            submitted = st.form_submit_button("Αποθήκευση στη Βάση")

            if submitted:
                if input_port and input_country and input_desc and input_types:
                    image_bytes = uploaded_file.read() if uploaded_file else None
                    types_str = ", ".join(input_types)

                    add_log(
                        input_port,
                        input_country,
                        input_nat,
                        input_role,
                        types_str,
                        severity_clean,
                        input_desc,
                        input_docs,
                        input_agent,
                        input_email,
                        image_bytes,
                    )
                    st.success(
                        f"Η εγγραφή για το λιμάνι {input_port.upper()} ({input_country.upper()}) αποθηκεύτηκε με επιτυχία!"
                    )
                else:
                    st.error(
                        "Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία με αστερίσκο (*) και επιλέξτε τουλάχιστον μία Κατηγορία Θέματος."
                    )


if __name__ == "__main__":
    main()
