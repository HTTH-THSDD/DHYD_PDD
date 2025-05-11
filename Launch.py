import streamlit as st
import pandas as pd
import base64
import gspread
from google.oauth2.service_account import Credentials
import pathlib

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache_data(ttl=3600)
def load_credentials():
    creds_info = {
    "type": st.secrets["google_service_account"]["type"],
    "project_id": st.secrets["google_service_account"]["project_id"],
    "private_key_id": st.secrets["google_service_account"]["private_key_id"],
    "private_key": st.secrets["google_service_account"]["private_key"],
    "client_email": st.secrets["google_service_account"]["client_email"],
    "client_id": st.secrets["google_service_account"]["client_id"],
    "auth_uri": st.secrets["google_service_account"]["auth_uri"],
    "token_uri": st.secrets["google_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["google_service_account"]["universe_domain"],
    }
    # Dùng để kết nối Google APIs
    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return credentials

@st.cache_data(ttl=3600)
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

def login():
    found = 0
    st.markdown(f"""
    <div class="login-header">
            <img src="data:image/png;base64,{img}" alt="logo" class="logo-img">
            <div class="login-header-text">
                <h4>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<br><span style="color:#c15088">Phòng Điều dưỡng</span></h4>
            </div>
        </div>
    """, unsafe_allow_html=True)
    #Lấy dữ liệu nhân viên
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data = load_data(sheeti1)
    tennv = data["Nhân viên"]
    mk = data['Mật khẩu']
    pq = data["Phân quyền"]
    #Form đăng nhập nhân viên
    with st.form("LoginForm"):
        name = st.selectbox("Tên nhân viên",
                            options= data["Nhân viên"].unique(),
                            index = None,
                            placeholder="",)
        code = st.text_input("Mật khẩu", type="password",placeholder="",)
        submit_button = st.form_submit_button("Đăng nhập")
    if submit_button:
        index = 0
        code=code.upper()
        for i in tennv:
            index +=1
            if name == i and code == mk[int(index-1)]:
                found +=1
                quyen = pq[int(index-1)]
                st.session_state.khoa=data["Khoa"].iloc[index-1]
        if found == 0:
            st.warning("Tên đăng nhập và mật khẩu không phù hợp")
        if found == 1:
            st.session_state["username"] = name
            st.session_state["phan_quyen"] = quyen
            st.rerun()

def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

#MS##########################################################################################################3
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
login_page = st.Page(login, title="Đăng nhập", icon=":material/login:")
logout_page = st.Page(logout, title="Đăng xuất", icon=":material/logout:")

AD1 = st.Page("admin/admin1.py",
             title="Thông tin quản trị",
             icon="💡",
             )
AD3 = st.Page("admin/admin3.py",
             title="Quản lí giám sát",
             icon="⭐",
             )
AD2 = st.Page("admin/admin2.py",
             title="Quản lí người dùng",
             icon="💻",
             )
PD = st.Page("users/1_thong_tin.py", 
               title="Thông tin cá nhân", 
               icon="👤",
)
YC = st.Page("users/2_yeu_cau.py", 
               title="Yêu cầu", 
               icon="📩",
)
PS = st.Page("users/3_doi_mk.py", 
               title="Đổi mật khẩu", 
               icon="🔑",
)

GSHS = st.Page("pages/1_GSQT.py", 
               title="Giám sát quy trình kỹ thuật", 
               icon="🩺", default=True
)
HSBA = st.Page("pages/2_HSBA.py", 
               title="Hồ sơ bệnh án", 
               icon="📋"
)
GDSK = st.Page("pages/3_GDSK.py",
                title="Giáo dục sức khỏe",
                icon="👄"
)
VTTB = st.Page("pages/4_VTTB.py",
                title="Báo cáo thiết bị hằng ngày",
                icon="🦽"
)

<<<<<<< HEAD
BC_GSQT = st.Page("reports/rp_GSQT.py", title="TK Giám sát quy trình",  icon="🔶")
BC_HSBA = st.Page("reports/rp_HSBA.py", title="TK Hồ sơ bệnh án", icon="🔶")
BC_GDSK = st.Page("reports/rp_GDSK.py", title="TK Giáo dục sức khỏe", icon="🔶")
BC_VTTB = st.Page("reports/rp_VTTB.py", title="TK Báo cáo thiết bị hằng ngày", icon="🔶")
=======
BC_GSQT = st.Page("reports/rp_GSQT.py", title="Báo cáo giám sát quy trình", icon="🔸")
BC_HSBA = st.Page("reports/rp_HSBA.py", title="Báo cáo hồ sơ bệnh án", icon="🔸")
BC_GDSK = st.Page("reports/rp_GDSK.py", title="Báo cáo giáo dục sức khỏe", icon="🔸")

>>>>>>> 125067bc691932de10fca9932c003cfc0cf83af4

if "username" in st.session_state:
    if st.session_state.phan_quyen in ["1"]:
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Nhập kết quả": [GSHS, HSBA, GDSK,VTTB],
                "Thống kê báo cáo": [BC_GSQT, BC_HSBA,BC_GDSK,BC_VTTB],
                "Quản trị viên admin": [AD1, AD2, AD3],
            },
        expanded=False,
        )
    elif st.session_state.phan_quyen in ["2"]:
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Giám sát": [GSHS, HSBA, GDSK,VTTB],
                "Báo cáo": [BC_GSQT, BC_HSBA,BC_GDSK,BC_VTTB],
                "Quản trị viên": [AD1],
            },
        expanded=False,
        )
    elif st.session_state.phan_quyen in ["3"]:
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Giám sát": [GSHS, HSBA, GDSK,VTTB],
                "Báo cáo": [BC_GSQT, BC_HSBA,BC_GDSK,BC_VTTB],
            },
        expanded=False,
        )
    elif st.session_state.phan_quyen in ["4"]:
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Giám sát": [GSHS, HSBA, GDSK,VTTB],
                "Báo cáo": [BC_GSQT, BC_HSBA,BC_GDSK],
            },
        expanded=False,
        )
    else:
        pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Giám sát": [GSHS, HSBA, GDSK, VTTB],
                },
        expanded=False,
        )
else:
    pg = st.navigation([login_page])
pg.run()

