# 内置模块

本篇为内置模块，若您不需要使用某一模块，可以删除模块或通过 `saya_manager` 进行管理

其中命令格式使用了正则语法

- (a|b)c 代表 a或b+c，即 ac，bc 都可触发
- ab?c 代表b可选，即 abc，ac 都可触发
- {name} 代表这是一个必须要的参数
- [name] 代表这是一个可选参数

> ## 缩写预测（AbbreviatedPrediction）

一个获取英文缩写意思的插件

模块位置：`modules.self_contained.abbreviated_prediction`

模块版本：`0.2`

使用方法：

- 在群中发送 `缩 内容` 即可

使用示例：

- `/缩 abc`

触发前缀：`/缩`、`/缩写`

可用性：可用

> ## 抽象话转换（AbstractMessageTransformer）

一个普通话转抽象话的插件

模块位置：`modules.self_contained.abstract_message_transform`

模块版本：`0.2`

使用方法：

- 在群中发送 `/抽象 文字` 即可

使用示例：

- `/抽象 你好`

触发前缀：`/抽象`

可用性：可用

> ## AI文/图转图（NovelAI）（StableDiffusion）

一个可以AI文/图转图的插件，配合https://github.com/SAGIRI-kawaii/stable-diffusion-webui-api使用

模块位置：`modules.self_contained.ai_text2img`

模块版本：`0.1`

使用方法：

- 在群中发送 `/ait2i 关键词` 即可文转图
- 在群中发送 `/aii2i 关键词[图片]` 即可图转图

使用示例：

- `/ait2i 1 girl`
- `/aii2i 1 girl[图片]`

触发前缀：

可用性：可用

> ## 学术搜索（Aminer）

一个搜索导师信息的插件

模块位置：`modules.self_contained.aminer`

模块版本：`0.2`

使用方法：

- 在群中发送 /aminer {keyword} 即可搜索学者
- 在群中发送 /aminer -paper {keyword} 即可搜索论文
- 在群中发送 /aminer -patent {keyword} 即可搜索专利

使用示例：

- `/aminer 学者`
- `/aminer -paper SMCQL`
- `/aminer -patent 一种新型专利`

触发前缀：`/aminer`

可用性：可用

> ## 防撤回（AntiRevoke）

一个防撤回的插件

模块位置：`modules.self_contained.anti_revoke`

模块版本：`0.1`

使用方法：

- 打开数据库开关后自动触发

使用示例：

暂无

触发前缀：

可用性：可用

> ## Apex战绩查询（ApexStat）

一个Apex数据查询插件

模块位置：`modules.self_contained.apex_stat`

模块版本：`0.2`

使用方法：

- 在群中发送 `/apex origin用户名` 即可

使用示例：

- `/apex account`

触发前缀：`/apex`

可用性：可用

> ## AV种子查询（AVBT）

一个AV种子查询插件

模块位置：`modules.self_contained.av_bt`

模块版本：`0.1`

使用方法：

- 在群中发送 `/av [-i] {番号/演员名/关键词}` 即可，默认没有图片，加上 -i 保留图片

使用示例：

- `/av STARS-256`
- `/av -i STARS-256`

触发前缀：`/av`

可用性：可用



> ## 番剧查询（BangumiInfoSearcher）

一个可以搜索番剧信息的插件

模块位置：`modules.self_contained.bangumi_info_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `番剧/搜索番剧/番剧查询 {番剧名}` 即可

使用示例：

- `番剧 埃罗芒阿老师`

触发前缀：`番剧`、`搜索番剧`、`番剧查询`、`/番剧`、`/搜索番剧`、`/番剧查询`

可用性：可用

> ## 以图搜番（BangumiSearcher）

一个可以根据图片搜索番剧的插件

模块位置：`modules.self_contained.bangumi_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `搜番` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）

使用示例：

暂无

触发前缀：`搜番`、`识番`、`以图搜番`、`/搜番`、`/识番`、`/以图搜番`

可用性：可用

> ## B站新番时间表（BiliBiliBangumiScheduler）

一个可以获取BiliBili7日内新番时间表的插件

模块位置：`modules.self_contained.bilibili_bangumi_scheduler`

模块版本：`0.2`

使用方法：

- 在群内发送 `[1-7]日内新番` 即可

使用示例：

- `7日内新番`

触发前缀：

可用性：可用

> ## B站链接解析（BilibiliResolve）

一个解析B站链接/AV/BV号/App消息的插件

