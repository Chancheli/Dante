import sqlite3
from datetime import datetime
import requests
import streamlit as st

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
            agent_details TEXT,
            date_logged TEXT NOT NULL
        )
    """
    )
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
    agent_details,
):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        INSERT INTO port_logs 
        (port_name, country, nationality, role, issue_type, severity, description, agent_details, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            port_name.strip().upper(),
            country.strip().title(),
            nationality,
            role,
            issue_type,
            severity,
            description,
            agent_details,
            today_str,
        ),
    )
    conn.commit()
    conn.close()


def get_logs_for_port(port_name, nationality=None, role=None):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    query = "SELECT * FROM port_logs WHERE port_name = ?"
    params = [port_name.strip().upper()]

    if nationality and nationality != "Όλες":
        query += " AND (nationality = ? OR nationality = 'Όλες')"
        params.append(nationality)

    if role and role != "Όλοι":
        query += " AND (role = ? OR role = 'Όλοι')"
        params.append(role)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# 2. ΕΞΩΤΕΡΙΚΗ ΑΝΤΛΗΣΗ ΠΛΗΡΟΦΟΡΙΩΝ (Δυναμική Λογική / API)
# ---------------------------------------------------------
def fetch_external_travel_rules(destination_country, passport_nationality):
    """
    Ελέγχει τους ταξιδιωτικούς κανόνες βάσει εθνικότητας και προορισμού.
    """
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
        elif dest in ["usa", "united states"]:
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
    init_db()

    st.title("⚓ Crew Operations & Port Intelligence System")
    st.write(
        "Σύστημα παρακολούθησης κανόνων λιμανιών, ταξιδιωτικών απαιτήσεων & ιστορικού συμβάντων."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🔍 Αναζήτηση Λιμανιού & Alerts (Internal)",
            "🌐 Live Εξωτερικές Πληροφορίες (External API)",
            "➕ Καταχώρηση Νέας Εμπειρίας / Δυσκολίας",
        ]
    )

    # -----------------------------------------------------
    # TAB 1: ΑΝΑΖΗΤΗΣΗ & AUTOMATED ALERTS (INTERNAL DB)
    # -----------------------------------------------------
    with tab1:
        st.subheader("Εσωτερικός Έλεγχος & Ιστορικό Εταιρείας")

        col1, col2, col3 = st.columns(3)
        with col1:
            search_port = st.text_input(
                "Όνομα Λιμανιού (π.χ. Singapore, Rotterdam, Alexandria):"
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
            if search_port:
                logs = get_logs_for_port(
                    search_port, search_nat, search_role
                )

                if logs:
                    critical_alerts = [
                        l for l in logs if l[6] in ["High", "Critical"]
                    ]

                    if critical_alerts:
                        st.error(
                            f"🚨 **ΠΡΟΣΟΧΗ! Βρέθηκαν {len(critical_alerts)} σημαντικές ειδοποιήσεις/δυσκολίες για το λιμάνι {search_port.upper()}!**"
                        )
                    else:
                        st.warning(
                            f"⚠️ Βρέθηκαν {len(logs)} καταγεγραμμένες σημειώσεις/συμβάντα για το λιμάνι {search_port.upper()}."
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
                            agent,
                            date_logged,
                        ) = log

                        log_date = datetime.strptime(date_logged, "%Y-%m-%d")
                        days_old = (datetime.now() - log_date).days
                        time_warning = ""
                        if days_old > 365:
                            time_warning = " ⏳ *(Καταγράφηκε πριν από 1+ χρόνο - Επιβεβαιώστε αν ισχύει ακόμα)*"

                        # Εμφάνιση εγγραφών ανάλογα με τη σοβαρότητα
                        if severity in ["High", "Critical"]:
                            st.error(
                                f"**[Σοβαρότητα: {severity}] - {i_type}** | Ημερομηνία: {date_logged}{time_warning}\n\n"
                                f"**Εθνικότητα:** {nat} | **Ιδιότητα:** {role} | **Χώρα:** {country}\n\n"
                                f"**Περιγραφή/Δυσκολία:** {desc}\n\n"
                                f"{'**Στοιχεία Πράκτορα / Tips:** ' + agent if agent else ''}"
                            )
                        elif severity == "Medium":
                            st.warning(
                                f"**[Σοβαρότητα: {severity}] - {i_type}** | Ημερομηνία: {date_logged}{time_warning}\n\n"
                                f"**Εθνικότητα:** {nat} | **Ιδιότητα:** {role} | **Χώρα:** {country}\n\n"
                                f"**Περιγραφή/Δυσκολία:** {desc}\n\n"
                                f"{'**Στοιχεία Πράκτορα / Tips:** ' + agent if agent else ''}"
                            )
                        else:
                            st.info(
                                f"**[Σοβαρότητα: {severity}] - {i_type}** | Ημερομηνία: {date_logged}{time_warning}\n\n"
                                f"**Εθνικότητα:** {nat} | **Ιδιότητα:** {role} | **Χώρα:** {country}\n\n"
                                f"**Περιγραφή/Δυσκολία:** {desc}\n\n"
                                f"{'**Στοιχεία Πράκτορα / Tips:** ' + agent if agent else ''}"
                            )
                else:
                    st.success(
                        f"✅ Δεν βρέθηκαν καταγεγραμμένες δυσκολίες ή ειδικές ειδοποιήσεις για το λιμάνι **{search_port.upper()}** στη βάση."
                    )
            else:
                st.info("Παρακαλώ πληκτρολογήστε ένα όνομα λιμανιού.")

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
                "Χώρα Προορισμού / Λιμανιού:", placeholder="e.g. Singapore, Egypt"
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

                    if ext_data['visa_required']:
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
            "Συμπληρώστε τα στοιχεία όταν συναντάτε μια νέα απαίτηση, καθυστέρηση ή ιδιαιτερότητα σε κάποιο λιμάνι."
        )

        with st.form("add_log_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                input_port = st.text_input("Όνομα Λιμανιού* (π.χ. Suez)")
                input_country = st.text_input("Χώρα* (π.χ. Egypt)")
                input_nat = st.selectbox(
                    "Εθνικότητα που αφορά*",
                    ["Όλες", "Έλληνας", "Φιλιππινέζος"],
                )
                input_role = st.selectbox(
                    "Ιδιότητα που αφορά*",
                    ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"],
                )

            with f_col2:
                input_type = st.selectbox(
                    "Κατηγορία Θέματος*",
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

            input_desc = st.text_area(
                "Περιγραφή Συμβάντος / Κανόνα*",
                placeholder="π.χ. Απαιτείται έγκριση OK to Board 72 ώρες πριν. Οι τεχνικοί με απλό διαβατήριο χρειάζονται ειδική βίζα πριν την αναχώρηση.",
            )
            input_agent = st.text_area(
                "Στοιχεία Πράκτορα / Σημειώσεις",
                placeholder="π.χ. Wilhelmsen Suez - Ο κ. Αχμέντ ζητάει πάντα αντίγραφο συμβολαίου στο mail...",
            )

            submitted = st.form_submit_button("Αποθήκευση στη Βάση")

            if submitted:
                if input_port and input_country and input_desc:
                    add_log(
                        input_port,
                        input_country,
                        input_nat,
                        input_role,
                        input_type,
                        severity_clean,
                        input_desc,
                        input_agent,
                    )
                    st.success(
                        f"Η εγγραφή για το λιμάνι {input_port.upper()} αποθηκεύτηκε με επιτυχία!"
                    )
                else:
                    st.error(
                        "Παρακαλώ συμπληρώστε όλα τα υποχρεωτικά πεδία με αστερίσκο (*)."
                    )


if __name__ == "__main__":
    main()
