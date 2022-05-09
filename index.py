import tornado
import tornado.web
import tornado.ioloop
import db
import uuid
from pathlib import Path
import base64
import os
import numpy as np
import cv2
import torch
import time
#from PIL import Image

class LogoDetectionHandler(tornado.web.RequestHandler):

    async def detect():
      
        start_time = time.time()

        model = torch.hub.load('ultralytics/yolov5', 'custom', path='model/best.pt')  # local model

        results = model(im, size=640)
        
        dictImg = {}

        for index, row in results.pandas().xyxy[0].iterrows():
         #print(row['xmin'], row['ymin'], row['xmax'], row['ymax'], row['confidence'])
          dictImg["xmin"] = int(row['xmin'])
          dictImg["ymin"] = int(row['ymin'])
          dictImg["xmax"] = int(row['xmax'])
          dictImg["ymax"] = int(row['ymax'])
          dictImg["name"] =  row['name']
          dictImg["confidence"] = float(row['confidence'])
        
        img = np.array(im)

        imgdetect = cv2.rectangle(img, (dictImg["xmin"],dictImg["ymin"]), (dictImg["xmax"], dictImg["ymax"]), (0,0,255), 3)
        imgdetect = cv2.putText(imgdetect, str(dictImg["confidence"]), (dictImg["xmin"],dictImg["ymin"]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 1, cv2.LINE_AA, False)
        imgdetect = cv2.putText(imgdetect, str(dictImg["name"]), (dictImg["xmax"], dictImg["ymax"]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 1, cv2.LINE_AA, False)
        
       
        result_img = "result/"+path_img

        # CV2
        if not cv2.imwrite(result_img, imgdetect):
            raise Exception("Could not write image")
        else: 
            print("wrote image")
        
        # Elapse-time
        
        end_time = time.time()
        eltime = end_time-start_time
        #LabelName=dictImg["name"] ,
        # eltime = end-start_time,strImg = dictImg["confidence"], pathImg = r"result/rs1.jpg")
       
        dictImg["eltime"] = eltime

        return dictImg


#https://stackoverflow.com/questions/55200507/how-i-can-convert-a-list-of-integers-to-an-image       
#https://pyimagesearch.com/2021/08/02/pytorch-object-detection-with-pre-trained-networks/

class uploadImgHandler(tornado.web.RequestHandler):
    
    async def get(self):
        self.render("templates/index.html")
    
    async def post(self):

        files = self.request.files["imgFile"]

        for f in files:
            fh = open(f"public/img/{f.filename}", "wb")
            fh.write(f.body)
            fh.close()
        
        #  uncommit
        global path_img
        path_img = "public/img/"+f.filename
       
        global im
        im = cv2.imread(path_img)
        
       
        temp_var = await LogoDetectionHandler.detect()

        #print("confidence: ", temp_var["confidence"])

        #  uncommit

        # lay duong dan den thu muc img chua hinh anh   
        #source_path = Path(__file__).resolve()
       # source_dir = source_path.parent

        #pathig = "http://localhost:8088" + r"/public/img/" + f.filename
        
        pathig = r"result/public/img/" + str(f.filename)

        # tao uuid cho hinh anh
        id = uuid.uuid1()
        

        lists_of_logo = {
             "logo_name" : "amazon",
             "bounding_box" : str(temp_var["xmin"])+","+str(temp_var["ymin"])+","+str(temp_var["xmax"])+","+str(temp_var["ymax"]),
             "confidence" : temp_var["confidence"]
        }

        logo_detection_result = {
        
         "elapse-time" : temp_var["eltime"],
         "lists_of_logo" :  lists_of_logo
        
        }

        x = {
              "_id": str(id),
              "pathimg": str(pathig),
              "logo_detection_result" : logo_detection_result
        }
        
        #the result is a JSON string:
        z = db.mycol.insert_one(x)
        print(z)
        
       
        for y in db.mycol.find():
            print(y)

        self.write(x["_id"])
        

class downloadImgHandler(tornado.web.RequestHandler):

    async def post(self):
        
        uuidImg = self.get_argument("uuidImg","")
        
        myquery = {"_id": str(uuidImg)}

        exemyquery = db.mycol.find_one(myquery,{'_id':0,'pathimg':1,'logo_detection_result':2})
        
        message = exemyquery["pathimg"]

        message_bytes = message.encode('ascii')
        
        base64_bytes = base64.b64encode(message_bytes)
        
        decode_img = base64.b64decode(base64_bytes)

        self.render("templates/showimg.html" , decode_img = decode_img, exemyquery = exemyquery)


if (__name__ == "__main__"):

    app = tornado.web.Application([
        ("/", uploadImgHandler),
        ("/public/img/(.*)", tornado.web.StaticFileHandler, {"path": "public/img"}),
        ("/result/public/img/(.*)", tornado.web.StaticFileHandler, {"path": "result/public/img"}),
        ("/download",downloadImgHandler),
        ("/detect",LogoDetectionHandler),
        
    ])

    TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), 'templates')
    
    settings = {
            'template_path': TEMPLATES_ROOT,
        }
        
    app.listen(8888)
    print("Listening on port 8888")
    tornado.ioloop.IOLoop.instance().start()