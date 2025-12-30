# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Titul aplikace
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Vstup pro jméno
name_on_order = st.text_input('Name on Smoothie')
if name_on_order:
    st.write('The name on your Smoothie will be:', name_on_order)

# Připojení k Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Získání dat z tabulky (včetně sloupce SEARCH_ON, pokud ho v tabulce máš pro přesnější API volání)
my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
fruit_list = [row["FRUIT_NAME"] for row in my_dataframe.collect()]

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
        
        # Volání API - hledaný výraz očistíme pro URL
        search_term = fruit_chosen.lower().replace(' ', '')
        try:
            response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_term}", timeout=5)
            data = response.json()

            if "nutrition" in data:
                # 1. Vytvoříme základní tabulku z nutričních hodnot (carbs, fat, protein...)
                nutrition_df = pd.DataFrame.from_dict(
                    data["nutrition"], 
                    orient="index", 
                    columns=["nutrition"]
                )
                
                # 2. Přidáme metadata jako samostatné sloupce (shodně se screenshotem)
                # Používáme 'attr' místo 'col', abychom neovlivnili import 'from snowflake... import col'
                for attr in ["family", "genus", "id", "name", "order"]:
                    nutrition_df[attr] = data.get(attr, "N/A")
                
                # 3. Seřadíme sloupce přesně podle obrázku
                nutrition_df = nutrition_df[["family", "genus", "id", "name", "nutrition", "order"]]
                
                # 4. Zobrazení tabulky
                st.dataframe(nutrition_df, use_container_width=True)
            else:
                st.warning(f"No nutrition data found for {fruit_chosen}")
                
        except Exception as e:
            st.error(f"Error fetching data: {e}")

    # Příprava SQL pro vložení objednávky
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        if name_on_order and ingredients_string:
            session.sql(my_insert_stmt).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        else:
            st.error("Please provide both a name and at least one ingredient.")
