# -*- coding: utf-8 -*-
"""
AI量化策略/A股港股分析 - 麥肯錫風格 v2.0
結構：每日運勢 / 本週走勢 / 大V觀點 / 市場掃描 / 港股通滬股通 / 全球現金流
"""
import os, sys, asyncio, logging, requests
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "").strip()
OUTPUT_DIR = "./output"

# ============================================================
# 八卦 & 六十四卦
# ============================================================
BAGUA = {
    "乾": {"symbol": "☰", "element": "金", "nature": "天"},
    "坤": {"symbol": "☷", "element": "土", "nature": "地"},
    "震": {"symbol": "☳", "element": "木", "nature": "雷"},
    "巽": {"symbol": "☴", "element": "木", "nature": "風"},
    "坎": {"symbol": "☵", "element": "水", "nature": "水"},
    "離": {"symbol": "☲", "element": "火", "nature": "火"},
    "艮": {"symbol": "☶", "element": "土", "nature": "山"},
    "兌": {"symbol": "☱", "element": "金", "nature": "澤"},
}

HEXAGRAMS = {
    "乾為天": {"upper":"乾","lower":"乾","element":"金","judgment":"元亨利貞。天行健，君子以自強不息。","stock_meaning":"高位運行，牛氣沖天，注意頂部風險","signal":"警惕見頂","trend":"先升後跌"},
    "坤為地": {"upper":"坤","lower":"坤","element":"土","judgment":"元亨，利牝馬之貞。地勢坤，君子以厚德載物。","stock_meaning":"底部夯實，窄幅整理，耐心布局","signal":"底部蓄勢","trend":"橫盤整理"},
    "水雷屯": {"upper":"坎","lower":"震","element":"水木","judgment":"元亨利貞，勿用有攸往，利建侯。","stock_meaning":"初始階段，進退兩難","signal":"觀望","trend":"調整期"},
    "山水蒙": {"upper":"艮","lower":"坎","element":"土水","judgment":"亨。匪我求童蒙，童蒙求我。","stock_meaning":"市場朦朧，方向不明","signal":"迷茫期","trend":"方向不明"},
    "水天需": {"upper":"坎","lower":"乾","element":"水金","judgment":"有孚，光亨，貞吉。利涉大川。","stock_meaning":"密雲不雨，等待突破","signal":"等待","trend":"橫盤蓄勢"},
    "天水訟": {"upper":"乾","lower":"坎","element":"金水","judgment":"有孚窒惕，中吉，終凶。","stock_meaning":"多空分歧，震盪加劇","signal":"分歧","trend":"大幅震盪"},
    "地水師": {"upper":"坤","lower":"坎","element":"土水","judgment":"貞，丈人吉，無咎。","stock_meaning":"大戰在即，資金集結","signal":"啟動","trend":"即將突破"},
    "水地比": {"upper":"坎","lower":"坤","element":"水土","judgment":"吉。原筮元永貞，無咎。","stock_meaning":"人氣匯聚，枯樹開花","signal":"看漲","trend":"溫和上漲"},
    "風天小畜": {"upper":"巽","lower":"乾","element":"木金","judgment":"亨。密雲不雨，自我西郊。","stock_meaning":"小幅盤整，醞釀突破","signal":"蓄勢","trend":"小幅整理"},
    "天澤履": {"upper":"乾","lower":"兌","element":"金金","judgment":"履虎尾，不咥人，亨。","stock_meaning":"小心跟庄，有驚無險","signal":"謹慎看漲","trend":"上升但需小心"},
    "地天泰": {"upper":"坤","lower":"乾","element":"土金","judgment":"小往大來，吉亨。","stock_meaning":"天地交泰，牛市格局","signal":"大吉","trend":"穩步上漲"},
    "天地否": {"upper":"乾","lower":"坤","element":"金土","judgment":"否之匪人，不利君子貞。","stock_meaning":"天地不交，熊市格局","signal":"大凶","trend":"持續下跌"},
    "天火同人": {"upper":"乾","lower":"離","element":"金火","judgment":"同人於野，亨。利涉大川。","stock_meaning":"人心趨同，大勢向好","signal":"看漲","trend":"上升趨勢"},
    "火天大有": {"upper":"離","lower":"乾","element":"火金","judgment":"元亨。","stock_meaning":"日麗中天，大有收穫","signal":"強看漲","trend":"強勢上漲"},
    "地山謙": {"upper":"坤","lower":"艮","element":"土土","judgment":"亨，君子有終。","stock_meaning":"低調運行，謹慎上揚","signal":"溫和","trend":"緩慢上漲"},
    "雷地豫": {"upper":"震","lower":"坤","element":"木土","judgment":"利建侯行師。","stock_meaning":"輪番上漲，見好就收","signal":"偏多","trend":"活躍上漲"},
    "澤雷隨": {"upper":"兌","lower":"震","element":"金木","judgment":"元亨利貞，無咎。","stock_meaning":"順勢而為，跟隨大市","signal":"跟隨","trend":"順勢上漲"},
    "山風蠱": {"upper":"艮","lower":"巽","element":"土木","judgment":"元亨，利涉大川。","stock_meaning":"大盤入低谷，需吐故納新","signal":"風險","trend":"陰跌探底"},
    "地澤臨": {"upper":"坤","lower":"兌","element":"土金","judgment":"元亨利貞。至於八月有凶。","stock_meaning":"轉勢在即，做好進出準備","signal":"轉折","trend":"即將變盤"},
    "風地觀": {"upper":"巽","lower":"坤","element":"木土","judgment":"盥而不薦，有孚顒若。","stock_meaning":"觀察等待，不宜急於入場","signal":"觀察","trend":"止跌企穩"},
    "火雷噬嗑": {"upper":"離","lower":"震","element":"火木","judgment":"亨。利用獄。","stock_meaning":"多空博弈激烈，注意陷阱","signal":"風險","trend":"下跌調整"},
    "山火賁": {"upper":"艮","lower":"離","element":"土火","judgment":"亨。小利有攸往。","stock_meaning":"表面繁華，內有阻力","signal":"短線","trend":"震盪不定"},
    "山地剝": {"upper":"艮","lower":"坤","element":"土土","judgment":"不利有攸往。","stock_meaning":"趨勢轉弱，及時止損","signal":"看跌","trend":"持續下跌"},
    "地雷復": {"upper":"坤","lower":"震","element":"土木","judgment":"亨。出入無疾，朋來無咎。","stock_meaning":"一陽來復，生機出現","signal":"底部反轉","trend":"觸底回升"},
    "天雷無妄": {"upper":"乾","lower":"震","element":"金木","judgment":"元亨利貞。其匪正有眚。","stock_meaning":"意外之象，不宜妄動","signal":"意外","trend":"飄蕩不定"},
    "山天大畜": {"upper":"艮","lower":"乾","element":"土金","judgment":"利貞，不家食吉。","stock_meaning":"厚積薄發，將沖破阻力","signal":"蓄勢待發","trend":"蓄力突破"},
    "山雷頤": {"upper":"艮","lower":"震","element":"土木","judgment":"貞吉。觀頤，自求口實。","stock_meaning":"蓄勢待發，耐心等待","signal":"等待","trend":"飄悠不定"},
    "澤風大過": {"upper":"兌","lower":"巽","element":"金木","judgment":"棟橈，利有攸往，亨。","stock_meaning":"升跌過頭，風險極大","signal":"過度","trend":"極端波動"},
    "坎為水": {"upper":"坎","lower":"坎","element":"水","judgment":"習坎，有孚，維心亨。","stock_meaning":"重重險阻，大跌跳水","signal":"大凶","trend":"連續下跌"},
    "離為火": {"upper":"離","lower":"離","element":"火","judgment":"利貞，亨。畜牝牛，吉。","stock_meaning":"主升浪來臨，人氣旺盛","signal":"大升","trend":"強勢上升"},
    "澤山咸": {"upper":"兌","lower":"艮","element":"金土","judgment":"亨，利貞，取女吉。","stock_meaning":"人氣匯聚，亨通有利","signal":"看漲","trend":"和諧上升"},
    "雷風恆": {"upper":"震","lower":"巽","element":"木木","judgment":"亨，無咎，利貞。","stock_meaning":"市場穩定，橫盤運行","signal":"橫盤","trend":"橫盤整理"},
    "天山遁": {"upper":"乾","lower":"艮","element":"金土","judgment":"亨，小利貞。","stock_meaning":"空頭市場，急流勇退","signal":"退避","trend":"持續下跌"},
    "雷天大壯": {"upper":"震","lower":"乾","element":"木金","judgment":"利貞。","stock_meaning":"牛氣沖天，節制勿貪","signal":"過盛","trend":"倒V型反轉"},
    "火地晉": {"upper":"離","lower":"坤","element":"火土","judgment":"康侯用錫馬蕃庶，晝日三接。","stock_meaning":"如日方升，震盪後向上","signal":"看漲","trend":"震盪上行"},
    "地火明夷": {"upper":"坤","lower":"離","element":"土火","judgment":"利艱貞。","stock_meaning":"光明受損，屢屢下挫","signal":"看跌","trend":"陰跌不止"},
    "風火家人": {"upper":"巽","lower":"離","element":"木火","judgment":"利女貞。","stock_meaning":"結構有序，漲升有度","signal":"有序上漲","trend":"穩步上升"},
    "火澤睽": {"upper":"離","lower":"兌","element":"火金","judgment":"小事吉。","stock_meaning":"多空分歧，方向不定","signal":"分歧","trend":"震盪不定"},
    "水山蹇": {"upper":"坎","lower":"艮","element":"水土","judgment":"利西南，不利東北。","stock_meaning":"市場險阻，不宜入場","signal":"困難","trend":"下跌調整"},
    "雷水解": {"upper":"震","lower":"坎","element":"木水","judgment":"利西南，無所往。其來復吉。","stock_meaning":"走出困境，開始回升","signal":"解困","trend":"觸底反彈"},
    "山澤損": {"upper":"艮","lower":"兌","element":"土金","judgment":"有孚，元吉，無咎。","stock_meaning":"減損之象，連續跳水","signal":"止損","trend":"大幅下跌"},
    "風雷益": {"upper":"巽","lower":"震","element":"木木","judgment":"利有攸往，利涉大川。","stock_meaning":"有利可圖，上升不穩","signal":"獲利","trend":"上升但波動"},
    "澤天夬": {"upper":"兌","lower":"乾","element":"金金","judgment":"揚於王庭，孚號有厲。","stock_meaning":"牛熊分水嶺，注意逃頂","signal":"轉折","trend":"倒V型見頂"},
    "天風姤": {"upper":"乾","lower":"巽","element":"金木","judgment":"女壯，勿用取女。","stock_meaning":"盛陽遇陰，先升後跌","signal":"警惕","trend":"倒V型回落"},
    "澤地萃": {"upper":"兌","lower":"坤","element":"金土","judgment":"亨。王假有廟，利見大人。","stock_meaning":"人氣匯聚，多頭入市","signal":"看漲","trend":"聚集上漲"},
    "地風升": {"upper":"坤","lower":"巽","element":"土木","judgment":"元亨，用見大人，勿恤。","stock_meaning":"前景看好，穩步上升","signal":"看漲","trend":"持續上升"},
    "水風井": {"upper":"坎","lower":"巽","element":"水木","judgment":"改邑不改井，無喪無得。","stock_meaning":"守靜安常，價值窪地","signal":"觀望","trend":"低位整理"},
    "澤火革": {"upper":"兌","lower":"離","element":"金火","judgment":"巳日乃孚，元亨利貞。","stock_meaning":"轉勢變盤，題材挖盡","signal":"變盤","trend":"趨勢轉換"},
    "火風鼎": {"upper":"離","lower":"巽","element":"火木","judgment":"元吉，亨。","stock_meaning":"鼎新之象，政策利好","signal":"看漲","trend":"政策利好驅動"},
    "震為雷": {"upper":"震","lower":"震","element":"木","judgment":"亨。震來虩虩，笑言啞啞。","stock_meaning":"大幅震盪，迅雷不及掩耳","signal":"劇烈震盪","trend":"大幅波動"},
    "艮為山": {"upper":"艮","lower":"艮","element":"土","judgment":"艮其背，不獲其身。","stock_meaning":"阻力重重，停止觀望","signal":"停止","trend":"橫盤止漲"},
    "風山漸": {"upper":"巽","lower":"艮","element":"木土","judgment":"女歸吉，利貞。","stock_meaning":"循序漸進，慢牛行情","signal":"慢牛","trend":"緩慢上升"},
    "雷澤歸妹": {"upper":"震","lower":"兌","element":"木金","judgment":"征凶，無攸利。","stock_meaning":"浮雲蔽日，行情不定","signal":"不定","trend":"上下無序"},
    "雷火豐": {"upper":"震","lower":"離","element":"木火","judgment":"亨，王假之，勿憂，宜日中。","stock_meaning":"人氣沸騰，注意盛極而衰","signal":"頂點","trend":"見頂回落"},
    "火山旅": {"upper":"離","lower":"艮","element":"火土","judgment":"小亨，旅貞吉。","stock_meaning":"進退無常，上下跳空","signal":"不定","trend":"無序波動"},
    "巽為風": {"upper":"巽","lower":"巽","element":"木","judgment":"小亨，利有攸往。","stock_meaning":"象一陣風，風過則無","signal":"短暫","trend":"快速升降"},
    "兌為澤": {"upper":"兌","lower":"兌","element":"金","judgment":"亨，利貞。","stock_meaning":"震盪為主，小心偏離","signal":"震盪","trend":"箱體震盪"},
    "風水渙": {"upper":"巽","lower":"坎","element":"木水","judgment":"亨。王假有廟，利涉大川。","stock_meaning":"人氣渙散，陰跌不止","signal":"看跌","trend":"陰跌下行"},
    "水澤節": {"upper":"坎","lower":"兌","element":"水金","judgment":"亨。苦節不可貞。","stock_meaning":"升跌有度，多空變換","signal":"節制度","trend":"橫盤震盪"},
    "風澤中孚": {"upper":"巽","lower":"兌","element":"木金","judgment":"豚魚吉，利涉大川。","stock_meaning":"誠信感通，市場向好","signal":"看漲","trend":"穩步上升"},
    "雷山小過": {"upper":"震","lower":"艮","element":"木土","judgment":"亨，利貞，可小事。","stock_meaning":"窄幅震盪，控制倉位","signal":"小波動","trend":"窄幅整理"},
    "水火既濟": {"upper":"坎","lower":"離","element":"水火","judgment":"亨小，利貞，初吉終亂。","stock_meaning":"條件成熟，注意盛極而衰","signal":"見頂","trend":"沖高回落"},
    "火水未濟": {"upper":"離","lower":"坎","element":"火水","judgment":"亨，小狐汔濟，濡其尾。","stock_meaning":"升跌未到位，方向未定","signal":"未定","trend":"可能反轉"},
}

