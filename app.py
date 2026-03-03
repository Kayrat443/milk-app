import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from fpdf import FPDF

# Настройка страницы
st.set_page_config(page_title="Milk Control PRO", layout="wide")

EMP_FILE = 'employees.csv'
LOG_FILE = 'log.csv'
ADMIN_PASSWORD = "12345"

def load_data():
    if os.path.exists(EMP_FILE):
        df = pd.read_csv(EMP_FILE)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["Код", "Сотрудник", "Должность", "Дней", "Литр"])

# Функция генерации PDF
def create_pdf(df, period_text):
    pdf = FPDF()
    pdf.add_page()
    # Добавляем шрифт, поддерживающий кириллицу (стандартные не умеют)
    pdf.add_font('DejaVu', '', 'https://github.com/reingart/pyfpdf/raw/master/font/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    
    pdf.cell(200, 10, txt=f"Отчет по выдаче молока: {period_text}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('DejaVu', '', 10)
    # Заголовки таблицы
    pdf.cell(40, 10, "Дата", border=1)
    pdf.cell(80, 10, "Сотрудник", border=1)
    pdf.cell(30, 10, "Литры", border=1)
    pdf.ln()
    
    for i, row in df.iterrows():
        pdf.cell(40, 10, str(row['Дата']), border=1)
        pdf.cell(80, 10, str(row['Имя']), border=1)
        pdf.cell(30, 10, str(row['Литры']), border=1)
        pdf.ln()
        
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"ИТОГО: {df['Литры'].sum()} л.", ln=True)
    return pdf.output()

df_emp = load_data()

st.sidebar.title("Управление")
page = st.sidebar.radio("Перейти к:", ["📱 Раздача", "📊 Статистика", "⚙️ Настройка"])

if page == "📱 Раздача":
    st.title("🥛 Регистрация выдачи")
    code = st.number_input("Введите ваш код", step=1, value=0)
    if code > 0:
        user = df_emp[df_emp['Код'] == code]
        if not user.empty:
            name = user.iloc[0]['Сотрудник']
            st.success(f"Сотрудник: {name}")
            liters = st.number_input("Литров получено", value=0.0)
            if st.button("✅ Подтвердить"):
                new_entry = pd.DataFrame([[datetime.now().strftime('%d.%m.%Y %H:%M'), code, name, liters, datetime.now()]], 
                                         columns=["Дата", "Код", "Имя", "Литры", "dt_obj"])
                new_entry.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                st.balloons()
        else:
            st.error("Код не найден")

else:
    st.sidebar.markdown("---")
    pwd_input = st.sidebar.text_input("Пароль админа", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        if page == "📊 Статистика":
            st.title("📈 Детальная статистика")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                # Превращаем колонку с датой в настоящий формат даты для фильтров
                df_log['dt_obj'] = pd.to_datetime(df_log['Дата'], dayfirst=True)
                
                # --- БЛОК ФИЛЬТРОВ ---
                st.subheader("Фильтры периода")
                filter_type = st.selectbox("Выберите период:", ["Сегодня", "За неделю", "За месяц", "Кастомный диапазон"])
                
                today = datetime.now()
                start_date = today
                
                if filter_type == "Сегодня":
                    start_date = today.replace(hour=0, minute=0, second=0)
                elif filter_type == "За неделю":
                    start_date = today - timedelta(days=7)
                elif filter_type == "За месяц":
                    start_date = today - timedelta(days=30)
                elif filter_type == "Кастомный диапазон":
                    dates = st.date_input("Выберите даты", [today - timedelta(days=7), today])
                    if len(dates) == 2:
                        start_date = datetime.combine(dates[0], datetime.min.time())
                        today = datetime.combine(dates[1], datetime.max.time())

                # Фильтруем данные
                mask = (df_log['dt_obj'] >= start_date) & (df_log['dt_obj'] <= today)
                filtered_df = df_log.loc[mask]

                # --- ОТОБРАЖЕНИЕ ---
                st.metric("Выдано за период", f"{round(filtered_df['Литры'].sum(), 2)} л.")
                st.dataframe(filtered_df[["Дата", "Имя", "Литры"]], use_container_width=True)

                # --- КНОПКИ СКАЧИВАНИЯ ---
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📥 Скачать Excel (CSV)", filtered_df.to_csv(index=False), "report.csv")
                with col2:
                    if st.button("📄 Сгенерировать PDF"):
                        pdf_data = create_pdf(filtered_df, filter_type)
                        st.download_button("⬇️ Сохранить PDF", pdf_data, "report.pdf", "application/pdf")
                with col3:
                    if st.button("🚨 Очистить ВСЮ историю"):
                        os.remove(LOG_FILE)
                        st.rerun()
            else:
                st.info("История пуста")

        elif page == "⚙️ Настройка":
            st.title("⚙️ Настройка базы")
            edited_df = st.data_editor(df_emp, num_rows="dynamic")
            if st.button("💾 Сохранить список"):
                edited_df.to_csv(EMP_FILE, index=False)
                st.success("Обновлено!")
