import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# --- 2. PERMANENT STATE KEYS ---
if 'atk_tmp' not in st.session_state: st.session_state['atk_tmp'] = []
if 'def_moves_list' not in st.session_state: st.session_state['def_moves_list'] = []
if 'last_log' not in st.session_state: st.session_state['last_log'] = ""
if 'last_atk_name' not in st.session_state: st.session_state['last_atk_name'] = ""
if 'last_def_name' not in st.session_state: st.session_state['last_def_name'] = ""

# --- 3. CALLBACKS ---
def on_atk_move_change():
    move = st.session_state.add_atk_m
    if move and move not in st.session_state['atk_tmp'] and len(st.session_state['atk_tmp']) < 4:
        st.session_state['atk_tmp'].append(move)
    st.session_state.add_atk_m = ""

def on_def_move_change():
    move = st.session_state.add_def_m
    if move and move not in st.session_state['def_moves_list'] and len(st.session_state['def_moves_list']) < 4:
        st.session_state['def_moves_list'].append(move)
    st.session_state.add_def_m = ""

# --- 4. STYLING ---
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
        .battle-log { background-color: #0e1117; color: #00ff00; padding: 15px; border-radius: 8px; border: 1px solid #333; font-family: monospace; }
        .turn-order-banner { background: #1e1e1e; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #444; font-weight: bold; margin-bottom: 20px;}
        .type-badge { color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; margin-left: 5px; }
        .move-card { border: 1px solid #444; border-radius: 8px; padding: 10px; text-align: center; background: rgba(255,255,255,0.03); min-height: 155px; margin-bottom: 10px; }
        .total-dmg { font-size: 16px; color: #978fdb; font-weight: bold; }
        .crit-toggle { margin-top: -15px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPERS ---
@st.cache_data(ttl=86400)
def get_poke_data(name):
    if not name: return None
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
        return res.json() if res.status_code == 200 else None
    except: return None

@st.cache_data(ttl=86400)
def get_move_info(move_name):
    if not move_name: return None
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower().replace(' ', '-')}")
        return res.json() if res.status_code == 200 else None
    except: return None

def get_move_power_bonus(power):
    if not power: return 0
    if 10 <= power <= 40: return 1
    elif 41 <= power <= 60: return 2
    elif 61 <= power <= 75: return 3
    elif 76 <= power <= 90: return 4
    elif 91 <= power <= 110: return 5
    elif 111 <= power <= 130: return 6
    return 7

@st.cache_data(ttl=86400)
def get_type_mod(move_type, defender_types):
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/type/{move_type.lower()}").json()
        rel = res['damage_relations']
        mod = 0
        for dt in defender_types:
            if any(t['name'] == dt for t in rel['double_damage_to']): mod += 2
            if any(t['name'] == dt for t in rel['half_damage_to']): mod -= 2
            if any(t['name'] == dt for t in rel['no_damage_to']): return -999
        return mod
    except: return 0

# --- 6. SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button("➡️ Team Builder", use_container_width=True): st.switch_page("pages/Team_Builder.py")

# --- 7. TEAM RIBBON (FIXED IMAGES) ---
st.title("⚔️ Poke Camp Battle Sim")
if st.session_state.get('team'):
    st.write("### 👥 Your Team")
    ribbon = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        with ribbon[i]:
            # Fetch fresh sprite data to ensure visibility
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p['id']}.png"
            st.image(img_url, width=80)
            if st.button(p['name'].capitalize(), key=f"rib_{i}", use_container_width=True):
                st.session_state['atk_sb'] = p['name']
                st.rerun()

st.divider()

try:
    all_p = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]
except:
    all_p = []

# --- 8. COMBATANT SELECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🛡️ Attacker")
    atk_name = st.selectbox("Search Attacker", [""] + all_p, key="atk_sb")
    
    if atk_name != st.session_state['last_atk_name']:
        st.session_state['atk_tmp'] = []
        st.session_state['last_atk_name'] = atk_name
    
    atk_data = get_poke_data(atk_name)
    if atk_data:
        st.image(atk_data['sprites']['front_default'], width=100)
        a_red = max(atk_data['stats'][2]['base_stat'], atk_data['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {atk_data['stats'][0]['base_stat']//10} | **Reduct:** -{a_red}")
        
        team_idx = next((i for i, p in enumerate(st.session_state.get('team', [])) if p['name'] == atk_name), None)
        if team_idx is not None:
            atk_moves = st.session_state['selected_moves'].get(team_idx, [])
            st.info("📍 Team Moveset Active")
        else:
            learn_a = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in atk_data['moves']])))
            st.selectbox("Add Move", [""] + learn_a, key="add_atk_m", on_change=on_atk_move_change)
            atk_moves = st.session_state['atk_tmp']
            
        # Attacker Controls
        c_a1, c_a2 = st.columns(2)
        with c_a1: atk_crit = st.checkbox("🎯 Force Crit", key="atk_crit_toggle")
        with c_a2: 
            if st.button("Clear Moves", key="cl_atk"): 
                st.session_state['atk_tmp'] = []
                st.rerun()

