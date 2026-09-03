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
VESSEL_LIST = ["MT GEA", "MT ESTIA", "MT ORFEAS", "MT EVRIDIKI"]


def init_db():
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS port_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vessel_name TEXT,
            case_title TEXT,
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

    if "vessel_name" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN vessel_name TEXT DEFAULT ''")
    if "case_title" not in columns:
        cursor.execute("ALTER TABLE port_logs ADD COLUMN case_title TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def add_log(
    vessel_name,
    case_title,
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

    cursor.execute(
        """
        INSERT INTO port_logs 
        (vessel_name, case_title, port_name, country, signer_type, nationality, role, issue_type, severity, description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged)
        VALUES (?, ?, ?, ?, 'BOTH', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            vessel_name,
            case_title.strip(),
            port_name.strip().upper(),
            country.strip().upper(),
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
    vessel_name,
    case_title,
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

    cursor.execute(
        """
        UPDATE port_logs 
        SET vessel_name=?, case_title=?, port_name=?, country=?, nationality=?, role=?, issue_type=?, severity=?, 
            description=?, desc_on=?, desc_off=?, required_docs=?, req_docs_on=?, req_docs_off=?, agent_details=?, contact_email=?
        WHERE id=?
    """,
        (
            vessel_name,
            case_title.strip(),
            port_name.strip().upper(),
            country.strip().upper(),
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
        SELECT id, vessel_name, case_title, port_name, country, signer_type, nationality, role, issue_type, severity, 
               description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged 
        FROM port_logs 
        ORDER BY id DESC
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_logs(query_text, nationality=None, role=None, vessel=None):
    conn = sqlite3.connect("crew_port_rules.db")
    cursor = conn.cursor()

    sql = """
        SELECT id, vessel_name, case_title, port_name, country, signer_type, nationality, role, issue_type, severity, 
               description, desc_on, desc_off, required_docs, req_docs_on, req_docs_off, agent_details, contact_email, date_logged 
        FROM port_logs WHERE 1=1
    """
    params = []

    if vessel and vessel != "Όλα":
        sql += " AND vessel_name = ?"
        params.append(vessel)

    if query_text:
        search_pattern = f"%{query_text.strip().upper()}%"
        sql += """ AND (
            UPPER(port_name) LIKE ? 
            OR UPPER(country) LIKE ? 
            OR UPPER(COALESCE(case_title,'')) LIKE ?
            OR UPPER(COALESCE(description,'')) LIKE ?
            OR UPPER(COALESCE(desc_on,'')) LIKE ?
            OR UPPER(COALESCE(desc_off,'')) LIKE ?
            OR UPPER(COALESCE(agent_details,'')) LIKE ? 
            OR UPPER(COALESCE(required_docs,'')) LIKE ?
            OR UPPER(COALESCE(req_docs_on,'')) LIKE ?
            OR UPPER(COALESCE(req_docs_off,'')) LIKE ?
        )"""
        params.extend([search_pattern] * 10)

    if nationality and nationality != "Όλες":
        sql += " AND (nationality = ? OR nationality = 'Όλες')"
        params.append(nationality)

    if role and role != "Όλοι":
        if role.upper() == "CREW":
            sql += " AND (role = 'Πλήρωμα' OR role = 'Όλοι')"
        elif role.upper() == "SUPTS":
            sql += " AND (role = 'Superintendent' OR role = 'Όλοι')"
        elif role.upper() == "TECHNICIANS":
            sql += " AND (role = 'Τεχνικός' OR role = 'Όλοι')"
        else:
            sql += " AND (role = ? OR role = 'Όλοι')"
            params.append(role)

    sql += " ORDER BY id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# 2. HELPER FUNCTIONS: UI COMPONENTS & METRICS
# ---------------------------------------------------------
def get_severity_badge(severity):
    sev = str(severity).upper()
    if "CRITICAL" in sev:
        return '<span class="badge-critical">🔴 CRITICAL</span>'
    elif "HIGH" in sev:
        return '<span class="badge-high">🟠 HIGH</span>'
    elif "MEDIUM" in sev:
        return '<span class="badge-medium">🟡 MEDIUM</span>'
    else:
        return '<span class="badge-low">🟢 LOW</span>'


def render_kpi_dashboard(logs):
    total_logs = len(logs)
    total_ports = len(set([l[3] for l in logs]))
    total_countries = len(set([l[4] for l in logs]))
    critical_count = len([l for l in logs if "CRITICAL" in str(l[9]).upper() or "HIGH" in str(l[9]).upper()])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📍 Καταγεγραμμένα Λιμάνια", total_ports)
    m2.metric("🌍 Χώρες", total_countries)
    m3.metric("📝 Σύνολο Οδηγιών / Cases", total_logs)
    m4.metric("⚠️ Υψηλού Κινδύνου / Alerts", critical_count)


def render_single_log_card(log):
    log_id = log[0]
    vessel = log[1] if log[1] else "N/A"
    case_title = log[2] if log[2] else ""
    p_name = log[3]
    country = log[4]
    nat = log[6]
    role = log[7]
    i_type = log[8]
    severity = log[9]
    old_desc = log[10] if log[10] else ""
    desc_on = log[11] if log[11] else ""
    desc_off = log[12] if log[12] else ""
    old_docs = log[13] if log[13] else ""
    docs_on = log[14] if log[14] else ""
    docs_off = log[15] if log[15] else ""
    agent = log[16] if log[16] else ""
    c_email = log[17] if log[17] else ""
    date_logged = log[18] if log[18] else ""

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)

    if case_title:
        st.markdown(f"### 🏷️ `{case_title}`")

    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(
            f"**Case #{log_id}:** 🚢 **{vessel}** | 👥 **{nat}** | 💼 **{role}** | 🏷️ `{i_type}`"
        )
        st.caption(f"📅 Ημερομηνία Καταγραφής: {date_logged} | 📍 Λιμάνι: {p_name}, {country}")
    with c_head2:
        st.markdown(get_severity_badge(severity), unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

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
            "Vessel",
            "Case Title / Subject",
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

    # Sidebar
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

    # Main Header
    st.title("⚓ Crew Operations & Port Intelligence System")
    st.caption("Κεντρικό σύστημα παρακολούθησης κανόνων λιμανιών, γραφειοκρατίας & ταξιδιωτικών απαιτήσεων.")

    # 📊 KPI Metrics Dashboard
    all_logs = fetch_all_logs()
    if all_logs:
        render_kpi_dashboard(all_logs)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🔍 Αναζήτηση & Cases",
            "🌍 Ευρετήριο Χωρών & Πλοίων",
            "➕ Νέα Καταχώρηση Case",
            "✏️ Επεξεργασία & Διαγραφή",
        ]
    )

    # -----------------------------------------------------
    # TAB 1: ΑΝΑΖΗΤΗΣΗ & CASES
    # -----------------------------------------------------
    with tab1:
        st.subheader("🔍 Έλεγχος Λιμανιού, Πλοίου & Cases")

        # Quick Role Chips Filter
        st.markdown("**⚡ Γρήγορο Φίλτρο Ιδιότητας:**")
        quick_role = st.radio(
            "Επιλέξτε Κατηγορία:",
            ["ALL", "CREW", "SUPTS", "TECHNICIANS"],
            horizontal=True,
            label_visibility="collapsed",
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search_vessel = st.selectbox("🚢 Πλοίο:", ["Όλα"] + VESSEL_LIST)
        with col2:
            search_query = st.text_input(
                "Λιμάνι, Χώρα, Τίτλος ή Keyword:",
                placeholder="e.g. Panama, EVRI-OF-50963, Visa",
            )
        with col3:
            search_nat = st.selectbox(
                "Εθνικότητα:", ["Όλες", "Έλληνας", "Φιλιππινέζος"]
            )
        with col4:
            role_options = ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"]
            default_index = 0
            if quick_role == "CREW":
                default_index = 1
            elif quick_role == "SUPTS":
                default_index = 2
            elif quick_role == "TECHNICIANS":
                default_index = 3

            search_role = st.selectbox(
                "Ιδιότητα:", role_options, index=default_index
            )

        if st.button("🔎 Έλεγχος Ιστορικού / Cases"):
            if search_query or search_role != "Όλοι" or search_nat != "Όλες" or search_vessel != "Όλα":
                logs = search_logs(search_query, search_nat, search_role, search_vessel)

                if logs:
                    st.success(f"⚠️ Βρέθηκαν {len(logs)} καταγεγραμμένες υποθέσεις / cases.")
                    for log in logs:
                        render_single_log_card(log)
                else:
                    st.info("Δεν βρέθηκαν αποτελέσματα στη βάση.")
            else:
                st.info("Παρακαλώ εισάγετε όνομα λιμανιού, τίτλο case ή επιλέξτε κάποιο φίλτρο.")

    # -----------------------------------------------------
    # TAB 2: ΕΥΡΕΤΗΡΙΟ ΧΩΡΩΝ & ΠΛΟΙΩΝ
    # -----------------------------------------------------
    with tab2:
        st.subheader("🌍 Κατάλογος Χωρών & Οργάνωση ανά Λιμάνι")

        if all_logs:
            countries = sorted(list(set([l[4] for l in all_logs if l[4]])))

            if countries:
                selected_country = st.selectbox(
                    "📌 Επιλέξτε Χώρα από τη λίστα:",
                    countries,
                )

                if selected_country:
                    country_logs = [l for l in all_logs if l[4] == selected_country]
                    ports_in_country = sorted(list(set([l[3] for l in country_logs])))

                    st.markdown(
                        f"### 📍 Χώρα: **{selected_country}** ({len(ports_in_country)} Λιμάνια)"
                    )

                    for port in ports_in_country:
                        port_specific_logs = [l for l in country_logs if l[3] == port]

                        with st.expander(
                            f"⚓ **ΛΙΜΑΝΙ: {port}** ({len(port_specific_logs)} Υποθέσεις / Cases)",
                            expanded=False,
                        ):
                            # Δημιουργία λίστας με επιλογή "-- Επιλέξτε Case / Ταξίδι --" στην αρχή
                            case_options_dict = {
                                f"{l[1]} - {l[2] if l[2] else 'Case #'+str(l[0])} ({l[18]})": l
                                for l in port_specific_logs
                            }
                            
                            select_placeholder = "-- Επιλέξτε Case / Ταξίδι --"
                            options_list = [select_placeholder] + list(case_options_dict.keys())

                            selected_case_label = st.selectbox(
                                f"📋 Επιλέξτε Case/Ταξίδι στο λιμάνι {port}:",
                                options_list,
                                index=0,
                                key=f"select_case_{port}",
                            )

                            # Εμφάνιση της κάρτας ΜΟΝΟ αν ο χρήστης επιλέξει κάποιο συγκεκριμένο case
                            if selected_case_label != select_placeholder:
                                chosen_log = case_options_dict[selected_case_label]
                                render_single_log_card(chosen_log)
            else:
                st.info("Δεν έχουν καταχωρηθεί ακόμη χώρες.")
        else:
            st.info("⚠️ Η βάση δεδομένων είναι ακόμα κενή. Προσθέστε μια καταχώρηση στο Tab '➕ Νέα Καταχώρηση Case'.")

    # -----------------------------------------------------
    # TAB 3: ΝΕΑ ΚΑΤΑΧΩΡΗΣΗ CASE
    # -----------------------------------------------------
    with tab3:
        st.subheader("➕ Καταχώρηση Νέου Case / Οδηγιών")

        with st.form("add_log_form", clear_on_submit=True):
            st.markdown("#### 🚢 Στοιχεία Case & Email Subject")
            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                input_vessel = st.selectbox("Επιλογή Πλοίου*", VESSEL_LIST)
            with col_v2:
                input_case_title = st.text_input(
                    "Τίτλος Case / Subject Email*",
                    placeholder="π.χ. MT EVRIDIKI(CASE NO.EVRI-OF-50963) CREW CHANGES PANAMA ON 04/SEPTEMBER",
                )

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                input_port = st.text_input("Όνομα Λιμανιού* (π.χ. Panama, Singapore)")
                input_country = st.text_input("Χώρα* (π.χ. Panama, Singapore)")
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
                    placeholder="Π.χ. Passport received, Arrival flight received, Departure flight pending...",
                    height=120,
                )
                input_docs_on = st.text_input(
                    "📋 Απαιτούμενα Έγγραφα (ON-SIGNERS)",
                    placeholder="π.χ. PP, VISA PAGADA, US C1/D Visa",
                )

            with col_off:
                input_desc_off = st.text_area(
                    "🔴 Οδηγίες για OFF-SIGNERS (Αποβίβαση)",
                    placeholder="Π.χ. Δεν επιτρέπεται shore leave, απαιτείται συνοδεία πράκτορα...",
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

            submitted = st.form_submit_button("💾 Αποθήκευση Case στη Βάση")

            if submitted:
                if input_port and input_country and input_types and (input_desc_on or input_desc_off or input_docs_on or input_docs_off):
                    types_str = ", ".join(input_types)
                    add_log(
                        input_vessel,
                        input_case_title,
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
                    st.success("✅ Το Case αποθηκεύτηκε επιτυχώς στη βάση!")
                    st.rerun()
                else:
                    st.error("❌ Παρακαλώ συμπληρώστε τα υποχρεωτικά πεδία (*) και τουλάχιστον μία οδηγία ή έγγραφο.")

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
                f"#{l[0]} - [{l[1]}] {l[2] if l[2] else l[3]} ({l[4]})": l
                for l in all_logs_edit
            }
            selected_option = st.selectbox(
                "Επιλέξτε εγγραφή για τροποποίηση:", list(log_options.keys())
            )

            selected_log = log_options[selected_option]

            e_id = selected_log[0]
            e_vessel = selected_log[1] if selected_log[1] else VESSEL_LIST[0]
            e_case_title = selected_log[2] if selected_log[2] else ""
            e_port = selected_log[3]
            e_country = selected_log[4]
            e_nat = selected_log[6]
            e_role = selected_log[7]
            e_type = selected_log[8]
            e_severity = selected_log[9]
            e_old_desc = selected_log[10] if selected_log[10] else ""
            e_desc_on = selected_log[11] if selected_log[11] else ""
            e_desc_off = selected_log[12] if selected_log[12] else ""
            e_old_docs = selected_log[13] if selected_log[13] else ""
            e_docs_on = selected_log[14] if selected_log[14] else ""
            e_docs_off = selected_log[15] if selected_log[15] else ""
            e_agent = selected_log[16] if selected_log[16] else ""
            e_email = selected_log[17] if selected_log[17] else ""

            if not e_desc_on and not e_desc_off and e_old_desc:
                e_desc_on = e_old_desc
            if not e_docs_on and not e_docs_off and e_old_docs:
                e_docs_on = e_old_docs

            st.markdown("---")
            with st.form("edit_log_form"):
                col_ev1, col_ev2 = st.columns([1, 2])
                with col_ev1:
                    vessel_idx = VESSEL_LIST.index(e_vessel) if e_vessel in VESSEL_LIST else 0
                    edit_vessel = st.selectbox("Πλοίο", VESSEL_LIST, index=vessel_idx)
                with col_ev2:
                    edit_case_title = st.text_input("Τίτλος Case / Subject", value=e_case_title)

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
                        index=["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"].index(e_role)
                        if e_role in ["Όλοι", "Πλήρωμα", "Superintendent", "Τεχνικός"]
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
                    current_cats = [c.strip() for c in e_type.split(",") if c.strip() in all_categories]
                    edit_types = st.multiselect(
                        "Κατηγορίες Θέματος",
                        all_categories,
                        default=current_cats if current_cats else [all_categories[0]],
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
                    update_submitted = st.form_submit_button("💾 Ενημέρωση Εγγραφής")
                with col_btn2:
                    delete_submitted = st.form_submit_button("🗑️ Διαγραφή Εγγραφής")

                if update_submitted:
                    types_str = ", ".join(edit_types)
                    update_log(
                        e_id,
                        edit_vessel,
                        edit_case_title,
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
