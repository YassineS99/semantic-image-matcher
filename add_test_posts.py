from add_post import add_post

TEST_POSTS = [
    "This little red fox visited my backyard again this morning - not a duplicate, second sighting!",
    "Spotted a coyote trotting across the field at dusk",
    "My siberian husky loves playing in the snow",
    "Our german shepherd guard dog is so loyal and protective",
]

for text in TEST_POSTS:
    add_post(text)