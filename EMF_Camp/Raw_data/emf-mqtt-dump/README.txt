This is a dump of all data posted to the mqtt.emf.camp mqtt server over EMFCamp 2026.

It was recorded using https://github.com/rpdswtk/mqtt_recorder and the same tool can
be used to play the data back to an mqtt server to relive the weekend :)

Github has a 100Mb file size limit, so concatenate and then decompress the
mqtt.emf.camp.csv.gz.1 & mqtt.emf.camp.csv.gz.2 files.

mqttrecorder was run with the --encode_b64 option so all messages are base64 encoded.

should you want them, the columns are msg.topic, payload, msg.qos, msg.retain, time_now, time_delta
