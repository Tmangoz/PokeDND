import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# --- 2. GLOBAL STATE INITIALIZATION ---
if 'attacker_search' not in st.session_state: st.session_state['attacker_search'] = ""
if 'def_s' not in st.session_state: st.session_state['def_s'] = ""
if 'atk_tmp' not in st.session_state: st.session_state['atk_tmp'] = []
if 'def_moves_list' not in st.session_state: st.session_state['def_moves_list'] = []
if 'team' not in st.session_state: st.session_state['team'] = []

# --- 3. CALLBACKS (Preventing State Loss) ---
def handle_atk_move():
    move = st.session_state.atk_move_selector
    if move and move not in st.session_state['atk_tmp'] and len(st.session_state['atk_tmp']) < 4:
        st.session_state['atk_tmp'].append(move)

def handle_def_move():
    move = st.session_state.def_move_selector
    if move and move not in st.session_state['def_moves_list'] and len(st.session_state['def_moves_list']) < 4:
        st.session_state['def_moves_list'].append(move)

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

# --- 6. SIDEBAR & NAVIGATION ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button("➡️ Team Builder", use_container_width=True): st.switch_page("pages/Team_Builder.py")
st.sidebar.divider()
force_crit = st.sidebar.checkbox("🎯 Force Nat 20")

# --- 7. TEAM RIBBON ---
st.title("⚔️ Poke Camp Battle Sim")
if st.session_state['team']:
    st.write("### 👥 Your Team")
    ribbon_cols = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        with ribbon_cols[i]:
            # Always fallback to default front sprite if session data is shaky
            sprite = p['sprites'].get('front_default')
            st.image(sprite, width=70)
            if st.button(p['name'].capitalize(), key=f"sel_{i}", use_container_width=True):
                st.session_state['attacker_search'] = p['name']
                st.rerun()

st.divider()

# --- 8. COMBATANT DATA FETCHING ---
all_names = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

c1, c2 = st.columns(2)

with c1:
    st.subheader("🛡️ Attacker")
    atk_name = st.selectbox("Select Attacker", [""] + all_names, 
                            index=all_names.index(st.session_state['attacker_search'])+1 if st.session_state['attacker_search'] in all_names else 0, 
                            key="atk_box")
    if atk_name != st.session_state['attacker_search']:
        st.session_state['attacker_search'] = atk_name
        st.session_state['atk_tmp'] = []
        st.rerun()

    attacker = get_poke_data(atk_name)
    if attacker:
        st.image(attacker['sprites']['front_default'], width=100)
        a_red = max(attacker['stats'][2]['base_stat'], attacker['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {attacker['stats'][0]['base_stat']//10} | **Reduct:** -{a_red}")
        
        team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == atk_name), None)
        if team_idx is not None:
            atk_moves = st.session_state['selected_moves'].get(team_idx, [])
        else:
            learnable_a = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in attacker['moves']])))
            st.selectbox("Add Move", [""] + learnable_a, key="atk_move_selector", on_change=handle_atk_move)
            atk_moves = st.session_state['atk_tmp']
            if st.button("Clear Attacker Moves"): st.session_state['atk_tmp'] = []; st.rerun()

with c2:
    st.subheader("🎯 Target")
    def_name = st.selectbox("Select Target", [""] + all_names, 
                            index=all_names.index(st.session_state['def_s'])+1 if st.session_state['def_s'] in all_names else 0, 
                            key="def_box")
    if def_name != st.session_state['def_s']:
        st.session_state['def_s'] = def_name
        st.session_state['def_moves_list'] = []
        st.rerun()

    defender = get_poke_data(def_name)
    if defender:
        st.image(defender['sprites']['front_default'], width=100)
        d_red = max(defender['stats'][2]['base_stat'], defender['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {defender['stats'][0]['base_stat']//10} | **Reduct:** -{d_red}")
        
        def_team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == def_name), None)
        if def_team_idx is not None:
            def_moves = st.session_state['selected_moves'].get(def_team_idx, [])
        else:
            learnable_d = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in defender['moves']])))
            st.selectbox("Add Move", [""] + learnable_d, key="def_move_selector", on_change=handle_def_move)
            def_moves = st.session_state['def_moves_list']
            if st.button("Clear Target Moves"): st.session_state['def_moves_list'] = []; st.rerun()

# --- 9. BATTLE ENGINE ---
st.divider()
if attacker and defender:
    # Turn Order Banner
    aspd, dspd = attacker['stats'][5]['base_stat']//15, defender['stats'][5]['base_stat']//15
    first = attacker['name'] if aspd >= dspd else defender['name']
    st.markdown(f'<div class="turn-order-banner">🏃 {first.capitalize()} acts FIRST (Speed: {max(aspd, dspd)})</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    def render_move_card(m_name, p_atk, p_def, i, key_prefix):
        mi = get_move_info(m_name)
        if mi:
            pb = get_move_power_bonus(mi.get('power', 0))
            ab = max(p_atk['stats'][1]['base_stat'], p_atk['stats'][3]['base_stat']) // 20
            tm = get_type_mod(mi['type']['name'], [t['type']['name'] for t in p_def['types']])
            dr = max(p_def['stats'][2]['base_stat'], p_def['stats'][4]['base_stat']) // 40
            c_bon = 5 if force_crit else 0
            exp = 0 if tm == -999 else max(0, ab + pb + tm + c_bon - dr)
            
            st.markdown(f"""
            <div class="move-card">
                <b>{m_name.upper()}</b><br>
                <div style="font-size:11px; color:#aaa;">Stat:+{ab} | Move:+{pb} | Type:{tm}<br>Crit:+{c_bon} | Target Reduct:-{dr}</div>
                <div class="total-dmg">Dmg: {exp}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Roll Attack", key=f"roll_{key_prefix}_{i}", use_container_width=True):
                roll = 20 if force_crit else random.randint(1, 20)
                final = 0 if tm == -999 else max(0, ab + pb + tm + (5 if roll == 20 else 0) - dr)
                st.session_state['last_log'] = f"🎲 **{roll}** | **{p_atk['name'].capitalize()}** deals **{final}** damage!"
                st.rerun()

    with g1:
        st.write(f"**{attacker['name'].capitalize()} Moves**")
        m_cols = st.columns(2)
        for i, m in enumerate(atk_moves):
            with m_cols[i % 2]: render_move_card(m, attacker, defender, i, "atk")

    with g2:
        st.write(f"**{defender['name'].capitalize()} Moves**")
        m_cols_d = st.columns(2)
        for i, m in enumerate(def_moves):
            with m_cols_d[i % 2]: render_move_card(m, defender, attacker, i, "def")

if 'last_log' in st.session_state:
    st.markdown(f'<div class="battle-log">{st.session_state["last_log"]}</div>', unsafe_allow_html=True)
