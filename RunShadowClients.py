# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import random
import glob
from pathlib import Path
from ShadowClient import ShadowClient 
import boto3
from botocore.config import Config

#Array to hold the names of things created during the setup
thingNames = []

#Meta data about charger types. Created things are assigned one of these types.
charger_specs = {
    "Level_1": {
        "type": "Level_1",
        "connectorType": "Standard",
        "voltage": "120V",
        "current": "16A",
        "powerOutput": "1.9kW" 
    },
    "Level_2": {
        "type": "Level_2",
        "connectorType": "Enhanced",
        "voltage": "240V",
        "current": "32A",
        "powerOutput": "7.7kW"
    },
    "Level_3": {
        "type": "Level_3",
        "connectorType": "Fast_Charging",
        "voltage": "480V",
        "current": "100A",
        "powerOutput": "50kW"
    }
}

#Config to be passed to boto library to set the default region to us-east-1
my_config = Config(
    region_name = 'us-east-1',
)
iotclient = boto3.client('iot', config=my_config)

#Utility function to read the thing names. It reads the certificates created during the setup process
def readTargetThingNames(targetDir):
    global thingNames
    for file in glob.glob(targetDir):
        thingNames.append(Path(file).stem)
    
#update the registry and shadow
def launchClients():
    #Find out the IoT Core End Point
    response = iotclient.describe_endpoint(
        endpointType='iot:Data-ATS'
    )
    endpoint = response["endpointAddress"]
    print ("IoT Core endpoint: " + endpoint)
    
    #update the thing attributes in registry
    for thing in thingNames:
        print("Updating thing attributes for: " + thing)
        
        random_type = random.choice(list(charger_specs.keys()))
        charger_metadata = {}
        charger_metadata['attributes'] = charger_specs[random_type]
        charger_metadata['merge'] = True
        
        print("thing attirbutes: " + json.dumps(charger_metadata))
        iotclient.update_thing(thingName=thing, attributePayload=charger_metadata)
        
        #Update shadow
        ShadowClient(endpoint, thing, "root-CA.crt", 
            "provisioning/"+thing+".crt", "provisioning/"+thing+".key")
    
if __name__ == '__main__':
    readTargetThingNames("provisioning/*.key")
    launchClients()
