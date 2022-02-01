from knx import Knx

knx = Knx()

adressList = []
objectList = []
j=0
k=0

for i in range(0, 15):
    print("now doing: " + str(i) + "/" + str(j) + "/" + str(k))
    for j in range(0, 7):
        for k in range(0, 255):
            knx.getState("%s/%s/%s"%(i,j,k))
            knx.read()
            while not knx.readBuffer.empty():
                data = knx.readBuffer.get_nowait()
                try:
                    adressList.index(data[1])
                except:
                    adressList.append(data[1])
                    objectList.append(data)

print(adressList)
print(objectList)