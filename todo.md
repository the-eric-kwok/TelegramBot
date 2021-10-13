# 需求

- [x] 用 `/sign` 来标注当天签到状态
- [x] 若已签到，通过命令 `/sign` 来停止当天的提醒
- [x] 用 `/ami` 指令查询当天签到状态
- [x] 数据持久化
- [x] 实现一个Alarm类，与User类的UserList配合实现通知功能
- [ ] 在收到SIGINT的时候将alarm线程杀掉  `.stop()`
- [x] 用/stop命令将用户移出Userlist
- [x] 用jsondump实现User类的持久化
- [ ] 将 TOKEN、PROXY、LOGFILE 等配置保存为 config.json 并在运行时读取 
- [ ] 用/set命令设定自定义的提醒事项

Alarm 类：
- 计时
- 按chat_id发送消息

User 类：
- 属性：
  - __chat_id
  - __sign_flag
- 方法:
  - getChatId()
  - getSignFlag()
  - sign()