import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Bool


class SkyPodPanTiltController(Node):

    def __init__(self):
        super().__init__('skypod_pan_tilt_controller')

        self.pan = 0.0
        self.tilt = 0.0
        self.target_detected = False

        # Subscribe to target position
        self.position_sub = self.create_subscription(
            Float32MultiArray,
            '/skypod/target_position',
            self.position_callback,
            10
        )

        # Subscribe to target detection status
        self.detected_sub = self.create_subscription(
            Bool,
            '/skypod/target_detected',
            self.detected_callback,
            10
        )

        # Publish simulated pan/tilt angles
        self.angle_pub = self.create_publisher(
            Float32MultiArray,
            '/skypod/pan_tilt',
            10
        )

        self.get_logger().info(
            'SkyPod pan/tilt controller started'
        )

    def detected_callback(self, msg):
        self.target_detected = msg.data

    def position_callback(self, msg):

        if not self.target_detected:
            return

        if len(msg.data) < 2:
            return

        x = msg.data[0]
        y = msg.data[1]

        # Camera image centre: 320 x 240 pixels
        error_x = x - 320.0
        error_y = y - 240.0

        # Simulated proportional pan/tilt control
        self.pan = max(
            -45.0,
            min(45.0, -error_x * 0.05)
        )

        self.tilt = max(
            -30.0,
            min(30.0, error_y * 0.05)
        )

        angles = Float32MultiArray()
        angles.data = [self.pan, self.tilt]

        self.angle_pub.publish(angles)

        self.get_logger().info(
            f'Target: ({x:.1f}, {y:.1f}) | '
            f'Error: ({error_x:.1f}, {error_y:.1f}) | '
            f'Pan: {self.pan:.2f} deg | '
            f'Tilt: {self.tilt:.2f} deg'
        )


def main(args=None):
    rclpy.init(args=args)

    node = SkyPodPanTiltController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
