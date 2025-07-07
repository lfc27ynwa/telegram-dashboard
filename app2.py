import streamlit as st
import pandas as pd
import re
import plotly.express as px
import textwrap

st.set_page_config(layout="wide")
st.title("Аналитика по TG-каналам с продуктовой тематикой")

# ======================
# Загрузка данных
# ======================
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfWtx-JbH9jxS-P6v_TZoAcxsmvccteo_BxtASUpoLxAL7AmFnXoZim5_3umjBh2or6-X20m39Zn9h/pub?output=tsv"
df = pd.read_csv(url, sep="\t")
df.columns = df.columns.str.strip()

# ======================
# Функции
# ======================
def get_companies(df):
    companies_set = set()
    for authors in df['Автор'].dropna():
        parts = [p.strip() for p in authors.split(',')]
        for p in parts:
            if not re.match(r'^[A-ZА-ЯЁ][a-zа-яё]+\s[A-ZА-ЯЁ][a-zа-яё]+$', p):
                if p != "Нет информации":
                    companies_set.add(p)
    return sorted(list(companies_set))

def filter_multi_category(df, column, selected_options):
    if not selected_options:
        return df
    mask = df[column].apply(lambda x: any(option in str(x) for option in selected_options))
    return df[mask]

# ======================
# Блок поиска
# ======================
st.header("Поиск")

search_options = pd.concat([df['Название канала'], df['Username'], df['Автор']]).dropna().unique()
search_selection = st.multiselect("Начните вводить название канала, его username или автора:", options=search_options)

if search_selection:
    df = df[
        df['Название канала'].isin(search_selection) |
        df['Username'].isin(search_selection) |
        df['Автор'].isin(search_selection)
    ]

# ======================
# Фильтр по компаниям
# ======================
st.header("Фильтр")

companies = get_companies(df)
col_comp1, col_comp2 = st.columns([4,1])
with col_comp1:
    selected_companies = st.multiselect("По компаниям: (в том числе личные блоги сотрудников компаний)", options=companies, default=[])
with col_comp2:
    all_companies_selected = set(selected_companies) == set(companies)
    select_all_companies = st.checkbox("выбрать все варианты", value=all_companies_selected, key='companies')

if select_all_companies and not all_companies_selected:
    selected_companies = companies
elif not select_all_companies and all_companies_selected and len(selected_companies) < len(companies):
    select_all_companies = False

if selected_companies:
    def company_filter(authors):
        parts = [p.strip() for p in str(authors).split(',')]
        return any(company in parts for company in selected_companies)
    df = df[df['Автор'].apply(company_filter)]

# ======================
# Фильтры по Типу, Тематике, Про что
# ======================

# Тип
types = df['Тип'].dropna().unique()
col_type1, col_type2 = st.columns([4,1])
with col_type1:
    selected_types = st.multiselect("По типу: (канал компании / личный блог / агрегатор данных)", options=types, default=[])
with col_type2:
    all_types_selected = set(selected_types) == set(types)
    select_all_types = st.checkbox("выбрать все варианты", value=all_types_selected, key='types')

if select_all_types and not all_types_selected:
    selected_types = types
elif not select_all_types and all_types_selected and len(selected_types) < len(types):
    select_all_types = False

# Тематика
allowed_themes = ["Вакансии","Дизайн","Карьера","Общее IT","Продакт-менеджмент","Разработка","Стартапы","AI","Софт-скиллы","Бизнес","Data Science","CX / Клиентский опыт","Обучение"]
col_theme1, col_theme2 = st.columns([4,1])
with col_theme1:
    selected_themes = st.multiselect("По тематике:", options=allowed_themes, default=allowed_themes)
with col_theme2:
    all_themes_selected = set(selected_themes) == set(allowed_themes)
    select_all_themes = st.checkbox("выбрать все варианты", value=all_themes_selected, key='themes')

if select_all_themes and not all_themes_selected:
    selected_themes = allowed_themes
elif not select_all_themes and all_themes_selected and len(selected_themes) < len(allowed_themes):
    select_all_themes = False

df = filter_multi_category(df, 'Тематика', selected_themes)

# Про что
allowed_about = ["Вакансии","Дизайн","Исследования","Менеджмент","Продукт","Разработка","Обучение"]
col_about1, col_about2 = st.columns([4,1])
with col_about1:
    selected_about = st.multiselect("По направлению:", options=allowed_about, default=allowed_about)
with col_about2:
    all_about_selected = set(selected_about) == set(allowed_about)
    select_all_about = st.checkbox("выбрать все варианты", value=all_about_selected, key='about')

if select_all_about and not all_about_selected:
    selected_about = allowed_about
elif not select_all_about and all_about_selected and len(selected_about) < len(allowed_about):
    select_all_about = False

df = filter_multi_category(df, 'Про что', selected_about)

# Фильтрация по типам
if selected_types:
    df = df[df['Тип'].isin(selected_types)]

