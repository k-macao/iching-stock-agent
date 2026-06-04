# -*- coding: utf-8 -*-
"""
快速启动版本 - 单文件运行
用法: python quick_start.py
"""
import sys
import os
import asyncio
import logging
import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================
@dataclass
class Config:
    pushplus_token: str = os.getenv("PUSHPLUS_TOKEN", "")
    pushplus_template: str = "html"
    output_dir: str = "./output"

config = Config()

# 从 .env 加载
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                os.environ[key] = val
                if key == "PUSHPLUS_TOKEN":
                    config.pushplus_token = val

# ============================================================
# 六十四卦数据
# ============================================================
BAGUA = {
    "乾": {"symbol": "☰", "element": "金", "direction": "西北", "nature": "天", "meaning": "刚健"},
    "坤": {"symbol": "☷", "element": "土", "direction": "西南", "nature": "地", "meaning": "柔顺"},
    "震": {"symbol": "☳", "element": "木", "direction": "东", "nature": "雷", "meaning": "动"},
    "巽": {"symbol": "☴", "element": "木", "direction": "东南", "nature": "风", "meaning": "入"},
    "坎": {"symbol": "☵", "element": "水", "direction": "北", "nature": "水", "meaning": "陷"},
    "离": {"symbol": "☲", "element": "火", "direction": "南", "nature": "火", "meaning": "丽"},
    "艮": {"symbol": "☶", "element": "土", "direction": "东北", "nature": "山", "meaning": "止"},
    "兑": {"symbol": "☱", "element": "金", "direction": "西", "nature": "泽", "meaning": "悦"},
}

