import requests
import json

def test_backend_health():
    """简单的健康检查测试"""
    try:
        print("🔍 测试后端服务连接...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 后端服务正常运行")
            print(f"📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 后端服务响应异常: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        print("💡 请确认后端服务是否已启动:")
        print("   cd backend")
        print("   uv run fastapi dev main.py")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 后端服务响应超时")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def test_api_endpoints():
    """测试主要API端点"""
    if not test_backend_health():
        return
    
    print("\n🚀 测试API端点...")
    
    # 测试注册接口
    try:
        print("\n📝 测试用户注册...")
        register_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "test123456",
            "full_name": "测试用户"
        }
        
        response = requests.post("http://localhost:8000/api/v1/auth/register", json=register_data, timeout=10)
        
        if response.status_code == 201:
            print("✅ 注册成功")
            result = response.json()
            token = result.get("access_token")
            print(f"📄 获得访问令牌: {token[:50]}..." if token else "⚠️ 未获得访问令牌")
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print("✅ 用户已存在（正常情况）")
        else:
            print(f"❌ 注册失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 注册测试失败: {str(e)}")
    
    # 测试登录接口
    try:
        print("\n🔑 测试用户登录...")
        login_data = {
            "username": "testuser",
            "password": "test123456"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login", 
            data=login_data,  # OAuth2使用form data
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 登录成功")
            result = response.json()
            token = result.get("access_token")
            print(f"📄 访问令牌: {token[:50]}..." if token else "⚠️ 未获得访问令牌")
            
            # 测试获取用户信息
            if token:
                print("\n👤 测试获取用户信息...")
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get("http://localhost:8000/api/v1/auth/me", headers=headers, timeout=10)
                
                if profile_response.status_code == 200:
                    print("✅ 获取用户信息成功")
                    user_data = profile_response.json()
                    print(f"📄 用户: {user_data.get('username')} ({user_data.get('email')})")
                else:
                    print(f"❌ 获取用户信息失败: {profile_response.status_code}")
                    
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            print("💡 尝试使用管理员账户登录...")
            
            # 尝试管理员账户
            admin_data = {"username": "admin", "password": "password123"}
            admin_response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                data=admin_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if admin_response.status_code == 200:
                print("✅ 管理员账户登录成功")
            else:
                print(f"❌ 管理员账户登录也失败: {admin_response.status_code}")
                
    except Exception as e:
        print(f"❌ 登录测试失败: {str(e)}")

if __name__ == "__main__":
    print("🧪 后端API快速测试")
    print("=" * 40)
    test_api_endpoints()
    print("\n🎉 测试完成!")