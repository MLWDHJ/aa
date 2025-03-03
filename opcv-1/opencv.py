import cv2

#加载人脸检测的分类器文件
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

#读取图片
img = cv2.imread('vsproject\picture material\selfie.jpg') 

#转换为灰度图（人脸检测需要）
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#检测人脸
faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

#在图片上画框标出人脸
for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

#显示结果
cv2.imshow('Face Detection', img)
cv2.waitKey(0)          # 按任意键关闭窗口
cv2.destroyAllWindows()