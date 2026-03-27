import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

# -----------------------
# GOOGLE SHEETS FIX (IMPORTANT)
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])

# 🔥 FIX PRIVATE KEY ERROR
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    gcp_info,
    scopes=scope
)

client = gspread.authorize(creds)

# 🔥 CHANGE THIS WITH YOUR SHEET ID
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.write("No filters. No fake photos. Only reality.")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# USER PAGE
# -----------------------
elif st.session_state.page == "user":

    st.title("👤 User Dashboard")

    data = pg_sheet.get_all_records()

    for pg in data:

        st.subheader(pg["name"])
        st.write(f"📍 {pg['location']}")

        # IMAGE
        if pg.get("image_url"):
            st.image(pg["image_url"])
        else:
            st.image("https://via.placeholder.com/300")

        # VERIFIED
        if pg.get("verified") == "Yes":
            st.success("✅ Verified by Us")
        else:
            st.warning("⚠️ Not Verified")

        st.markdown("""
        📸 Real room images  
        🚿 Bathroom reality  
        🍛 Actual food plate  
        🍽️ Dining area  
        🧳 Storage space  
        🏢 Building view  
        """)

        st.divider()

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()

# -----------------------
# ADMIN PAGE
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Enter Password", type="password")

    if password == "1234":
        st.session_state.admin_logged = True

    if not st.session_state.admin_logged:
        st.stop()

    st.success("Admin Logged In")

    # LOGOUT
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    # -----------------------
    # ADD PG
    # -----------------------
    st.subheader("📤 Add New PG")

    name = st.text_input("PG Name")
    location = st.text_input("Location")
    image_url = st.text_input("Image URL")
    verified = st.selectbox("Verified", ["Yes", "No"])

    if st.button("➕ Add PG"):

        if name and location:
            pg_sheet.append_row([
                name,
                location,
                image_url,
                verified
            ])

            st.success("✅ PG Added!")
            st.rerun()
        else:
            st.error("Fill all fields")

    st.divider()

    # -----------------------
    # VIEW + EDIT PGs
    # -----------------------
    st.subheader("📋 Manage PGs")

    data = pg_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.write(f"🏠 {pg['name']} - {pg['location']}")

        col1, col2 = st.columns(2)

        # DELETE
        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(i + 2)
            st.rerun()

        # TOGGLE VERIFY
        if col2.button("✅ Toggle Verify", key=f"v{i}"):

            new_status = "No" if pg["verified"] == "Yes" else "Yes"

            pg_sheet.update_cell(i + 2, 4, new_status)
            st.rerun()

        st.divider()

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()