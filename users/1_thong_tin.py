import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
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

# @st.cache_data(ttl=20)
# def load_data_GSheet(name):
#     credentials = load_credentials()
#     gc = gspread.authorize(credentials)
#     sheet = gc.open(name).sheet1
#     data = sheet.get_all_records()
#     df = pd.DataFrame(data)
#     if "Nhân viên yêu cầu" in df.columns:
#         username = st.session_state.username
#         df = df[df["Nhân viên yêu cầu"] == username]
#         index = []
#         ngay_yc = []
#         loai_yc = []
#         nd_yc = []
#         tt = []
#         for i in range (0,len(df)):
#             index.append(int(i+1))
#             ngay_yc.append(df.iloc[i,1])
#             loai_yc.append(df.iloc[i,5])
#             nd_yc.append(df.iloc[i,6]) 
#             # nd_yc.append(df.iloc[i,5][:40]+"...") #40 kí tự chữ đầu
#             if df.iloc[i,7] == "" or df.iloc[i,7] == None:
#                 tt.append("Đang chờ")
#             else:
#                 if df.iloc[i,8] == "" or df.iloc[i,8] == None:
#                     tt.append("Đang cập nhât")
#                 elif df.iloc[i,8] == 1:
#                     tt.append("Hoàn thành")
#                 elif df.iloc[i,8] == 0:
#                     tt.append("Từ chối")
#         k = {"STT": pd.Series(index),
#             "Ngày gửi yêu cầu": pd.Series(ngay_yc),
#                 "Tình trạng": pd.Series(tt),
#                 "Loại yêu cầu": pd.Series(loai_yc),
#                 "Nội dung": pd.Series(nd_yc),
#                 }
#         df_yc = pd.DataFrame(k)

#         return df_yc
#     else:
#         return pd.DataFrame()
    
# @st.cache_data(ttl=3600)
# def highlight_status(val):
#     if val == "Hoàn thành":
#         color = "green"
#     elif val == "Đang cập nhât":
#         color = "orange"
#     elif val == "Từ chối":
#         color = "red"
#     else:
#         color = "black"
#     return f"color: {color}"

# def upload_data_yc():
#     credentials = load_credentials()
#     gc = gspread.authorize(credentials)
#     sheeto4 = st.secrets["sheet_name"]["output_4"]
#     sheet = gc.open(sheeto4).sheet1
#     column_index = len(sheet.get_all_values())
#     now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
#     column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
#     column_khoa = str(st.session_state.khoa_YC)
#     column_nvyc = str(st.session_state.username)
#     column_ttlh = str(st.session_state.ttlh)
#     column_loaiyc = str(st.session_state.lyc)
#     column_ndyc = str(st.session_state.ndyc)
#     sheet.append_row([  column_index,
#                         column_timestamp,
#                         column_khoa,
#                         column_nvyc,
#                         column_ttlh,
#                         column_loaiyc,
#                         column_ndyc,
#                      ])
#     st.toast("Yêu cầu đã được gửi!")

