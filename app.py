import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- CẤU HÌNH AI ---
genai.configure(api_key="AIzaSyBvuuNnTfBHZbkfiNF5eC56ZQ1VtTpjRlM")

def generate_analysis(prompt_text):
    try:
        with st.spinner("🔍 AI đang phân tích dữ liệu..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            default_instruction = (
                "Hãy phân tích dữ liệu điểm thi này. Đưa ra nhận xét về sự chênh lệch giữa các đơn vị, "
                "xác định các đơn vị có kết quả tốt nhất và các đơn vị cần cải thiện. "
                "Đề xuất hướng khắc phục cụ thể.\n\n"
            )
            response = model.generate_content(default_instruction + str(prompt_text))
            return response.text
    except Exception as e:
        return f"❌ Lỗi AI: {e}"

# --- GIAO DIỆN & SETUP ---
st.set_page_config(page_title="Phân tích điểm thi - Tuyên Quang", layout="wide")

st.markdown("## SỞ GIÁO DỤC VÀ ĐÀO TẠO TUYÊN QUANG")
st.title("📘 PHÂN TÍCH KẾT QUẢ KHÁO SÁT GIỮA NĂM HỌC 2025 - 2026")

# --- QUẢN LÝ FILE (ADMIN) ---
admin_mode = st.sidebar.checkbox("Chế độ quản trị (Tải dữ liệu)")
if admin_mode:
    password = st.sidebar.text_input("Nhập mật khẩu", type="password")
    if password == "123":
        uploaded_file = st.file_uploader("📤 Tải file dữ liệu", type=["xlsx", "csv"])
        if uploaded_file:
            # Lưu file tương ứng (Cần logic nhận diện file THPT/THCS/TH nếu muốn tự động hoàn toàn)
            with open("du_lieu_mau.xlsx", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Đã cập nhật dữ liệu!")

# --- HÀM VẼ BIỂU ĐỒ PLOTLY CHUNG ---
def draw_plotly_chart(df_plot, title, color_main, y_label="Điểm trung bình"):
    fig = px.bar(
        df_plot, 
        x='Nhãn', 
        y='Điểm',
        color='Loại',
        color_discrete_map={'Trung bình': 'orange', 'Trường': color_main},
        text_auto='.2f',
        title=title,
        labels={'Nhãn': 'Đơn vị', 'Điểm': y_label}
    )
    fig.update_layout(
        xaxis_tickangle=-90,
        xaxis={'categoryorder':'total descending'},
        hovermode="x unified",
        height=600
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# --- LOAD DỮ LIỆU THPT ---
try:
    try:
        df = pd.read_csv("du_lieu_mau.xlsx - Sheet1.csv")
    except:
        df = pd.read_excel("du_lieu_mau.xlsx")
    df.columns = df.columns.str.strip()
    df['Điểm thi'] = pd.to_numeric(df['Điểm thi'], errors='coerce')
except Exception as e:
    st.error("❌ Không tìm thấy dữ liệu THPT.")
    st.stop()

# --- BỘ LỌC ---
st.sidebar.header("🔎 Bộ lọc")
school_options = ["Toàn tỉnh"] + sorted(df['Đơn vị'].dropna().unique().tolist())
selected_school = st.sidebar.selectbox("Chọn phạm vi phân tích:", school_options)
df_filtered = df if selected_school == "Toàn tỉnh" else df[df['Đơn vị'] == selected_school]

# =========================================================================
# PHẦN 1: CẤP THPT
# =========================================================================
st.subheader("🏫 Phần 1: Biểu đồ điểm trung bình cấp THPT")
avg_by_school = df_filtered.groupby("Đơn vị")['Điểm thi'].mean()
avg_all = df_filtered['Điểm thi'].mean()

plot_df_thpt = pd.DataFrame({
    'Nhãn': avg_by_school.index,
    'Điểm': avg_by_school.values,
    'Loại': 'Trường'
})
plot_df_thpt = pd.concat([plot_df_thpt, pd.DataFrame({'Nhãn': ['Trung bình'], 'Điểm': [avg_all], 'Loại': ['Trung bình']})])

draw_plotly_chart(plot_df_thpt, f"So sánh điểm trung bình THPT ({selected_school})", "skyblue")

if st.checkbox("📌 Nhận xét AI cho Phần 1", key="ai1"):
    st.markdown(generate_analysis(plot_df_thpt.to_dict()))

# =========================================================================
# PHẦN 3: CẤP THCS
# =========================================================================
st.divider()
st.subheader("🏫 Phần 3: Biểu đồ điểm trung bình cấp THCS")
try:
    df_thcs = pd.read_excel("du_lieu_mau_thcs.xlsx")
    df_thcs.columns = df_thcs.columns.str.strip()
    df_thcs['Điểm thi'] = pd.to_numeric(df_thcs['Điểm thi'], errors='coerce')
    
    avg_by_thcs = df_thcs.groupby("Đơn vị")['Điểm thi'].mean()
    avg_all_thcs = df_thcs['Điểm thi'].mean()

    plot_df_thcs = pd.DataFrame({'Nhãn': avg_by_thcs.index, 'Điểm': avg_by_thcs.values, 'Loại': 'Trường'})
    plot_df_thcs = pd.concat([plot_df_thcs, pd.DataFrame({'Nhãn': ['Trung bình'], 'Điểm': [avg_all_thcs], 'Loại': ['Trung bình']})])

    draw_plotly_chart(plot_df_thcs, "Kết quả khảo sát cấp THCS Toàn tỉnh", "#2ECC71")

    if st.checkbox("📌 Nhận xét AI cho Phần 3", key="ai3"):
        st.markdown(generate_analysis(plot_df_thcs.to_dict()))
except:
    st.warning("⚠️ Chưa có dữ liệu cấp THCS.")

# =========================================================================
# PHẦN 4: CẤP TIỂU HỌC
# =========================================================================
st.divider()
st.subheader("🏫 Phần 4: Biểu đồ điểm trung bình cấp Tiểu học")
try:
    df_th = pd.read_excel("du_lieu_mau_th.xlsx")
    df_th.columns = df_th.columns.str.strip()
    df_th['Điểm thi'] = pd.to_numeric(df_th['Điểm thi'], errors='coerce')
    
    avg_by_th = df_th.groupby("Đơn vị")['Điểm thi'].mean()
    avg_all_th = df_th['Điểm thi'].mean()

    plot_df_th = pd.DataFrame({'Nhãn': avg_by_th.index, 'Điểm': avg_by_th.values, 'Loại': 'Trường'})
    plot_df_th = pd.concat([plot_df_th, pd.DataFrame({'Nhãn': ['Trung bình'], 'Điểm': [avg_all_th], 'Loại': ['Trung bình']})])

    draw_plotly_chart(plot_df_th, "Kết quả khảo sát cấp Tiểu học Toàn tỉnh", "violet")

    if st.checkbox("📌 Nhận xét AI cho Phần 4", key="ai4"):
        st.markdown(generate_analysis(plot_df_th.to_dict()))
except:
    st.warning("⚠️ Chưa có dữ liệu cấp Tiểu học.")

# =========================================================================
# PHẦN 2: CHI TIẾT THEO LỚP (PLOTLY)
# =========================================================================
st.divider()
st.subheader("📊 Phần 2: Phân tích chi tiết theo Lớp cấp THPT")

list_schools = sorted(df['Đơn vị'].dropna().unique().tolist())
selected_schools_p2 = st.multiselect("Chọn các trường muốn xem chi tiết lớp:", options=list_schools)

if selected_schools_p2:
    df_p2 = df[df['Đơn vị'].isin(selected_schools_p2)]
    if 'Lớp' in df_p2.columns:
        avg_by_class = df_p2.groupby(['Đơn vị', 'Lớp'])['Điểm thi'].mean().reset_index()
        
        for school in selected_schools_p2:
            school_data = avg_by_class[avg_by_class['Đơn vị'] == school]
            if not school_data.empty:
                fig_class = px.bar(
                    school_data, x='Lớp', y='Điểm thi', 
                    text_auto='.2f', title=f"Chi tiết các lớp - {school}",
                    color_discrete_sequence=['mediumseagreen']
                )
                st.plotly_chart(fig_class, use_container_width=True)

        if st.checkbox("📌 Nhận xét AI về các lớp", key="ai2"):
            st.markdown(generate_analysis(avg_by_class.to_string(index=False)))
    else:
        st.error("❌ Thiếu cột 'Lớp' trong dữ liệu.")