# ======================
# Таблица с данными по выбранным фильтрам / поиску
# ======================
total_channels = len(df)
companies_count = len(df[df['Тип'] == 'Компания'])
personal_count = len(df[df['Тип'] == 'Персональный'])
aggregators_count = len(df[df['Тип'] == 'Агрегатор'])

summary_df = pd.DataFrame({
    "Категория": ["Всего каналов", "Количество компаний", "Количество персональных", "Количество агрегаторов"],
    "Количество каналов": [total_channels, companies_count, personal_count, aggregators_count]
})

# Отображаем таблицу с кастомной шириной, по центру и с выравниванием
styled_table = f"""
<style>
.table-container {{
    display: flex;
    justify-content: center;
}}
table {{
    width: 500px !important;
    border-collapse: collapse;
}}
th {{
    text-align: left !important;
    padding: 4px 8px;
}}
td {{
    text-align: left !important;
    padding: 4px 8px;
}}
</style>

<div class="table-container">
{summary_df.to_html(index=False)}
</div>
"""

st.markdown(styled_table, unsafe_allow_html=True)

# ======================
# Визуализации
# ======================
def plot_bar(df_filtered, title, value_col, y_col='Название канала', max_rows=25, key=None, show_checkbox=True):
    if value_col not in df_filtered.columns:
        st.warning(f"Колонка '{value_col}' отсутствует в данных.")
        return
    
    df_sorted = df_filtered.sort_values(by=value_col, ascending=True)
    total_rows = len(df_sorted)
    
    if not key:
        key = title

    show_all = False
    if show_checkbox and total_rows > max_rows:
        show_all = st.checkbox("Показать статистику по всем каналам", key=f"{key}_show_all")
    
    if show_all or total_rows <= max_rows:
        df_display = df_sorted
    else:
        df_display = df_sorted.tail(max_rows)
    
    height = len(df_display) * 20 + 200

    fig = px.bar(
        df_display,
        x=value_col,
        y=y_col,
        orientation='h',
        title=title,
        height=height
    )
    st.plotly_chart(fig, use_container_width=True)

# Подписчики
st.subheader("Количество подписчиков")
col1, col2 = st.columns(2)
with col1:
    df_company = df[df['Тип'] == 'Компания']
    plot_bar(df_company, "Каналы компаний", 'Подписчики', key='comp_subs')
with col2:
    df_personal = df[df['Тип'] == 'Персональный']
    plot_bar(df_personal, "Личные блоги", 'Подписчики', key='pers_subs')

# Посты за 30 дней
st.subheader("Авторских постов / за 30 дней")
col3, col4 = st.columns(2)
with col3:
    plot_bar(df_company, "Каналы компаний", 'Постов за 30 дней', key='comp_posts')
with col4:
    plot_bar(df_personal, "Личные блоги", 'Постов за 30 дней', key='pers_posts')

# Комментарии за 30 дней
st.subheader("Число комментариев / за 30 дней")
col5, col6 = st.columns(2)
with col5:
    plot_bar(df_company, "Каналы компаний", 'Комментариев за 30 дней', key='comp_comms')
with col6:
    plot_bar(df_personal, "Личные блоги", 'Комментариев за 30 дней', key='pers_comms')

# Комментарии на 1 пост
st.subheader("В среднем комментариев / на 1 пост")
col7, col8 = st.columns(2)
with col7:
    plot_bar(df_company, "Каналы компаний", 'Комментов на 1 пост', key='comp_comms_post')
with col8:
    plot_bar(df_personal, "Личные блоги", 'Комментов на 1 пост', key='pers_comms_post')

# ======================
# Новые визуализации (Агрегаторы)
# ======================
st.header("Агрегаторы")

col9, col10 = st.columns(2)
with col9:
    df_agg = df[df['Тип'] == 'Агрегатор']
    plot_bar(df_agg, "Число подписчиков", 'Подписчики', key='agg_subs', show_checkbox=False)
with col10:
    plot_bar(df_agg, "Количество постов / за последний 30 дней", 'Постов за 30 дней', key='agg_posts', show_checkbox=False)

# ======================
# Сводная таблица
# ======================
st.header("Сводная таблица по каналам")
st.dataframe(df, use_container_width=True)

# ======================
# Блок информации о канале
# ======================
st.header("Подробная информация о каналах")

# Используем полный DataFrame без фильтров для информации о канале
full_df = pd.read_csv(url, sep="\t")
full_df.columns = full_df.columns.str.strip()

search_options_full = pd.concat([full_df['Название канала'], full_df['Username'], full_df['Автор']]).dropna().unique()

channel_selection = st.selectbox(
    "Выберите канал:",
    options=search_options_full
)

channel_info = full_df[
    (full_df['Название канала'] == channel_selection) |
    (full_df['Username'] == channel_selection) |
    (full_df['Автор'] == channel_selection)
]

if not channel_info.empty:
    # Перенос строк в описании
    if 'Описание' in channel_info.columns:
        desc = channel_info.iloc[0]['Описание']
        wrapped_desc = "\n".join(textwrap.wrap(str(desc), width=80))
        channel_info.loc[channel_info.index[0], 'Описание'] = wrapped_desc
    st.write(channel_info.T)
