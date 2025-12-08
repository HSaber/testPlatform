import os

# 在这个文件中，我们集中管理应用的配置

# TODO: 请根据您的本地MySQL设置修改以下连接字符串
# 格式: "mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>"
DATABASE_URL = "mysql+pymysql://root:root123@127.0.0.1:3306/test_platform"

# 环境配置
ENV_CONFIGS = {
    "dev": {
        "API_BASE_URL": "http://47.96.74.113:90"  # 开发环境 Host
    },
    "uat": {
        "API_BASE_URL": "http://test-server.com"   # 测试环境 uat
    },
    "prod": {
        "API_BASE_URL": "https://api.production.com" # 生产环境 Host
    }
}

# 获取当前环境，默认为 'dev'
# 在不同代码分支的部署/运行脚本中，可以通过设置环境变量 APP_ENV 来切换配置
APP_ENV = os.getenv("APP_ENV", "dev")

# 获取当前环境的配置
CURRENT_ENV_CONFIG = ENV_CONFIGS.get(APP_ENV, ENV_CONFIGS["dev"])
API_BASE_URL = CURRENT_ENV_CONFIG["API_BASE_URL"]