模块位置：`modules.self_contained.bilibili_resolve`

模块版本：`0.1`

使用方法：

- 自动触发

使用示例：

暂无

触发前缀：

可用性：可用

> ## BT搜索器（BTSearcher）

一个可以搜索bt的插件

模块位置：`modules.self_contained.bt`

模块版本：`0.2`

使用方法：

- 在群中发送 `/bt + 想搜索的内容` 即可

使用示例：

- `/bt 计算机网络`

触发前缀：`/bt`

可用性：可用

> ## ChatGPT（ChatGPT）

一个接入 ChatGPT 的插件

模块位置：`modules.self_contained.chat_gpt`

模块版本：`0.1`

使用方法：

- 在群中发送 `/chat 内容` 即可开启对话，之后默认为同一轮对话
- 在群中发送 `/chat -n 内容` 即可开启新一轮对话
- 在群中发送 `/chat -t 内容` 即可以文字形式返回结果（默认为图片）

使用示例：

- `/chat 你好`
- `/chat -n 你好`
- `/chat -t 你好`
- `/chat -n -t 你好`

触发前缀：`/chat`

可用性：维护中，不可用

> ## 色卡生成（ColorCard）

一个获取图片色卡的插件

模块位置：`modules.self_contained.color_card`

模块版本：`0.2`

使用方法：

- 在群中发送 `/色卡 -s={size} -m={mode} -t {图片/@成员/qq号/回复有图片的消息}` 即可
- 发送 `/色卡 -h` 查看帮助
- 可选参数：
    - -s/-size：色卡颜色个数，在群中发送 `/色卡 -s={size} {图片/@成员/qq号/回复有图片的消息}` 即可，默认值为5 
    - -m/-mode：色卡形式，在群中发送 `/色卡 -s={size} {图片/@成员/qq号/回复有图片的消息}` 即可，默认值为center，可选值及说明如下：
        - pure：纯颜色
        - below：在下方添加方形色块
        - center：在图片中央添加圆形色块（自适应，若图片长>宽则为center_horizon，反之则为center_vertical）
        - center_horizon：在图片中央水平添加圆形色块
        - center_vertical：在图片中央垂直添加圆形色块
    - -t/-text：是否在下方附加色块RGB即十六进制值文本，在群中发送 `/色卡 -t {图片/@成员/qq号/回复有图片的消息}` 即可
- 上述参数可同步使用，并按照 -s、-m、-t的顺序添加，如 `/色卡 -s=10 -m=pure -t {图片/@成员/qq号/回复有图片的消息}`

使用示例：

- `/色卡 -s=3 -m=pure -t @target`

触发前缀：`color_card`、`色卡`、`/color_card`、`/色卡`

可用性：可用

> ## CP文生成器（CPGenerator）

一个可以生成CP文的插件

模块位置：`modules.self_contained.cp_generator`

模块版本：`0.2`

使用方法：

- 在群中发送 `/cp {攻名字} {受名字}`

使用示例：

- `/cp Alice Bob`

触发前缀：`/cp`

可用性：可用

> ## 每日60s新闻（DailyNewspaper）

一个定时发送每日日报的插件

模块位置：`modules.self_contained.daily_newspaper`

模块版本：`0.2`

使用方法：

- 主人私聊bot发送 `发送早报` 可在群中发送早报
- 在群中发送 `今日早报` 可在群中发送早报

使用示例：

暂无

触发前缀：`早报`、`今日早报`、`/早报`、`/今日早报`

可用性：可用

> ## 成分查询（DDCheck）

一个查成分的插件

模块位置：`modules.self_contained.dd_check`

模块版本：`0.2`

使用方法：

- 在群中发送 `/查成分 {B站UID/用户名}` 即可

使用示例：

- `/查成分 陈睿`

触发前缀：`查看成分`、`查成分`、`/查看成分`、`/查成分`

可用性：可用

> ## 投骰子（Dice）

一个简单的投骰子插件

模块位置：`modules.self_contained.dice`

模块版本：`0.2`

使用方法：

- 发送 `{次数}d{范围}` 即可

使用示例：

- `2d3`

触发前缀：

可用性：可用

> ## emoji融合（EmojiMix）

一个生成emoji融合图的插件

模块位置：`modules.self_contained.emoji_mix`

模块版本：`0.3`

使用方法：

- 发送 '{emoji1}+{emoji2}' 即可

使用示例：

暂无

触发前缀：

可用性：可用



