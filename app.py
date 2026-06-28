"""
Streamlit front-end for the PostgreSQL Bank Management System.

This file is purely a UI layer. All business logic (account creation,
login, deposits, withdrawals, audit logging, deletion) is delegated to
the BankSystem / Account / Audit classes already defined in main.py,
so the app stays in sync with the underlying banking engine.
"""

import time
from datetime import datetime

import streamlit as st

from main import BankSystem, verify_pin

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Vaultline Bank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme — dark navy / gold fintech look
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
    --bg-deep: #0b1220;
    --bg-panel: #121b2e;
    --bg-panel-light: #16223a;
    --border-soft: #243352;
    --gold: #d4af6a;
    --gold-soft: #e9cf9c;
    --green: #3ecf8e;
    --red: #ef5d6f;
    --text-main: #eef2f8;
    --text-dim: #93a1bb;
}

html, body, [class*="css"]  {
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 15% 0%, #15233f 0%, #0b1220 55%) fixed;
    color: var(--text-main);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1830 0%, #0a1222 100%);
    border-right: 1px solid var(--border-soft);
}
section[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* Hero header */
.vault-hero {
    background: linear-gradient(120deg, #16223a 0%, #1b2c4d 60%, #233a63 100%);
    border: 1px solid var(--border-soft);
    border-radius: 18px;
    padding: 28px 34px;
    margin-bottom: 26px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.vault-hero h1 {
    font-size: 1.9rem;
    margin: 0;
    color: var(--text-main);
    letter-spacing: 0.5px;
}
.vault-hero .sub {
    color: var(--gold-soft);
    font-size: 0.95rem;
    margin-top: 4px;
    font-weight: 500;
}
.vault-badge {
    background: rgba(212,175,106,0.12);
    border: 1px solid rgba(212,175,106,0.4);
    color: var(--gold-soft);
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* Card panels */
.vault-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-soft);
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}
.vault-card h3 {
    margin-top: 0;
    color: var(--gold-soft);
    font-size: 1.1rem;
}

/* Balance hero card */
.balance-card {
    background: linear-gradient(135deg, #1b2c4d 0%, #0e1830 100%);
    border: 1px solid var(--gold);
    border-radius: 18px;
    padding: 30px 32px;
    text-align: left;
    box-shadow: 0 8px 24px rgba(212,175,106,0.08);
}
.balance-card .label {
    color: var(--text-dim);
    font-size: 0.85rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.balance-card .amount {
    color: var(--gold-soft);
    font-size: 2.6rem;
    font-weight: 700;
    margin: 6px 0 0 0;
}
.balance-card .acc {
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-top: 10px;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--gold) 0%, #b9914e 100%);
    color: #11192b;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    padding: 10px 18px;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
    box-shadow: 0 4px 14px rgba(212,175,106,0.18);
}
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(212,175,106,0.3);
    color: #11192b;
}
.stButton button:active {
    transform: translateY(0px);
}

/* Danger button variant via key prefix handled in markdown below buttons */
div[data-testid="stForm"] {
    background: var(--bg-panel-light);
    border: 1px solid var(--border-soft);
    border-radius: 16px;
    padding: 22px 24px 6px 24px;
}

/* Inputs */
input, textarea {
    background-color: #0e1728 !important;
    color: var(--text-main) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-soft) !important;
}

/* Metric tiles */
div[data-testid="stMetric"] {
    background: var(--bg-panel);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 14px 18px;
}
div[data-testid="stMetric"] label {
    color: var(--text-dim) !important;
}

/* Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    overflow: hidden;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: var(--text-dim);
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--gold-soft);
}

/* Alerts override tone */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

hr {
    border-color: var(--border-soft);
}

.vault-footer {
    text-align: center;
    color: var(--text-dim);
    font-size: 0.78rem;
    padding: 18px 0 6px 0;
}

.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.pill-credit { background: rgba(62,207,142,0.15); color: var(--green); }
.pill-debit { background: rgba(239,93,111,0.15); color: var(--red); }
.pill-neutral { background: rgba(147,161,187,0.15); color: var(--text-dim); }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cached bank engine (initializes tables once per session)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_bank():
    return BankSystem()


bank = get_bank()


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "logged_in": False,
        "account": None,
        "plain_pin": None,
        "admin_mode": False,
        "flash": None,  # (type, message) shown once after rerun
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def set_flash(kind, message):
    st.session_state["flash"] = (kind, message)


def show_flash():
    flash = st.session_state.get("flash")
    if flash:
        kind, message = flash
        getattr(st, kind)(message)
        st.session_state["flash"] = None


def logout():
    st.session_state["logged_in"] = False
    st.session_state["account"] = None
    st.session_state["plain_pin"] = None


def refresh_account():
    """Re-load the current account from DB so balance/name stay current."""
    acc = st.session_state.get("account")
    pin = st.session_state.get("plain_pin")
    if acc and pin:
        fresh = bank.read_account(acc.get_account_number(), pin)
        if fresh:
            st.session_state["account"] = fresh
    return st.session_state.get("account")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
def render_header(subtitle):
    st.markdown(
        f"""
        <div class="vault-hero">
            <div>
                <h1>🏦 Vaultline Bank</h1>
                <div class="sub">{subtitle}</div>
            </div>
            <div class="vault-badge">SECURE • POSTGRESQL BACKED</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Public area: create account / login / admin
# ---------------------------------------------------------------------------
def render_public_area():
    render_header("Open an account or log in to manage your money")
    show_flash()

    tab_login, tab_create, tab_admin = st.tabs(
        ["🔐 Login", "🆕 Create Account", "🛠️ Admin"]
    )

    # ---------------- Login ----------------
    with tab_login:
        st.markdown('<div class="vault-card">', unsafe_allow_html=True)
        st.markdown("### Welcome back")
        st.caption("Enter your account number and 4-digit PIN to continue.")
        with st.form("login_form", clear_on_submit=False):
            acc_num = st.text_input("Account Number", placeholder="e.g. 1KFQ99EYA8").strip()
            pin = st.text_input("PIN", type="password", max_chars=4, placeholder="••••")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not acc_num or not pin:
                set_flash("error", "Please enter both account number and PIN.")
            else:
                account = bank.read_account(acc_num, pin)
                if account:
                    st.session_state["logged_in"] = True
                    st.session_state["account"] = account
                    st.session_state["plain_pin"] = pin
                    set_flash("success", f"Welcome back, {account.get_name()}!")
                else:
                    set_flash("error", "Wrong account number or PIN.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Create account ----------------
    with tab_create:
        st.markdown('<div class="vault-card">', unsafe_allow_html=True)
        st.markdown("### Open a new account")
        st.caption("Choose a name and a 4-digit PIN. Your account number is generated automatically.")
        with st.form("create_form", clear_on_submit=True):
            name = st.text_input("Full Name", placeholder="John Doe").strip()
            new_pin = st.text_input("Choose 4-digit PIN", type="password", max_chars=4)
            confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4)
            create_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if create_submitted:
            if not name:
                set_flash("error", "Name cannot be empty.")
            elif len(new_pin) != 4 or not new_pin.isdigit():
                set_flash("error", "PIN must be exactly 4 digits.")
            elif new_pin != confirm_pin:
                set_flash("error", "PINs do not match.")
            else:
                account = bank.create_account(name, new_pin)
                if account:
                    set_flash(
                        "success",
                        f"Account created! Your account number is **{account.get_account_number()}** "
                        "— save it somewhere safe, you'll need it to log in.",
                    )
                else:
                    set_flash("error", "Something went wrong while creating your account.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Admin ----------------
    with tab_admin:
        st.markdown('<div class="vault-card">', unsafe_allow_html=True)
        st.markdown("### Admin access")
        st.caption("View or clear system-wide audit logs.")
        admin_pass = st.text_input("Admin passcode", type="password", key="admin_pass_input")
        if st.button("Enter admin panel"):
            # Simple fixed passcode gate for this demo system.
            if admin_pass == "admin1234":
                st.session_state["admin_mode"] = True
                st.rerun()
            else:
                st.error("Incorrect admin passcode.")
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------
def render_admin_panel():
    render_header("Administrator panel — full audit trail")
    show_flash()

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back to login"):
            st.session_state["admin_mode"] = False
            st.rerun()

    logs = bank.get_all_audit_logs()

    c1, c2, c3 = st.columns(3)
    total_logs = len(logs) if logs else 0
    total_deposits = sum(l["amount"] for l in logs if logs and l["action"].lower().strip() == "amount deposited") if logs else 0.0
    total_withdrawals = sum(l["amount"] for l in logs if logs and l["action"].lower().strip() == "amount withdrawn") if logs else 0.0
    c1.metric("Total Log Entries", total_logs)
    c2.metric("Total Deposited", f"${total_deposits:,.2f}")
    c3.metric("Total Withdrawn", f"${total_withdrawals:,.2f}")

    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### 📜 All Audit Logs")
    if not logs:
        st.info("No audit logs found.")
    else:
        rows = []
        for log in logs:
            rows.append(
                {
                    "ID": log["id"],
                    "Account": log["account_number"] if log["account_number"] else "[deleted]",
                    "Holder": log["holder_name"],
                    "Action": log["action"].strip(),
                    "Amount": f"${log['amount']:.2f}" if log["amount"] else "",
                    "Timestamp": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(log["timestamp"], datetime)
                    else str(log["timestamp"]),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### ⚠️ Danger zone")
    st.caption("Permanently delete every audit log entry. This cannot be undone.")
    confirm_clear = st.checkbox("I understand this will permanently delete all audit logs.")
    if st.button("Clear all audit logs", disabled=not confirm_clear):
        if bank.clear_audit_logs():
            set_flash("success", "All audit logs successfully cleared!")
        else:
            set_flash("error", "Problem clearing audit logs.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Authenticated dashboard
# ---------------------------------------------------------------------------
def render_sidebar_nav(account):
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 10px 0 22px 0;">
                <div style="font-size:2.2rem;">🏦</div>
                <div style="font-weight:700; font-size:1.05rem; margin-top:4px;">{account.get_name()}</div>
                <div style="color:#93a1bb; font-size:0.8rem;">{account.get_account_number()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        page = st.radio(
            "Navigate",
            [
                "💰 Overview",
                "⬇️ Deposit",
                "⬆️ Withdraw",
                "📜 Transaction History",
                "⚙️ Account Settings",
                "🗑️ Delete Account",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        return page


def render_overview(account):
    st.markdown(
        f"""
        <div class="balance-card">
            <div class="label">Available Balance</div>
            <div class="amount">${account.get_balance():,.2f}</div>
            <div class="acc">Account #{account.get_account_number()} • {account.get_name()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    logs = bank.get_single_audit_logs(account.get_account_number()) or []
    recent = logs[:5]

    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### 🕒 Recent activity")
    if not recent:
        st.info("No transactions yet. Make your first deposit to get started.")
    else:
        for log in recent:
            action = log["action"].strip()
            amount = log["amount"]
            if "deposit" in action.lower():
                pill = '<span class="pill pill-credit">DEPOSIT</span>'
            elif "withdraw" in action.lower():
                pill = '<span class="pill pill-debit">WITHDRAW</span>'
            else:
                pill = f'<span class="pill pill-neutral">{action.upper()}</span>'
            ts = log["timestamp"]
            ts_str = ts.strftime("%d %b %Y, %H:%M") if isinstance(ts, datetime) else str(ts)
            amt_str = f"${amount:.2f}" if amount else "—"
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            padding:10px 0; border-bottom:1px solid #243352;">
                    <div>{pill}&nbsp;&nbsp;<span style="color:#93a1bb;">{ts_str}</span></div>
                    <div style="font-weight:600;">{amt_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_deposit(account):
    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### ⬇️ Deposit money")
    st.caption("Add funds to your account balance.")
    with st.form("deposit_form", clear_on_submit=True):
        amount = st.number_input("Amount ($)", min_value=0.0, step=10.0, format="%.2f")
        submitted = st.form_submit_button("Deposit", use_container_width=True)

    if submitted:
        if amount <= 0:
            set_flash("error", "Amount must be greater than zero.")
        else:
            plain_pin = st.session_state["plain_pin"]
            if bank.deposit(account.get_account_number(), plain_pin, amount):
                refresh_account()
                set_flash("success", f"${amount:.2f} successfully deposited!")
            else:
                set_flash("error", "Error occurred while depositing, please try again.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_withdraw(account):
    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### ⬆️ Withdraw money")
    st.caption(f"Available balance: **${account.get_balance():,.2f}**")
    with st.form("withdraw_form", clear_on_submit=True):
        amount = st.number_input("Amount ($)", min_value=0.0, step=10.0, format="%.2f")
        submitted = st.form_submit_button("Withdraw", use_container_width=True)

    if submitted:
        if amount <= 0:
            set_flash("error", "Amount must be greater than zero.")
        else:
            plain_pin = st.session_state["plain_pin"]
            if bank.withdraw(account.get_account_number(), plain_pin, amount):
                refresh_account()
                set_flash("success", f"${amount:.2f} successfully withdrawn!")
            else:
                set_flash("error", "Insufficient balance or invalid amount.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_history(account):
    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### 📜 Transaction history")
    logs = bank.get_single_audit_logs(account.get_account_number())
    if not logs:
        st.info("No transaction history found.")
    else:
        rows = []
        for log in logs:
            ts = log["timestamp"]
            rows.append(
                {
                    "ID": log["id"],
                    "Action": log["action"].strip(),
                    "Amount": f"${log['amount']:.2f}" if log["amount"] else "",
                    "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else str(ts),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_settings(account):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="vault-card">', unsafe_allow_html=True)
        st.markdown("### 🧑 Update name")
        with st.form("name_form"):
            new_name = st.text_input("New name", value=account.get_name())
            submitted = st.form_submit_button("Save name", use_container_width=True)
        if submitted:
            new_name = new_name.strip()
            if not new_name:
                set_flash("error", "Name cannot be empty.")
            else:
                account.set_name(new_name)
                if bank.update_account(account):
                    refresh_account()
                    set_flash("success", "Name successfully updated!")
                else:
                    set_flash("error", "Error updating name.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="vault-card">', unsafe_allow_html=True)
        st.markdown("### 🔑 Change PIN")
        with st.form("pin_form", clear_on_submit=True):
            old_pin = st.text_input("Current PIN", type="password", max_chars=4)
            new_pin = st.text_input("New 4-digit PIN", type="password", max_chars=4)
            confirm_pin = st.text_input("Confirm new PIN", type="password", max_chars=4)
            submitted_pin = st.form_submit_button("Update PIN", use_container_width=True)
        if submitted_pin:
            if not verify_pin(old_pin, account.get_pin_hash()):
                set_flash("error", "Current PIN is incorrect.")
            elif len(new_pin) != 4 or not new_pin.isdigit():
                set_flash("error", "New PIN must be exactly 4 digits.")
            elif new_pin != confirm_pin:
                set_flash("error", "New PINs do not match.")
            else:
                account.set_pin(new_pin)
                if bank.update_account(account):
                    st.session_state["plain_pin"] = new_pin
                    refresh_account()
                    set_flash("success", "PIN successfully updated!")
                else:
                    set_flash("error", "Problem updating PIN.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_delete(account):
    st.markdown('<div class="vault-card">', unsafe_allow_html=True)
    st.markdown("### 🗑️ Delete account")
    st.warning("⚠️ This action cannot be reversed. Your account and balance will be permanently removed.")
    st.write(f"**Account Number:** {account.get_account_number()}")

    with st.form("delete_form"):
        acc_confirm = st.text_input("Re-enter your account number to confirm")
        pin_confirm = st.text_input("Re-enter your PIN", type="password", max_chars=4)
        agree = st.checkbox("I understand this action is permanent.")
        submitted = st.form_submit_button("Permanently delete my account", use_container_width=True)

    if submitted:
        if not agree:
            set_flash("error", "Please confirm you understand this action is permanent.")
        elif acc_confirm.strip() != account.get_account_number() or not verify_pin(
            pin_confirm, account.get_pin_hash()
        ):
            set_flash("error", "Account number or PIN did not match. Deletion canceled.")
        else:
            if bank.delete_account(account.get_account_number(), pin_confirm):
                logout()
                set_flash("success", "Your account was successfully deleted. Goodbye!")
                st.rerun()
            else:
                set_flash("error", "Error occurred while deleting your account.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard():
    account = refresh_account()
    if not account:
        # Account no longer exists (e.g. deleted in another session) — bounce to login.
        logout()
        st.rerun()
        return

    page = render_sidebar_nav(account)
    render_header(f"Hello, {account.get_name()} 👋")
    show_flash()

    if page == "💰 Overview":
        render_overview(account)
    elif page == "⬇️ Deposit":
        render_deposit(account)
    elif page == "⬆️ Withdraw":
        render_withdraw(account)
    elif page == "📜 Transaction History":
        render_history(account)
    elif page == "⚙️ Account Settings":
        render_settings(account)
    elif page == "🗑️ Delete Account":
        render_delete(account)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def main():
    if st.session_state["logged_in"] and st.session_state["account"]:
        render_dashboard()
    elif st.session_state["admin_mode"]:
        render_admin_panel()
    else:
        render_public_area()

    st.markdown(
        '<div class="vault-footer">Vaultline Bank • Demo banking system • PostgreSQL backed</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
