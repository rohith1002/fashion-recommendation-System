import os
import cv2
def create_wardrobe(name):
    if os.path.exists("users") == False:
        os.mkdir("users")
    path="users/"+name
    os.mkdir(path)

def upload(type,color,path_user,img):
    #path_occasion=path_user+"/"+occasion
    #path_type=path_occasion+"/"+type
    path_type=path_user+"/"+type
    path_color=path_type+"/"+color
    path_party=path_user+"/party"
    path_party_color=path_party+"/"+color
    print(os.getcwd())
    # if os.path.exists(path_occasion) == False:
    #     print(os.getcwd())
    #     os.mkdir(path_occasion)
    if os.path.exists(path_type) == False:
        os.mkdir(path_type)
    if os.path.exists(path_color) == False:
        os.mkdir(path_color)
    if os.path.exists(path_party) == False:
        os.mkdir(path_party)
   
    os.chdir(path_color)
    if len(os.listdir()) == 0:
        i=1
    else:
       i=int((os.listdir()[len(os.listdir())-1]).rstrip(".jpg"))+1
    cv2.imwrite(str(i)+".jpg",img)
    os.chdir("../../../..")

    if type == "shirt" or type == "t-shirt":
            if os.path.exists(path_party_color) == False:
                os.mkdir(path_party_color)
            os.chdir(path_party_color)
            if len(os.listdir()) == 0:
                i=1
            else:
                i=int((os.listdir()[len(os.listdir())-1]).rstrip(".jpg"))+1
            cv2.imwrite(str(i)+".jpg",img)
            os.chdir("../../../..")