> ## 图库（Gallery）

一个可以自定义图库并发送图片的插件

模块位置：`modules.self_contained.gallery`

模块版本：`0.3`

使用方法：

- 添加图库关键词：添加图库关键词#{图库名}#{关键词}
- 删除图库关键词：删除图库关键词#{关键词}
- 查看图库列表：查看图库列表
- 图库开关：打开/关闭图库{图库名}
- 添加图片：添加{图库名}图片{图片们}

使用示例：

- `添加图库关键词#setu#色图`
- `删除图库关键词#色图`
- `查看图库列表`
- `打开图库setu`
- `关闭图库setu`
- `添加setu图片[图片][图片][图片][图片]`

触发前缀：

可用性：可用

!!! info "配置说明"
    - 对于本地图片文件夹，请使用绝对路径，并在路径最后加上 `/`，示例：`M:\pixiv\`

    - 对于网络地址，直接返回图片的网址直接填入即可，示例：`https://api.mtyqx.cn/api/random.php`

    - 对于网络地址，返回 `json` 的网址，请使用如下格式：`json:{patha}.{pathb}${url}`
    - json示例：
    对如下返回格式，可使用 `json:data.data.|1$https://ovooa.com/API/cosplay/api.php`
    ```json
    {
        "code": "1",
        "text": "获取成功",
        "data": {
            "Title": "【COS正片】王者荣耀 小鹿女瑶cos CN人形团子",
            "data": [
                "http://t2cy.com/d/file/acg/cos/cosplay/2019-05-24/01da1a430bb31368ae402291309f6673.jpg",
            ]
        }
    }
    ```
其中对于 `json数组索引`，请使用 `|{index}` 的格式，路径和网址之间使用 `$` 进行间隔
    

> ## 原神角色卡（GenshinCharaCard）

一个原神角色卡查询插件

模块位置：`modules.self_contained.genshin_chara_card`

模块版本：`0.2`

使用方法：

- 在群中发送 `/原神角色卡 UID 角色名` 即可

使用示例：

- `/原神角色卡 1234567890 芭芭拉`

触发前缀：`/原神角色卡`

可用性：可用

> ## 原神角色语音（GenshinVoice）

发送特定原神角色语音

模块位置：`modules.self_contained.genshin_voice`

模块版本：`0.1`

使用方法：

- 在群中发送 `原神角色说 内容` 即可

使用示例：

- `原神派蒙说 前面的区域，以后在探索吧`

触发前缀：`原神`、`/原神`

可用性：维护中，不可用

> ## Github项目信息（GithubInfo）

可以搜索Github项目信息的插件

模块位置：`modules.self_contained.github_info`

模块版本：`0.2`

使用方法：

- 在群中发送 `/github [-i] {项目名}` 即可

使用示例：

- `/github sagiri-bot`
- `/github -i sagiri-bot`

触发前缀：`/github`

可用性：可用



> ## 群小组（GroupTeam）

一个可以将群内组员分为小组进行呼叫的插件

模块位置：`modules.self_contained.group_team`

模块版本：`0.2`

使用方法：

- 发送 `群小组/group_team 添加分组/创建分组/create <小组名> <@要添加的组员>` 即可创建分组
- 发送 `群小组/group_team 删除分组/解散分组/delete <小组名>` 即可删除分组
- 发送 `群小组/group_team 添加成员/add <小组名> <@要添加的组员>` 即可在分组中添加成员
- 发送 `群小组/group_team 移除成员/删除成员/remove <小组名> <@要移除的组员>` 即可在分组中移除成员
- 发送 `群小组/group_team 通知/呼叫/notice/call <小组名> <要发送的信息>` 即可对小组内成员发送消息
- 发送 `群小组/group_team 列出/显示/列表/show/list` 即可查看所在群组中所有小组
- 发送 `群小组/group_team 列出/显示/列表/show/list <小组名>` 即可查看小组内组员

使用示例：

- `群小组 添加分组 A小组 @要添加的组员`
- `群小组 删除分组 A小组`
- `群小组 添加成员 A小组 @要添加的组员`
- `发送 `群小组 移除成员 A小组 @要移除的组员`
- `发送 `群小组 通知 A小组 上号！`
- `发送 `群小组 列表`
- `发送 `群小组 列出 A小组`

触发前缀：`/群小组`、`/group_team`

可用性：可用

> ## 恶臭数字转换（HomoNumberConverter）

一个将复数域数字转换为114514格式的插件

