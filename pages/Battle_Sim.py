import streamlit as st
import requests
import random

# 1. Page Config
st.set_page_config(page_title="Battle Simulator", layout="wide")

# 2. Initialization & Safety
if 'team' not in st.session_state:
    st.session_state['team'] = []
if 'selected_moves' not in st.session_state:
    st.session_state['selected_moves'] = {}

# 3. Styling
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .battle-log {
            background-color: #0e1117;
            color: #00ff00;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', Courier, monospace;
            border: 1px solid #333;
            line-height: 1.6;
        }
        .dice-roll { color: #f39c12; font-weight: bold; }
        .team-slot {
            text-align: center;
            padding: 10px;
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            transition: 0.3s;
            cursor: pointer;
        }
        .team-slot:hover {
            background: rgba(255,255,255,0.15);
            border: 1px solid #978fdb;
        }
    </style>
""", unsafe_allow_html=True)

# 4. Helper Functions
def get_mod(stat_value):
    return (stat_value - 100) // 10

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
def get_move_stats(move_name):
    url = f"https://pokeapi.co/api/v2/move/{move_name.lower().replace(' ', '-')}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

# --- SIDEBAR ---
st.sidebar.title("🎮 PokéDND Menu")
if st.sidebar.button("🏠 Home Page", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button(f"➡️ Team Builder ({len(st.session_state['team'])}/6)", use_container_width=True): st.switch_page("pages/Team_Builder.py")
if st.sidebar.button("⚔️ Battle Simulator", use_container_width=True): st.switch_page("pages/Battle_Sim.py")

# --- TEAM QUICK SELECT RIBBON ---
st.title("⚔️ D&D Battle Simulator")

if st.session_state['team']:
    st.write("### 👥 Quick Select from Team")
    ribbon_cols = st.columns(6)
    for i, p_member in enumerate(st.session_state['team']):
        with ribbon_cols[i]:
            # Use the shiny state from Team Builder if it exists
            is_shiny = st.session_state.get('shiny_states', {}).get(i, False)
            sprite_key = 'front_shiny' if is_shiny else 'front_default'
            
            st.image(p_member['sprites'][sprite_key], width=80)
            if st.button(f"Select {p_member['name'].capitalize()}", key=f"quick_{i}", use_container_width=True):
                # When clicked, update the selectbox for Attacker (Left)
                st.session_state['attacker_search'] = p_member['name']
                st.rerun()

st.divider()

# --- MAIN INTERFACE ---
all_names = get_all_pokemon_names()

col1, col2 = st.columns(2)

# LEFT SIDE: ATTACKER
with col1:
    st.subheader("🛡️ Attacker (Left)")
    
    # Use session state to allow the Ribbon to change this value
    if 'attacker_search' not in st.session_state:
        st.session_state['attacker_search'] = ""

    attacker_name = st.selectbox(
        "Search or Select Attacker:",
        options=[""] + all_names,
        index=all_names.index(st.session_state['attacker_search']) + 1 if st.session_state['attacker_search'] in all_names else 0,
        key="atk_search_box"
    )
    
    attacker = get_pokemon_data(attacker_name) if attacker_name else None
    
    if attacker:
        st.image(attacker['sprites']['front_default'], width=150)
        # Get moves: If it's a team member, show their 4 saved moves. 
        # Otherwise, show all possible moves for that Pokémon.
        team_idx = next((i for i, p in enumerate(st.session_state['team']) if p['name'] == attacker['name']), None)
        
        if team_idx is not None:
            moves_to_show = st.session_state.get('selected_moves', {}).get(team_idx, [])
            st.info(f"Using {attacker['name'].capitalize()}'s Team Loadout")
        else:
            moves_to_show = sorted([m['move']['name'].replace("-", " ").title() for m in attacker['moves']])
            st.caption("Custom Pokémon: All moves available")

        selected_move = st.selectbox("Choose Move:", options=[""] + moves_to_show)

# RIGHT SIDE: DEFENDER
with col2:
    st.subheader("🎯 Target (Right)")
    defender_name = st.selectbox("Search or Select Defender:", options=[""] + all_names, key="def_search_box")
    defender = get_pokemon_data(defender_name) if defender_name else None
    
    if defender:
        st.image(defender['sprites']['front_default'], width=150)
        st.write(f"**AC:** {10 + get_mod(defender['stats'][2]['base_stat'])} (Defense)")
        st.write(f"**Special AC:** {10 + get_mod(defender['stats'][4]['base_stat'])} (Sp. Def)")

st.divider()

# --- COMBAT LOGIC ---
if st.button("🎲 ROLL ATTACK", type="primary", use_container_width=True):
    if not attacker or not defender or not selected_move:
        st.error("Please select an Attacker, a Defender, and a Move first!")
    else:
        move_data = get_move_stats(selected_move)
        if move_data:
            # Stats for calculation
            is_special = move_data.get('damage_class', {}).get('name') == 'special'
            atk_val = attacker['stats'][3]['base_stat'] if is_special else attacker['stats'][1]['base_stat']
            def_val = defender['stats'][4]['base_stat'] if is_special else defender['stats'][2]['base_stat']
            
            atk_mod = get_mod(atk_val)
            def_ac = 10 + get_mod(def_val)
            
            d20 = random.randint(1, 20)
            total_hit = d20 + atk_mod
            
            log = f"**{attacker['name'].capitalize()}** uses **{selected_move.upper()}**!<br>"
            log += f"Roll: <span class='dice-roll'>{d20}</span> + {atk_mod} (Mod) = **{total_hit}** vs **{def_ac} AC**<br>"
            
            if total_hit >= def_ac or d20 == 20:
                power = move_data.get('power', 60) or 60
                num_dice = max(1, power // 20)
                rolls = [random.randint(1, 8) for _ in range(num_dice)]
                total_dmg = sum(rolls) + atk_mod
                
                if d20 == 20:
                    total_dmg *= 2
                    log += "⭐ **CRITICAL HIT!**<br>"
                
                log += f"💥 **HIT!** Damage ({num_dice}d8 + {atk_mod}): {rolls} = <span style='color: #ff4b4b; font-weight:bold;'>{total_dmg} Damage</span>"
                st.balloons()
            else:
                log += "💨 **MISS!** The attack was deflected."
            
            st.markdown(f'<div class="battle-log">{log}</div>', unsafe_allow_html=True)
