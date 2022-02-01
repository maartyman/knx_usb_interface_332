from lights import Element

#mqtt
mqtt_username = "" 
mqtt_password = "" 
mqtt_adress = "" 
mqtt_port = 1883 
mqtt_keep_alive = 60 

#other
doGeneralUpdate = False
generalUpadteFrequency = 480 #every x seconds

LIGHTS = {
    # mqtt topic                :Element(             A discription             ,groupadress,non binary output,second groupadress (not required)),
    "/light/living/big"         :Element(   "The big lights in the living"      ,"1/1/1"    ,True            ,"2/1/8"                           ),
    "/outlet/living/floor"      :Element(   "The floor outlets in the living"   ,"2/1/1"    ,False)
}