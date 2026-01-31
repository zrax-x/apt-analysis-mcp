#!/usr/bin/env python3
"""
样本下载器API接口
提供简洁的函数接口用于下载样本文件
"""
import os
import tempfile
import subprocess
import time
import shutil
from typing import List, Tuple, Optional, Callable
from pathlib import Path


class SampleDownloaderAPI:
    """样本下载器API类"""
    
    def __init__(
        self,
        jumper_user: str,
        jumper_host: str,
        jumper_port: int,
        jumper_key: str,
        target_user: str,
        target_host: str,
        target_port: int,
        target_key: str,
        target_workdir: str
    ):
        """
        初始化样本下载器
        
        Args:
            jumper_user: 跳板机用户名
            jumper_host: 跳板机地址
            jumper_port: 跳板机端口
            jumper_key: 跳板机SSH私钥路径
            target_user: 目标服务器用户名
            target_host: 目标服务器地址
            target_port: 目标服务器端口
            target_key: 目标服务器SSH私钥路径
            target_workdir: 目标服务器工作目录
        """
        self.jumper_user = jumper_user
        self.jumper_host = jumper_host
        self.jumper_port = jumper_port
        self.jumper_key = os.path.expanduser(jumper_key)
        self.target_user = target_user
        self.target_host = target_host
        self.target_port = target_port
        self.target_key = os.path.expanduser(target_key)
        self.target_workdir = target_workdir
    
    def _run_ssh_command(
        self,
        command: str,
        max_retries: int = 3,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        通过跳板机执行SSH命令
        
        Args:
            command: 要执行的命令
            max_retries: 最大重试次数
            timeout: 命令超时时间（秒）
            
        Returns:
            (返回码, 标准输出, 标准错误)
        """
        for attempt in range(max_retries):
            try:
                ssh_cmd = [
                    "ssh", "-i", self.target_key,
                    "-o", f"ProxyCommand=ssh -i {self.jumper_key} -p {self.jumper_port} "
                          f"-o ConnectTimeout=30 -o ServerAliveInterval=60 "
                          f"-W %h:%p {self.jumper_user}@{self.jumper_host}",
                    "-o", "ConnectTimeout=30",
                    "-o", "ServerAliveInterval=60",
                    "-p", str(self.target_port),
                    f"{self.target_user}@{self.target_host}",
                    command
                ]
                
                result = subprocess.run(
                    ssh_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return result.returncode, result.stdout, result.stderr
                
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return -1, "", "SSH命令执行超时"
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return -1, "", str(e)
    
    def _upload_file(
        self,
        local_file: str,
        remote_path: str,
        timeout: int = 300
    ) -> Tuple[bool, str]:
        """
        通过跳板机上传文件到目标服务器
        
        Args:
            local_file: 本地文件路径
            remote_path: 远程文件路径
            timeout: 上传超时时间（秒）
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            scp_cmd = [
                "scp", "-i", self.target_key,
                "-o", f"ProxyCommand=ssh -i {self.jumper_key} -p {self.jumper_port} "
                      f"-o ConnectTimeout=30 -o ServerAliveInterval=60 "
                      f"-W %h:%p {self.jumper_user}@{self.jumper_host}",
                "-o", "ConnectTimeout=30",
                "-o", "ServerAliveInterval=60",
                "-P", str(self.target_port),
                local_file,
                f"{self.target_user}@{self.target_host}:{remote_path}"
            ]
            result = subprocess.run(
                scp_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)
    
    def _download_directory(
        self,
        remote_dir: str,
        local_dir: str,
        timeout: int = 600
    ) -> Tuple[bool, str]:
        """
        通过跳板机从目标服务器下载目录
        
        Args:
            remote_dir: 远程目录路径
            local_dir: 本地目录路径
            timeout: 下载超时时间（秒）
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            os.makedirs(os.path.dirname(local_dir), exist_ok=True)
            
            scp_cmd = [
                "scp", "-r", "-i", self.target_key,
                "-o", f"ProxyCommand=ssh -i {self.jumper_key} -p {self.jumper_port} "
                      f"-o ConnectTimeout=30 -o ServerAliveInterval=60 "
                      f"-W %h:%p {self.jumper_user}@{self.jumper_host}",
                "-o", "ConnectTimeout=30",
                "-o", "ServerAliveInterval=60",
                "-P", str(self.target_port),
                f"{self.target_user}@{self.target_host}:{remote_dir}",
                local_dir
            ]
            result = subprocess.run(
                scp_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)
    
    def download_samples(
        self,
        hash_list: List[str],
        local_output_dir: str,
        output_dirname: str = "samples",
        cleanup_remote: bool = True,
        log_callback: Optional[Callable[[str], None]] = None,
        flat_output: bool = False
    ) -> Tuple[bool, str, str]:
        """
        下载样本文件
        
        Args:
            hash_list: SHA256哈希值列表
            local_output_dir: 本地输出目录路径
            output_dirname: 输出目录名称（在目标服务器和本地都使用此名称）
            cleanup_remote: 是否清理远程服务器上的临时文件
            log_callback: 日志回调函数，用于接收日志消息
            flat_output: 是否直接下载到输出目录而不创建子目录
            
        Returns:
            (是否成功, 本地下载路径, 错误信息)
        """
        def log(message: str):
            """内部日志函数"""
            if log_callback:
                log_callback(message)
            else:
                # 默认不打印日志，除非提供回调
                pass
        
        try:
            # 验证hash列表
            if not hash_list:
                return False, "", "hash列表不能为空"
            
            log(f"开始下载 {len(hash_list)} 个样本...")
            
            # 创建临时文件存储hash列表
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False
            ) as f:
                f.write('\n'.join(hash_list))
                hash_file_path = f.name
            
            log(f"已创建hash列表文件: {hash_file_path}")
            
            # 上传hash文件到目标服务器
            log("正在上传hash列表文件到目标服务器...")
            remote_hash_file = f"{self.target_workdir}/hashList.txt"
            success, error = self._upload_file(hash_file_path, remote_hash_file)
            
            if not success:
                os.unlink(hash_file_path)
                return False, "", f"上传hash文件失败: {error}"
            
            log("hash文件上传成功")
            
            # 在目标服务器上执行下载脚本
            log("正在目标服务器上执行下载脚本...")
            download_cmd = (
                f"cd {self.target_workdir} && "
                f"python3 obs_collect_new.py --input ./hashList.txt --output ./{output_dirname}"
            )
            rc, out, err = self._run_ssh_command(download_cmd, timeout=600)
            
            if rc != 0:
                os.unlink(hash_file_path)
                return False, "", f"下载脚本执行失败: {err}"
            
            log("下载脚本执行成功")
            if out:
                log(f"脚本输出: {out}")
            
            # 创建本地输出目录
            local_output_dir = os.path.abspath(local_output_dir)
            os.makedirs(local_output_dir, exist_ok=True)
            
            # 从目标服务器下载整个目录到本地
            log("正在从目标服务器下载文件到本地...")
            remote_download_dir = f"{self.target_workdir}/{output_dirname}"
            
            if flat_output:
                # 直接下载到输出目录，不创建子目录
                # 先下载到临时目录，然后移动文件
                temp_dir = tempfile.mkdtemp()
                temp_download_path = os.path.join(temp_dir, output_dirname)
                
                success, error = self._download_directory(
                    remote_download_dir,
                    temp_download_path,
                    timeout=600
                )
                
                if not success:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    os.unlink(hash_file_path)
                    return False, "", f"下载文件失败: {error}"
                
                # 移动文件到目标目录
                os.makedirs(local_output_dir, exist_ok=True)
                for filename in os.listdir(temp_download_path):
                    src = os.path.join(temp_download_path, filename)
                    dst = os.path.join(local_output_dir, filename)
                    shutil.move(src, dst)
                
                # 清理临时目录
                shutil.rmtree(temp_dir, ignore_errors=True)
                local_download_path = local_output_dir
            else:
                # 创建子目录
                local_download_path = os.path.join(local_output_dir, output_dirname)
                
                success, error = self._download_directory(
                    remote_download_dir,
                    local_download_path,
                    timeout=600
                )
                
                if not success:
                    os.unlink(hash_file_path)
                    return False, "", f"下载文件失败: {error}"
            
            log("文件下载成功")
            
            # 清理远程服务器上的输出目录
            if cleanup_remote:
                log("正在删除服务器上的输出目录...")
                cleanup_cmd = f"cd {self.target_workdir} && rm -rf {output_dirname}"
                rc, out, err = self._run_ssh_command(cleanup_cmd)
                
                if rc == 0:
                    log("服务器输出目录删除成功")
                else:
                    log(f"删除服务器输出目录失败: {err}")
            
            # 清理本地临时文件
            os.unlink(hash_file_path)
            
            log(f"任务完成，文件已下载到: {local_download_path}")
            return True, local_download_path, ""
            
        except Exception as e:
            return False, "", f"任务执行异常: {str(e)}"


def download_samples(
    hash_list: List[str],
    local_output_dir: str,
    jumper_config: dict,
    target_config: dict,
    output_dirname: str = "samples",
    cleanup_remote: bool = True,
    log_callback: Optional[Callable[[str], None]] = None,
    flat_output: bool = False
) -> Tuple[bool, str, str]:
    """
    下载样本文件的便捷函数
    
    Args:
        hash_list: SHA256哈希值列表
        local_output_dir: 本地输出目录路径
        jumper_config: 跳板机配置字典，包含: user, host, port, key
        target_config: 目标服务器配置字典，包含: user, host, port, key, workdir
        output_dirname: 输出目录名称
        cleanup_remote: 是否清理远程服务器上的临时文件
        log_callback: 日志回调函数
        flat_output: 是否直接下载到输出目录而不创建子目录
        
    Returns:
        (是否成功, 本地下载路径, 错误信息)
    """
    api = SampleDownloaderAPI(
        jumper_user=jumper_config['user'],
        jumper_host=jumper_config['host'],
        jumper_port=jumper_config['port'],
        jumper_key=jumper_config['key'],
        target_user=target_config['user'],
        target_host=target_config['host'],
        target_port=target_config['port'],
        target_key=target_config['key'],
        target_workdir=target_config['workdir']
    )
    
    return api.download_samples(
        hash_list=hash_list,
        local_output_dir=local_output_dir,
        output_dirname=output_dirname,
        cleanup_remote=cleanup_remote,
        log_callback=log_callback,
        flat_output=flat_output
    )
