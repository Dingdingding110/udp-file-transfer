from socket import *
import argparse
import os
import time
from datetime import datetime
from socket import timeout
"""
UDP文件传输服务器
学号：241002523
姓名：丁晨
GitHub地址：https://github.com/Dingdingding110/udp-file-transfer

运行环境：Python 3.6+
依赖库：socket, argparse, os, time, datetime (均为Python标准库)

使用说明：
1. 启动服务器：python udpserver.py <端口号>
2. 运行客户端：python udpclient.py <服务器IP> <服务器端口> <文件路径>

示例：
python udpserver.py 8080

功能特点：
- 基于UDP协议实现可靠的文件传输
- 模拟TCP三次握手建立连接
- 模拟TCP四次挥手关闭连接
- 自动生成带时间戳的文件名，避免覆盖
- 支持多客户端顺序处理
- 完整的错误处理机制

项目GitHub地址：https://github.com/Dingdingding110/udp-file-transfer
"""
def handle_connection(serverSocket):
    """
    处理连接建立过程
    服务器等待客户端发起连接，完成三次握手
    返回：客户端地址和错误信息
    """
    print("等待客户端连接...")

    try:
        # 设置30秒的连接等待超时
        # 如果30秒内没有客户端连接请求，抛出timeout异常
        serverSocket.settimeout(30.0)

        # 等待第一次握手：客户端发送SYN包
        # 这是连接建立的开始
        syn_msg, clientAddress = serverSocket.recvfrom(1024)

        # 验证客户端发送的是否是SYN包
        if syn_msg == b"SYN":
            print(f"接收: 来自 {clientAddress} 的SYN")
        else:
            return None, "无效的SYN包"

        # 第二次握手：服务器发送SYN-ACK包
        # SYN-ACK表示服务器同意建立连接
        syn_ack_msg = b"SYN-ACK"
        serverSocket.sendto(syn_ack_msg, clientAddress)
        print("发送: SYN-ACK")

        # 等待第三次握手：客户端发送ACK包
        # 这是连接建立的最后一步
        ack_msg, clientAddress = serverSocket.recvfrom(1024)
        if ack_msg == b"ACK":
            print("接收: ACK")
        else:
            return None, "无效的ACK包"

        # 发送连接建立确认消息
        # 通知客户端连接已成功建立
        established_msg = b"CONNECTION_ESTABLISHED"
        serverSocket.sendto(established_msg, clientAddress)
        print("与客户端建立连接成功")

        # 连接建立后移除超时限制
        # 文件传输可能需要较长时间
        serverSocket.settimeout(None)

        # 返回客户端地址，表示连接成功
        return clientAddress, None

    except timeout:
        # 30秒内没有收到连接请求
        return None, "连接超时"
    except Exception as e:
        # 处理其他可能的异常
        return None, str(e)


def handle_file_transfer(serverSocket, clientAddress):
    """
    处理文件传输过程
    接收客户端发送的文件并保存到本地
    """
    try:
        # 接收客户端发送的文件名
        # 文件名以字符串形式发送，需要解码
        message, clientAddress = serverSocket.recvfrom(4096)
        original_file_name = message.decode()
        print(f"正在接收文件: {original_file_name}")

        # 初始化接收数据缓冲区
        received_data = b""  # 空的字节串，用于累积接收到的数据
        total_bytes = 0  # 记录总共接收的字节数

        # 循环接收文件数据
        while True:
            # 接收数据块，最大4096字节
            data, clientAddress = serverSocket.recvfrom(4096)

            # 检查是否收到结束标记
            if data == b"<END_OF_FILE>":
                # 收到结束标记，退出接收循环
                break

            # 将接收到的数据添加到缓冲区
            received_data += data
            total_bytes += len(data)
            # 显示实时接收进度
            print(f"已接收: {total_bytes} 字节", end='\r')

        # 生成带时间戳的新文件名
        # 避免覆盖原始文件，同时便于管理
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 分离文件名和扩展名
        name, ext = os.path.splitext(original_file_name)
        # 创建新的文件名格式：RECEIVED_原文件名_时间戳.扩展名
        new_file_name = f"RECEIVED_{name}_{timestamp}{ext}"

        # 以二进制写入模式保存文件
        with open(new_file_name, 'wb') as f:
            f.write(received_data)

        # 打印传输完成信息
        print(f"\n文件传输完成:")
        print(f"   原始文件名: {original_file_name}")
        print(f"   保存为: {new_file_name}")
        print(f"   文件大小: {len(received_data)} 字节")
        print(f"   完成时间: {datetime.now().strftime('%H:%M:%S')}")

        return True

    except Exception as e:
        # 文件传输过程中发生错误
        print(f"文件传输错误: {e}")
        return False


