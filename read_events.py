import sys
import os

events_path = r"C:\Users\Kelly\AppData\Roaming\Python\Python314\site-packages\agents\realtime\events.py"
runner_path = r"C:\Users\Kelly\AppData\Roaming\Python\Python314\site-packages\agents\realtime\runner.py"

for path in [events_path, runner_path]:
    print(f"\n{'='*80}")
    print(f"FILE: {path}")
    print('='*80)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e:
        print(f"ERROR: {e}")
