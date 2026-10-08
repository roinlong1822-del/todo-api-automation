# api_test/testcases/smoke/ — 冒烟用例

- 目的:几分钟内判断"这版能不能测"——核心主流程 + 关键接口可用性
- 标记:外网依赖用例打 `@pytest.mark.network`,CI 上用 `-m "not network"` 跳过
- 建议条数:**≤ 5 条**,只断言"能不能通",不做细节校验
