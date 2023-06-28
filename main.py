import streamlit as st
import pandas as pd
from pulp import *
import matplotlib.pyplot as plt
import circlify
import random

st.title('The Eat-out-worry-free Tool')
st.text('''
        Use this tool for calculate calories for your order
        ''')

fast_food_data = pd.read_csv('fastfood.csv')


RestaurantName_list = fast_food_data.restaurant.unique().tolist()

RestaurantName = st.selectbox(
    'Please choose your restaurant', RestaurantName_list,index=6
    )

st.write('You selected: ', RestaurantName)
mask_restaurant = fast_food_data["restaurant"] == RestaurantName
fast_food_data = fast_food_data[mask_restaurant]
# Convert the item names to a list
Menuitems = fast_food_data.item.tolist()

# Convert all of the macro nutrients fields to be dictionaries of the item names
TotalFat        =      fast_food_data.set_index('item')['total_fat'].to_dict()
calories        =      fast_food_data.set_index('item')['calories'].to_dict()
SaturatedFat    =      fast_food_data.set_index('item')['sat_fat'].to_dict()
total_carb   =         fast_food_data.set_index('item')['total_carb'].to_dict()
sugar          =       fast_food_data.set_index('item')['sugar'].to_dict()
protein         =      fast_food_data.set_index('item')['protein'].to_dict()
sodium          =      fast_food_data.set_index('item')['sodium'].to_dict()

# Using Linear Optimization to minimize the calories intakes

prob = LpProblem("Fastfood Optimization Problem", LpMinimize)

Menuitems_vars = LpVariable.dicts("Menuitems", Menuitems, lowBound=0,
                                  upBound=15, cat='Integer')

# Setting up the sidebar for the combinations
st.sidebar.write('Limits for Combo')
TotalFat_val = st.sidebar.slider(
    'Max Fat', min_value=0, max_value=141, value=5)
# TotalFat_val    =  st.sidebar.number_input('Max Fat', value=140)
SatFat_val = st.sidebar.slider(
    'Max Sat Fat', min_value=0, max_value=47, value=3)

SugarMin = st.sidebar.slider(
    'Sugar Min', min_value=0, max_value=87,  value=0)
SugarMax = st.sidebar.slider(
    'Sugar Max', min_value=0, max_value=87,  value=5)

CarbsMin = st.sidebar.slider(
    'Total Carb Min', min_value=0, max_value=156,  value=0)
CarbsMax = st.sidebar.slider(
    'Total Carb Max', min_value=0, max_value=156,  value=10)
proteinMin = st.sidebar.slider(
    'Protein Min', min_value=1, max_value=186, value=18)
proteinMax = st.sidebar.slider(
    'Protein Max', min_value=1, max_value=186,  value=43)

sodiumMax = st.sidebar.slider(
    'sodium Max', min_value=15, max_value=6080, value=503)


# First entry is the calorie calculation (this is our objective)
prob += lpSum([calories[i]*Menuitems_vars[i] for i in Menuitems]), "calories"
# total_fat must be <= 70 g
prob += lpSum([TotalFat[i]*Menuitems_vars[i]
              for i in Menuitems]) <= TotalFat_val, "TotalFat"
# Saturated Fat is <= 20 g
prob += lpSum([SaturatedFat[i]*Menuitems_vars[i]
              for i in Menuitems]) <= SatFat_val, "Saturated Fat"
# total_carb must be more than 260 g
prob += lpSum([total_carb[i]*Menuitems_vars[i]
              for i in Menuitems]) >= CarbsMin, "total_carb_lower"
prob += lpSum([total_carb[i]*Menuitems_vars[i]
              for i in Menuitems]) <= CarbsMax, "total_carb_upper"
# Sugar between 80-100 g
prob += lpSum([sugar[i]*Menuitems_vars[i]
              for i in Menuitems]) >= SugarMin, "sugar_lower"
prob += lpSum([sugar[i]*Menuitems_vars[i]
              for i in Menuitems]) <= SugarMax, "sugar_upper"
# protein between 45-55g
prob += lpSum([protein[i]*Menuitems_vars[i]
              for i in Menuitems]) >= proteinMin, "protein_lower"
prob += lpSum([protein[i]*Menuitems_vars[i]
              for i in Menuitems]) <= proteinMax, "protein_upper"
# sodium <= 6000 mg
prob += lpSum([sodium[i]*Menuitems_vars[i]
              for i in Menuitems]) <= sodiumMax*1000, "sodium"

# Use Linear Optimization
prob.solve()


# Loop over the constraint set and get the final solution
results = {}

for constraint in prob.constraints:
    s = 0
    for var, coefficient in prob.constraints[constraint].items():
        s += var.varValue * coefficient
    results[prob.constraints[constraint].name.replace('_lower', '')
            .replace('_upper', '')] = s


objective_function_value = value(prob.objective)

varsdict = {}
for v in prob.variables():
    if v.varValue > 0:
        varsdict[v.name] = v.varValue



st.header('Total calories: ' + str(objective_function_value))


# Create just a figure and only one subplot
fig, ax = plt.subplots(figsize=(15, 10))

# Title
ax.set_title('McHealthy Combo')

# Remove axes
ax.axis('off')

circles = circlify.circlify(
    varsdict.values(),
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=1)
)

# Find axis boundaries
lim = max(
    max(
        abs(circle.x) + circle.r,
        abs(circle.y) + circle.r,
    )
    for circle in circles
)
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

# list of labels
labels = [i[10:] for i in varsdict.keys()]


# print circles
for circle, label in zip(circles, labels):
    x, y, r = circle
    ax.add_patch(plt.Circle((x, y), r*0.7, alpha=0.9, linewidth=2,
                 facecolor="#%06x" % random.randint(0, 0xFFFFFF), edgecolor="black"))
    plt.annotate(label, (x, y), va='center', ha='center', bbox=dict(
        facecolor='white', edgecolor='black', boxstyle='round', pad=.5))
    value = circle.ex['datum']
    plt.annotate(value, (x, y-.1), va='center', ha='center',
                 bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.5))


st.pyplot(fig)

st.subheader('Created by Khai Nguyen')
st.text('Please use this as a reference only.')
st.caption(
    'Get the code [here](https://www.datacareerjumpstart.com/30projectsresourcesignup)')
st.caption(
    'My [LinkedIn] profile (https://www.linkedin.com/in/kh-ai/)')
