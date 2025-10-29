import streamlit as st
import pandas as pd
import gspread
import datetime
import pathlib
import base64
import time
import html

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

#########################################################################################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&reg;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:#b36002; padding-left:25px">THÔNG TIN GHI NHỚ</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="admin_1"><i>Xin chào admin:{st.session_state.username}</i></p>'
st.html(html_code)

st.markdown("""
    <br>
    <p style="font-size: 15px; color: #333;">
        <span style="color: #b80f04; font-weight: bold;">PHÂN QUYỀN</span> 
        <br><br>
        <span style="color: #042f66; font-weight: bold;">1. Quản trị viên (admin):</span> Có quyền truy cập và quản lý toàn bộ hệ thống, bao gồm việc thêm, sửa, xóa người dùng và phân quyền.
        <br><br>
        <span style="color: #042f66; font-weight: bold;">2. Quản trị viên (admin):</span> Có quyền truy cập và quản lý toàn bộ hệ thống, bao gồm việc thêm, sửa, xóa người dùng.
        <br><br>
        <span style="color: #042f66; font-weight: bold;">3. Người dùng (user) - Nhóm lâm sàng PĐD:</span> Có quyền truy cập và sử dụng các chức năng, được phân quyền <b>toàn viện</b>.
        <br><br>
        <span style="color: #042f66; font-weight: bold;">4. Người dùng (user) - ĐD Trưởng Khoa/Đơn nguyên:</span> Có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>Khoa/Đơn nguyên trực tiếp quản lý,</b> Không bao gồm các chức năng liên quan đến KSNK và Loét tì đè.
        <br><br>
        <span style="color: #042f66; font-weight: bold;">5. Người dùng (user) - ĐD viên + QTKT + CSCS + PRIME:</span> Có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả, xem được thống kê cá nhân, xem được Thống kê báo cáo: QTKT, CSCS, PRIME).</b>
        <br><br>
        <span style="color: #042f66; font-weight: bold;">6. Người dùng (user) - ĐD viên + HSBA + GDSK:</span> Chỉ có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả, xem được thống kê cá nhân, xem được Thống kê báo cáo: HSBA, GDSK).</b>
        <br><br>
        <span style="color: #042f66; font-weight: bold;">7. Người dùng (user) - ĐD viên + VTTB + PCCS:</span> Chỉ có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả, xem được thống kê cá nhân, xem được Thống kê báo cáo: VTTB, PCCS).</b>
        <br><br>
        <span style="color: #042f66; font-weight: bold;">8. Người dùng (user) - ĐD viên + QTKT + CSCS + PRIME + VTTB + PCCS:</span> Chỉ có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả, xem được thống kê cá nhân, xem được Thống kê báo cáo: QTKT, CSCS, PRIME, VTTB, PCCS).</b>
        <br><br>
        <span style="color: #042f66; font-weight: bold;">9. Người dùng (user) - ĐD viên + HSBA + GDSK + VTTB + PCCS:</span> Chỉ có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả, xem được thống kê cá nhân, xem được Thống kê báo cáo: HSBA, GDSK, VTTB, PCCS).</b>
        <br><br>
        <span style="color: #042f66; font-weight: bold;">10. Người dùng (user) - ĐD viên:</span> Chỉ có quyền truy cập và sử dụng các chức năng, được phân quyền theo <b>cá nhân (vào được tất cả Nhập kết quả nhưng chỉ xem được thống kê cá nhân, không hiện mục Thống kê báo cáo).</b>
    </p>
""", unsafe_allow_html=True)

