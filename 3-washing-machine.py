import time
import random
import json
import asyncio
import aiomqtt
import os
import sys
from enum import Enum

student_id = "6310301027"

class MachineStatus(Enum):
    pressure = round(random.uniform(2000,3000), 2)
    temperature = round(random.uniform(25.0,40.0), 2)

class MachineMaintStatus(Enum):
    filter = random.choice(["clear", "clogged"])
    noise = random.choice(["quiet", "noisy"])

class WashingMachine:
    def __init__(self, serial):
        self.MACHINE_STATUS = 'OFF'
        self.OP_STATUS = 'DOOROPEN'
        self.FAULT_STATUS = 'EMPTY'
        self.SERIAL = serial        
        self.event = asyncio.Event()


async def publish_message(w, client, app, action, name, value):
    print(f"{time.ctime()} - [{w.SERIAL}] {name}:{value}")
    await asyncio.sleep(2)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : w.SERIAL,
                "name"      : name,
                "value"     : value
            }
    print(f"{time.ctime()} - PUBLISH - [{w.SERIAL}] - {payload['name']} > {payload['value']}")
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{w.SERIAL}"
                        , payload=json.dumps(payload))
    
#filling water
async def Filling_water(self, filltime=100):
    print(f"{time.ctime()} - PUBLISH - [{self.SERIAL} - {self.MACHINE_STATUS}] is filling water max time for {filltime} sec")
    await asyncio.sleep(filltime)

#Heating water
async def Heating_water(self, filltime=100):
    print(f"{time.ctime()} - PUBLISH - [{self.SERIAL} - {self.MACHINE_STATUS}] is heating water max time for {filltime} sec")
    await asyncio.sleep(filltime)

#Washing
async def WASHING(self, filltime=100):
    print(f"{time.ctime()} - PUBLISH - [{self.SERIAL} - {self.MACHINE_STATUS}] is Washing for 10 sec")
    await asyncio.sleep(filltime)

#Rinsing
async def RINSING(self, filltime=100):
    print(f"{time.ctime()} - PUBLISH - [{self.SERIAL} - {self.MACHINE_STATUS}] is Rinsing for 10 sec")
    await asyncio.sleep(filltime)

#Spining
async def SPINING(self, filltime=100):
    print(f"{time.ctime()} - PUBLISH - [{self.SERIAL} - {self.MACHINE_STATUS}] is Spining for 10 sec")
    await asyncio.sleep(filltime)

