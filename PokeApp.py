import streamlit as st
import requests

# Page Configuration
st.set_page_config(
    page_title="PokéExplorer", 
    layout="wide", 
    page_icon="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"
)

# --- CUSTOM STYLING (Pokémon Vibe & Black Sidebar Text) ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url("https://www.transparenttextures.com/patterns/cubes.png"),
                    linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Sidebar background (Dark Blue) */
    section[data-testid="stSidebar"] {
        background-color: #3761a8 !important;
    }

    /* Force Sidebar Text, Labels, and Headers to BLACK */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: black !important;
        font-weight: bold !important;
    }

    /* Input box text color */
    input {
        color: black !important;
    }

    /* Card/Container styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 2px solid #ffcb05;
    }

    /* Main Titles color */
    h1, h2, h3 {
        color: #3761a8 !important;
        font-family: 'Verdana', sans-serif;
    }

    /* Custom Button Style (Yellow/Blue) */
    .stButton>button {
        background-color: #ffcb05 !important;
        color: #3c5aa6 !important;
        border: 2px solid #3c5aa6 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #3c5aa6 !important;
        color: #ffcb05 !important;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- API FUNCTIONS ---

@st.cache_data
def get_pokemon_locations(pokemon_id):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/encounters"
    r = requests.get(url)
    if r.status_code != 200:
        return {}
    
    encounters = r.json()
    location_data = {}

    for enc in encounters:
        location_name = enc['location_area']['name'].replace('-', ' ').title()
        
        for version_details in enc.get('version_details', []):
            game_version = version_details['version']['name'].capitalize()
            details_list = version_details.get('encounter_details', [])
            
            methods = []
            for det in details_list:
                method_name = det.get('method', {}).get('name', 'unknown')
                methods.append(method_name.replace('-', ' '))
            
            if not methods:
                methods = ["Special Encounter"]
            
            method_desc = f"{location_name} ({', '.join(set(methods))})"
            
            if game_version not in location_data:
                location_data[game_version] = []
            
            if method_desc not in location_data[game_version]:
                location_data[game_version].append(method_desc)
            
    return location_data

@st.cache_data
def get_type_effectiveness(type_list):
    weaknesses = set()
    strengths = set()
    advantages = set() # For defensive resistances
    
    for t in type_list:
        url = f"https://pokeapi.co/api/v2/type/{t.lower()}"
        r = requests.get(url)
        if r.status_code == 200:
            damage_relations = r.json()['damage_relations']
            
            # 1. Weaknesses (Takes 2x damage from)
            for w in damage_relations['double_damage_from']:
                weaknesses.add(w['name'].capitalize())
            
            # 2. Offensive Strengths (Deals 2x damage to)
            for s in damage_relations['double_damage_to']:
                strengths.add(s['name'].capitalize())
            
            # 3. Defensive Advantages (Takes 0.5x damage or 0x damage)
            for res in damage_relations['half_damage_from']:
                advantages.add(res['name'].capitalize())
            for imm in damage_relations['no_damage_from']:
                advantages.add(f"{imm['name'].capitalize()} (Immune)")
    
    return sorted(list(weaknesses)), sorted(list(strengths)), sorted(list(advantages))

@st.cache_data
def get_pokemon_data(name_or_id):
    url = f"https://pokeapi.co/api/v2/pokemon/{str(name_or_id).lower()}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

@st.cache_data
def get_gen_data(gen_id):
    url = f"https://pokeapi.co/api/v2/generation/{gen_id}"
    r = requests.get(url)
    if r.status_code == 200:
        species = r.json()['pokemon_species']
        species.sort(key=lambda x: int(x['url'].split('/')[-2]))
        return species
    return []

def get_evolution_chain(pokemon_name):
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name.lower()}"
    res = requests.get(species_url)
    if res.status_code != 200: return None
    chain_url = res.json()['evolution_chain']['url']
    return requests.get(chain_url).json()['chain']