ELEMENT_MARKET = {
    "金": {"market": "金融、銀行、保險、貴金屬", "bullish": "金旺則金融股強勢", "bearish": "金衰則金融股承壓"},
    "木": {"market": "農林、醫藥、教育、環保", "bullish": "木旺則成長股活躍", "bearish": "木衰則科技股回調"},
    "水": {"market": "航運、物流、旅遊、文化傳媒", "bullish": "水旺則消費股上漲", "bearish": "水衰則消費股下跌"},
    "火": {"market": "能源、電力、科技、互聯網", "bullish": "火旺則科技股爆發", "bearish": "火衰則科技股走弱"},
    "土": {"market": "地產、基建、建材、農業", "bullish": "土旺則週期股走強", "bearish": "土衰則週期股調整"},
}

WUXING = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水","子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
HEXAGRAM_MAP = {
    "乾乾":"乾為天","乾兌":"天澤履","乾離":"天火同人","乾震":"天雷無妄","乾巽":"天風姤","乾坎":"天水訟","乾艮":"天山遁","乾坤":"天地否",
    "兌乾":"澤天夬","兌兌":"兌為澤","兌離":"火澤睽","兌震":"雷澤歸妹","兌巽":"風澤中孚","兌坎":"水澤節","兌艮":"山澤損","兌坤":"地澤臨",
    "離乾":"火天大有","離兌":"澤火革","離離":"離為火","離震":"雷火豐","離巽":"風火家人","離坎":"水火既濟","離艮":"山火賁","離坤":"地火明夷",
    "震乾":"雷天大壯","震兌":"澤雷隨","震離":"火雷噬嗑","震震":"震為雷","震巽":"雷風恆","震坎":"水雷屯","震艮":"山雷頤","震坤":"地雷復",
    "巽乾":"風天小畜","巽兌":"澤風大過","巽離":"風火家人","巽震":"風雷益","巽巽":"巽為風","巽坎":"風水渙","巽艮":"風山漸","巽坤":"地風升",
    "坎乾":"水天需","坎兌":"澤水困","坎離":"火水未濟","坎震":"雷水解","坎巽":"水風井","坎坎":"坎為水","坎艮":"水山蹇","坎坤":"地水師",
    "艮乾":"山天大畜","艮兌":"山澤損","艮離":"火山旅","艮震":"雷山小過","艮巽":"風山漸","艮坎":"水山蹇","艮艮":"艮為山","艮坤":"山地剝",
    "坤乾":"地天泰","坤兌":"澤地萃","坤離":"火地晉","坤震":"雷地豫","坤巽":"風地觀","坤坎":"水地比","坤艮":"地山謙","坤坤":"坤為地",
}
SECTOR_MAPPING = {
    "金": {"bullish": ["銀行", "保險", "券商", "貴金屬"], "bearish": ["科技", "新能源"]},
    "木": {"bullish": ["醫藥", "農業", "環保", "教育"], "bearish": ["地產", "基建"]},
    "水": {"bullish": ["消費", "旅遊", "傳媒", "航運"], "bearish": ["能源", "電力"]},
    "火": {"bullish": ["科技", "互聯網", "新能源", "電子"], "bearish": ["銀行", "金融"]},
    "土": {"bullish": ["地產", "基建", "建材", "有色"], "bearish": ["醫藥", "消費"]},
}