HEXAGRAMS = {
    "乾为天": {"upper": "乾", "lower": "乾", "element": "金",
               "judgment": "元亨利贞。天行健，君子以自强不息。",
               "stock_meaning": "高位运行，牛气冲天，注意顶部风险，宜获利了结",
               "signal": "⚠️ 警惕见顶", "trend": "先升后跌"},
    "坤为地": {"upper": "坤", "lower": "坤", "element": "土",
               "judgment": "元亨，利牝马之贞。地势坤，君子以厚德载物。",
               "stock_meaning": "底部夯实，窄幅整理，耐心布局等待时机",
               "signal": "🟢 底部蓄势", "trend": "横盘整理"},
    "水雷屯": {"upper": "坎", "lower": "震", "element": "水木",
               "judgment": "元亨利贞，勿用有攸往，利建侯。",
               "stock_meaning": "初始阶段，进退两难，谨慎观望为宜",
               "signal": "🟡 观望", "trend": "调整期"},
    "山水蒙": {"upper": "艮", "lower": "坎", "element": "土水",
               "judgment": "亨。匪我求童蒙，童蒙求我。",
               "stock_meaning": "市场朦胧不清，方向不明，宜学习和研究",
               "signal": "🟡 迷茫期", "trend": "方向不明"},
    "水天需": {"upper": "坎", "lower": "乾", "element": "水金",
               "judgment": "有孚，光亨，贞吉。利涉大川。",
               "stock_meaning": "密云不雨，等待时机，耐心等待突破",
               "signal": "🟡 等待", "trend": "横盘蓄势"},
    "天水讼": {"upper": "乾", "lower": "坎", "element": "金水",
               "judgment": "有孚窒惕，中吉，终凶。",
               "stock_meaning": "多空分歧严重，震荡加剧，注意风险控制",
               "signal": "🟠 分歧", "trend": "大幅震荡"},
    "地水师": {"upper": "坤", "lower": "坎", "element": "土水",
               "judgment": "贞，丈人吉，无咎。",
               "stock_meaning": "大战在即，资金集结，关注主力资金动向",
               "signal": "🟢 启动", "trend": "即将突破"},
    "水地比": {"upper": "坎", "lower": "坤", "element": "水土",
               "judgment": "吉。原筮元永贞，无咎。",
               "stock_meaning": "众星拱月，人气汇聚，枯树开花",
               "signal": "🟢 看涨", "trend": "温和上涨"},
    "风天小畜": {"upper": "巽", "lower": "乾", "element": "木金",
                 "judgment": "亨。密云不雨，自我西郊。",
                 "stock_meaning": "力量积蓄不足，小幅盘整，酝酿突破",
                 "signal": "🟡 蓄势", "trend": "小幅度整理"},
    "天泽履": {"upper": "乾", "lower": "兑", "element": "金金",
               "judgment": "履虎尾，不咥人，亨。",
               "stock_meaning": "小心跟庄，注意风险，有惊无险",
               "signal": "🟢 谨慎看涨", "trend": "上升但需小心"},
    "地天泰": {"upper": "坤", "lower": "乾", "element": "土金",
               "judgment": "小往大来，吉亨。",
               "stock_meaning": "天地交泰，牛市格局，稳步上升",
               "signal": "🟢🟢 大吉", "trend": "稳步上涨"},
    "天地否": {"upper": "乾", "lower": "坤", "element": "金土",
               "judgment": "否之匪人，不利君子贞，大往小来。",
               "stock_meaning": "天地不交，熊市格局，宜空仓观望",
               "signal": "🔴 大凶", "trend": "持续下跌"},
    "天火同人": {"upper": "乾", "lower": "离", "element": "金火",
                 "judgment": "同人于野，亨。利涉大川。",
                 "stock_meaning": "人心趋同，大势向好，顺势而为",
               "signal": "🟢 看涨", "trend": "上升趋势"},
    "火天大有": {"upper": "离", "lower": "乾", "element": "火金",
                 "judgment": "元亨。",
                 "stock_meaning": "日丽中天，大有收获，顺势做多",
               "signal": "🟢🟢 强看涨", "trend": "强势上涨"},
    "地山谦": {"upper": "坤", "lower": "艮", "element": "土土",
               "judgment": "亨，君子有终。",
               "stock_meaning": "低调运行，谨慎上扬，不宜张扬",
               "signal": "🟢 温和", "trend": "缓慢上涨"},
    "雷地豫": {"upper": "震", "lower": "坤", "element": "木土",
               "judgment": "利建侯行师。",
               "stock_meaning": "欢乐之象，轮番上涨，见好就收",
               "signal": "🟢 偏多", "trend": "活跃上涨"},
    "泽雷随": {"upper": "兑", "lower": "震", "element": "金木",
               "judgment": "元亨利贞，无咎。",
               "stock_meaning": "顺势而为，革故鼎新，跟随大市",
               "signal": "🟢 跟随", "trend": "顺势上涨"},
    "山风蛊": {"upper": "艮", "lower": "巽", "element": "土木",
               "judgment": "元亨，利涉大川。",
               "stock_meaning": "内部腐败，大盘入低谷，需吐故纳新",
               "signal": "🟠 风险", "trend": "阴跌探底"},
    "地泽临": {"upper": "坤", "lower": "兑", "element": "土金",
               "judgment": "元亨利贞。至于八月有凶。",
               "stock_meaning": "转势在即，突破关口，做好进出准备",
               "signal": "🟢 转折", "trend": "即将变盘"},
    "风地观": {"upper": "巽", "lower": "坤", "element": "木土",
               "judgment": "盥而不荐，有孚颙若。",
               "stock_meaning": "观察等待，止跌企稳，不宜急于入场",
               "signal": "🟡 观察", "trend": "止跌企稳"},
    "火雷噬嗑": {"upper": "离", "lower": "震", "element": "火木",
                 "judgment": "亨。利用狱。",
                 "stock_meaning": "障碍当前，多空博弈激烈，注意陷阱",
               "signal": "🔴 风险", "trend": "下跌调整"},
    "山火贲": {"upper": "艮", "lower": "离", "element": "土火",
               "judgment": "亨。小利有攸往。",
               "stock_meaning": "表面繁华，内有阻力，快进快出",
               "signal": "🟡 短线", "trend": "震荡不定"},
    "山地剥": {"upper": "艮", "lower": "坤", "element": "土土",
               "judgment": "不利有攸往。",
               "stock_meaning": "剥落之象，趋势转弱，及时止损",
               "signal": "🔴 看跌", "trend": "持续下跌"},
    "地雷复": {"upper": "坤", "lower": "震", "element": "土木",
               "judgment": "亨。出入无疾，朋来无咎。反复其道。",
               "stock_meaning": "一阳来复，回归起点，生机出现",
               "signal": "🟢 底部反转", "trend": "触底回升"},
    "天雷无妄": {"upper": "乾", "lower": "震", "element": "金木",
                 "judgment": "元亨利贞。其匪正有眚，不利有攸往。",
                 "stock_meaning": "意外之象，与预期偏离，不宜妄动",
               "signal": "🟠 意外", "trend": "飘荡不定"},
    "山天大畜": {"upper": "艮", "lower": "乾", "element": "土金",
                 "judgment": "利贞，不家食吉，利涉大川。",
                 "stock_meaning": "积蓄力量，厚积薄发，将冲破阻力",
               "signal": "🟢 蓄势待发", "trend": "蓄力突破"},
    "山雷颐": {"upper": "艮", "lower": "震", "element": "土木",
               "judgment": "贞吉。观颐，自求口实。",
               "stock_meaning": "蓄势待发，自给自足，耐心等待",
               "signal": "🟡 等待", "trend": "飘悠不定"},
    "泽风大过": {"upper": "兑", "lower": "巽", "element": "金木",
                 "judgment": "栋桡，利有攸往，亨。",
                 "stock_meaning": "升跌过头，风险极大，掌握时机进出",
               "signal": "🟠 过度", "trend": "极端波动"},
    "坎为水": {"upper": "坎", "lower": "坎", "element": "水",
               "judgment": "习坎，有孚，维心亨，行有尚。",
               "stock_meaning": "重重险阻，大跌跳水，及时逃命",
               "signal": "🔴 大凶", "trend": "连续下跌"},
    "离为火": {"upper": "离", "lower": "离", "element": "火",
               "judgment": "利贞，亨。畜牝牛，吉。",
               "stock_meaning": "主升浪来临，人气旺盛，可积极做多",
               "signal": "🟢🟢 大升", "trend": "强势上升"},
    "泽山咸": {"upper": "兑", "lower": "艮", "element": "金土",
               "judgment": "亨，利贞，取女吉。",
               "stock_meaning": "感应相通，人气汇聚，亨通有利",
               "signal": "🟢 看涨", "trend": "和谐上升"},
    "雷风恒": {"upper": "震", "lower": "巽", "element": "木木",
               "judgment": "亨，无咎，利贞，利有攸往。",
               "stock_meaning": "恒久之象，市场稳定，横盘运行",
               "signal": "🟡 横盘", "trend": "横盘整理"},
    "天山遁": {"upper": "乾", "lower": "艮", "element": "金土",
               "judgment": "亨，小利贞。",
               "stock_meaning": "退避之象，空头市场，急流勇退",
               "signal": "🔴 退避", "trend": "持续下跌"},
    "雷天大壮": {"upper": "震", "lower": "乾", "element": "木金",
                 "judgment": "利贞。",
                 "stock_meaning": "牛气冲天但先顺后逆，节制勿贪",
               "signal": "🟠 过盛", "trend": "倒V型反转"},
    "火地晋": {"upper": "离", "lower": "坤", "element": "火土",
               "judgment": "康侯用锡马蕃庶，昼日三接。",
               "stock_meaning": "如日方升，反复震荡后向上",
               "signal": "🟢 看涨", "trend": "震荡上行"},
    "地火明夷": {"upper": "坤", "lower": "离", "element": "土火",
                 "judgment": "利艰贞。",
                 "stock_meaning": "光明受损，暗箭难防，屡屡下挫",
               "signal": "🔴 看跌", "trend": "阴跌不止"},
    "风火家人": {"upper": "巽", "lower": "离", "element": "木火",
                 "judgment": "利女贞。",
                 "stock_meaning": "结构有序，涨升有度，板块轮动",
               "signal": "🟢 有序上涨", "trend": "稳步上升"},
    "火泽睽": {"upper": "离", "lower": "兑", "element": "火金",
               "judgment": "小事吉。",
               "stock_meaning": "多空分歧，二女同居方向不定",
               "signal": "🟡 分歧", "trend": "震荡不定"},
    "水山蹇": {"upper": "坎", "lower": "艮", "element": "水土",
               "judgment": "利西南，不利东北。利见大人，贞吉。",
               "stock_meaning": "市场险阻，艰难跋涉，不宜入场",
               "signal": "🔴 困难", "trend": "下跌调整"},
    "雷水解": {"upper": "震", "lower": "坎", "element": "木水",
               "judgment": "利西南，无所往。其来复吉。",
               "stock_meaning": "走出困境，否极泰来，开始回升",
               "signal": "🟢 解困", "trend": "触底反弹"},
    "山泽损": {"upper": "艮", "lower": "兑", "element": "土金",
               "judgment": "有孚，元吉，无咎，可贞。",
               "stock_meaning": "减损之象，连续跳水，及时止损",
               "signal": "🔴 止损", "trend": "大幅下跌"},
    "风雷益": {"upper": "巽", "lower": "震", "element": "木木",
               "judgment": "利有攸往，利涉大川。",
               "stock_meaning": "有利可图，入市获利但上升不稳",
               "signal": "🟢 获利", "trend": "上升但波动"},
    "泽天夬": {"upper": "兑", "lower": "乾", "element": "金金",
               "judgment": "扬于王庭，孚号有厉。",
               "stock_meaning": "牛熊分水岭，先升后跌，注意逃顶",
               "signal": "🟠 转折", "trend": "倒V型见顶"},
    "天风姤": {"upper": "乾", "lower": "巽", "element": "金木",
               "judgment": "女壮，勿用取女。",
               "stock_meaning": "盛阳遇阴，遭遇空头，先升后跌",
               "signal": "🟠 警惕", "trend": "倒V型回落"},
    "泽地萃": {"upper": "兑", "lower": "坤", "element": "金土",
               "judgment": "亨。王假有庙，利见大人。",
               "stock_meaning": "人气汇聚，多头入市，可积极介入",
               "signal": "🟢 看涨", "trend": "聚集上涨"},
    "地风升": {"upper": "坤", "lower": "巽", "element": "土木",
               "judgment": "元亨，用见大人，勿恤，南征吉。",
               "stock_meaning": "前景看好，走势分明，稳步上升",
               "signal": "🟢 看涨", "trend": "持续上升"},
    "水风井": {"upper": "坎", "lower": "巽", "element": "水木",
               "judgment": "改邑不改井，无丧无得。",
               "stock_meaning": "守静安常，价值洼地，珠落深渊",
               "signal": "🟡 观望", "trend": "低位整理"},
    "泽火革": {"upper": "兑", "lower": "离", "element": "金火",
               "judgment": "巳日乃孚，元亨利贞，悔亡。",
               "stock_meaning": "转势变盘，题材挖尽转变策略",
               "signal": "🟠 变盘", "trend": "趋势转换"},
    "火风鼎": {"upper": "离", "lower": "巽", "element": "火木",
               "judgment": "元吉，亨。",
               "stock_meaning": "鼎新之象，政策引导行业可获大利",
               "signal": "🟢 看涨", "trend": "政策利好驱动"},
    "震为雷": {"upper": "震", "lower": "震", "element": "木",
               "judgment": "亨。震来虩虩，笑言哑哑。震惊百里。",
               "stock_meaning": "大幅震荡，惊吓连连，迅雷不及掩耳",
               "signal": "🟠 剧烈震荡", "trend": "大幅波动"},
    "艮为山": {"upper": "艮", "lower": "艮", "element": "土",
               "judgment": "艮其背，不获其身，行其庭，不见其人。",
               "stock_meaning": "阻力重重，难进难退，停止观望",
               "signal": "🟡 停止", "trend": "横盘止涨"},
    "风山渐": {"upper": "巽", "lower": "艮", "element": "木土",
               "judgment": "女归吉，利贞。",
               "stock_meaning": "循序渐进，慢牛行情或逐步介入",
               "signal": "🟢 慢牛", "trend": "缓慢上升"},
    "雷泽归妹": {"upper": "震", "lower": "兑", "element": "木金",
                 "judgment": "征凶，无攸利。",
                 "stock_meaning": "浮云蔽日，行情不定，哪来哪去",
               "signal": "🟡 不定", "trend": "上下无序"},
    "雷火丰": {"upper": "震", "lower": "离", "element": "木火",
               "judgment": "亨，王假之，勿忧，宜日中。",
               "stock_meaning": "人气沸腾，达到顶峰，注意盛极而衰",
               "signal": "🟢 顶点", "trend": "见顶回落"},
    "火山旅": {"upper": "离", "lower": "艮", "element": "火土",
               "judgment": "小亨，旅贞吉。",
               "stock_meaning": "进退无常，上下跳空，东奔西跑",
               "signal": "🟡 不定", "trend": "无序波动"},
    "巽为风": {"upper": "巽", "lower": "巽", "element": "木",
               "judgment": "小亨，利有攸往，利见大人。",
               "stock_meaning": "象一阵风，风过则无，注意倒V型",
               "signal": "🟠 短暂", "trend": "快速升降"},
    "兑为泽": {"upper": "兑", "lower": "兑", "element": "金",
               "judgment": "亨，利贞。",
               "stock_meaning": "随心所欲，震荡为主，小心偏离",
               "signal": "🟡 震荡", "trend": "箱体震荡"},
    "风水涣": {"upper": "巽", "lower": "坎", "element": "木水",
               "judgment": "亨。王假有庙，利涉大川，利贞。",
               "stock_meaning": "人气涣散，大风吹物，阴跌不止",
               "signal": "🔴 看跌", "trend": "阴跌下行"},
    "水泽节": {"upper": "坎", "lower": "兑", "element": "水金",
               "judgment": "亨。苦节不可贞。",
               "stock_meaning": "升跌有度，横盘整理，多空变换",
               "signal": "🟡 节制度", "trend": "横盘震荡"},
    "风泽中孚": {"upper": "巽", "lower": "兑", "element": "木金",
                 "judgment": "豚鱼吉，利涉大川，利贞。",
                 "stock_meaning": "诚信感通，市场向好，可以进场",
               "signal": "🟢 看涨", "trend": "稳步上升"},
    "雷山小过": {"upper": "震", "lower": "艮", "element": "木土",
                 "judgment": "亨，利贞，可小事，不可大事。",
                 "stock_meaning": "窄幅震荡，不可大玩，控制仓位",
               "signal": "🟡 小波动", "trend": "窄幅整理"},
    "水火既济": {"upper": "坎", "lower": "离", "element": "水火",
                 "judgment": "亨小，利贞，初吉终乱。",
                 "stock_meaning": "条件成熟，达到最高点，注意盛极而衰",
               "signal": "🟠 见顶", "trend": "冲高回落"},
    "火水未济": {"upper": "离", "lower": "坎", "element": "火水",
                 "judgment": "亨，小狐汔济，濡其尾，无攸利。",
                 "stock_meaning": "升跌未到位，可能反走，方向未定",
               "signal": "🟡 未定", "trend": "可能反转"},
}

