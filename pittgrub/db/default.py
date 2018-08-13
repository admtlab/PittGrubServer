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
    'Role': [
        (1, 'User', "View events, receive notifications"),
        (2, 'Host', "Create events"),
        (3, 'Admin', "Approve hosts, manage application"),
    ],
    'Building': [
        (1, "Allen Hall", 40.44461599, -79.95841026),
        (2, "Alumni Hall", 40.44557946, -79.95388269),
        (3, "Amos Hall", 40.44349329, -79.95573342),
        (4, "Bellefield Hall", 40.44539166, -79.95090008),
        (5, "Benedum Hall", 40.44369742, -79.95861411),
        (6, "The University Store", 40.44318302, -79.95621622),
        (7, "Brackenridge Hall", 40.44275843, -79.95556712),
        (8, "Bruce Hall", 40.44297481, -79.95507896),
        (9, "Biomedical Science Towers 1 and 2", 40.44211745, -79.96204734),
        (10, "Biomedical Science Tower 3", 40.44104371, -79.9600625),
        (11, "Cathedral of Learning", 40.44425265, -79.95323896),
        (12, "Chevron Science Center", 40.44597545, -79.95747149),
        (13, "Clapp Hall", 40.44620407, -79.95316386),
        (14, "Charles L. Cost Sport Center", 40.44628571, -79.9649334),
        (15, "Craig Hall", 40.44617549, -79.94922638),
        (16, "Crawford Hall", 40.44697564, -79.95424747),
        (17, "Eberly Hall", 40.44590605, -79.95834589),
        (18, "Engineering Auditorium", 40.44406077, -79.95813668),
        (19, "Falk Medical Building", 40.44152547, -79.95935977),
        (20, "Falk School", 40.44699605, -79.95970309),
        (21, "Forbes Craig Apartments", 40.44451801, -79.94917274),
        (22, "Fitzgerald Field House", 40.44345247, -79.96418238),
        (23, "Frick Fine Arts Building", 40.4416602, -79.9512434),
        (24, "Gardner Steel Conference Center", 40.44443636, -79.95792747),
        (25, "Heinz Memorial Chapel", 40.44526919, -79.95188177),
        (26, "Hillman Library", 40.4425543, -79.95411873),
        (27, "Holland Hall", 40.44288907, -79.95590508),
        (28, "Information Sciences Building", 40.44737979, -79.95274544),
        (29, "Langley Hall", 40.44669395, -79.95371103),
        (30, "Barco Law Building", 40.44177043, -79.95568514),
        (31, "Lawrence Hall", 40.44239507, -79.95523453),
        (32, "Loeffler Building", 40.44085999, -79.95848536),
        (33, "Lothrop", 40.44165611, -79.96004105),
        (34, "Learning Research and Development Center", 40.44446086, -79.95894134),
        (35, "McCormick Hall", 40.44327284, -79.95540082),
        (36, "Mervis Hall", 40.44081099, -79.95333552),
        (37, "Music Building", 40.44667354, -79.95223045),
        (38, "Old Engineering Hall", 40.44499158, -79.95809376),
        (39, "Oxford Building", 40.44011692, -79.95946169),
        (40, "Pennsylvania Hall", 40.444963, -79.96032),
        (41, "Panther Hall", 40.44528144, -79.9616611),
        (42, "Forbes Pavilion", 40.44039047, -79.95901108),
        (43, "Petersen Events Center", 40.44382806, -79.96228337),
        (44, "Public Health", 40.44286049, -79.95842099),
        (45, "Ruskin Hall", 40.44706545, -79.9530673),
        (46, "Salk Hall", 40.44257879, -79.96272326),
        (47, "Scaif Hall", 40.44251347, -79.9618274),
        (48, "Sennott Square", 40.44158671, -79.95638251),
        (49, "Space Research Coordination Center", 40.44544882, -79.95723009),
        (50, "Stephen Foster Memorial", 40.44381582, -79.95280445),
        (51, "Sutherland Hall", 40.44588564, -79.9626267),
        (52, "Thackeray Hall", 40.44419549, -79.95744467),
        (53, "Thaw Hall", 40.44517937, -79.95759487),
        (54, "Litchfield Towers", 40.44257471, -79.95667756),
        (55, "Trees Hall", 40.44408118, -79.96550202),
        (56, "University Club", 40.44421182, -79.95683312),
        (57, "Victoria Building", 40.44129684, -79.96071696),
        (58, "Van de Graaff Building", 40.44479562, -79.95856583),
        (59, "William Pitt Union", 40.4434688, -79.95480001),
        (60, "Wesley W. Posvar Hall", 40.44164387, -79.95381832),
    ],
    'PrimaryAffiliation': [
        (1, 'Kenneth P. Dietrich School of Arts and Science'),
        (2, 'School of Computing and Information'),
        (3, 'Swanson School of Engineering'),
        (4, 'Sodexo Dining Services')
    ]
})
