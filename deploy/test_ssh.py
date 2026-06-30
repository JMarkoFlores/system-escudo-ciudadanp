"""
Test SSH connection to VM
"""
import paramiko
import sys

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print('Conectando a 142.93.240.223...')
    client.connect(
        hostname='142.93.240.223',
        port=22,
        username='root',
        password='TatoS69uwu',
        timeout=60,
        banner_timeout=60,
        auth_timeout=60
    )
    print('Conexion exitosa!')
    
    stdin, stdout, stderr = client.exec_command('uname -a')
    print(f'Sistema: {stdout.read().decode().strip()}')
    
    stdin, stdout, stderr = client.exec_command('docker --version')
    docker_out = stdout.read().decode().strip()
    if docker_out:
        print(f'Docker: {docker_out}')
    else:
        print('Docker: No instalado')
    
    client.close()
    print('OK')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
