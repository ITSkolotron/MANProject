from PyQt5 import QtCore, QtGui, QtWidgets
from Project import Ui_Project
import cv2
import numpy as np
from PIL import Image
import os
import sys
import subprocess
import time
from twilio.rest import Client
import shutil
import socket

app = QtWidgets.QApplication(sys.argv)
Form = QtWidgets.QWidget()
ui = Ui_Project()
ui.setupUi(Form)
Form.show()
def Scan ():
        cam = cv2.VideoCapture(0)
        cam.set(3, 640)  # set video width
        cam.set(4, 480)  # set video height

        folder1 = 'trainer'
        for the_file1 in os.listdir(folder1):
            file_path1 = os.path.join(folder1, the_file1)
            try:
                if os.path.isfile(file_path1):
                    os.unlink(file_path1)
            except Exception as e:
                print(e)
        face_detector = cv2.CascadeClassifier(
            r'C:\Users\1\git\opencv\data\haarcascades_cuda\haarcascade_frontalface_alt.xml')

        # For each person, enter one numeric face id
        #face_id = input('\n enter user id end press  ==>  ')
        face_id = "1"

        ui.lineEdit.setText("[INFO] Initializing face capture. Look the camera and wait ...")
        # Initialize individual sampling face count
        f = open("data.txt", "r",encoding='cp1251')
        count = f.read()
        count = int(count)
        countprog = count
        f.close()
        print("1")
        while (True):
            ret, img = cam.read()
            # flip video image vertically
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                countprog += 1

                # Save the captured image into the datasets folder
                cv2.imwrite("dataset/User." + str(face_id) + '.' + str(
                    countprog) + ".jpg", gray[y:y + h, x:x + w])

                cv2.imshow('image', img)

            k = cv2.waitKey(100) & 0xff  # Press 'ESC' for exiting video
            if k == 27:
                break
            elif countprog >= count + 30:  # Take 30 face sample and stop video
                break
            print("2")
        # Do a bit of cleanup
        ui.lineEdit.setText("[INFO] Exiting Program and cleanup stuff")
        cam.release()
        cv2.destroyAllWindows()
        path = 'dataset'

        f = open("data.txt", "w")
        countprog = str(countprog)
        f.write(countprog)
        f.close()
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        detector = cv2.CascadeClassifier(
            r"C:\Users\1\git\opencv\data\haarcascades_cuda\haarcascade_frontalface_default.xml")

        # function to get the images and label data
        def getImagesAndLabels(path):
            imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
            faceSamples = []
            ids = []
            for imagePath in imagePaths:
                PIL_img = Image.open(imagePath).convert('L')  # convert it to grayscale
                img_numpy = np.array(PIL_img, 'uint8')
                id = int(os.path.split(imagePath)[-1].split(".")[1])
                faces = detector.detectMultiScale(img_numpy)
                for (x, y, w, h) in faces:
                    faceSamples.append(img_numpy[y:y + h, x:x + w])
                    ids.append(id)
            return faceSamples, ids

        ui.lineEdit.setText("[INFO] Training faces. It will take a few seconds. Wait ...")
        faces, ids = getImagesAndLabels(path)
        recognizer.train(faces, np.array(ids))

        # Save the model into trainer/trainer.yml

        recognizer.save('trainer/trainer.yml')  # recognizer.save() worked on Mac, but not on Pi

        # Print the numer of faces trained and end program
        ui.lineEdit.setText("[INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))

def Start ():
    try:
        ui.lineEdit.setText("Program starts working")
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('trainer/trainer.yml')
        cascadePath = r"C:\Users\1\git\opencv\data\haarcascades_cuda\haarcascade_frontalface_default.xml"
        faceCascade = cv2.CascadeClassifier(cascadePath)
        # Twilio config

        sms_sent = False
        twilio_account_sid = 'ACdd6914d657da2353b514f0b1fe0d7757'
        twilio_auth_token = '48d10574c18f64bc1cb07fe29615b890'
        twilio_phone_number = '+18043966595'
        destination_phone_number = '+380994002620'
        client = Client(twilio_account_sid, twilio_auth_token)

        font = cv2.FONT_HERSHEY_SIMPLEX
        counter = 0
        identification_count = 0
        # iniciate id counter
        id = 0

        # names related to ids: example ==> Marcelo: id=1,  etc
        names = ['None', 'Illia']

        # Initialize and start realtime video capture
        cam = cv2.VideoCapture(0)
        cam.set(3, 800)  # set video widht
        cam.set(4, 800)  # set video height

        # Define min window size to be recognized as a face
        minW = 0.1 * cam.get(3)
        minH = 0.1 * cam.get(4)

        while True:

            ret, img = cam.read()
            # img = cv2.flip(img, -1)  # Flip vertically
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(int(minW), int(minH)),
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

                # Check if confidence is less them 100 ==> "0" is perfect match
                if (confidence <= 55 and confidence > 20):  #
                    id = names[id]
                    confidence = "  {0}%".format(round(100 - confidence))
                    print(confidence)
                    identification_count += 1
                else:
                    id = "unknown"
                    confidence = "  {0}%".format(round(100 - confidence))
                    counter += 1
                    identification_count -= 1
                    sms_sent = False
                if counter > 30 and identification_count < 0:
                    try:
                        socket.gethostbyaddr('www.google.com')
                        if not sms_sent:
                            print("SENDING SMS!!!")
                            message = client.messages.create(
                                body="Unknown user detected!!! "
                                     "Your PC will be turn off in 10 seconds",
                                from_=twilio_phone_number,
                                to=destination_phone_number
                            )
                            # time.sleep(10)
                            #subprocess.call(["shutdown", "/l"])
                            counter = 0
                        sms_sent = True
                    except socket.gaierror:
                        ui.lineEdit.setText("Wifi connection lost")
                        print("shutdown")
                        #subprocess.call(["shutdown", "/l"])

                cv2.putText(img, str(id), (x + 5, y - 5), font, 1, (255, 255, 255), 2)
                cv2.putText(img, str(confidence), (x + 5, y + h - 5), font, 1, (255, 255, 0), 1)

            cv2.imshow('camera', img)
            k = cv2.waitKey(10) & 0xff  # Press 'ESC' for exiting video
            if k == 27:
                break

        # Do a bit of cleanup
        print("\n [INFO] Exiting Program and cleanup stuff")
        cam.release()
        cv2.destroyAllWindows()
    except cv2.error:
        ui.lineEdit.setText("Files dataset and trainer must be full, not empty")

def Delete ():
    folder = 'dataset'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    folder1 = 'trainer'
    for the_file1 in os.listdir(folder1):
        file_path1 = os.path.join(folder1, the_file1)
        try:
            if os.path.isfile(file_path1):
                os.unlink(file_path1)
        except Exception as e:
            print(e)
    f = open("data.txt","w")
    f.write("0")
    f.close()
    ui.lineEdit.setText("Cache was deleted!")

def Add():
    pass



ui.pushButton_4.clicked.connect(Scan)
ui.pushButton_2.clicked.connect(Delete)
ui.pushButton.clicked.connect(Start)
ui.pushButton_3.clicked.connect(Add)
sys.exit(app.exec_())