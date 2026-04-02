import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import cloudinary
import cloudinary.uploader

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="PG Admin", layout="wide")

# -----------------------
# CLOUDINARY CONFIG (NESTED SECRETS)
# -----------------------
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

# -----------------------
# SESSION INIT
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "arrived" not in st.session_state:
    st.session_state.arrived = False

# -----------------------
# GOOGLE SHEETS
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1
order_sheet = sheet.worksheet("orders")

# -----------------------
# LOAD PG DATA
# -----------------------
pg_raw = pg_sheet.get_all_records()

pg_data = []
for row in pg_raw:
    val = row.get("pg_name") or row.get("pg")
    if val:
        pg_data.append(val)

pg_data = sorted(list(set(pg_data)))

# =====================
# HOME
# =====================
if st.session_state.page == "home":

    st.title("🏠 Move-in Assistant")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# =====================
# USER DASHBOARD
# =====================
elif st.session_state.page == "user":

    st.title("👤 User Dashboard")

    name = st.text_input("Name")
    phone = st.text_input("Phone")

    selected_pg = st.selectbox("Select PG", pg_data)

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True
        st.rerun()

    if st.session_state.arrived:

        cart = st.session_state.cart

        products = {
            "basic": {"name": "Basic Kit", "price": 249},
            "utility": {"name": "Utility Kit", "price": 199},
            "hygiene": {"name": "Hygiene Kit", "price": 129},
            "combo": {"name": "Combo Kit", "price": 499}
        }

        for key in products:
            p = products[key]

            st.write(f"{p['name']} - ₹{p['price']}")

            if key in cart:
                if st.button("❌ Remove", key=f"r{key}"):
                    del cart[key]
                    st.rerun()
            else:
                if st.button("Add", key=f"a{key}"):
                    cart[key] = p
                    st.rerun()

        if cart:
            total = sum(i["price"] for i in cart.values())

            st.write(f"### Total: ₹{total}")

            if st.button("Place Order"):

                items = ", ".join([i["name"] for i in cart.values()])

                order_sheet.append_row([
                    name,
                    phone,
                    selected_pg,
                    items,
                    total,
                    "Pending",
                    str(datetime.now()),
                    ""  # screenshot column
                ])

                st.session_state.order_done = True
                st.session_state.total = total
                st.rerun()

        # -----------------------
        # PAYMENT
        # -----------------------
        if st.session_state.get("order_done"):

            total = st.session_state.total
            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.success("Order placed!")

            if "paid_clicked" not in st.session_state:
                st.session_state.paid_clicked = False

            if st.button("💰 Pay Now"):
                st.session_state.paid_clicked = True
                st.markdown(f"[Click here to Pay]({upi})")

            if st.session_state.paid_clicked:

                st.divider()
                st.write("📤 Upload Payment Screenshot")

                file = st.file_uploader("Upload Screenshot", type=["png","jpg","jpeg"])

                if file:
                    st.image(file, width=200)

                    # Upload to Cloudinary
                    result = cloudinary.uploader.upload(file)
                    image_url = result["secure_url"]

                    # Save URL in sheet
                    last_row = len(order_sheet.get_all_values())
                    order_sheet.update_cell(last_row, 8, image_url)

                    st.success("✅ Screenshot uploaded!")
                    st.info("📲 We will verify and send WhatsApp confirmation.")

# =====================
# ADMIN DASHBOARD
# =====================
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    data = order_sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    for i in reversed(range(len(rows))):

        o = dict(zip(headers, rows[i]))

        st.write(f"👤 {o.get('Owner_name')} | 📞 {o.get('phone_number')}")
        st.write(f"🏠 {o.get('pg_name')} | 🛒 {o.get('items')}")

        # Screenshot display
        if o.get("screenshot"):
            st.success("📸 Screenshot Uploaded")
            st.image(o["screenshot"], width=150)
        else:
            st.warning("❌ No Screenshot")

        st.divider()