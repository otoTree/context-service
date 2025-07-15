#!/usr/bin/env python3
"""API测试脚本"""
import asyncio
import json
from uuid import uuid4

import httpx


BASE_URL = "http://localhost:8000"


async def test_health_check():
    """测试健康检查端点"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/healthz")
        print(f"Health Check: {response.status_code} - {response.json()}")
        return response.status_code == 200


async def test_create_task_from_text():
    """测试从文本创建任务"""
    test_dsl = """
# 示例DSL任务
@variable user_input = "测试输入"
@variable result = ""

@task search_info {
    @tool web_search {
        query: $user_input
        max_results: 5
    }
    @condition success {
        @variable result = $web_search.results
    }
}

@task process_results {
    @depends_on search_info
    @tool text_processor {
        input: $result
        action: "summarize"
    }
}
"""
    
    payload = {
        "dsl_content": test_dsl,
        "agent_id": str(uuid4()),
        "metadata": {
            "description": "测试任务",
            "version": "1.0",
            "tags": ["test", "demo"]
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/tasks/create-from-text",
                json=payload,
                timeout=30.0
            )
            print(f"Create Task: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Task ID: {result.get('task_id')}")
                print(f"Slices Count: {result.get('slices_count')}")
                return result.get('task_id')
            else:
                print(f"Error: {response.text}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None


async def test_get_task_detail(task_id: str):
    """测试获取任务详情"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/tasks/{task_id}")
            print(f"Get Task Detail: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Task Name: {result.get('name')}")
                print(f"Status: {result.get('status')}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"Request failed: {e}")
            return False


async def test_get_task_slices(task_id: str):
    """测试获取任务切片"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/tasks/{task_id}/slices")
            print(f"Get Task Slices: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Slices Count: {len(result.get('slices', []))}")
                for i, slice_data in enumerate(result.get('slices', [])):
                    print(f"  Slice {i+1}: {slice_data.get('name')} - {slice_data.get('status')}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"Request failed: {e}")
            return False


async def main():
    """主测试函数"""
    print("开始API测试...\n")
    
    # 测试健康检查
    print("1. 测试健康检查")
    health_ok = await test_health_check()
    if not health_ok:
        print("健康检查失败，请确保服务正在运行")
        return
    
    print("\n2. 测试创建任务")
    task_id = await test_create_task_from_text()
    if not task_id:
        print("创建任务失败")
        return
    
    print("\n3. 测试获取任务详情")
    await test_get_task_detail(task_id)
    
    print("\n4. 测试获取任务切片")
    await test_get_task_slices(task_id)
    
    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())