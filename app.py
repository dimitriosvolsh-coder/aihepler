
import os
import base64
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Study Helper",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 AI Study Helper")
st.caption("Твій AI-помічник у навчанні")


# ----------------------------
# Gemini API
# ----------------------------

def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


def get_client():
    key = get_api_key()
    if not key:
        raise ValueError(
            "Не знайдено GEMINI_API_KEY. "
            "Перевір файл .streamlit/secrets.toml"
        )
    return genai.Client(api_key=key)


def ask_ai(prompt, instructions=None):
    client = get_client()

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=instructions or (
                "Ти — уважний AI-репетитор. "
                "Відповідай українською мовою. "
                "Пояснюй зрозуміло та крок за кроком. "
                "Не вигадуй відсутні дані."
            ),
            max_output_tokens=1800,
        ),
    )

    if not response.text:
        raise RuntimeError("AI не повернув текстову відповідь.")

    return response.text


# ----------------------------
# Історія
# ----------------------------

if "history" not in st.session_state:
    st.session_state.history = []


def save_history(section, question, answer):
    st.session_state.history.insert(
        0,
        {
            "section": section,
            "question": question,
            "answer": answer,
        },
    )


# ----------------------------
# Меню
# ----------------------------

page = st.sidebar.radio(
    "Оберіть розділ",
    [
        "Головна",
        "Пояснення теми",
        "Розв'язати задачу",
        "Розібрати фото",
        "Тест",
        "Історія",
    ],
)


# ----------------------------
# Головна
# ----------------------------

if page == "Головна":
    st.header("Привіт! 👋")
    st.write(
        "Твій навчальний помічник допоможе пояснювати теми, "
        "розв'язувати задачі та готуватися до уроків."
    )
    st.markdown(
        """
        - 📚 Пояснення навчальних тем
        - 🧮 Розв'язання задач
        - 📸 Розпізнавання завдань із фотографій
        - 📝 Створення тестів
        - 📖 Історія відповідей
        """
    )


# ----------------------------
# Пояснення теми
# ----------------------------

elif page == "Пояснення теми":
    st.header("📚 Пояснення теми")

    topic = st.text_input(
        "Яку тему пояснити?",
        placeholder="Наприклад: квадратні рівняння",
    )

    level = st.selectbox(
        "Рівень пояснення",
        [
            "Просто, як для початківця",
            "Шкільний рівень",
            "Докладно з прикладами",
        ],
    )

    if st.button("Пояснити тему", type="primary"):
        if not topic.strip():
            st.warning("Введи назву теми.")
        else:
            try:
                with st.spinner("Gemini готує пояснення..."):
                    answer = ask_ai(
                        f"Поясни тему: {topic}\n"
                        f"Рівень: {level}.\n"
                        "Додай приклади та короткий підсумок."
                    )

                st.markdown("### Відповідь AI")
                st.markdown(answer)
                save_history("Пояснення теми", topic, answer)

            except Exception as e:
                st.error(f"Не вдалося отримати відповідь: {e}")


# ----------------------------
# Розв'язання задачі
# ----------------------------

elif page == "Розв'язати задачу":
    st.header("🧮 Розв'язати задачу")

    problem = st.text_area(
        "Введи умову задачі",
        placeholder="Напиши умову завдання тут...",
        height=150,
    )

    detail = st.selectbox(
        "Як пояснювати розв'язання?",
        ["Докладно, крок за кроком", "Звичайно", "Коротко"],
    )

    if st.button("Розв'язати", type="primary"):
        if not problem.strip():
            st.warning("Спочатку введи умову задачі.")
        else:
            try:
                with st.spinner("Gemini розв'язує задачу..."):
                    answer = ask_ai(
                        f"Розв'яжи задачу:\n{problem}\n"
                        f"Рівень пояснення: {detail}.\n"
                        "Покажи послідовність кроків, поясни їх "
                        "і наприкінці запиши відповідь. "
                        "Перевір обчислення, якщо це можливо."
                    )

                st.markdown("### Розв'язання")
                st.markdown(answer)
                save_history("Розв'язання задачі", problem, answer)

            except Exception as e:
                st.error(f"Не вдалося розв'язати задачу: {e}")


# ----------------------------
# Розпізнавання фотографії
# ----------------------------

elif page == "Розібрати фото":
    st.header("📸 Розібрати завдання з фото")

    st.write(
        "Завантаж фотографію. Gemini прочитає умову "
        "та спробує розв'язати завдання."
    )

    photo = st.file_uploader(
        "Обери фотографію завдання",
        type=["png", "jpg", "jpeg"],
    )

    detail = st.selectbox(
        "Рівень пояснення",
        ["Докладно", "Звичайно", "Коротко"],
        key="photo_level",
    )

    if photo is not None:
        st.image(photo, caption="Завантажене завдання", width=450)

        if st.button("🤖 Розпізнати та розв'язати", type="primary"):
            try:
                client = get_client()
                image_bytes = photo.getvalue()

                with st.spinner("Gemini аналізує фотографію..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(
                                data=image_bytes,
                                mime_type=photo.type,
                            ),
                            (
                                "Прочитай завдання на фотографії. "
                                "Відповідай українською мовою. "
                                f"Рівень пояснення: {detail}. "
                                "Спочатку перепиши умову, потім "
                                "покажи розв'язання крок за кроком "
                                "і запиши остаточну відповідь. "
                                "Якщо текст нечіткий, скажи про це "
                                "і не вигадуй відсутні дані."
                            ),
                        ],
                        config=types.GenerateContentConfig(
                            max_output_tokens=2000,
                        ),
                    )

                answer = response.text

                if not answer:
                    raise RuntimeError(
                        "Gemini не повернув відповідь."
                    )

                st.markdown("### 📝 Результат")
                st.markdown(answer)

                save_history(
                    "Розбір фото",
                    "Завдання з фотографії",
                    answer,
                )

            except Exception as e:
                st.error(f"Не вдалося обробити фотографію: {e}")


# ----------------------------
# Створення тесту
# ----------------------------

elif page == "Тест":
    st.header("📝 Створити тест")

    topic = st.text_input(
        "Тема тесту",
        placeholder="Наприклад: біологія — клітина",
    )

    count = st.selectbox(
        "Кількість запитань",
        [5, 10, 15],
    )

    difficulty = st.selectbox(
        "Складність",
        ["Легка", "Середня", "Складна"],
    )

    if st.button("Створити тест", type="primary"):
        if not topic.strip():
            st.warning("Введи тему тесту.")
        else:
            try:
                with st.spinner("Gemini створює тест..."):
                    answer = ask_ai(
                        f"Створи тест українською мовою на тему: {topic}.\n"
                        f"Кількість запитань: {count}.\n"
                        f"Складність: {difficulty}.\n"
                        "Для кожного запитання дай чотири варіанти "
                        "відповіді A, B, C, D. Наприкінці додай "
                        "ключ правильних відповідей із поясненнями."
                    )

                st.markdown("### Твій тест")
                st.markdown(answer)
                save_history("Тест", topic, answer)

            except Exception as e:
                st.error(f"Не вдалося створити тест: {e}")


# ----------------------------
# Історія
# ----------------------------

elif page == "Історія":
    st.header("📖 Історія відповідей")

    if not st.session_state.history:
        st.info("Тут поки немає відповідей.")
    else:
        if st.button("Очистити історію"):
            st.session_state.history = []
            st.rerun()

        for item in st.session_state.history:
            with st.expander(
                f"{item['section']} — {item['question'][:60]}"
            ):
                st.markdown(item["answer"])