模块位置：`modules.self_contained.homo_number_converter`

模块版本：`0.1`

使用方法：

- 在群中发送 `/homo {数字}` 即可，注意：这个数字应为实数或复数形式，若复数实部为0，则使用0+xi的格式

使用示例：

- `/homo 123456`
- `/homo 123.456`
- `/homo 123+456i`
- `/homo 123.456+789.012i`
- `/homo 123.456-789.012i`

触发前缀：`/恶臭`、`/homo`

可用性：可用

> ## 热梗查询（HotWordsExplainer）

一个可以查询热门词的插件

模块位置：`modules.self_contained.hot_words_explainer`

模块版本：`0.2`

使用方法：

- 在群中发送 `{keyword}是什么梗`

使用示例：

- `鸡你太美是什么梗`

触发前缀：

可用性：可用

> ## 发病（Ill）

生成对特定对象的发病文

模块位置：`modules.self_contained.ill`

模块版本：`0.2`

使用方法：

- 在群中发送 `/发病 [@target] 内容` 即可，target 未填时默认对自己发病

使用示例：

暂无

触发前缀：`/发病`

可用性：可用

> ## 以图搜图（ImageSearcher）

一个可以以图搜图的插件

模块位置：`modules.self_contained.image_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）

使用示例：

- `/搜图 [图片]`

触发前缀：`搜图`、`以图搜图`、`识图`、`/搜图`、`/以图搜图`、`/识图`

可用性：可用

> ## 我有一个朋友（IHaveAFriend）

一个生成假聊天记录插件

模块位置：`modules.self_contained.i_have_a_friend`

模块版本：`0.1`

使用方法：

- 在群中发送 `我(有一?个)?朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问) [-dark] [@target] 内容` 即可 [@目标]

使用示例：

- `我有一个朋友说 @Alice 我要攻击Bob`
- `我有一个朋友说 -dark @Alice 我要攻击Bob`

触发前缀：`我有一个朋友`、`我有个朋友`、`我朋友`

可用性：可用

> ## 笑话（Joke）

一个生成笑话的插件

模块位置：`modules.self_contained.joke`

模块版本：`0.2`

使用方法：

- 在群中发送 `来点{keyword|法国|苏联|美国}笑话` 即可

使用示例：

- `来点纱雾笑话`
- `来点法国笑话`

触发前缀：

可用性：可用

> ## 关键字回复（KeywordRespondent）

一个关键字回复插件

模块位置：`modules.self_contained.keyword_respondent`

模块版本：`0.3`

使用方法：

- 在群中发送已添加关键词可自动回复
- 在群中发送 `添加[群组][模糊|正则]回复关键词#{keyword}#{reply}` 可添加关键词
- 在群中发送 `删除[群组][模糊|正则]回复关键词#{keyword}` 可删除关键词
- 在群中发送 `查询回复关键词` 可查看所有启用关键词

使用示例：

- `添加回复关键词#你好#看文档去`
- `添加正则回复关键词#想问一下.?#看文档去`
- `添加群组正则回复关键词#想问一下.?#看文档去`
- `添加模糊回复关键词#想问一下#看文档去`
- `删除模糊回复关键词#想问一下`

触发前缀：

可用性：可用

> ## 钉宫语音包（KugimiyaVoice）

一个钉宫语音包插件

模块位置：`modules.self_contained.kugimiya_voice`

模块版本：`0.2`

使用方法：

- 发送 `来点钉宫` 即可

使用示例：

- `来点钉宫`

触发前缀：`来点钉宫`、`/来点钉宫`

可用性：可用

> ## Leetcode信息查询（LeetcodeInfo）

一个可以获取Leetcode信息的插件

模块位置：`modules.self_contained.leetcode_info`

模块版本：`0.2`

使用方法：

- 在群中发送 `leetcode {userslug}` 可查询个人资料（userslug为个人主页地址最后的唯一识别代码）
- 在群中发送 `leetcode 每日一题` 可查询每日一题

使用示例：

- `leetcode test`

触发前缀：`力扣`、`leetcode`、`/力扣`、`/leetcode`

可用性：可用

> ## LoliconAPI图片（LoliconKeywordSearcher）

一个接入lolicon api的插件

