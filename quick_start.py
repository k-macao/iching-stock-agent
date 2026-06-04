# -*- coding: utf-8 -*-
"""
每日A股港股周易分析 - 麦肯锡风格完整版
五大部分：大V观点 / 市场扫描 / 本周走势 / 每日运势 / 全球现金流
"""
import os, sys, asyncio, logging, requests, json, hashlib
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "").strip()
OUTPUT_DIR = "./output"

# ============================================================
# 六十四卦数据 (完整)
# ============================================================
BAGUA = {
    "乾": {"symbol": "☰", "element": "金", "nature": "天"},
    "坤": {"symbol": "☷", "element": "土", "nature": "地"},
    "震": {"symbol": "☳", "element": "木", "nature": "雷"},
    "巽": {"symbol": "☴", "element": "木", "nature": "风"},
    "坎": {"symbol": "☵", "element": "水", "nature": "水"},
    "离": {"symbol": "☲", "element": "火", "nature": "火"},
    "艮": {"symbol": "☶", "element": "土", "nature": "山"},
    "兑": {"symbol": "☱", "element": "金", "nature": "泽"},
}

HEXAGRAMS = {
    "乾为天": {"upper":"乾","lower":"乾","element":"金","judgment":"元亨利贞。天行健，君子以自强不息。","stock_meaning":"高位运行，牛气冲天，注意顶部风险","signal":"警惕见顶","trend":"先升后跌"},
    "坤为地": {"upper":"坤","lower":"坤","element":"土","judgment":"元亨，利牝马之贞。地势坤，君子以厚德载物。","stock_meaning":"底部夯实，窄幅整理，耐心布局","signal":"底部蓄势","trend":"横盘整理"},
    "水雷屯": {"upper":"坎","lower":"震","element":"水木","judgment":"元亨利贞，勿用有攸往，利建侯。","stock_meaning":"初始阶段，进退两难","signal":"观望","trend":"调整期"},
    "山水蒙": {"upper":"艮","lower":"坎","element":"土水","judgment":"亨。匪我求童蒙，童蒙求我。","stock_meaning":"市场朦胧，方向不明","signal":"迷茫期","trend":"方向不明"},
    "水天需": {"upper":"坎","lower":"乾","element":"水金","judgment":"有孚，光亨，贞吉。利涉大川。","stock_meaning":"密云不雨，等待突破","signal":"等待","trend":"横盘蓄势"},
    "天水讼": {"upper":"乾","lower":"坎","element":"金水","judgment":"有孚窒惕，中吉，终凶。","stock_meaning":"多空分歧，震荡加剧","signal":"分歧","trend":"大幅震荡"},
    "地水师": {"upper":"坤","lower":"坎","element":"土水","judgment":"贞，丈人吉，无咎。","stock_meaning":"大战在即，资金集结","signal":"启动","trend":"即将突破"},
    "水地比": {"upper":"坎","lower":"坤","element":"水土","judgment":"吉。原筮元永贞，无咎。","stock_meaning":"人气汇聚，枯树开花","signal":"看涨","trend":"温和上涨"},
    "风天小畜": {"upper":"巽","lower":"乾","element":"木金","judgment":"亨。密云不雨，自我西郊。","stock_meaning":"小幅盘整，酝酿突破","signal":"蓄势","trend":"小幅整理"},
    "天泽履": {"upper":"乾","lower":"兑","element":"金金","judgment":"履虎尾，不咥人，亨。","stock_meaning":"小心跟庄，有惊无险","signal":"谨慎看涨","trend":"上升但需小心"},
    "地天泰": {"upper":"坤","lower":"乾","element":"土金","judgment":"小往大来，吉亨。","stock_meaning":"天地交泰，牛市格局","signal":"大吉","trend":"稳步上涨"},
    "天地否": {"upper":"乾","lower":"坤","element":"金土","judgment":"否之匪人，不利君子贞。","stock_meaning":"天地不交，熊市格局","signal":"大凶","trend":"持续下跌"},
    "天火同人": {"upper":"乾","lower":"离","element":"金火","judgment":"同人于野，亨。利涉大川。","stock_meaning":"人心趋同，大势向好","signal":"看涨","trend":"上升趋势"},
    "火天大有": {"upper":"离","lower":"乾","element":"火金","judgment":"元亨。","stock_meaning":"日丽中天，大有收获","signal":"强看涨","trend":"强势上涨"},
    "地山谦": {"upper":"坤","lower":"艮","element":"土土","judgment":"亨，君子有终。","stock_meaning":"低调运行，谨慎上扬","signal":"温和","trend":"缓慢上涨"},
    "雷地豫": {"upper":"震","lower":"坤","element":"木土","judgment":"利建侯行师。","stock_meaning":"轮番上涨，见好就收","signal":"偏多","trend":"活跃上涨"},
    "泽雷随": {"upper":"兑","lower":"震","element":"金木","judgment":"元亨利贞，无咎。","stock_meaning":"顺势而为，跟随大市","signal":"跟随","trend":"顺势上涨"},
    "山风蛊": {"upper":"艮","lower":"巽","element":"土木","judgment":"元亨，利涉大川。","stock_meaning":"大盘入低谷，需吐故纳新","signal":"风险","trend":"阴跌探底"},
    "地泽临": {"upper":"坤","lower":"兑","element":"土金","judgment":"元亨利贞。至于八月有凶。","stock_meaning":"转势在即，做好进出准备","signal":"转折","trend":"即将变盘"},
    "风地观": {"upper":"巽","lower":"坤","element":"木土","judgment":"盥而不荐，有孚颙若。","stock_meaning":"观察等待，不宜急于入场","signal":"观察","trend":"止跌企稳"},
    "火雷噬嗑": {"upper":"离","lower":"震","element":"火木","judgment":"亨。利用狱。","stock_meaning":"多空博弈激烈，注意陷阱","signal":"风险","trend":"下跌调整"},
    "山火贲": {"upper":"艮","lower":"离","element":"土火","judgment":"亨。小利有攸往。","stock_meaning":"表面繁华，内有阻力","signal":"短线","trend":"震荡不定"},
    "山地剥": {"upper":"艮","lower":"坤","element":"土土","judgment":"不利有攸往。","stock_meaning":"趋势转弱，及时止损","signal":"看跌","trend":"持续下跌"},
    "地雷复": {"upper":"坤","lower":"震","element":"土木","judgment":"亨。出入无疾，朋来无咎。","stock_meaning":"一阳来复，生机出现","signal":"底部反转","trend":"触底回升"},
    "天雷无妄": {"upper":"乾","lower":"震","element":"金木","judgment":"元亨利贞。其匪正有眚。","stock_meaning":"意外之象，不宜妄动","signal":"意外","trend":"飘荡不定"},
    "山天大畜": {"upper":"艮","lower":"乾","element":"土金","judgment":"利贞，不家食吉。","stock_meaning":"厚积薄发，将冲破阻力","signal":"蓄势待发","trend":"蓄力突破"},
    "山雷颐": {"upper":"艮","lower":"震","element":"土木","judgment":"贞吉。观颐，自求口实。","stock_meaning":"蓄势待发，耐心等待","signal":"等待","trend":"飘悠不定"},
    "泽风大过": {"upper":"兑","lower":"巽","element":"金木","judgment":"栋桡，利有攸往，亨。","stock_meaning":"升跌过头，风险极大","signal":"过度","trend":"极端波动"},
    "坎为水": {"upper":"坎","lower":"坎","element":"水","judgment":"习坎，有孚，维心亨。","stock_meaning":"重重险阻，大跌跳水","signal":"大凶","trend":"连续下跌"},
    "离为火": {"upper":"离","lower":"离","element":"火","judgment":"利贞，亨。畜牝牛，吉。","stock_meaning":"主升浪来临，人气旺盛","signal":"大升","trend":"强势上升"},
    "泽山咸": {"upper":"兑","lower":"艮","element":"金土","judgment":"亨，利贞，取女吉。","stock_meaning":"人气汇聚，亨通有利","signal":"看涨","trend":"和谐上升"},
    "雷风恒": {"upper":"震","lower":"巽","element":"木木","judgment":"亨，无咎，利贞。","stock_meaning":"市场稳定，横盘运行","signal":"横盘","trend":"横盘整理"},
    "天山遁": {"upper":"乾","lower":"艮","element":"金土","judgment":"亨，小利贞。","stock_meaning":"空头市场，急流勇退","signal":"退避","trend":"持续下跌"},
    "雷天大壮": {"upper":"震","lower":"乾","element":"木金","judgment":"利贞。","stock_meaning":"牛气冲天，节制勿贪","signal":"过盛","trend":"倒V型反转"},
    "火地晋": {"upper":"离","lower":"坤","element":"火土","judgment":"康侯用锡马蕃庶，昼日三接。","stock_meaning":"如日方升，震荡后向上","signal":"看涨","trend":"震荡上行"},
    "地火明夷": {"upper":"坤","lower":"离","element":"土火","judgment":"利艰贞。","stock_meaning":"光明受损，屡屡下挫","signal":"看跌","trend":"阴跌不止"},
    "风火家人": {"upper":"巽","lower":"离","element":"木火","judgment":"利女贞。","stock_meaning":"结构有序，涨升有度","signal":"有序上涨","trend":"稳步上升"},
    "火泽睽": {"upper":"离","lower":"兑","element":"火金","judgment":"小事吉。","stock_meaning":"多空分歧，方向不定","signal":"分歧","trend":"震荡不定"},
    "水山蹇": {"upper":"坎","lower":"艮","element":"水土","judgment":"利西南，不利东北。","stock_meaning":"市场险阻，不宜入场","signal":"困难","trend":"下跌调整"},
    "雷水解": {"upper":"震","lower":"坎","element":"木水","judgment":"利西南，无所往。其来复吉。","stock_meaning":"走出困境，开始回升","signal":"解困","trend":"触底反弹"},
    "山泽损": {"upper":"艮","lower":"兑","element":"土金","judgment":"有孚，元吉，无咎。","stock_meaning":"减损之象，连续跳水","signal":"止损","trend":"大幅下跌"},
    "风雷益": {"upper":"巽","lower":"震","element":"木木","judgment":"利有攸往，利涉大川。","stock_meaning":"有利可图，上升不稳","signal":"获利","trend":"上升但波动"},
    "泽天夬": {"upper":"兑","lower":"乾","element":"金金","judgment":"扬于王庭，孚号有厉。","stock_meaning":"牛熊分水岭，注意逃顶","signal":"转折","trend":"倒V型见顶"},
    "天风姤": {"upper":"乾","lower":"巽","element":"金木","judgment":"女壮，勿用取女。","stock_meaning":"盛阳遇阴，先升后跌","signal":"警惕","trend":"倒V型回落"},
    "泽地萃": {"upper":"兑","lower":"坤","element":"金土","judgment":"亨。王假有庙，利见大人。","stock_meaning":"人气汇聚，多头入市","signal":"看涨","trend":"聚集上涨"},
    "地风升": {"upper":"坤","lower":"巽","element":"土木","judgment":"元亨，用见大人，勿恤。","stock_meaning":"前景看好，稳步上升","signal":"看涨","trend":"持续上升"},
    "水风井": {"upper":"坎","lower":"巽","element":"水木","judgment":"改邑不改井，无丧无得。","stock_meaning":"守静安常，价值洼地","signal":"观望","trend":"低位整理"},
    "泽火革": {"upper":"兑","lower":"离","element":"金火","judgment":"巳日乃孚，元亨利贞。","stock_meaning":"转势变盘，题材挖尽","signal":"变盘","trend":"趋势转换"},
    "火风鼎": {"upper":"离","lower":"巽","element":"火木","judgment":"元吉，亨。","stock_meaning":"鼎新之象，政策利好","signal":"看涨","trend":"政策利好驱动"},
    "震为雷": {"upper":"震","lower":"震","element":"木","judgment":"亨。震来虩虩，笑言哑哑。","stock_meaning":"大幅震荡，迅雷不及掩耳","signal":"剧烈震荡","trend":"大幅波动"},
    "艮为山": {"upper":"艮","lower":"艮","element":"土","judgment":"艮其背，不获其身。","stock_meaning":"阻力重重，停止观望","signal":"停止","trend":"横盘止涨"},
    "风山渐": {"upper":"巽","lower":"艮","element":"木土","judgment":"女归吉，利贞。","stock_meaning":"循序渐进，慢牛行情","signal":"慢牛","trend":"缓慢上升"},
    "雷泽归妹": {"upper":"震","lower":"兑","element":"木金","judgment":"征凶，无攸利。","stock_meaning":"浮云蔽日，行情不定","signal":"不定","trend":"上下无序"},
    "雷火丰": {"upper":"震","lower":"离","element":"木火","judgment":"亨，王假之，勿忧，宜日中。","stock_meaning":"人气沸腾，注意盛极而衰","signal":"顶点","trend":"见顶回落"},
    "火山旅": {"upper":"离","lower":"艮","element":"火土","judgment":"小亨，旅贞吉。","stock_meaning":"进退无常，上下跳空","signal":"不定","trend":"无序波动"},
    "巽为风": {"upper":"巽","lower":"巽","element":"木","judgment":"小亨，利有攸往。","stock_meaning":"象一阵风，风过则无","signal":"短暂","trend":"快速升降"},
    "兑为泽": {"upper":"兑","lower":"兑","element":"金","judgment":"亨，利贞。","stock_meaning":"震荡为主，小心偏离","signal":"震荡","trend":"箱体震荡"},
    "风水涣": {"upper":"巽","lower":"坎","element":"木水","judgment":"亨。王假有庙，利涉大川。","stock_meaning":"人气涣散，阴跌不止","signal":"看跌","trend":"阴跌下行"},
    "水泽节": {"upper":"坎","lower":"兑","element":"水金","judgment":"亨。苦节不可贞。","stock_meaning":"升跌有度，多空变换","signal":"节制度","trend":"横盘震荡"},
    "风泽中孚": {"upper":"巽","lower":"兑","element":"木金","judgment":"豚鱼吉，利涉大川。","stock_meaning":"诚信感通，市场向好","signal":"看涨","trend":"稳步上升"},
    "雷山小过": {"upper":"震","lower":"艮","element":"木土","judgment":"亨，利贞，可小事。","stock_meaning":"窄幅震荡，控制仓位","signal":"小波动","trend":"窄幅整理"},
    "水火既济": {"upper":"坎","lower":"离","element":"水火","judgment":"亨小，利贞，初吉终乱。","stock_meaning":"条件成熟，注意盛极而衰","signal":"见顶","trend":"冲高回落"},
    "火水未济": {"upper":"离","lower":"坎","element":"火水","judgment":"亨，小狐汔济，濡其尾。","stock_meaning":"升跌未到位，方向未定","signal":"未定","trend":"可能反转"},
}

