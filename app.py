import streamlit as st
import random
from PIL import Image
import torch
import torchvision.transforms as transforms
import openai
import base64

# ---------------- OPENAI CLIENT ----------------
client = openai.OpenAI(
    api_key="YOUR OWN API KEY",
    base_url="https://openrouter.ai/api/v1"
)

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- BACKGROUND ----------------
background_url = "https://img.freepik.com/premium-photo/pixel-art-depicting-pink-clouds-floating-pastel-sky_1406461-2475.jpg?w=360"
st.markdown(f"""
<style>
.stApp {{
    background-image: url('{background_url}');
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- STYLES ----------------
st.markdown("""
<style>
@import url('https://fonts.cdnfonts.com/css/jersey-10');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

html, body, [class*="css"] { font-family: 'Press Start 2P', monospace; }

.title { font-family: 'Jersey 10', cursive; text-align: center; font-size: 60px; color: white;
text-shadow: 3px 3px #ff9bd5, 6px 6px #c77dff, 9px 9px #ff6fb5; }

.panel { font-family: 'Jersey 10', cursive; background: #2E282B; padding: 16px; margin-bottom: 16px;
box-shadow: 6px 6px 0px #d77aff; border-radius: 12px; }

.stButton > button { position: relative; background-color: #ff6fb5 !important; border: 3px solid #b44cff !important;
color: white !important; font-family: 'Jersey 10', monospace !important; font-size: 10px !important;
box-shadow: 4px 4px 0px #b44cff; transition: all 0.15s ease-in-out; overflow: hidden; }

.stButton > button:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0px #b44cff; }

label { font-family: 'Jersey 10', monospace !important; color: #FF96CF !important; background: rgba(255,255,255,0.4) !important; }

.star { position: fixed; pointer-events: none; image-rendering: pixelated; animation: twinkle 1.5s infinite; z-index: 0; }
@keyframes twinkle { 0%,100% {opacity:0.3;} 50% {opacity:1;} }
</style>
""", unsafe_allow_html=True)

# ---------------- PIXEL STARS ----------------
star_url = "https://static.vecteezy.com/system/resources/previews/071/674/013/non_2x/pixel-star-illustration-shape-free-png.png"
stars_html = ""
for _ in range(35):
    stars_html += f"""
    <img src="{star_url}" class="star"
    style="top:{random.randint(0,95)}%;
           left:{random.randint(0,95)}%;
           width:{random.randint(10,20)}px;
           height:auto;
           animation-delay:{random.uniform(0,2)}s;">
    """
st.markdown(stars_html, unsafe_allow_html=True)

# ---------------- COLOR EXTRACTION ----------------
def dominantColours(imagePath, numColour):
    img = Image.open(imagePath).convert("RGB").resize((150,150))
    pixels = (transforms.ToTensor()(img).permute(1,2,0).reshape(-1,3) * 255).float()
    centroids = pixels[torch.randperm(len(pixels))[:numColour]]
    for _ in range(10):
        labels = torch.cdist(pixels, centroids).argmin(1)
        centroids = torch.stack([pixels[labels==i].mean(0) for i in range(numColour)])
    return ['#%02x%02x%02x' % tuple(c.int().tolist()) for c in centroids]

# ---------------- WEATHER INTERPRETER ----------------
def interpret_weather(temp_range, rainy):
    if temp_range == "Cold": return "cold" + (" and rainy" if rainy else "")
    if temp_range == "Mild": return "mild" + (" and rainy" if rainy else "")
    return "hot" + (" and rainy" if rainy else "")

# ---------------- AI OUTFIT GENERATION ----------------
def ai_generate_full_outfit(aesthetic, budget, event, weather, colours):
    prompt = f"""
Create a COMPLETE outfit (Top, Bottom, Outerwear, Shoes, Accessories).
Rules:
- Consider aesthetic: {aesthetic}
- Consider budget: {budget} USD
- Event: {event}
- Weather: {weather}
- Use dominant colors: {', '.join(colours) if colours else 'none'}
- Cold → include jacket/coat
- Rainy → waterproof shoes and outerwear
- Hot → avoid heavy layers
Format exactly:
Top | Store | https://www.google.com/search?q=ITEM+STORE
Bottom | Store | https://www.google.com/search?q=ITEM+STORE
Outerwear | Store | https://www.google.com/search?q=ITEM+STORE
Shoes | Store | https://www.google.com/search?q=ITEM+STORE
Accessories | Store | https://www.google.com/search?q=ITEM+STORE
"""
    res = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    return res.choices[0].message.content

# ---------------- AI IMAGE AESTHETIC ANALYSIS ----------------
def analyze_image_aesthetic(image_path):
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    prompt = "Describe the fashion aesthetic or style in this image. Choose from: Y2K, Cottagecore, Emo/Goth, Coquette, Dark Academia, Clean Girl, Minimalist, Boho, Girly, High Fashion, or specify 'Other' with a brief description if none match."
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}}
        ]}
    ]
    res = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=messages
    )
    return res.choices[0].message.content.strip()

# ---------------- AI AESTHETIC WEBSITES GENERATION ----------------
def generate_aesthetic_websites(aesthetic, colours=None, budget=None, event=None, weather=None):
    prompt = f"""
Suggest 5 specific product or collection pages (not just homepages) from online stores that CLEARLY and strongly embody the {aesthetic} fashion aesthetic.
Each link must go directly to a product or collection that visually matches the following dominant colors: {', '.join(colours) if colours else 'any'}.
Strictly avoid generic, homepage, or irrelevant links. Do NOT include results that do not fit the {aesthetic} style, color, or user preferences below:
 - Budget: {budget if budget else 'any'}
 - Event: {event if event else 'any'}
 - Weather: {weather if weather else 'any'}
Only include links that are a strong, obvious match for the requested vibe. If you cannot find 5, return as many as possible, but do not fill with unrelated links.
IMPORTANT: Only include links that are accessible and working (no 404s, no login required, no region-locked or broken pages). Test the links before including them.
Include a mix of popular brands and unique boutiques.
Format exactly as: Website Name | https://link
"""
    res = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    return res.choices[0].message.content

# ---------------- LAYOUT ----------------
st.markdown("<div class='title'>StyLily</div>", unsafe_allow_html=True)
st.divider()
left, middle, right = st.columns([1,2,1])

# LEFT PANEL
with left:
    st.markdown("<div class='panel'>IMAGE INSPIRATION</div>", unsafe_allow_html=True)
    img = st.file_uploader("Upload image", ["png","jpg","jpeg"])
    colours = []
    detected_aesthetic = ""
    websites = ""
    if img:
        with open("temp.png","wb") as f: f.write(img.getbuffer())
        st.image(img, use_column_width=True)
        colours = dominantColours("temp.png", 3)
        for c in colours:
            st.markdown(f"<div style='background:{c};height:25px'></div>", unsafe_allow_html=True)
        
        # AI Analysis
        try:
            detected_aesthetic = analyze_image_aesthetic("temp.png")
            st.markdown(f"""
<div style='background:#2E282B; color:white; padding:16px; border-radius:12px; margin-bottom:10px; font-weight:bold;'>
Detected Aesthetic: {detected_aesthetic}
</div>
""", unsafe_allow_html=True)
            # Use current user selections for context
            user_budget = st.session_state.get('budget', None)
            user_event = st.session_state.get('event', None)
            user_weather = st.session_state.get('weather', None)
            # Generate websites with all context
            websites = generate_aesthetic_websites(
                detected_aesthetic,
                colours=colours,
                budget=user_budget,
                event=user_event,
                weather=user_weather
            )
            st.markdown("""
<div style='background:#2E282B; color:white; padding:16px; border-radius:12px; margin-bottom:10px; font-weight:bold;'>
Websites matching this aesthetic and color:
<ul style='margin:0; padding-left:20px;'>
""", unsafe_allow_html=True)
            for line in websites.split("\n"):
                if "|" in line:
                    parts = [x.strip() for x in line.split("|")]
                    if len(parts) == 2:
                        name, link = parts
                        st.markdown(f"<li><a href='{link}' style='color:white; text-decoration:underline;' target='_blank'>{name}</a></li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"AI analysis failed: {str(e)}. Please check your API key or try again later.")
            detected_aesthetic = ""

# MIDDLE PANEL
with middle:
    st.markdown("<div class='panel'>OUTFIT GENERATION</div>", unsafe_allow_html=True)

    budget = st.selectbox("Budget", ["0–25","25–50","50–75","75–100","100–125"], key='budget')
    event = st.text_input("Event", key='event')
    temp_range = st.selectbox("Temperature", ["Cold", "Mild", "Hot"], key='temp_range')
    rainy = st.checkbox("Rainy", key='rainy')
    aesthetic = st.selectbox("Aesthetic",
        ["Y2K","Cottagecore","Emo/Goth","Coquette","Dark Academia","Clean Girl","Minimalist","Boho","Girly","High Fashion"], key='aesthetic')
    weather = interpret_weather(temp_range, rainy)

    if st.button("GENERATE OUTFIT"):
        outfit = ai_generate_full_outfit(aesthetic, budget, event, weather, colours)
        st.markdown("<div class='panel'>SHOP THE LOOK</div>", unsafe_allow_html=True)
        for line in outfit.split("\n"):
            if "|" in line:
                name, store, link = [x.strip() for x in line.split("|")]
                st.markdown(f"**{name}** — {store}  \n[{link}]({link})")

# RIGHT PANEL
with right:
    st.markdown("<div class='panel'>AI STYLIST CHAT</div>", unsafe_allow_html=True)

    # Always ensure system message is first
    if "messages" not in st.session_state or not st.session_state.messages or st.session_state.messages[0]["role"] != "system":
        st.session_state.messages = [{"role":"system","content":"You are a fashion stylist."}]

    # Clear chat button
    if st.button("CLEAR CHAT"):
        st.session_state.messages = [{"role":"system","content":"You are a fashion stylist."}]

    # Display chat messages
    for m in st.session_state.messages:
        if m["role"] != "system":
            with st.chat_message(m["role"]):
                st.markdown(f"""
<div style='background:#2E282B; color:white; padding:16px; border-radius:12px; margin-bottom:10px;'>
{m['content']}
</div>
""", unsafe_allow_html=True)

    # Chat input
    if q := st.chat_input("Ask about fashion"):
        # Always start with system message if not present
        if not st.session_state.messages or st.session_state.messages[0]["role"] != "system":
            st.session_state.messages = [{"role":"system","content":"You are a fashion stylist."}]
        # Append user message
        st.session_state.messages.append({"role":"user","content":q})
        # Only send system + user message if this is the first prompt
        messages_to_send = st.session_state.messages
        if len(messages_to_send) == 2:
            messages_to_send = st.session_state.messages[:2]
        r = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages_to_send
        ).choices[0].message.content
        st.session_state.messages.append({"role":"assistant","content":r})