模块位置：`modules.self_contained.lolicon_keyword_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `来点{keyword}[色涩瑟]图` 即可

使用示例：

- `来点和泉纱雾色图`

触发前缀：

可用性：可用

> ## 营销号内容生成器（MarketingContentGenerator）

一个营销号内容生成器插件

模块位置：`modules.self_contained.marketing_content_generator`

模块版本：`0.2`

使用方法：

- 在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可

使用示例：

- `营销号#开水#不能直接喝#太烫了不能直接喝`

触发前缀：`营销号`、`/营销号`

可用性：可用

> ## MockingBird语音生成（MockingBird）

MockingBird语音生成

模块位置：`modules.self_contained.mockingbird`

模块版本：`0.3`

使用方法：

- 在群中发送 `纱雾说 {content}` 即可

使用示例：

- `我才没见过那样的人呢`

触发前缀：`纱雾说`、`/纱雾说`

可用性：可用

!!! info "注意"
    此插件因为模型过大而不在仓库中，需要多走几步安装，安装前需要安装如下依赖：
    ```text
    torch
    scipy
    librosa
    numba
    pypinyin
    webrtcvad
    Unidecode
    inflect
    ```
    
    假设你用了 `poetry`，也可以使用 `poetry install -E "mockingbird"`
    
    然后前往[这里](https://github.com/TimeRainStarSky/Sagiri_MockingBird)下载所需要的模型。  
    但是注意，**请不要使用 `git clone` 方法下载**，因为该仓库采用了 `git-lfs` 的存储方式，
    导致直接 `git clone` 的情况下只会下载到一个只有 1kb 大小的占用包  
    请直接进入详细界面，如<https://github.com/TimeRainStarSky/Sagiri_MockingBird/blob/main/mockingbird.txz>，
    然后点击 `Download` 按钮进行下载。

> ## 点歌模块（Music）

一个可以点歌的插件

模块位置：`modules.self_contained.music`

模块版本：`0.1`

使用方法：

- 发送 `/点歌`

使用示例：

暂无

触发前缀：`#点歌`、`点歌`、`.点歌`、`/点歌`

可用性：可用

> ## 网络编译器（NetworkCompiler）

一个网络编译器插件

模块位置：`modules.self_contained.network_compiler`

模块版本：`0.2`

使用方法：

- 在群中发送 `run {language}\n code`即可

使用示例：

- `run py3
print("hello")`

触发前缀：`super`、`compiler`、`run`、`网络编译器`、`run code`、`/super`、`/compiler`、`/run`、`/网络编译器`、`/run code`

可用性：可用

> ## PDF搜索（PDFSearcher）

可以搜索pdf的插件

模块位置：`modules.self_contained.pdf_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `/pdf 书名` 即可

使用示例：

- `/pdf 计算机网络`

触发前缀：`pdf`、`/pdf`

可用性：维护中，不可用

> ## 舔狗日记（PeroDog）

一个获取舔狗日记的插件

模块位置：`modules.self_contained.pero_dog`

模块版本：`0.2`

使用方法：

- 在群中发送 `舔` 即可

使用示例：

暂无

触发前缀：`舔`、`/舔`

可用性：可用

> ## 幻影坦克（PhantomTank）

一个幻影坦克生成器

模块位置：`modules.self_contained.phantom_tank`

模块版本：`0.2`

使用方法：

- 在群中发送 `幻影 [显示图] [隐藏图]` 即可

使用示例：

暂无

触发前缀：

可用性：可用

> ## 哔咔漫画（Pica）

一个接入哔咔漫画的插件，支持搜索关键词，随机漫画，下载漫画，排行榜获取

模块位置：`modules.self_contained.pica`

模块版本：`0.2`

使用方法：

- 在群中发送 `pica search {keyword}` 来搜索特定关键词
- 在群中发送 `pica random` 来获取随机漫画
- 在群中发送 `pica rank -H24/-D7/-D30` 来获取24小时/一周/一月内排行榜
- 在群中发送 `pica download (-message|-forward) {comic_id}` 来获取图片消息/转发消息/压缩文件形式的漫画

使用示例：

- `pica search 和泉纱雾`
- `pica random`
- `pica rank -H24`

触发前缀：`pica`、`哔咔`、`/pica`、`/哔咔`

可用性：可用

> ## 二维码生成器（QrcodeGenerator）

一个生成二维码的插件

模块位置：`modules.self_contained.qrcode_generator`

模块版本：`0.2`

使用方法：

- 在群中发送 `qrcode 内容` 即可（文字）

使用示例：

- `/qrcode SAGIRI-BOT`

触发前缀：`qrcode`、`/qrcode`

可用性：可用

> ## 随机人设（RandomCharacter）

随机生成人设插件

模块位置：`modules.self_contained.random_character`

模块版本：`0.2`

使用方法：

- 在群中发送 `随机人设` 即可

使用示例：

暂无

触发前缀：`随机人设`、`/随机人设`

可用性：可用

> ## 随机餐点（RandomFood）

随机餐点

模块位置：`modules.self_contained.random_food`

模块版本：`0.2`

使用方法：

- 在群中发送 `随机[早餐|午餐|晚餐|奶茶|果茶]` 即可

使用示例：

- `随机早餐`
- `随机午餐`
- `随机奶茶`

触发前缀：

可用性：可用

> ## 随机老婆（RandomWife）

生成随机老婆图片的插件

模块位置：`modules.self_contained.random_wife`

模块版本：`0.2`

使用方法：

- 在群中发送 `[来个老婆|随机老婆]` 即可

使用示例：

暂无

触发前缀：`随机老婆`、`来个老婆`、`/随机老婆`、`/来个老婆`

可用性：可用

> ## 复读机（Repeater）

一个复读插件

模块位置：`modules.self_contained.repeater`

模块版本：`0.2`

使用方法：

- 有两条以上相同信息时自动触发

使用示例：

暂无

触发前缀：

可用性：可用

> ## 腾讯语音合成（Speak）

腾讯语音合成插件

模块位置：`modules.self_contained.speak`

模块版本：`0.2`

使用方法：

- 在群中发送 `说 {content}` 即可

使用示例：

- `说 你好`

触发前缀：`说`、`/说`

可用性：可用

> ## steam游戏信息（SteamGameInfoSearch）

一个可以搜索steam游戏信息的插件

模块位置：`modules.self_contained.steam_game_info_searcher`

模块版本：`0.2`

使用方法：

- 在群中发送 `steam {游戏名}` 即可

使用示例：

- `steam mirror`

触发前缀：`steam`、`/steam`

可用性：可用

> ## 风格图片生成（StylePictureGenerator）

一个可以生成不同风格图片的插件

模块位置：`modules.self_contained.style_picture_generator`

模块版本：`0.2`

使用方法：

- 在群中发送 `[5000兆|ph|yt] 文字1 文字2` 即可

使用示例：

- `5000兆 我操 真的吗`
- `ph porn hub`
- `yt you tube`

触发前缀：

可用性：可用

> ## 超分辨率（SuperResolution）

一个图片超分插件

模块位置：`modules.self_contained.super_resolution`

模块版本：`0.2`

使用方法：

- 在群中发送 `/超分 图片` 即可

使用示例：

暂无

触发前缀：`/超分`

可用性：可用

> ## 塔罗牌（Tarot）

可以抽塔罗牌的插件

模块位置：`modules.self_contained.tarot`

模块版本：`0.2`

使用方法：

- 在群中发送 `塔罗牌` 即可

使用示例：

- `塔罗牌`

触发前缀：`塔罗牌`、`tarot`、`/塔罗牌`、`/tarot`

可用性：可用



> ## 热搜（Trending）

一个获取热搜的插件

模块位置：`modules.self_contained.trending`

模块版本：`0.2`

使用方法：

- 在群中发送 `微博热搜` 即可查看微博热搜
- 在群中发送 `知乎热搜` 即可查看知乎热搜
- 在群中发送 `github热搜` 即可查看github热搜

使用示例：

- `微博热搜`
- `知乎热搜`
- `github热搜`

触发前缀：

可用性：可用

> ## WolframAlpha科学计算（WolframAlpha）

一个接入WolframAlpha的插件

模块位置：`modules.self_contained.wolfram_alpha`

模块版本：`0.2`

使用方法：

- 在群中发送 `/solve {content}` 即可

使用示例：

- `/solve curve trump`

触发前缀：`/solve`

可用性：可用

> ## 群词云生成器（Wordcloud）

群词云生成器

模块位置：`modules.self_contained.wordcloud`

模块版本：`0.2`

使用方法：

- 在群中发送

使用示例：

暂无

触发前缀：

可用性：可用

> ## 那种老师查询（XsList）

一个查老师的插件

模块位置：`modules.self_contained.xslist`

模块版本：`0.2`

使用方法：

- 发送 `/查老师 {作品名/老师名/图片}` 即可

使用示例：

- `/查老师 STARS-256`

触发前缀：`/查老师`、`/xslist`

可用性：可用