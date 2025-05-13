import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = pathlib.Path("asset/style.css")

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)

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
@st.cache_data(ttl=10)
def load_data1(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    return data


@st.cache_data(ttl=10)
def load_data(x,sd,ed,khoa_select):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    if khoa_select == "Tất cả" and st.session_state.username == st.secrets["user_special"]["u1"]:
        khoa_select = [st.secrets["user_special"]["u1_khoa1"],
                        st.secrets["user_special"]["u1_khoa2"],
                        st.secrets["user_special"]["u1_khoa3"],]
    if khoa_select == "Tất cả" and st.session_state.username == st.secrets["user_special"]["u2"]:
        khoa_select = [st.secrets["user_special"]["u2_khoa1"],
                            st.secrets["user_special"]["u2_khoa2"]]
    if khoa_select == "Tất cả" and st.session_state.username == st.secrets["user_special"]["u3"]:
        khoa_select = [st.secrets["user_special"]["u3_khoa1"],
                            st.secrets["user_special"]["u3_khoa2"]]
    if khoa_select == "Tất cả" and st.session_state.phan_quyen in ["1","2","3"]:
        khoa_select = data["Khoa"]
    data = data.loc[data["Khoa"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def chuyendoi_phantram(df,x):
    df[x] = df[x].str.replace(',', '.')
    df[x] = pd.to_numeric(df[x], errors='coerce')
    df[x] = df[x] * 100
    return df

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    if y == "Chi tiết":
        df = pd.DataFrame(df).sort_values(["Khoa"])
        df = pd.DataFrame(df).sort_values("Timestamp", ascending=True)
        df = chuyendoi_phantram(df,"Tỉ lệ hiểu")
        df = chuyendoi_phantram(df,"Tỉ lệ biết")
        df = chuyendoi_phantram(df,"Tỉ lệ không biết")
        df = df.drop("Data",axis=1)
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [st.secrets["user_special"]["u1"],st.secrets["user_special"]["u2"],st.secrets["user_special"]["u3"]]:
            df = df.drop("Khoa",axis=1)
        return df
    else:
        df = pd.DataFrame(df).drop("STT",axis=1)
        df = pd.DataFrame(df).sort_values("Khoa")
        df = pd.DataFrame(df).sort_values("Timestamp", ascending=False)
        df = chuyendoi_phantram(df,"Tỉ lệ hiểu")
        df = chuyendoi_phantram(df,"Tỉ lệ biết")
        df = chuyendoi_phantram(df,"Tỉ lệ không biết")
        df["Tháng"] = df["Timestamp"].dt.strftime("%m/%Y")
        df = df.groupby(["Tháng","Khoa"]).agg({
        "Tháng": "count",
        "Tỉ lệ hiểu": "mean",
        "Tỉ lệ biết": "mean",
        "Tỉ lệ không biết": "mean",
        }).rename(columns={"Tháng": "Số lượt"}).reset_index()
        df.insert(0, 'STT', range(1, len(df) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [st.secrets["user_special"]["u1"],st.secrets["user_special"]["u2"],st.secrets["user_special"]["u3"]]:
            df=df.drop("Khoa",axis=1)
        return df
    
def chon_khoa(khoa):
    placeholder1 = st.empty()
    if st.session_state.phan_quyen in ["1","2","3"]:
        if st.checkbox("Chọn tất cả khoa"):
            placeholder1.empty()
            khoa_select = "Tất cả"
        else:
            with placeholder1:
                khoa_select = st.multiselect(label="Chọn khoa",
                                                  options= khoa.unique())
            st.write("Hãy chọn khoa xem thống kê")
        return khoa_select
    else:
        if st.session_state.username == st.secrets["user_special"]["u1"]:
            if st.checkbox("Cả 3 khoa"):
                placeholder1.empty()
                khoa_select = "Tất cả"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u1_khoa1"],
                            st.secrets["user_special"]["u1_khoa2"],
                            st.secrets["user_special"]["u1_khoa3"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u2"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Tất cả"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u2_khoa1"],
                            st.secrets["user_special"]["u2_khoa2"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u3"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Tất cả"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u3_khoa1"],
                            st.secrets["user_special"]["u3_khoa2"]])
            return khoa_select
        else:
            khoa_select = st.session_state.khoa
            khoa_select = [khoa_select]
            return khoa_select
##################################### Main Section ###############################################
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:green">THỐNG KÊ GIÁO DỤC SỨC KHỎE</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 = st.secrets["sheet_name"]["input_1"]
data = load_data1(sheeti1)
khoa = data["Khoa"]
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) 
md = date(2025, 1, 1)
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value= md,
        min_value= md,
        max_value= now_vn.date(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=now_vn.date(),
        min_value= md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    khoa_select = chon_khoa(khoa)
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto3 = st.secrets["sheet_name"]["output_3"]
        data = load_data(sheeto3,sd,ed,khoa_select)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            with st.expander("Thống kê tổng quát"):
                thongke = tao_thong_ke(data,"Tổng quát")
                st.dataframe(thongke, 
                            hide_index=True,
                            column_config = {
                        "Tỉ lệ hiểu": st.column_config.NumberColumn(format="%.2f %%"),
                        "Tỉ lệ biết": st.column_config.NumberColumn(format="%.2f %%"),
                        "Tỉ lệ không biết": st.column_config.NumberColumn(format="%.2f %%"),
                            })
            with st.expander("Thống kê chi tiết"):
                thongkechitiet = tao_thong_ke(data,"Chi tiết")
                st.dataframe(thongkechitiet,
                        hide_index=True,
                        column_config = {
                        "Tỉ lệ hiểu": st.column_config.NumberColumn(format="%.2f %%"),
                        "Tỉ lệ biết": st.column_config.NumberColumn(format="%.2f %%"),
                        "Tỉ lệ không biết": st.column_config.NumberColumn(format="%.2f %%"),
                        })

    


