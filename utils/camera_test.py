import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

print("Opened:", cap.isOpened())

ret, frame = cap.read()
print("Frame read:", ret)

if ret:
    cv2.imshow("Camera Test", frame)
    cv2.waitKey(3000)  # show for 3 seconds

cap.release()
cv2.destroyAllWindows()