def extract_all_evolutions(chain_node):
    evolutions = []
    name = chain_node['species']['name']
    details_text = []
    
    if chain_node['evolution_details']:
        det = chain_node['evolution_details'][0]
        if det.get('min_level'): details_text.append(f"Level {det['min_level']}")
        if det.get('item'): details_text.append(f"Stone: {det['item']['name'].replace('-', ' ').title()}")
        if det.get('min_happiness'): details_text.append(f"High Happiness ({det['min_happiness']})")
        if det.get('min_affection'): details_text.append(f"High Affection ({det['min_affection']})")
        if det.get('time_of_day'): details_text.append(f"During {det['time_of_day'].capitalize()}")
        if det.get('known_move_type'): details_text.append(f"Know {det['known_move_type']['name'].capitalize()} move")
        if det.get('location'): details_text.append(f"At: {det['location']['name'].replace('-', ' ').title()}")
        if det['trigger']['name'] == 'trade': details_text.append("Trade")

    final_info = " + ".join(details_text) if details_text else ""
    evolutions.append({"name": name, "details": final_info})
    
    for next_evolution in chain_node['evolves_to']:
        evolutions.extend(extract_all_evolutions(next_evolution))
    return evolutions

def get_direct_evolutions(pokemon_name):
    chain_root = get_evolution_chain(pokemon_name)
    if not chain_root: return []
    
    # Recursive function to find exactly where our Pokémon is in the family tree
    def find_node(node, name):
        if node['species']['name'] == name:
            return node
        for child in node['evolves_to']:
            result = find_node(child, name)
            if result: return result
        return None
        
    current_node = find_node(chain_root, pokemon_name.lower())
    # If the Pokémon exists and has an evolution, return the next names
    if current_node and current_node['evolves_to']:
        return [child['species']['name'] for child in current_node['evolves_to']]
    return []

# --- CALLBACK FUNCTIONS ---

def nav_to_details_cb(name):
    st.session_state.selected_pokemon = name
    st.session_state.view = 'details'

def nav_to_gen_cb(gen_id):
    st.session_state.selected_gen = gen_id
    st.session_state.view = 'gen_view'

def go_home_cb():
    st.session_state.view = 'home'
    st.session_state.selected_gen = None
    st.session_state.selected_pokemon = None

def nav_to_team_cb():
    st.session_state.view = 'team'

def add_to_team(pokemon_name):
    if len(st.session_state.team) < 6 and pokemon_name not in st.session_state.team:
        st.session_state.team.append(pokemon_name)

def remove_from_team(pokemon_name):
    if pokemon_name in st.session_state.team:
        st.session_state.team.remove(pokemon_name)

def evolve_in_team_cb(old_name, new_name):
    if old_name in st.session_state.team:
        idx = st.session_state.team.index(old_name)
        st.session_state.team[idx] = new_name

# --- SESSION STATE INITIALIZATION ---
if 'view' not in st.session_state:
    st.session_state.view = 'home'
if 'selected_pokemon' not in st.session_state:
    st.session_state.selected_pokemon = None
if 'selected_gen' not in st.session_state:
    st.session_state.selected_gen = None
if 'team' not in st.session_state:
    st.session_state.team = [] # Initialize empty team

# --- INTERFACE ---

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/98/International_Pok%C3%A9mon_logo.svg")
    st.button("🏠 Home / Generations", on_click=go_home_cb, use_container_width=True)
    
    # NEW TEAM BUILDER BUTTON IN SIDEBAR
    st.button(f"🎒 My Team ({len(st.session_state.team)}/6)", on_click=nav_to_team_cb, use_container_width=True)
    
    st.divider()
    st.subheader("Direct Search")
    search_query = st.text_input("Pokémon Name:", key="search_query").lower()
    if st.button("Search", use_container_width=True):
        if search_query:
            nav_to_details_cb(search_query)
            st.rerun()

# SCREEN 1: HOME
if st.session_state.view == 'home':
    st.title("🏛️ Explore by Generation")
    gens = [
        ("Generation 1", "Kanto"), ("Generation 2", "Johto"), ("Generation 3", "Hoenn"),
        ("Generation 4", "Sinnoh"), ("Generation 5", "Unova"), ("Generation 6", "Kalos"),
        ("Generation 7", "Alola"), ("Generation 8", "Galar"), ("Generation 9", "Paldea")
    ]
    
    cols = st.columns(3)
    for i, (g_name, region) in enumerate(gens):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(g_name)
                st.write(f"Region: **{region}**")
                st.button(f"Open {region}", key=f"gen_btn_{i+1}", 
                          on_click=nav_to_gen_cb, args=(i+1,), 
                          use_container_width=True)

