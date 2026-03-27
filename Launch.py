import streamlit as st
import pandas as pd
import base64
import gspread
from google.oauth2.service_account import Credentials
import pathlib
import smtplib
from email.mime.text import MIMEText
import time

def load_css(file_path):
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(css_path, 'r', encoding='latin-1') as f:
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

def gui_email_quen_mat_khau(receiver_email):
    info = "\n".join([f"{k}: {v}" for k, v in st.session_state.vote.items()])
    ten = st.session_state.vote["Họ và tên"]
    subject = f"Quên mật khẩu - nhân viên {ten}"
    body = f"Thông tin nhân viên quên mật khẩu:\n{info}"
    # Thiết lập thông tin email
    sender_email = st.secrets["email_info"]["sender_email"]
    sender_password = st.secrets["email_info"]["sender_password"]

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Gửi email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
    st.session_state.sendemail = True
    st.session_state.sendemail_time = time.time()

@st.dialog("NHẬP THÔNG TIN CẤP LẠI MẬT KHẨU")
def cap_lai_mat_khau():
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data_nv = load_data(sheeti1)
    chon_khoa = st.selectbox("Chọn Khoa/Đơn vị ",
                            options=data_nv["Khoa"].unique(),
                            index=None,
                            placeholder=""
                            )
    HoTen = st.text_input("Họ và tên")
    MNV = st.text_input("Mã nhân viên")
    Email = st.text_input("Email",placeholder="Mật khẩu mới sẽ được gửi đến email này")
    Gui = st.button("Gửi thông tin đến quản trị viên")
    if Gui:
        st.session_state.vote = {"Họ và tên": HoTen,
                                "Mã nhân viên": MNV,
                                "Khoa": chon_khoa,
                                "Email": Email}
        receiver_email = st.secrets["email_info"]["receiver_1"]
        gui_email_quen_mat_khau(receiver_email)
        st.rerun()

