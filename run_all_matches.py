from match_post import match_post

POST_IDS = [2, 3, 4, 5, 6, 7]

for pid in POST_IDS:
    print(f"--- Post {pid} ---")
    match_post(post_id=pid, top_n=10)