import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import random
import time
from tkinter import *
from math import sin, cos, pi, log

# Heart animation constants
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480
CANVAS_CENTER_X = CANVAS_WIDTH / 2
CANVAS_CENTER_Y = CANVAS_HEIGHT / 2
IMAGE_ENLARGE = 11
HEART_COLOR = "#ff2121"
# 開啟攝影機
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Camera not found.")
    exit()

cap.set(3, 1280)  # 設定寬度
cap.set(4, 720)  # 設定高度

# 初始化手勢檢測器
detector = HandDetector(detectionCon=0.8, maxHands=1)

# 數據映射
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2)  # y = Ax^2 + Bx + C

# Heart animation functions
def heart_function(t, shrink_ratio: float = IMAGE_ENLARGE):
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    x *= shrink_ratio
    y *= shrink_ratio
    x += CANVAS_CENTER_X
    y += CANVAS_CENTER_Y
    return int(x), int(y)

def scatter_inside(x, y, beta=0.15):
    ratio_x = - beta * log(random.random())
    ratio_y = - beta * log(random.random())
    dx = ratio_x * (x - CANVAS_CENTER_X)
    dy = ratio_y * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy

def shrink(x, y, ratio):
    force = -1 / (((x - CANVAS_CENTER_X) ** 2 + (y - CANVAS_CENTER_Y) ** 2) ** 0.6)
    dx = ratio * force * (x - CANVAS_CENTER_X)
    dy = ratio * force * (y - CANVAS_CENTER_Y)
    return x - dx, y - dy

def curve(p):
    return 2 * (2 * sin(4 * p)) / (2 * pi)

class Heart:
    def __init__(self, generate_frame=20):
        self._points = set()
        self._edge_diffusion_points = set()
        self._center_diffusion_points = set()
        self.all_points = {}
        self.build(2000)
        self.random_halo = 1000
        self.generate_frame = generate_frame
        for frame in range(generate_frame):
            self.calc(frame)

    def build(self, number):
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t)
            self._points.add((x, y))

        for _x, _y in list(self._points):
            for _ in range(3):
                x, y = scatter_inside(_x, _y, 0.05)
                self._edge_diffusion_points.add((x, y))

        point_list = list(self._points)
        for _ in range(4000):
            x, y = random.choice(point_list)
            x, y = scatter_inside(x, y, 0.17)
            self._center_diffusion_points.add((x, y))

    @staticmethod
    def calc_position(x, y, ratio):
        force = 1 / (((x - CANVAS_CENTER_X) ** 2 + (y - CANVAS_CENTER_Y) ** 2) ** 0.520)
        dx = ratio * force * (x - CANVAS_CENTER_X) + random.randint(-1, 1)
        dy = ratio * force * (y - CANVAS_CENTER_Y) + random.randint(-1, 1)
        return x - dx, y - dy

    def calc(self, generate_frame):
        ratio = 10 * curve(generate_frame / 10 * pi)
        halo_radius = int(4 + 6 * (1 + curve(generate_frame / 10 * pi)))
        halo_number = int(3000 + 4000 * abs(curve(generate_frame / 10 * pi) ** 2))
        all_points = []

        heart_halo_point = set()
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t, shrink_ratio=11.6)
            x, y = shrink(x, y, halo_radius)
            if (x, y) not in heart_halo_point:
                heart_halo_point.add((x, y))
                x += random.randint(-14, 14)
                y += random.randint(-14, 14)
                size = random.choice((1, 2, 2))
                all_points.append((x, y, size))

        for x, y in self._points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 3)
            all_points.append((x, y, size))

        for x, y in self._edge_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))

        for x, y in self._center_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))

        self.all_points[generate_frame] = all_points

    def render(self, img, render_frame):
        points = self.all_points[render_frame % self.generate_frame]
        for x, y, size in points:
            # 调整心形的位置，将其移到左上角
            adjusted_x = int(x) + 350  # 向右移动100像素
            adjusted_y = int(y) - 50  # 向下移动100像素
            cv2.rectangle(img, 
                        (adjusted_x, adjusted_y), 
                        (adjusted_x + size, adjusted_y + size), 
                        (0, 0, 255), -1)

# 遊戲變數
cx, cy = 250, 250
color = (255,167,153)
counter = 0
score = 0
blocksize = 20  # 初始的馬賽克區塊大小
finished_picture = 0  # 記錄完成模糊效果的圖片數量
paused = False  # 新增：遊戲暫停狀態
pauseStartTime = 0  # 新增：暫停開始時間
pauseDuration = 0  # 新增：累計暫停時間
heart_animation = Heart()
heart_frame = 0

