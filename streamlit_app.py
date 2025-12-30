# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Write directly to the app
st.title(f":cup_with_straw: Customize Your Smoothie:cup_with_straw:")
st.write(
  """Choose the fruits you want in your custome Smoothie!
  """)


name_on_order = st.text_input('Name on Smoothie')
st.write('The name on your Smoothie will be:', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
fruit_list = [row["FRUIT_NAME"] for row in df.collect()]

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_list,
    max_selections=5
)

if ingredients_list:

    ingredients_string = ""

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + " "

        st.subheader(fruit_chosen + " Nutrition Information")

        response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{fruit_chosen.lower()}",
            timeout=5
        )

        data = response.json()

        # --- Error case: fruit not in database ---
        if "error" in data:
            st.dataframe(
                pd.DataFrame(
                    {"value": [data["error"]]},
                    index=["error"]
                ),
                use_container_width=True
            )
            continue

        # --- Normal case: nutrition breakdown ---
        nutrition_df = (
            pd.DataFrame.from_dict(
                data["nutrition"],
                orient="index",
                columns=["nutrition"]
            )
            .reset_index()
            .rename(columns={"index": "nutrient"})
        )

        for col in ["family", "genus", "id", "name", "order"]:
            nutrition_df[col] = data[col]

        nutrition_df = nutrition_df[
            ["family", "genus", "id", "name", "nutrition", "order"]
        ]

        st.dataframe(nutrition_df, use_container_width=True)


    #st.write (ingredients_string)

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
values ('""" + ingredients_string + """','""" +name_on_order+ """')"""


    #st.write(my_insert_stmt)
 
    
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
      
