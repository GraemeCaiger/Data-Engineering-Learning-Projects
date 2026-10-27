import paho.mqtt.client as mqtt
import time


MQTT_Broker = "mqtt.emf.camp"
MQTT_Port = 1883
MQTT_Topic = "emf/weather/#"
Listen_Seconds = 30



# Example function for publishing a message to an MQTT topic
def MQTT_Publish(topic, payload, waittime=1):
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="Project_Publisher",
    )
    client.connect(MQTT_Broker, MQTT_Port)
    client.loop_start()
    try:
        result = client.publish(topic, payload)
        result.wait_for_publish(timeout=waittime)
        if not result.is_published():
            raise TimeoutError(f"Publish to {topic!r} was not confirmed in time")
    finally:
        client.disconnect()
        client.loop_stop()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"MQTT connection rejected: {reason_code}")
        return

    print(f"Connected to {MQTT_Broker}:{MQTT_Port}")
    result, _ = client.subscribe(MQTT_Topic)
    if result == mqtt.MQTT_ERR_SUCCESS:
        print(f"Subscribed to {MQTT_Topic}; listening for {Listen_Seconds} seconds")
    else:
        print(f"Could not subscribe to {MQTT_Topic}: {mqtt.error_string(result)}")


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8", errors="replace")
    print(f"Received message on topic {message.topic}: {payload}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="Project_Listener",
)
client.on_connect = on_connect
client.on_message = on_message
try:
    client.connect(MQTT_Broker, MQTT_Port, keepalive=60)
except TimeoutError as exc:
    raise SystemExit(
        f"Could not reach MQTT broker at {MQTT_Broker}:{MQTT_Port}. "
        "Check your network connection and whether the EMF broker is currently online."
    ) from exc
client.loop_start()
try:
    time.sleep(Listen_Seconds)
finally:
    client.disconnect()
    client.loop_stop()https://mqttx.app/