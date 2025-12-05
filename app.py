import streamlit as st
from google import genai

st.set_page_config(page_title="Gemini Models Explorer", page_icon="🔍", layout="wide")

st.title("🔍 Gemini Models Explorer")
st.write("רשימת מודלי Gemini שניתן להשתמש בהם מהאפליקציה שלך, כולל סוג שימוש מומלץ.")

# --- קריאת מפתח מה-secrets ---
API_KEY = (
    st.secrets.get("GOOGLE_API_KEY")
    or st.secrets.get("GEMINI_API_KEY")
)

if not API_KEY:
    st.error("חסר מפתח API. הגדר GOOGLE_API_KEY או GEMINI_API_KEY ב־secrets.toml של Streamlit.")
    st.stop()

# יצירת לקוח ל-Gemini Developer API
client = genai.Client(api_key=API_KEY)


# --- Fallback סטטי (למקרה שה-API לא מחזיר כלום) ---
FALLBACK_MODELS = [
    {"id": "gemini-2.5-pro", "category": "Chat / Reasoning", "notes": "מודל חזק לחשיבה מרובת שלבים, קוד וניתוח מורכב."},
    {"id": "gemini-2.5-flash", "category": "Chat / General", "notes": "מהיר וזול יחסית, מתאים לצ'אט, סיכומים ועומס גבוה."},
    {"id": "gemini-2.5-flash-lite", "category": "Chat / Cost-Optimized", "notes": "גרסה קלה וזולה לעומסים כבדים ו-latency נמוך."},
    {"id": "gemini-3-pro-preview", "category": "Chat / Reasoning (Preview)", "notes": "דור חדש, כרגע ב-Preview – מומלץ ל-POC בלבד."},
    {"id": "gemini-flash-latest", "category": "Chat / General (Alias)", "notes": "Alias למודל Flash האחרון."},
    {"id": "gemini-pro-latest", "category": "Chat / Reasoning (Alias)", "notes": "Alias למודל Pro האחרון."},
    {"id": "text-embedding-004", "category": "Embeddings", "notes": "מודל embedding למשימות חיפוש ו-clustering."},
    {"id": "gemini-embedding-001", "category": "Embeddings", "notes": "מודל embedding נוסף, מתאים ליישומי טקסט כלליים."},
    {"id": "imagen-4.0-generate-001", "category": "Image Generation", "notes": "יצירת תמונות מטקסט."},
    {"id": "veo-3.0-generate-001", "category": "Video Generation", "notes": "יצירת וידאו מטקסט/תיאור."},
]


def classify_type(short_id: str) -> str:
    sid = short_id.lower()

    if "embedding" in sid:
        return "Embeddings"

    if "imagen" in sid or "veo" in sid or "image" in sid:
        return "Image / Video"

    if "live" in sid or "tts" in sid or "native-audio" in sid or "audio" in sid:
        return "Audio / Live"

    if "gemma" in sid:
        return "Chat / Lightweight (Gemma)"

    if "gemini" in sid:
        return "Chat / General"

    return "Other / Tools"


def is_recommended(short_id: str) -> bool:
    sid = short_id.lower()
    recommended_ids = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-3-pro-preview",
        "text-embedding-004",
        "gemini-embedding-001",
        "imagen-4.0-generate-001",
        "veo-3.0-generate-001",
    ]
    return any(sid == r or sid.endswith("/" + r) for r in recommended_ids)


@st.cache_data(show_spinner=True)
def fetch_models_from_api():
    """ניסיון להביא רשימת מודלים מה-Gemini API. אם ריק – נחזיר []."""
    items = []
    try:
        pager = client.models.list()
        for m in pager:
            name = getattr(m, "name", "") or getattr(m, "model", "")
            if not name:
                continue

            short_id = name.split("/")[-1]

            display_name = getattr(m, "display_name", "") or ""
            description = getattr(m, "description", "") or ""

            items.append(
                {
                    "full_id": name,
                    "id": short_id,
                    "display_name": display_name,
                    "description": description,
                    "type": classify_type(short_id),
                    "recommended": is_recommended(short_id),
                }
            )
    except Exception as e:
        st.warning(f"models.list() נכשל מה-API: {e}")
    return items


