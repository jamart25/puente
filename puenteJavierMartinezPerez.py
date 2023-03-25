"""
Solution to the one-way tunnel

Once a carN has crossed, lets carS cross. When carS has crossed
lets pedestrians cross.
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 200
NPED = 30
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.ncarN = Value('i', 0)
        self.ncarS = Value('i', 0)
        self.npedestrian = Value('i', 0)
        self.ncarN_waiting = Value('i', 0)
        self.ncarS_waiting = Value('i', 0)
        self.npedestrian_waiting = Value('i', 0)
        self.turn = Value('i', -1)
        self.nthings = Value('i', 0) #number of thing that are crossing the bridge
        #turn -1 for the beggining
        #turn 0 for carN
        #turn 1 for carS
        #turn 2 for pedestrian
        self.canN_cross = Condition(self.mutex)
        self.canS_cross = Condition(self.mutex)
        self.canP_cross = Condition(self.mutex)

    def carN_can_cross(self) -> bool:
        return self.npedestrian.value == 0 \
                and self.ncarS.value == 0 \
                and self.ncarN.value < 1 \
                and (self.turn.value == 0 or self.turn.value == -1)
    def carS_can_cross(self) -> bool:
        return self.npedestrian.value == 0 \
                and self.ncarN.value == 0 \
                and self.ncarS.value < 1 \
                and (self.turn.value == 1 or self.turn.value == -1)

    def can_pedestrian_cross(self) -> bool:
        return self.npedestrian.value < 3 \
                and self.ncarN.value == 0 and self.ncarS.value == 0 \
                and (self.turn.value == 2 or self.turn.value == -1)
                

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()

        if direction == NORTH:
            self.ncarN_waiting.value += 1
            self.canN_cross.wait_for(self.carN_can_cross)
            self.ncarN_waiting.value -= 1
            self.ncarN.value += 1
            self.nthings.value += 1
        elif direction == SOUTH:
            self.ncarS_waiting.value += 1
            self.canS_cross.wait_for(self.carS_can_cross)
            self.ncarS_waiting.value -= 1
            self.ncarS.value += 1
            self.nthings.value += 1
        
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 

        if direction == NORTH:
            self.ncarN.value -= 1
            self.nthings.value -= 1
            """
            if self.ncarN.value == 0:
                self.canS_cross.notify_all()
                self.canN_cross.notify_all()
            """
            if self.ncarS_waiting.value > 0:
                self.turn.value = 1
                self.canS_cross.notify_all()
            elif self.npedestrian_waiting.value > 0:
                self.turn.value = 2
                self.canP_cross.notify_all()
            elif self.ncarN_waiting.value == 0:
                self.turn.value = -1
                #self.canS_cross.notify_all()
                #self.canP_cross.notify_all()
            self.canN_cross.notify_all()
        elif direction == SOUTH:
            self.ncarS.value -= 1
            self.nthings.value -= 1
            """
            if self.ncarS.value == 0:
                self.canN_cross.notify_all()
                self.canS_cross.notify_all()
            """
            if self.npedestrian_waiting.value > 0:
                self.turn.value = 2
                self.canP_cross.notify_all()
            elif self.ncarN_waiting.value > 0:
                self.turn.value = 0
                self.canN_cross.notify_all()
            elif self.ncarN_waiting.value == 0:
                self.turn.value = -1
                #self.canN_cross.notify_all()
                #self.canP_cross.notify_all()
            self.canS_cross.notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.npedestrian_waiting.value += 1
        self.canP_cross.wait_for(self.can_pedestrian_cross)
        self.npedestrian_waiting.value -= 1
        self.npedestrian.value += 1
        self.nthings.value += 1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()

        self.npedestrian.value -= 1
        self.nthings.value -= 1
        """
        if self.npedestrian.value < 2:
            self.canP_cross.notify_all()
            self.canN_cross.notify_all()
            self.canS_cross.notify_all()
        """
        if self.ncarN_waiting.value > 0:
            self.turn.value = 0
            self.canN_cross.notify_all()
        elif self.ncarS_waiting.value > 0:
            self.turn.value = 1
            self.canS_cross.notify_all()
        elif self.npedestrian.value == 0:
            self.turn.value = -1 
            #self.canN_cross.notify_all()
            #self.canS_cross.notify_all()
        self.canP_cross.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.nthings.value} carsN: {self.ncarN.value} waiting {self.ncarN_waiting.value} carsS: {self.ncarS.value} waiting {self.ncarS_waiting.value} peds: {self.npedestrian.value} waiting {self.npedestrian_waiting.value}'

def delay_car_north() -> None:
    pass

def delay_car_south() -> None:
    pass

def delay_pedestrian() -> None:
    pass

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()