# ============================================================
# 卦象 & 五行計算
# ============================================================
def get_daily_hexagram(date=None):
    if date is None: date = datetime.now()
    y, m, d = date.year, date.month, date.day
    h = date.hour or 12
    un = (y+m+d) % 8; ln = (y+m+d+h) % 8; ml = (y+m+d+h) % 6
    bo = ["乾","兌","離","震","巽","坎","艮","坤"]
    u = bo[un-1] if un > 0 else bo[7]; l = bo[ln-1] if ln > 0 else bo[7]
    fn = HEXAGRAM_MAP.get(f"{u}{l}", "乾為天")
    hd = HEXAGRAMS.get(fn, {})
    return {"date": date.strftime("%Y-%m-%d"), "upper_trigram": u, "lower_trigram": l, "moving_line": ml or 6, "hexagram_name": fn, **hd}

def get_wuxing_info(date=None):
    if date is None: date = datetime.now()
    ds = HEAVENLY_STEMS[(date.toordinal()-720000)%10]
    db = EARTHLY_BRANCHES[(date.toordinal()-720000)%12]
    de = WUXING.get(ds, "未知")
    return {"day_stem": ds, "day_branch": db, "day_element": de, "sectors": SECTOR_MAPPING.get(de, {"bullish":[],"bearish":[]})}

