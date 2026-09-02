import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# 0. ΑΣΦΑΛΕΙΑ & THEMING
# ---------------------------------------------------------
def apply_custom_theme():
    with st.sidebar:
        st.markdown("### 🎨 Εμφάνιση & Θέμα")
        theme_choice = st.selectbox(
            "Επιλέξτε Θέμα (Theme):",
            ["Dark (Σκούρο)", "Light (Φωτεινό)", "Pink (Ροζ)"],
            index=0,
        )

    if theme_choice == "Dark (Σκούρο)":
        bg_color = "#121214"
        card_bg = "#1E1E24"
        text_color = "#E4E6EB"
        label_color = "#FFFFFF"
        border_color = "#3A3A4C"
        accent_color = "#3B82F6"
        input_bg = "#22222A"
        input_text = "#FFFFFF"
        placeholder_color = "#9CA3AF"
        header_color = "#60A5FA"
        tab_unselected = "#9CA3AF"
    elif theme_choice == "Light (Φωτεινό)":
        bg_color = "#F8FAFC"
        card_bg = "#FFFFFF"
        text_color = "#1E293B"
        label_color = "#0F172A"
        border_color = "#CBD5E1"
        accent_color = "#2563EB"
        input_bg = "#FFFFFF"
        input_text = "#0F172A"
        placeholder_color = "#64748B"
        header_color = "#1D4ED8"
        tab_unselected = "#64748B"
    else:  # Pink Theme
        bg_color = "#FFF0F5"
        card_bg = "#FFFFFF"
        text_color = "#4A1525"
        label_color = "#831843"
        border_color = "#FBCFE8"
        accent_color = "#DB2777"
        input_bg = "#FFFFFF"
        input_text = "#831843"
        placeholder_color = "#9D4C6C"
        header_color = "#BE185D"
        tab_unselected = "#9D4C6C"

    css = f"""
    <style>
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        h1, h2, h3 {{
            color: {header_color} !important;
            font-weight: 700 !important;
        }}
        
        label, div[data-testid="stMarkdownContainer"] p {{
            color: {label_color} !important;
            font-weight: 600 !important;
        }}
        
        .stTextInput input, .stTextArea textarea {{
            background-color: {input_bg} !important;
            color: {input_text} !important;
            border-radius: 8px !important;
            border: 1.5px solid {border_color} !important;
        }}
        
        ::placeholder {{
            color: {placeholder_color} !important;
            opacity: 0.8 !important;
        }}

        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            color: {input_text} !important;
            border-radius: 8px !important;
            border: 1.5px solid {border_color} !important;
        }}
        div[data-baseweb="select"] span {{
            color: {input_text} !important;
        }}
        
        .stButton>button {{
            background-color: {accent_color} !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.2rem !important;
            box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.12) !important;
        }}
        .stButton>button:hover {{
            opacity: 0.9 !important;
            transform: translateY(-1px);
        }}
        
        button[data-baseweb="tab"] p {{
            color: {tab_unselected} !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }}
        button[aria-selected="true"] p {{
            color: {accent_color} !important;
            font-weight: 700 !important;
        }}
        button[aria-selected="true"] {{
            border-bottom: 3px solid {accent_color} !important;
        }}

        .custom-card {{
            background-color: {card_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 12px !important;
            padding: 18px !important;
            margin-bottom: 15px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        
        .badge-critical {{
            background-color: #EF4444; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.82rem;
        }}
        .badge-high {{
            background-color: #F97316; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.82rem;
        }}
        .badge-medium {{
            background-color: #EAB308; color: black; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.82rem;
        }}
        .badge-low {{
            background-color: #10B981; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.82rem;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


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
            signer_type TEXT DEFAULT 'BOTH',
            nationality TEXT NOT NULL,
            role TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            desc_on TEXT,
            desc_off TEXT,
            required_docs TEXT,
            req_docs_on TEXT,
            req_docs_off TEXT,
            agent_details TEXT,
            contact_email TEXT,
            date_logged TEXT NOT NULL
        )
    """
    )

    cursor.execute("PRAGMA table_info(port_logs)")
    columns = [col[1] for col in cursor.fetchall()]

    if "signer_type" not in columns:
        cursor.execute(
            "ALTER TABLE port_logs ADD COLUMN signer_type TEXT DEFAULT 'BOTH'"
        )
    if "desc_on" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN desc_on TEXT")
    if "desc_off" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN desc_off TEXT")
    if "req_docs_on" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN req_docs_on TEXT")
    if "req_docs_off" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN req_docs_off TEXT")

    conn.commit()
    conn.close()


