import importlib
import numpy as np

component = importlib.import_module("components.Ethane")
print(component.liq_enthalpy(np.atleast_2d([100]))[0])