import os

RENAME_MAP = {
    "red fox": "fox",
    "gray wolf": "wolf",
    "coyote": "coyote",
    "husky": "husky",
    "german": "german",
}

folder = "data/images"

for filename in os.listdir(folder):
    if not filename.lower().endswith(".jpg"):
        continue
    name, ext = os.path.splitext(filename)
    for old_prefix, new_prefix in RENAME_MAP.items():
        if name.lower().startswith(old_prefix):
            number = name[len(old_prefix):].strip()
            new_name = f"{new_prefix}_{int(number):03d}{ext}"
            os.rename(
                os.path.join(folder, filename),
                os.path.join(folder, new_name)
            )
            print(f"{filename} -> {new_name}")
            break