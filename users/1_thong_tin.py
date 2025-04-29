import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pathlib
import base64

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
    with open(file_path) as f:
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
        index = []
        ngay_yc = []
        loai_yc = []
        nd_yc = []
        tt = []
        for i in range (0,len(df)):
            index.append(int(i+1))
            ngay_yc.append(df.iloc[i,1])
            loai_yc.append(df.iloc[i,5])
            nd_yc.append(df.iloc[i,6]) 
            # nd_yc.append(df.iloc[i,5][:40]+"...") #40 kí tự chữ đầu
            if df.iloc[i,7] == "" or df.iloc[i,7] == None:
                tt.append("Đang chờ")
            else:
                if df.iloc[i,8] == "" or df.iloc[i,8] == None:
                    tt.append("Đang cập nhât")
                elif df.iloc[i,8] == 1:
                    tt.append("Hoàn thành")
                elif df.iloc[i,8] == 0:
                    tt.append("Từ chối")
        k = {"STT": pd.Series(index),
            "Ngày gửi yêu cầu": pd.Series(ngay_yc),
                "Tình trạng": pd.Series(tt),
                "Loại yêu cầu": pd.Series(loai_yc),
                "Nội dung": pd.Series(nd_yc),
                }
        df_yc = pd.DataFrame(k)

        return df_yc
    else:
        return pd.DataFrame()
    
@st.cache_data(ttl=3600)
def highlight_status(val):
    if val == "Hoàn thành":
        color = "green"
    elif val == "Đang cập nhât":
        color = "orange"
    elif val == "Từ chối":
        color = "red"
    else:
        color = "black"
    return f"color: {color}"

def upload_data_yc():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open("Output-st-YC").sheet1
    column_index = len(sheet.get_all_values())
    now = datetime.datetime.now()
    column_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    column_khoa = str(st.session_state.khoa_YC)
    column_nvyc = str(st.session_state.username)
    column_ttlh = str(st.session_state.ttlh)
    column_loaiyc = str(st.session_state.lyc)
    column_ndyc = str(st.session_state.ndyc)
    sheet.append_row([  column_index,
                        column_timestamp,
                        column_khoa,
                        column_nvyc,
                        column_ttlh,
                        column_loaiyc,
                        column_ndyc,
                     ])
    st.toast("Yêu cầu đã được gửi!")

def xuli(data,a,ten_ma,sd,ed):
    data = data.loc[data[a] == st.session_state.username]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + datetime.timedelta(days=1)
    data = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] <= pd.Timestamp(end_date))]
    if data.empty:
        st.warning("Không có dữ liệu trong khoảng thời gian yêu cầu")
    else:
        data.insert(0, 'STT', range(1, len(data) + 1))
        data['Tỉ lệ tuân thủ'] = data['Tỉ lệ tuân thủ'].str.slice(0, 4)
        data['Tỉ lệ an toàn'] = data['Tỉ lệ an toàn'].str.slice(0, 4)
        data = data.drop([a,"Index"], axis=1)
        if data.empty:
            if a == "Tên người đánh giá":
                st.write("Bạn chưa không tham gia đánh giá quy trình kỹ thuật trong thời gian yêu cầu")
            else:
                st.write("Bạn chưa được đánh giá kỹ thuật thực hiện quy trình trong thời gian yêu cầu")
        else:
            if a == "Tên người đánh giá":
                st.write(f"Nhân viên {ten_ma} đã tham gia giám sát {len(data)} lần trong thời gian yêu cầu.")
                with st.expander("Thông tin chi tiết:"):
                    st.dataframe(data, hide_index=True)
            else:
                st.write(f"Nhân viên {ten_ma} đã được đánh giá kỹ thuật {len(data)} lần trong thời gian yêu cầu.")
                with st.expander("Thông tin chi tiết:"):
                    st.dataframe(data, hide_index=True)

# Main Section ####################################################################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
ten_ma = st.session_state.username
ten_ma = ten_ma[:-9]
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:#34eb89">THÔNG TIN TÀI KHOẢN</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Thông tin nhân viên</i></p>'
st.html(html_code)
data_canhan = load_data("Input-st-DSNS")
data_final = data_canhan.loc[data_canhan["Nhân viên"]==st.session_state.username]
data_final = data_final[["Mã số","Khối","Khoa","Họ và tên","Năm bắt đầu công tác","Ngày sinh","Bằng cấp chuyên môn","Phân cấp năng lực", "Email","Sđt"]]
st.dataframe(data_final, hide_index=True)
datags = load_data("Output-st-GSQT")
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=datetime.date(2025, 1, 1),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=datetime.date.today(),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    submit_thoigian = st.form_submit_button("Xem thống kê")
if submit_thoigian:
    if ed < sd:
        st.error("Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        xuli(datags,"Tên người đánh giá",ten_ma,sd,ed)
        xuli(datags,"Tên người thực hiện",ten_ma,sd,ed)