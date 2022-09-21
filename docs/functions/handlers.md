# 内置模块

本篇为内置模块，若您不需要使用某一模块，可以删除模块或通过 `saya_manager` 进行管理

其中命令格式使用了正则语法

- (a|b)c 代表 a或b+c，即 ac，bc 都可触发
- ab?c 代表b可选，即 abc，ac 都可触发

> ## 查询成分

一个查询B站成分的插件

模块位置：`sagiri_bot.handler.handlers.dd_check`

使用方法：在群中发送 `/查成分 {B站UID/用户名}` 即可

> ## 原神抽卡

一个原神抽卡插件

模块位置：`sagiri_bot.handler.handlers.genshin_gacha`

使用方法：

- 在群中发送 `原神(10|90|180)连?抽?` 即可进行抽卡
- 在群中发送 `原神(卡池|up|UP)(信息)?` 即可查看目前卡池信息
- 在群中发送 `原神(卡池切换|切换卡池) {pool_name}` 即可切换当前卡池（管理）
- 在群中发送 `更新原神卡池` 即可更新卡池信息（管理）

可修改的参数：

- `sagiri_bot.handler.handlers.genshin_gacha.__init__.py`
    - `Gacha10Limit (line 39)` 为每天可以进行的10连次数
    - `Gacha90Limit (line 40)` 为每天可以进行的90连次数
    - `Gacha180Limit (line 41)` 为每天可以进行的180连次数
- `sagiri_bot.handler.handlers.genshin_gacha.pool_data.py`
    - `AUTO_UPDATE (line 16)` 是否自动更新卡池数据

注意：第一次更新可能会阻塞一段时间直至更新完毕

