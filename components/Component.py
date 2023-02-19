from abc import ABC, abstractmethod

class Component(ABC):
    """
    Abstract base class for component. All user-defined components should inherit from this class
    """
    @staticmethod
    @abstractmethod
    def vapor_pressure(T):
        """
        Takes in a temperature value and return the vapor pressure of the component
        """
        pass

    @staticmethod
    @abstractmethod
    def density(T):
        """
        Takes in a temperature value and returns the liquid density of the component
        """
        pass

    @staticmethod
    @abstractmethod
    def liq_enthalpy(T):
        """
        Takes in an array of temperature values and return an array of liquid enthalpy values
        """
        pass

    @staticmethod
    @abstractmethod
    def vap_enthalpy(T):
        """
        Takes in an array of temperature values and return an array of vapor enthalpy values
        """
        pass

    @staticmethod
    @abstractmethod
    def liq_heat_capacity(T):
        """
        Takes in an array of temperature values and return an array of liquid specific heat capacity
        of the component
        """
        pass
    
    @staticmethod
    @abstractmethod
    def vap_heat_capacity(T):
        """
        Takes in an array of temperature values and return an array of vapor specific heat capacity
        of the component
        """
        pass
    

