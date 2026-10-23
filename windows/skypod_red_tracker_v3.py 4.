"""
SkyPod V1 — improved red/pink target detector (OpenCV)
- Uses stricter saturation/hue filtering to reduce skin/hand false positives.
- Uses contour shape/size filters and temporal target continuity.
- Sends x,y,status over UDP to the existing ROS 2 receiver.
- This is colour-based: other similarly coloured objects can still be detected.
Keys: Q/Esc quit, C clear target lock, M toggle mask.
"""

import socket
import sys
import time
import cv2
import numpy as np

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
CAMERA_INDEX = 0

# Your target looks bright pink/red. Higher saturation helps reject skin tones.
# OpenCV HSV hue is 0..179. Adjust these if the object is missed.
PINK_RED_LOW = np.array([160, 135, 65], dtype=np.uint8)
PINK_RED_HIGH = np.array([179, 255, 255], dtype=np.uint8)
PURE_RED_LOW = np.array([0, 155, 65], dtype=np.uint8)
PURE_RED_HIGH = np.array([7, 255, 255], dtype=np.uint8)

MIN_AREA = 700
MAX_AREA_RATIO = 0.12       # reject very large merged regions
MIN_SATURATION = 135
MIN_CIRCULARITY = 0.06      # broad enough for irregular toy/object shapes
MAX_LOST_FRAMES = 12
SMOOTHING = 0.28
MAX_JUMP_RATIO = 0.22
SHOW_MASK = True


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = None
    locked_center = None
    smooth_center = None
    lost_frames = 99
    show_mask = SHOW_MASK

    try:
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            print("ERROR: Webcam could not be opened.")
            return 1

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        print("SkyPod strict pink/red target detector started.")
        print("Place the bright red/pink object clearly in view.")
        print("Q=quit, C=clear target, M=toggle mask.")
        print(f"Sending UDP coordinates to {UDP_IP}:{UDP_PORT}")

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("WARNING: Failed to read webcam frame.")
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            center_x, center_y = width // 2, height // 2
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Focus on saturated pink/red rather than broad red hues.
            mask_pink = cv2.inRange(hsv, PINK_RED_LOW, PINK_RED_HIGH)
            mask_red = cv2.inRange(hsv, PURE_RED_LOW, PURE_RED_HIGH)
            mask = cv2.bitwise_or(mask_pink, mask_red)

            # Erode once to separate nearby regions, then remove speckles.
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
            frame_area = float(width * height)
            diagonal = (width * width + height * height) ** 0.5
            candidates = []

            for contour in contours:
                area = float(cv2.contourArea(contour))
                if area < MIN_AREA or area > frame_area * MAX_AREA_RATIO:
                    continue

                x, y, box_w, box_h = cv2.boundingRect(contour)
                if box_w < 12 or box_h < 12:
                    continue

                # Require the region itself to be strongly saturated.
                roi = hsv[y:y + box_h, x:x + box_w]
                if roi.size == 0:
                    continue
                saturation = float(np.mean(roi[:, :, 1]))
                if saturation < MIN_SATURATION:
                    continue

                perimeter = cv2.arcLength(contour, True)
                circularity = (4.0 * np.pi * area / (perimeter * perimeter)
                               if perimeter > 0 else 0.0)
                if circularity < MIN_CIRCULARITY:
                    continue

                # Reject thin lines and extreme merged blobs.
                aspect = box_w / float(box_h)
                if aspect < 0.18 or aspect > 3.5:
                    continue

                cx, cy = x + box_w // 2, y + box_h // 2
                candidates.append({
                    "area": area, "box": (x, y, box_w, box_h),
                    "center": (cx, cy), "circularity": circularity
                })

            selected = None
            if candidates:
                if locked_center is not None and lost_frames <= MAX_LOST_FRAMES:
                    max_jump = diagonal * MAX_JUMP_RATIO
                    nearby = []
                    for c in candidates:
                        cx, cy = c["center"]
                        dist = ((cx - locked_center[0]) ** 2 +
                                (cy - locked_center[1]) ** 2) ** 0.5
                        if dist <= max_jump:
                            nearby.append((dist, c))
                    if nearby:
                        selected = min(nearby, key=lambda pair: pair[0])[1]

                if selected is None and (locked_center is None or lost_frames > MAX_LOST_FRAMES):
                    # Acquire a compact saturated region; do not choose the largest by area alone.
                    selected = max(
                        candidates,
                        key=lambda c: c["area"] * (0.5 + c["circularity"])
                    )

            target_x, target_y, status = center_x, center_y, 0
            cv2.drawMarker(frame, (center_x, center_y), (255, 255, 0),
                           cv2.MARKER_CROSS, 20, 2)

            if selected is not None:
                x, y, box_w, box_h = selected["box"]
                raw_x, raw_y = selected["center"]

                if smooth_center is None or lost_frames > MAX_LOST_FRAMES:
                    sx, sy = float(raw_x), float(raw_y)
                else:
                    sx = SMOOTHING * raw_x + (1.0 - SMOOTHING) * smooth_center[0]
                    sy = SMOOTHING * raw_y + (1.0 - SMOOTHING) * smooth_center[1]

                smooth_center = (sx, sy)
                locked_center = (int(round(sx)), int(round(sy)))
                target_x, target_y = locked_center
                status = 1
                lost_frames = 0

                # Tight bounding box around the selected colour contour.
                cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), (0, 255, 0), 2)
                cv2.circle(frame, (target_x, target_y), 4, (0, 0, 255), -1)
                cv2.putText(frame, "RED/PINK TARGET", (x, max(22, y - 7)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                cv2.putText(frame, f"Target: ({target_x}, {target_y})",
                            (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                            (255, 255, 255), 2)
                cv2.putText(frame,
                            f"Pixel error X={target_x-center_x} Y={target_y-center_y}",
                            (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (255, 255, 255), 2)
            else:
                lost_frames += 1
                cv2.putText(frame, "SEARCHING FOR RED/PINK OBJECT",
                            (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                            (0, 165, 255), 2)
                if lost_frames > MAX_LOST_FRAMES:
                    locked_center = None
                    smooth_center = None

            try:
                sock.sendto(f"{target_x},{target_y},{status}".encode("utf-8"),
                            (UDP_IP, UDP_PORT))
            except OSError as exc:
                print("UDP send warning:", exc)

            cv2.imshow("SkyPod Red Target Tracking", frame)
            if show_mask:
                cv2.imshow("Red Detection Mask", mask)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("c"):
                locked_center = None
                smooth_center = None
                lost_frames = 99
                print("Target lock cleared.")
            if key == ord("m"):
                show_mask = not show_mask
                if not show_mask:
                    cv2.destroyWindow("Red Detection Mask")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as exc:
        print("ERROR:", repr(exc))
        return 1
    finally:
        if cap is not None:
            cap.release()
        sock.close()
        cv2.destroyAllWindows()

    print("SkyPod tracker stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
