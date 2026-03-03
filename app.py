import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Milk Control PRO", layout="wide")

EMP_FILE = 'employees.csv'
LOG_FILE = 'log.csv'
ADMIN_PASSWORD = "12345"  # Твой пароль

# Функция загрузки базы сотрудников
def load_data():
    if os.path.exists(EMP_FILE):
        df = pd.read_csv(EMP_FILE)
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=["Код", "Сотрудник", "Должность", "Дней", "Литр"])

df_emp = load_data()

# Меню слева
st.sidebar.title("Управление")
page = st.sidebar.radio("Перейти к:", ["📱 Раздача", "📊 Статистика", "⚙️ Настройка сотрудников"])

# --- 1. СТРАНИЦА РАЗДАЧИ ---
if page == "📱 Раздача":
    st.title("🥛 Регистрация выдачи")
    code = st.number_input("Введите ваш личный код", step=1, value=0)
    
    if code > 0:
        user = df_emp[df_emp['Код'] == code]
        if not user.empty:
            name = user.iloc[0]['Сотрудник']
            
            norma = 0.0
            days = 0
            
            for col in df_emp.columns:
                if col.lower() == 'литр':
                    norma = str(user.iloc[0][col]).replace(',', '.')
                if col.lower() == 'дней':
                    days = user.iloc[0][col]

            st.success(f"Сотрудник: {name}")
            
            col_ui1, col_ui2 = st.columns(2)
            with col_ui1:
                st.info(f"Дней по плану: {days}")
            with col_ui2:
                try:
                    val = float(norma)
                except:
                    val = 0.0
                liters = st.number_input("Литров к получению", value=val)
            
            if st.button("✅ Подтвердить получение"):
                new_entry = pd.DataFrame([[datetime.now().strftime('%d.%m.%Y %H:%M'), code, name, liters]], 
                                         columns=["Дата", "Код", "Имя", "Литры"])
                new_entry.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                st.balloons()
                st.success(f"Записано в базу!")
        else:
            st.error("Код не найден")

# --- ПРОВЕРКА ПАРОЛЯ ---
else:
    st.sidebar.markdown("---")
    pwd_input = st.sidebar.text_input("Введите пароль админа", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        # --- 2. СТРАНИЦА СТАТИСТИКИ ---
        if page == "📊 Статистика":
            st.title("📈 История выдачи")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("Всего выдано (л)", round(df_log['Литры'].sum(), 2))
                with col2:
                    # Кнопка очистки
                    st.write("---")
                    if st.button("🚨 Очистить историю"):
                        os.remove(LOG_FILE)
                        st.warning("История выдачи полностью удалена!")
                        st.rerun()

                st.dataframe(df_log, use_container_width=True)
                st.download_button("📥 Скачать отчет (Excel/CSV)", df_log.to_csv(index=False), "milk_report.csv")
            else:
                st.info("Записей пока нет.")

        # --- 3. АДМИНКА ---
        elif page == "⚙️ Настройка сотрудников":
            st.title("⚙️ Управление персоналом")
            tab1, tab2 = st.tabs(["📋 Список сотрудников", "➕ Добавить"])
            
            with tab1:
                edited_df = st.data_editor(df_emp, num_rows="dynamic")
                if st.button("💾 Сохранить изменения"):
                    edited_df.to_csv(EMP_FILE, index=False)
                    st.success("Данные успешно обновлены!")

            with tab2:
                with st.form("new_user"):
                    c1, c2 = st.columns(2)
                    n_code = c1.number_input("Код", step=1)
                    n_name = c2.text_input("ФИО")
                    n_pos = st.text_input("Должность")
                    c3, c4 = st.columns(2)
                    n_days = c3.number_input("Дней", value=19)
                    n_litr = c4.number_input("Норма литров", value=9.5)
                    
                    if st.form_submit_button("Добавить"):
                        new_row = pd.DataFrame([[n_code, n_name, n_pos, n_days, n_litr]], 
                                               columns=["Код", "Сотрудник", "Должность", "Дней", "Литр"])
                        new_row.to_csv(EMP_FILE, mode='a', index=False, header=not os.path.exists(EMP_FILE))
                        st.success("Добавлено!")
                        st.rerun()
    
    elif pwd_input != "":
        st.error("Неверный пароль")