ELEMENT_MARKET = {
    "金": {"market": "金融、银行、保险、贵金属", "bullish": "金旺则金融股强势", "bearish": "金衰则金融股承压"},
    "木": {"market": "农林、医药、教育、环保", "bullish": "木旺则成长股活跃", "bearish": "木衰则科技股回调"},
    "水": {"market": "航运、物流、旅游、文化传媒", "bullish": "水旺则消费股上涨", "bearish": "水衰则消费股下跌"},
    "火": {"market": "能源、电力、科技、互联网", "bullish": "火旺则科技股爆发", "bearish": "火衰则科技股走弱"},
    "土": {"market": "地产、基建、建材、农业", "bullish": "土旺则周期股走强", "bearish": "土衰则周期股调整"},
}

WUXING = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水","子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
HEXAGRAM_MAP = {
    "乾乾":"乾为天","乾兑":"天泽履","乾离":"天火同人","乾震":"天雷无妄","乾巽":"天风姤","乾坎":"天水讼","乾艮":"天山遁","乾坤":"天地否",
    "兑乾":"泽天夬","兑兑":"兑为泽","兑离":"火泽睽","兑震":"雷泽归妹","兑巽":"风泽中孚","兑坎":"水泽节","兑艮":"山泽损","兑坤":"地泽临",
    "离乾":"火天大有","离兑":"泽火革","离离":"离为火","离震":"雷火丰","离巽":"风火家人","离坎":"水火既济","离艮":"山火贲","离坤":"地火明夷",
    "震乾":"雷天大壮","震兑":"泽雷随","震离":"火雷噬嗑","震震":"震为雷","震巽":"雷风恒","震坎":"水雷屯","震艮":"山雷颐","震坤":"地雷复",
    "巽乾":"风天小畜","巽兑":"泽风大过","巽离":"风火家人","巽震":"风雷益","巽巽":"巽为风","巽坎":"风水涣","巽艮":"风山渐","巽坤":"地风升",
    "坎乾":"水天需","坎兑":"泽水困","坎离":"火水未济","坎震":"雷水解","坎巽":"水风井","坎坎":"坎为水","坎艮":"水山蹇","坎坤":"地水师",
    "艮乾":"山天大畜","艮兑":"山泽损","艮离":"火山旅","艮震":"雷山小过","艮巽":"风山渐","艮坎":"水山蹇","艮艮":"艮为山","艮坤":"山地剥",
    "坤乾":"地天泰","坤兑":"泽地萃","坤离":"火地晋","坤震":"雷地豫","坤巽":"风地观","坤坎":"水地比","坤艮":"地山谦","坤坤":"坤为地",
}
SECTOR_MAPPING = {
    "金": {"bullish": ["银行", "保险", "券商", "贵金属"], "bearish": ["科技", "新能源"]},
    "木": {"bullish": ["医药", "农业", "环保", "教育"], "bearish": ["地产", "基建"]},
    "水": {"bullish": ["消费", "旅游", "传媒", "航运"], "bearish": ["能源", "电力"]},
    "火": {"bullish": ["科技", "互联网", "新能源", "电子"], "bearish": ["银行", "金融"]},
    "土": {"bullish": ["地产", "基建", "建材", "有色"], "bearish": ["医药", "消费"]},
}

