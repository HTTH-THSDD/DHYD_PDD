import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials

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
    except:
        pass

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

@st.cache_data(ttl=60)
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
                "Sheet 0": 0, "Sheet 1": 1, "Sheet 2": 2, "Sheet 3": 3,
            }
            if worksheet_name in worksheet_map:
                idx = worksheet_map[worksheet_name]
                sheet = spreadsheet.get_worksheet(idx)
                data = sheet.get_all_values()
            else:
                return pd.DataFrame()
        
        if len(data) > 0:
            header = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=header)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi: {str(e)}")
        return pd.DataFrame()

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
                <p style="color:green">THỐNG KÊ KẾT QUẢ KIỂM TRA</p>
                </div>
            </div>
            <div class="header-underline"></div>
        """, unsafe_allow_html=True)
    except:
        st.title("THỐNG KÊ KẾT QUẢ KIỂM TRA")
    
    if 'username' in st.session_state:
        html_code = f'<p class="demuc"><i>Nhân viên thực hiện: {st.session_state.username}</i></p>'
        st.html(html_code)

def parse_result_string(result_str):
    """Parse chuỗi kết quả: 1|Đáp án A#2|Đúng-Sai-Đúng"""
    results = []   
    # Kiểm tra chuỗi có rỗng không
    if not result_str or result_str == '' or result_str is None:
        return results
    # Xóa khoảng trắng dư thừa
    result_str = str(result_str).strip()
    if result_str == '':
        return results
    questions = result_str.split('#')
    for q in questions:
        # Bỏ qua các phần tử rỗng
        if not q or q.strip() == '':
            continue
        q = q.strip()
        # Kiểm tra xem có ký tự '|' không
        if '|' not in q:
            st.warning(f"⚠️ Format kết quả không hợp lệ: {q}")
            continue
        parts = q.split('|', 1)
        # Kiểm tra xem có đủ 2 phần không
        if len(parts) < 2:
            st.warning(f"⚠️ Format kết quả không hợp lệ: {q}")
            continue 
        stt = parts[0].strip()
        answer = parts[1].strip() if len(parts) > 1 else ""
        # Bỏ qua nếu STT rỗng
        if not stt:
            continue
        results.append({'stt': stt, 'answer': answer})
    return results


