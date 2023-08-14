import re

# Extract parameters from the Python class docstring
with open("application/app_descriptor.py", "r") as file:
    content = file.read()
    params_py = re.findall(r":param (\w+):", content)

# Extract parameters from README.md
with open("README.md", "r") as file:
    content = file.read()
    params_md = re.findall(r"- \*\*`(\w+)`\*\* \(", content)

# Compare parameters
if set(params_py) != set(params_md):
    missing_in_md = set(params_py) - set(params_md)
    missing_in_py = set(params_md) - set(params_py)

    if missing_in_md:
        print(f"Parameters present in `app_descriptor.py` but missing in `README.md`: {', '.join(missing_in_md)}")
    if missing_in_py:
        print(f"Parameters present in `README.md` but missing in `app_descriptor.py`: {', '.join(missing_in_py)}")

    raise SystemExit("Parameter lists do not match!")
