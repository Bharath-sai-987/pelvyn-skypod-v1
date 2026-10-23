import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Bool

class SkyPodUDPReceiver(Node):

    def __init__(self):
        super().__init__('skypod_udp_receiver')

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

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 5005))
        self.sock.settimeout(0.5)

        self.timer = self.create_timer(0.02, self.receive_data)

        self.get_logger().info('SkyPod UDP receiver listening on port 5005')

    def receive_data(self):
        try:
            data, _ = self.sock.recvfrom(1024)
            x_str, y_str, detected_str = data.decode().strip().split(',')

            x = float(x_str)
            y = float(y_str)
            detected = detected_str == '1'

            position = Float32MultiArray()
            position.data = [x, y]
            self.position_pub.publish(position)

            status = Bool()
            status.data = detected
            self.detected_pub.publish(status)

        except socket.timeout:
            pass
        except (ValueError, UnicodeDecodeError):
            self.get_logger().warning('Received invalid target data')

    def destroy_node(self):
        self.sock.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SkyPodUDPReceiver()

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