async def CoroWashingMachine(w:WashingMachine , client):

    while True:
        if w.MACHINE_STATUS == 'OFF':
            print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}] Be Waiting...")
            await w.event.wait()
            w.event.clear()
            continue

        #FAULT STATE
        if w.MACHINE_STATUS == 'FAULT':
            print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}] NOW IN FAULT STATE...")
            await w.event.wait()
            w.event.clear()
            continue
            

        #Start Step
        if w.MACHINE_STATUS == 'READY':
            print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}] IN NOW READY!")

            await publish_message(w, client, "app", "get", "STATUS", "READY")

            w.OP_STATUS = 'DOORCLOSE'
            if w.OP_STATUS == 'DOORCLOSE':
                # door close
                await publish_message(w, client, "app", "set", "OP_STATUS", "DOORCLOSE")
                w.MACHINE_STATUS = 'FILLWATER'

        #Fill water Step
        if w.MACHINE_STATUS == 'FILLWATER':

            # fill water untill full level detected within 10 seconds if not full then timeout
            try:
                async with asyncio.timeout(10):
                    await publish_message(w, client, "app", "get", "STATUS", "FILLWATER")
                    w.Task = asyncio.create_task(Filling_water(w))
                    await w.Task

            except TimeoutError:
                await publish_message(w, client, "app", "get", "FAULT_STATUS", "TIMEOUT")
                w.FAULT_STATUS = 'TIMEOUT'
                w.MACHINE_STATUS = 'FAULT'
                continue

            except asyncio.CancelledError:
                await publish_message(w, client, "app", "get", "OP_STATUS", "WATERFULLLEVEL")
                w.OP_STATUS = 'WATERFULLLEVEL'


        #Heat Step
        if w.OP_STATUS == 'WATERFULLLEVEL':
            await publish_message(w, client, "app", "get", "STATUS", "HEATWATER")
            w.MACHINE_STATUS = 'HEATWATER'


        if w.MACHINE_STATUS == 'HEATWATER':
            # heat water untill required temperature reached detected within 10 seconds if not full then timeout
            try:
                async with asyncio.timeout(10):
                    await publish_message(w, client, "app", "get", "STATUS", "HEATWATER")
                    w.Task = asyncio.create_task(Heating_water(w))
                    await w.Task

            except TimeoutError:
                await publish_message(w, client, "app", "get", "FAULT_STATUS", "TIMEOUT")
                w.FAULT_STATUS = 'TIMEOUT'
                w.MACHINE_STATUS = 'FAULT'
                continue

            except asyncio.CancelledError:
                await publish_message(w, client, "app", "get", "OP_STATUS", "RequiredTemperatureReached")
                w.OP_STATUS = 'RequiredTemperatureReached'


        #WASH Step
        if w.OP_STATUS == 'RequiredTemperatureReached':
            await publish_message(w, client, "app", "get", "STATUS", "WASH")
            w.MACHINE_STATUS = 'WASH'
        
            try:
                async with asyncio.timeout(10):
                    await publish_message(w, client, "app", "get", "STATUS", "WASH")
                    w.Task = asyncio.create_task(WASHING(w))
                    await w.Task

            except asyncio.CancelledError:
                await publish_message(w, client, "app", "get", "FAULT_STATUS", "OUTOFBALANCE")
                w.FAULT_STATUS = 'OUTOFBALANCE'
                w.MACHINE_STATUS = 'FAULT'
                continue

            except TimeoutError:
                await publish_message(w, client, "app", "get", "OP_STATUS", "FUNCTIONCOMPLETE")
                w.OP_STATUS = 'FUNCTIONCOMPLETE'

        #RINSE Step
        if w.OP_STATUS == 'FUNCTIONCOMPLETE':
            await publish_message(w, client, "app", "get", "STATUS", "RINSE")
            w.MACHINE_STATUS = 'RINSE'
        
            try:
                async with asyncio.timeout(10):
                    await publish_message(w, client, "app", "get", "STATUS", "RINSE")
                    w.Task = asyncio.create_task(RINSING(w))
                    await w.Task

            except asyncio.CancelledError:
                await publish_message(w, client, "app", "get", "FAULT_STATUS", "MOTORFAILURE")
                w.FAULT_STATUS = 'MOTORFAILURE'
                w.MACHINE_STATUS = 'FAULT'
                continue

            except TimeoutError:
                await publish_message(w, client, "app", "get", "OP_STATUS", "FUNCTIONCOMPLETE")
                w.OP_STATUS = 'FUNCTIONCOMPLETE'

        #SPIN Step
        if w.OP_STATUS == 'FUNCTIONCOMPLETE':
            await publish_message(w, client, "app", "get", "STATUS", "SPIN")
            w.MACHINE_STATUS = 'SPIN'
        
            try:
                async with asyncio.timeout(10):
                    await publish_message(w, client, "app", "get", "STATUS", "SPIN")
                    w.Task = asyncio.create_task(SPINING(w))
                    await w.Task

            except asyncio.CancelledError:
                await publish_message(w, client, "app", "get", "FAULT_STATUS", "MOTORFAILURE")
                w.FAULT_STATUS = 'MOTORFAILURE'
                w.MACHINE_STATUS = 'FAULT'
                continue

            except TimeoutError:
                await publish_message(w, client, "app", "get", "OP_STATUS", "FUNCTIONCOMPLETE")
                w.OP_STATUS = 'FUNCTIONCOMPLETE'
                print("Finish All Washing Process")
                w.MACHINE_STATUS = 'OFF'

        


            # try:
            #     await asyncio.wait_for(w.OP_STATUS == 'WATERFULLLEVEL', timeout=10)
            #     await publish_message(w, client, "app", "set", "OP_STATUS", "WATERFULLLEVEL")
            # except TimeoutError:
            #     w.OP_STATUS = 'TIMEOUT'
            #     await publish_message(w, client, "app", "get", "FAULT_STATUS", "TIMEOUT")
            #     w.MACHINE_STATUS = 'OFF'


                # heat water until temperature reach 30 celcius within 10 seconds if not reach 30 celcius then timeout

                # wash 10 seconds, if out of balance detected then fault

                # rinse 10 seconds, if motor failure detect then fault

                # spin 10 seconds, if motor failure detect then fault

                # ready state set 

                # When washing is in FAULT state, wait until get FAULTCLEARED
            