def xuli(data,a,ten_ma,sd,ed):
    # Chỉ lấy cột A đến N (14 cột)
    data = data.iloc[:, :14] if len(data.columns) > 14 else data
    
    data = data.loc[data[a] == st.session_state.username]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] <= pd.Timestamp(end_date))]
    if data.empty:
        if a == "Tên người đánh giá":
            st.warning("Không có dữ liệu tham gia giám sát trong khoảng thời gian yêu cầu")
        else:
            st.warning("Không có dữ liệu được giám sát trong khoảng thời gian yêu cầu")
    else:
        data.insert(0, 'ID', range(1, len(data) + 1))
        # Format các cột Tỉ lệ thành phần trăm (XX.XX%)
        def format_percentage(val):
            try:
                if val == "" or val is None:
                    return ""
                num = float(val)
                return f"{num * 100:.1f}%"
            except:
                return val
        
        if 'Tỉ lệ tuân thủ' in data.columns:
            data['Tỉ lệ tuân thủ'] = data['Tỉ lệ tuân thủ'].apply(format_percentage)
        if 'Tỉ lệ an toàn' in data.columns:
            data['Tỉ lệ an toàn'] = data['Tỉ lệ an toàn'].apply(format_percentage)
        if 'Tỉ lệ nhận dạng NB' in data.columns:
            data['Tỉ lệ nhận dạng NB'] = data['Tỉ lệ nhận dạng NB'].apply(format_percentage)
        
        data = data.drop([a,"STT"], axis=1)
        data["Data"] = data["Data"].str.replace("#", "\n")
        data["Data"] = data["Data"].str.replace("|", "  ")
        if data.empty:
            if a == "Tên người đánh giá":
                st.write("Bạn chưa giám sát quy trình kỹ thuật nào trong thời gian yêu cầu")
            else:
                st.write("Bạn chưa được giám sát quy trình kỹ thuật nào trong thời gian yêu cầu")
        else:
            if a == "Tên người đánh giá":
                html_code = f'<p class="ttcn"><i>Thông tin tham gia giám sát quy trình:</i></p>'
                st.html(html_code)
                st.write(f"Nhân viên {ten_ma} **đã tham gia giám sát {len(data)} lần** trong khoảng thời gian được chọn.")
                with st.expander("Thông tin chi tiết:"):
                    st.dataframe(data, hide_index=True)
            else:
                html_code = f'<p class="ttcn"><i>Thông tin được giám sát thực hiện quy trình:</i></p>'
                st.html(html_code)
                st.markdown(f"Nhân viên {ten_ma} **đã được giám sát {len(data)} lần** trong khoảng thời gian được chọn.")
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
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:#9F2B68">THÔNG TIN TÀI KHOẢN</p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
sheeti1 = st.secrets["sheet_name"]["input_1"]
data_canhan = load_data(sheeti1)
data_final = data_canhan.loc[data_canhan["Nhân viên"]==st.session_state.username]
data_final = data_final[["Mã số","Khối","Khoa","Họ và tên","Năm bắt đầu công tác","Ngày sinh","Bằng cấp chuyên môn","Phân cấp năng lực", "Email","Sđt"]]
data_final_dict = data_final.iloc[0].to_dict()
html_code = f"""
<div class="bangtt">
    <h4 style="color:#9F2B68;">📋 Thông tin nhân viên</h4>
    <table style="width:100%;">
        <tr><td><b>Mã số nhân viên:</b></td><td>{data_final_dict["Mã số"]}</td></tr>
        <tr><td><b>Khối:</b></td><td>{data_final_dict["Khối"]}</td></tr>
        <tr><td><b>Khoa:</b></td><td>{data_final_dict["Khoa"]}</td></tr>
        <tr><td><b>Họ và tên:</b></td><td>{data_final_dict["Họ và tên"]}</td></tr>
        <tr><td><b>Năm bắt đầu công tác:</b></td><td>{data_final_dict["Năm bắt đầu công tác"]}</td></tr>
        <tr><td><b>Ngày sinh:</b></td><td>{data_final_dict["Ngày sinh"]}</td></tr>
        <tr><td><b>Bằng cấp chuyên môn:</b></td><td>{data_final_dict["Bằng cấp chuyên môn"]}</td></tr>
        <tr><td><b>Phân cấp năng lực:</b></td><td>{data_final_dict["Phân cấp năng lực"]}</td></tr>
        <tr><td><b>Email:</b></td><td>{data_final_dict["Email"]}</td></tr>
        <tr><td><b>SĐT:</b></td><td>0{data_final_dict["Sđt"]}</td></tr>
    </table>
</div>
"""
st.markdown(html_code, unsafe_allow_html=True)
sheeto1 = st.secrets["sheet_name"]["output_1"]
datags = load_data(sheeto1)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) 
md = date(2025, 1, 1)
with st.form("Thời gian"):
    html_code = f'<p class="ttcn"><i>Thông tin giám sát cá nhân</i></p>'
    st.html(html_code)
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=md,
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=now_vn.date(),
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    submit_thoigian = st.form_submit_button("Xem thống kê")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        xuli(datags,"Tên người đánh giá",ten_ma,sd,ed)
        xuli(datags,"Tên người thực hiện",ten_ma,sd,ed)