timeStart = time.time()
totalTime = 60
kernel_size = 15
amount = 0.08

# 載入圖片
photo = cv2.imread(r"/Users/nicky/Desktop/Visual code/final/queen1.jpg", cv2.IMREAD_UNCHANGED)
if photo.shape[2] == 3:  # 如果圖片沒有 Alpha 通道
    b, g, r = cv2.split(photo)
    alpha = np.ones(b.shape, dtype=b.dtype) * 255
    photo = cv2.merge((b, g, r, alpha))
scale = 0.3
photo_resized = cv2.resize(photo, (0, 0), fx=scale, fy=scale)

#旋渦名人1
def rotate(img, score):
    # 動態計算旋轉角度
    if score < 23 or score > 28:
        return img  # 不進行旋轉

    # 旋轉角度從 25（23 分）逐步減少到 0（28 分）
    max_degree = 90
    min_degree = 20
    degree = min_degree + (score - 23) * ((max_degree - min_degree) / (29 - 23))


    # 確認是否有 Alpha 通道
    if img.shape[2] == 4:  # 圖片包含 RGBA
        # 分離 RGB 和 Alpha 通道
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]

        # 處理 RGB 和 Alpha 通道
        rotated_bgr = _rotate_channel(bgr, degree)
        rotated_alpha = _rotate_channel(alpha, degree, is_grayscale=True)

        # 合併旋轉後的 RGB 和 Alpha 通道
        rotated_img = cv2.merge((rotated_bgr, rotated_alpha))
    else:
        # 如果圖片沒有 Alpha 通道，直接處理 RGB
        rotated_img = _rotate_channel(img, degree)
    
    return rotated_img

def _rotate_channel(channel, degree, is_grayscale=False):
    # 圖片轉換
    if not is_grayscale:
        channel = cv2.cvtColor(channel, cv2.COLOR_BGR2RGB)  # 轉換為 RGB
    channel = channel.astype(np.float32) / 255.0  # 正規化為浮點數

    # 圖片尺寸
    row, col = channel.shape[:2]
    channel_out = np.copy(channel)

    # 中心點座標
    center_x = (col - 1) / 2.0
    center_y = (row - 1) / 2.0

    # 計算變換
    x_mask, y_mask = np.meshgrid(np.arange(col), np.arange(row))
    xx_dif = x_mask - center_x
    yy_dif = center_y - y_mask

    r = np.sqrt(xx_dif**2 + yy_dif**2)
    theta = np.arctan2(yy_dif, xx_dif)

    theta += r / degree

    x_new = r * np.cos(theta) + center_x
    y_new = center_y - r * np.sin(theta)

    # 整數索引
    int_x = np.floor(x_new).astype(int)
    int_y = np.floor(y_new).astype(int)

    # 防止索引越界
    int_x = np.clip(int_x, 0, col - 1)
    int_y = np.clip(int_y, 0, row - 1)

    # 重映射像素
    for ii in range(row):
        for jj in range(col):
            new_xx = int_x[ii, jj]
            new_yy = int_y[ii, jj]
            channel_out[ii, jj] = channel[new_yy, new_xx]

    # 如果是 RGB，轉回 BGR
    if not is_grayscale:
        channel_out = cv2.cvtColor(channel_out, cv2.COLOR_RGB2BGR)

    return (channel_out * 255).astype(np.uint8)

#旋渦名人2
def rotate1(img):
    # 確認是否有 Alpha 通道
    if img.shape[2] == 4:  # 圖片包含 RGBA
        # 分離 RGB 和 Alpha 通道
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]

        # 處理 RGB 通道
        rotated_bgr = _rotate_channel1(bgr)

        # 處理 Alpha 通道
        rotated_alpha = _rotate_channel1(alpha, is_grayscale=True)

        # 合併旋轉後的 RGB 和 Alpha 通道
        rotated_img = cv2.merge((rotated_bgr, rotated_alpha))
    else:
        # 如果圖片沒有 Alpha 通道，直接處理 RGB
        rotated_img = _rotate_channel1(img)
    
    return rotated_img