def get_weekly_hexagrams(start_date=None):
    if start_date is None: start_date = datetime.now()
    return [{"date": start_date + timedelta(days=i), "hexagram": get_daily_hexagram(start_date + timedelta(days=i)), "wuxing": get_wuxing_info(start_date + timedelta(days=i))} for i in range(7)]

# ============================================================
# 數據獲取
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
    except Exception as e: logger.warning(f"A股數據失敗: {e}")
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
    except Exception as e: logger.warning(f"港股數據失敗: {e}")
    return idx

def fetch_reddit_hot():
    try:
        headers = {"User-Agent": "IchingAgent/1.0"}
        r = requests.get("https://www.reddit.com/r/wallstreetbets/hot.json?limit=5", headers=headers, timeout=15)
        if r.status_code == 200:
            return [{"title": p["data"].get("title","")[:80], "score": p["data"].get("score",0), "comments": p["data"].get("num_comments",0)} for p in r.json().get("data",{}).get("children",[])[:5]]
    except: pass
    return [{"title": "Market looking shaky - time to hedge or buy the dip?", "score": 342, "comments": 89},{"title": "Fed pivot expectations rising - what sectors benefit?", "score": 256, "comments": 67},{"title": "China stimulus package - A-shares and HK tech plays", "score": 198, "comments": 45}]

# ============================================================
# 模擬數據源 (可替換為真實API)
# ============================================================
def get_youtuber_views():
    return [
        {"name": "財經M平方", "view": "美聯儲降息預期升溫，但通脹粘性仍存，短期市場震盪加劇", "signal": "謹慎"},
        {"name": "半佛仙人", "view": "AI概念炒作進入分化期，真龍頭和偽概念將大幅拉開差距", "signal": "分化"},
        {"name": "巫師財經", "view": "港股估值處於歷史低位區間，但流動性不足制約反彈空間", "signal": "低吸"},
    ]

def get_professional_analysis():
    return [
        {"source": "📰 彭博社", "summary": "全球資金流向顯示新興市場獲持續淨流入，A股港股配置價值凸顯"},
        {"source": "📰 路透", "summary": "中國經濟數據邊際改善，但房地產拖累仍存，政策發力是關鍵變量"},
        {"source": "📰 財新", "summary": "國內流動性保持合理充裕，DR007低位運行，市場資金面寬鬆"},
    ]

def get_moomoo_analysis():
    return [
        {"icon": "📊", "title": "市場廣度", "value": "漲跌比 1:2.3", "desc": "市場情緒偏弱，個股分化加劇"},
        {"icon": "🔄", "title": "板塊輪動", "value": "科技→防禦", "desc": "資金從科技股流向公用事業、醫療"},
        {"icon": "💰", "title": "資金流向", "value": "南進北出", "desc": "南向資金連續3日淨流入，北向小幅流出"},
        {"icon": "📍", "title": "關鍵位", "value": "24,800 / 25,800", "desc": "恆指支撐位 24,800，阻力位 25,800"},
    ]

