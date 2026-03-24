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
            border: 1px solid #444; border-radius: 8px; padding: 10px;
            text-align: center; background: rgba(255,255,255,0.03);
            margin-bottom: 10px;
        }
        .breakdown-text { font-size: 12px; color: #aaa; line-height: 1.2; }
        .total-dmg { font-size: 16px; color: #978fdb; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. Helpers
def get_move_power_bonus(power):
    if not power: return 0
    if 10 <= power <= 40: return 1
    elif 41 <= power <= 60: return 2
    elif 61 <= power <= 75: return 3
    elif 76 <= power <= 90: return 4
    elif 91 <= power <= 110: return 5
    elif 111 <= power <= 130: return 6
    return 7 if power >= 131 else 0

def render_type_badges(pokemon_data):
    badges = ""
    for t in pokemon_data.get('types', []):
        t_name = t['type']['name']
        c = TYPE_COLORS.get(t_name, "#777")
        badges += f'<span class="type-badge" style="background-color: {c};">{t_name}</span>'
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
    try:
        url_name = move_name.lower().replace(' ', '-')
        return requests.get(f"https://pokeapi.co/api/v2/move/{url_name}").json()
    except: return None

@st.cache_data(ttl=86400)
def get_all_learnable_moves(pokemon_name):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}").json()
        moves = [m['move']['name'].replace("-", " ").title() for m in res['moves']]
        return sorted(list(set(moves)))
    except: return []

# --- SIDEBAR MENU ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder ({len(st.session_state.get('team', []))}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")
st.sidebar.divider()
force_crit = st.sidebar.checkbox("🎯 Force Nat 20 (Crit Hit)")

# --- MAIN INTERFACE ---
st.title("⚔️ Poke Camp Battle Sim")

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

atk_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{st.session_state['attacker_search'].lower()}").json() if st.session_state['attacker_search'] else None
def_name = st.session_state.get('def_s', "")
def_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{def_name.lower()}").json() if def_name else None

if atk_data and def_data:
    a_spd, d_spd = atk_data['stats'][5]['base_stat'] // 15, def_data['stats'][5]['base_stat'] // 15
    first = atk_data['name'].capitalize() if a_spd >= d_spd else def_data['name'].capitalize()
    st.markdown(f'<div class="turn-order-banner">🏃 {first} attacks FIRST (Speed: {max(a_spd, d_spd)} vs {min(a_spd, d_spd)})</div>', unsafe_allow_html=True)

all_p = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛡️ Attacker")
    val = st.selectbox("Search Attacker", options=[""] + all_p, label_visibility="collapsed",
                       index=all_p.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_p else 0)
    if val != st.session_state['attacker_search']:
        st.session_state['attacker_search'] = val
        st.session_state['is_team_selection'] = any(p['name'] == val for p in st.session_state['team'])
        st.rerun()

    if atk_data:
        st.markdown(f"**HP:** {atk_data['stats'][0]['base_stat']//10} | **Speed:** {atk_data['stats'][5]['base_stat']//15} {render_type_badges(atk_data)}", unsafe_allow_html=True)
        st.image(atk_data['sprites']['front_default'], width=120)
        
        # --- MOVE LOGIC (2x2 GRID) ---
        is_team = st.session_state.get('is_team_selection', False)
        moves_list = []
        if is_team:
            idx = st.session_state.get('active_team_idx', 0)
            moves_list = st.session_state.get('selected_moves', {}).get(idx, [])
        else:
            all_learnable = get_all_learnable_moves(atk_data['name'])
            search_m = st.selectbox("Search Move", options=[""] + all_learnable)
            if search_m: moves_list = [search_m]

        if moves_list and def_data:
            st.write("**🤺 Select Move to Roll**")
            m_grid = st.columns(2)
            for i, m_name in enumerate(moves_list):
                m_info = get_move_info(m_name)
                if m_info:
                    p_bon = get_move_power_bonus(m_info.get('power', 0))
                    a_bon = max(atk_data['stats'][1]['base_stat'], atk_data['stats'][3]['base_stat']) // 20
                    d_types = [t['type']['name'] for t in def_data['types']]
                    t_mod = get_type_modifier(m_info['type']['name'], d_types)
                    d_red = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
                    c_bon = 5 if force_crit else 0
                    
                    expected = 0 if t_mod == -999 else max(0, a_bon + p_bon + t_mod + c_bon - d_red)
                    
                    with m_grid[i % 2]:
                        st.markdown(f"""
                        <div class="move-card">
                            <b style="color:{TYPE_COLORS.get(m_info['type']['name'], '#444')};">{m_name.upper()}</b><br>
                            <div class="breakdown-text">Stat: +{a_bon} | Move: +{p_bon}<br>Type: {t_mod if t_mod != -999 else 'Immune'} | Crit: +{c_bon}</div>
                            <div class="breakdown-text">Def Reduction: -{d_red}</div>
                            <div class="total-dmg">Total: {expected}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Roll", key=f"btn_{i}", use_container_width=True):
                            roll = 20 if force_crit else random.randint(1, 20)
                            if roll >= 8:
                                final = 0 if t_mod == -999 else max(0, a_bon + p_bon + t_mod + (5 if roll == 20 else 0) - d_red)
                                st.session_state['last_log'] = f"🎲 **{roll}** (Hit!) | 💥 **{final}** Damage {'⭐ NAT 20!' if roll == 20 else ''}"
                            else: st.session_state['last_log'] = f"🎲 **{roll}** (Miss!)"
                            st.rerun()

with col2:
    st.subheader("🎯 Target")
    d_name_box = st.selectbox("Target Search", options=[""] + all_p, key="def_s", label_visibility="collapsed")
    if def_data:
        st.markdown(f"**HP:** {def_data['stats'][0]['base_stat']//10} | **Speed:** {def_data['stats'][5]['base_stat']//15} {render_type_badges(def_data)}", unsafe_allow_html=True)
        st.image(def_data['sprites']['front_default'], width=120)
        d_val = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat'])
        st.write(f"**Defensive Reduction:** -{d_val // 40}")

if 'last_log' in st.session_state:
    st.markdown(f'<div class="battle-log">{st.session_state["last_log"]}</div>', unsafe_allow_html=True)