ELEMENT_MARKET = {
    "金": {"market": "金融、银行、保险、贵金属", "bullish": "金旺则金融股强势", "bearish": "金衰则金融股承压"},
    "木": {"market": "农林、医药、教育、环保", "bullish": "木旺则成长股活跃", "bearish": "木衰则科技股回调"},
    "水": {"market": "航运、物流、旅游、文化传媒", "bullish": "水旺则消费股上涨", "bearish": "水衰则消费股下跌"},
    "火": {"market": "能源、电力、科技、互联网", "bullish": "火旺则科技股爆发", "bearish": "火衰则科技股走弱"},
    "土": {"market": "地产、基建、建材、农业", "bullish": "土旺则周期股走强", "bearish": "土衰则周期股调整"},
}

WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

HEXAGRAM_MAP = {
    "乾乾": "乾为天", "乾兑": "天泽履", "乾离": "天火同人", "乾震": "天雷无妄",
    "乾巽": "天风姤", "乾坎": "天水讼", "乾艮": "天山遁", "乾坤": "天地否",
    "兑乾": "泽天夬", "兑兑": "兑为泽", "兑离": "火泽睽", "兑震": "雷泽归妹",
    "兑巽": "风泽中孚", "兑坎": "水泽节", "兑艮": "山泽损", "兑坤": "地泽临",
    "离乾": "火天大有", "离兑": "泽火革", "离离": "离为火", "离震": "雷火丰",
    "离巽": "风火家人", "离坎": "水火既济", "离艮": "山火贲", "离坤": "地火明夷",
    "震乾": "雷天大壮", "震兑": "泽雷随", "震离": "火雷噬嗑", "震震": "震为雷",
    "震巽": "雷风恒", "震坎": "水雷屯", "震艮": "山雷颐", "震坤": "地雷复",
    "巽乾": "风天小畜", "巽兑": "泽风大过", "巽离": "风火家人", "巽震": "风雷益",
    "巽巽": "巽为风", "巽坎": "风水涣", "巽艮": "风山渐", "巽坤": "地风升",
    "坎乾": "水天需", "坎兑": "泽水困", "坎离": "火水未济", "坎震": "雷水解",
    "坎巽": "水风井", "坎坎": "坎为水", "坎艮": "水山蹇", "坎坤": "地水师",
    "艮乾": "山天大畜", "艮兑": "山泽损", "艮离": "火山旅", "艮震": "雷山小过",
    "艮巽": "风山渐", "艮坎": "水山蹇", "艮艮": "艮为山", "艮坤": "山地剥",
    "坤乾": "地天泰", "坤兑": "泽地萃", "坤离": "火地晋", "坤震": "雷地豫",
    "坤巽": "风地观", "坤坎": "水地比", "坤艮": "地山谦", "坤坤": "坤为地",
}

