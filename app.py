import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Milk Control PRO", layout="wide")

EMP_FILE = 'employees.csv'
LOG_FILE = 'log.csv'
ADMIN_PASSWORD = "12345"  # Твой пароль

# Функция загрузки базы
def load_data():
    if os.path.exists(EMP_FILE):
        return pd.read_csv(EMP_FILE)
    return pd.DataFrame(columns=["Код", "Сотрудник", "Должность", "Литр"])

df_emp = load_data()

# Меню слева
st.sidebar.title("Управление")
page = st.sidebar.radio("Перейти к:", ["📱 Раздача", "📊 Статистика", "⚙️ Настройка сотрудников"])

# --- 1. СТРАНИЦА РАЗДАЧИ (БЕЗ ПАРОЛЯ) ---
if page == "📱 Раздача":
    st.title("🥛 Регистрация выдачи")
    code = st.number_input("Введите ваш Код", step=1, value=0)
    
    if code > 0:
        user = df_emp[df_emp['Код'] == code]
        if not user.empty:
            name = user.iloc[0]['Сотрудник']
            norma = user.iloc[0]['Литр']
            st.success(f"Сотрудник: {name}")
            
            # Чиним отображение литров (заменяем запятую на точку если нужно)
            try:
                val = float(str(norma).replace(',', '.'))
            except:
                val = 0.0
                
            liters = st.number_input("Литров к получению", value=val)
            
            if st.button("✅ Подтвердить получение"):
                new_entry = pd.DataFrame([[datetime.now().strftime('%d.%m %H:%M'), code, name, liters]], 
                                         columns=["Дата", "Код", "Имя", "Литры"])
                new_entry.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                st.balloons()
                st.success(f"Записано: {name} получил {liters} л.")
        else:
            st.error("Код не найден в базе данных")

# --- ПРОВЕРКА ПАРОЛЯ ДЛЯ ОСТАЛЬНЫХ СТРАНИЦ ---
else:
    st.sidebar.markdown("---")
    pwd_input = st.sidebar.text_input("Введите пароль админа", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        # --- 2. СТРАНИЦА СТАТИСТИКИ ---
        if page == "📊 Статистика":
            st.title("📈 История выдачи молока")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                st.metric("Всего выдано за сегодня", f"{round(df_log['Литры'].sum(), 2)} л.")
                st.dataframe(df_log, use_container_width=True)
                st.download_button("Скачать отчет CSV", df_log.to_csv(index=False), "report.csv")
            else:
                st.info("Данных о выдаче пока нет.")

        # --- 3. АДМИНКА (УПРАВЛЕНИЕ) ---
        elif page == "⚙️ Настройка сотрудников":
            st.title("⚙️ Управление персоналом")
            tab1, tab2 = st.tabs(["📋 Список", "➕ Добавить нового"])
            
            with tab1:
                edited_df = st.data_editor(df_emp, num_rows="dynamic")
                if st.button("💾 Сохранить изменения"):
                    edited_df.to_csv(EMP_FILE, index=False)
                    st.success("Список обновлен!")

            with tab2:
                with st.form("new_user"):
                    new_code = st.number_input("Код", step=1)
                    new_name = st.text_input("ФИО")
                    new_pos = st.text_input("Должность")
                    new_litr = st.number_input("Норма (литров)", value=9.5)
                    if st.form_submit_button("Добавить"):
                        new_row = pd.DataFrame([[new_code, new_name, new_pos, new_litr]], 
                                               columns=["Код", "Сотрудник", "Должность", "Литр"])
                        new_row.to_csv(EMP_FILE, mode='a', index=False, header=not os.path.exists(EMP_FILE))
                        st.success("Добавлено! Обновите страницу.")
    
    elif pwd_input == "":
        st.warning("Пожалуйста, введите пароль в боковом меню для доступа к этому разделу.")
    else:
        st.error("Неверный пароль!")