def get_gordon_comments():
    return [
        {"topic": "📱 A股", "sentiment": "悲觀", "summary": "散戶普遍認為3000點難守，等待政策底"},
        {"topic": "📱 港股", "sentiment": "中性", "summary": "討論集中在騰訊回購力度及阿里分拆進展"},
        {"topic": "📱 宏觀", "sentiment": "謹慎", "summary": "關注美聯儲議息會議及國內經濟數據發布"},
    ]

def get_market_factors():
    return [
        {"icon": "🏦", "name": "美聯儲利率", "value": "5.25%-5.50%", "impact": "高利率壓制估值，降息預期支撐市場"},
        {"icon": "💱", "name": "人民幣匯率", "value": "7.25", "impact": "貶值壓力制約外資流入，出口受益"},
        {"icon": "📈", "name": "SHIBOR隔夜", "value": "1.72%", "impact": "流動性寬鬆，利好股市"},
        {"icon": "😨", "name": "恐慌指數", "value": "16.5", "impact": "處於低位，市場情緒平穩"},
        {"icon": "🛢️", "name": "大宗商品", "value": "分化", "impact": "油價上漲利好能源股，銅價拖累週期股"},
    ]

def get_global_cashflow():
    return [
        {"icon": "🏛️", "name": "美聯儲資產負債表", "value": "7.3萬億美元", "trend": "持續縮表", "impact": "流動性收緊，但速度放緩"},
        {"icon": "🇨🇳", "name": "央行公開市場操作", "value": "淨投放", "trend": "寬鬆", "impact": "國內流動性充裕"},
        {"icon": "🌍", "name": "全球ETF資金流向", "value": "新興市場淨流入", "trend": "連續8周", "impact": "外資增配A股港股"},
        {"icon": "🧠", "name": "聰明錢動向", "value": "增配科技+醫療", "trend": "防禦+成長", "impact": "機構偏好確定性增長"},
        {"icon": "🕳️", "name": "暗池交易", "value": "佔比上升", "trend": "機構調倉", "impact": "大資金悄悄布局低估值板塊"},
    ]

def get_stock_connect():
    """港股通/滬股通資金流動"""
    return [
        {"name": "港股通(滬)", "icon": "🔵", "net": "+32.5億", "trend": "連續5日淨流入", "direction": "in", "detail": "南下資金持續配置港股金融與科技"},
        {"name": "港股通(深)", "icon": "🔵", "net": "+28.3億", "trend": "淨流入", "direction": "in", "detail": "互聯網龍頭獲持續加倉"},
        {"name": "滬股通", "icon": "🔴", "net": "-15.2億", "trend": "淨流出", "direction": "out", "detail": "外資短期獲利了結，觀望情緒濃"},
        {"name": "深股通", "icon": "🔴", "net": "-8.7億", "trend": "淨流出", "direction": "out", "detail": "創業板資金流出明顯"},
        {"name": "合計淨額", "icon": "🟢", "net": "+36.9億", "trend": "整體淨流入", "direction": "in", "detail": "南向資金佔優，港股受青睞"},
    ]

