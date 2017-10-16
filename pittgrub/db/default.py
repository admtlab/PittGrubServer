"""
Default values to insert into database
Always inserted into database on server start

Author: Mark Silvis (marksilvis@pitt.edu)
"""


# Values to insert
# Specify by mapping table name to list of entries
# where entries are tuples of values
DEFAULTS = dict({
    'FoodPreference': [
        (1, 'Gluten Free',
            "No gluten, which is found in wheat, barley, rye, and oat."),
        (2, 'Dairy Free',
            "No dairy, which includes any items made with cow's milk. This "
            "includes milk, butter, cheese, and cream."),
        (3, 'Vegetarian',
            "No meat, which includes red meat, poultry, and seafood."),
        (4, 'Vegan',
            "No animal products, including, but not limited to, dairy "
            "(milk products), eggs, meat (red meat, poultry, and seafood), "
            "and honey."),
    ],
})