def handle_connection_close(serverSocket, clientAddress):
    """
    处理连接关闭过程
    与客户端完成四次挥手，优雅地关闭连接
    """
    print("正在关闭连接...")

    try:
        # 设置10秒超时，防止连接关闭过程卡住
        serverSocket.settimeout(10.0)

        # 等待第一次挥手：客户端发送FIN包
        fin_msg, clientAddress = serverSocket.recvfrom(1024)

        if fin_msg == b"FIN":
            print("接收: FIN (客户端关闭请求)")
        else:
            return False

        # 第二次挥手：服务器发送ACK包
        # 确认收到客户端的FIN请求
        ack_msg = b"ACK"
        serverSocket.sendto(ack_msg, clientAddress)
        print("发送: ACK")

        # 第三次挥手：服务器发送FIN包
        # 表示服务器也准备关闭连接
        fin_msg = b"FIN"
        serverSocket.sendto(fin_msg, clientAddress)
        print("发送: FIN")

        # 等待第四次挥手：客户端发送ACK包
        # 确认收到服务器的FIN请求
        ack_msg, clientAddress = serverSocket.recvfrom(1024)
        if ack_msg == b"ACK":
            print("接收: ACK")
        else:
            return False

        # 发送连接关闭确认
        closed_msg = b"CONNECTION_CLOSED"
        serverSocket.sendto(closed_msg, clientAddress)
        print("连接关闭成功")

        return True

    except timeout:
        print("连接关闭超时")
        return False
    except Exception as e:
        print(f"连接关闭错误: {e}")
        return False


def main():
    """
    主函数：UDP文件传输服务器
    持续运行，处理多个客户端的连接请求
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='UDP文件传输服务器')
    # 服务器只需要端口号参数
    parser.add_argument('port', type=int, help='服务器监听端口号')

    # 解析命令行参数
    args = parser.parse_args()

    # 获取端口号
    serverPort = args.port

    # 创建UDP socket
    serverSocket = socket(AF_INET, SOCK_DGRAM)

    # 绑定socket到所有网络接口的指定端口
    # 空字符串表示绑定到所有可用的网络接口
    serverSocket.bind(('', serverPort))

    print(f"UDP文件传输服务器已启动，监听端口 {serverPort}")
    print("=" * 50)

    try:
        # 主服务循环：持续运行处理客户端请求
        while True:
            # 第一阶段：连接建立
            # 等待客户端连接并完成三次握手
            clientAddress, error = handle_connection(serverSocket)

            # 检查连接是否成功建立
            if error:
                print(f"连接失败: {error}")
                continue  # 继续等待下一个连接
            if not clientAddress:
                continue  # 没有有效的客户端地址，继续等待
            # 第二阶段：文件传输
            # 接收并保存客户端发送的文件
            transfer_success = handle_file_transfer(serverSocket, clientAddress)

            # 第三阶段：连接关闭
            # 只有在文件传输成功时才进行优雅的连接关闭
            if transfer_success:
                close_success = handle_connection_close(serverSocket, clientAddress)
                if not close_success:
                    print("连接关闭过程出现问题，但文件传输已完成")
            else:
                print("文件传输失败，跳过连接关闭过程")

            # 打印分隔线，准备处理下一个连接
            print("=" * 50)
            print("准备接收下一个连接...")

    except KeyboardInterrupt:
        # 捕获Ctrl+C信号，优雅地关闭服务器
        print("\n用户请求关闭服务器")
    except Exception as e:
        # 捕获其他未预期的错误
        print(f"服务器错误: {e}")
    finally:
        # 确保在任何情况下都关闭socket
        serverSocket.close()
        print("服务器socket已关闭")


if __name__ == "__main__":

    main()
