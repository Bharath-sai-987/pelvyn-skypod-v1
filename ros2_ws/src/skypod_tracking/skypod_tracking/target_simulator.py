import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Bool


class SkyPodTargetSimulator(Node):

    def __init__(self):
        super().__init__('skypod_target_simulator')

        self.position_pub = self.create_publisher(
            Float32MultiArray,
            '/skypod/target_position',
            10
        )

        self.detected_pub = self.create_publisher(
            Bool,
            '/skypod/target_detected',
            10
        )

        self.step = 0

        self.timer = self.create_timer(
            0.2,
            self.publish_target
        )

        self.get_logger().info(
            'SkyPod target simulator started'
        )

    def publish_target(self):

        # Simulate a moving target in a 640 x 480 image.
        x = 320.0 + 150.0 * math.sin(self.step * 0.1)
        y = 240.0 + 80.0 * math.cos(self.step * 0.1)

        position = Float32MultiArray()
        position.data = [x, y]

        detected = Bool()
        detected.data = True

        self.position_pub.publish(position)
        self.detected_pub.publish(detected)

        self.step += 1


def main(args=None):

    rclpy.init(args=args)

    node = SkyPodTargetSimulator()

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