api_models = fetch_models_from_api()

# --- פילטרים בצד ---
with st.sidebar:
    st.header("⚙️ פילטרים")
    show_only_recommended = st.checkbox("רק מודלים מומלצים לשימוש שוטף", value=True)
    type_filter = st.multiselect(
        "סינון לפי סוג מודל",
        options=["Chat / General", "Chat / Lightweight (Gemma)", "Embeddings", "Image / Video", "Audio / Live", "Other / Tools"],
        default=["Chat / General", "Chat / Lightweight (Gemma)", "Embeddings", "Image / Video", "Audio / Live"],
    )
    search_text = st.text_input("🔎 חיפוש לפי שם/תיאור/ID:", value="")

# --- תצוגת API ---

st.subheader("תוצאה מה-API הרשמי")

if len(api_models) == 0:
    st.info(
        "ה-SDK לא החזיר מודלים (0 תוצאות). "
        "זה יכול להיות בגלל סוג החשבון/מפתח. "
        "למטה תוצג רשימת מודלים סטנדרטית לפי הדוקומנטציה."
    )
    st.write("📦 נמצאו **0 מודלים** מה-API.")
else:
    # סינון
    filtered_api = []
    q = (search_text or "").strip().lower()

    for m in api_models:
        if m["type"] not in type_filter:
            continue
        if show_only_recommended and not m["recommended"]:
            continue

        blob = " ".join(
            [
                str(m.get("id", "")),
                str(m.get("full_id", "")),
                str(m.get("display_name", "")),
                str(m.get("description", "")),
                str(m.get("type", "")),
            ]
        ).lower()
        if q and q not in blob:
            continue

        filtered_api.append(m)

    st.write(f"📦 נמצאו **{len(filtered_api)}** מודלים אחרי סינון.")

    # טבלה קומפקטית
    if filtered_api:
        table_data = [
            {
                "ID קצר": m["id"],
                "ID מלא": m["full_id"],
                "סוג": m["type"],
                "מומלץ": "✅" if m["recommended"] else "",
                "Display Name": m["display_name"],
            }
            for m in filtered_api
        ]
        st.dataframe(table_data, use_container_width=True)

    # פירוט לכל מודל
    st.markdown("---")
    for m in filtered_api:
        with st.expander(f'{m["id"]}  ·  {m["type"]}', expanded=False):
            st.write("**ID מלא:**", m.get("full_id", "—"))
            st.write("**Display Name:**", m.get("display_name") or "—")
            st.write("**סוג:**", m.get("type", "—"))
            st.write("**מומלץ לשימוש שוטף:**", "✅ כן" if m.get("recommended") else "—")
            st.write("**Description:**", m.get("description") or "—")

st.markdown("---")

# --- תצוגת Fallback סטטי ---

st.subheader("Fallback – רשימת מודלים סטנדרטית לפי הדוקומנטציה")

search_fb = st.text_input("חיפוש במודלי fallback (id / category / הערות):", key="search_fb")
q_fb = (search_fb or "").strip().lower()

filtered_fb = []
for m in FALLBACK_MODELS:
    blob = " ".join(
        [
            str(m.get("id", "")),
            str(m.get("category", "")),
            str(m.get("notes", "")),
        ]
    ).lower()
    if q_fb and q_fb not in blob:
        continue
    filtered_fb.append(m)

st.write(f"📦 נמצאו **{len(filtered_fb)}** מודלים ברשימת ה-fallback.")

for m in filtered_fb:
    with st.expander(str(m.get("id", "")), expanded=False):
        st.write("**קטגוריה:**", m.get("category", "—"))
        st.write("**הערות:**", m.get("notes", "—"))