# SCREEN 2: GENERATION POKÉDEX
elif st.session_state.view == 'gen_view':
    gen_id = st.session_state.selected_gen
    st.title(f"📍 Pokédex - Generation {gen_id}")
    st.button("⬅ Back", on_click=go_home_cb)
    
    pokemon_list = get_gen_data(gen_id)
    pcols = st.columns(6)
    for idx, p in enumerate(pokemon_list):
        with pcols[idx % 6]:
            p_name = p['name']
            p_id = p['url'].split('/')[-2]
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p_id}.png"
            
            st.caption(f"No. {p_id}")
            st.image(img_url, use_container_width=True)
            st.button(p_name.capitalize(), key=f"p_{p_id}", 
                      on_click=nav_to_details_cb, args=(p_name,), 
                      use_container_width=True)

# SCREEN 3: DETAILS & EVOLUTION
elif st.session_state.view == 'details':
    pokemon_name = st.session_state.selected_pokemon
    
    # Back button logic
    if st.session_state.selected_gen:
        st.button("⬅ Back to Pokédex", on_click=lambda: setattr(st.session_state, 'view', 'gen_view'))
    else:
        st.button("⬅ Back to Home", on_click=go_home_cb)

    data = get_pokemon_data(pokemon_name)
    if data:
        col1, col2 = st.columns([1, 2])
        with col1:
            # --- START OF SHINY TOGGLE ADDITION ---
            is_shiny = st.toggle("✨ Show Shiny")
            
            if is_shiny:
                # Try to get the high-res shiny artwork, fallback to standard shiny sprite if it's missing
                img_url = data['sprites']['other']['official-artwork'].get('front_shiny') or data['sprites']['front_shiny']
            else:
                img_url = data['sprites']['other']['official-artwork']['front_default']
                
            st.image(img_url, use_container_width=True)
            # --- END OF SHINY TOGGLE ADDITION ---

            # --- START OF TEAM BUILDER BUTTON ---
            st.divider()
            in_team = data['name'] in st.session_state.team
            if in_team:
                st.button("❌ Remove from Team", on_click=remove_from_team, args=(data['name'],), use_container_width=True)
            elif len(st.session_state.team) < 6:
                st.button("➕ Add to Team", on_click=add_to_team, args=(data['name'],), use_container_width=True)
            else:
                st.button("⚠️ Team Full (6/6)", disabled=True, use_container_width=True)
            # --- END OF TEAM BUILDER BUTTON ---
        
        with col2:
            st.title(f"#{data['id']} - {data['name'].upper()}")
            
            # Prepare types for effectiveness function
            types_raw = [t['type']['name'] for t in data['types']]
            types_cap = [t.capitalize() for t in types_raw]
            
            st.subheader(f"Type: {' / '.join(types_cap)}")
            st.write(f"**Height:** {data['height']/10}m | **Weight:** {data['weight']/10}kg")
            
            # --- START OF UPDATED TYPE EFFECTIVENESS (Weakness, Offensive Strength, Defensive Advantage) ---
            st.divider()
            weak, strong, advantages = get_type_effectiveness(types_raw)
            
            eff_col1, eff_col2, eff_col3 = st.columns(3)
            with eff_col1:
                st.markdown("🔴 **Weaknesses**")
                st.caption("Takes 2x damage")
                st.write(", ".join(weak) if weak else "None")
                    
            with eff_col2:
                st.markdown("⚔️ **Offensive Strength**")
                st.caption("Deals 2x damage")
                st.write(", ".join(strong) if strong else "None")

            with eff_col3:
                st.markdown("🛡️ **Defensive Advantages**")
                st.caption("Takes 0.5x or 0x damage")
                st.write(", ".join(advantages) if advantages else "None")
            # --- END OF TYPE EFFECTIVENESS ADDITION ---
            
            st.divider()
            st.subheader("📊 Base Stats")
            for stat in data['stats']:
                s_name = stat['stat']['name'].replace('-', ' ').upper()
                s_val = stat['base_stat']
                st.write(f"**{s_name}**: {s_val}")
                st.progress(min(s_val / 200, 1.0))

        # Catch Locations Section
        st.divider()
        st.header("📍 Where to Catch")
        locations = get_pokemon_locations(data['id'])
        
        if locations:
            for version, spots in locations.items():
                with st.expander(f"🎮 Pokémon {version}"):
                    for spot in spots:
                        st.write(f"• {spot}")
        else:
            st.info("This Pokémon cannot be caught in the wild (evolution, gift, or event).")

        # Evolution Chain Section
        st.divider()
        st.header("🧬 Evolution Chain")
        chain_root = get_evolution_chain(pokemon_name)
        if chain_root:
            evolution_list = extract_all_evolutions(chain_root)
            ev_cols = st.columns(min(len(evolution_list), 5))
            for i, ev in enumerate(evolution_list):
                with ev_cols[i % 5]:
                    ev_data = get_pokemon_data(ev['name'])
                    if ev_data:
                        is_current = " (Current)" if ev['name'] == pokemon_name.lower() else ""
                        st.image(ev_data['sprites']['front_default'], width=120)
                        st.markdown(f"**{ev['name'].capitalize()}**{is_current}")
                        if ev['details']: 
                            st.info(ev['details'])
        else:
            st.warning("This Pokémon has no evolution chain.")
    else:
        st.error("Pokémon not found.")

