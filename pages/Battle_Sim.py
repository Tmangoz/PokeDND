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

# --- 3. CALLBACK FUNCTIONS (The Fix) ---
def add_atk_move():
    move = st.session_state.atk_move_selector
    if move and move not in st.session_state['atk_tmp'] and len(st.session_state['atk_tmp']) < 4:
        st.session_state['atk_tmp'].append(move)

def add_def_move():
    move = st.session_state.def_move_selector
    if move and move not in st.session_state['def_moves_list'] and len(st.session_state['def_moves_list']) < 4:
        st.session_state['def_moves_list'].append(move)

def clear_atk(): st.session_state['atk_tmp'] = []
def clear_def(): st.session_state['def_moves_list'] = []

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
        .move-card { border: 1px solid #444; border-radius: 8px; padding: 10px; text-align: center; background: rgba(255,255,255,0.03); min-height: 150px; }
        .total-dmg { font-size: 16px; color: #978fdb; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 5. HELPERS ---
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
def get_poke_data(name):
    if not name: return None
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")
    return res.json() if res.status_code == 200 else None

@st.cache_data(ttl=86400)
def get_move_info(move_name):
    if not move_name: return None
    res = requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower().replace(' ', '-')}")
    return res.json() if res.status_code == 200 else None

@st.cache_data(ttl=86400)
def get_type_mod(move_type, defender_types):
    res = requests.get(f"https://pokeapi.co/api/v2/type/{move_type.lower()}").json()
    rel = res['damage_relations']
    mod = 0
    for dt in defender_types:
        if any(t['name'] == dt for t in rel['double_damage_to']): mod += 2
        if any(t['name'] == dt for t in rel['half_damage_to']): mod -= 2
        if any(t['name'] == dt for t in rel['no_damage_to']): return -999
    return mod

# --- 6. SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home"): st.switch_page("app.py")
if st.sidebar.button("➡️ Team Builder"): st.switch_page("pages/Team_Builder.py")
st.sidebar.divider()
force_crit = st.sidebar.checkbox("🎯 Force Nat 20")

# --- 7. MAIN UI ---
st.title("⚔️ Poke Camp Battle Sim")

# Team Ribbon
if st.session_state['team']:
    cols = st.columns(6)
    for i, p in enumerate(st.session_state['team']):
        if cols[i].button(p['name'].capitalize(), key=f"ribbon_{i}"):
            st.session_state['attacker_search'] = p['name']
            st.rerun()

all_names = [p['name'] for p in requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000").json()['results']]

c1, c2 = st.columns(2)

with c1:
    st.subheader("🛡️ Attacker")
    atk_name = st.selectbox("Search Attacker", [""] + all_names, index=all_names.index(st.session_state['attacker_search'])+1 if st.session_state['attacker_search'] in all_names else 0, key="atk_sb")
    if atk_name != st.session_state['attacker_search']:
        st.session_state['attacker_search'] = atk_name
        st.session_state['atk_tmp'] = []
        st.rerun()
    
    atk_data = get_poke_data(atk_name)
    if atk_data:
        st.image(atk_data['sprites']['front_default'], width=100)
        a_red = max(atk_data['stats'][2]['base_stat'], atk_data['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {atk_data['stats'][0]['base_stat']//10} | **Reduct:** -{a_red}")
        
        # Move Logic
        team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == atk_name), None)
        if team_idx is not None:
            a_moves = st.session_state.get('selected_moves', {}).get(team_idx, [])
        else:
            learnable = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in atk_data['moves']])))
            st.selectbox("Add Move", [""] + learnable, key="atk_move_selector", on_change=add_atk_move)
            a_moves = st.session_state['atk_tmp']
            st.button("Clear Moves", key="cl_atk", on_click=clear_atk)