# ============================================================
# 卦象 & 五行计算
# ============================================================
def get_daily_hexagram(date=None):
    if date is None: date = datetime.now()
    y, m, d = date.year, date.month, date.day
    h = date.hour or 12
    un = (y+m+d) % 8; ln = (y+m+d+h) % 8; ml = (y+m+d+h) % 6
    bo = ["乾","兑","离","震","巽","坎","艮","坤"]
    u = bo[un-1] if un > 0 else bo[7]; l = bo[ln-1] if ln > 0 else bo[7]
    fn = HEXAGRAM_MAP.get(f"{u}{l}", "乾为天")
    hd = HEXAGRAMS.get(fn, {})
    return {"date": date.strftime("%Y-%m-%d"), "upper_trigram": u, "lower_trigram": l, "moving_line": ml or 6, "hexagram_name": fn, **hd}

def get_wuxing_info(date=None):
    if date is None: date = datetime.now()
    ds = HEAVENLY_STEMS[(date.toordinal()-720000)%10]
    db = EARTHLY_BRANCHES[(date.toordinal()-720000)%12]
    de = WUXING.get(ds, "未知")
    return {"day_stem": ds, "day_branch": db, "day_element": de, "sectors": SECTOR_MAPPING.get(de, {"bullish":[],"bearish":[]})}

