# coding=utf-8

class FTP:

    def __init__(self, ip: str, port: int):
        self.server_ip = f'{ip}:{port}'
        pass

    def upload_file(self):
        """
        向服务端ftp上传文件
        :return:
        """
        pass

    def download_file(self):
        """
        从服务端ftp下载文件
        :return:
        """
        pass