# SCREEN 4: TEAM BUILDER SCREEN
elif st.session_state.view == 'team':
    st.title("🎒 My Pokémon Team")
    st.button("⬅ Back to Home", on_click=go_home_cb)
    
    st.divider()
    
    if not st.session_state.team:
        st.info("Your team is currently empty! Search for Pokémon or browse the Pokédex to add some to your squad.")
    else:
        # Create dictionaries and sets to hold the combined team data
        team_weaknesses = {}
        team_strengths = set()
        team_resistances = set()

        # 1. Display the Team Roster
        team_cols = st.columns(6)
        for idx, t_name in enumerate(st.session_state.team):
            with team_cols[idx]:
                with st.container(border=True):
                    t_data = get_pokemon_data(t_name)
                    if t_data:
                        # Display Pokémon Image & Name
                        st.image(t_data['sprites']['front_default'], use_container_width=True)
                        st.markdown(f"<center><b>{t_data['name'].capitalize()}</b></center>", unsafe_allow_html=True)
                        
                        # REMOVE BUTTON (using idx to prevent errors if you have duplicate Pokémon)
                        st.button("Remove", key=f"rm_{t_name}_{idx}", on_click=remove_from_team, args=(t_name,), use_container_width=True)
                        
                        # --- NEW: EVOLVE BUTTON LOGIC ---
                        next_evos = get_direct_evolutions(t_name)
                        if next_evos:
                            if len(next_evos) == 1:
                                # Standard evolution (e.g., Charmander -> Charmeleon)
                                st.button("✨ Evolve", key=f"ev_{t_name}_{idx}", on_click=evolve_in_team_cb, args=(t_name, next_evos[0]), use_container_width=True)
                            else:
                                # Split evolution (e.g., Eevee, Gloom, Poliwhirl)
                                evo_choice = st.selectbox("Evolve to:", [e.capitalize() for e in next_evos], key=f"sel_{t_name}_{idx}")
                                st.button("✨ Evolve", key=f"ev_split_{t_name}_{idx}", on_click=evolve_in_team_cb, args=(t_name, evo_choice.lower()), use_container_width=True)
                        
                        # --- Gather type data for Team Analysis ---
                        types_raw = [t['type']['name'] for t in t_data['types']]
                        weak, strong, advantages = get_type_effectiveness(types_raw)
                        
                        for w in weak: team_weaknesses[w] = team_weaknesses.get(w, 0) + 1
                        for s in strong: team_strengths.add(s)
                        for a in advantages: team_resistances.add(a)

        # 2. Display the Team Type Analysis
        st.divider()
        st.header("📊 Team Type Synergy")
        
        t_col1, t_col2, t_col3 = st.columns(3)
        
        with t_col1:
            st.markdown("🔴 **Team Vulnerabilities**")
            st.caption("How many Pokémon are weak to:")
            if team_weaknesses:
                sorted_weaknesses = sorted(team_weaknesses.items(), key=lambda x: x[1], reverse=True)
                for w_type, count in sorted_weaknesses:
                    alert = "⚠️ " if count >= 3 else "" 
                    st.write(f"{alert}**{w_type}**: {count} Pokémon")
            else:
                st.write("None")
                
        with t_col2:
            st.markdown("⚔️ **Team Coverage**")
            st.caption("Types your team deals 2x damage to:")
            if team_strengths:
                st.write(", ".join(sorted(list(team_strengths))))
            else:
                st.write("None")
                
        with t_col3:
            st.markdown("🛡️ **Team Resistances**")
            st.caption("Types your team resists (or is immune to):")
            if team_resistances:
                st.write(", ".join(sorted(list(team_resistances))))
            else:
                st.write("None")