SECTOR_MAPPING = {
    "金": {"bullish": ["银行", "保险", "券商", "贵金属"], "bearish": ["科技", "新能源"]},
    "木": {"bullish": ["医药", "农业", "环保", "教育"], "bearish": ["地产", "基建"]},
    "水": {"bullish": ["消费", "旅游", "传媒", "航运"], "bearish": ["能源", "电力"]},
    "火": {"bullish": ["科技", "互联网", "新能源", "电子"], "bearish": ["银行", "金融"]},
    "土": {"bullish": ["地产", "基建", "建材", "有色"], "bearish": ["医药", "消费"]},
}


def get_daily_hexagram(date: datetime = None) -> dict:
    """梅花易数时间起卦"""
    if date is None:
        date = datetime.now()
    year, month, day = date.year, date.month, date.day
    hour = date.hour or 12
    upper_num = (year + month + day) % 8
    lower_num = (year + month + day + hour) % 8
    moving_line = (year + month + day + hour) % 6
    bagua_order = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
    upper = bagua_order[upper_num - 1] if upper_num > 0 else bagua_order[7]
    lower = bagua_order[lower_num - 1] if lower_num > 0 else bagua_order[7]
    hex_key = f"{upper}{lower}"
    full_name = HEXAGRAM_MAP.get(hex_key, "乾为天")
    hex_data = HEXAGRAMS.get(full_name, {})
    return {
        "date": date.strftime("%Y-%m-%d"),
        "upper_trigram": upper,
        "lower_trigram": lower,
        "moving_line": moving_line or 6,
        "hexagram_name": full_name,
        **hex_data,
    }


