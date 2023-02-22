import importlib
import numpy as np

component = importlib.util.find_spec("components\\Ethane.py")
print(component.liq_enthalpy(np.atleast_2d([100]))[0])