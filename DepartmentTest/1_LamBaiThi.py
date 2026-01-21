import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import re
import random
import time

@st.cache_data(ttl=360)
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
    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return credentials

@st.cache_data(ttl=360)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

@st.cache_data(ttl=360)
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

@st.cache_data(ttl=600) #Thời gian cache tự load lại file sau 10 phút
def load_sheet_data(sheet_name, worksheet_index):
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        sheet = gc.open(sheet_name).get_worksheet(worksheet_index)
        data = sheet.get_all_values()
        if len(data) > 0:
            header = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=header)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi load dữ liệu từ sheet {sheet_name}, worksheet {worksheet_index}: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=600)  #Thời gian cache tự load lại file sau 10 phút
def load_sheet_by_name(sheet_name, worksheet_name):
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open(sheet_name)
        
        try:
            sheet = spreadsheet.worksheet(worksheet_name)
            data = sheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            worksheet_map = {
                "Sheet 0": 0, "Sheet 1": 1, "Sheet 2": 2,
            }
            if worksheet_name in worksheet_map:
                idx = worksheet_map[worksheet_name]
                sheet = spreadsheet.get_worksheet(idx)
                data = sheet.get_all_values()
            else:
                sheet = spreadsheet.get_worksheet(0)
                data = sheet.get_all_values()
        
        if len(data) > 0:
            header = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=header)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def save_result_to_sheet(result_data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto = st.secrets["sheet_name"]["output_11"]
    sheet = gc.open(sheeto).sheet1
    sheet.append_row(result_data)

def check_existing_submission(ma_de, user, khoa, ngay):
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        sheeto = st.secrets["sheet_name"]["output_11"]
        sheet = gc.open(sheeto).sheet1
        data = sheet.get_all_values()
        
        if len(data) <= 1:
            return False    
        df = pd.DataFrame(data[1:], columns=data[0])
        existing = df[
            (df['Mã đề'].astype(str).str.strip() == str(ma_de).strip()) & 
            (df['Nhân viên'].astype(str).str.strip() == str(user).strip()) & 
            (df['Khoa'].astype(str).str.strip() == str(khoa).strip()) & 
            (df['Ngày thực hiện'].astype(str).str.strip() == str(ngay).strip())
        ]
        # Nếu có bản ghi đã tồn tại, không cho nộp lại
        if len(existing) > 0:
            return True
        return False
    except Exception as e:
        st.error(f"❌ Lỗi kiểm tra: {str(e)}")
        return False

def get_next_stt(sheeto):
    """Lấy STT tiếp theo liên tục"""
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        sheet = gc.open(sheeto).sheet1
        data = sheet.get_all_values()
        if len(data) <= 1:
            return 1    
        # Lấy STT cuối cùng từ cột A (index 0)
        df = pd.DataFrame(data[1:], columns=data[0])     
        try:
            last_stt = int(df['STT'].iloc[-1])
            return last_stt + 1
        except:
            return len(data)  
    except Exception as e:
        st.error(f"❌ Lỗi lấy STT: {str(e)}")
        return len(data) if len(data) > 0 else 1

def thong_tin_hanh_chinh():
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data_nv = load_data(sheeti1)
    chon_khoa = st.selectbox("Khoa/Đơn vị ",
                             options=data_nv["Khoa"].unique(),
                             index=None,
                             placeholder="",
                             key="khoa_select"
                             )
    if chon_khoa:
        st.session_state.khoa_THI = chon_khoa
    else:
        if "khoa_THI" in st.session_state:
            del st.session_state["khoa_THI"]

def hien_thi_header():
    try:
        img = get_img_as_base64("pages/img/logo.png")
        css_path = pathlib.Path("asset/style.css")
        load_css(css_path)
        st.markdown(f"""
            <div class="fixed-header">
                <div class="header-content">
                    <img src="data:image/png;base64,{img}" alt="logo">
                    <div class="header-text">
                        <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
                    </div>
                </div>
                <div class="header-subtext">
                <p>HỆ THỐNG KIỂM TRA LÝ THUYẾT</p>
                </div>
            </div>
            <div class="header-underline"></div>
         """, unsafe_allow_html=True)
    except:
        st.title("HỆ THỐNG KIỂM TRA LÝ THUYẾT")
    
    if 'username' in st.session_state:
        html_code = f'<p class="demuc"><i>Nhân viên thực hiện: {st.session_state.username}</i></p>'
        st.html(html_code)

def hien_thi_cau_hoi_trac_nghiem(stt, question, answers_text, results_text):
    st.markdown(f"### Câu {stt}: {question}")
    
    # Parse answers và results
    answer_list = [ans.strip() for ans in answers_text.split('\n') if ans.strip()]
    result_list = [res.strip() for res in results_text.split('\n') if res.strip()]
    
    # Đóng gói câu trả lời với kết quả
    if f"q_{stt}_mapping" not in st.session_state:
        answer_result_pairs = list(zip(answer_list, result_list))
        random.shuffle(answer_result_pairs)
        st.session_state[f"q_{stt}_mapping"] = answer_result_pairs
    
    pairs = st.session_state[f"q_{stt}_mapping"]
    display_options = [pair[0] for pair in pairs]
    
    selected = st.radio(
        "Chọn đáp án đúng nhất:",
        display_options,
        key=f"question_{stt}",
        index=None
    )
    
    if selected:
        for pair in pairs:
            if pair[0] == selected:
                st.session_state.answers[stt] = {
                    'answer': selected,
                    'result': pair[1]
                }
                break

def hien_thi_cau_hoi_dung_sai(stt, question, answers_text, results_text):
    st.markdown(f"### Câu {stt}: {question}")
    answer_statements = [ans.strip() for ans in answers_text.split('\n') if ans.strip()]
    correct_results = [res.strip() for res in results_text.split('\n') if res.strip()]
    if stt not in st.session_state.answers:
        st.session_state.answers[stt] = {}
    
    for i, statement in enumerate(answer_statements):
        col1, col2 = st.columns([2, 5])
        with col1:
            choice = st.radio(
                "Chọn:",
                ["Đúng", "Sai"],
                key=f"question_{stt}_sub_{i}",
                horizontal=True,
                label_visibility="collapsed",
                index=None
            )
            if choice:
                st.session_state.answers[stt][i] = {
                    'answer': choice,
                    'correct': correct_results[i] if i < len(correct_results) else 'Đúng'
                }
        with col2:
            st.markdown(f"{statement}")

def tinh_diem_va_ket_qua(exam_questions):
    total_score = 0
    result_string = ""
    
    # Group by STT để chỉ xử lý mỗi câu 1 lần
    unique_questions = exam_questions.drop_duplicates(subset=['STT câu hỏi'])
    
    for idx, row in unique_questions.iterrows():
        stt = row["STT câu hỏi"]
        question_type = row["Loại câu hỏi"]
        answers_text = row["Câu trả lời"]
        correct_results = row["Kết quả"]
        
        if question_type == "Trắc nghiệm":
            user_data = st.session_state.answers.get(stt, {})
            
            if user_data:
                user_answer = user_data.get('answer', '')
                user_result = user_data.get('result', '')
                
                # Kiểm tra nếu kết quả của đáp án đã chọn là "Đúng"
                if user_result == "Đúng":
                    total_score += 1
                
                result_string += f"{stt}|{user_answer}#"
            else:
                result_string += f"{stt}|#"
            
        elif question_type == "Đúng/Sai":
            answer_statements = [ans.strip() for ans in answers_text.split('\n') if ans.strip()]
            user_data = st.session_state.answers.get(stt, {})
            
            user_answer_list = []
            correct_count = 0
            
            for i in range(len(answer_statements)):
                if i in user_data:
                    ans_data = user_data[i]
                    user_choice = ans_data.get('answer', '')
                    correct_choice = ans_data.get('correct', '') 
                    user_answer_list.append(user_choice)       
                    # So sánh đáp án người dùng với đáp án đúng
                    if user_choice == correct_choice:
                        correct_count += 1
                else:
                    user_answer_list.append("Chưa trả lời")
            
            # Tính điểm = số câu đúng / tổng số câu
            #score = round(correct_count / len(answer_statements), 2) if len(answer_statements) > 0 else 0
            #total_score += score
            total_score += correct_count
            result_string += f"{stt}|{'-'.join(user_answer_list)}#"
    
    result_string = result_string.rstrip('#')
    return total_score, result_string

def kiem_tra_hoan_thanh(exam_questions):
    unique_questions = exam_questions.drop_duplicates(subset=['STT câu hỏi'])
    
    for idx, row in unique_questions.iterrows():
        stt = row["STT câu hỏi"]
        question_type = row["Loại câu hỏi"]
        
        if question_type == "Trắc nghiệm":
            if stt not in st.session_state.answers or not st.session_state.answers[stt]:
                return False
        elif question_type == "Đúng/Sai":
            answers_text = row["Câu trả lời"]
            num_statements = len([ans.strip() for ans in answers_text.split('\n') if ans.strip()])
            if stt not in st.session_state.answers or len(st.session_state.answers[stt]) < num_statements:
                return False
            for i in range(num_statements):
                if i not in st.session_state.answers[stt] or not st.session_state.answers[stt][i]:
                    return False
    return True

# Main ########################################################################
if 'exam_started' not in st.session_state:
    st.session_state.exam_started = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# CSS cho fixed timer
st.markdown("""
<style>
    .fixed-timer {
        position: fixed;
        top: 400px;
        right: 20px;
        z-index: 9999;
        background-color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .timer-text {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    .timer-red {
        color: #ff4b4b;
    }
    .timer-blue {
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Placeholder cho timer
timer_placeholder = st.empty()

# Main Section
hien_thi_header()
thong_tin_hanh_chinh()

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
st.date_input(
    label="Ngày kiểm tra lý thuyết ",
    value=now_vn.date(),
    format="DD/MM/YYYY",
    key="ngay_kiem_tra",
    max_value=now_vn.date(),
)

sheeti8 = st.secrets["sheet_name"]["input_8"]
df_config = load_sheet_by_name(sheeti8, "Sheet 2")
df_questions_all = load_sheet_by_name(sheeti8, "Sheet 3")
ma_de_list = []

if len(df_config) > 0:
    df_config_active = df_config[df_config["Trạng thái"].astype(str).str.upper() == "ON"]
    ma_de_list = df_config_active["Tên bộ câu hỏi"].unique().tolist()
elif len(df_questions_all) > 0:
    ma_de_list = df_questions_all["Tên bộ câu hỏi"].unique().tolist()

ma_de_input = st.text_input(
    label="Nhập mã đề",
    key="ma_de_input",
    placeholder="Nhập mã đề thi..."
)
ma_de_input = ma_de_input.upper()

if ma_de_input:
    if len(ma_de_list) > 0 and ma_de_input in ma_de_list:
        st.success(f"✅ Mã đề đã được chọn: **{ma_de_input}**")
        st.session_state.ma_de = ma_de_input
        st.session_state.ma_de_valid = True
    else:
        st.error("❌ Mã đề chưa đúng hoặc chưa được mở")
        if "ma_de" in st.session_state:
            del st.session_state["ma_de"]
        st.session_state.ma_de_valid = False
else:
    if "ma_de" in st.session_state:
        del st.session_state["ma_de"]
    if "ma_de_valid" in st.session_state:
        del st.session_state["ma_de_valid"]

can_start = (
    "khoa_THI" in st.session_state and st.session_state.khoa_THI and
    "ngay_kiem_tra" in st.session_state and st.session_state.ngay_kiem_tra and
    "ma_de" in st.session_state and st.session_state.ma_de and
    "ma_de_valid" in st.session_state and st.session_state.ma_de_valid and
    len(ma_de_list) > 0
)

if can_start and not st.session_state.exam_started:
    if st.button("🚀 Bắt đầu làm bài", type="primary", use_container_width=True):
        ngay_str = st.session_state.ngay_kiem_tra.strftime("%Y-%m-%d")
        
        if check_existing_submission(st.session_state.ma_de, st.session_state.username, 
                                    st.session_state.khoa_THI, ngay_str):
            st.error("⚠️ Bạn đã nộp bài rồi, không thể thi lại!")
        else:
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.session_state.answers = {}
            st.session_state.submitted = False
            st.rerun()

# Phần làm bài thi
if st.session_state.exam_started and not st.session_state.submitted:
    # Kiểm tra xem ma_de còn tồn tại không
    if "ma_de" not in st.session_state or not st.session_state.ma_de:
        st.error("❌ Phiên làm bài đã kết thúc, vui lòng bắt đầu lại")
        st.session_state.exam_started = False
        st.session_state.submitted = False
        st.rerun()
        st.stop()
    
    ma_de = st.session_state.ma_de
    
    df_questions = load_sheet_by_name(sheeti8, "Sheet 1")
    if len(df_questions) == 0:
        st.error("❌ Không tìm thấy dữ liệu câu hỏi!")
        if st.button("🔙 Quay lại"):
            st.session_state.exam_started = False
            st.rerun()
        st.stop()
    
    exam_questions = df_questions[df_questions["Tên bộ câu hỏi"] == ma_de]
    
    if len(exam_questions) == 0:
        st.error(f"❌ Không tìm thấy câu hỏi cho mã đề: {ma_de}")
        if st.button("🔙 Quay lại"):
            st.session_state.exam_started = False
            st.rerun()
        st.stop()
    
    df_config = load_sheet_by_name(sheeti8, "Sheet 2")
    
    if len(df_config) > 0:
        exam_config = df_config[df_config["Tên bộ câu hỏi"] == ma_de]
        if len(exam_config) > 0:
            time_limit = int(exam_config.iloc[0]["Thời gian tối đa (phút)"]) * 60
        else:
            time_limit = 10 * 60
    else:
        time_limit = 10 * 60
    
    # Hiển thị đồng hồ cố định
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = max(0, time_limit - elapsed_time)
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    color_class = "timer-red" if remaining_time < 300 else "timer-blue"
    
    timer_placeholder.markdown(f"""
    <div class="fixed-timer">
        <p class="timer-text {color_class}">⏱️ {minutes:02d}:{seconds:02d}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if remaining_time == 0:
        st.session_state.submitted = True
        st.rerun()
    
    st.markdown("---")
    
    # Hiển thị câu hỏi (unique only)
    unique_questions = exam_questions.drop_duplicates(subset=['STT câu hỏi'])
    
    for idx, row in unique_questions.iterrows():
        stt = row["STT câu hỏi"]
        question = row["Câu hỏi"]
        question_type = row["Loại câu hỏi"]
        answers_text = row["Câu trả lời"]
        results_text = row["Kết quả"]
        
        if question_type == "Trắc nghiệm":
            hien_thi_cau_hoi_trac_nghiem(stt, question, answers_text, results_text)
        elif question_type == "Đúng/Sai":
            hien_thi_cau_hoi_dung_sai(stt, question, answers_text, results_text)
        
        st.markdown("---")
    
    if st.button("📝 Nộp bài", type="primary", use_container_width=True):
        if not kiem_tra_hoan_thanh(exam_questions):
            st.warning("⚠️ Bạn cần trả lời hết câu hỏi để có thể nộp bài!")
            # Nút xác nhận nộp bài chưa chạy được
            # if st.button("✅ Xác nhận nộp bài", type="secondary"):
            #     st.session_state.submitted = True
            #     st.rerun()
        else:
            st.session_state.submitted = True
            st.rerun()

# Trang kết quả
if st.session_state.submitted:
    timer_placeholder.empty()
    st.success("✅ Bài thi đã được nộp thành công!")

    # Kiểm tra xem ma_de còn tồn tại không
    if "ma_de" not in st.session_state or not st.session_state.ma_de:
        st.error("❌ Lỗi: Không tìm thấy mã đề")
        st.stop()

    ma_de = st.session_state.ma_de
    df_questions = load_sheet_by_name(sheeti8, "Sheet 1")
    
    if len(df_questions) == 0:
        st.error("❌ Lỗi: Không tìm thấy dữ liệu câu hỏi")
        st.stop()
    
    exam_questions = df_questions[df_questions["Tên bộ câu hỏi"] == ma_de]
    df_config = load_sheet_by_name(sheeti8, "Sheet 2")
    
    max_score = 10
    loai_bo_cau_hoi = "N/A"
    if len(df_config) > 0:
        exam_config = df_config[df_config["Tên bộ câu hỏi"].astype(str).str.strip() == str(ma_de).strip()]
        if len(exam_config) > 0:
            max_score = int(exam_config.iloc[0]["Điểm số tối đa"])
            # Lấy loại bộ câu hỏi từ exam_config
            for cot in exam_config.columns:
                if 'loại' in cot.lower() or 'type' in cot.lower():
                    loai_bo_cau_hoi = str(exam_config.iloc[0][cot]).strip()
                    break
    total_score, result_string = tinh_diem_va_ket_qua(exam_questions)
    
    # Tính số câu hỏi unique
    num_questions = len(exam_questions.drop_duplicates(subset=['STT câu hỏi']))

    # Cột H: "Số câu đúng" - format: số_đúng/tổng_số
    so_cau_dung = f"{int(total_score)}/{num_questions}"
    
    # Cột I: "Điểm quy đổi" - tính từ tỉ lệ * max_score
    diem_quy_doi = round((total_score / num_questions) * max_score, 2) if num_questions > 0 else 0
    

    st.markdown(f"### Kết quả của bạn")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tổng số câu đúng", f"{total_score:.0f}/{num_questions}")
    with col2:
        st.metric("Điểm quy đổi", f"{diem_quy_doi:.1f}/{max_score}")
    
    timestamp = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    ngay_thuc_hien = st.session_state.ngay_kiem_tra.strftime("%Y-%m-%d")
    
    sheeto = st.secrets["sheet_name"]["output_11"]
    current_data = load_sheet_data(sheeto, 0)
    # Lấy STT tiếp theo liên tục
    stt_moi = get_next_stt(sheeto)
    
    result_row = [
        str(stt_moi),
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        ngay_thuc_hien,
        st.session_state.khoa_THI,
        st.session_state.username,
        loai_bo_cau_hoi,
        ma_de,
        result_string,
        so_cau_dung,
        f"{diem_quy_doi:.2f}"
    ]
    
    try:
        save_result_to_sheet(result_row)
        st.success("💾 Kết quả đã được lưu vào hệ thống!")
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu kết quả: {str(e)}")
    
    if st.button("🔄 Làm bài thi mới", use_container_width=True):
        keys_to_delete = [
            "exam_started",
            "start_time",
            "answers",
            "submitted",
            "ma_de",
            "ma_de_valid",
            "ma_de_input",
            "khoa_THI",
            "khoa_select",
            "ngay_kiem_tra",
            "shuffled_options",
        ]
        # Xóa các key chính xác
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        
        # Xóa tất cả key bắt đầu với q_ hoặc question_
        for key in list(st.session_state.keys()):
            if key.startswith("q_") or key.startswith("question_"):
                try:
                    del st.session_state[key]
                except KeyError:
                    pass
        
        # Clear cache
        st.cache_data.clear()
        
        import time
        time.sleep(0.5)
        st.rerun()

# Auto-refresh chỉ khi đang thi
if st.session_state.exam_started and not st.session_state.submitted:
    time.sleep(1)
    st.rerun()