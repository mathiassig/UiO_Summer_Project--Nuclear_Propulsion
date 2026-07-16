class FuelNeeds:
    def __init__(self,fuel_throughput,swu,feedmass,pebble_number,waste):
        self.fuel_throughput = fuel_throughput # fuel throughput [tons of enriched uranium]
        self.pebble_number = pebble_number# TRISO pebbles needed = TRISO pebbles out
        self.swu = swu # separative work needed [SWU]
        self.feedmass = feedmass # natural uranium need in [tons]
        self.waste = waste # waste volume [m^3]
class InfrastructureNeeds:
    def __init__(self,fresh_store,spent_store,
                 refuelings,refueling_tons,refueling_pebbles,
                 fuelinit,fuelinit_tons,fuelinit_pebbles,truckloads_waste,
                 swu,feedmass):
        self.fresh_store = fresh_store # storage capacity for fresh fuel [m^3]
        self.spent_store = spent_store # storage capacity for spent fuel [m^3]
        self.refuelings = refuelings # number of ships being refueled globally
        self.refueling_tons = refueling_tons # amount of enriched uranium going to refueling in a given year [tons]
        self.refueling_pebbles = refueling_pebbles # number of TRISO pebbles going to refueling in a given year
        self.fuelinit = fuelinit # number of new ships being deployed
        self.fuelinit_tons = fuelinit_tons # amount of enriched uranium going to initial fuel loadings in a given year [tons]
        self.fuelinit_pebbles = fuelinit_pebbles # number of TRISO pebbles going to initial fuel loadings in a given year
        self.truckloads_waste = truckloads_waste # number of truckloads of waste being moved from interim storage per year
        self.swu = swu # separative work needed for a given year [SWU]
        self.feedmass = feedmass # natural uranium needed to produce HALEU in a given year [tons]
        