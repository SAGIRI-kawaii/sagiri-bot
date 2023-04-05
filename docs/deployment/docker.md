# Docker 部署

!!! danger "使用前注意"
    
    本教程需要：
    
    - **进阶**文件操作能力
    
    - **进阶**终端使用能力
    
    - 基础搜索引擎使用能力
    
    - 中文阅读理解能力
    
    - 一个可以正常运转的脑子
    
    没有的话建议快跑

!!! danger "一个建议"
    
    极度不建议没有任何计算机基础的人安装或使用 SAGIRI-BOT!
    
    除非你懂得如何阅读文档、虚心提问并可以正常使用搜索引擎

!!! danger "需要注意"

    本章内容需要你有 Docker 基础，Docker 安装请自行查询资料，本章不做叙述

## 创建 Docker 网络

运行 `docker network create -d bridge sagiri`

## sagiri-mah

1. 运行 `docker run -it -v [path]/bots:/mcl/bots -v [path]/config:/mcl/config --name sagiri-mah --network sagiri zaphakiel/sagiri-mah`
2. 等待运行完成，出现可以输入的光标（初次运行可能时间很长，请耐心等待，这取决于网络状态），若觉得太卡可以 `Ctrl-C` 退出后使用 `docker start -i sagiri-mah` 重启继续运行
3. 配置自动登录，输入如下命令：
    ```
    /autoLogin add qq号 qq密码
    /autoLogin setConfig qq号 protocol 要更换的协议（若你不知道这是什么也可以不换）
    ```
   上述命令可以执行多次以添加多个bot账号
4. `/stop` 或 `Ctrl-C` 退出 MCL，打开之前映射的本地目录 `[path]/config`，打开其中的 `net.mamoe.mirai-api-http/setting.yml`，并将下列内容覆盖粘贴：

    ```yaml
    adapters:
      - http
      - ws
    debug: false
    enableVerify: true
    verifyKey: 1234567890 # 你可以自己设定, 这里作为示范, 请保持和 config.yaml 中 verify_key 项一致
    singleMode: false
    cacheSize: 4096 # 可选, 缓存大小, 默认4096. 缓存过小会导致引用回复与撤回消息失败
    adapterSettings:
      ## 详情看 http adapter 使用说明 配置
      http:
        host: 0.0.0.0
        port: 23456 # 端口
        cors: [*]

      ## 详情看 websocket adapter 使用说明 配置
      ws:
        host: 0.0.0.0
        port: 23456 # 端口
        reservedSyncId: -1 # 确保为 -1, 否则 WebsocketAdapter(Experimental) 没法正常工作.
    
    ```
   
## sagiri-bot

1. 运行 `docker run -it -v [path]/log:/sagiri-bot/log -v [path]/config:/sagiri-bot/config --name sagiri-bot --network sagiri zaphakiel/sagiri-bot`
2. 等待镜像拉取完成，按照提示填写配置，注意其中 `mirai_host` 项要改为 `http://sagiri-mah:23456`
3. 等待插件加载完成即可，配置可以到 `[path]/config` 手动修改，日志可在 `[path]/log` 查看

## proxy[optional]

请自行寻找镜像，如 [clash for docker](https://hub.docker.com/r/80x86/clash#!) 等并配置，并在运行时添加参数 `--network sagiri`，并将 `config.yaml` 中的 `proxy` 改为 `{container_name}:{port}`

示例：`clash` 端口为 `7890`

容器创建时名字为 `clash`

创建命令如下
```docker
docker run --user 1024:100 --name clash -d \
--network sagiri \
--name clash \
--restart=unless-stopped \
-e CLASH_CTL_ADDR="0.0.0.0:8082" \
-e CLASH_SECRET="YOUR-PASSWORD-HERE" \
-v $(pwd)/config.yaml:/etc/clash/config.yaml:ro,z \
-v $(pwd)/GeoIP2-Country-2020-08-18.mmdb:/etc/clash/Country.mmdb:ro,z \
80x86/clash:v1.5.0
```
则 `proxy` 应为 `http://clash:7890`