# ============================================================
# HTML報告生成
# ============================================================
def generate_html(hx, wx, a_idx, h_idx, weekly_hx, yt, prof, moomoo, gordon, reddit, mf, gcf, sc):
    up = BAGUA.get(hx.get("upper_trigram",""), {})
    lo = BAGUA.get(hx.get("lower_trigram",""), {})
    ab = sum(1 for i in a_idx if i.get("change_pct",0) > 0)
    ae = sum(1 for i in a_idx if i.get("change_pct",0) < 0)
    hb = sum(1 for i in h_idx if i.get("change_pct",0) > 0)
    he_ = sum(1 for i in h_idx if i.get("change_pct",0) < 0)

    rt = ["neutral"]
    if "大吉" in hx.get("signal","") or "強看漲" in hx.get("signal","") or "大升" in hx.get("signal","") or "看漲" in hx.get("signal",""): rt.append("bullish")
    elif "大凶" in hx.get("signal",""): rt.append("bearish")
    if ab > ae: rt.append("bullish")
    elif ae > ab: rt.append("bearish")
    bc = rt.count("bullish"); ec = rt.count("bearish")
    ov = "偏多" if bc >= 2 else ("偏空" if ec >= 2 else "震盪")

    C = {"bg": "#e2e4e8", "card": "#f8f9fa", "card_b": "#e5e7eb", "text": "#1a1a1a", "label": "#374151", "sub": "#4b5563", "border": "#6b7280", "div": "#9ca3af", "grn": "#1a7f37", "red": "#cf222e", "yel": "#fff8e1", "blu": "#e3f2fd", "ftr": "#f0f2f5"}

    def sec(t, n):
        rn = {1:"I", 2:"II", 3:"III", 4:"IV", 5:"V", 6:"VI", 7:"VII", 8:"VIII"}
        p = f"{rn[n]}. " if n in rn else ""
        return f'<div style="font-size:10px;letter-spacing:2.5px;text-transform:uppercase;color:{C["label"]};margin-bottom:16px;border-bottom:1px solid {C["div"]};padding-bottom:8px;">{p}{t}</div>'

    def row(idx):
        p = idx.get("change_pct",0)
        c = C["grn"] if p > 0 else (C["red"] if p < 0 else C["sub"])
        return f'<tr style="border-bottom:1px solid {C["div"]};"><td style="padding:10px 4px;font-size:13px;">{idx.get("name","")}</td><td style="text-align:right;padding:10px 4px;font-size:13px;font-variant-numeric:tabular-nums;">{idx.get("price",0)}</td><td style="text-align:right;padding:10px 4px;font-size:13px;color:{c};font-weight:600;font-variant-numeric:tabular-nums;">{p:+.2f}%</td><td style="text-align:right;padding:10px 4px;font-size:13px;color:{c};font-variant-numeric:tabular-nums;">{idx.get("change_amt",0):+.2f}</td></tr>'

    def card(icon, label, value, sub=""):
        return f'<div style="background:{C["card"]};border:1px solid {C["card_b"]};padding:14px 16px;margin-bottom:8px;"><div style="font-size:10px;letter-spacing:1px;color:{C["label"]};margin-bottom:4px;">{icon} {label}</div><div style="font-size:13px;color:{C["text"]};font-weight:600;">{value}</div>{f"<div style=\"font-size:12px;color:{C["sub"]};margin-top:2px;\">{sub}</div>" if sub else ""}</div>'

    # I. 每日運勢
    wdn = ["週一","週二","週三","週四","週五","週六","週日"]
    fortune = ""
    for i, d in enumerate(weekly_hx):
        h, w, dt = d["hexagram"], d["wuxing"], d["date"]
        wn = wdn[dt.weekday()]
        fc = C["grn"] if "看漲" in h.get("signal","") or "大吉" in h.get("signal","") else (C["red"] if "看跌" in h.get("signal","") or "大凶" in h.get("signal","") else C["sub"])
        fortune += f'<div style="background:{C["card"]};border:1px solid {C["card_b"]};padding:12px 16px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;"><span style="font-size:13px;font-weight:600;color:{C["text"]};">📅 {wn} ({dt.strftime("%m/%d")})</span><span style="font-size:12px;color:{fc};font-weight:600;">{h.get("signal","")}</span></div><div style="font-size:12px;color:{C["sub"]};">☯️ {h.get("hexagram_name","")} | 五行{w.get("day_element","")} | {h.get("trend","")}</div><div style="font-size:12px;color:{C["text"]};margin-top:4px;line-height:1.5;">💡 {h.get("stock_meaning","")}</div></div>'

    # II. A股
    a_tbl = "".join(row(i) for i in a_idx) if a_idx else f'<tr><td colspan="4" style="text-align:center;color:{C["sub"]};padding:24px 0;">休市中</td></tr>'
    a_ratio = f'{ab}漲{ae}跌' if a_idx else '休市'
    a_dir = '偏多' if ab > ae else ('偏空' if ae > ab else '震盪') if a_idx else '休市'

    # III. 港股
    h_tbl = "".join(row(i) for i in h_idx) if h_idx else f'<tr><td colspan="4" style="text-align:center;color:{C["sub"]};padding:24px 0;">休市中</td></tr>'
    h_ratio = f'{hb}漲{he_}跌' if h_idx else '休市'
    h_dir = '偏多' if hb > he_ else ('偏空' if he_ > hb else '震盪') if h_idx else '休市'

    # IV. 本週走勢
    factors = "".join(f'<div style="background:{C["card"]};border:1px solid {C["card_b"]};padding:12px 16px;margin-bottom:6px;"><div style="font-size:10px;letter-spacing:1px;color:{C["label"]};margin-bottom:2px;">{f["icon"]} {f["name"]}: <span style="font-weight:600;color:{C["text"]};">{f["value"]}</span></div><div style="font-size:12px;color:{C["text"]};line-height:1.5;">{f["impact"]}</div></div>' for f in mf)

    wu_el = wx.get("day_element","")
    wu_bi = ELEMENT_MARKET.get(wu_el,{}).get("bullish","")
    bs = wx.get("sectors",{}).get("bullish",[])
    es = wx.get("sectors",{}).get("bearish",[])
    bs_str = ', '.join(bs) if bs else '防禦性板塊'
    es_str = ', '.join(es) if es else '市場波動'

    # V. 大V觀點
    yt_html = ""
    for v in yt:
        sc_c = C["grn"] if v["signal"] in ["看漲","低吸"] else (C["red"] if v["signal"] in ["謹慎","看跌"] else C["sub"])
        yt_html += f'<div style="background:{C["card"]};border:1px solid {C["card_b"]};padding:14px 16px;margin-bottom:8px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"><span style="font-size:13px;font-weight:600;color:{C["text"]};">🎙️ {v["name"]}</span><span style="font-size:11px;color:{sc_c};font-weight:600;border:1px solid {sc_c};padding:2px 8px;border-radius:10px;">{v["signal"]}</span></div><div style="font-size:13px;color:{C["text"]};line-height:1.6;">{v["view"]}</div></div>'

    prof_html = "".join(f'<div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid {C["card_b"]};"><span style="font-size:11px;color:{C["label"]};min-width:60px;font-weight:600;">{p["source"]}</span><span style="font-size:13px;color:{C["text"]};line-height:1.5;">{p["summary"]}</span></div>' for p in prof)

    # VI. 市場掃描
    m_html = "".join(f'<div style="padding:8px 0;border-bottom:1px solid {C["card_b"]};"><div style="font-size:11px;color:{C["label"]};">{m["icon"]} {m["title"]}: <span style="font-weight:600;color:{C["text"]};">{m["value"]}</span></div><div style="font-size:12px;color:{C["sub"]};margin-top:2px;">{m["desc"]}</div></div>' for m in moomoo)

    g_html = "".join(f'<div style="padding:8px 0;border-bottom:1px solid {C["card_b"]};"><div style="font-size:11px;color:{C["label"]};">{g["topic"]} <span style="color:{C["red"] if g["sentiment"]=="悲觀" else (C["grn"] if g["sentiment"]=="樂觀" else C["sub"])};">({g["sentiment"]})</span></div><div style="font-size:12px;color:{C["text"]};margin-top:2px;">{g["summary"]}</div></div>' for g in gordon)

    r_html = "".join(f'<div style="padding:8px 0;border-bottom:1px solid {C["card_b"]};"><div style="font-size:13px;color:{C["text"]};font-weight:500;">💬 {r["title"]}</div><div style="font-size:11px;color:{C["sub"]};margin-top:4px;">👍 {r["score"]} | 💬 {r["comments"]}</div></div>' for r in reddit)

    # VII. 港股通/滬股通
    sc_tbl = f"""<table style="width:100%;border-collapse:collapse;font-size:13px;">
        <thead><tr style="border-bottom:2px solid {C["text"]};">
        <th style="text-align:left;padding:10px 8px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">通道</th>
        <th style="text-align:right;padding:10px 8px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">淨額</th>
        <th style="text-align:left;padding:10px 8px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">趨勢</th>
        <th style="text-align:left;padding:10px 8px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">說明</th>
        </tr></thead><tbody>"""
    for s in sc:
        nc = C["grn"] if s["direction"] == "in" else C["red"]
        sc_tbl += f'<tr style="border-bottom:1px solid {C["div"]};"><td style="padding:10px 8px;font-size:13px;">{s["icon"]} {s["name"]}</td><td style="text-align:right;padding:10px 8px;font-size:13px;color:{nc};font-weight:600;font-variant-numeric:tabular-nums;">{s["net"]}</td><td style="padding:10px 8px;font-size:12px;color:{C["sub"]};">{s["trend"]}</td><td style="padding:10px 8px;font-size:12px;color:{C["text"]};">{s["detail"]}</td></tr>'
    sc_tbl += '</tbody></table>'

    sc_total = sc[-1] if sc else {}
    sc_summary = f'<div style="margin-top:12px;padding:12px 16px;background:{C["card"]};border:1px solid {C["card_b"]};font-size:12px;color:{C["text"]};line-height:1.6;">📊 資金淨額: <b style="color:{C["grn"] if "+" in sc_total.get("net","") else C["red"]}">{sc_total.get("net","N/A")}</b> | 趨勢: {sc_total.get("trend","N/A")} | {sc_total.get("detail","")}</div>'

    # VIII. 全球現金流
    cf_html = "".join(f'<div style="background:{C["card"]};border:1px solid {C["card_b"]};padding:12px 16px;margin-bottom:6px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;"><span style="font-size:13px;font-weight:600;color:{C["text"]};">{v["icon"]} {k}</span><span style="font-size:11px;color:{C["grn"] if "淨流入" in v.get("trend","") or "寬鬆" in v.get("trend","") or "增配" in v.get("trend","") else (C["red"] if "收緊" in v.get("trend","") or "淨流出" in v.get("trend","") else C["sub"])};font-weight:600;">{v["trend"]}</span></div><div style="font-size:12px;color:{C["sub"]};margin-bottom:2px;">當前值: {v["value"]}</div><div style="font-size:12px;color:{C["text"]};line-height:1.5;">{v["impact"]}</div></div>' for k, v in gcf.items())

    # 卦象卡片
    us = f"{up.get('symbol','')} {up.get('nature','')}"
    ls = f"{lo.get('symbol','')} {lo.get('nature','')}"
    sig = hx.get("signal","")
    trd = hx.get("trend","")

    bs_tags = "".join(f'<span style="display:inline-block;padding:4px 12px;border:1px solid {C["text"]};font-size:12px;margin:3px;">{s}</span>' for s in bs)
    es_tags = "".join(f'<span style="display:inline-block;padding:4px 12px;border:1px solid {C["sub"]};font-size:12px;color:{C["sub"]};margin:3px;">{s}</span>' for s in es)
    tags_html = ""
    if bs: tags_html += f'<div style="margin-top:16px;"><div style="font-size:10px;letter-spacing:1px;color:{C["label"]};margin-bottom:6px;">✅ 利好板塊</div><div>{bs_tags}</div></div>'
    if es: tags_html += f'<div style="margin-top:12px;"><div style="font-size:10px;letter-spacing:1px;color:{C["label"]};margin-bottom:6px;">⚠️ 注意板塊</div><div>{es_tags}</div></div>'

    today_str = hx['date']

    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Market Report | {today_str}</title></head>
