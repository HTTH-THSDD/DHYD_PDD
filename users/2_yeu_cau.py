import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
import pathlib
import base64
from email.mime.text import MIMEText
import smtplib

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
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

@st.cache_data(ttl=20)
def load_data_GSheet(name):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(name).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if "Nhân viên yêu cầu" in df.columns:
        username = st.session_state.username
        df = df[df["Nhân viên yêu cầu"] == username]
        ngay_yc = []
        loai_yc = []
        nd_yc = []
        li_do_yc = []
        tt = []
        for i in range (0,len(df)):
            ngay_yc.append(df.iloc[i,1])
            loai_yc.append(df.iloc[i,5])
            nd_yc.append(df.iloc[i,6])
            li_do_yc.append(df.iloc[i,9])
            # nd_yc.append(df.iloc[i,5][:40]+"...") #40 kí tự chữ đầu
            if df.iloc[i,7] == "" or df.iloc[i,7] == None:
                tt.append("Đang chờ")
            else:
                if df.iloc[i,8] == "" or df.iloc[i,8] == None:
                    tt.append("Đang cập nhật")
                elif df.iloc[i,8] == 1:
                    tt.append("Hoàn thành")
                elif df.iloc[i,8] == 0:
                    tt.append("Từ chối")
        k = {   "Ngày gửi yêu cầu": pd.Series(ngay_yc),
                "Tình trạng": pd.Series(tt),
                "Loại yêu cầu": pd.Series(loai_yc),
                "Nội dung": pd.Series(nd_yc),
                "Ghi chú lí do":pd.Series(li_do_yc),
                }
        df_yc = pd.DataFrame(k)
        df_yc = pd.DataFrame(df_yc).sort_values("Ngày gửi yêu cầu", ascending=False)
        df_yc.insert(0, 'STT', range(1, len(df_yc) + 1))
        return df_yc
    else:
        return pd.DataFrame()
    
@st.cache_data(ttl=3600)
def highlight_status(val):
    if val == "Hoàn thành":
        color = "green"
    elif val == "Đang cập nhật":
        color = "orange"
    elif val == "Từ chối":
        color = "red"
    else:
        color = "black"
    return f"color: {color}"

def gui_email_yc():
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    timestamp = now_vn.strftime('%H:%M %d-%m-%Y')
    subject = f"YÊU CẦU TỪ PHẦN MỀM GSCTCMĐD"
    body = f"""
    <html>
        <body>
            <h4 style="color:DodgerBlue;">{timestamp}</h4>
            <p> Bạn có 01 yêu cầu <strong>{st.session_state.lyc}</strong> từ nhân viên <strong>{st.session_state.username} - {st.session_state.khoa_YC}</strong><br></p>
            <p> <strong>Nội dung yêu cầu:</strong> {st.session_state.ndyc}<br>
                <strong>Thông tin liên hệ:</strong> {st.session_state.ttlh}<br>
            </p>
        </body>
    </html>
    """
    # Thiết lập thông tin email
    sender_email = st.secrets["email_info"]["sender_email"]
    sender_password = st.secrets["email_info"]["sender_password"]
    receiver_emails = [st.secrets["email_info"]["receiver_1"],st.secrets["email_info"]["receiver_2"]]

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)

    # Gửi email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())

def upload_data_yc():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open("Output-st-YC").sheet1
    
    all_values = sheet.get_all_values()
    next_row = len(all_values) + 1
    if len(all_values) > 1:
        try:
            last_row = all_values[-1]
            last_stt = int(last_row[0])  # Cột đầu tiên là STT
            new_stt = last_stt + 1
        except (ValueError, IndexError):
            new_stt = len(all_values)
    else:
        new_stt = 1
    
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))    
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_khoa = str(st.session_state.khoa_YC)
    column_nvyc = str(st.session_state.username)
    column_ttlh = str(st.session_state.ttlh)
    column_loaiyc = str(st.session_state.lyc)
    column_ndyc = str(st.session_state.ndyc)
    new_row = [
        new_stt,
        column_timestamp,
        column_khoa,
        column_nvyc,
        column_ttlh,
        column_loaiyc,
        column_ndyc,
    ]
    
    try:
        sheet.insert_row(new_row, index=next_row, value_input_option='USER_ENTERED')
        gui_email_yc()
        
        # Clear cache
        st.cache_data.clear()
        
        st.toast("Yêu cầu đã được gửi!")
        return True
        
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi gửi yêu cầu: {str(e)}")
        return False

# Main Section ####################################################################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:#9F2B68">YÊU CẦU BỔ SUNG/PHÂN QUYỀN</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên gửi yêu cầu: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 = st.secrets["sheet_name"]["input_1"]   
data_nv = load_data(sheeti1)
st.session_state.khoa_YC = data_nv.loc[data_nv["Nhân viên"]==st.session_state.username,"Khoa"].values[0]
tab1, tab2 = st.tabs(["🔍 Gửi yêu cầu", "📊 Các yêu cầu trước đây"])
with tab1:
    option_yeu_cau = ["Cập nhật nhân sự", "Phân quyền nhân sự", "Bổ sung quy trình kỹ thuật", "Khác"]
    with st.form(key="yc"):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("###### Loại yêu cầu:")
        with col2:
            lyc = st.selectbox("",
                            options=option_yeu_cau,
                            index=None,
                            placeholder="Chọn yêu loại yêu cầu",
                            key="lyc")
            
        st.session_state.ndyc = st.text_area("Nội dung yêu cầu:")
        st.session_state.ttlh = st.text_input("Thông tin liên hệ", placeholder="Email/SĐT liên hệ",key="yc_ttlh")
        submitbt=st.form_submit_button("Gửi yêu cầu")
    if submitbt:
        if "lyc" in st.session_state and st.session_state["lyc"] and "ndyc" in st.session_state and st.session_state["ndyc"]:
            upload_data_yc()
        else:
            st.warning("Anh/Chị vui lòng chọn loại yêu cầu và điền nội dung yêu cầu")
with tab2:
    sheeto4 = st.secrets["sheet_name"]["output_4"]
    data_yc = load_data_GSheet(sheeto4)
    if not data_yc.empty:
        st.subheader("Danh sách các yêu cầu của bạn:")
        placeholder = st.empty()
        styled_df = data_yc.style.applymap(highlight_status, subset=["Tình trạng"])
        placeholder.dataframe(styled_df, use_container_width=True, hide_index=True)
        # st.dataframe(data_yc[["STT", "Ngày gửi yêu cầu", "Loại yêu cầu", "Nội dung", "Tình trạng"]],hide_index=True)
    else:
        st.warning("Không có yêu cầu nào được tìm thấy.")
    button=st.button("Cập nhật")
    if button:
        load_data_GSheet.clear()
        st.rerun()


st.markdown("""
    <br><br><br>
    <hr style="border: 1.325px solid #195e83; margin: 15px 0;">
    <p style="font-size: 13.5px; color: #333;">
        <i>Các yêu cầu thông thường sẽ được giải quyết trong vòng 72 giờ. Sau thời gian này nếu yêu cầu của Quý Anh/Chị chưa được giải quyết hoặc có những thắc mắc khác, Quý Anh/Chị vui lòng liên hệ:
        <span style="color: #042f66; font-weight: bold;">ThSĐD. Huỳnh Thị Thanh Hằng (5379)</span> 
        hoặc 
        <span style="color: #042f66; font-weight: bold;">ThSĐD. Võ Thị Cẩm Nhung (5624)</span>
        <br> Xin cảm ơn Quý Anh/Chị!
        </i>
    </p>
""", unsafe_allow_html=True)


