import streamlit as st
from google import genai

# קריאת מפתח מה-Secrets של Streamlit
API_KEY = st.secrets["GOOGLE_API_KEY"]
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="Gemini Models Explorer", layout="wide")

st.title("🔍 Gemini Models Explorer")
st.write("רשימת כל מודלי Gemini הזמינים בחשבון שלך.")


# --- Filters ---
col1, col2, col3 = st.columns(3)
only_active = col1.checkbox("Active only", value=True)
text_only = col2.checkbox("Text models only", value=False)
embeddings_only = col3.checkbox("Embeddings only", value=False)


@st.cache_data(show_spinner=True)
def fetch_models():
    raw = client.models.list()
    out = []
    for m in raw:
        # חלק מהאובייקטים מגיעים כ־dict-like
        d = m.to_dict() if hasattr(m, "to_dict") else dict(m)
        out.append(d)
    return out


models = fetch_models()

# --- Filtering ---
filtered = []
for m in models:

    # סינון Active
    if only_active and m.get("state") != "ACTIVE":
        continue

    # סינון טקסט בלבד
    if text_only and "generateContent" not in m.get("supported_generation_methods", []):
        continue

    # סינון Embeddings בלבד
    if embeddings_only and "embedContent" not in m.get("supported_generation_methods", []):
        continue

    filtered.append(m)

st.subheader(f"📦 נמצאו {len(filtered)} מודלים")

# --- Display ---
for m in filtered:
    with st.expander(m.get("name", "unknown model"), expanded=False):
        st.write(f"**Display name:** {m.get('display_name')}")
        st.write(f"**State:** {m.get('state')}")
        st.write(f"**Base model:** {m.get('base_model')}")
        st.write(f"**Input tokens:** {m.get('input_token_limit')}")
        st.write(f"**Output tokens:** {m.get('output_token_limit')}")
        st.write(f"**Methods:** {m.get('supported_generation_methods')}")
        st.write(f"**Description:**\n{m.get('description')}")
