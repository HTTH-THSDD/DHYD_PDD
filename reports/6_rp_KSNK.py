import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np
import plotly.graph_objects as go

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
def load_data(x,sd,ed):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    idx = data_final.groupby(
            ["Ngày báo cáo"]
        )["Timestamp"].idxmax()

    # Lọc ra các dòng tương ứng
    data_final_latest = data_final.loc[idx].reset_index(drop=True)
    return data_final_latest

def format_permille(val): #def format phần nghìn (‰)
    if pd.isna(val):
        return "N/A"
    try:
        return f"{float(val):.2f}‰"
    except:
        return str(val)


def format_percent(val): #def format phần trăm (%)
    if pd.isna(val):
        return "N/A"
    try:
        return f"{float(val):.2f}%"
    except:
        return str(val)

def to_mau_dong_cuoi(data):
    def highlight(row):
        if row.name == len(data) - 1:
            return ['background-color: #ffe599; color: #cf1c00'] * len(row)
        return [''] * len(row)
    return highlight







##################################### Main Section ###############################################
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
        <p style="color:green">THỐNG KÊ SỐ LIỆU KIỂM SOÁT NHIỄM KHUẨN</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
md = date(2025, 1, 1)
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=now_vn.date(),
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
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto9 = st.secrets["sheet_name"]["output_9"]
        data = load_data(sheeto9,sd,ed)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            numeric_start_col = 4  # Bắt đầu từ cột thứ 5 (index 4)
            
            for i in range(numeric_start_col, len(data.columns)):
                data.iloc[:, i] = data.iloc[:, i].astype(str).str.replace(',', '.', regex=False)               
                data.iloc[:, i] = pd.to_numeric(data.iloc[:, i], errors='coerce')
            
            cot_phan_nghin = [4, 5, 6, 7, 8]  # Index của các cột cần nhân 1000
            for i in cot_phan_nghin:
                if i < len(data.columns):
                    data.iloc[:, i] = data.iloc[:, i] * 1000
            
            cot_phan_tram = [9,10,11] 
            for i in cot_phan_tram:
                if i < len(data.columns):
                    data.iloc[:, i] = data.iloc[:, i] * 100

            data.iloc[:, numeric_start_col:] = data.iloc[:, numeric_start_col:].fillna(0)
            
            if data.empty:
                st.error("❌ Không có dữ liệu hợp lệ sau khi chuyển đổi. Vui lòng kiểm tra dữ liệu trong Google Sheets.")
                st.stop()
            
            
            #### Ô trung bình NKBV mắc mới (Cột 4)
            TB_NKBV_ToanVien = data.iloc[:, 5].mean()
            st.markdown("##### 🚨 :orange[TỈ SUẤT NHIỄM KHUẨN BỆNH VIỆN MẮC MỚI]")
            col_metric = st.columns([1, 2, 1])
            with col_metric[1]:
                st.metric(
                    label="",
                    value=f"{TB_NKBV_ToanVien:.2f}‰" if not np.isnan(TB_NKBV_ToanVien) else "N/A",
                    delta=None
                )
            
            st.markdown("---")
            
            # ============= BẢNG 1: Nhiễm khuẩn bệnh viện mắc mới khối Hồi sức =============
            
            st.markdown("##### 🚩 :red[Nhiễm khuẩn bệnh viện mắc mới khối Hồi sức]")
            Data_Bang_1 = data.iloc[:, [2, 5, 6, 7, 8]].copy()
            Ten_Cot_Bang_1 = ['Ngày báo cáo','NKBV mắc mới khối Hồi sức','VAP','CLABSI','CAUTI']
            Data_Bang_1.columns = Ten_Cot_Bang_1
            
            # Tính dòng trung bình (chỉ tính các cột số)
            TB_Bang_1 = {}
            TB_Bang_1['Ngày báo cáo'] = 'Trung bình'
            for col in ['NKBV mắc mới khối Hồi sức','VAP','CLABSI','CAUTI']:
                TB_Bang_1[col] = Data_Bang_1[col].mean()
            
            Dong_TB_Bang_1 = pd.DataFrame([TB_Bang_1])
            Bang_1_display = pd.concat([Data_Bang_1, Dong_TB_Bang_1], ignore_index=True)
            Bang_1_styled = Bang_1_display.copy()
            
            for col in ['NKBV mắc mới khối Hồi sức','VAP','CLABSI','CAUTI']:
                Bang_1_styled[col] = Bang_1_styled[col].apply(format_permille)
            styled_df1 = Bang_1_styled.style.apply(to_mau_dong_cuoi(Bang_1_styled), axis=1)
            st.dataframe(
                styled_df1,
                use_container_width=True,
                hide_index=True
            )
           
            # Chuẩn bị dữ liệu cho biểu đồ (không bao gồm dòng trung bình)
            chart1_data = Data_Bang_1.copy()
            try:
                chart1_data['Tháng'] = pd.to_datetime(chart1_data['Ngày báo cáo'], errors='coerce').dt.strftime('%m/%Y')
            except:
                chart1_data['Tháng'] = chart1_data['Ngày báo cáo']
            
            # Loại bỏ các dòng có Tháng là NaT
            chart1_data = chart1_data.dropna(subset=['Tháng'])
            fig1 = go.Figure()
            
            # Thêm biểu đồ cột cho Cột 5
            fig1.add_trace(go.Bar(
                x=chart1_data['Tháng'],
                y=chart1_data['NKBV mắc mới khối Hồi sức'],
                name='NKBV mắc mới khối Hồi sức',
                marker_color='lightblue',
                yaxis='y'
            ))
            
            # Thêm các đường cho Cột 6, 7, 8
            colors = ['red', 'green', 'orange']
            for idx, col in enumerate(['VAP','CLABSI','CAUTI']):
                fig1.add_trace(go.Scatter(
                    x=chart1_data['Tháng'],
                    y=chart1_data[col],
                    name=col,
                    mode='lines+markers',
                    line=dict(color=colors[idx], width=2),
                    marker=dict(size=8),
                    yaxis='y'
                ))
            
            fig1.update_layout(
                title='Tỉ suất nhiễm khuẩn bệnh viện mắc mới khối Hồi sức theo thời gian',
                xaxis_title='Tháng',
                yaxis_title='Giá trị (‰)',
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=500
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            st.markdown("---")
            
            # ============= BẢNG 2: Tỉ lệ giám sát vệ sinh tay =============
            
            st.markdown("##### 🧼 :red[Tỉ lệ giám sát vệ sinh tay]")
            Data_Bang_2 = data.iloc[:, [2, 9, 10, 11]].copy()
            Ten_Cot_Bang_2 = ['Ngày báo cáo', 'VST trực tiếp', 'VST camera', 'VST ngoại khoa']
            Data_Bang_2.columns = Ten_Cot_Bang_2
            
            # Tính dòng trung bình
            TB_Bang_2 = {}
            TB_Bang_2['Ngày báo cáo'] = 'Trung bình'
            for col in ['VST trực tiếp', 'VST camera', 'VST ngoại khoa']:
                TB_Bang_2[col] = Data_Bang_2[col].mean()
            
            Dong_TB_Bang_2 = pd.DataFrame([TB_Bang_2])
            
            # Gộp dòng trung bình vào bảng
            Bang_2_display = pd.concat([Data_Bang_2, Dong_TB_Bang_2], ignore_index=True)
            Bang_2_styled = Bang_2_display.copy()
            for col in ['VST trực tiếp', 'VST camera', 'VST ngoại khoa']:
                Bang_2_styled[col] = Bang_2_styled[col].apply(format_percent)
            
            styled_df2 = Bang_2_styled.style.apply(to_mau_dong_cuoi(Bang_2_styled), axis=1)
            st.dataframe(
                styled_df2,
                use_container_width=True,
                hide_index=True
            )
            
            # Chuẩn bị dữ liệu cho biểu đồ
            chart2_data = Data_Bang_2.copy()
            try:
                chart2_data['Tháng'] = pd.to_datetime(chart2_data['Ngày báo cáo'], errors='coerce').dt.strftime('%m/%Y')
            except:
                chart2_data['Tháng'] = chart2_data['Ngày báo cáo']
            
            # Loại bỏ các dòng có Tháng là NaT
            chart2_data = chart2_data.dropna(subset=['Tháng'])
            fig2 = go.Figure()
            
            # Thêm các đường cho Cột 9, 10, 11
            colors2 = ['blue', 'purple', 'teal']
            for idx, col in enumerate(['VST trực tiếp', 'VST camera', 'VST ngoại khoa']):
                fig2.add_trace(go.Scatter(
                    x=chart2_data['Tháng'],
                    y=chart2_data[col],
                    name=col,
                    mode='lines+markers',
                    line=dict(color=colors2[idx], width=2),
                    marker=dict(size=8), 
                ))
            
            fig2.update_layout(
                title='Tỉ lệ giám sát vệ sinh tay theo thời gian',
                xaxis_title='Tháng',
                yaxis_title='Giá trị (%)',
                yaxis=dict(
                    range=[0, 100],  # Giá trị từ 0-100%
                    tickmode='linear',
                    tick0=0,
                    dtick=20  # Khoảng chia là 20%
                ),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=500
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            