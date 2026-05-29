import sys
import os

# Ensure `import tokenmesh` resolves to sdk/tokenmesh
# and `import collector` resolves to collector/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk"))
sys.path.insert(0, os.path.dirname(__file__))