def get_wuxing_info(date: datetime = None) -> dict:
    """获取当日干支五行"""
    if date is None:
        date = datetime.now()
    day_stem = HEAVENLY_STEMS[(date.toordinal() - 720000) % 10]
    day_branch = EARTHLY_BRANCHES[(date.toordinal() - 720000) % 12]
    day_element = WUXING.get(day_stem, "未知")
    return {
        "day_stem": day_stem,
        "day_branch": day_branch,
        "day_element": day_element,
        "sectors": SECTOR_MAPPING.get(day_element, {"bullish": [], "bearish": []}),
    }


def _parse_tencent_quote(line: str) -> Dict:
    """解析腾讯财经行情数据"""
    try:
        # 格式: v_code="市场~名称~代码~最新价~昨收~今开~成交量~..."
        start = line.index('"') + 1
        end = line.rindex('"')
        fields = line[start:end].split("~")
        if len(fields) < 30:
            return {}
        
        name = fields[1]
        code = fields[2]
        price = float(fields[3]) if fields[3] else 0
        prev_close = float(fields[4]) if fields[4] else 0
        open_price = float(fields[5]) if fields[5] else 0
        high = float(fields[33]) if len(fields) > 33 and fields[33] else 0
        low = float(fields[34]) if len(fields) > 34 and fields[34] else 0
        volume = float(fields[6]) if fields[6] else 0
        volume_amount = float(fields[37]) if len(fields) > 37 and fields[37] else 0
        
        change_amt = price - prev_close
        change_pct = (change_amt / prev_close * 100) if prev_close else 0
        
        return {
            "name": name,
            "code": code,
            "price": round(price, 2),
            "prev_close": round(prev_close, 2),
            "open": round(open_price, 2),
            "high": round(high, 2) if high else round(price, 2),
            "low": round(low, 2) if low else round(price, 2),
            "volume": int(volume),
            "volume_amount": int(volume_amount),
            "change_pct": round(change_pct, 2),
            "change_amt": round(change_amt, 2),
        }
    except Exception as e:
        logger.warning(f"解析腾讯行情数据失败: {e}")
        return {}


