import streamlit as st
import requests
import os

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide")

# --- INITIALIZATION LOGIC ---
if 'team' not in st.session_state:
    st.session_state['team'] = []
if 'selected_moves' not in st.session_state:
    st.session_state['selected_moves'] = {}

# 2. Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .move-bar-centered {
            color: white; padding: 8px 10px; border-radius: 6px;
            font-size: 11px; font-weight: bold; margin-top: 4px;
            height: 32px; display: flex; align-items: center;
            justify-content: center; text-align: center;
            border-bottom: 3px solid rgba(0,0,0,0.2); text-transform: uppercase;
        }
        .stat-label { font-size: 12px; font-weight: bold; margin-bottom: -5px; }
    </style>
""", unsafe_allow_html=True)

TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

# 3. Helper Functions
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
def get_type_data(type_name):
    try: return requests.get(f"https://pokeapi.co/api/v2/type/{type_name}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    try: return requests.get(move_url).json()
    except: return None

def calculate_analysis(pokemon_types):
    weak, resist, super_eff, not_very = set(), set(), set(), set()
    def_mults = {}
    
    for t_info in pokemon_types:
        data = get_type_data(t_info['type']['name'])
        if data:
            rel = data['damage_relations']
            # Defensive Calculations
            for t in rel['double_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 2.0
            for t in rel['half_damage_from']: def_mults[t['name']] = def_mults.get(t['name'], 1.0) * 0.5
            for t in rel['no_damage_from']: def_mults[t['name']] = 0.0
            
            # Offensive Calculations (What this Pokemon's types hit)
            for t in rel['double_damage_to']: super_eff.add(t['name'])
            for t in rel['half_damage_to']: not_very.add(t['name'])
            for t in rel['no_damage_to']: not_very.add(t['name']) # Immunities also count as "not very effective" offense

    for t, m in def_mults.items():
        if m > 1.0: weak.add(t)
        elif 0.0 <= m < 1.0: resist.add(t)
        
    return sorted(list(weak)), sorted(list(resist)), sorted(list(super_eff)), sorted(list(not_very))

def render_badges(types):
    if not types: return '<span style="font-size:10px; color:gray;">None</span>'
    return "".join([f'<span style="background-color:{TYPE_COLORS.get(t,"#777")}; color:white; padding:2px 4px; border-radius:3px; margin:1px; font-size:10px; display:inline-block; font-weight:bold;">{t.upper()[:4]}</span>' for t in types])

def add_move_callback(idx):
    val = st.session_state[f"search_move_{idx}"]
    if val:
        curr = st.session_state['selected_moves'].get(idx, [])
        if len(curr) < 4 and val not in curr:
            curr.append(val)
            st.session_state['selected_moves'][idx] = curr
        st.session_state[f"search_move_{idx}"] = ""

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
team_count = len(st.session_state['team'])
if st.sidebar.button(f"➡️ Team Builder ({team_count}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Full Team", type="secondary", use_container_width=True):
    st.session_state['team'] = []; st.session_state['selected_moves'] = {}; st.rerun()

# --- MAIN PAGE ---
st.title("🏆 PokéDND Team Builder")
all_names = get_all_pokemon_names()
quick_add = st.selectbox("Quick Add Pokémon:", options=[""] + all_names, format_func=lambda x: x.capitalize() if x else "Search to add...", key="quick_add_team")

if quick_add:
    p_data = get_pokemon_data(quick_add)
    if p_data:
        if len(st.session_state['team']) < 6:
            if not any(p['name'] == p_data['name'] for p in st.session_state['team']):
                st.session_state['team'].append(p_data); st.rerun()
        else: st.error("Team is full!")

st.divider()

if not st.session_state['team']:
    st.info("Your team is empty.")
else:
    cols = st.columns(3)
    STAT_MAP = {"hp": "HP", "attack": "ATK", "defense": "DEF", "special-attack": "SpA", "special-defense": "SpD", "speed": "Spd"}

    for i, p_data in enumerate(st.session_state['team']):
        if i not in st.session_state['selected_moves']: st.session_state['selected_moves'][i] = []
        
        with cols[i % 3]:
            with st.container(border=True):
                h1, h2 = st.columns([5, 1])
                h1.subheader(p_data['name'].capitalize())
                if h2.button("🗑️", key=f"rem_p_{i}"):
                    st.session_state['team'].pop(i); st.session_state['selected_moves'].pop(i, None); st.rerun()

                r1c1, r1c2 = st.columns([1, 1.2])
                with r1c1: st.image(p_data['sprites']['front_default'], width=120)
                with r1c2:
                    for s in p_data['stats']:
                        label, val = STAT_MAP.get(s['stat']['name'], s['stat']['name'].upper()), s['base_stat']
                        st.markdown(f'<div class="stat-label">{label}: {val}</div>', unsafe_allow_html=True)
                        st.progress(min(val / 160, 1.0))

                weak, resist, super_eff, not_very = calculate_analysis(p_data['types'])
                st.markdown('<div style="margin-top:10px; border-top:1px solid #444; padding-top:8px;"></div>', unsafe_allow_html=True)
                
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    st.markdown(f'<div style="font-size:11px; font-weight:bold; color:#ff4b4b;">🛡️ DEFENSE</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:10px;"><b>Weak:</b><br>{render_badges(weak)}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:10px;"><b>Resist:</b><br>{render_badges(resist)}</div>', unsafe_allow_html=True)
                with t_col2:
                    # UPDATED OFFENSE SECTION
                    st.markdown(f'<div style="font-size:11px; font-weight:bold; color:#3498db;">⚔️ OFFENSE</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:10px;"><b>Super:</b><br>{render_badges(super_eff)}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:10px;"><b>Resisted:</b><br>{render_badges(not_very)}</div>', unsafe_allow_html=True)

                st.divider()
                all_m = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in p_data['moves']])))
                st.selectbox("Add Move", options=[""] + all_m, key=f"search_move_{i}", on_change=add_move_callback, args=(i,), label_visibility="collapsed")
                
                for m_idx, m_name in enumerate(st.session_state['selected_moves'][i]):
                    api_n = m_name.lower().replace(" ", "-")
                    try:
                        m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_n)
                        m_details = get_move_details(m_url)
                        bg_color = TYPE_COLORS.get(m_details['type']['name'], "#978fdb")
                        m_col1, m_col2 = st.columns([5, 1])
                        with m_col1: st.markdown(f'<div class="move-bar-centered" style="background-color: {bg_color};">{m_name}</div>', unsafe_allow_html=True)
                        with m_col2: 
                            if st.button("✖", key=f"del_m_{i}_{m_idx}"):
                                st.session_state['selected_moves'][i].pop(m_idx); st.rerun()
                    except: continue
