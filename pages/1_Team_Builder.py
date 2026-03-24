import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="Team Builder", layout="wide", initial_sidebar_state="expanded")

# 2. Type Colors
TYPE_COLORS = {
    "fire": "#F08030", "water": "#6890F0", "grass": "#78C850", "electric": "#F8D030",
    "ice": "#98D8D8", "fighting": "#C03028", "poison": "#A040A0", "ground": "#E0C068",
    "flying": "#A890F0", "psychic": "#F85888", "bug": "#A8B820", "rock": "#B8A038",
    "ghost": "#705898", "dragon": "#7038F8", "dark": "#705848", "steel": "#B8B8D0",
    "fairy": "#EE99AC", "normal": "#A8A878"
}

@st.cache_data(ttl=86400)
def get_move_details(move_url):
    try:
        return requests.get(move_url).json()
    except: return None

# Initialize session states
if 'team' not in st.session_state:
    st.session_state['team'] = []
if 'selected_moves' not in st.session_state:
    st.session_state['selected_moves'] = {}

# --- CALLBACK FUNCTION FOR AUTO-ADD ---
def add_move_callback(pokemon_index):
    # Get the value from the selectbox using its unique key
    selected_val = st.session_state[f"search_{pokemon_index}"]
    
    if selected_val and selected_val != "":
        current_moves = st.session_state['selected_moves'].get(pokemon_index, [])
        if len(current_moves) < 4:
            if selected_val not in current_moves:
                current_moves.append(selected_val)
                st.session_state['selected_moves'][pokemon_index] = current_moves
        else:
            st.toast(f"Max 4 moves reached for this Pokémon!", icon="⚠️")
        
        # Reset the selectbox to empty after adding
        st.session_state[f"search_{pokemon_index}"] = ""

st.title("🏆 My Pokémon Team")

if not st.session_state['team']:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    for i, p_data in enumerate(st.session_state['team']):
        if i not in st.session_state['selected_moves']:
            st.session_state['selected_moves'][i] = []

        with st.container(border=True):
            main_col1, main_col2 = st.columns([2, 3])
            
            with main_col1:
                st.subheader(f"{p_data['name'].capitalize()}")
                img_col, stat_col = st.columns([1, 1])
                with img_col:
                    st.image(p_data['sprites']['front_default'], width=120)
                    if st.button("🗑️ Remove Pokémon", key=f"rem_pkmn_{i}"):
                        st.session_state['team'].pop(i)
                        st.session_state['selected_moves'].pop(i, None)
                        st.rerun()
                
                with stat_col:
                    for s in p_data['stats']:
                        short_name = s['stat']['name'].replace("special-attack", "Sp.Atk").replace("special-defense", "Sp.Def").upper()
                        st.write(f"**{short_name}**: {s['base_stat']}")

            with main_col2:
                # 1. Prepare Move List
                all_moves = []
                for m in p_data['moves']:
                    methods = [d['move_learn_method']['name'] for d in m['version_group_details']]
                    if 'level-up' in methods or 'machine' in methods:
                        all_moves.append(m['move']['name'].replace("-", " ").title())
                all_moves = sorted(list(set(all_moves)))

                # 2. Auto-Add Selectbox
                st.write("🔍 **Add a Move:**")
                st.selectbox(
                    "Search and select to add automatically",
                    options=[""] + all_moves,
                    key=f"search_{i}",
                    on_change=add_move_callback,
                    args=(i,),
                    label_visibility="collapsed"
                )

                # 3. Display Moves in a Grid
                st.write("**Active Moves:**")
                m_cols = st.columns(2)
                
                for idx, m_display_name in enumerate(st.session_state['selected_moves'][i]):
                    # Re-fetch data for the badge
                    api_name = m_display_name.lower().replace(" ", "-")
                    try:
                        m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_name)
                        m_info = get_move_details(m_url)
                        
                        if m_info:
                            m_type = m_info['type']['name']
                            m_power = m_info.get('power') if m_info.get('power') else "—"
                            bg = TYPE_COLORS.get(m_type, "#777")
                            
                            with m_cols[idx % 2]:
                                # Styled Badge
                                st.markdown(f'''
                                    <div style="background-color:{bg}; color:white; padding:8px; border-radius:8px; margin-bottom:2px; text-align:center; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                                        <div style="font-weight:bold; font-size:12px;">{m_display_name.upper()}</div>
                                        <div style="font-size:10px; opacity:0.8;">PWR: {m_power} | {m_type.upper()}</div>
                                    </div>
                                ''', unsafe_allow_html=True)
                                
                                # Small red remove button
                                if st.button(f"✖ Remove {m_display_name}", key=f"del_{i}_{idx}", use_container_width=True, type="secondary"):
                                    st.session_state['selected_moves'][i].pop(idx)
                                    st.rerun()
                    except StopIteration:
                        continue # Move not found in data

    st.divider()
    if st.button("Clear Full Team", type="primary"):
        st.session_state['team'] = []
        st.session_state['selected_moves'] = {}
        st.rerun()
