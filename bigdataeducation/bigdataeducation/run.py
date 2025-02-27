from pyngrok import ngrok
from app import app
import os

def start_ngrok():
    try:
        # 直接设置 authtoken
        ngrok.set_auth_token("2taBuNUh9T8zX0cuLMlQVaXgkk1_3d97fSvkcKK8njTLSp4FM")

        # 启动 ngrok
        http_tunnel = ngrok.connect(5000)
        print(f'公网访问地址: {http_tunnel.public_url}')
        return http_tunnel
    except Exception as e:
        print(f'Ngrok 启动失败: {e}')
        return None

if __name__ == '__main__':
    # 启动 ngrok
    tunnel = start_ngrok()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5000) 