def _rotate_channel1(channel, is_grayscale=False):
    # 圖片轉換
    if not is_grayscale:
        channel = cv2.cvtColor(channel, cv2.COLOR_BGR2RGB)  # 轉換為 RGB
    channel = channel.astype(np.float32) / 255.0  # 正規化為浮點數

    # 圖片尺寸
    row, col = channel.shape[:2]
    channel_out = np.copy(channel)
    degree = 20

    # 中心點座標
    center_x = (col - 1) / 2.0
    center_y = (row - 1) / 2.0

    # 計算變換
    x_mask, y_mask = np.meshgrid(np.arange(col), np.arange(row))
    xx_dif = x_mask - center_x
    yy_dif = center_y - y_mask

    r = np.sqrt(xx_dif**2 + yy_dif**2)
    theta = np.arctan2(yy_dif, xx_dif)

    theta += r / degree

    x_new = r * np.cos(theta) + center_x
    y_new = center_y - r * np.sin(theta)

    # 整數索引
    int_x = np.floor(x_new).astype(int)
    int_y = np.floor(y_new).astype(int)

    # 防止索引越界
    int_x = np.clip(int_x, 0, col - 1)
    int_y = np.clip(int_y, 0, row - 1)

    # 重映射像素
    for ii in range(row):
        for jj in range(col):
            new_xx = int_x[ii, jj]
            new_yy = int_y[ii, jj]
            channel_out[ii, jj] = channel[new_yy, new_xx]

    # 如果是 RGB，轉回 BGR
    if not is_grayscale:
        channel_out = cv2.cvtColor(channel_out, cv2.COLOR_RGB2BGR)

    return (channel_out * 255).astype(np.uint8)


# 優化的馬賽克函數
def apply_mosaic(image, block_size):
    height, width = image.shape[:2]
    for i in range(0, height, block_size):
        for j in range(0, width, block_size):
            if i + block_size <= height and j + block_size <= width:
                block = image[i:i + block_size, j:j + block_size]
                avg_color = np.mean(block, axis=(0, 1))
                image[i:i + block_size, j:j + block_size] = avg_color
    return image

# 胡椒鹽噪音處理
def apply_salt_and_pepper(image, amount):
    row, col, _ = image.shape
    salt = int(amount * row * col)
    pepper = int(amount * row * col)

    for _ in range(salt):
        x, y = random.randint(0, row - 1), random.randint(0, col - 1)
        image[x, y] = [255, 255, 255, 255]  # White pixel

    for _ in range(pepper):
        x, y = random.randint(0, row - 1), random.randint(0, col - 1)
        image[x, y] = [0, 0, 0, 255]  # Black pixel

    return image

# 模糊效果的處理函數
def apply_fuzzy(image):
    try:
        fuzzy_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return fuzzy_image
    except Exception as e:
        print(f"Error during fuzzy effect: {e}")
        return image