def get_correct_answer(ma_de, stt):
    """Lấy đáp án đúng từ input_8"""
    try:
        sheeti8 = st.secrets["sheet_name"]["input_8"]
        df_questions = load_sheet_by_name(sheeti8, "Sheet 3")
        
        if len(df_questions) == 0:
            st.warning(f"⚠️ Không tìm thấy dữ liệu trong Sheet 3")
            return None
        
        # Kiểm tra xem các cột cần thiết có tồn tại không
        required_columns = ["Tên bộ câu hỏi", "STT câu hỏi", "Câu hỏi", "Loại câu hỏi", "Câu trả lời", "Kết quả"]
        missing_columns = [col for col in required_columns if col not in df_questions.columns]
        
        if missing_columns:
            st.error(f"❌ Sheet 3 thiếu các cột: {', '.join(missing_columns)}")
            st.write(f"Các cột hiện có: {list(df_questions.columns)}")
            return None
        
        # Tìm câu hỏi theo mã đề và STT
        question_data = df_questions[
            (df_questions["Tên bộ câu hỏi"].astype(str).str.strip() == str(ma_de).strip()) & 
            (df_questions["STT câu hỏi"].astype(str).str.strip() == str(stt).strip())
        ]
        
        if len(question_data) == 0:
            st.warning(f"⚠️ Không tìm thấy câu hỏi: mã đề={ma_de}, STT={stt}")
            return None
        
        row = question_data.iloc[0]
        
        # Trích xuất dữ liệu một cách an toàn
        return {
            'question': str(row["Câu hỏi"]) if "Câu hỏi" in row else "",
            'type': str(row["Loại câu hỏi"]) if "Loại câu hỏi" in row else "",
            'answers': str(row["Câu trả lời"]) if "Câu trả lời" in row else "",
            'results': str(row["Kết quả"]) if "Kết quả" in row else ""
        }
        
    except Exception as e:
        st.error(f"❌ Lỗi khi lấy đáp án cho câu {stt}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def check_answer_correct(user_answer, ma_de, stt):
    """Kiểm tra đáp án đúng hay sai"""
    try:
        correct_data = get_correct_answer(ma_de, stt)
        
        if not correct_data:
            return False, ""
        
        q_type = correct_data.get('type', '')
        answers = correct_data.get('answers', '')
        results = correct_data.get('results', '')
        
        if not answers or not results:
            return False, ""
        
        if q_type == "Trắc nghiệm":
            answer_list = [ans.strip() for ans in str(answers).split('\n') if ans.strip()]
            result_list = [res.strip() for res in str(results).split('\n') if res.strip()]
            
            if len(answer_list) == 0 or len(result_list) == 0:
                return False, ""
            
            correct_answer = None
            for ans, res in zip(answer_list, result_list):
                if res == "Đúng":
                    correct_answer = ans
                    break
            
            return user_answer.strip() == correct_answer if correct_answer else False, correct_data.get('question', '')
        
        elif q_type == "Đúng/Sai":
            user_choices = [u.strip() for u in str(user_answer).split('-') if u.strip()]
            correct_choices = [res.strip() for res in str(results).split('\n') if res.strip()]
            
            if len(user_choices) != len(correct_choices):
                return False, ""
            
            all_correct = True
            for user_choice, correct_choice in zip(user_choices, correct_choices):
                if user_choice != correct_choice:
                    all_correct = False
                    break
            
            return all_correct, correct_data.get('question', '')
        
        return False, ""
    
    except Exception as e:
        st.warning(f"⚠️ Lỗi khi kiểm tra câu {stt}: {str(e)}")
        return False, ""

def apply_filters(df, start_date, end_date, selected_khoa, selected_nhanvien):
    """Áp dụng bộ lọc cho dataframe"""
    filtered = df.copy()
    
    # Convert Ngày thực hiện to datetime
    filtered['Ngày thực hiện'] = pd.to_datetime(filtered['Ngày thực hiện'])
    
    # Filter by date range
    filtered = filtered[
        (filtered['Ngày thực hiện'].dt.date >= start_date) & 
        (filtered['Ngày thực hiện'].dt.date <= end_date)
    ]
    
    # Filter by Khoa
    if selected_khoa != "Tất cả":
        filtered = filtered[filtered['Khoa'] == selected_khoa]
    
    # Filter by Nhân viên
    if selected_nhanvien != "Tất cả":
        filtered = filtered[filtered['Nhân viên'] == selected_nhanvien]
    
    return filtered

# CSS
st.markdown("""
<style>
    .correct-answer {
        color: #28a745;
        font-weight: bold;
    }
    .incorrect-answer {
        color: #dc3545;
        font-weight: bold;
    }
    .highlight-correct {
        background-color: #d4edda;
        padding: 5px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Main
hien_thi_header()

# Load data
sheeto = st.secrets["sheet_name"]["output_11"]
df_output = load_data(sheeto)

if len(df_output) == 0:
    st.warning("⚠️ Chưa có dữ liệu kết quả thi")
    st.stop()

# Bộ lọc
st.markdown("## 🔍 Bộ lọc")

col1, col2, col3, col4 = st.columns(4)

with col1:
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    start_date = st.date_input(
        "Từ ngày",
        value=now_vn.date(),
        format="DD/MM/YYYY",
        key="start_date"
    )

with col2:
    end_date = st.date_input(
        "Đến ngày",
        value=now_vn.date(),
        format="DD/MM/YYYY",
        key="end_date"
    )

with col3:
    all_khoa = ["Tất cả"] + df_output['Khoa'].unique().tolist()
    selected_khoa = st.selectbox("Khoa", all_khoa)

with col4:
    all_nhanvien = ["Tất cả"] + df_output['Nhân viên'].unique().tolist()
    selected_nhanvien = st.selectbox("Nhân viên", all_nhanvien)

# Apply filters
df_filtered = apply_filters(df_output, start_date, end_date, selected_khoa, selected_nhanvien)

if len(df_filtered) == 0:
    st.info("📭 Không có dữ liệu phù hợp với bộ lọc")
    st.stop()

st.markdown("---")

# Bảng thống kê tổng hợp
st.markdown("## 📊 Bảng thống kê tổng hợp")

summary_data = []
for idx, row in df_filtered.iterrows():
    summary_data.append({
        'Khoa': row['Khoa'],
        'Nhân viên': row['Nhân viên'],
        'Bộ câu hỏi': row['Mã đề'],
        'Số câu đúng': row['Điểm trên 10'],
        'Điểm': row['Điểm quy đổi']
    })

df_summary = pd.DataFrame(summary_data)
st.dataframe(df_summary, use_container_width=True, hide_index=True)


st.markdown("---")

# Bảng thống kê chi tiết
st.markdown("## 📋 Bảng thống kê chi tiết")

detail_data = []

for idx, row in df_filtered.iterrows():
    khoa = row['Khoa']
    nhanvien = row['Nhân viên']
    ma_de = row['Mã đề']
    result_str = row['Kết quả']
    
    # Parse result string
    parsed = parse_result_string(result_str)
    
    for item in parsed:
        stt = item['stt']
        user_answer = item['answer']
        
        # Check if answer is correct
        is_correct, question_text = check_answer_correct(user_answer, ma_de, stt)
        
        detail_data.append({
            'Khoa': khoa,
            'Nhân viên': nhanvien,
            'Bộ câu hỏi': ma_de,
            'Câu hỏi': f"Câu {stt}",
            'Câu trả lời': user_answer,
            'Kết quả': '✗ Sai' if not is_correct else '✓ Đúng',
            '_is_correct': is_correct
        })

if len(detail_data) > 0:
    df_detail = pd.DataFrame(detail_data)
    
    # Create styled dataframe
    def highlight_incorrect(row):
        if not row['_is_correct']:
            return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * (len(row) - 1) + ['']
        else:
            return [''] * len(row)
    
    # Display table
    df_detail_display = df_detail[['Khoa', 'Nhân viên', 'Bộ câu hỏi', 'Câu hỏi', 'Câu trả lời', 'Kết quả']]
    
    # Apply styling manually for each row
    st.write("**Chú thích:** Dòng màu đỏ là câu trả lời sai")
    
    # Hiển thị bảng với HTML để tô màu chính xác
    try:
        html_table = "<table style='width:100%; border-collapse: collapse;'>"
        html_table += "<thead><tr style='background-color: #f0f0f0;'>"
        for col in df_detail_display.columns:
            html_table += f"<th style='padding: 10px; border: 1px solid #ddd; text-align: left;'>{col}</th>"
        html_table += "</tr></thead><tbody>"
        
        for i, row_data in df_detail_display.iterrows():
            if i < len(df_detail):
                is_correct = df_detail.loc[i, '_is_correct']
                row_style = "background-color: #f8d7da; color: #721c24;" if not is_correct else ""
                
                html_table += f"<tr style='{row_style}'>"
                for col in df_detail_display.columns:
                    cell_value = str(row_data[col]) if row_data[col] is not None else ""
                    html_table += f"<td style='padding: 8px; border: 1px solid #ddd;'>{cell_value}</td>"
                html_table += "</tr>"
        
        html_table += "</tbody></table>"
        
        st.markdown(html_table, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Lỗi khi hiển thị bảng: {str(e)}")
        st.dataframe(df_detail_display, use_container_width=True, hide_index=True)
        
else:
    st.info("Không có dữ liệu chi tiết để hiển thị")

st.markdown("---")

# Tra cứu bộ câu hỏi
st.markdown("## 🔎 Tra cứu bộ câu hỏi")

sheeti8 = st.secrets["sheet_name"]["input_8"]
df_config = load_sheet_by_name(sheeti8, "Sheet 2")

if len(df_config) > 0 and 'Tên bộ câu hỏi' in df_config.columns:
    all_made = df_config['Tên bộ câu hỏi'].unique().tolist()
    
    if len(all_made) > 0:
        selected_made = st.selectbox("Chọn bộ câu hỏi", all_made, key="lookup_made")
        
        if selected_made:
            # Load questions
            df_questions = load_sheet_by_name(sheeti8, "Sheet 3")
            
            if len(df_questions) > 0 and 'Tên bộ câu hỏi' in df_questions.columns:
                # Filter by selected ma_de
                questions = df_questions[df_questions['Tên bộ câu hỏi'] == selected_made]
                
                if len(questions) == 0:
                    st.info("Không tìm thấy câu hỏi cho bộ đề này")
                else:
                    # Group by STT to avoid duplicates
                    if 'STT câu hỏi' in questions.columns:
                        unique_questions = questions.drop_duplicates(subset=['STT câu hỏi'])
                        
                        st.markdown(f"### Danh sách câu hỏi: {selected_made}")
                        
                        for idx, row in unique_questions.iterrows():
                            try:
                                stt = row['STT câu hỏi']
                                question = row['Câu hỏi']
                                q_type = row['Loại câu hỏi']
                                answers = row['Câu trả lời']
                                results = row['Kết quả']
                                
                                st.markdown(f"#### Câu {stt}: {question}")
                                st.write(f"**Loại:** {q_type}")
                                
                                # Parse answers
                                answer_list = [ans.strip() for ans in str(answers).split('\n') if ans.strip()]
                                result_list = [res.strip() for res in str(results).split('\n') if res.strip()]
                                
                                if q_type == "Trắc nghiệm":
                                    st.write("**Các đáp án:**")
                                    for ans, res in zip(answer_list, result_list):
                                        if res == "Đúng":
                                            st.markdown(f"<p class='highlight-correct'>✓ {ans} (Đáp án đúng)</p>", 
                                                      unsafe_allow_html=True)
                                        else:
                                            st.write(f"  {ans}")
                                
                                elif q_type == "Đúng/Sai":
                                    st.write("**Các câu:**")
                                    for i, (ans, res) in enumerate(zip(answer_list, result_list)):
                                        if res == "Đúng":
                                            st.markdown(f"<p class='highlight-correct'>{i+1}. {ans} - Đúng ✓</p>", 
                                                      unsafe_allow_html=True)
                                        else:
                                            st.write(f"{i+1}. {ans} - Sai")
                                
                                st.markdown("---")
                            except Exception as e:
                                st.error(f"Lỗi khi hiển thị câu hỏi: {str(e)}")
                                continue
                    else:
                        st.error("Không tìm thấy cột 'STT câu hỏi' trong dữ liệu")
            else:
                st.warning("Không tìm thấy dữ liệu câu hỏi trong Sheet 3 hoặc thiếu cột 'Tên bộ câu hỏi'")
    else:
        st.info("Chưa có bộ câu hỏi nào trong hệ thống")
else:
    st.warning("Không tìm thấy danh sách bộ câu hỏi trong Sheet 2 hoặc thiếu cột 'Tên bộ câu hỏi'")