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

# Функция генерации PDF с колонкой "Код"
def create_pdf(df, period_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'https://github.com/reingart/pyfpdf/raw/master/font/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    
    pdf.cell(200, 10, txt=f"Отчет по выдаче молока: {period_text}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font('DejaVu', '', 9)
    # Заголовки таблицы (расширили под Код)
    pdf.cell(35, 10, "Дата", border=1)
    pdf.cell(20, 10, "Код", border=1)
    pdf.cell(85, 10, "Сотрудник", border=1)
    pdf.cell(25, 10, "Литры", border=1)
    pdf.ln()
    
    for i, row in df.iterrows():
        pdf.cell(35, 10, str(row['Дата']), border=1)
        pdf.cell(20, 10, str(row['Код']), border=1)
        pdf.cell(85, 10, str(row['Имя']), border=1)
        pdf.cell(25, 10, str(row['Литры']), border=1)
        pdf.ln()
        
    pdf.ln(10)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(200, 10, txt=f"ИТОГО ВЫДАНО: {df['Литры'].sum()} л.", ln=True)
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
            
            # ОГРАНИЧЕНИЕ: max_value=20.0 защитит от случайного ввода "40"
            liters = st.number_input("Литров получено", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
            
            if liters > 20:
                st.error("Ошибка! Нельзя выдать более 20 литров за раз.")
            
            if st.button("✅ Подтвердить"):
                if liters > 0:
                    new_entry = pd.DataFrame([[datetime.now().strftime('%d.%m.%Y %H:%M'), code, name, liters]], 
                                             columns=["Дата", "Код", "Имя", "Литры"])
                    new_entry.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                    st.balloons()
                    st.success(f"Данные сохранены для {name}")
                else:
                    st.warning("Введите количество литров")
        else:
            st.error("Код не найден")

else:
    st.sidebar.markdown("---")
    pwd_input = st.sidebar.text_input("Пароль админа", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        if page == "📊 Статистика":
            st.title("📈 История выдачи")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                # Конвертируем дату для фильтрации
                df_log['dt_obj'] = pd.to_datetime(df_log['Дата'], dayfirst=True)
                
                st.subheader("Фильтр периода")
                filter_type = st.selectbox("Период:", ["Сегодня", "За неделю", "За месяц", "Весь период", "Выбрать даты"])
                
                today = datetime.now()
                start_date = datetime(2000, 1, 1) # По умолчанию для "Весь период"
                
                if filter_type == "Сегодня":
                    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
                elif filter_type == "За неделю":
                    start_date = today - timedelta(days=7)
                elif filter_type == "За месяц":
                    start_date = today - timedelta(days=30)
                elif filter_type == "Выбрать даты":
                    range_dates = st.date_input("Диапазон", [today - timedelta(days=7), today])
                    if len(range_dates) == 2:
                        start_date = datetime.combine(range_dates[0], datetime.min.time())
                        today = datetime.combine(range_dates[1], datetime.max.time())

                mask = (df_log['dt_obj'] >= start_date) & (df_log['dt_obj'] <= today)
                filtered_df = df_log.loc[mask].sort_values(by='dt_obj', ascending=False)

                st.metric("ИТОГО ЗА ПЕРИОД", f"{round(filtered_df['Литры'].sum(), 2)} л.")
                # Показываем таблицу с Кодом
                st.dataframe(filtered_df[["Дата", "Код", "Имя", "Литры"]], use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📥 Excel (CSV)", filtered_df.to_csv(index=False), "milk_report.csv")
                with col2:
                    if st.button("📄 Создать PDF"):
                        pdf_data = create_pdf(filtered_df, filter_type)
                        st.download_button("⬇️ Скачать PDF", pdf_data, "milk_report.pdf", "application/pdf")
                with col3:
                    if st.button("🚨 Очистить историю"):
                        os.remove(LOG_FILE)
                        st.rerun()
            else:
                st.info("Записей пока нет")

        elif page == "⚙️ Настройка":
            st.title("⚙️ Настройка персонала")
            edited_df = st.data_editor(df_emp, num_rows="dynamic")
            if st.button("💾 Сохранить изменения"):
                edited_df.to_csv(EMP_FILE, index=False)
                st.success("Список обновлен!")
