class Reactor:
    # simulated reactor
    # power == electrical power
    def __init__(self,power,burnup,enrichment,name):
        self.power = power
        self.burnup = burnup
        self.enrichment = enrichment
        self.reactorname = name
    def __str__(self):
        return (
            f"=== {self.reactorname} Reactor characteristics ===\n"
            f"Power: {self.power} MWe\n"
            f"Burnup:  {self.burnup} GWd/t\n"
            f"Fuel enrichment:    {self.enrichment}%\n"
        )