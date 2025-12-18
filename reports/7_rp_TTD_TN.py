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
    data['Thời gian báo cáo'] = pd.to_datetime(data.iloc[:, 2], format='%Y-%m', errors='coerce')
    start_date = f"{sd.year}-{sd.month:02d}"
    end_date = f"{ed.year}-{ed.month:02d}"
    data_final = data[(data.iloc[:, 2] >= start_date) & (data.iloc[:, 2] <= end_date)
    ].reset_index(drop=True)
    idx = data_final.groupby(
            ["Thời gian báo cáo"]
        )["Thời gian báo cáo"].idxmax()

    # Lọc ra các dòng tương ứng
    data_final_latest = data_final.loc[idx].reset_index(drop=True)
    return data_final_latest

def format_permille(val): #def format phần nghìn (‰)
    if pd.isna(val):
        return "N/A"
    try:
        return f"{float(val):.2f}"
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

def tinh_metrics(data):
    data_temp = data.copy()
    
    data_temp['Loét hiện mắc'] = pd.to_numeric(
    data_temp['Loét hiện mắc'].astype(str).str.replace(',', '.'), 
    errors='coerce'
    )
    data_temp['Loét mắc mới'] = pd.to_numeric(
        data_temp['Loét mắc mới'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    data_temp['Số ca té ngã'] = pd.to_numeric(
        data_temp['Số ca té ngã'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    data_temp['Ngày điều trị'] = pd.to_numeric(
        data_temp['Ngày điều trị'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    ngay_dieu_tri_total = data_temp['Ngày điều trị'].sum()
    hien_mac = int(data_temp['Loét hiện mắc'].sum()) 
    data_temp['ti_suat_hien_mac'] = (data_temp['Loét hiện mắc'] / data_temp['Ngày điều trị']) * 1000
    ti_suat_hien_mac = round((hien_mac/ngay_dieu_tri_total)*1000,2)
    
    mac_moi = int(data_temp['Loét mắc mới'].sum())
    data_temp['ti_suat_mac_moi'] = (data_temp['Loét mắc mới'] / data_temp['Ngày điều trị']) * 1000
    ti_suat_mac_moi = round((mac_moi/ngay_dieu_tri_total)*1000,2)
    
    so_ca_te_nga = int(data_temp['Số ca té ngã'].sum())
    data_temp['ti_suat_te_nga'] = (data_temp['Số ca té ngã'] / data_temp['Ngày điều trị']) * 1000
    ti_suat_te_nga = round((so_ca_te_nga/ngay_dieu_tri_total)*1000,2)
    
    return {
        'hien_mac': hien_mac,
        'ti_suat_hien_mac': ti_suat_hien_mac,
        'mac_moi': mac_moi,
        'ti_suat_mac_moi': ti_suat_mac_moi,
        'so_ca_te_nga': so_ca_te_nga,
        'ti_suat_te_nga': ti_suat_te_nga,
    }

def ve_bieu_do_hien_mac_mac_moi(data):
    """Biểu đồ 1: Cột chồng hiện mắc và mắc mới theo tháng"""
    Bieu_do_1 = data.iloc[:, [2, 5, 6]].copy()
    data_bieu_do_1 = Bieu_do_1.copy()
    data_bieu_do_1['Tháng'] = pd.to_datetime(data_bieu_do_1['Thời gian báo cáo']).dt.strftime('%m/%Y')
    data_bieu_do_1 = data_bieu_do_1.dropna(subset=['Tháng'])

    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x= data_bieu_do_1['Tháng'],
        y= data_bieu_do_1['Loét hiện mắc'],
        name='Hiện mắc',
        marker_color='lightblue',
        textposition='inside',
    ))
    
    fig.add_trace(go.Bar(
        x=data_bieu_do_1['Tháng'],
        y=data_bieu_do_1['Loét mắc mới'],
        name='Mắc mới',
        marker_color='lightcoral',
        #text=data_bieu_do_1['Loét mắc mới'].round(0),
        textposition='inside',
    ))
    
    fig.update_layout(
        title='Biểu đồ 1: Số ca loét hiện mắc và mắc mới theo tháng',
        xaxis_title='Tháng',
        xaxis=dict(type='category',tickangle=0),
        yaxis_title='Số lượng ca',
        barmode='stack',
        height=450,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def ve_bieu_do_ti_suat(data):
    """Biểu đồ 2: Line tỉ suất hiện mắc và tỉ suất mắc mới theo tháng"""
    Bieu_do_2 = data.iloc[:, [2, 4, 5, 6]].copy()
    data_bieu_do_2 =  Bieu_do_2.copy()
    data_bieu_do_2['Tháng'] = data_bieu_do_2['Thời gian báo cáo'].dt.strftime('%m/%Y')
    data_bieu_do_2 = data_bieu_do_2.dropna(subset=['Tháng'])

    # Chuyển đổi dữ liệu
    data_bieu_do_2['Loét hiện mắc'] = pd.to_numeric(
        data_bieu_do_2['Loét hiện mắc'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    data_bieu_do_2['Loét mắc mới'] = pd.to_numeric(
        data_bieu_do_2['Loét mắc mới'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    data_bieu_do_2['Ngày điều trị'] = pd.to_numeric(
        data_bieu_do_2['Ngày điều trị'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )

    # Tính tỉ suất cho từng dòng
    data_bieu_do_2['Tỉ suất hiện mắc'] = (data_bieu_do_2['Loét hiện mắc'] / data_bieu_do_2['Ngày điều trị']) * 1000
    data_bieu_do_2['Tỉ suất mắc mới'] = (data_bieu_do_2['Loét mắc mới'] / data_bieu_do_2['Ngày điều trị']) * 1000
      
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data_bieu_do_2['Tháng'],
        y=data_bieu_do_2['Tỉ suất hiện mắc'],
        mode='lines+markers',
        name='Tỉ suất hiện mắc',
        line=dict(color='blue', width=3),
        marker=dict(size=5),
        hovertemplate='Tỉ suất loét hiện mắc: %{y:.2f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=data_bieu_do_2['Tháng'],
        y=data_bieu_do_2['Tỉ suất mắc mới'],
        mode='lines+markers',
        name='Tỉ suất mắc mới',
        line=dict(color='red', width=3),
        marker=dict(size=5),
        hovertemplate='Tỉ suất loét mắc mới: %{y:.2f}<extra></extra>'
    ))
    fig.update_layout(
        title='Biểu đồ 2: Tỉ suất loét hiện mắc và mắc mới theo tháng',
        xaxis_title='Tháng',
        xaxis=dict(type='category',tickangle=0),
        yaxis_title='Tỉ suất',
        height=450,
        hovermode='x unified',
        showlegend=True
    )
    return fig


def ve_bieu_do_te_nga(data):
    """Biểu đồ 3: Cột và line - số ca té ngã và tỉ suất té ngã"""
    Bieu_do_3 = data.iloc[:, [2, 4, 7]].copy()
    data_bieu_do_3 = Bieu_do_3.copy()
    data_bieu_do_3['Tháng'] = data_bieu_do_3['Thời gian báo cáo'].dt.strftime('%m/%Y')
    data_bieu_do_3 = data_bieu_do_3.dropna(subset=['Tháng'])
    
    # Chuyển đổi dữ liệu
    data_bieu_do_3['Số ca té ngã'] = pd.to_numeric(
        data_bieu_do_3['Số ca té ngã'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    data_bieu_do_3['Ngày điều trị'] = pd.to_numeric(
        data_bieu_do_3['Ngày điều trị'].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )
    # Tính tỉ suất té ngã
    data_bieu_do_3['Tỉ suất té ngã'] = (data_bieu_do_3['Số ca té ngã'] / data_bieu_do_3['Ngày điều trị']) * 1000
    # Tính min/max để đồng bộ gridline
    max_ca = data_bieu_do_3['Số ca té ngã'].max()
    max_ti_suat = data_bieu_do_3['Tỉ suất té ngã'].max()
    y1_max = int(np.ceil(max_ca))+2
    y2_max = y1_max * 0.1
    if max_ti_suat > y2_max:
        y2_max = np.ceil(max_ti_suat * 10) / 10
        y1_max = int(y2_max * 10)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data_bieu_do_3['Tháng'],
        y=data_bieu_do_3['Số ca té ngã'],
        name='Số ca té ngã',
        marker_color='lightblue',
        text=data_bieu_do_3['Số ca té ngã'].round(0),
        textposition='outside',
        yaxis='y',
        hovertemplate='Số ca té ngã: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=data_bieu_do_3['Tháng'],
        y=data_bieu_do_3['Tỉ suất té ngã'],
        mode='lines+markers',
        name='Tỉ suất té ngã',
        line=dict(color='orange', width=3),
        marker=dict(size=5),
        yaxis='y2',
        hovertemplate='Tỉ suất té ngã: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Biểu đồ 3: Số ca té ngã và tỉ suất té ngã theo tháng',
        xaxis_title='Tháng',
        xaxis=dict(type='category',tickangle=0),
        yaxis=dict(
            title=dict(text='Số ca té ngã'),
            range=[0, y1_max],
            dtick=1,
            showgrid=True),
        yaxis2=dict(
            title=dict(text='Tỉ suất té ngã'),
            overlaying='y',
            side='right',
            range=[0, y2_max],
            dtick= 0.1,
            showgrid=False
        ),
        height=450,
        hovermode='x unified',
        showlegend=True,
        #legend=dict(x=0.01, y=0.99)
    )
    return fig


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
        <p style="color:green">THỐNG KÊ SỐ LIỆU TỔN THƯƠNG DA DO ÁP LỰC VÀ TÉ NGÃ</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
md = date(2024, 1, 1)
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
    if (ed.year < sd.year) or (ed.year == sd.year and ed.month < sd.month):
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto10 = st.secrets["sheet_name"]["output_10"]
        data = load_data(sheeto10,sd,ed)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            metrics = tinh_metrics(data)
            st.markdown("##### 🚩 :red[TỔN THƯƠNG DA DO ÁP LỰC]")
            col1, col2 = st.columns([1,2])
            with col1:
                st.metric("**:blue[Số ca hiện mắc (Tổng)]**", f"{metrics['hien_mac']:.2f}",border=True)
            with col2:
                st.metric("**:blue[Tỉ suất hiện mắc/1000 ngày điều trị]**",  f"{metrics['ti_suat_hien_mac']:.2f}",border=True)

            col3, col4 = st.columns([1,2])
            with col3:
                st.metric("**:blue[Số ca mắc mới (Tổng)]**", f"{metrics['mac_moi']:.0f}",border=True)
            with col4:
                st.metric("**:blue[Tỉ suất mắc mới/1000 ngày điều trị]**", f"{metrics['ti_suat_mac_moi']:.2f}",border=True)
            
            st.markdown("<br></br>", unsafe_allow_html=True)
            st.markdown("##### 🚩 :red[TÉ NGÃ]")
            col5, col6 = st.columns([1,2])
            with col5:
                st.metric("**:blue[Số ca té ngã (Tổng)]**", f"{metrics['so_ca_te_nga']:,}",border=True)
            with col6:
                st.metric("**:blue[Tỉ suất số ca té ngã/1000 ngày điều trị]**", f"{metrics['ti_suat_te_nga']:.2f}",border=True)

            st.markdown("---")
            st.markdown("##### 📊 :red[BIỂU ĐỒ SO SÁNH]")
            
            # Biểu đồ 1: Hiện mắc và Mắc mới
            fig1 = ve_bieu_do_hien_mac_mac_moi(data)
            st.plotly_chart(fig1, use_container_width=True)
            
            # Biểu đồ 2: Tỉ suất
            fig2 = ve_bieu_do_ti_suat(data)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Biểu đồ 3: Té ngã
            fig3 = ve_bieu_do_te_nga(data)
            st.plotly_chart(fig3, use_container_width=True)