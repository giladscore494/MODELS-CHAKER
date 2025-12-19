import streamlit as st
from google import genai

st.set_page_config(page_title="Google GenAI Models Explorer", page_icon="🧭", layout="wide")

st.title("🧭 Google GenAI Models Explorer")
st.write("מציג *כל* המודלים שהמפתח שלך רואה דרך ה-SDK (לא רק Gemini), עם סינון וחיפוש.")

# --- API KEY מה-secrets ---
API_KEY = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("חסר מפתח API. הגדר GOOGLE_API_KEY או GEMINI_API_KEY ב־secrets.toml של Streamlit.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ---------- helpers ----------
def to_str(x):
    try:
        return "" if x is None else str(x)
    except Exception:
        return ""

def classify_family(model_id: str) -> str:
    sid = (model_id or "").lower()
    # משפחות/יכולות נפוצות
    if "embedding" in sid:
        return "Embeddings"
    if any(k in sid for k in ["imagen", "image", "veo", "video"]):
        return "Image / Video"
    if any(k in sid for k in ["audio", "tts", "asr", "native-audio", "live"]):
        return "Audio / Live"
    if "gemma" in sid:
        return "Gemma (Lightweight LLM)"
    if "gemini" in sid:
        return "Gemini (LLM)"
    return "Other / Tools"

def extract_short_id(full_name: str) -> str:
    if not full_name:
        return ""
    return full_name.split("/")[-1]

@st.cache_data(show_spinner=True)
def fetch_models():
    items = []
    err = None
    try:
        pager = client.models.list()
        for m in pager:
            name = getattr(m, "name", None) or getattr(m, "model", None) or ""
            name = to_str(name).strip()
            if not name:
                continue

            short_id = extract_short_id(name)

            display_name = to_str(getattr(m, "display_name", "")) or ""
            description = to_str(getattr(m, "description", "")) or ""

            # יש SDK-ים שמחזירים שדות נוספים – ננסה בעדינות
            version = to_str(getattr(m, "version", "")) or ""
            input_token_limit = to_str(getattr(m, "input_token_limit", "")) or to_str(getattr(m, "inputTokenLimit", ""))
            output_token_limit = to_str(getattr(m, "output_token_limit", "")) or to_str(getattr(m, "outputTokenLimit", ""))
            supported_actions = getattr(m, "supported_actions", None) or getattr(m, "supportedActions", None)
            if supported_actions is None:
                supported_actions_str = ""
            else:
                try:
                    supported_actions_str = ", ".join([to_str(x) for x in supported_actions])
                except Exception:
                    supported_actions_str = to_str(supported_actions)

            items.append(
                {
                    "Full ID": name,
                    "Short ID": short_id,
                    "Family": classify_family(short_id),
                    "Display Name": display_name,
                    "Version": version,
                    "Input Token Limit": input_token_limit,
                    "Output Token Limit": output_token_limit,
                    "Supported Actions": supported_actions_str,
                    "Description": description,
                }
            )
    except Exception as e:
        err = str(e)

    return items, err

# ---------- UI controls ----------
with st.sidebar:
    st.header("⚙️ סינון")
    q = st.text_input("🔎 חיפוש (שם/ID/תיאור):", value="").strip().lower()

    families = [
        "Gemini (LLM)",
        "Gemma (Lightweight LLM)",
        "Embeddings",
        "Image / Video",
        "Audio / Live",
        "Other / Tools",
    ]
    default_families = families  # מציג הכול כברירת מחדל
    family_filter = st.multiselect("סינון לפי Family", options=families, default=default_families)

    # טיפ קטן: לפעמים אנשים רוצים לראות רק Gemini/Gemma
    quick = st.radio(
        "Quick filter",
        options=["All", "Only LLMs (Gemini/Gemma)", "Only Embeddings", "Only Image/Video", "Only Audio/Live"],
        index=0,
    )

# ---------- fetch ----------
st.subheader("תוצאה מה-API (SDK)")
models, err = fetch_models()

if err:
    st.warning(f"models.list() נכשל: {err}")

if not models:
    st.info("לא התקבלו מודלים מה-API. זה יכול להיות הרשאות/מפתח/endpoint. נסה מפתח אחר או בדוק שה-API פעיל בפרויקט.")
    st.stop()

# ---------- apply quick filter ----------
def quick_match(row):
    fam = row.get("Family", "")
    if quick == "All":
        return True
    if quick == "Only LLMs (Gemini/Gemma)":
        return fam in ["Gemini (LLM)", "Gemma (Lightweight LLM)"]
    if quick == "Only Embeddings":
        return fam == "Embeddings"
    if quick == "Only Image/Video":
        return fam == "Image / Video"
    if quick == "Only Audio/Live":
        return fam == "Audio / Live"
    return True

filtered = []
for row in models:
    if row["Family"] not in family_filter:
        continue
    if not quick_match(row):
        continue

    blob = " ".join(
        [
            to_str(row.get("Full ID", "")),
            to_str(row.get("Short ID", "")),
            to_str(row.get("Display Name", "")),
            to_str(row.get("Description", "")),
            to_str(row.get("Family", "")),
            to_str(row.get("Supported Actions", "")),
        ]
    ).lower()

    if q and q not in blob:
        continue

    filtered.append(row)

# ---------- output ----------
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.metric("סה״כ מודלים שהתקבלו", len(models))
with col2:
    st.metric("אחרי סינון", len(filtered))
with col3:
    st.caption("אם אתה מחפש ספציפית Gemini 3 Flash, נסה לחפש: `3` / `flash` / `latest` / `preview` בשדה החיפוש.")

# טבלה
st.dataframe(
    [
        {
            "Short ID": r["Short ID"],
            "Family": r["Family"],
            "Display Name": r["Display Name"],
            "Input": r["Input Token Limit"],
            "Output": r["Output Token Limit"],
            "Supported Actions": r["Supported Actions"],
            "Full ID": r["Full ID"],
        }
        for r in filtered
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.subheader("פירוט מודלים (Expand)")

for r in filtered:
    title = f'{r["Short ID"]}  ·  {r["Family"]}'
    with st.expander(title, expanded=False):
        st.write("**Full ID:**", r["Full ID"] or "—")
        st.write("**Display Name:**", r["Display Name"] or "—")
        st.write("**Family:**", r["Family"] or "—")
        st.write("**Version:**", r["Version"] or "—")
        st.write("**Input Token Limit:**", r["Input Token Limit"] or "—")
        st.write("**Output Token Limit:**", r["Output Token Limit"] or "—")
        st.write("**Supported Actions:**", r["Supported Actions"] or "—")
        st.write("**Description:**", r["Description"] or "—")

st.markdown("---")
st.caption("הערה: הרשימה תלויה במפתח/הרשאות/endpoint (Developer API vs Vertex AI). אם מודל לא מופיע – יכול להיות שהוא לא פתוח לחשבון שלך עדיין.")