async def fetch_a_share_indices() -> List[Dict]:
    """获取A股主要指数 (腾讯财经API)"""
    indices = []
    codes = "sh000001,sz399001,sz399006,sh000300"
    try:
        resp = requests.get(f"https://qt.gtimg.cn/q={codes}", timeout=10)
        resp.encoding = "gbk"
        for line in resp.text.strip().split(";"):
            line = line.strip()
            if line:
                data = _parse_tencent_quote(line)
                if data:
                    indices.append(data)
    except Exception as e:
        logger.warning(f"获取A股指数失败: {e}")
    return indices


async def fetch_hk_indices() -> List[Dict]:
    """获取港股指数 (腾讯财经API)"""
    indices = []
    codes = "hkHSI,hkHSTECH,hkHSCEI"
    try:
        resp = requests.get(f"https://qt.gtimg.cn/q={codes}", timeout=10)
        resp.encoding = "gbk"
        for line in resp.text.strip().split(";"):
            line = line.strip()
            if line:
                data = _parse_tencent_quote(line)
                if data:
                    indices.append(data)
    except Exception as e:
        logger.warning(f"获取港股指数失败: {e}")
    return indices


def generate_html_report(hexagram: dict, wuxing: dict,
                         a_indices: list, h_indices: list) -> str:
    """生成美观的HTML报告"""
    upper = BAGUA.get(hexagram.get("upper_trigram", ""), {})
    lower = BAGUA.get(hexagram.get("lower_trigram", ""), {})
    upper_symbol = f"{upper.get('symbol', '')}{upper.get('nature', '')}"
    lower_symbol = f"{lower.get('symbol', '')}{lower.get('nature', '')}"

    signal = hexagram.get("signal", "")
    trend = hexagram.get("trend", "")
    if "🟢" in signal or "看涨" in signal or "涨" in trend:
        signal_bg = "#e8f5e9"; signal_color = "#2e7d32"
    elif "🔴" in signal or "看跌" in signal or "跌" in trend:
        signal_bg = "#ffebee"; signal_color = "#c62828"
    else:
        signal_bg = "#fff3e0"; signal_color = "#e65100"

    a_bull = sum(1 for i in a_indices if i.get("change_pct", 0) > 0.5)
    a_bear = sum(1 for i in a_indices if i.get("change_pct", 0) < -0.5)
    h_bull = sum(1 for i in h_indices if i.get("change_pct", 0) > 0.5)
    h_bear = sum(1 for i in h_indices if i.get("change_pct", 0) < -0.5)

    if "🟢" in signal:
        ratings = ["bullish"]
    elif "🔴" in signal:
        ratings = ["bearish"]
    else:
        ratings = ["neutral"]
    if a_bull > a_bear:
        ratings.append("bullish")
    elif a_bear > a_bull:
        ratings.append("bearish")
    bullish = ratings.count("bullish")
    bearish = ratings.count("bearish")

    if bullish >= 2:
        overall_rating = "🟢 偏多"; overall_bg = "#e8f5e9"; overall_color = "#2e7d32"
    elif bearish >= 2:
        overall_rating = "🔴 偏空"; overall_bg = "#ffebee"; overall_color = "#c62828"
    else:
        overall_rating = "🟡 震荡"; overall_bg = "#fff3e0"; overall_color = "#e65100"

    def idx_row(idx):
        change = idx.get("change_pct", 0)
        c_class = "up" if change > 0 else ("down" if change < 0 else "neutral-c")
        return f"""<tr>
            <td>{idx.get('name', '')}</td>
            <td>{idx.get('price', 0) or 'N/A'}</td>
            <td class="{c_class}">{change:+.2f}%</td>
            <td>{idx.get('change_amt', 0):+.2f}</td>
        </tr>"""

    bullish_sectors = wuxing.get("sectors", {}).get("bullish", [])
    bearish_sectors = wuxing.get("sectors", {}).get("bearish", [])
    sector_html = ""
    if bullish_sectors:
        sector_html += '<div style="margin-top:8px;"><b style="color:#2e7d32;">📈 今日利好板块:</b><br>'
        for s in bullish_sectors:
            sector_html += f'<span style="display:inline-block;padding:3px 10px;margin:3px;background:#e8f5e9;color:#2e7d32;border-radius:12px;font-size:13px;">{s}</span>'
        sector_html += '</div>'
    if bearish_sectors:
        sector_html += '<div style="margin-top:8px;"><b style="color:#c62828;">📉 今日注意板块:</b><br>'
        for s in bearish_sectors:
            sector_html += f'<span style="display:inline-block;padding:3px 10px;margin:3px;background:#ffebee;color:#c62828;border-radius:12px;font-size:13px;">{s}</span>'
        sector_html += '</div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background: #f5f7fa; color: #333; }}