with col2:
    st.subheader("🎯 Target")
    def_name = st.selectbox("Search Target", [""] + all_p, key="def_sb")
    
    if def_name != st.session_state['last_def_name']:
        st.session_state['def_moves_list'] = []
        st.session_state['last_def_name'] = def_name
        
    def_data = get_poke_data(def_name)
    if def_data:
        st.image(def_data['sprites']['front_default'], width=100)
        d_red = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {def_data['stats'][0]['base_stat']//10} | **Reduct:** -{d_red}")
        
        def_team_idx = next((i for i, p in enumerate(st.session_state.get('team', [])) if p['name'] == def_name), None)
        if def_team_idx is not None:
            def_moves = st.session_state['selected_moves'].get(def_team_idx, [])
            st.info("📍 Team Moveset Active")
        else:
            learn_d = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in def_data['moves']])))
            st.selectbox("Add Move", [""] + learn_d, key="add_def_m", on_change=on_def_move_change)
            def_moves = st.session_state['def_moves_list']
            
        # Target Controls
        c_d1, c_d2 = st.columns(2)
        with c_d1: def_crit = st.checkbox("🎯 Force Crit", key="def_crit_toggle")
        with c_d2:
            if st.button("Clear Moves", key="cl_def"): 
                st.session_state['def_moves_list'] = []
                st.rerun()

# --- 9. THE BATTLE GRIDS ---
st.divider()
if atk_data and def_data:
    aspd, dspd = atk_data['stats'][5]['base_stat']//15, def_data['stats'][5]['base_stat']//15
    f_p = atk_data['name'] if aspd >= dspd else def_data['name']
    st.markdown(f'<div class="turn-order-banner">🏃 {f_p.capitalize()} acts FIRST</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    def render_card(m_name, p_atk, p_def, key_pre, i, force_nat_20):
        mi = get_move_info(m_name)
        if mi:
            pb, ab = get_move_power_bonus(mi.get('power', 0)), max(p_atk['stats'][1]['base_stat'], p_atk['stats'][3]['base_stat']) // 20
            tm = get_type_mod(mi['type']['name'], [t['type']['name'] for t in p_def['types']])
            dr = max(p_def['stats'][2]['base_stat'], p_def['stats'][4]['base_stat']) // 40
            c_b = 5 if force_nat_20 else 0
            exp = 0 if tm == -999 else max(0, ab + pb + tm + c_b - dr)
            
            st.markdown(f'<div class="move-card"><b style="color:{TYPE_COLORS.get(mi["type"]["name"],"#444")};">{m_name.upper()}</b><br><small>Stat:+{ab} Pwr:+{pb} Type:{tm}</small><br><small>Crit:{c_b} Reduct:-{dr}</small><br><div class="total-dmg">Dmg: {exp}</div></div>', unsafe_allow_html=True)
            if st.button(f"Roll {m_name}", key=f"r_{key_pre}_{i}", use_container_width=True):
                roll = 20 if force_nat_20 else random.randint(1, 20)
                final = 0 if tm == -999 else max(0, ab + pb + tm + (5 if roll == 20 else 0) - dr)
                st.session_state['last_log'] = f"🎲 **{roll}** | **{p_atk['name'].capitalize()}** deals **{final}** damage with **{m_name}**!"
                st.rerun()

    with g1:
        st.write(f"**{atk_data['name'].capitalize()} Moves**")
        cols = st.columns(2)
        for i, m in enumerate(atk_moves):
            with cols[i%2]: render_card(m, atk_data, def_data, "atk", i, atk_crit)

    with g2:
        st.write(f"**{def_data['name'].capitalize()} Moves**")
        cols_d = st.columns(2)
        for i, m in enumerate(def_moves):
            with cols_d[i%2]: render_card(m, def_data, atk_data, "def", i, def_crit)

if st.session_state['last_log']:
    st.markdown(f'<div class="battle-log">{st.session_state["last_log"]}</div>', unsafe_allow_html=True)