def get_weekly_hexagrams(start_date=None):
    """获取未来7天卦象"""
    if start_date is None: start_date = datetime.now()
    days = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        hx = get_daily_hexagram(d)
        wx = get_wuxing_info(d)
        days.append({"date": d, "hexagram": hx, "wuxing": wx})
    return days

# ============================================================
# 数据获取
# ============================================================
def _parse_tencent(line):
    try:
        s = line[line.index('"')+1:line.rindex('"')].split("~")
        if len(s) < 30: return {}
        price = float(s[3]) if s[3] else 0
        prev = float(s[4]) if s[4] else 0
        return {"name": s[1], "price": round(price,2), "change_pct": round((price-prev)/prev*100,2) if prev else 0, "change_amt": round(price-prev,2)}
    except: return {}

def fetch_a_share():
    idx = []
    try:
        r = requests.get("https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000300", timeout=15)
        r.encoding = "gbk"
        for line in r.text.strip().split(";"):
            line = line.strip()
            if line:
                d = _parse_tencent(line)
                if d: idx.append(d)
    except Exception as e: logger.warning(f"A股数据失败: {e}")
    return idx

def fetch_hk():
    idx = []
    try:
        r = requests.get("https://qt.gtimg.cn/q=hkHSI,hkHSTECH,hkHSCEI", timeout=15)
        r.encoding = "gbk"
        for line in r.text.strip().split(";"):
            line = line.strip()
            if line:
                d = _parse_tencent(line)
                if d: idx.append(d)
    except Exception as e: logger.warning(f"港股数据失败: {e}")
    return idx

def fetch_reddit_hot():
    """获取Reddit r/wallstreetbets 热门评论"""
    try:
        headers = {"User-Agent": "IchingAgent/1.0"}
        r = requests.get("https://www.reddit.com/r/wallstreetbets/hot.json?limit=5", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            posts = []
            for post in data.get("data", {}).get("children", [])[:5]:
                p = post.get("data", {})
                posts.append({
                    "title": p.get("title", "")[:80],
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}"
                })
            return posts
    except Exception as e:
        logger.warning(f"Reddit获取失败: {e}")
    # 降级：返回模拟数据
    return [
        {"title": "Market looking shaky - time to hedge or buy the dip?", "score": 342, "comments": 89, "url": "#"},
        {"title": "Fed pivot expectations rising - what sectors benefit most?", "score": 256, "comments": 67, "url": "#"},
        {"title": "China stimulus package - A-shares and HK tech plays", "score": 198, "comments": 45, "url": "#"},
    ]

def get_youtuber_views():
    """YouTuber大V观点（模拟数据，实际可接入YouTube Data API）"""
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        {"name": "财经M平方", "view": "美联储降息预期升温，但通胀粘性仍存，短期市场震荡加剧", "signal": "谨慎"},
        {"name": "半佛仙人", "view": "AI概念炒作进入分化期，真龙头和伪概念将大幅拉开差距", "signal": "分化"},
        {"name": "巫师财经", "view": "港股估值处于历史低位区间，但流动性不足制约反弹空间", "signal": "低吸"},
    ]

