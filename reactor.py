class Reactor:
    # simulated reactor
    # power == electrical power
    def __init__(self,power,burnup,enrichment,name):
        self.power = power
        self.burnup = burnup
        self.enrichment = enrichment
        self.name = name
    def __str__(self):
        return (
            f"=== {self.name} Reactor characteristics ===\n"
            f"Power: {self.power} MWe\n"
            f"Burnup:  {self.burnup} GWd/t\n"
            f"Fuel enrichment:    {self.enrichment}%"
        )