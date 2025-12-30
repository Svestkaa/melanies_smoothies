# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Titul a úvod
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Vstup pro jméno
name_on_order = st.text_input('Name on Smoothie')
if name_on_order:
    st.write('The name on your Smoothie will be:', name_on_order)

# Připojení k Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Získání seznamu ovoce
df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
# Převedení na list (pro multiselect)
fruit_list = [row["FRUIT_NAME"] for row in df.collect()]

# Výběr ingrediencí
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_list,
    max_selections=5
)

if ingredients_list:
    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "
        
        st.subheader(f"{fruit_chosen} Nutrition Information")
        
        # Volání API
        try:
            # Vyčištění názvu pro API (malá písmena a bez mezer)
            search_term = fruit_chosen.lower().replace(' ', '')
            response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_term}", timeout=5)
            data = response.json()

            # Kontrola chyby v API
            if "error" in data:
                st.warning(f"Could not find nutrition data for {fruit_chosen}.")
            else:
                # Normalizace dat do tabulky
                nutrition_df = pd.DataFrame.from_dict(
                    data["nutrition"], 
                    orient="index", 
                    columns=["Value"]
                ).reset_index().rename(columns={"index": "Nutrient"})
                
                # Přidání doplňkových informací bez přepsání funkce 'col'
                for info_key in ["family", "genus", "name", "order"]:
                    if info_key in data:
                        nutrition_df[info_key] = data[info_key]
                
                st.dataframe(nutrition_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching data for {fruit_chosen}: {e}")

    # Sestavení SQL dotazu
    # Odstraníme poslední mezeru z ingredients_string pomocí .strip()
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    # Tlačítko pro odeslání
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        if name_on_order:
            session.sql(my_insert_stmt).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        else:
            st.error("Please enter a name for the order.")