with c2:
    st.subheader("🎯 Target")
    def_name = st.selectbox("Search Target", [""] + all_names, index=all_names.index(st.session_state['def_s'])+1 if st.session_state['def_s'] in all_names else 0, key="def_sb")
    if def_name != st.session_state['def_s']:
        st.session_state['def_s'] = def_name
        st.session_state['def_moves_list'] = []
        st.rerun()
    
    def_data = get_poke_data(def_name)
    if def_data:
        st.image(def_data['sprites']['front_default'], width=100)
        d_red = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
        st.write(f"**HP:** {def_data['stats'][0]['base_stat']//10} | **Reduct:** -{d_red}")
        
        # Move Logic
        def_team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == def_name), None)
        if def_team_idx is not None:
            d_moves = st.session_state.get('selected_moves', {}).get(def_team_idx, [])
        else:
            learnable_d = sorted(list(set([m['move']['name'].replace("-"," ").title() for m in def_data['moves']])))
            st.selectbox("Add Move", [""] + learnable_d, key="def_move_selector", on_change=add_def_move)
            d_moves = st.session_state['def_moves_list']
            st.button("Clear Moves", key="cl_def", on_click=clear_def)

# --- 8. THE BATTLE GRID ---
st.divider()
if atk_data and def_data:
    # Speed Check
    aspd, dspd = atk_data['stats'][5]['base_stat']//15, def_data['stats'][5]['base_stat']//15
    first = atk_data['name'] if aspd >= dspd else def_data['name']
    st.markdown(f'<div class="turn-order-banner">🏃 {first.capitalize()} acts FIRST (Speed: {max(aspd, dspd)})</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    
    with g1:
        st.write(f"**{atk_data['name'].capitalize()} Moves**")
        m_g1 = st.columns(2)
        for i, mn in enumerate(a_moves):
            mi = get_move_info(mn)
            if mi:
                pb, ab = get_move_power_bonus(mi.get('power', 0)), max(atk_data['stats'][1]['base_stat'], atk_data['stats'][3]['base_stat']) // 20
                tm = get_type_mod(mi['type']['name'], [t['type']['name'] for t in def_data['types']])
                dr = max(def_data['stats'][2]['base_stat'], def_data['stats'][4]['base_stat']) // 40
                exp = 0 if tm == -999 else max(0, ab + pb + tm + (5 if force_crit else 0) - dr)
                with m_g1[i % 2]:
                    st.markdown(f'<div class="move-card"><b>{mn.upper()}</b><br><small>Stat:+{ab} Pwr:+{pb} Type:{tm}</small><br><small>Crit:{5 if force_crit else 0} Red:-{dr}</small><br><div class="total-dmg">Dmg: {exp}</div></div>', unsafe_allow_html=True)
                    if st.button("Roll", key=f"arol_{i}"):
                        roll = 20 if force_crit else random.randint(1, 20)
                        final = 0 if tm == -999 else max(0, ab + pb + tm + (5 if roll == 20 else 0) - dr)
                        st.session_state['last_log'] = f"🎲 {roll} | {atk_data['name'].capitalize()} dealt {final} damage!"
                        st.rerun()

    with g2:
        st.write(f"**{def_data['name'].capitalize()} Moves**")
        m_g2 = st.columns(2)
        for i, mn in enumerate(d_moves):
            mi = get_move_info(mn)
            if mi:
                pb, ab = get_move_power_bonus(mi.get('power', 0)), max(def_data['stats'][1]['base_stat'], def_data['stats'][3]['base_stat']) // 20
                tm = get_type_mod(mi['type']['name'], [t['type']['name'] for t in atk_data['types']])
                dr = max(atk_data['stats'][2]['base_stat'], atk_data['stats'][4]['base_stat']) // 40
                exp = 0 if tm == -999 else max(0, ab + pb + tm + (5 if force_crit else 0) - dr)
                with m_g2[i % 2]:
                    st.markdown(f'<div class="move-card"><b>{mn.upper()}</b><br><small>Stat:+{ab} Pwr:+{pb} Type:{tm}</small><br><small>Crit:{5 if force_crit else 0} Red:-{dr}</small><br><div class="total-dmg">Dmg: {exp}</div></div>', unsafe_allow_html=True)
                    if st.button("Roll", key=f"drol_{i}"):
                        roll = 20 if force_crit else random.randint(1, 20)
                        final = 0 if tm == -999 else max(0, ab + pb + tm + (5 if roll == 20 else 0) - dr)
                        st.session_state['last_log'] = f"🎲 {roll} | {def_data['name'].capitalize()} dealt {final} damage!"
                        st.rerun()

if 'last_log' in st.session_state:
    st.markdown(f'<div class="battle-log">{st.session_state["last_log"]}</div>', unsafe_allow_html=True)
