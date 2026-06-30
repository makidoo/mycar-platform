# debug_models.py
import os
import sys

# Add your project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Read the models.py file directly
models_path = os.path.join('core', 'models.py')
if os.path.exists(models_path):
    print("✓ Found core/models.py")
    print("\nFile contents:")
    print("-" * 40)
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
        
    # Extract class names
    import re
    classes = re.findall(r'^class (\w+)\(', content, re.MULTILINE)
    print("\nClasses found:", classes)
else:
    print("✗ core/models.py NOT FOUND!")