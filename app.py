import streamlit as st
from google import genai

st.set_page_config(page_title="Gemini Models Explorer", page_icon="🔍", layout="centered")

st.title("🔍 Gemini Models Explorer")
st.write("רשימת מודלי Gemini שניתן להשתמש בהם מהאפליקציה.")

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

# רשימת מודלים סטנדרטית לפי הדוקומנטציה של Gemini (fallback)
FALLBACK_MODELS = [
    {
        "id": "gemini-2.5-pro",
        "category": "Chat / Reasoning",
        "notes": "מודל חזק לחשיבה מרובת שלבים, קוד וניתוח מורכב.",
    },
    {
        "id": "gemini-2.5-flash",
        "category": "Chat / General",
        "notes": "מהיר וזול יחסית, מתאים לצ'אט, סיכומים ועומס גבוה.",
    },
    {
        "id": "gemini-2.5-flash-lite",
        "category": "Chat / Cost-Optimized",
        "notes": "גרסה קלה וזולה לעומסים כבדים ו-latency נמוך.",
    },
    {
        "id": "gemini-2.5-flash-preview-tts",
        "category": "TTS",
        "notes": "המרת טקסט לדיבור (Flash).",
    },
    {
        "id": "gemini-2.5-pro-preview-tts",
        "category": "TTS",
        "notes": "המרת טקסט לדיבור (Pro).",
    },
    {
        "id": "gemini-2.0-flash",
        "category": "Chat / General (דור קודם)",
        "notes": "מודל מהיר מהדור הקודם.",
    },
    {
        "id": "gemini-2.0-flash-lite",
        "category": "Chat / Cost-Optimized (דור קודם)",
        "notes": "גרסת Lite של 2.0 Flash.",
    },
    {
        "id": "gemini-2.0-flash-preview-image-generation",
        "category": "Image Generation",
        "notes": "יצירת תמונות מטקסט (תלוי מדינה).",
    },
    {
        "id": "gemini-2.0-flash-live-001",
        "category": "Live / Audio",
        "notes": "שיחות Live קוליות/מולטימודל בזמן אמת.",
    },
    {
        "id": "text-embedding-004",
        "category": "Embeddings",
        "notes": "מודל embedding למשימות חיפוש ו-clustering.",
    },
    {
        "id": "models/embedding-001",
        "category": "Embeddings",
        "notes": "מודל embedding ותיק יותר.",
    },
]


@st.cache_data(show_spinner=True)
def fetch_models_from_api():
    """ניסיון להביא רשימת מודלים מה-Gemini API. אם ריק – נחזיר []."""
    items = []
    try:
        pager = client.models.list()
        for m in pager:
            # אובייקט המודל מגיע מה-SDK, לא תמיד אותו מבנה – נמשוך מה שיש.
            name = getattr(m, "name", "") or getattr(m, "model", "")
            display_name = getattr(m, "display_name", "")
            description = getattr(m, "description", "")
            if not name:
                continue
            items.append(
                {
                    "id": name,
                    "display_name": display_name,
                    "description": description,
                }
            )
    except Exception as e:
        st.warning(f"models.list() נכשל מה-API: {e}")
    return items


api_models = fetch_models_from_api()

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
    st.success(f"📦 נמצאו **{len(api_models)} מודלים** מה-API.")
    search_api = st.text_input("חיפוש במודלים מה-API (שם / תיאור):", key="search_api")
    q = (search_api or "").strip().lower()

    filtered_api = []
    for m in api_models:
        blob = " ".join(
            [
                str(m.get("id", "")),
                str(m.get("display_name", "")),
                str(m.get("description", "")),
            ]
        ).lower()
        if q in blob:
            filtered_api.append(m)

    st.write(f"🔎 סינון API: **{len(filtered_api)}** מודלים לאחר חיפוש.")
    for m in filtered_api:
        with st.expander(str(m.get("id", "unknown")), expanded=False):
            st.write("**Display Name:**", m.get("display_name") or "—")
            st.write("**Description:**", m.get("description") or "—")

st.markdown("---")

# --- תצוגת Fallback ---

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
    if q_fb in blob:
        filtered_fb.append(m)

st.write(f"📦 נמצאו **{len(filtered_fb)}** מודלים ברשימת ה-fallback.")

for m in filtered_fb:
    with st.expander(str(m.get("id", "")), expanded=False):
        st.write("**קטגוריה:**", m.get("category", "—"))
        st.write("**הערות:**", m.get("notes", "—"))