def login():
    if st.session_state.get("sendemail", False):
        if time.time() - st.session_state.get("sendemail_time", 0) < 5:
            st.toast("Đã gửi thông tin đến quản trị viên! Vui lòng chờ phản hồi",icon="✅")
        else:
            del st.session_state["sendemail"]
            del st.session_state["sendemail_time"]
    if st.session_state.get("dmk", False):
        if time.time() - st.session_state.get("dmk_time", 0) < 5:
            st.toast("Bạn đã nhập sai mật khẩu 3 lần",icon="🚫")
        else:
            del st.session_state["dmk"]
            del st.session_state["dmk_time"]
    found = 0
    st.markdown(f"""
    <div class="login-header">
            <img src="data:image/png;base64,{img}" alt="logo" class="logo-img">
            <div class="login-header-text">
                <h4>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h4>
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
        code = st.text_input("Mật khẩu", type="password",placeholder="",  key="matkhau_login",)
        submit_button = st.form_submit_button("Đăng nhập")
        #QuenMatKhau = st.form_submit_button("Quên mật khẩu",type="tertiary")
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
    # if QuenMatKhau:
    #     cap_lai_mat_khau()

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
             title="Thông tin ghi nhớ",
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

QTKT = st.Page("pages/1_QTKT.py", 
               title="1. Giám sát quy trình kỹ thuật", 
               icon="🩺", default=True
)
CSCS = st.Page("pages/1.2_CSCS.py", 
               title="2. Chỉ số chăm sóc", 
               icon="🩹"
)
PRIME = st.Page("pages/1.1_PRIME.py", 
               title="3. PRIME", 
               icon="💉"
)
HSBA = st.Page("pages/2_HSBA.py", 
               title="4. Hồ sơ bệnh án", 
               icon="📋"
)
GDSK = st.Page("pages/3_GDSK.py",
                title="5. Giáo dục sức khỏe",
                icon="👄"
)
VTTB = st.Page("pages/4_VTTB.py",
                title="6. Báo cáo thiết bị hằng ngày",
                icon="🦽"
)
PCCS = st.Page("pages/5_PCCS.py",
                title="7. Người bệnh PCCS cấp I/ ĐD",
                icon="🥇"
)
KSNK = st.Page("pages/6_KSNK.py",
                title="8. Kiểm soát nhiễm khuẩn",
                icon="🌷"
)
TTD_TN = st.Page("pages/7_TTD_TN.py",
                title="9. Loét - Té ngã",
                icon="🔖"
)
QLDD_HDCM = st.Page("pages/8_QLDD_HDCM.py",
                title="10. Quản lý điều dưỡng",
                icon="💎"
)
PCNL = st.Page("pages/9_PCNL.py",
                title="11. TEST",
                icon="💎"
)

BC_QTKT = st.Page("reports/1_rp_QTKT.py", title="TK Giám sát quy trình kỹ thuật",  icon="🔹")
BC_CSCS = st.Page("reports/1.2_rp_CSCS.py", title="TK Chỉ số chăm sóc ", icon="🔹")
BC_PRIME = st.Page("reports/1.1_rp_PRIME.py", title="TK PRIME ", icon="🔹")
BC_HSBA = st.Page("reports/2_rp_HSBA.py", title="TK Hồ sơ bệnh án", icon="🔹")
BC_GDSK = st.Page("reports/3_rp_GDSK.py", title="TK Giáo dục sức khỏe", icon="🔹")
BC_VTTB = st.Page("reports/4_rp_VTTB.py", title="TK Báo cáo thiết bị", icon="🔹")
BC_PCCS = st.Page("reports/5_rp_PCCS.py", title="TK NB PCCS Cấp I/ ĐD", icon="🔹")
BC_KSNK = st.Page("reports/6_rp_KSNK.py", title="TK Số liệu KSNK", icon="🔹")
BC_TTD_TN = st.Page("reports/7_rp_TTD_TN.py", title="TK Số liệu Loét - Té ngã", icon="🔹")
BC_QLDD_HDCM = st.Page("reports/8_rp_QLDD_HDCM.py", title="TK QLĐD & HĐCM", icon="🔹")


THI_test = st.Page("DepartmentTest/1_LamBaiThi.py", title="Làm bài thi",  icon="📝")
THI_manage = st.Page("DepartmentTest/2_QuanLyDeThi.py", title="Quản lý đề thi",  icon="📊")
THI_result = st.Page("DepartmentTest/3_KetQuaThi.py", title="Xem kết quả thi",  icon="📈")


khoa = ["Đơn vị Gây mê hồi sức Phẫu thuật tim mạch",
        "Đơn vị Hồi sức Ngoại Thần kinh",
        "Khoa Hô hấp",
        "Khoa Hồi sức tích cực",
        "Khoa Thần kinh",
        "Khoa Nội Tim mạch",
        "Khoa Phẫu thuật tim mạch",
        "Khoa Tim mạch can thiệp"]

if "username" in st.session_state:
    if "khoa" not in st.session_state:
        st.session_state.khoa = ""
    if st.session_state.phan_quyen in ["1"]: 
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test, THI_manage, THI_result],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS, KSNK, TTD_TN, QLDD_HDCM],
                "Thống kê báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_HSBA, 
                                     BC_GDSK, BC_VTTB, BC_PCCS, BC_KSNK, BC_TTD_TN,
                                     BC_QLDD_HDCM],
                "Quản trị viên": [AD1, AD2, AD3],
                "Trắc nghiệm": [THI_test, THI_manage, THI_result],
            },
        expanded=False,
        )
    elif st.session_state.phan_quyen in ["2"]: 
        pg = st.navigation(    
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test, THI_manage,THI_result],
                "Nhập kết quả": [QTKT,CSCS,PRIME, HSBA, GDSK,VTTB, PCCS, KSNK, TTD_TN],
                "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_HSBA, BC_GDSK, BC_VTTB, BC_PCCS, BC_KSNK, BC_TTD_TN],
                "Quản trị viên": [AD1],
            },
        expanded=False,
        )
    ##### 3. Nhóm lâm sàng PĐD ########
    elif st.session_state.phan_quyen in ["3"]: 
        pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test, THI_manage,THI_result],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS, KSNK, TTD_TN],
                "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_HSBA, BC_GDSK,BC_VTTB, BC_PCCS, BC_KSNK, BC_TTD_TN],
            },
        expanded=False,
        )
    ######## 4. ĐD Trưởng Khoa/Đơn nguyên ########
    elif st.session_state.phan_quyen in ["4"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_HSBA, BC_GDSK, BC_VTTB, BC_PCCS],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_HSBA, BC_GDSK, BC_VTTB, BC_PCCS],
                },
            expanded=False,
            )
    ##### 5: ĐD viên + QTKT + CSCS + PRIME ########
    elif st.session_state.phan_quyen in ["5"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME],
                },
            expanded=False,
            )
    ##### 6: ĐD viên + HSBA + GDSK ########
    elif st.session_state.phan_quyen in ["6"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_HSBA, BC_GDSK],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_HSBA, BC_GDSK],
                },
            expanded=False,
            )
    ##### 7: ĐD viên + VTTB + PCCS ########
    elif st.session_state.phan_quyen in ["7"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_VTTB, BC_PCCS],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_VTTB, BC_PCCS],
                },
            expanded=False,
            )
    ##### 8: ĐD viên + QTKT + CSCS + PRIME + VTTB + PCCS ########
    elif st.session_state.phan_quyen in ["8"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT,CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_VTTB, BC_PCCS],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_QTKT, BC_CSCS, BC_PRIME, BC_VTTB, BC_PCCS],
                },
            expanded=False,
            )
    ##### 9: ĐD viên + GDSK + HSBA + VTTB + PCCS ########
    elif st.session_state.phan_quyen in ["9"]:
        if st.session_state.khoa and st.session_state.khoa in khoa:
            pg = st.navigation(
            {
                "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                "Trắc nghiệm": [THI_test],
                "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                "Báo cáo": [BC_GDSK, BC_HSBA, BC_VTTB, BC_PCCS],
            },
        expanded=False,
        )
        else:
            pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo": [BC_GDSK, BC_HSBA, BC_VTTB, BC_PCCS],
                },
            expanded=False,
            )
    else: ##### 10: ĐD viên bình thường ########
        if st.session_state.khoa and st.session_state.khoa in khoa:
           pg = st.navigation(
                {
                    "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                    "Trắc nghiệm": [THI_test],
                    "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    "Báo cáo":[BC_VTTB, BC_PCCS]
                },
        expanded=False,
        )
        else:
            pg = st.navigation(
                    {
                        "Thông tin tài khoản": [ logout_page,PD,PS, YC],
                        "Trắc nghiệm": [THI_test],
                        "Nhập kết quả": [QTKT, CSCS, PRIME, HSBA, GDSK, VTTB, PCCS],
                    },
            expanded=False,
            )
else:
    pg = st.navigation([login_page])
pg.run()

