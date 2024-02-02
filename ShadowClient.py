# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import time
import random
from awscrt import io, mqtt
from awsiot import iotshadow
from awsiot import mqtt_connection_builder

keeprunnig = True
shadow_client = ""
thingName = ""

class ShadowClient():
        
    def on_get_shadow_accepted(self, response):
        print("get shadow accepted")
    
    def on_get_shadow_rejected(self, error):
        print("get shadow rejected")
    
    def on_shadow_delta_updated(self, delta):
        print("shadow delta updated")
    
    def on_publish_update_shadow(self, future):
        #type: (Future) -> None
        try:
            future.result()
            print("Update request published.")
        except Exception as e:
            print("Failed to publish update request.")
            exit(e)
    
    def on_update_shadow_accepted(self, response):
        print("Update shadow accepted")
    
    def on_update_shadow_rejected(self, error):
        print("Update shadow rejected")
    
    def on_disconnected(self, disconnect_future):
        # type: (Future) -> None
        print("Disconnected.")
        
    def on_message_received(self, topic, payload, dup, qos, retain, **kwargs):
        print("Received message from topic '{}': {}".format(topic, payload))
    
    def __init__(self, endpoint, client_id, root_ca, cert, key):
        global shadow_client
        global thingName
        thingName = client_id
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        self.__mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint = endpoint,
            cert_filepath = cert,
            pri_key_filepath = key,
            client_bootstrap = client_bootstrap,
            ca_filepath = root_ca,
            client_id = client_id,
            clean_session = False,
            keep_alive_secs = 30)
        connect_future = self.__mqtt_connection.connect()
        shadow_client = iotshadow.IotShadowClient(self.__mqtt_connection)

        # Wait for connection to be fully established.
        # Note that it's not necessary to wait, commands issued to the
        # mqtt_connection before its fully connected will simply be queued.
        # But this sample waits here so it's obvious when a connection
        # fails or succeeds.
        connect_future.result()
        print("Connected! {}".format(client_id))
        
        try:
            
            print("Subscribing to Update responses...")
            update_accepted_subscribed_future, _ = shadow_client.subscribe_to_update_shadow_accepted(
                request=iotshadow.UpdateShadowSubscriptionRequest(thing_name=client_id),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_update_shadow_accepted)
    
            update_rejected_subscribed_future, _ = shadow_client.subscribe_to_update_shadow_rejected(
                request=iotshadow.UpdateShadowSubscriptionRequest(thing_name=client_id),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_update_shadow_rejected)
    
            # Wait for subscriptions to succeed
            update_accepted_subscribed_future.result()
            update_rejected_subscribed_future.result()
            
            
    
            print("Subscribing to Get responses...")
            get_accepted_subscribed_future, _ = shadow_client.subscribe_to_get_shadow_accepted(
                request=iotshadow.GetShadowSubscriptionRequest(thing_name=client_id),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_get_shadow_accepted)
    
            get_rejected_subscribed_future, _ = shadow_client.subscribe_to_get_shadow_rejected(
                request=iotshadow.GetShadowSubscriptionRequest(thing_name=client_id),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_get_shadow_rejected)
    
            # Wait for subscriptions to succeed
            get_accepted_subscribed_future.result()
            get_rejected_subscribed_future.result()
    
            print("Subscribing to Delta events...")
            delta_subscribed_future, _ = shadow_client.subscribe_to_shadow_delta_updated_events(
                request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(thing_name=client_id),
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=self.on_shadow_delta_updated)
    
            # Wait for subscription to succeed
            delta_subscribed_future.result()
    
            self.updateDeviceShadow()
    
        except Exception as e:
            exit(e)
    
        '''
        # Subscribe
        print("Subscribing to topic '{}'...".format(TOPIC))
        subscribe_future, packet_id = self.__mqtt_connection .subscribe(
            topic=TOPIC,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_message_received)

        subscribe_result = subscribe_future.result()
        print("Subscribed with {}".format(str(subscribe_result['qos'])))
        '''
    def publish(self, topic, payload):
        self.__mqtt_connection.publish(
            topic = topic,
            payload = json.dumps(payload),
            qos = mqtt.QoS.AT_MOST_ONCE) # mqtt.QoS.AT_LEAST_ONCE
 
    def __del__(self):
        disconnect_future = self.__mqtt_connection.disconnect()
        disconnect_future.result()
        
    #Utility fucntion to populat the shadow. This implementation updates the shadow 
    #with random values for location and other attributes
    def get_charger_shadow(self):
        charger_data = {
            "config":{
                "location":{
                    "lat": random.uniform(37.7045, 37.8120), 
                    "lon": random.uniform(-122.5270, -122.3565)
                }
            },
            "usage":{
                "isOnline": random.choices([True, False], weights=[70, 30], k=1)[0],
                "dailySessions":random.randint(15, 75),
                "enableIdleFee": 0,
                "ratePerHour": round(random.uniform(1.5,4),2),
            }
        }
        return charger_data
    
    #Function to update the shadow
    def updateDeviceShadow(self):
        print("inside updateShadow")
        global shadow_client
        global thingName
        payload = self.get_charger_shadow()
        shadowMessage = iotshadow.ShadowState(reported=payload)
        update_shadow_request = iotshadow.UpdateNamedShadowRequest(state=shadowMessage, thing_name=thingName, shadow_name="chargerusage")
        update_shadow_future = shadow_client.publish_update_named_shadow(request=update_shadow_request, qos=mqtt.QoS.AT_LEAST_ONCE)
        update_shadow_future.add_done_callback(self.on_publish_update_shadow)


