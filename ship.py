class Ship:
    def __init__(self,installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
        self.installed_power = installed_power
        self.propulsion = propulsion
        self.auxiliary = auxiliary
        self.avg_speed = avg_speed
        self.op_time = op_time
        self.portcalls = portcalls
        self.shipname = name
    def __str__(self):
        return (
            f"=== {self.shipname} ship characteristics ===\n"
            f"Installed propulsion power: {self.propulsion} MW\n"
            f"Installed auxiliary power:  {self.auxiliary} MW\n"
            f"Average speed:  {self.avg_speed} knots\n"
            f"Operational time:    {self.op_time} hours\n"
            f"Number of portcalls per year:  {self.portcalls}\n"
        )    
from reactor import Reactor   
from country import Country
import math

class PoweredShip(Ship,Reactor,Country):
    def __init__(self,
                installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname, # Ship parameters
                power,burnup,enrichment,reactorname, # Reactor parameters
                countryname, # Country name, e.g. "France", "Norway", "Canada"
                iso3, # Three-letter ISO country code, e.g. "FRA", "NOR", "CAN"
                region, # Broad geographical region, e.g. "Europe", "North America", "Asia"
                oecd_member,   # True if the country is in the OECD
                supply, # True if the country takes part in the supply chain
                step,              # Supply-chain step: "enrichment", "triso_fabrication", "reactor_manufacturing"
                supply_from_year, # Year when the capability is assumed available
                capacity,          # Numerical capacity per year
                capacity_unit,     # e.g. "SWU/year", "t/year", "reactor modules/year"
                operation, # True if the country has relevant ports for the ships operation routes
                available_from_year, # Year when the country ports start taking part in the routes
                ports, # Number of relevant ports
                ports_names, # Names of the relevant ports
                latitude,  # Port latitudes separated by ","
                longitude, # Port longitude separated by ","
                number = 1 # PoweredShip parameters
                ):
        # Run initialisers from parent classes
        Ship.__init__(self,installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname) 
        Reactor.__init__(self,power,burnup,enrichment,reactorname)
        if countryname:
            Country.__init__(self,
                            countryname,iso3,region,oecd_member,   
                            supply,step,supply_from_year,capacity,capacity_unit,
                            operation,available_from_year,ports,ports_names,
                            latitude,longitude,
                            )
        # Continue with initialiser for child class
        self.reactornumber = math.ceil(self.installed_power/self.power) # divide ship power demand by reactor power supply and round up to nearest integer to find number of reactor modules needed
        self.shipnumber = number
        self.total_reactornumber = self.shipnumber*self.reactornumber

    # set number of combinations of ship and reactor
    def set_number(self,number): # set number of ships of this type
        self.shipnumber = number
        self.total_reactornumber = self.shipnumber*self.reactornumber
    
    def __str__(self):
        return f"{self.shipnumber} {self.shipname} ship(s) from {self.countryname} with {self.reactornumber} {self.reactorname} reactors each\n"+Ship.__str__(self)+Reactor.__str__(self)+Country.__str__(self)