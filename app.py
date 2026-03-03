import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

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

df_emp = load_data()

st.sidebar.title("Управление")
page = st.sidebar.radio("Перейти к:", ["📱 Раздача", "📊 Статистика", "⚙️ Настройка"])

# --- 1. СТРАНИЦА РАЗДАЧИ ---
if page == "📱 Раздача":
    st.title("🥛 Регистрация выдачи")
    
    code = st.number_input("Введите ваш код", step=1, value=None, placeholder="Начните вводить код...")
    
    if code is not None:
        user = df_emp[df_emp['Код'] == code]
        if not user.empty:
            name = user.iloc[0]['Сотрудник']
            st.success(f"Сотрудник: {name}")
            
            liters = st.number_input("Литров получено", min_value=0.0, max_value=20.0, value=None, step=0.5, placeholder="0.0")
            
            if st.button("✅ Подтвердить"):
                if liters is not None and liters > 0:
                    new_entry = pd.DataFrame([[datetime.now().strftime('%d.%m.%Y %H:%M'), code, name, liters]], 
                                             columns=["Дата", "Код", "Имя", "Литры"])
                    new_entry.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE))
                    st.balloons()
                    st.success(f"Данные сохранены для {name}")
                else:
                    st.error("Укажите количество литров!")
        else:
            st.error("Код не найден")

# --- СЕКЦИЯ АДМИНА ---
else:
    st.sidebar.markdown("---")
    pwd_input = st.sidebar.text_input("Пароль админа", type="password")
    
    if pwd_input == ADMIN_PASSWORD:
        # --- 2. СТРАНИЦА СТАТИСТИКИ ---
        if page == "📊 Статистика":
            st.title("📈 История выдачи")
            if os.path.exists(LOG_FILE):
                df_log = pd.read_csv(LOG_FILE)
                df_log['dt_obj'] = pd.to_datetime(df_log['Дата'], dayfirst=True)
                
                st.subheader("Фильтр периода")
                filter_type = st.selectbox("Выберите период:", ["Сегодня", "За неделю", "За месяц", "Весь период", "Выбрать даты"])
                
                today = datetime.now()
                start_date = datetime(2000, 1, 1)
                
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
                st.dataframe(filtered_df[["Дата", "Код", "Имя", "Литры"]], use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    # Кнопка скачивания CSV (открывается в Excel)
                    st.download_button("📥 Скачать Excel (CSV)", filtered_df.to_csv(index=False), "milk_report.csv")
                with col2:
                    if st.button("🚨 Очистить ВСЮ историю"):
                        os.remove(LOG_FILE)
                        st.rerun()
            else:
                st.info("История пуста")

        # --- 3. НАСТРОЙКА БАЗЫ ---
        elif page == "⚙️ Настройка":
            st.title("⚙️ Настройка персонала")
            edited_df = st.data_editor(df_emp, num_rows="dynamic")
            if st.button("💾 Сохранить изменения"):
                edited_df.to_csv(EMP_FILE, index=False)
                st.success("Список обновлен!")
    
    elif pwd_input != "":
        st.error("Неверный пароль")