来源: [Genshin_Impact_bot](https://github.com/H-K-Y/Genshin_Impact_bot)

> ## 原神资源点查询

一个获取原神资源的插件

模块位置：`sagiri_bot.handler.handlers.genshin_resource_points`

使用方法：

- 在群中发送 `原神{resource_name} 在哪里? | 哪里?有 {resource_name}` 即可查看资源地图
- 在群中发送 `原神资源列表` 即可查看资源列表

来源: [Genshin_Impact_bot](https://github.com/H-K-Y/Genshin_Impact_bot)

> ## MockingBird

一个可以生成语音的插件

模块位置：`sagiri_bot.handler.handlers.mockingbird`

使用方法：在群中发送 `纱雾说 {content}` 即可

注意：此插件因为模型过大而不在仓库中，需要多走几步安装，安装前需要安装如下依赖：
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



> ## 哔咔漫画

一个接入哔咔漫画的插件，支持搜索关键词，随机漫画，下载漫画，排行榜获取

注意：使用该组件的情况下，需要在配置中配置 pica 账号密码和代理

模块位置：`sagiri_bot.handler.handlers.pica`

使用方法：

- 在群中发送 `pica search {keyword}` 来搜索特定关键词
- 在群中发送 `pica random` 来获取随机漫画
- 在群中发送 `pica rank -H24/-D7/-D30` 来获取24小时/一周/一月内排行榜
- 在群中发送 `pica download (-message|-forward) {comic_id}` 来获取图片消息/转发消息/压缩文件形式的漫画

> ## 超分辨率

一个图片超分插件

模块位置：`sagiri_bot.handler.handlers.super_resolution`

使用方法：在群中发送 `/超分 图片` 即可

注意：  
若需要使用本插件，请运行 `pip install realesrgan basicsr torch`，或者直接使用`poetry install -E "super_resolution"`，若想使用 `gpu` 进行运算则还需要安装 `CUDA` 和 `CUDNN`，请上网自行寻找教程，各个库版本都应对应才可以使用 `gpu`，若不安装则插件默认不启用

> ## Wordle

Wordle文字游戏

答案为指定长度单词，发送对应长度单词即可。灰色块代表此单词中没有此字母，黄色块代表此单词中有此字母，但该字母所处位置不对，绿色块代表此单词中有此字母且位置正确，猜出单词或用光次数则游戏结束。


模块位置：`sagiri_bot.handler.handlers.wordle`

使用方法：

- 发起游戏：/wordle -l=5 -d=SAT，其中-l/-length为单词长度，-d/-dic为指定词典，默认为5和CET4

- 中途放弃：/wordle -g 或 /wordle -giveup

- 查看提示：/wordle -hint

- 查看数据统计：/wordle -s 或 /wordle -statistic

扩展：可自行添加词库，将词库json放入 `sagiri_bot.handler.handlers.wordle.words` 文件夹即可，json格式如下
```json
{
  ...
  "word": {
    "CHS": "单词",
    "ENG": "word"
  },
  ...
}
```

> ## 查老师

一个查老师的插件

模块位置：`sagiri_bot.handler.handlers.xslist`

使用方法：在群中发送 `/查老师 {作品名/老师名/图片}` 即可

> ## 缩写预测

一个获取英文缩写意思的插件

模块位置：`sagiri_bot.handler.handlers.abbreviated_prediction`

使用方法：在群中发送 `缩 内容` 即可

> ## 普通话转抽象话

一个普通话转抽象话的插件

模块位置：`sagiri_bot.handler.handlers.abstract_message_transformer`

使用方法：在群中发送 `/抽象 文字` 即可

> ## 学术搜索（aminer）

一个可以搜学者、论文、专利的插件

模块位置：`sagiri_bot.handler.handlers.aminer`

使用方法：

- 在群中发送 `/aminer {keyword}` 即可搜索学者
- 在群中发送 `/aminer -paper {keyword}` 即可搜索论文
- 在群中发送 `/aminer -patent {keyword}` 即可搜索专利

> ## 头像趣图

一个可以生成头像相关趣味图的插件

模块位置：`sagiri_bot.handler.handlers.avatar_fun_pic`

使用方法：在群中发送 `(摸|亲|贴|撕|丢|爬|精神支柱|吞) (@目标|目标qq|目标图片)` 即可

来源：部分来自于 [MeetWq](https://github.com/MeetWq/mybot/) & [SuperWaterGod](https://github.com/SuperWaterGod)

> ## 搜番

一个可以搜索番剧信息的插件

模块位置：`sagiri_bot.handler.handlers.bangumi_info_searcher`

使用方法：在群中发送 `番剧 {番剧名}` 即可

注意：可能需要设置代理

> ## 以图搜番

一个可以根据图片搜索番剧的插件

模块位置：`sagiri_bot.handler.handlers.bangumi_searcher`

使用方法：在群中发送 `搜番` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）

注意：可能需要设置代理

> ## BiliBili 7日内新番

一个可以获取BiliBili7日内新番时间表的插件

模块位置：`sagiri_bot.handler.handlers.bilibili_bangumi_scheduler`

使用方法：在群内发送 `[1-7]日内新番` 即可

> ## 黑白生草图

一个生成黑白草图的插件

模块位置：`sagiri_bot.handler.handlers.black_white_grass`

使用方法：在群中发送 `黑白草?图 内容 图片` 即可

> ## 种子搜索

一个可以搜索种子的插件

模块位置：`sagiri_bot.handler.handlers.bt`

使用方法：在群中发送 `/bt + {keyword}` 即可

> ## 智能回复

一个可以实现智能回复的插件

模块位置：`sagiri_bot.handler.handlers.chat_reply`

使用方法：

- 在群中发送 `@bot + 想说的话` 即可
- 使用 `setting -set (speakMode|speak_mode)=value` 即可改变说话方式

其中 `value` 如下：

| 名称      | 描述      | 备注                                   |
|---------|---------|--------------------------------------|
| normal  | 不进行回复   |                                      |
| rainbow | 彩虹屁模式   |                                      |
| chat    | 腾讯云智能回复 | 自行注册腾讯云获取 `secret_id` & `secret_key` |

> ## 色卡生成插件

一个可以生成色卡的插件

模块位置：`sagiri_bot.handler.handlers.color_card`

使用方法：

- 在群中发送 `/色卡 {图片/@成员/qq号/回复有图片的消息}` 即可
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

> ## CP文生成

一个生成CP文的插件

模块位置：`sagiri_bot.handler.handlers.cp_generator`

使用方法：在群中发送 `/cp {攻名字} {受名字}`

> ## 每日新闻早报

一个定时发送每日新闻早报插件

模块位置：`sagiri_bot.handler.handlers.daily_newspaper`

使用方法：自动发送（需打开群内 `daily_newspaper` 开关）

> ## 骰子

一个简单的投骰子插件

模块位置：`sagiri_bot.handler.handlers.dice`

使用方法：在群中发送 `{times}d{range}` 即可

> ## emoji融合

一个生成emoji融合图的插件

模块位置：`sagiri_bot.handler.handlers.emoji_mix`

使用方法：在群中发送 '{emoji1}+{emoji2}' 即可

来源：[nonebot-plugin-emojimix](https://github.com/MeetWq/nonebot-plugin-emojimix)

注意：仅适用于emoji表情，不适用于qq表情

> ## 一个生成转发消息的插件

转发消息生成器

模块位置：`sagiri_bot.handler.handlers.fake_forward`

使用方法：在群中发送 `/fake {content} @target` 即可

> ## 闪照转换插件

闪照转换插件

模块位置：`sagiri_bot.handler.handlers.flash_image_catcher`

使用方法：自动触发，可通过 `setting -set antiFlashImage(anti_flash_image)=False` 关闭

> ## 原神角色卡

一个原神角色卡查询插件

模块位置：`sagiri_bot.handler.handlers.genshin_chara_card`

使用方法：在群中发送 `/原神角色卡 UID 角色名` 即可

> ## 原神每日可获取素材查询

一个可以查询原神每日可获取素材的插件

模块位置：`sagiri_bot.handler.handlers.genshin_material_remind`

使用方法：在群中发送 `原神今日素材` 即可

> ## Github项目搜索

可以搜索Github项目信息的插件

模块位置：`sagiri_bot.handler.handlers.github_info`

使用方法：在群中发送 `github (-i)? {项目名}` 即可，其中 `-i` 为可选项，代表图片化输出

注意：可能需要设置代理

> ## 群小组

一个可以将群内组员分为小组进行呼叫的插件

模块位置：`sagiri_bot.handler.handlers.group_team`

使用方法：
- 发送 `群小组/group_team 添加分组/创建分组/create <小组名> <@要添加的组员>` 即可创建分组
- 发送 `群小组/group_team 删除分组/解散分组/delete <小组名>` 即可删除分组
- 发送 `群小组/group_team 添加成员/add <小组名> <@要添加的组员>` 即可在分组中添加成员
- 发送 `群小组/group_team 移除成员/删除成员/remove <小组名> <@要移除的组员>` 即可在分组中移除成员
- 发送 `群小组/group_team 通知/呼叫/notice/call <小组名> <要发送的信息>` 即可对小组内成员发送消息
- 发送 `群小组/group_team 列出/显示/列表/show/list` 即可查看所在群组中所有小组
- 发送 `群小组/group_team 列出/显示/列表/show/list <小组名>` 即可查看小组内组员

注意：可能需要设置代理

> ## 群词云生成器

群词云生成器

模块位置：`sagiri_bot.handler.handlers.group_wordcloud_generator`

使用方法：

- 在群中发送 `我的日/月/年内总结 {topK} {背景图}` 即可查看个人日/月/年词云
- 在群中发送 `本群日/月/年内总结 {topK} {背景图}` 即可查看群组日/月/年词云（需要权限等级2）
- 其中 `topK` 为关键词数量，`背景图` 为词云的蒙版

> ## 热梗解释

一个可以查询热梗的插件

> 2022.09.21 更新：因为所依赖的API更新，所以现在暂时处于一种不可用状态

模块位置：`sagiri_bot.handler.handlers.hot_words_explainer`

使用方法：在群中发送 `{keyword}是什么梗` 即可

> ## 我有一个朋友

一个生成假聊天记录截图插件

模块位置：`sagiri_bot.handler.handlers.i_have_a_friend`

使用方法：在群中发送 `我(有一?个)?朋友(想问问|说|让我问问|想问|让我问|想知道|让我帮他问问|让我帮他问|让我帮忙问|让我帮忙问问|问) (-dark)? (@目标)? 内容` 即可

> ## 图片存储

一个能够在图库中添加图片的插件

模块位置：`sagiri_bot.handler.handlers.image_adder`

使用方法：在群中发送 `添加(图库名)图片([图片])+` 即可

> ## 以图搜图

一个可以以图搜图的插件

模块位置：`sagiri_bot.handler.handlers.image_searcher`

使用方法：在群中发送 `搜图` 后，等待回应在30s内发送图片即可（多张图片只会搜索第一张）

注意：可能需要设置代理

> ## 图库

一个可以自定义图库发送图片的插件

模块位置：`sagiri_bot.handler.handlers.image_sender`

使用方法：

- 在群中发送设置好的关键词即可
- 在群中发送 `(添加|删除|查看)图库关键词#{gallery_name}#{keyword}` 即可添加/删除/查看图库关键词
- 在群中发送 `查看已加载图库` 即可查看已加载图库

图库配置方法：

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

> ## 笑话生成

一个生成笑话的插件，内置了苏联&美国&法国笑话

模块位置：`sagiri_bot.handler.handlers.joke`

使用方法：在群中发送 `来点{keyword|法国|苏联|美国}笑话`

> ## 关键词回复

一个关键字回复插件，在群中发送已添加关键词可自动回复

模块位置：`sagiri_bot.handler.handlers.keyword_respondent`

使用方法：

- 在群中发送已添加关键词可自动回复
- 在群中发送 `添加[正则|模糊][群组]回复关键词#{keyword}#{reply}` 可添加关键词
- 在群中发送 `删除[正则|模糊][群组]回复关键词#{keyword}` 可删除关键词

> ## 钉宫语音

一个钉宫语音包插件

模块位置：`sagiri_bot.handler.handlers.kugimiya_voice`

使用方法：发送 `来点钉宫` 即可

> ## Leetcode信息

一个可以获取Leetcode信息的插件

模块位置：`sagiri_bot.handler.handlers.leetcode_info`

使用方法：

- 在群中发送 `leetcode userslug` 可查询个人资料（userslug为个人主页地址最后的唯一识别代码）
- 在群中发送 `leetcode每日一题` 可查询每日一题

> ## Lolicon图片

一个接入lolicon api的插件

模块位置：`sagiri_bot.handler.handlers.lolicon_keyword_searcher`

使用方法：在群中发送 `来点{keyword}[色涩瑟]图` 即可

> ## 营销号生成器

一个营销号内容生成器插件

模块位置：`sagiri_bot.handler.handlers.marketing_content_generator`

使用方法：在群中发送 `营销号#事件主体#事件内容#事件另一种说法` 即可

> ## 表情包生成

一个生成趣味表情包的插件

模块位置：`sagiri_bot.handler.handlers.memes`

使用方法：

- 在群中发送 `(nokia|鲁迅说|狂粉|狂爱|喜报|记仇|低语|别说了|一巴掌|滚屏) {content}` 即可
- 在群中发送 `(王境泽|谁反对|曾小贤|连连看|食屎啦你|五年怎么过的) {content1} {content2} {content3} {content4}` 即可
- 在群中发送 `(馋身子|压力大爷|你好骚啊) {content1} {content2} {content3}` 即可 
- 在群中发送 `切格瓦拉 {content} * 6` 即可 
- 在群中发送 `为所欲为 {content} * 9` 即可 

具体说明可查看下方来源链接

来源： [nonebot-plugin-memes](https://github.com/MeetWq/nonebot-plugin-memes)

> ## 消息转图片

将收到的消息合并为图片，支持文字和图片

模块位置：`sagiri_bot.handler.handlers.message_merger`

使用方法：在群中发送 `/merge 文字/图片` 即可

> ## 网络编译器

一个网络编译器插件

模块位置：`sagiri_bot.handler.handlers.network_compiler`

使用方法：在群中发送 `super language\ncode`即可

> ## PDF搜索

一个可以搜索pdf的插件

模块位置：`sagiri_bot.handler.handlers.pdf_searcher`

使用方法：在群中发送 `pdf 书名` 即可

注意：可能需要设置代理

> ## 舔狗日记

一个获取舔狗日记的插件

模块位置：`sagiri_bot.handler.handlers.pero_dog`

使用方法：在群中发送 `舔` 即可

> ## 幻影坦克

一个幻影坦克生成器

模块位置：`sagiri_bot.handler.handlers.phantom_tank`

使用方法：

- 在群中发送 `幻影 [显示图] [隐藏图]` 可获得黑白幻影图
- 在群中发送 `彩色幻影 [显示图] [隐藏图]` 可获得彩色幻影图

> ## 毒鸡汤

一个获取毒鸡汤的插件

模块位置：`sagiri_bot.handler.handlers.poisonous_chicken_soup`

使用方法：在群中发送 `(鸡汤|毒鸡汤|来碗鸡汤)` 即可

> ## 文字转二维码

一个生成二维码的插件，仅支持文字

模块位置：`sagiri_bot.handler.handlers.qrcode_generator`

使用方法：在群中发送 `qrcode {content}` 即可（文字）

> ## 随机人设

一个随机生成人设插件

模块位置：`sagiri_bot.handler.handlers.random_character`

使用方法：在群中发送 `随机人设` 即可

来源：[A60](https://github.com/djkcyl/ABot-Graia)

> ## 随机老婆

一个生成随机老婆图片的插件

模块位置：`sagiri_bot.handler.handlers.random_wife`

使用方法：在群中发送 `(来个老婆|随机老婆)` 即可

> ## 复读机

一个复读插件

模块位置：`sagiri_bot.handler.handlers.repeater`

使用方法：自动触发

> ## 语音合成

一个语音合成插件

模块位置：`sagiri_bot.handler.handlers.speak`

使用方法：在群中发送 `说 {content}` 即可

> ## steam游戏搜索

一个可以搜索steam游戏信息的插件

模块位置：`sagiri_bot.handler.handlers.steam_game_info_searcher`

使用方法：在群中发送 `steam {game_name}` 即可

注意：可能需要设置代理

> ## 风格logo图片生成

一个可以生成不同风格logo图片的插件

模块位置：`sagiri_bot.handler.handlers.style_picture_generator`

使用方法：在群中发送 `(5000兆|ph|yt) {文字1} {文字2}` 即可

其中 `ph` 为 `pornhub` 风格，`yt` 为 `youtube` 风格，`5000兆` 为 `5000兆元` 风格

> ## 塔罗牌

一个可以抽塔罗牌的插件

模块位置：`sagiri_bot.handler.handlers.tarot`

使用方法：在群中发送 `塔罗牌` 即可

来源：[MeetWq](https://github.com/MeetWq/mybot/)

> ## trending

一个获取热搜的插件

模块位置：`sagiri_bot.handler.handlers.trending`

使用方法：

- 在群中发送 `微博热搜` 即可查看微博热搜
- 在群中发送 `知乎热搜` 即可查看知乎热搜
- 在群中发送 `github热搜` 即可查看github热搜

注意：可能需要设置代理

> ## 科学计算

一个接入WolframAlpha的插件

模块位置：`sagiri_bot.handler.handlers.wolfram_alpha`

使用方法：在群中发送 `/solve {content}` 即可

> ## 发病

一个快速发病的插件

模块位置：`sagiri_bot.handler.handlers.ill`

使用方法：在群中发送 `/发病` 即可

> 纱雾，我真的好喜欢你，为了你，我要******