def add_log(
    port_name,
    country,
    nationality,
    role,
    issue_type,
    severity,
    desc_on,
    desc_off,
    req_docs_on,
    req_docs_off,
    agent_details,
    contact_email,
):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    combined_desc = f"ON: {desc_on}\nOFF: {desc_off}".strip()
    combined_docs = f"ON: {req_docs_on}\nOFF: {req_docs_off}".strip()
    signer_type_val = "BOTH"

    cursor.execute(
        """
        INSERT INTO port_logs 
        (port_name, country, signer_type, nationality, role, issue_type, severity, description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            port_name.strip().upper(),
            country.strip().upper(),
            signer_type_val,
            nationality,
            role,
            issue_type,
            severity,
            combined_desc,
            desc_on,
            desc_off,
            combined_docs,
            req_docs_on,
            req_docs_off,
            agent_details,
            contact_email,
            today_str,
        ),
    )
    conn.commit()
    conn.close()


def update_log(
    log_id,
    port_name,
    country,
    nationality,
    role,
    issue_type,
    severity,
    desc_on,
    desc_off,
    req_docs_on,
    req_docs_off,
    agent_details,
    contact_email,
):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    combined_desc = f"ON: {desc_on}\nOFF: {desc_off}".strip()
    combined_docs = f"ON: {req_docs_on}\nOFF: {req_docs_off}".strip()
    signer_type_val = "BOTH"

    cursor.execute(
        """
        UPDATE port_logs 
        SET port_name=?, country=?, signer_type=?, nationality=?, role=?, issue_type=?, severity=?, 
            description=?, desc_on=?, desc_off=?, required_docs=?, req_docs_on=?, req_docs_off=?, agent_details=?, contact_email=?
        WHERE id=?
    """,
        (
            port_name.strip().upper(),
            country.strip().upper(),
            signer_type_val,
            nationality,
            role,
            issue_type,
            severity,
            combined_desc,
            desc_on,
            desc_off,
            combined_docs,
            req_docs_on,
            req_docs_off,
            agent_details,
            contact_email,
            log_id,
        ),
    )
    conn.commit()
    conn.close()


def delete_log(log_id):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM port_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()


def fetch_all_logs():
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, port_name, country, signer_type, nationality, role, issue_type, severity, 
               description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged 
        FROM port_logs 
        ORDER BY id DESC
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_logs(query_text, nationality=None, role=None):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    sql = """
        SELECT id, port_name, country, signer_type, nationality, role, issue_type, severity, 
               description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged 
        FROM port_logs WHERE 1=1
    """
    params = []

    if query_text:
        search_pattern = f"%{query_text.strip().upper()}%"
        sql += """ AND (
            UPPER(port_name) LIKE ? 
            OR UPPER(country) LIKE ? 
            OR UPPER(COALESCE(description,'')) LIKE ?
            OR UPPER(COALESCE(desc_on,'')) LIKE ?
            OR UPPER(COALESCE(desc_off,'')) LIKE ?
            OR UPPER(COALESCE(agent_details,'')) LIKE ? 
            OR UPPER(COALESCE(required_docs,'')) LIKE ?
            OR UPPER(COALESCE(req_docs_on,'')) LIKE ?
            OR UPPER(COALESCE(req_docs_off,'')) LIKE ?
        )"""
        params.extend([search_pattern] * 9)

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
# 2. HELPER FUNCTIONS: UI COMPONENTS
# ---------------------------------------------------------
def get_severity_badge(severity):
    sev = severity.upper()
    if "CRITICAL" in sev:
        return '<span class="badge-critical">🔴 CRITICAL</span>'
    elif "HIGH" in sev:
        return '<span class="badge-high">🟠 HIGH</span>'
    elif "MEDIUM" in sev:
        return '<span class="badge-medium">🟡 MEDIUM</span>'
    else:
        return '<span class="badge-low">🟢 LOW</span>'


def render_metrics_summary(logs):
    total_logs = len(logs)
    total_ports = len(set([l[1] for l in logs]))
    total_countries = len(set([l[2] for l in logs]))
    critical_count = len(
        [
            l
            for l in logs
            if "CRITICAL" in str(l[7]).upper() or "HIGH" in str(l[7]).upper()
        ]
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📍 Καταγεγραμμένα Λιμάνια", total_ports)
    m2.metric("🌍 Χώρες", total_countries)
    m3.metric("📝 Σύνολο Οδηγιών", total_logs)
    m4.metric(
        "⚠️ Υψηλού Κινδύνου / Alerts", critical_count, delta_color="inverse"
    )


def render_single_log_card(log):
    """Εμφανίζει μία συγκεκριμένη υποθετική εγγραφή με καθαρή διάταξη On/Off δίπλα-δίπλα"""
    log_id = log[0]
    p_name = log[1]
    country = log[2]
    nat = log[4]
    role = log[5]
    i_type = log[6]
    severity = log[7]
    old_desc = log[8] if log[8] else ""
    desc_on = log[9] if log[9] else ""
    desc_off = log[10] if log[10] else ""
    old_docs = log[11] if log[11] else ""
    docs_on = log[12] if log[12] else ""
    docs_off = log[13] if log[13] else ""
    agent = log[14] if log[14] else ""
    c_email = log[15] if log[15] else ""
    date_logged = log[16] if log[16] else ""

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(
            f"**Case #{log_id}:** 👥 **{nat}** | 💼 **{role}** | 🏷️ `{i_type}`"
        )
        st.caption(f"📅 Ημερομηνία Καταγραφής: {date_logged}")
    with c_head2:
        st.markdown(get_severity_badge(severity), unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    # On-signers Column
    with col_left:
        st.markdown("🟢 **ON-SIGNERS (Επιβίβαση)**")
        if desc_on and desc_on.strip():
            st.info(f"**Οδηγίες:**\n{desc_on}")
        if docs_on and docs_on.strip():
            st.markdown("**📋 Απαιτούμενα Έγγραφα:**")
            for doc in [d.strip() for d in docs_on.split(",") if d.strip()]:
                st.markdown(f"- 📄 {doc}")
        if not (desc_on or docs_on):
            st.caption("— Καμία ειδική οδηγία επιβίβασης —")

    # Off-signers Column
    with col_right:
        st.markdown("🔴 **OFF-SIGNERS (Αποβίβαση)**")
        if desc_off and desc_off.strip():
            st.warning(f"**Οδηγίες:**\n{desc_off}")
        if docs_off and docs_off.strip():
            st.markdown("**📋 Απαιτούμενα Έγγραφα:**")
            for doc in [d.strip() for d in docs_off.split(",") if d.strip()]:
                st.markdown(f"- 📄 {doc}")
        if not (desc_off or docs_off):
            st.caption("— Καμία ειδική οδηγία αποβίβασης —")

    # Fallback για παλιές εγγραφές
    if old_desc and old_desc.strip() and not (desc_on or desc_off):
        st.markdown("📝 **Γενική Περιγραφή / Οδηγίες:**")
        st.write(old_desc)
    if old_docs and old_docs.strip() and not (docs_on or docs_off):
        st.markdown("📋 **Γενικά Απαιτούμενα Έγγραφα:**")
        for doc in [d.strip() for d in old_docs.split(",") if d.strip()]:
            st.markdown(f"- 📄 {doc}")

    if (agent and agent.strip()) or (c_email and c_email.strip()):
        st.markdown("---")
        st.markdown("##### 📞 Στοιχεία Πράκτορα & Επικοινωνία")
        if agent and agent.strip():
            st.write(f"**Σημειώσεις Πράκτορα:** {agent}")
        if c_email and c_email.strip():
            st.write(f"**Email / Contact:** `{c_email}`")

    st.markdown("</div>", unsafe_allow_html=True)


def generate_excel_export(logs):
    df = pd.DataFrame(
        logs,
        columns=[
            "ID",
            "Port",
            "Country",
            "Signer Type",
            "Nationality",
            "Role",
            "Issue Type",
            "Severity",
            "General Desc",
            "Desc ON",
            "Desc OFF",
            "General Docs",
            "Docs ON",
            "Docs OFF",
            "Agent Details",
            "Contact Email",
            "Date Logged",
        ],
    )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Port Rules")
    return buffer.getvalue()


# ---------------------------------------------------------
# 3. STREAMLIT INTERFACE
# ---------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Crew Operations & Port Intelligence",
        page_icon="⚓",
        layout="wide",
    )

    apply_custom_theme()

    if not check_password():
        return

    init_db()

    with st.sidebar:
        st.title("⚓ Operations Hub")
        st.markdown("---")

        all_db_logs = fetch_all_logs()
        if all_db_logs:
            excel_data = generate_excel_export(all_db_logs)
            st.download_button(
                label="📥 Εξαγωγή Βάσης σε Excel",
                data=excel_data,
                file_name=f"Crew_Port_Rules_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown("---")
        st.write("👤 Συνδεδεμένος Χρήστης")
        if st.button("Αποσύνδεση (Logout)"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.title("⚓ Crew Operations & Port Intelligence System")
    st.caption(
        "Κεντρικό σύστημα παρακολούθησης κανόνων λιμανιών, γραφειοκρατίας & ταξιδιωτικών απαιτήσεων."
    )

    all_logs = fetch_all_logs()
    if all_logs:
        render_metrics_summary(all_logs)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🔍 Αναζήτηση & Alerts",
            "🌍 Ευρετήριο Χωρών",
            "➕ Νέα Καταχώρηση",
            "✏️ Επεξεργασία & Διαγραφή",
        ]
    )

    # -----------------------------------------------------
    # TAB 1: ΑΝΑΖΗΤΗΣΗ & ALERTS
    # -----------------------------------------------------
    with tab1:
        st.subheader("🔍 Έλεγχος Λιμανιού & Ιστορικού")

        col1, col2, col3 = st.columns(3)
        with col1:
            search_query = st.text_input(
                "Λιμάνι, Χώρα ή Λέξη-Κλειδί:",
                placeholder="e.g. Singapore, Garyville, US C1/D",
            )
        with col2:
            search_nat = st.selectbox(
                "Εθνικότητα:", ["Όλες", "Έλληνας", "Φιλιππινέζος"]
            )
        with col3:
            search_role = st.selectbox(
                "Ιδιότητα:", ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"]
            )

        if st.button("🔎 Έλεγχος Ιστορικού"):
            if search_query:
                logs = search_logs(search_query, search_nat, search_role)

                if logs:
                    st.success(
                        f"⚠️ Βρέθηκαν {len(logs)} καταγεγραμμένες σημειώσεις για '{search_query.upper()}'."
                    )
                    for log in logs:
                        render_single_log_card(log)
                else:
                    st.info("Δεν βρέθηκαν αποτελέσματα στη βάση.")
            else:
                st.info(
                    "Παρακαλώ πληκτρολογήστε όνομα λιμανιού, χώρας ή λέξη-κλειδί."
                )

    # -----------------------------------------------------
    # TAB 2: ΕΥΡΕΤΗΡΙΟ ΧΩΡΩΝ (ΟΜΑΔΟΠΟΙΗΜΕΝΟ ΑΝΑ ΛΙΜΑΝΙ)
    # -----------------------------------------------------
    with tab2:
        st.subheader("🌍 Κατάλογος Χωρών & Οργάνωση ανά Λιμάνι")

        if all_logs:
            countries = sorted(list(set([l[2] for l in all_logs if l[2]])))

            if countries:
                selected_country = st.selectbox(
                    "📌 Επιλέξτε Χώρα από τη λίστα:",
                    countries,
                )

                if selected_country:
                    country_logs = [
                        l for l in all_logs if l[2] == selected_country
                    ]
                    ports_in_country = sorted(
                        list(set([l[1] for l in country_logs]))
                    )

                    st.markdown(
                        f"### 📍 Χώρα: **{selected_country}** ({len(ports_in_country)} Λιμάνια)"
                    )
                    st.write(
                        "Πατήστε σε ένα λιμάνι για να δείτε τις καταχωρημένες υποθέσεις του:"
                    )

                    # Ομαδοποίηση και προβολή ανά Λιμάνι
                    for port in ports_in_country:
                        port_specific_logs = [
                            l for l in country_logs if l[1] == port
                        ]

                        with st.expander(
                            f"⚓ **ΛΙΜΑΝΙ: {port}** ({len(port_specific_logs)} Υποθέσεις)",
                            expanded=True,
                        ):
                            for log in port_specific_logs:
                                render_single_log_card(log)
            else:
                st.info("Δεν έχουν καταχωρηθεί ακόμη χώρες.")
        else:
            st.info(
                "⚠️ Η βάση δεδομένων είναι ακόμα κενή. Προσθέστε μια καταχώρηση στο Tab '➕ Νέα Καταχώρηση'."
            )

    # -----------------------------------------------------
    # TAB 3: ΝΕΑ ΚΑΤΑΧΩΡΗΣΗ
    # -----------------------------------------------------
    with tab3:
        st.subheader("➕ Καταχώρηση Νέων Οδηγιών / Δυσκολιών")

        with st.form("add_log_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                input_port = st.text_input(
                    "Όνομα Λιμανιού* (π.χ. Singapore, Garyville)"
                )
                input_country = st.text_input("Χώρα* (π.χ. Singapore, USA)")
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
                    default=["Visa / Schengen / US C1-D"],
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
            st.markdown("#### 📝 Οδηγίες & Απαιτούμενα Έγγραφα")

            col_on, col_off = st.columns(2)
            with col_on:
                input_desc_on = st.text_area(
                    "🟢 Οδηγίες για ON-SIGNERS (Επιβίβαση)",
                    placeholder="Π.χ. Απαιτείται OK to Board 48h πριν, ESTA, Guarantee Letter...",
                    height=120,
                )
                input_docs_on = st.text_input(
                    "📋 Απαιτούμενα Έγγραφα (ON-SIGNERS)",
                    placeholder="π.χ. US C1/D Visa, Flight Ticket, Guarantee Letter",
                )

            with col_off:
                input_desc_off = st.text_area(
                    "🔴 Οδηγίες για OFF-SIGNERS (Αποβίβαση)",
                    placeholder="Π.χ. Δεν επιτρέπεται shore leave, απαιτείται συνοδεία πράκτορα στο αεροδρόμιο...",
                    height=120,
                )
                input_docs_off = st.text_input(
                    "📋 Απαιτούμενα Έγγραφα (OFF-SIGNERS)",
                    placeholder="π.χ. Transit Visa, Exit Stamp, SIRB",
                )

            st.markdown("---")
            col_agent1, col_agent2 = st.columns(2)
            with col_agent1:
                input_agent = st.text_area("Στοιχεία Πράκτορα / Σημειώσεις")
            with col_agent2:
                input_email = st.text_input("📧 Contact Email")

            submitted = st.form_submit_button("💾 Αποθήκευση στη Βάση")

            if submitted:
                if (
                    input_port
                    and input_country
                    and input_types
                    and (
                        input_desc_on
                        or input_desc_off
                        or input_docs_on
                        or input_docs_off
                    )
                ):
                    types_str = ", ".join(input_types)
                    add_log(
                        input_port,
                        input_country,
                        input_nat,
                        input_role,
                        types_str,
                        severity_clean,
                        input_desc_on,
                        input_desc_off,
                        input_docs_on,
                        input_docs_off,
                        input_agent,
                        input_email,
                    )
                    st.success("✅ Η εγγραφή αποθηκεύτηκε επιτυχώς στη βάση!")
                    st.rerun()
                else:
                    st.error(
                        "❌ Παρακαλώ συμπληρώστε τα υποχρεωτικά πεδία (*) και τουλάχιστον μία οδηγία ή έγγραφο."
                    )

    # -----------------------------------------------------
    # TAB 4: ΕΠΕΞΕΡΓΑΣΙΑ & ΔΙΑΓΡΑΦΗ
    # -----------------------------------------------------
    with tab4:
        st.subheader("✏️ Επεξεργασία & Διόρθωση Εγγραφών")
        all_logs_edit = fetch_all_logs()

        if not all_logs_edit:
            st.info("Δεν υπάρχουν εγγραφές στη βάση για επεξεργασία.")
        else:
            log_options = {
                f"#{l[0]} - {l[1]} ({l[2]}) [{l[6]}]": l for l in all_logs_edit
            }
            selected_option = st.selectbox(
                "Επιλέξτε εγγραφή για τροποποίηση:", list(log_options.keys())
            )

            selected_log = log_options[selected_option]

            e_id = selected_log[0]
            e_port = selected_log[1]
            e_country = selected_log[2]
            e_nat = selected_log[4]
            e_role = selected_log[5]
            e_type = selected_log[6]
            e_severity = selected_log[7]
            e_old_desc = selected_log[8] if selected_log[8] else ""
            e_desc_on = selected_log[9] if selected_log[9] else ""
            e_desc_off = selected_log[10] if selected_log[10] else ""
            e_old_docs = selected_log[11] if selected_log[11] else ""
            e_docs_on = selected_log[12] if selected_log[12] else ""
            e_docs_off = selected_log[13] if selected_log[13] else ""
            e_agent = selected_log[14] if selected_log[14] else ""
            e_email = selected_log[15] if selected_log[15] else ""

            if not e_desc_on and not e_desc_off and e_old_desc:
                e_desc_on = e_old_desc
            if not e_docs_on and not e_docs_off and e_old_docs:
                e_docs_on = e_old_docs

            st.markdown("---")
            with st.form("edit_log_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_port = st.text_input("Όνομα Λιμανιού", value=e_port)
                    edit_country = st.text_input("Χώρα", value=e_country)
                    edit_nat = st.selectbox(
                        "Εθνικότητα",
                        ["Όλες", "Έλληνας", "Φιλιππινέζος"],
                        index=["Όλες", "Έλληνας", "Φιλιππινέζος"].index(e_nat)
                        if e_nat in ["Όλες", "Έλληνας", "Φιλιππινέζος"]
                        else 0,
                    )

                with ec2:
                    edit_role = st.selectbox(
                        "Ιδιότητα",
                        ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"],
                        index=[
                            "Όλοι",
                            "Πλήρωμα",
                            "Superintendent",
                            "Τεχνικός",
                        ].index(e_role)
                        if e_role
                        in ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"]
                        else 0,
                    )

                    all_categories = [
                        "OK to Board Issue",
                        "Visa / Schengen / US C1-D",
                        "Seaman's Book / Transit",
                        "Shore Leave Restriction",
                        "Customs / Technical Equipment",
                        "Agent Negligence / Delay",
                        "Άλλο",
                    ]
                    current_cats = [
                        c.strip()
                        for c in e_type.split(",")
                        if c.strip() in all_categories
                    ]
                    edit_types = st.multiselect(
                        "Κατηγορίες Θέματος",
                        all_categories,
                        default=current_cats
                        if current_cats
                        else [all_categories[0]],
                    )

                    sev_index = 0
                    if e_severity == "Medium":
                        sev_index = 1
                    elif e_severity == "High":
                        sev_index = 2
                    elif e_severity == "Critical":
                        sev_index = 3

                    edit_severity = st.selectbox(
                        "Επίπεδο Σοβαρότητας",
                        [
                            "Low (Απλή πληροφορία)",
                            "Medium (Προσοχή)",
                            "High (Μεγάλη δυσκολία)",
                            "Critical (Απαγόρευση)",
                        ],
                        index=sev_index,
                    )
                    edit_sev_clean = edit_severity.split()[0]

                st.markdown("---")
                col_e_on, col_e_off = st.columns(2)
                with col_e_on:
                    edit_desc_on = st.text_area(
                        "🟢 Οδηγίες για ON-SIGNERS (Επιβίβαση)",
                        value=e_desc_on,
                        height=120,
                    )
                    edit_docs_on = st.text_input(
                        "📋 Απαιτούμενα Έγγραφα (ON-SIGNERS)",
                        value=e_docs_on,
                    )

                with col_e_off:
                    edit_desc_off = st.text_area(
                        "🔴 Οδηγίες για OFF-SIGNERS (Αποβίβαση)",
                        value=e_desc_off,
                        height=120,
                    )
                    edit_docs_off = st.text_input(
                        "📋 Απαιτούμενα Έγγραφα (OFF-SIGNERS)",
                        value=e_docs_off,
                    )

                st.markdown("---")
                ec_a1, ec_a2 = st.columns(2)
                with ec_a1:
                    edit_agent = st.text_area(
                        "Στοιχεία Πράκτορα / Σημειώσεις",
                        value=e_agent,
                    )
                with ec_a2:
                    edit_email = st.text_input(
                        "📧 Contact Email",
                        value=e_email,
                    )

                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    update_submitted = st.form_submit_button(
                        "💾 Ενημέρωση Εγγραφής"
                    )
                with col_btn2:
                    delete_submitted = st.form_submit_button(
                        "🗑️ Διαγραφή Εγγραφής"
                    )

                if update_submitted:
                    types_str = ", ".join(edit_types)
                    update_log(
                        e_id,
                        edit_port,
                        edit_country,
                        edit_nat,
                        edit_role,
                        types_str,
                        edit_sev_clean,
                        edit_desc_on,
                        edit_desc_off,
                        edit_docs_on,
                        edit_docs_off,
                        edit_agent,
                        edit_email,
                    )
                    st.success(f"✅ Η εγγραφή #{e_id} ενημερώθηκε επιτυχώς!")
                    st.rerun()

                if delete_submitted:
                    delete_log(e_id)
                    st.warning(f"🗑️ Η εγγραφή #{e_id} διαγράφηκε.")
                    st.rerun()


if __name__ == "__main__":
    main()
