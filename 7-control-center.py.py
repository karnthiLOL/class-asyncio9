import time
import random
import json
import asyncio
import aiomqtt
import os
import sys
from enum import Enum

student_id = "6310301027"

async def publish_message(SERIAL, client, app, action, name, value):
    print(f"{time.ctime()} - [{name}:{value}] - v1cdti/{app}/{action}/{student_id}/model-01/{SERIAL}")
    await asyncio.sleep(2)
    payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01",
                "serial"    : SERIAL,
                "name"      : name,
                "value"     : value
            }
    await client.publish(f"v1cdti/{app}/{action}/{student_id}/model-01/{SERIAL}"
                        , payload=json.dumps(payload))
    
#making loop
async def loop_matchine(client):
    while True:
        await asyncio.sleep(10)
        payload = {
                "action"    : "get",
                "project"   : student_id,
                "model"     : "model-01"
            }
        print("inloop")
        print(f"{time.ctime()} - PUBLISH - v1cdti/hw/get/{student_id}/model-01/")
        await client.publish(f"v1cdti/hw/get/{student_id}/model-01/"
                        , payload=json.dumps(payload))


#listen to client to know the message
async def listen(client):
    async with client.messages() as messages:
        await client.subscribe(f"v1cdti/app/get/{student_id}/model-01/+")
        print(f"{time.ctime()} SUB topic: v1cdti/app/get/{student_id}/model-01/+")

        async for message in messages:
            m_decode = json.loads(message.payload)

            if message.topic.matches(f"v1cdti/app/get/{student_id}/model-01/+"):
                #print(f"{time.ctime()} - MQTT - [{m_decode['project']}] {m_decode['serial']} : {m_decode['name']} => {m_decode['value']}")

            
                if (m_decode['name']=="STATUS" and m_decode['value']=="OFF"):
                    await publish_message( m_decode['serial'], client, "hw", "set", "STATUS", "READY")
                    await asyncio.sleep(2)

                elif (m_decode['name']=="STATUS" and m_decode['value']=="FILLWATER"):
                    await publish_message( m_decode['serial'], client, "hw", "set", "OP_STATUS", "WATERFULLLEVEL")
                    await asyncio.sleep(2)

                elif (m_decode['name']=="STATUS" and m_decode['value']=="HEATWATER"):
                    await publish_message( m_decode['serial'], client, "hw", "set", "OP_STATUS", "RequiredTemperatureReached")
                    await asyncio.sleep(2)

#create main()
async def main():
    async with aiomqtt.Client("mqtt.eclipseprojects.io") as client:
        await asyncio.gather(listen(client),loop_matchine(client))

# Change to the "Selector" event loop if platform is Windows
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

asyncio.run(main())