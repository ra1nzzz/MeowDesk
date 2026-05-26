"""
AI Agent 集成示例
"""

from meowdesk.agent import AgentGateway, CommandRegistry


def example_gateway():
    """Agent Gateway 使用示例"""
    print("=== Agent Gateway 示例 ===\n")
    
    # 配置
    config = {
        'enabled': True,
        'agent_type': 'openclaw',
        'endpoint': 'http://localhost:8080',
        'api_key': '',
        'timeout': 30
    }
    
    gateway = AgentGateway(config)
    
    # 检查可用性
    if gateway.is_available():
        print("✅ Agent 可用\n")
        
        # 对话
        print("对话示例：")
        response = gateway.chat("今天星期几？")
        if response['success']:
            print(f"Agent: {response.get('response', '无响应')}\n")
        else:
            print(f"❌ 错误: {response.get('error')}\n")
        
        # 执行命令
        print("命令执行示例：")
        result = gateway.execute_command('check_date')
        if result['success']:
            data = result.get('result', {})
            print(f"今天: {data.get('today')}")
            print(f"星期: {data.get('weekday')}")
            print(f"距离周末: {data.get('days_to_weekend')} 天\n")
        else:
            print(f"❌ 错误: {result.get('error')}\n")
    else:
        print("❌ Agent 不可用")
        print("请确保 Agent 正在运行: http://localhost:8080\n")


def example_commands():
    """内置命令示例"""
    print("=== 内置命令示例 ===\n")
    
    registry = CommandRegistry()
    
    # 列出所有命令
    print("可用命令:")
    for cmd in registry.list_commands():
        print(f"  - {cmd}")
    print()
    
    # 日期查询
    print("1. 日期查询:")
    result = registry.execute('check_date')
    if result['success']:
        data = result['result']
        print(f"   今天: {data['today']} {data['weekday']}")
        print(f"   距离周末: {data['days_to_weekend']} 天")
        print(f"   距离月底: {data['days_to_month_end']} 天\n")
    
    # 假期查询
    print("2. 假期查询:")
    result = registry.execute('check_holidays')
    if result['success']:
        holidays = result['result']['upcoming_holidays']
        for holiday in holidays[:3]:
            print(f"   {holiday['name']}: {holiday['date']} (还有 {holiday['days_left']} 天)")
    print()
    
    # 系统信息
    print("3. 系统信息:")
    result = registry.execute('system_info')
    if result['success']:
        data = result['result']
        print(f"   操作系统: {data['os']} {data['os_version']}")
        print(f"   CPU: {data['cpu_count']} 核心, 使用率 {data['cpu_percent']}%")
        print(f"   内存: {data['memory_used_gb']}/{data['memory_total_gb']} GB ({data['memory_percent']}%)")
        print(f"   磁盘: {data['disk_used_gb']}/{data['disk_total_gb']} GB ({data['disk_percent']}%)")
    print()


def example_custom_command():
    """自定义命令示例"""
    print("=== 自定义命令示例 ===\n")
    
    registry = CommandRegistry()
    
    # 注册自定义命令
    @registry.register_command('greet')
    def greet(params):
        name = params.get('name', 'World')
        time = params.get('time', 'day')
        greetings = {
            'morning': '早上好',
            'afternoon': '下午好',
            'evening': '晚上好',
            'day': '你好'
        }
        greeting = greetings.get(time, '你好')
        return {'message': f'{greeting}, {name}!'}
    
    # 执行自定义命令
    result = registry.execute('greet', {'name': 'MeowDesk', 'time': 'morning'})
    if result['success']:
        print(f"结果: {result['result']['message']}\n")


def example_period_reminder():
    """经期提醒示例"""
    print("=== 经期提醒示例 ===\n")
    
    registry = CommandRegistry()
    
    # 首次使用（需要设置）
    result = registry.execute('period_reminder', {})
    if result['success'] and result['result'].get('need_setup'):
        print("⚠️  需要先设置上次经期日期\n")
    
    # 设置后使用
    result = registry.execute('period_reminder', {
        'last_date': '2026-05-01',
        'cycle_days': 28
    })
    
    if result['success']:
        data = result['result']
        print(f"上次日期: {data['last_date']}")
        print(f"已过天数: {data['days_since']} 天")
        print(f"距离下次: {data['days_until_next']} 天")
        print(f"预计日期: {data['next_date']}")
        
        status_map = {
            'normal': '正常',
            'coming_soon': '⚠️  即将到来',
            'overdue': '❗ 已延迟'
        }
        print(f"状态: {status_map.get(data['status'], '未知')}\n")


if __name__ == '__main__':
    # 运行示例
    example_commands()
    example_custom_command()
    example_period_reminder()
    
    # 如果 Agent 可用，运行 Gateway 示例
    print("\n" + "="*50)
    print("尝试连接 Agent...")
    print("="*50 + "\n")
    example_gateway()