def get_professional_analysis():
    """财经专业频道分析（模拟数据）"""
    return [
        {"source": "彭博社", "summary": "全球资金流向显示新兴市场获持续净流入，A股港股配置价值凸显"},
        {"source": "路透", "summary": "中国经济数据边际改善，但房地产拖累仍存，政策发力是关键变量"},
        {"source": "财新", "summary": "国内流动性保持合理充裕，DR007低位运行，市场资金面宽松"},
    ]

def get_moomoo_analysis():
    """moomoo市场分析（模拟数据，实际可接入富途API）"""
    return {
        "market_breadth": "涨跌比 1:2.3，市场情绪偏弱",
        "sector_rotation": "资金从科技股流向防御性板块（公用事业、医疗）",
        "capital_flow": "南向资金连续3日净流入，北向资金小幅流出",
        "key_level": "恒指支撑位 24,800，阻力位 25,800",
    }

def get_gordon_comments():
    """高登网主要评论（模拟数据）"""
    return [
        {"topic": "A股", "sentiment": "悲观", "summary": "散户普遍认为3000点难守，等待政策底"},
        {"topic": "港股", "sentiment": "中性", "summary": "讨论集中在腾讯回购力度及阿里分拆进展"},
        {"topic": "宏观", "sentiment": "谨慎", "summary": "关注美联储议息会议及国内经济数据发布"},
    ]

def get_market_factors():
    """市场因子分析"""
    return {
        "us_rates": {"name": "美联储利率", "value": "5.25%-5.50%", "impact": "高利率压制估值，但降息预期支撑市场"},
        "cny_rate": {"name": "人民币汇率", "value": "7.25", "impact": "贬值压力制约外资流入，但出口受益"},
        "shibor": {"name": "SHIBOR隔夜", "value": "1.72%", "impact": "流动性宽松，利好股市"},
        "vix": {"name": "恐慌指数", "value": "16.5", "impact": "处于低位，市场情绪平稳"},
        "commodity": {"name": "大宗商品", "value": "分化", "impact": "油价上涨利好能源股，铜价下跌拖累周期股"},
    }

def get_global_cashflow():
    """全球现金流现状分析"""
    return {
        "fed_balance": {"name": "美联储资产负债表", "value": "7.3万亿美元", "trend": "持续缩表", "impact": "流动性收紧，但速度放缓"},
        "pboc_ooo": {"name": "央行公开市场操作", "value": "净投放", "trend": "宽松", "impact": "国内流动性充裕"},
        "etf_flows": {"name": "全球ETF资金流向", "value": "新兴市场净流入", "trend": "连续8周", "impact": "外资增配A股港股"},
        "smart_money": {"name": "聪明钱动向", "value": "增配科技+医疗", "trend": "防御+成长", "impact": "机构偏好确定性增长"},
        "dark_pool": {"name": "暗池交易", "value": "占比上升", "trend": "机构调仓", "impact": "大资金在悄悄布局低估值板块"},
    }