# 主迴圈
while True:
    success, img = cap.read()
    if not success:
        print("Error: Failed to capture image.")
        break
    img = cv2.flip(img, 1)

    hands, img = detector.findHands(img, draw=False)
    if hands:
        hand = hands[0]
        lmList = hand['lmList']
        bbox = hand['bbox']
        x, y, w, h = bbox

        # 偵測握拳
        fingers = detector.fingersUp(hand)
        if fingers == [0, 0, 0, 0, 0]:
            if not paused:
                paused = True
                pauseStartTime = time.time()
        else:
            if paused:
                paused = False
                pauseDuration += time.time() - pauseStartTime

        cv2.rectangle(img, (x, y), (x + w, y + h), (255,167,153), 3)
    TEXT_COLOR = (255,167,153)
    if score > 30 and finished_picture == 3:
        totalTime = 0
        elapsedTime = totalTime

    # 文本位置調整
        text1_position = (300, 520)  # "Happy New Year!" 文本位置
        text2_position = (410, 660)  # "Press R to restart" 文本位置

    # 愛心動畫位置調整（文本正上方，偏右上角）
        heart_offset_x = 200  # 向右偏移更多
        heart_offset_y = 200  # 向上偏移更多
        heart_center = (
            text1_position[0] + heart_offset_x,  # 文本的中心 X + 偏移
            text1_position[1] - heart_offset_y,  # 文本的中心 Y - 偏移
        )

    # 愛心動畫渲染
        heart_animation.render(img, heart_frame)
        heart_frame = (heart_frame + 1) % heart_animation.generate_frame

    # 文本渲染
        cvzone.putTextRect(img, "Happy New Year!", text1_position, scale=5, offset=30, thickness=7)
        cvzone.putTextRect(img, f'Your Score: {score}', (300, 600), scale=3, offset=20, colorR=TEXT_COLOR)
        cvzone.putTextRect(img, f'Pictures: {int(finished_picture)}', (721, 600), scale=3, offset=20, colorR=TEXT_COLOR)
        cvzone.putTextRect(img, "Press R to restart", text2_position, scale=3, offset=10, colorR=(153, 153, 255))
    elif paused:
        cvzone.putTextRect(img, "PAUSE", (550, 350), scale=5, offset=30, thickness=7, colorR=(0, 0, 255))
    else:
        elapsedTime = time.time() - timeStart - pauseDuration
        if elapsedTime < totalTime:
            if hands:
                hand = hands[0]
                lmList = hand['lmList']
                bbox = hand['bbox']
                x, y, w, h = bbox

                x1, y1, _ = lmList[5]
                x2, y2, _ = lmList[17]

                distance = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

                A, B, C = coff
                distanceCM = A * distance ** 2 + B * distance + C

                if distanceCM < 40:
                    if x < cx < x + w and y < cy < y + h:
                        counter = 1

                cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10), colorR=TEXT_COLOR)

            if counter:
                counter += 1
                color = (0, 255, 0)
                if counter == 3:
                    cx = random.randint(100, 850)
                    cy = random.randint(100, 600)
                    color = (255,167,153)
                    score += 1
                    counter = 0

                    if blocksize > 2:
                        blocksize -= 2
                    if blocksize == 2 and kernel_size > 3:
                        kernel_size -= 2
                    if kernel_size == 3 and amount > 0:
                        amount -= 0.01

            cv2.circle(img, (cx, cy), 30, color, cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
            cv2.circle(img, (cx, cy), 30, (50, 50, 50), 2)

            position = (980, 450)

            if score == 0:
                photo_rotate = rotate1(photo_resized.copy())
                photo_with_mosaic = apply_mosaic(photo_rotate.copy(), blocksize)
                photo_with_noise = apply_salt_and_pepper(photo_with_mosaic.copy(), amount)
                photo_fuzzy = apply_fuzzy(photo_with_noise.copy())
                img = cvzone.overlayPNG(img, photo_fuzzy, position)
            elif score >= 23 and score <= 30:
                    photo_rotate = rotate(photo_resized.copy(), score)
                    img = cvzone.overlayPNG(img, photo_rotate, position)
                    if finished_picture == 2:
                        finished_picture = 3
            else:

                if blocksize == 2:
                    if finished_picture == 0:
                        finished_picture = 1

                    if kernel_size > 3:
                        photo_rotate = rotate1(photo_resized.copy())
                        photo_resized_noise = apply_salt_and_pepper(photo_rotate.copy(), amount)
                        photo_resized_fuzzy = apply_fuzzy(photo_resized_noise.copy())
                        img = cvzone.overlayPNG(img, photo_resized_fuzzy, position)

                    if kernel_size == 3 and amount > 0:
                        if finished_picture == 1:
                            finished_picture = 2
                        photo_rotate = rotate1(photo_resized.copy())
                        photo_resized_noise = apply_salt_and_pepper(photo_rotate.copy(), amount)
                        img = cvzone.overlayPNG(img, photo_resized_noise, position)
                    else:
                        photo_rotate = rotate1(photo_resized.copy())
                        photo_resized_noise = apply_salt_and_pepper(photo_rotate.copy(), amount)
                        img = cvzone.overlayPNG(img, photo_resized_noise, position)

                else:
                    photo_rotate = rotate1(photo_resized.copy())
                    photo_resized_mosaic = apply_mosaic(photo_rotate.copy(), blocksize)
                    photo_resized_noise = apply_salt_and_pepper(photo_resized_mosaic.copy(), amount)
                    photo_resized_fuzzy = apply_fuzzy(photo_resized_noise.copy())
                    img = cvzone.overlayPNG(img, photo_resized_fuzzy, position)

            cvzone.putTextRect(img, f'Time: {int(totalTime - elapsedTime)}', (1000, 75), scale=3, offset=20, colorR=TEXT_COLOR)
            cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60, 75), scale=3, offset=20, colorR=TEXT_COLOR)
            cvzone.putTextRect(img, f'Picture:', (1000, 410), scale=2, offset=20, colorR=TEXT_COLOR)

        else:
            cvzone.putTextRect(img, f'Game over:', (400, 280), scale=5, offset=30, thickness=7, colorR=TEXT_COLOR)
            cvzone.putTextRect(img, f'Your Score: {score}', (455, 410), scale=3, offset=20, colorR=TEXT_COLOR)
            cvzone.putTextRect(img, f'Pictures: {int(finished_picture)}', (490, 500), scale=3, offset=20, colorR=TEXT_COLOR)
            cvzone.putTextRect(img, f'Press R to restart', (400, 585), scale=3, offset=10, colorR=(153, 153, 255))

    cv2.imshow("Image", img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        counter = 0
        score = 0
        blocksize = 20
        finished_picture = 0
        paused = False
        timeStart = time.time()
        pauseStartTime = 0
        pauseDuration = 0
        amount = 0.08
        kernel_size = 15
        totalTime = 60
        heart_frame = 0

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()