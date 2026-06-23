class Ship:
    def __init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
        self.propulsion = propulsion
        self.auxiliary = auxiliary
        self.power = self.propulsion+self.auxiliary
        self.avg_speed = avg_speed
        self.op_time = op_time
        self.portcalls = portcalls
        self.name = name
    
    
