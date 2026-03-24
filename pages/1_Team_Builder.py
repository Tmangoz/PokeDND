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

# Initialize move storage in session state if not exists
if 'selected_moves' not in st.session_state:
    st.session_state['selected_moves'] = {} # Dictionary mapping pokemon index to list of moves

st.title("🏆 My Pokémon Team")

if 'team' not in st.session_state or len(st.session_state['team']) == 0:
    st.info("Your team is empty! Go back to the Explorer to add some Pokémon.")
else:
    for i, p_data in enumerate(st.session_state['team']):
        # Ensure every pokemon has a slot in the move dictionary
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
                # 1. Get all possible moves (Level-up + TMs)
                all_moves = []
                for m in p_data['moves']:
                    methods = [d['move_learn_method']['name'] for d in m['version_group_details']]
                    if 'level-up' in methods or 'machine' in methods:
                        all_moves.append(m['move']['name'].replace("-", " ").title())
                all_moves = sorted(list(set(all_moves)))

                # 2. Search and Add Section
                m_search_col, m_btn_col = st.columns([3, 1])
                with m_search_col:
                    move_to_add = st.selectbox(f"Search Moves", options=[""] + all_moves, key=f"search_{i}", label_visibility="collapsed")
                with m_btn_col:
                    if st.button("➕ Add", key=f"add_btn_{i}"):
                        if move_to_add and move_to_add != "":
                            if len(st.session_state['selected_moves'][i]) < 4:
                                if move_to_add not in st.session_state['selected_moves'][i]:
                                    st.session_state['selected_moves'][i].append(move_to_add)
                                    st.rerun()
                            else:
                                st.warning("Max 4 moves!")

                # 3. Render Moves with Internal Remove Buttons
                st.write("**Active Moves:**")
                move_cols = st.columns(2) # Show moves in 2 mini-columns per pokemon
                
                for idx, m_display_name in enumerate(st.session_state['selected_moves'][i]):
                    api_name = m_display_name.lower().replace(" ", "-")
                    m_url = next(m['move']['url'] for m in p_data['moves'] if m['move']['name'] == api_name)
                    m_info = get_move_details(m_url)
                    
                    if m_info:
                        m_type = m_info['type']['name']
                        m_power = m_info.get('power') if m_info.get('power') else "—"
                        bg = TYPE_COLORS.get(m_type, "#777")
                        
                        # Use a sub-container for the move "Card"
                        with move_cols[idx % 2]:
                            st.markdown(f'''
                                <div style="background-color:{bg}; color:white; padding:10px; border-radius:10px; margin-bottom:5px; text-align:center; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
                                    <div style="font-weight:bold; font-size:13px;">{m_display_name.upper()}</div>
                                    <div style="font-size:10px; opacity:0.9;">PWR: {m_power} | {m_type.upper()}</div>
                                </div>
                            ''', unsafe_allow_html=True)
                            
                            # The Remove Button right under the badge
                            if st.button(f"Remove {m_display_name}", key=f"del_move_{i}_{idx}", use_container_width=True):
                                st.session_state['selected_moves'][i].pop(idx)
                                st.rerun()

    st.divider()
    if st.button("Clear Full Team"):
        st.session_state['team'] = []
        st.session_state['selected_moves'] = {}
        st.rerun()