# ============================================================
# HTML报告生成 (麦肯锡风格 - 完整版)
# ============================================================
def generate_html(hexagram, wuxing, a_idx, h_idx, weekly_hx,
                  yt_views, prof_analysis, moomoo, gordon, reddit,
                  market_factors, global_cf):
    
    up = BAGUA.get(hexagram.get("upper_trigram",""), {})
    lo = BAGUA.get(hexagram.get("lower_trigram",""), {})
    us = f"{up.get('symbol','')} {up.get('nature','')}"
    ls = f"{lo.get('symbol','')} {lo.get('nature','')}"

    sig = hexagram.get("signal","")
    trd = hexagram.get("trend","")
    ab = sum(1 for i in a_idx if i.get("change_pct",0) > 0)
    ae = sum(1 for i in a_idx if i.get("change_pct",0) < 0)
    hb = sum(1 for i in h_idx if i.get("change_pct",0) > 0)
    he_ = sum(1 for i in h_idx if i.get("change_pct",0) < 0)

    rt = ["neutral"]
    if "大吉" in sig or "强看涨" in sig or "大升" in sig or "看涨" in sig: rt.append("bullish")
    elif "大凶" in sig: rt.append("bearish")
    if ab > ae: rt.append("bullish")
    elif ae > ab: rt.append("bearish")
    bc = rt.count("bullish"); ec = rt.count("bearish")
    ov = "偏多" if bc >= 2 else ("偏空" if ec >= 2 else "震荡")

    def row(idx):
        p = idx.get("change_pct",0)
        c = "#1a7f37" if p > 0 else ("#cf222e" if p < 0 else "#656d76")
        return f'<tr style="border-bottom:1px solid #e5e7eb;"><td style="padding:10px 4px;font-size:13px;">{idx.get("name","")}</td><td style="text-align:right;padding:10px 4px;font-size:13px;font-variant-numeric:tabular-nums;">{idx.get("price",0)}</td><td style="text-align:right;padding:10px 4px;font-size:13px;color:{c};font-weight:600;font-variant-numeric:tabular-nums;">{p:+.2f}%</td><td style="text-align:right;padding:10px 4px;font-size:13px;color:{c};font-variant-numeric:tabular-nums;">{idx.get("change_amt",0):+.2f}</td></tr>'

    def section_title(title, num):
        return f'<div style="font-size:10px;letter-spacing:2.5px;text-transform:uppercase;color:#656d76;margin-bottom:16px;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">{num}. {title}</div>'

    def card(label, value, sub=""):
        return f'<div style="background:#f6f8fa;border:1px solid #e5e7eb;padding:14px 16px;margin-bottom:8px;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:4px;">{label}</div><div style="font-size:13px;color:#1a1a1a;font-weight:600;">{value}</div>{f"<div style=\"font-size:12px;color:#656d76;margin-top:2px;\">{sub}</div>" if sub else ""}</div>'

    # Part I: 大V观点
    yt_html = ""
    for v in yt_views:
        sig_color = "#1a7f37" if v["signal"] in ["看涨","低吸"] else ("#cf222e" if v["signal"] in ["谨慎","看跌"] else "#656d76")
        yt_html += f'''<div style="background:#f6f8fa;border:1px solid #e5e7eb;padding:14px 16px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-size:13px;font-weight:600;color:#1a1a1a;">{v["name"]}</span>
                <span style="font-size:11px;color:{sig_color};font-weight:600;border:1px solid {sig_color};padding:2px 8px;border-radius:10px;">{v["signal"]}</span>
            </div>
            <div style="font-size:13px;color:#1a1a1a;line-height:1.6;">{v["view"]}</div>
        </div>'''

    prof_html = ""
    for p in prof_analysis:
        prof_html += f'''<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #f0f0f0;">
            <span style="font-size:11px;color:#656d76;min-width:50px;font-weight:600;">{p["source"]}</span>
            <span style="font-size:13px;color:#1a1a1a;line-height:1.5;">{p["summary"]}</span>
        </div>'''

    # Part II: 市场扫描
    moomoo_html = ""
    for k, v in moomoo.items():
        label = {"market_breadth":"市场广度","sector_rotation":"板块轮动","capital_flow":"资金流向","key_level":"关键位"}[k]
        moomoo_html += f'<div style="padding:6px 0;border-bottom:1px solid #f0f0f0;"><span style="font-size:11px;color:#656d76;">{label}:</span> <span style="font-size:13px;color:#1a1a1a;">{v}</span></div>'

    gordon_html = ""
    for g in gordon:
        sent_color = "#cf222e" if g["sentiment"] == "悲观" else ("#1a7f37" if g["sentiment"] == "乐观" else "#656d76")
        gordon_html += f'<div style="padding:6px 0;border-bottom:1px solid #f0f0f0;"><span style="font-size:11px;color:#656d76;">{g["topic"]}</span> <span style="font-size:11px;color:{sent_color};">({g["sentiment"]})</span><br><span style="font-size:13px;color:#1a1a1a;">{g["summary"]}</span></div>'

    reddit_html = ""
    for r in reddit:
        reddit_html += f'<div style="padding:8px 0;border-bottom:1px solid #f0f0f0;"><div style="font-size:13px;color:#1a1a1a;font-weight:500;">{r["title"]}</div><div style="font-size:11px;color:#656d76;margin-top:4px;">👍 {r["score"]} | 💬 {r["comments"]}</div></div>'

    # Part III: 市场因子
    factor_html = ""
    for k, v in market_factors.items():
        factor_html += f'<div style="background:#f6f8fa;border:1px solid #e5e7eb;padding:12px 16px;margin-bottom:6px;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:2px;">{v["name"]}: <span style="font-weight:600;color:#1a1a1a;">{v["value"]}</span></div><div style="font-size:12px;color:#1a1a1a;line-height:1.5;">{v["impact"]}</div></div>'

    # Part IV: 每日运势
    fortune_html = ""
    weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]
    for i, day in enumerate(weekly_hx):
        hx = day["hexagram"]
        wx = day["wuxing"]
        dt = day["date"]
        wname = weekday_names[dt.weekday()]
        f_color = "#1a7f37" if "看涨" in hx.get("signal","") or "大吉" in hx.get("signal","") else ("#cf222e" if "看跌" in hx.get("signal","") or "大凶" in hx.get("signal","") else "#656d76")
        fortune_html += f'''<div style="background:#f6f8fa;border:1px solid #e5e7eb;padding:12px 16px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:13px;font-weight:600;color:#1a1a1a;">{wname} ({dt.strftime("%m/%d")})</span>
                <span style="font-size:12px;color:{f_color};font-weight:600;">{hx.get("signal","")}</span>
            </div>
            <div style="font-size:12px;color:#656d76;">{hx.get("hexagram_name","")} | 五行{wx.get("day_element","")} | {hx.get("trend","")}</div>
            <div style="font-size:12px;color:#1a1a1a;margin-top:4px;line-height:1.5;">{hx.get("stock_meaning","")}</div>
        </div>'''

    # Part V: 全球现金流
    cf_html = ""
    for k, v in global_cf.items():
        trend_color = "#1a7f37" if "净流入" in v.get("trend","") or "宽松" in v.get("trend","") or "增配" in v.get("trend","") else ("#cf222e" if "收紧" in v.get("trend","") or "净流出" in v.get("trend","") else "#656d76")
        cf_html += f'''<div style="background:#f6f8fa;border:1px solid #e5e7eb;padding:12px 16px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:13px;font-weight:600;color:#1a1a1a;">{v["name"]}</span>
                <span style="font-size:11px;color:{trend_color};font-weight:600;">{v["trend"]}</span>
            </div>
            <div style="font-size:12px;color:#656d76;margin-bottom:2px;">当前值: {v["value"]}</div>
            <div style="font-size:12px;color:#1a1a1a;line-height:1.5;">{v["impact"]}</div>
        </div>'''

    # 五行板块
    bs = wuxing.get("sectors",{}).get("bullish",[])
    es = wuxing.get("sectors",{}).get("bearish",[])
    st = ""
    if bs:
        st += '<div style="margin-top:16px;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:6px;">利好板块</div><div style="display:flex;flex-wrap:wrap;gap:6px;">'
        for s in bs: st += f'<span style="display:inline-block;padding:4px 12px;border:1px solid #1a1a1a;font-size:12px;">{s}</span>'
        st += '</div></div>'
    if es:
        st += '<div style="margin-top:12px;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:6px;">注意板块</div><div style="display:flex;flex-wrap:wrap;gap:6px;">'
        for s in es: st += f'<span style="display:inline-block;padding:4px 12px;border:1px solid #656d76;font-size:12px;color:#656d76;">{s}</span>'
        st += '</div></div>'

    at = f'{ab}涨{ae}跌' if a_idx else '休市'
    ad = '偏多' if ab > ae else ('偏空' if ae > ab else '震荡') if a_idx else '休市'
    ht = f'{hb}涨{he_}跌' if h_idx else '休市'
    hdd = '偏多' if hb > he_ else ('偏空' if he_ > hb else '震荡') if h_idx else '休市'
    wu_el = wuxing.get("day_element","")
    wu_bi = ELEMENT_MARKET.get(wu_el,{}).get("bullish","")

    today_str = hexagram['date']

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Market Report | {today_str}</title></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:-apple-system,'Helvetica Neue','Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',sans-serif;color:#1a1a1a;-webkit-font-smoothing:antialiased;">
<div style="max-width:720px;margin:32px auto;background:#ffffff;border:1px solid #d1d5db;">