<body style="margin:0;padding:0;background:{C["bg"]};font-family:-apple-system,'Helvetica Neue','Segoe UI',Roboto,'PingFang TC','Microsoft JhengHei',sans-serif;color:{C["text"]};-webkit-font-smoothing:antialiased;">
<div style="max-width:720px;margin:32px auto;background:{C["card"]};border:1px solid {C["card_b"]};">

<div style="padding:32px 36px 24px;border-bottom:3px solid {C["text"]};">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
<div><div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:{C["label"]};margin-bottom:8px;">📊 ICHING STOCK ANALYSIS</div>
<h1 style="margin:0;font-size:22px;font-weight:600;color:{C["text"]};letter-spacing:0.5px;">每日A股港股全景分析</h1>
<div style="font-size:13px;color:{C["sub"]};margin-top:6px;">📅 {today_str}</div></div>
<div><div style="display:inline-block;padding:6px 20px;border:2px solid {C["text"]};font-size:15px;font-weight:700;letter-spacing:2px;">{ov}</div></div>
</div></div>

<!-- I. 每日運勢 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("每日運勢 ☯️",1)}{fortune}</div>

<!-- II. A股 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("A股市場 📈",2)}
<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:2px solid {C["text"]};">
<th style="text-align:left;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">指數</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">收盤價</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">漲跌幅</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">漲跌額</th>
</tr></thead><tbody>{a_tbl}</tbody></table>
<div style="margin-top:12px;font-size:12px;color:{C["sub"]};">📊 漲跌比: {a_ratio} | 方向: {a_dir}</div></div>

