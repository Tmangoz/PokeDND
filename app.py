import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="PokéDND Explorer", layout="wide")

# 2. Advanced Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        
        .centered-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            width: 100%;
        }
        
        .move-badge {
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            margin: 3px;
            font-size: 10px;
            font-weight: bold;
            display: inline-block;
            text-align: center;
            width: 135px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            border-bottom: 3px solid rgba(0,0,0,0.3);
        }
        
        .tm-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
    </style>
""", unsafe_allow_html=True)

TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

# 3. Cached Data Fetching
@st.cache_data(ttl=86400)
def get_all_pokemon_names():
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        return [p['name'] for p in requests.get(url).json()['results']]
    except: return []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    if not name: return None
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
    return res.json() if res.status_code == 200 else None

@st.cache_data(ttl=86400)
def get_move_info(move_url):
    try: return requests.get(move_url).json()
    except: return None

# 4. Session State Initialization
if 'team' not in st.session_state: 
    st.session_state['team'] = []

# --- SIDEBAR MENU ---
st.sidebar.title("🎮 PokéDND Menu")

# Navigation
if st.sidebar.button("🏠 Home Page", use_container_width=True):
    st.switch_page("app.py")

# Restored Team Counter Logic
team_count = len(st.session_state['team'])
if st.sidebar.button(f"➡️ Team Builder ({team_count}/6)", use_container_width=True):
    st.switch_page("pages/Team_Builder.py")

st.sidebar.divider()

# Restored Clear Team Button in Sidebar
if st.sidebar.button("🗑️ Clear Full Team", type="secondary", use_container_width=True):
    st.session_state['team'] = []
    if 'selected_moves' in st.session_state:
        st.session_state['selected_moves'] = {}
    st.rerun()

# --- MAIN INTERFACE ---
st.title("🔍 Pokémon Explorer")
all_names = get_all_pokemon_names()
search_query = st.selectbox("Search for a Pokémon:", options=[""] + all_names, format_func=lambda x: x.capitalize() if x else "Start typing...", index=0)

if search_query:
    p_data = get_pokemon_data(search_query)
    if p_data:
        st.divider()
        col1, col2 = st.columns([2, 3])
        
        with col1:
            artwork = p_data['sprites']['other']['official-artwork']['front_default']
            img_url = artwork if artwork else p_data['sprites']['front_default']
            
            st.markdown(f'''
                <div class="centered-container">
                    <img src="{img_url}" width="380" style="margin-bottom: 20px;">
                </div>
            ''', unsafe_allow_html=True)
            
            if st.button(f"➕ Add {p_data['name'].capitalize()} to Team", use_container_width=True, type="primary"):
                if len(st.session_state['team']) < 6:
                    if any(p['name'] == p_data['name'] for p in st.session_state['team']):
                        st.warning("Already in your team!")
                    else:
                        st.session_state['team'].append(p_data)
                        st.success("Added!")
                        st.rerun()
                else: 
                    st.error("Team is full!")

        with col2:
            st.header(p_data['name'].capitalize())
            type_badges = "".join([f'<span style="background-color:{TYPE_COLORS.get(t["type"]["name"],"#777")}; color:white; padding:5px 15px; border-radius:20px; margin-right:10px; font-weight:bold; font-size:16px;">{t["type"]["name"].upper()}</span>' for t in p_data['types']])
            st.markdown(type_badges, unsafe_allow_html=True)
            
            st.write("### Base Stats")
            STAT_LABELS = {"hp": "HP", "attack": "ATK", "defense": "DEF", "special-attack": "SpA", "special-defense": "SpD", "speed": "Spd"}
            stat_cols = st.columns(2)
            for idx, s in enumerate(p_data['stats']):
                label, val = STAT_LABELS.get(s['stat']['name'], s['stat']['name'].upper()), s['base_stat']
                with stat_cols[idx % 2]:
                    st.markdown(f"**{label}:** {val}")
                    st.progress(min(val / 160, 1.0))

            st.divider()
            st.write("### 📀 Learnable TMs")
            
            tm_moves = [m for m in p_data['moves'] if any(v['move_learn_method']['name'] == 'machine' for v in m['version_group_details'])]
            
            if tm_moves:
                move_html = '<div class="tm-grid">'
                for m in sorted(tm_moves, key=lambda x: x['move']['name']):
                    m_name = m['move']['name'].replace("-", " ").upper()
                    m_data = get_move_info(m['move']['url'])
                    m_type = m_data['type']['name'] if m_data else "normal"
                    bg = TYPE_COLORS.get(m_type, "#777")
                    move_html += f'<div class="move-badge" style="background-color: {bg};">{m_name}</div>'
                move_html += '</div>'
                st.markdown(move_html, unsafe_allow_html=True)
            else:
                st.info("No TMs found.")
    else:
        st.error("Pokémon not found.")
else:
    st.info("Select a Pokémon above to get started.")
