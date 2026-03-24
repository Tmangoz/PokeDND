import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# --- INITIALIZATION ---
if 'team' not in st.session_state: st.session_state['team'] = []
if 'selected_moves' not in st.session_state: st.session_state['selected_moves'] = {}
if 'attacker_search' not in st.session_state: st.session_state['attacker_search'] = ""

# 2. Styling & Colors
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .battle-log {
            background-color: #0e1117; color: #00ff00; padding: 15px;
            border-radius: 8px; font-family: 'Courier New', monospace;
            border: 1px solid #333; line-height: 1.4; font-size: 14px; margin-top: 10px;
        }
        .turn-order-banner {
            background: #1e1e1e; padding: 10px; border-radius: 10px;
            text-align: center; border: 1px solid #444; margin-bottom: 20px; font-weight: bold;
        }
        .type-badge {
            color: white; padding: 2px 8px; border-radius: 4px;
            font-size: 10px; font-weight: bold; text-transform: uppercase;
            margin-left: 5px; display: inline-block;
        }
        .move-card {
            border: 1px solid #444; border-radius: 8px; padding: 12px;
            text-align: center; background: rgba(255,255,255,0.03);
        }
    </style>
""", unsafe_allow_html=True)

# 3. Helpers
def get_move_power_bonus(power):
    if not power: return 0
    if 10 <= power <= 40: return 1
    if 41 <= power <= 60: return 2
    if 61 <= power <= 75: return 3
    if 76 <= power <= 90: return 4
    if 91 <= power <= 110: return 5
    if 111 <= power <= 130: return 6
    return 7 if power >= 131 else 0

def render_type_badges(pokemon_data):
    badges = ""
    for t in pokemon_data['types']:
        c = TYPE_COLORS.get(t['type']['name'], "#777")
        badges += f'<span class="type-badge" style="background-color: {c};">{t["type"]["name"]}</span>'
    return badges

@st.cache_data(ttl=86400)
def get_type_modifier(move_type, defender_types):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/type/{move_type.lower()}").json()
        rel = res['damage_relations']
        mod = 0
        for d_type in defender_types:
            if any(t['name'] == d_type for t in rel['double_damage_to']): mod += 2
            if any(t['name'] == d_type for t in rel['half_damage_to']): mod -= 2
            if any(t['name'] == d_type for t in rel['no_damage_to']): return -999 
        return mod
    except: return 0

@st.cache_data(ttl=86400)
def get_move_info(move_name):
    try: return requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower().replace(' ', '-')}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_all_learnable_moves(pokemon_name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}").json()
        return sorted(list(set([m['move']['name'].replace("-", " ").title() for m in res['moves']])))
    except: return []

# --- SIDEBAR MENU (RESTORED) ---
st.sidebar.title("🎮 PokéDND Menu")

if st.sidebar.button("🏠 Home Page", use_container_width=True):
    st.switch_page("app.py")

team_count = len(st.session_state.get('team', []))
if st.sidebar.button(f"➡️ Team Builder ({team_count}/6)", use_container_width=True):
    st.switch_page("pages/Team_Builder.py")

if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True):
    st.switch_page("pages/Battle_Sim.py")

st.sidebar.divider()

if st.sidebar.button("🗑️ Clear Full Team", type="secondary", use_container_width=True):
    st.session_state['team'] = []
    st.session_state['selected_moves'] = {}
    st.session_state['shiny_states'] = {}
    st.rerun()

# --- MAIN INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

# Team Ribbon
if st.session_state['team']:
    st.write("### 👥 Quick Select from Team")
    ribbon = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        with ribbon[i]:
            shiny = st.session_state.get('shiny_states', {}).get(i, False)
            st.image(p['sprites']['front_shiny' if shiny else 'front_default'], width=80)
            if st.button(f"Select {p['name'].capitalize()}", key=f"q_{i}", use_container_width=True):
                st.session_state['attacker_search'] = p['name']
                st.session_state['is_team_selection'] = True
                st.session_state['active_team_idx'] = i 
                st.rerun()

st.divider()

# Setup Data
atk_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{st.session_state['attacker_search'].lower()}").json() if st.session_state['attacker_search'] else None
def_name = st.session_state.get('def_s', "")
def_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{def_name.lower()}").json() if def_name else None

# Speed Banner
if atk_data and def_data:
    a_spd, d_spd = atk_data['stats'][5]['base_stat'] // 15, def_data['stats'][5]['base_stat'] // 15
    first = atk_data['name'].capitalize() if a_spd >= d_spd else def_data['name'].capitalize()
    st.markdown(f'<div class="turn-order-banner">🏃 {first} attacks FIRST (Speed: {max(a_spd, d_spd)} vs {min(a_spd, d_spd)})</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
all_p = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

with col1:
    st.subheader("🛡️ Attacker")
    val = st.selectbox("Search Attacker", options=[""] + all_p, label_visibility="collapsed",
                       index=all_p.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_p else 0)
    
    if val != st.session_state['attacker_search']:
        st.session_state['attacker_search'] = val
        st.session_state['is_team_selection'] = any(p['name'] == val for p in st.session_state['team'])
        st.rerun()

    attacker = atk_data
    if attacker:
        st.markdown(f"**HP:** {attacker['stats'][0]['base_stat']//10} | **Speed:** {attacker['stats'][5]['base_stat']//15} {render_type_badges(attacker)}", unsafe_allow_html=True)
        st.image(attacker['sprites']['front_default'], width=120)

with col2:
    st.subheader("🎯 Target")
    defender_name = st.selectbox("Target Search", options=[""] + all_p, key="def_s", label_visibility="collapsed")
    defender = def_data
    if defender:
        d_hp, d_spd = defender['stats'][0]['base_stat'] // 10, defender['stats'][5]['base_stat'] // 15
        st.markdown(f"**HP:** {d_hp} | **Speed:** {d_spd} {render_type_badges(defender)}", unsafe_allow_html=True)
        st.image(defender['sprites']['front_default'], width=120)
        def_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
        st.write(f"**Defensive Reduction:** -{def_red}")

# --- MOVE DISPLAY LOGIC ---
if attacker and defender:
    st.divider()
    is_team = st.session_state.get('is_team_selection', False)
    
    def handle_roll(m_name, m_data):
        d20 = random.randint(1, 20)
        p_bon = get_move_power_bonus(m_data.get('power', 0))
        a_bon = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
        t_mod = get_type_modifier(m_data['type']['name'], [t['type']['name'] for t in defender['types']])
        d_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
        
        if d20 >= 8:
            dmg = 0 if t_mod == -999 else max(0, a_bon + p_bon + t_mod + (5 if d20 == 20 else 0) - d_red)
            st.session_state['last_log'] = f"🎲 **{d20}** (Hit!) | 💥 **{dmg}** Damage {'⭐ NAT 20!' if d20 == 20 else ''}"
        else:
            st.session_state['last_log'] = f"🎲 **{d20}** (Miss!)"
        st.rerun()

    if is_team:
        st.subheader("🤺 Team Moveset")
        idx = st.session_state.get('active_team_idx', 0)
        team_moves = st.session_state.get('selected_moves', {}).get(idx, [])
        m_cols = st.columns(4)
        for i, m_name in enumerate(team_moves):
            m_info = get_move_info(m_name)
            if m_info:
                p_bon = get_move_power_bonus(m_info.get('power', 0))
                a_bon = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
                t_mod = get_type_modifier(m_info['type']['name'], [t['type']['name'] for t in defender['types']])
                d_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
                expected = 0 if t_mod == -999 else max(0, a_bon + p_bon + t_mod - d_red)
                
                with m_cols[i]:
                    st.markdown(f'<div class="move-card"><b style="color:{TYPE_COLORS.get(m_info["type"]["name"],"#444")};">{m_name.upper()}</b><br>Dmg: {expected}</div>', unsafe_allow_html=True)
                    if st.button("Roll", key=f"roll_team_{i}", use_container_width=True):
                        handle_roll(m_name, m_info)
    else:
        st.subheader("🔍 All Learnable Moves")
        all_learnable = get_all_learnable_moves(attacker['name'])
        selected_m = st.selectbox("Search and Pick a Move", options=[""] + all_learnable)
        if selected_m:
            m_info = get_move_info(selected_m)
            if m_info:
                p_bon = get_move_power_bonus(m_info.get('power', 0))
                a_bon = max(attacker['stats'][1]['base_stat'], attacker['stats'][3]['base_stat']) // 20
                t_mod = get_type_modifier(m_info['type']['name'], [t['type']['name'] for t in defender['types']])
                d_red = max(defender['stats'][2]['base_stat'], defender