async def listen(w, client):
    async with client.messages() as messages:
        await client.subscribe(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}")
        async for message in messages:
            m_decode = json.loads(message.payload)
            if message.topic.matches(f"v1cdti/hw/set/{student_id}/model-01/{w.SERIAL}"):
                if w.SERIAL == m_decode['serial']:
                    # set washing machine status
                    print(f"{time.ctime()} - MQTT - [{m_decode['serial']}]:{m_decode['name']} => {m_decode['value']}")
                    if (m_decode['name']=="STATUS" and m_decode['value']=="READY") and w.MACHINE_STATUS != 'FAULT' :
                        w.MACHINE_STATUS = 'READY'
                        w.event.set()
                    
                    #check FAULT_STATUS
                    elif (m_decode['name']=="FAULT_STATUS" and m_decode['value']!="EMPTY") and w.MACHINE_STATUS != 'READY':
                        w.MACHINE_STATUS = 'FAULT'

                    #cancel task from Fillwater
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="WATERFULLLEVEL"):
                        if w.MACHINE_STATUS == 'FILLWATER':
                            w.OP_STATUS = "WATERFULLLEVEL"
                            if w.Task:
                                w.Task.cancel()
                        else:
                            print("Command Error!")
                    
                    #cancel task from Heatwater
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="RequiredTemperatureReached"):
                        if w.OP_STATUS == 'WATERFULLLEVEL':
                            w.OP_STATUS = "RequiredTemperatureReached"
                            if w.Task:
                                w.Task.cancel()
                            else:
                                print("Command Error!")

                    #cancel task from Washing_Task
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="OUTOFBALANCE"):
                        if w.OP_STATUS == "RequiredTemperatureReached":
                            w.OP_STATUS = "OUTOFBALANCE"
                            if w.Task:
                                w.Task.cancel()
                        else:
                            print("Command Error!")

                    #cancel task from OUTOFBALANCE_Task
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="MOTORFAILURE"):
                        if w.MACHINE_STATUS == 'RINSE':
                            w.OP_STATUS = "MOTORFAILURE"
                            if w.Task:
                                w.Task.cancel()
                        elif w.MACHINE_STATUS == 'SPIN':
                            w.OP_STATUS = "MOTORFAILURE"
                            if w.Task:
                                w.Task.cancel()
                        else:
                            print("Command Error!")
                    
                    #Fault clear
                    elif (m_decode['name']=="STATUS" and m_decode['value']=="FAULTCLEAR"):
                        if  w.MACHINE_STATUS == 'FAULT':
                            w.MACHINE_STATUS = 'OFF'
                            w.event.set()
                        else:
                            print("Command Error!")
                else:
                    print(f"{time.ctime()} - [{w.SERIAL}-{w.MACHINE_STATUS}] The serial doesn't exict")
            


async def main():
    n = 2
    W_list = [WashingMachine(serial=f'SN-00{i+1}')for i in range(n)]
    async with aiomqtt.Client("mqtt.eclipseprojects.io") as client:
        CoroWashingMachine_list = []
        listen_list = []
        for w in W_list:
            CoroWashingMachine_list.append(CoroWashingMachine(w, client))
            listen_list.append(listen(w, client))
        await asyncio.gather(*CoroWashingMachine_list,*listen_list)

# Change to the "Selector" event loop if platform is Windows
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

asyncio.run(main())