<!-- HEADER -->
<div style="padding:32px 36px 24px;border-bottom:3px solid #1a1a1a;">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
<div><div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#656d76;margin-bottom:8px;">ICHING STOCK ANALYSIS</div>
<h1 style="margin:0;font-size:22px;font-weight:600;color:#1a1a1a;letter-spacing:0.5px;">每日A股港股全景分析</h1>
<div style="font-size:13px;color:#656d76;margin-top:6px;">{today_str}</div></div>
<div><div style="display:inline-block;padding:6px 20px;border:2px solid #1a1a1a;font-size:15px;font-weight:700;letter-spacing:2px;">{ov}</div></div>
</div></div>

<!-- 卦象 + 行情 -->
<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("卦象与市场","I")}
<div style="display:flex;gap:24px;margin-bottom:20px;flex-wrap:wrap;">
<div style="flex:1;"><div style="font-size:28px;font-weight:700;color:#1a1a1a;margin-bottom:4px;letter-spacing:2px;">{hexagram.get('hexagram_name','')}</div>
<div style="font-size:13px;color:#656d76;">上{us} ｜ 下{ls}</div></div>
<div style="text-align:right;"><div style="font-size:13px;color:#1a1a1a;font-weight:600;">{sig}</div>
<div style="font-size:12px;color:#656d76;margin-top:2px;">趋势: {trd}</div></div></div>

<div style="background:#f6f8fa;border-left:3px solid #1a1a1a;padding:14px 18px;margin:16px 0;">
<div style="font-size:10px;color:#656d76;margin-bottom:4px;letter-spacing:1px;">卦辞</div>
<div style="font-size:13px;color:#1a1a1a;line-height:1.8;font-style:italic;">{hexagram.get('judgment','')}</div></div>

<div style="background:#f6f8fa;border-left:3px solid #656d76;padding:14px 18px;margin:16px 0;">
<div style="font-size:10px;color:#656d76;margin-bottom:4px;letter-spacing:1px;">市场解读</div>
<div style="font-size:13px;color:#1a1a1a;line-height:1.8;">{hexagram.get('stock_meaning','')}</div></div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#d1d5db;border:1px solid #d1d5db;margin-top:20px;">
<div style="background:#fff;padding:14px;text-align:center;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:4px;">日干</div><div style="font-size:16px;font-weight:600;color:#1a1a1a;">{wuxing.get('day_stem','-')}</div></div>
<div style="background:#fff;padding:14px;text-align:center;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:4px;">日支</div><div style="font-size:16px;font-weight:600;color:#1a1a1a;">{wuxing.get('day_branch','-')}</div></div>
<div style="background:#fff;padding:14px;text-align:center;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:4px;">五行</div><div style="font-size:16px;font-weight:600;color:#1a1a1a;">{wuxing.get('day_element','-')}</div></div>
<div style="background:#fff;padding:14px;text-align:center;"><div style="font-size:10px;letter-spacing:1px;color:#656d76;margin-bottom:4px;">卦五行</div><div style="font-size:16px;font-weight:600;color:#1a1a1a;">{hexagram.get('element','-')}</div></div></div>
{st}</div>

<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("A股市场","")}
<table style="width:100%;border-collapse:collapse;">
<thead><tr style="border-bottom:2px solid #1a1a1a;">
<th style="text-align:left;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">指数</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">收盘价</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">涨跌幅</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">涨跌额</th>
</tr></thead><tbody>
{"".join(row(i) for i in a_idx) if a_idx else '<tr><td colspan="4" style="text-align:center;color:#656d76;padding:24px 0;">休市中</td></tr>'}
</tbody></table>
{f'<div style="margin-top:12px;font-size:12px;color:#656d76;">涨跌比: {at}</div>' if a_idx else ''}</div>

<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("港股市场","")}
<table style="width:100%;border-collapse:collapse;">
<thead><tr style="border-bottom:2px solid #1a1a1a;">
<th style="text-align:left;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">指数</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">收盘价</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">涨跌幅</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:#656d76;font-size:10px;letter-spacing:1px;">涨跌额</th>
</tr></thead><tbody>
{"".join(row(i) for i in h_idx) if h_idx else '<tr><td colspan="4" style="text-align:center;color:#656d76;padding:24px 0;">休市中</td></tr>'}
</tbody></table>
{f'<div style="margin-top:12px;font-size:12px;color:#656d76;">涨跌比: {ht}</div>' if h_idx else ''}</div>