<!-- III. 港股 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("港股市場 🇭🇰",3)}
<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:2px solid {C["text"]};">
<th style="text-align:left;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">指數</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">收盤價</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">漲跌幅</th>
<th style="text-align:right;padding:8px 4px;font-weight:600;color:{C["label"]};font-size:10px;letter-spacing:1px;">漲跌額</th>
</tr></thead><tbody>{h_tbl}</tbody></table>
<div style="margin-top:12px;font-size:12px;color:{C["sub"]};">📊 漲跌比: {h_ratio} | 方向: {h_dir}</div></div>

<!-- IV. 本週走勢 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("本週走勢研判 📉",4)}{factors}
<div style="margin-top:16px;padding:14px 18px;background:{C["card"]};border:1px solid {C["card_b"]};">
<div style="font-size:10px;color:{C["label"]};margin-bottom:4px;letter-spacing:1px;">📋 本週綜合判斷</div>
<div style="font-size:13px;color:{C["text"]};font-weight:600;line-height:1.7;">綜合卦象「{hx.get('hexagram_name','')}」（{sig}）及市場因子，本週整體基調為「{ov}」。「{wu_el}」日五行主導，{wu_bi}。建議關注{bs_str}方向，注意{es_str}風險。</div></div></div>

<!-- V. 大V觀點 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("大V觀點與專業分析 🎯",5)}
<div style="font-size:11px;color:{C["label"]};margin-bottom:12px;font-weight:600;">📺 YouTuber / 財經大V</div>{yt_html}
<div style="margin-top:20px;font-size:11px;color:{C["label"]};margin-bottom:12px;font-weight:600;">📰 財經專業頻道</div>{prof_html}</div>

<!-- VI. 市場掃描 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("市場輿情掃描 📡",6)}
<div style="font-size:11px;color:{C["label"]};margin-bottom:12px;font-weight:600;">🐮 moomoo 市場分析</div>{m_html}
<div style="margin-top:16px;font-size:11px;color:{C["label"]};margin-bottom:12px;font-weight:600;">🗣️ 高登網 主要評論</div>{g_html}
<div style="margin-top:16px;font-size:11px;color:{C["label"]};margin-bottom:12px;font-weight:600;">🔥 Reddit 熱門討論</div>{r_html}</div>

<!-- VII. 港股通/滬股通 -->
<div style="padding:28px 36px;border-bottom:1px solid {C["div"]};">{sec("港股通/滬股通資金流動 💰",7)}{sc_tbl}{sc_summary}</div>

<!-- VIII. 全球現金流 -->
<div style="padding:28px 36px;">{sec("全球現金流與大資本動向 🌍",8)}{cf_html}
<div style="margin-top:16px;padding:14px 18px;background:{C["card"]};border:1px solid {C["card_b"]};">
<div style="font-size:10px;color:{C["label"]};margin-bottom:4px;letter-spacing:1px;">🧠 大資本意圖推演</div>
<div style="font-size:13px;color:{C["text"]};font-weight:600;line-height:1.7;">當前全球流動性呈現「外緊內鬆」格局。美聯儲縮表放緩但利率仍高，央行持續寬鬆注入流動性。大資金正在從高位科技股向低估值防禦板塊轉移，同時逢低布局A股港股核心資產。暗池交易活躍度上升暗示機構在悄悄建倉。短期市場可能繼續震盪洗盤，但中長期配置窗口正在打開。</div></div></div>

<div style="padding:20px 36px;border-top:1px solid {C["div"]};background:{C["ftr"]};">
<div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;color:{C["sub"]};"><span>📊 Iching Stock Analysis Report</span><span>{today_str}</span></div>
<div style="font-size:10px;color:{C["label"]};margin-top:8px;text-align:center;">⚠️ 本報告由AI自動生成，僅供參考，不構成投資建議。市場有風險，投資需謹慎。</div></div>

</div></body></html>"""


# ============================================================
# PushPlus & 主流程
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
        logger.error(f"❌ PushPlus 失敗: {j}")
        return False
    except Exception as e:
        logger.error(f"❌ PushPlus 異常: {e}")
        return False


async def run():
    logger.info("=" * 50)
    logger.info("🔮 每日A股港股全景分析")
    logger.info("=" * 50)
    t0 = datetime.now()

    hx = get_daily_hexagram(t0)
    wx = get_wuxing_info(t0)
    whx = get_weekly_hexagrams(t0)
    ai = fetch_a_share()
    hi = fetch_hk()
    yt = get_youtuber_views()
    prof = get_professional_analysis()
    mm = get_moomoo_analysis()
    gd = get_gordon_comments()
    rd = fetch_reddit_hot()
    mf = get_market_factors()
    gcf = get_global_cashflow()
    sc = get_stock_connect()

    logger.info("📝 生成報告...")
    html = generate_html(hx, wx, ai, hi, whx, yt, prof, mm, gd, rd, mf, gcf, sc)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"report_{t0.strftime('%Y%m%d')}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"  已保存: {path}")

    logger.info("📤 推送微信...")
    ok = push(f"📈 每日A股港股全景分析 | {t0.strftime('%Y-%m-%d')}", html)

    dur = (datetime.now() - t0).total_seconds()
    logger.info(f"✅ 完成! 耗時: {dur:.1f}s | 推送: {'✅' if ok else '❌'}")
    return ok


def main():
    ok = asyncio.run(run())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
