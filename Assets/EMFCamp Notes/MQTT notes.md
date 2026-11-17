# Understanding the data 

Example data with guessed colulumn labels 

[Reppo With data link](https://github.com/GraemeCaiger/Data-Engineering-Learning-Projects/tree/main/EMF_Camp/Raw_data/emf-mqtt-dump)


|topic|payload_EcodededBase64|MQTT Quality of Service (QoS)|Retained-message flag|Retained-message flag|TimeStamp_Unix?|ElapsedTimeSincePrevious(s)|
|-----|----------------------|-----------------------------|---------------------|---------------------|---------------|---------------------------|
|open/jungle-breaks-served|	NDE=|	0	|FALSE	|1784160001.638832	|1.6994733810424805|
open/wnstlyktrasdi|	MDExMDExMTE=|	0	|FALSE	|1784160003.266492	|1.627659797668457 |
open/wnstlyktrasdi|	MDExMTAxMDE=|	0	|FALSE	|1784160007.2672062	|4.000714302062988 |
open/view-the-full-schedule-timeline-at|	aHR0cHM6Ly9oZWFsdy5pbmc=	|0	|FALSE|	1784160008.0491984|	0.7819921970367432|

__<u>note</u>__ :<br>
"It was recorded using https://github.com/rpdswtk/mqtt_recorder and the same tool can
be used to play the data back to an mqtt server to relive the weekend :)"