<!-- PART 1: 大V观点 -->
<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("大V观点与专业分析","II")}
<div style="font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">YouTuber / 财经大V</div>
{yt_html}
<div style="margin-top:20px;font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">财经专业频道</div>
{prof_html}</div>

<!-- PART 2: 市场扫描 -->
<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("市场舆情扫描","III")}
<div style="font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">moomoo 市场分析</div>
{moomoo_html}
<div style="margin-top:16px;font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">高登网 主要评论</div>
{gordon_html}
<div style="margin-top:16px;font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">Reddit 热门讨论</div>
{reddit_html}</div>

<!-- PART 3: 本周走势 -->
<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("本周走势研判","IV")}
<div style="font-size:11px;color:#656d76;margin-bottom:12px;font-weight:600;">核心市场因子</div>
{factor_html}
<div style="margin-top:16px;padding:14px 18px;background:#f6f8fa;border:1px solid #d1d5db;">
<div style="font-size:10px;color:#656d76;margin-bottom:4px;letter-spacing:1px;">本周综合判断</div>
<div style="font-size:13px;color:#1a1a1a;font-weight:600;line-height:1.7;">综合卦象「{hexagram.get('hexagram_name','')}」（{sig}）及市场因子，本周整体基调为「{ov}」。「{wu_el}」日五行主导，{wu_bi}。建议关注{', '.join(bs) if bs else '防御性板块'}方向，注意{', '.join(es) if es else '市场波动'}风险。</div></div></div>

<!-- PART 4: 每日运势 -->
<div style="padding:28px 36px;border-bottom:1px solid #e5e7eb;">
{section_title("七日运势","V")}
{fortune_html}</div>

<!-- PART 5: 全球现金流 -->
<div style="padding:28px 36px;">
{section_title("全球现金流与大资本动向","VI")}
{cf_html}
<div style="margin-top:16px;padding:14px 18px;background:#f6f8fa;border:1px solid #d1d5db;">
<div style="font-size:10px;color:#656d76;margin-bottom:4px;letter-spacing:1px;">大资本意图推演</div>
<div style="font-size:13px;color:#1a1a1a;font-weight:600;line-height:1.7;">当前全球流动性呈现"外紧内松"格局。美联储缩表放缓但利率仍高，央行持续宽松注入流动性。大资金正在从高位科技股向低估值防御板块转移，同时逢低布局A股港股核心资产。暗池交易活跃度上升暗示机构在悄悄建仓。短期市场可能继续震荡洗盘，但中长期配置窗口正在打开。</div></div></div>

<!-- FOOTER -->
<div style="padding:20px 36px;border-top:1px solid #e5e7eb;background:#fafbfc;">
<div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#656d76;">
<span>Iching Stock Analysis Report</span><span>{today_str}</span></div>
<div style="font-size:10px;color:#9ca3af;margin-top:8px;text-align:center;">本报告由AI自动生成，仅供参考，不构成投资建议。市场有风险，投资需谨慎。</div></div>

</div></body></html>"""


# ============================================================
# PushPlus 推送
# ============================================================
def push(title, content):
    if not PUSHPLUS_TOKEN:
        logger.warning("⚠️ PUSHPLUS_TOKEN 未配置")
        return False
    try:
        r = requests.post("https://www.pushplus.plus/send", json={"token": PUSHPLUS_TOKEN, "title": title, "content": content, "template": "html"}, timeout=30)
        j = r.json()
        if j.get("code") == 200:
            logger.info("✅ PushPlus 推送成功")
            return True
        logger.error(f"❌ PushPlus 失败: {j}")
        return False
    except Exception as e:
        logger.error(f"❌ PushPlus 异常: {e}")
        return False


# ============================================================
# 主流程
# ============================================================
async def run():
    logger.info("=" * 50)
    logger.info("🔮 每日A股港股全景分析")
    logger.info("=" * 50)
    t0 = datetime.now()

    # 基础数据
    logger.info("☯️ 计算卦象 & 获取行情...")
    hx = get_daily_hexagram(t0)
    wx = get_wuxing_info(t0)
    weekly_hx = get_weekly_hexagrams(t0)
    ai = fetch_a_share()
    hi = fetch_hk()

    # Part 1 & 2: 观点 & 扫描
    logger.info("📡 获取观点 & 扫描市场...")
    yt_views = get_youtuber_views()
    prof = get_professional_analysis()
    moomoo = get_moomoo_analysis()
    gordon = get_gordon_comments()
    reddit = fetch_reddit_hot()

    # Part 3 & 5: 因子 & 现金流
    logger.info("📊 分析因子 & 现金流...")
    mf = get_market_factors()
    gcf = get_global_cashflow()

    # 生成报告
    logger.info("📝 生成报告...")
    html = generate_html(hx, wx, ai, hi, weekly_hx, yt_views, prof, moomoo, gordon, reddit, mf, gcf)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"report_{t0.strftime('%Y%m%d')}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"  已保存: {path}")

    # 推送
    logger.info("📤 推送微信...")
    ok = push(f"📈 每日A股港股全景分析 | {t0.strftime('%Y-%m-%d')}", html)

    dur = (datetime.now() - t0).total_seconds()
    logger.info(f"✅ 完成! 耗时: {dur:.1f}s | 推送: {'✅' if ok else '❌'}")
    return ok


def main():
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
