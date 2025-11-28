from socket import *
import argparse
import os
import time
from socket import timeout
"""
UDP文件传输客户端
学号：你的学号
姓名：你的姓名
GitHub地址：https://github.com/Dingdingding110/udp-file-transfer

运行环境：Python 3.6+
依赖库：socket, argparse, os, time (均为Python标准库)

使用说明：
1. 启动服务器：python udpserver.py <端口号>
2. 运行客户端：python udpclient.py <服务器IP> <服务器端口> <文件路径>

示例：
python udpclient.py 127.0.0.1 8080 ./test.txt

功能特点：
- 基于UDP协议实现可靠的文件传输
- 模拟TCP三次握手建立连接
- 模拟TCP四次挥手关闭连接
- 支持大文件分块传输（4KB/块）
- 实时显示传输进度
- 完整的错误处理机制

项目GitHub地址：https://github.com/Dingdingding110/udp-file-transfer
"""
def establish_connection(clientSocket, serverName, serverPort):
    """
    模拟TCP三次握手连接建立过程
    客户端主动发起连接，与服务器完成三次握手
    """
    print("正在建立连接...")

    # 第一次握手：客户端发送SYN包（同步序列编号）到服务器
    # SYN表示客户端请求建立连接
    syn_msg = b"SYN"
    clientSocket.sendto(syn_msg, (serverName, serverPort))
    print("发送: SYN (连接请求)")

    # 等待第二次握手：服务器回复SYN-ACK包
    # 设置5秒超时，防止无限等待
    try:
        clientSocket.settimeout(5.0)
        # 接收服务器的响应
        response, addr = clientSocket.recvfrom(1024)

        # 检查服务器是否回复了正确的SYN-ACK
        if response == b"SYN-ACK":
            print("接收: SYN-ACK (服务器确认连接请求)")
        else:
            # 如果服务器回复了错误的消息，抛出异常
            raise Exception("服务器响应无效")

        # 第三次握手：客户端发送ACK包（确认字符）
        # 确认收到服务器的SYN-ACK，完成连接建立
        ack_msg = b"ACK"
        clientSocket.sendto(ack_msg, (serverName, serverPort))
        print("发送: ACK (确认连接)")

        # 等待服务器的最终连接确认
        final_response, addr = clientSocket.recvfrom(1024)
        if final_response == b"CONNECTION_ESTABLISHED":
            print("连接建立成功！")
            # 连接建立后移除超时限制，文件传输可能需要更长时间
            clientSocket.settimeout(None)
            return True
        else:
            raise Exception("连接建立失败")

    except timeout:
        # 如果在5秒内没有收到服务器响应
        print("连接超时：服务器无响应")
        return False
    except Exception as e:
        print(f"连接失败: {e}")
        return False


def close_connection(clientSocket, serverName, serverPort):
    """
    模拟TCP四次挥手连接释放过程
    在文件传输完成后，优雅地关闭连接
    """
    print("正在关闭连接...")

    try:
        # 第一次挥手：客户端发送FIN包（结束标志）
        # 表示客户端已经没有数据要发送了
        fin_msg = b"FIN"
        clientSocket.sendto(fin_msg, (serverName, serverPort))
        print("发送: FIN (连接关闭请求)")

        # 等待第二次挥手：服务器回复ACK包
        # 确认收到客户端的FIN请求
        clientSocket.settimeout(5.0)
        response, addr = clientSocket.recvfrom(1024)
        if response == b"ACK":
            print("接收: ACK (服务器确认关闭请求)")
        else:
            raise Exception("服务器ACK响应无效")

        # 等待第三次挥手：服务器发送FIN包
        # 表示服务器也没有数据要发送了
        response, addr = clientSocket.recvfrom(1024)
        if response == b"FIN":
            print("接收: FIN (服务器关闭请求)")
        else:
            raise Exception("服务器FIN响应无效")

        # 第四次挥手：客户端发送ACK包
        # 确认收到服务器的FIN请求
        ack_msg = b"ACK"
        clientSocket.sendto(ack_msg, (serverName, serverPort))
        print("发送: ACK (确认服务器关闭请求)")

        # 等待连接关闭确认
        final_response, addr = clientSocket.recvfrom(1024)
        if final_response == b"CONNECTION_CLOSED":
            print("连接关闭成功！")
            return True
        else:
            raise Exception("连接关闭失败")

    except timeout:
        print("连接关闭超时")
        return False
    except Exception as e:
        print(f"连接关闭失败: {e}")
        return False


def main():
    """
    主函数：UDP文件传输客户端
    支持命令行参数，包含完整的连接管理
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='UDP文件传输客户端')
    # 添加必需的参数
    parser.add_argument('server_ip', help='服务器IP地址')
    parser.add_argument('server_port', type=int, help='服务器端口号')
    parser.add_argument('file_path', help='要发送的文件路径')

    # 解析命令行参数
    args = parser.parse_args()

    # 从命令行参数获取服务器信息和文件路径
    serverName = args.server_ip
    serverPort = args.server_port
    file_path = args.file_path

    # 检查要发送的文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在!")
        return

    # 创建UDP socket
    # AF_INET表示使用IPv4地址族
    # SOCK_DGRAM表示使用UDP协议
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    try:
        # 第一步：建立TCP-like连接
        # 在开始文件传输前，先与服务器建立可靠的连接
        if not establish_connection(clientSocket, serverName, serverPort):
            print("无法建立连接，终止程序")
            return

        # 第二步：文件传输阶段
        # 获取纯文件名（不包含路径）
        file_name = os.path.basename(file_path)
        print(f"开始文件传输: {file_name}")

        # 先发送文件名，让服务器知道要创建什么文件
        clientSocket.sendto(file_name.encode(), (serverName, serverPort))

        # 获取文件大小用于显示传输进度
        file_size = os.path.getsize(file_path)
        bytes_sent = 0

        # 以二进制模式打开文件进行读取
        with open(file_path, 'rb') as f:
            while True:
                # 每次读取4096字节（4KB）的数据块
                # 分块读取可以处理大文件，避免内存不足
                data = f.read(4096)
                # 如果读取到文件末尾，data为空，退出循环
                if not data:
                    break
                # 发送数据块到服务器
                clientSocket.sendto(data, (serverName, serverPort))
                # 更新已发送字节数
                bytes_sent += len(data)
                # 计算并显示传输进度
                progress = (bytes_sent / file_size) * 100
                print(f"传输进度: {bytes_sent}/{file_size} 字节 ({progress:.1f}%)", end='\r')

        # 文件内容发送完成后，发送结束标记
        # 告诉服务器文件传输已完成
        clientSocket.sendto(b"<END_OF_FILE>", (serverName, serverPort))
        print(f"\n文件传输完成: {file_name}")

        # 第三步：关闭连接
        # 文件传输完成后，优雅地关闭连接
        close_connection(clientSocket, serverName, serverPort)

    except Exception as e:
        # 捕获并显示任何在传输过程中发生的错误
        print(f"文件传输过程中发生错误: {e}")
    finally:
        # 无论是否发生错误，都确保关闭socket
        clientSocket.close()
        print("Socket已关闭")


if __name__ == "__main__":
    main()