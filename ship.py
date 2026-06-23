class Ship:
    def __init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
        self.propulsion = propulsion
        self.auxiliary = auxiliary
        self.power = self.propulsion+self.auxiliary
        self.avg_speed = avg_speed
        self.op_time = op_time
        self.portcalls = portcalls
        self.name = name
    def __str__(self):
        return (
            f"=== {self.name} ship characteristics ===\n"
            f"Installed propulsion power: {self.propulsion} MW\n"
            f"Installed auxiliary power:  {self.auxiliary} MW\n"
            f"Average speed:  {self.avg_speed} knots\n"
            f"Operational time:    {self.op_time} hours\n"
            f"Number of portcalls per year:  {self.portcalls}"
        )    
    