.container {{ max-width: 680px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
.header {{ background: linear-gradient(135deg, #1a237e, #283593); color: #fff; padding: 28px 24px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 22px; }}
.header .date {{ font-size: 13px; opacity: 0.85; margin-top: 6px; }}
.rating-badge {{ display: inline-block; padding: 8px 24px; border-radius: 20px; font-size: 17px; font-weight: bold; margin-top: 14px; background: {overall_bg}; color: {overall_color}; }}
.section {{ padding: 18px 22px; border-bottom: 1px solid #f0f0f0; }}
.section:last-child {{ border-bottom: none; }}
.section-title {{ font-size: 17px; font-weight: bold; color: #1a237e; margin-bottom: 14px; padding-bottom: 6px; border-bottom: 2px solid #e8eaf6; }}
.hex-display {{ text-align: center; padding: 18px; background: #fafbfc; border-radius: 10px; margin-bottom: 12px; }}
.hex-name {{ font-size: 24px; font-weight: bold; margin-bottom: 6px; }}
.hex-symbols {{ font-size: 20px; margin-bottom: 8px; color: #666; }}
.signal-badge {{ display: inline-block; padding: 5px 14px; border-radius: 14px; font-size: 14px; font-weight: bold; margin: 4px; background: {signal_bg}; color: {signal_color}; }}
.judgment {{ font-style: italic; color: #555; padding: 12px 14px; background: #fff8e1; border-left: 4px solid #ffc107; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 14px; line-height: 1.7; }}
.stock-meaning {{ padding: 12px 14px; background: #e3f2fd; border-left: 4px solid #2196f3; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 14px; line-height: 1.7; }}
.wuxing-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 14px 0; }}
.wuxing-card {{ padding: 12px; background: #f8f9fa; border-radius: 8px; text-align: center; }}
.wuxing-card .label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
.wuxing-card .value {{ font-size: 15px; font-weight: bold; color: #333; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
th {{ background: #f8f9fa; font-weight: bold; color: #555; font-size: 13px; }}
.up {{ color: #e53935; font-weight: bold; }}
.down {{ color: #43a047; font-weight: bold; }}
.neutral-c {{ color: #888; }}
.footer {{ padding: 16px 22px; background: #f5f5f5; text-align: center; font-size: 11px; color: #999; }}
.recommendations {{ list-style: none; padding: 0; margin: 0; }}
.recommendations li {{ padding: 8px 12px; margin-bottom: 6px; background: #f8f9fa; border-radius: 6px; border-left: 3px solid #2196f3; font-size: 14px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>☯️ 每日A股港股周易分析</h1>
        <div class="date">📅 {hexagram['date']}</div>
        <div class="rating-badge">{overall_rating}</div>
    </div>
    <div class="section">
        <div class="section-title">☯️ 今日卦象</div>
        <div class="hex-display">
            <div class="hex-name">{hexagram.get('hexagram_name', 'N/A')}</div>
            <div class="hex-symbols">上{upper_symbol} ｜ 下{lower_symbol}</div>
            <div>
                <span class="signal-badge">{hexagram.get('signal', '')}</span>
                <span class="signal-badge">趋势: {hexagram.get('trend', '')}</span>
            </div>
        </div>
        <div class="judgment">📖 <b>卦辞:</b> {hexagram.get('judgment', '')}</div>
        <div class="stock-meaning">💡 <b>股市解读:</b> {hexagram.get('stock_meaning', '')}</div>
        <div class="wuxing-grid">
            <div class="wuxing-card"><div class="label">📅 日干</div><div class="value">{wuxing.get('day_stem', 'N/A')}</div></div>
            <div class="wuxing-card"><div class="label">📅 日支</div><div class="value">{wuxing.get('day_branch', 'N/A')}</div></div>
            <div class="wuxing-card"><div class="label">🔥 五行</div><div class="value">{wuxing.get('day_element', 'N/A')}</div></div>
            <div class="wuxing-card"><div class="label">⚖️ 卦五行</div><div class="value">{hexagram.get('element', 'N/A')}</div></div>
        </div>
        {sector_html}
    </div>
    <div class="section">
        <div class="section-title">📈 A股指数行情</div>
        <table>
            <tr><th>指数</th><th>最新价</th><th>涨跌幅</th><th>涨跌额</th></tr>
            {''.join(idx_row(i) for i in a_indices) if a_indices else '<tr><td colspan="4" style="text-align:center;color:#888;">数据获取中...</td></tr>'}
        </table>
    </div>
    <div class="section">
        <div class="section-title">🇭🇰 港股指数行情</div>
        <table>
            <tr><th>指数</th><th>最新价</th><th>涨跌幅</th><th>涨跌额</th></tr>
            {''.join(idx_row(i) for i in h_indices) if h_indices else '<tr><td colspan="4" style="text-align:center;color:#888;">数据获取中...</td></tr>'}
        </table>
    </div>
    <div class="section">
        <div class="section-title">💡 综合研判</div>
        <ul class="recommendations">
            <li>☯️ <b>卦象:</b> {hexagram.get('hexagram_name', 'N/A')} - {hexagram.get('stock_meaning', '')}</li>
            <li>📈 <b>A股:</b> {f"{a_bull}涨{a_bear}跌" if a_indices else "数据未获取"} - {"偏多" if a_bull > a_bear else "偏空" if a_bear > a_bull else "震荡"}</li>
            <li>🇭🇰 <b>港股:</b> {f"{h_bull}涨{h_bear}跌" if h_indices else "数据未获取"} - {"偏多" if h_bull > h_bear else "偏空" if h_bear > h_bull else "震荡"}</li>
            <li>🔥 <b>五行:</b> 今日{wuxing.get("day_element", "")}日，{ELEMENT_MARKET.get(wuxing.get("day_element", ""), {}).get("bullish", "")}</li>
            <li>📊 <b>综合:</b> {overall_rating} - 建议结合卦象与技术面综合判断</li>
        </ul>
    </div>
    <div class="footer">
        <p>☯️ 每日A股港股周易分析智能体 | {hexagram['date']}</p>
        <p>⚠️ 本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    </div>
</div>
</body>
</html>"""
    return html


def push_to_wechat(title: str, content: str) -> bool:
    """推送消息到微信"""
    token = config.pushplus_token
    if not token:
        logger.warning("⚠️ PushPlus Token 未配置")
        return False
    try:
        url = "https://www.pushplus.plus/send"
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": config.pushplus_template,
        }
        resp = requests.post(url, json=data, timeout=30)
        result = resp.json()
        if result.get("code") == 200:
            logger.info("✅ PushPlus推送成功")
            return True
        else:
            logger.error(f"❌ PushPlus推送失败: {result}")
            return False
    except Exception as e:
        logger.error(f"❌ PushPlus推送异常: {e}")
        return False


async def run_analysis():
    """执行完整的每日分析流程"""
    logger.info("=" * 60)
    logger.info("🔮 每日A股港股周易分析智能体启动")
    logger.info("=" * 60)
    start_time = datetime.now()

    # Phase 1: 计算卦象
    logger.info("☯️ 计算今日卦象...")
    hexagram = get_daily_hexagram(start_time)
    wuxing = get_wuxing_info(start_time)
    logger.info(f"  今日卦象: {hexagram['hexagram_name']}")
    logger.info(f"  信号: {hexagram['signal']}")
    logger.info(f"  趋势: {hexagram['trend']}")
    logger.info(f"  五行: {wuxing['day_element']}")

    # Phase 2: 获取行情数据
    logger.info("📊 获取行情数据...")
    a_indices = await fetch_a_share_indices()
    h_indices = await fetch_hk_indices()
    logger.info(f"  A股指数: {len(a_indices)} 个")
    logger.info(f"  港股指数: {len(h_indices)} 个")

    # Phase 3: 生成报告
    logger.info("📝 生成HTML报告...")
    html_report = generate_html_report(hexagram, wuxing, a_indices, h_indices)

    # Phase 4: 保存报告
    os.makedirs(config.output_dir, exist_ok=True)
    date_str = start_time.strftime("%Y%m%d")
    report_path = os.path.join(config.output_dir, f"daily_report_{date_str}.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    logger.info(f"  报告已保存: {report_path}")

    # Phase 5: 推送通知
    logger.info("📤 推送通知到微信...")
    push_title = f"📈 每日A股港股分析 | {start_time.strftime('%Y-%m-%d')}"
    push_sent = push_to_wechat(push_title, html_report)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("=" * 60)
    logger.info(f"✅ 分析完成! 耗时: {duration:.1f}秒")
    logger.info(f"📊 卦象: {hexagram['hexagram_name']} - {hexagram['signal']}")
    logger.info(f"📈 推送: {'✅ 成功' if push_sent else '❌ 失败'}")
    logger.info("=" * 60)
    return {
        "hexagram": hexagram,
        "wuxing": wuxing,
        "a_indices": a_indices,
        "h_indices": h_indices,
        "report_path": report_path,
        "push_sent": push_sent,
    }


def main():
    """主入口"""
    result = asyncio.run(run_analysis())
    return result


if __name__ == "__main__":
    main()
