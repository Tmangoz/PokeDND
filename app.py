import streamlit as st
import requests

# 1. Page Config
st.set_page_config(page_title="PokéDND Explorer", layout="wide")

# 2. Hide Default Sidebar Navigation
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .stSelectbox div[data-baseweb="select"] {cursor: pointer;}
    </style>
""", unsafe_allow_html=True)

# 3. API Fetching Functions
@st.cache_data(ttl=86400)
def get_all_pokemon_names():
    """Fetches all 1000+ Pokemon names for the search dropdown."""
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        response = requests.get(url).json()
        return [p['name'] for p in response['results']]
    except:
        return []

@st.cache_data(ttl=86400)
def get_pokemon_data(name):
    """Fetches full data for a specific Pokemon."""
    if not name: return None
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# 4. Session State Initialization
if 'team' not in st.session_state:
    st.session_state['team'] = []

# --- SIDEBAR MENU ---
st.sidebar.title("🎮 PokéDND Menu")

if st.sidebar.button("🏠 Home Page", use_container_width=True):
    st.switch_page("app.py")

team_count = len(st.session_state['team'])
if st.sidebar.button(f"➡️ Team Builder ({team_count}/6)", use_container_width=True):
    st.switch_page("pages/Team_Builder.py")

st.sidebar.divider()
st.sidebar.caption("Search for a Pokémon to add it to your D&D party. Max 6 members.")

# --- MAIN INTERFACE ---
st.title("🔍 Pokémon Explorer")
st.write("Start typing a name to see suggestions!")

# Get full list for auto-complete
all_names = get_all_pokemon_names()

# Auto-complete Search Bar
search_query = st.selectbox(
    "Search for a Pokémon:",
    options=[""] + all_names,
    format_func=lambda x: x.capitalize() if x else "Type to search...",
    index=0,
    help="Select a Pokémon from the list to view stats."
)

if search_query:
    with st.spinner(f"Loading {search_query.capitalize()}..."):
        p_data = get_pokemon_data(search_query)
        
    if p_data:
        st.divider()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display Sprite
            st.image(p_data['sprites']['front_default'], width=250)
            
            # Add to Team Button
            if st.button(f"➕ Add {p_data['name'].capitalize()} to Team", use_container_width=True):
                if len(st.session_state['team']) < 6:
                    # Check for duplicates
                    if any(p['name'] == p_data['name'] for p in st.session_state['team']):
                        st.warning(f"{p_data['name'].capitalize()} is already in your team!")
                    else:
                        st.session_state['team'].append(p_data)
                        st.success(f"Added {p_data['name'].capitalize()} to your team!")
                        st.rerun()
                else:
                    st.error("Your team is full! Remove someone in the Team Builder first.")

        with col2:
            st.header(p_data['name'].capitalize())
            
            # Display Types as Badges
            type_html = ""
            for t in p_data['types']:
                t_name = t['type']['name']
                type_html += f'<span style="background-color:#777; color:white; padding:5px 10px; border-radius:15px; margin-right:5px; font-weight:bold;">{t_name.upper()}</span>'
            st.markdown(type_html, unsafe_allow_html=True)
            
            st.write("") # Spacer
            
            # Display Stats
            st.subheader("Base Stats")
            STAT_LABELS = {
                "hp": "HP", "attack": "ATK", "defense": "DEF", 
                "special-attack": "SpA", "special-defense": "SpD", "speed": "Spd"
            }
            
            for s in p_data['stats']:
                label = STAT_LABELS.get(s['stat']['name'], s['stat']['name'].upper())
                val = s['base_stat']
                # Visual progress bar for stats
                st.write(f"**{label}**: {val}")
                st.progress(min(val / 150, 1.0))

    else:
        st.error("Could not find data for that Pokémon. Please try again.")

else:
    # Instructions when nothing is searched
    st.info("Select a Pokémon above to see its stats and add it to your party.")
    
    # Optional: Display some "Trending" or Random Pokemon
    st.write("### Need inspiration?")
    suggest_cols = st.columns(3)
    starters = ["bulbasaur", "charmander", "squirtle"]
    for i, name in enumerate(starters):
        with suggest_cols[i]:
            if st.button(f"View {name.capitalize()}", use_container_width=True):
                # This doesn't trigger the selectbox directly but gives a hint
                st.info(f"Search for '{name}' in the bar above!")

