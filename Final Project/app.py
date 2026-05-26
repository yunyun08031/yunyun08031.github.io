# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import json
import os
import re
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. 頁面基本設定 (Page Config)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="☕ 引路微光 — 盲盒式活動推薦助理",
    page_icon="🛍️",
    layout="wide", # 🎯 全螢幕寬度，強迫 3 張放大盲盒絕對橫向一排呈現在公佈欄上！
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. 全域溫馨「引路微光」CSS 注入
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=Zhi+Mang+Xing&display=swap');

    /* 隱藏 Streamlit 預設選單與浮水印，消除工程生硬感 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge {display: none !important;}

    /* 溫暖燕麥白底色 */
    .stApp {
        background-color: #FCFAF7;
        color: #3D3430;
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    /* 療癒手寫風大標題 */
    .warm-title {
        color: #E07A5F;
        font-family: 'Noto Sans TC', sans-serif;
        font-weight: 900;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 0.1rem;
        margin-top: 1.5rem;
        text-shadow: 2px 2px 0px rgba(232, 220, 196, 0.4);
    }
    
    .warm-subtitle {
        color: #8D5B4C;
        text-align: center;
        font-size: 1.15rem;
        margin-bottom: 2.5rem;
        font-weight: 500;
        font-style: italic;
    }
    
    /* 溫馨手寫卡片容器 (Wide 模式下寬度限縮至 900px 保持視覺緊湊美感) */
    .section-card {
        background: linear-gradient(135deg, #FCF9F5 0%, #F6F0E8 100%);
        border: 2px solid #E8DCC4;
        border-radius: 28px;
        padding: 35px;
        box-shadow: 0 15px 30px rgba(141, 91, 76, 0.05), 
                    inset 0 1px 0 rgba(255,255,255,0.6);
        margin-bottom: 35px;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        position: relative;
        transition: transform 0.2s ease;
    }
    
    /* 溫馨紙膠帶裝飾 */
    .tape-deco-premium {
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%) rotate(-1.5deg);
        width: 140px;
        height: 28px;
        background-color: rgba(224, 122, 95, 0.25);
        border-left: 1px dashed rgba(224, 122, 95, 0.4);
        border-right: 1px dashed rgba(224, 122, 95, 0.4);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        color: #E07A5F;
        font-size: 10px;
        font-weight: bold;
        text-align: center;
        line-height: 28px;
        letter-spacing: 2px;
        user-select: none;
    }
    
    /* 實體軟木塞佈告欄 - 在 Wide 模式下展寬至 1100px */
    .corkboard {
        background-color: #FAF0E6;
        border: 10px solid #8D5B4C;
        border-radius: 32px;
        padding: 30px 10px;
        box-shadow: 0 20px 40px rgba(61, 52, 48, 0.12),
                    inset 0 0 30px rgba(141, 91, 76, 0.15);
        margin-top: 20px;
        max-width: 1100px;
        margin-left: auto;
        margin-right: auto;
        position: relative;
    }
    
    .corkboard-title {
        color: #8D5B4C;
        font-weight: 800;
        text-align: center;
        font-size: 1.3rem;
        margin-bottom: 20px;
        margin-top: -10px;
        text-shadow: 1px 1px 0px white;
    }

    /* 溫馨悄悄話卡片 (Wide 模式限寬 900px) */
    .whisper-card {
        background-color: #FFFDF9;
        border-left: 5px solid #E07A5F;
        border-radius: 16px;
        padding: 18px 22px;
        margin: 25px auto;
        max-width: 900px;
        box-shadow: 0 8px 20px rgba(141, 91, 76, 0.03);
    }
    
    .whisper-title {
        color: #E07A5F;
        font-weight: 800;
        font-size: 0.95rem;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .whisper-body {
        color: #6D5952;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
    }

    /* Focus 橘色光暈 */
    textarea:focus, input:focus {
        border-color: #E07A5F !important;
        box-shadow: 0 0 0 3px rgba(224, 122, 95, 0.2) !important;
    }

    /* 自訂 Streamlit 底部按鈕視覺 */
    div.stButton > button {
        background: linear-gradient(135deg, #E07A5F 0%, #D0694D 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 14px 28px !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 8px 25px rgba(224, 122, 95, 0.25) !important;
        transition: all 0.2s ease !important;
        border-bottom: 4px solid #A84E37 !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 28px rgba(224, 122, 95, 0.35) !important;
        border-bottom-width: 4px !important;
    }
    div.stButton > button:active {
        transform: translateY(2px) !important;
        border-bottom-width: 0px !important;
    }
    
    /* 刪除標籤按鈕專用 */
    div.del-btn > div > button {
        background-color: #FFF !important;
        color: #CBB190 !important;
        border: 1px solid #E8DCC4 !important;
        border-radius: 50% !important;
        width: 26px !important;
        height: 26px !important;
        padding: 0 !important;
        font-size: 0.75rem !important;
        box-shadow: none !important;
        line-height: 24px !important;
        border-bottom-width: 1px !important;
    }
    div.del-btn > div > button:hover {
        background-color: #E07A5F !important;
        color: white !important;
        border-color: #E07A5F !important;
        transform: scale(1.1) !important;
    }
    
    /* 溫馨的標籤晶片 */
    .warm-chip-premium {
        background-color: #FDFBF7;
        color: #8D5B4C;
        border: 2px solid #E8DCC4;
        border-radius: 20px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 0.95rem;
        display: inline-block;
        box-shadow: 0 4px 10px rgba(141, 91, 76, 0.03);
    }
    
    /* 用於按鈕排版居中 */
    .button-center {
        display: flex;
        justify-content: center;
        width: 100%;
        max-width: 900px;
        margin: 0 auto;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. 初始化 Session State
# -----------------------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 1

if "tags" not in st.session_state:
    st.session_state.tags = []

if "user_desc" not in st.session_state:
    st.session_state.user_desc = ""

if "recommended_events" not in st.session_state:
    st.session_state.recommended_events = []

if "show_balloons" not in st.session_state:
    st.session_state.show_balloons = False

# -----------------------------------------------------------------------------
# 4. 極致「個別化」24大類別標籤提取函數
# -----------------------------------------------------------------------------
def extract_tags_from_text(user_input: str):
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        matched_tags = []
        
        # A. 豐富多元且高質感的 24 大特質正則映射字典，涵蓋大學生所有主流領域與興趣
        mapping = [
            # 1. 商業與企劃類
            (r"行銷|廣告|品牌|社群行銷|文案|推廣|SEO", "商管行銷"),
            (r"商管|管理|企管|商業|策略|諮詢|顧問|經營|MBA", "商業策略"),
            (r"財金|經濟|財務|金融|投資|證券|會計|科技金融|FinTech", "金融科技"),
            (r"創業|創客|孵化|加速器|新創|Startup|募資", "創業孵化"),
            
            # 2. 資訊與 AI 科技類
            (r"python|程式|代碼|開發|資工|資管|軟體|工程師|網頁", "軟體工程"),
            (r"數據|分析|Tableau|爬蟲|SQL|統計|BI|資料庫", "數據開發"),
            (r"AI|人工智慧|機器學習|ChatGPT|LLM|Midjourney|Prompt", "AI 實踐"),
            (r"資安|資訊安全|駭客|網路安全|密碼", "資訊安全"),
            
            # 3. 藝術、影音與設計類
            (r"設計|美工|視覺|插畫|排版|Canva|平面|美術|繪畫", "視覺創意"),
            (r"UI|UX|Figma|介面|用戶體驗|網頁設計|原型", "UI/UX設計"),
            (r"影音|剪輯|影片|YouTube|Podcast|導演|編劇|影視|動畫|3D", "影音創作"),
            (r"遊戲|Game|Unity|Unreal|動漫|ACG|角色設計", "遊戲設計"),
            
            # 4. 人文、傳播與教育類
            (r"文學|寫作|閱讀|故事|出版|編譯|文藝|創作|報導", "故事創作"),
            (r"傳播|媒體|新聞|公關|外語|英文|翻譯|日文|韓文|雙語", "跨領域傳播"),
            (r"教育|學習|兒少|教學|補習|特殊教育|線上課程|教案", "教育科技"),
            (r"法律|法學|法規|思辨|辯論|政治|公共事務", "法律思辨"),
            
            # 5. 永續、地方與社會實踐類
            (r"永續|ESG|綠色|減碳|環境|生態|再生能源|氣候", "永續轉型"),
            (r"社會|公益|創新|NGO|NPO|社企|地方創生|社區|在地|農村|創生", "地方創生"),
            (r"高齡|老人|樂齡|銀髮|長者|長照|照護", "樂齡設計"),
            
            # 6. 個人成長與職場軟實力類
            (r"自省|心理|探索|心靈|諮商|成長|情緒|正念", "自我探索"),
            (r"專案|PM|進度|時程|跨部門|協作|敏捷", "專案管理"),
            (r"領導|幹部|會長|統籌|決策|公關|團隊", "領導統籌"),
            (r"出國|留學|交換|多元|國際|跨文化|全球|語文", "國際視野"),
            (r"簡報|演講|口語|表達|說服|說故事|辯論", "口語表達")
        ]
        
        for pattern, tag in mapping:
            if re.search(pattern, user_input, re.IGNORECASE):
                matched_tags.append(tag)
        
        # 移除重複項並維持順序
        seen = set()
        matched_tags = [x for x in matched_tags if not (x in seen or seen.add(x))]
        
        # B. 更加豐富的保底特質填充庫，防止類別單一
        fillers = ["跨域探索", "自我突破", "實踐精神", "數位進修", "社群經營", "商業策略", "社會實踐", "口語表達", "專案管理"]
        for f in fillers:
            if len(matched_tags) >= 3:
                break
            if f not in matched_tags:
                matched_tags.append(f)
                
        return matched_tags[:3]
    
    try:
        client = genai.Client()
        prompt = f"""
        請分析這段大學生自我描述的背景文字，萃取出剛好 3 個最能代表他個人背景、專業興趣、或是渴望突破方向的「特質/領域標籤」。
        
        【強制約束規範】
        1. 標籤必須是繁體中文有實際明確意義的專業領域、能力特質或興趣名詞，長度在 2 到 4 字之間（例如："數據開發"、"視覺傳達"、"自我探索"、"社會創新"、"商業分析" 等）。
        2. 絕對禁止輸出任何無意義的碎詞、連接詞、形容詞或半截短句（例如："系貼近"、"想做些"、"也略懂"、"很有興" 等不合理用詞）。
        3. 請優先從以下推薦的「大學生熱門標籤類別庫」中挑選符合用戶背景的標籤，或進行同等質感的衍生：
           - 商業企劃類：["商管行銷", "商業策略", "金融科技", "創業孵化"]
           - 資訊科技類：["軟體工程", "數據開發", "AI 實踐", "資訊安全"]
           - 藝術創意類：["視覺創意", "UI/UX設計", "影音創作", "遊戲設計"]
           - 人文傳播類：["故事創作", "跨領域傳播", "教育科技", "法律思辨"]
           - 永續社會類：["永續轉型", "地方創生", "樂齡設計"]
           - 核心軟實力：["自我探索", "專案管理", "領導統籌", "國際視野", "口語表達"]
        
        用戶輸入背景描述：「{user_input}」
        
        請直接以 JSON Array 的格式輸出，例如：["商管行銷", "UI/UX設計", "自我探索"]。不要有額外的 Markdown 標記或任何說明文字。
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return ["商管領域", "行銷企劃", "自我探索"]

# -----------------------------------------------------------------------------
# 5. Gemini API 智慧個人化盲盒生成 (強制固定順序：技能、活動、競賽)
# -----------------------------------------------------------------------------
def generate_recommendations(user_input: str, tags: list):
    api_key = os.getenv("GEMINI_API_KEY")
    
    tag_str = "、".join(tags)
    
    # 🎯 全網首創：超大型大學生專業領域直達網址數據庫 (Tag-to-Resource Database)
    # 根據用戶被標記的標籤，動態配對高質感、100% 真實直達課程與活動傳送門！
    tag_resources = {
        "商管行銷": {
            "skill_query": "Google 數位行銷與電商證照課程",
            "skill_url": "https://www.coursera.org/professional-certificates/google-digital-marketing-ecommerce",
            "event_query": "Accupass 商業企劃工作坊專區",
            "event_url": "https://www.accupass.com/",
            "competition_query": "Blink 商業創新競賽看板",
            "competition_url": "https://www.blink.com.tw/board/3/"
        },
        "商業策略": {
            "skill_query": "Hahow 商業邏輯與商戰策略課程",
            "skill_url": "https://hahow.in/courses?category=5a8d9a26323cf1001e3a6c56",
            "event_query": "Accupass 企業經理人論壇大廳",
            "event_url": "https://www.accupass.com/",
            "competition_query": "Blink 商業競賽挑戰看板",
            "competition_url": "https://www.blink.com.tw/board/3/"
        },
        "金融科技": {
            "skill_query": "Coursera 金融科技專業課程 (FinTech)",
            "skill_url": "https://www.coursera.org/specializations/financial-technology-innovations",
            "event_query": "台灣金融研訓院活動公告網",
            "event_url": "https://www.tabf.org.tw/",
            "competition_query": "獎金獵人 金融創新與 FinTech 挑戰賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "創業孵化": {
            "skill_query": "Coursera 創新與創業管理學程",
            "skill_url": "https://www.coursera.org/specializations/startup-entrepreneurship",
            "event_query": "國發會地方創生與創業基地入口網",
            "event_url": "https://www.twrr.ndc.gov.tw/index",
            "competition_query": "獎金獵人 全國青年大專創業提案賽大廳",
            "competition_url": "https://bhuntr.com/tw"
        },
        "軟體工程": {
            "skill_query": "Coursera Python 基礎與物件導向程式",
            "skill_url": "https://www.coursera.org/specializations/python",
            "event_query": "GitHub 官方學生成長大禮包專區",
            "event_url": "https://education.github.com/pack",
            "competition_query": "獎金獵人 全國軟體創意與 App 開發大賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "數據開發": {
            "skill_query": "Coursera Python 大數據分析與 Pandas 實戰課程",
            "skill_url": "https://www.coursera.org/specializations/data-science-python",
            "event_query": "Kaggle 數據分析與大數據挑戰大廳",
            "event_url": "https://www.kaggle.com/",
            "competition_query": "獎金獵人 全國大專數據建模與分析大賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "AI 實踐": {
            "skill_query": "Google 官方機器學習速成課程",
            "skill_url": "https://developers.google.com/machine-learning/crash-course",
            "event_query": "Coursera：人人可學的生成式 AI 課程 (Generative AI for Everyone)",
            "event_url": "https://www.coursera.org/learn/generative-ai-for-everyone-deeplearning-ai",
            "competition_query": "獎金獵人 智慧 AI 應用與演算法挑戰賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "資訊安全": {
            "skill_query": "Coursera Google 資訊安全專業證書",
            "skill_url": "https://www.coursera.org/professional-certificates/google-cybersecurity",
            "event_query": "OWASP 台灣分會安全活動官網",
            "event_url": "https://owasp.org/",
            "competition_query": "獎金獵人 青年資安搶旗賽 (CTF) 專區",
            "competition_url": "https://bhuntr.com/tw"
        },
        "視覺創意": {
            "skill_query": "Hahow 平面視覺設計與排版實戰",
            "skill_url": "https://hahow.in/",
            "event_query": "Canva 官方視覺排版與創意學習大廳",
            "event_url": "https://www.canva.com/",
            "competition_query": "獎金獵人 全國海報與視覺傳達設計競賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "UI/UX設計": {
            "skill_query": "Figma 官方 UI/UX 基礎資源學習庫",
            "skill_url": "https://www.figma.com/resource-library/design-basics/",
            "event_query": "Hahow Figma 介面設計與互動原型實戰課程",
            "event_url": "https://hahow.in/courses?category=5a8d9a26323cf1001e3a6c5f",
            "competition_query": "獎金獵人 數位介面與 UI 創新體驗大賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "影音創作": {
            "skill_query": "Hahow 影片剪輯與 Premiere/AE 動畫實戰",
            "skill_url": "https://hahow.in/courses?category=5a8d9a26323cf1001e3a6c57",
            "event_query": "YouTube 創作者官方學習資源大廳",
            "event_url": "https://creatoracademy.youtube.com/",
            "competition_query": "獎金獵人 微電影與短影音創意大賽專區",
            "competition_url": "https://bhuntr.com/tw"
        },
        "遊戲設計": {
            "skill_query": "Unity 官方遊戲開發學習大廳",
            "skill_url": "https://learn.unity.com/",
            "event_query": "Steam 學生遊戲開發者資源專區",
            "event_url": "https://partner.steamgames.com/",
            "competition_query": "獎金獵人 獨立遊戲開發與虛擬引擎挑戰賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "故事創作": {
            "skill_query": "Hahow 文案寫作與故事劇本創作課程",
            "skill_url": "https://hahow.in/courses?category=5a8d9a26323cf1001e3a6c58",
            "event_query": "Blink 文藝與故事創作自媒體看板",
            "event_url": "https://www.blink.com.tw/board/15/",
            "competition_query": "獎金獵人 青年文學與短篇故事競賽大廳",
            "competition_url": "https://bhuntr.com/tw"
        },
        "跨領域傳播": {
            "skill_query": "Hahow 新媒體行銷與跨領域傳播課程",
            "skill_url": "https://hahow.in/",
            "event_query": "Blink 大學生自媒體與傳播交流大廳",
            "event_url": "https://www.blink.com.tw/board/15/",
            "competition_query": "獎金獵人 創意數位傳播提案賽大廳",
            "competition_url": "https://bhuntr.com/tw"
        },
        "教育科技": {
            "skill_query": "均一教育平台官方多元學習大廳",
            "skill_url": "https://www.junyiacademy.org/",
            "event_query": "教育部官方青年科技教育活動看板",
            "event_url": "https://www.edu.tw/",
            "competition_query": "獎金獵人 全國數位教案與教育科技創新賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "法律思辨": {
            "skill_query": "台大開放式課程：法律思辨與邏輯導論",
            "skill_url": "http://ocw.aca.ntu.edu.tw/",
            "event_query": "司法院官方法律普及與公民體驗論壇",
            "event_url": "https://www.judiciary.gov.tw/",
            "competition_query": "獎金獵人 全國大專法學論辯與模擬法庭挑戰賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "永續轉型": {
            "skill_query": "台灣永續能源研究基金會 ESG 多元學習課程",
            "skill_url": "https://taise.org.tw/",
            "event_query": "環境部官方國家環境學習館大廳",
            "event_url": "https://www.moenv.gov.tw/",
            "competition_query": "獎金獵人 全國 ESG 綠色永續策略提案賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "地方創生": {
            "skill_query": "國發會地方創生青年培力學習網",
            "skill_url": "https://www.twrr.ndc.gov.tw/index",
            "event_query": "社企流社會企業與地方創生專欄",
            "event_url": "https://www.seinsights.asia/",
            "competition_query": "獎金獵人 USR 社會實踐與地方創生創意挑戰",
            "competition_url": "https://bhuntr.com/tw"
        },
        "樂齡設計": {
            "skill_query": "台大開放式課程：高齡化社會與設計思考",
            "skill_url": "http://ocw.aca.ntu.edu.tw/",
            "event_query": "Accupass 樂齡照護與銀髮創新設計工作坊專區",
            "event_url": "https://www.accupass.com/",
            "competition_query": "獎金獵人 全國大專樂齡科技與福祉設計賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "自我探索": {
            "skill_query": "教育部青年發展署 生涯探索與職場輔導專區",
            "skill_url": "https://www.yda.gov.tw/",
            "event_query": "台大開放式課程：心理學大講堂與人際探索",
            "event_url": "http://ocw.aca.ntu.edu.tw/",
            "competition_query": "Blink 大學生職涯探索與交流看板",
            "competition_url": "https://www.blink.com.tw/board/9/"
        },
        "專案管理": {
            "skill_query": "Hahow PMP 專案管理實戰基礎課",
            "skill_url": "https://hahow.in/",
            "event_query": "專案管理學會 PMI 官方學生資源大廳",
            "event_url": "https://www.pmi.org/",
            "competition_query": "獎金獵人 跨領域青年專案執行策略挑戰",
            "competition_url": "https://bhuntr.com/tw"
        },
        "領導統籌": {
            "skill_query": "Coursera 卓越領導力與組織管理課程",
            "skill_url": "https://www.coursera.org/specializations/leadership-management",
            "event_query": "教育部青年發展署 青年領袖培訓大廳",
            "event_url": "https://www.yda.gov.tw/",
            "competition_query": "Blink 學生會與社團領導人成長看板",
            "competition_url": "https://www.blink.com.tw/board/1/"
        },
        "國際視野": {
            "skill_query": "EF 官方國際語文與跨文化培訓大廳",
            "skill_url": "https://www.ef.com.tw/",
            "event_query": "教育部青年發展署 海外國際體驗專區",
            "event_url": "https://www.yda.gov.tw/",
            "competition_query": "獎金獵人 全國青年國際外交與英語模擬聯合國賽",
            "competition_url": "https://bhuntr.com/tw"
        },
        "口語表達": {
            "skill_query": "Hahow 簡報傳達與說服性口語表達課程",
            "skill_url": "https://hahow.in/",
            "event_query": "教育部青年發展署 青年表達與思辨論壇",
            "event_url": "https://www.yda.gov.tw/",
            "competition_query": "獎金獵人 全國大專盃演講與簡報大賽",
            "competition_url": "https://bhuntr.com/tw"
        }
    }

    mock_skill = {
        "type": "skill",
        "title": "⚡ 盲盒 01：技能修煉 — 硬實力補強",
        "category": "數位與關鍵工具進修 (Skill)",
        "theme": f"針對 {tags[0] if tags else '跨域'} 特質的 Python 數據分析 Pandas 實戰 或是 Figma 介面設計",
        "desc": "行銷與企劃不只靠直覺，要用數據與精美視覺說服人！多這項實用工具，你在分組報告與實習招募中就是無法被取代的即戰力！",
        "roadmap_1": "🧭 步驟一【觀摩打底】：每天花 30 分鐘，在 YouTube 或是 Coursera 上看基礎教學，掌握基本操作與常用語法工具。",
        "roadmap_2": "🤝 步驟二【臨摹實戰】：把你的學校報告或生活數據，用此工具重新整理。例如把簡報視覺化，或做出一個 UI Mockup。",
        "roadmap_3": "🏆 步驟三【專案輸出】：將這個作品整理成精美的 PDF 作品集，放在履歷上當作硬實力最好的即戰力佐證材料！",
        "search_query": "Coursera Python 數據科學實戰課程",
        "search_url": "https://www.coursera.org/specializations/data-science-python"
    }

    mock_event = {
        "type": "event",
        "title": "🌱 盲盒 02：探索人脈 — 實體實踐活動",
        "category": "社會設計/地方創生體驗 (Event)",
        "theme": "高齡樂齡設計工作坊 或是 綠色永續與地方創生論壇",
        "desc": "別整天關在學校同溫層！去線下工作坊走走，理解真實社會痛點，並在協作中認識有熱忱、跨領域的團隊，人脈就是這樣打開的！",
        "roadmap_1": "🧭 步驟一【報名加入】：在 Accupass 上搜尋此主題，挑選一場兩天的週末線下工作坊報名，勇敢跨出第一步！",
        "roadmap_2": "🤝 步驟二【跨域協作】：活動中主動擔任溝通橋樑，用你的行銷或設計專業與組員協作，合力產出一個解決方案模型。",
        "roadmap_3": "🏆 步驟三【人脈留存】：活動結束後，主動加組員與講師的 LinkedIn 或 Instagram，將這次緣分轉化為長期的成長智囊團！",
        "search_query": "Accupass 官方活動平台大廳",
        "search_url": "https://www.accupass.com/"
    }

    mock_competition = {
        "type": "competition",
        "title": "🏆 盲盒 03：職涯起跑 — 實戰競賽挑戰",
        "category": "商業策略與品牌提案賽 (Competition)",
        "theme": "大專院校永續商業創新 (ESG) 提案賽 或是 全國大專行銷爭霸戰",
        "desc": "你履歷上正缺乏一個具備說服力的『代表作』！這種競賽強迫你解決企業真實題目。不要等變強才去，去邊打邊學！",
        "roadmap_1": "🧭 步驟一【跨界組隊】：在 Blink 或社群上尋找 3~4 位不同背景的隊友，確保團隊裡有技術、簡報、行銷多方好手。",
        "roadmap_2": "🤝 步驟二【痛點解題】：針對競賽企業的痛點做深度調研，避開天馬行空的幻想，產出一份具備財務估算與可行性的商案簡報。",
        "roadmap_3": "🏆 步驟三【複盤寫入】：無論得獎與否，將這段經驗用 STAR 原則（情境、任務、行動、結果）寫進履歷，證明你具備商案實戰力！",
        "search_query": "獎金獵人 (台灣最大青年競賽平台)",
        "search_url": "https://bhuntr.com/tw"
    }

    # 根據用戶的第一個標籤，動態配對並覆寫 Mock 資料的網址和名稱！實現離線狀態下的「千人千面」
    primary_tag = tags[0] if tags else "自我探索"
    res = tag_resources.get(primary_tag, tag_resources["自我探索"])
    
    mock_skill["search_query"] = res["skill_query"]
    mock_skill["search_url"] = res["skill_url"]
    mock_event["search_query"] = res["event_query"]
    mock_event["search_url"] = res["event_url"]
    mock_competition["search_query"] = res["competition_query"]
    mock_competition["search_url"] = res["competition_url"]

    if "商管" in tag_str or "行銷" in tag_str:
        mock_skill["theme"] = "Python 數據分析 Pandas 實戰（用數據支撐你的行銷案）"
        mock_skill["desc"] = "行銷不只靠嘴，要用數字說服人！懂行銷又懂 Python 數據分析或 Tableau 的人，在各大實習招募中都是搶手貨，點亮它吧！"
    elif "軟體" in tag_str or "數據" in tag_str or "AI" in tag_str:
        mock_skill["theme"] = "UI/UX Figma 介面設計與 Canva 視覺傳達"
        mock_skill["desc"] = "寫程式也需要美學！學會如何把複雜的演算法與數據，用最精美、直覺的視覺呈現給非技術主管聽，是你在科技業的殺手鐧！"

    if not api_key:
        return [mock_skill, mock_event, mock_competition]

    try:
        client = genai.Client()
        prompt = f"""
        請根據用戶的特質標籤：{tags}，為他量身打造三個「個人化行動建議盲盒」。
        
        【參考真實網站/課程 URL 資料庫】
        我們提供了一個真實、多元的直達學習與活動 URL 對照庫（這將作為你生成 search_query 與 search_url 的唯一真實依據）：
        {json.dumps(tag_resources, ensure_ascii=False)}
        
        【強制約束規範】
        1. 輸出的 JSON 陣列長度必須剛好為 3，且順序與種類必須嚴格固定為：
           - 第一個盲盒: 技能 (type: "skill") ➔ 建議進修的硬實力或核心數位工具。
           - 第二個盲盒: 活動 (type: "event") ➔ 擴大交友圈與實踐的講座、工作坊、地方創生或體驗。
           - 第三個盲盒: 競賽 (type: "competition") ➔ 提供背景補強的大學生實戰商業/技術競賽建議。
        
        2. 【重要】前往參考網站連結的生成規則：
           - 請從上述提供之 URL 資料庫中，尋找最貼近該用戶標籤 {tags} 的類別。
           - 對於第一個技能盲盒 (skill)，請將對應類別的 "skill_query" 和 "skill_url" 填入它的 search_query 與 search_url 欄位。
           - 對於第二個活動盲盒 (event)，請將對應類別 the "event_query" 和 "event_url" 填入它的 search_query 與 search_url 欄位。
           - 對於第三個競賽盲盒 (competition)，請將對應類別的 "competition_query" 和 "competition_url" 填入它的 search_query 與 search_url 欄位。
           - 嚴禁胡亂捏造網址，也不要一律推薦同一個網址，必須根據用戶的標籤對齊數據庫，確保千人千面的多元化與真實性！
           
        每個盲盒的 JSON 必須包含：
        - type: "skill" 或 "event" 或 "competition"
        - title: 標題（如：⚡ 盲盒 01：技能修煉 — 硬實力補強）
        - category: 具體種類
        - theme: 具體主題/建議方向
        - desc: 一針見血的推薦理由 (約100字，直擊大學生履歷空白、焦慮痛點)
        - roadmap_1: 實踐歷程步驟一（🧭 步驟一【起步/打底】：...）
        - roadmap_2: 實踐歷程步驟二（🤝 步驟二【實戰/協作】：...）
        - roadmap_3: 實踐歷程步驟三（🏆 步驟三【收割/履歷】：...）
        - search_query: 配對到的參考平台名稱
        - search_url: 配對到的真實直達 URL
        
        請直接以 JSON Array 格式輸出，不要有任何 Markdown 包裹或文字。
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        res_list = json.loads(response.text)
        type_order = {"skill": 0, "event": 1, "competition": 2}
        try:
            res_list.sort(key=lambda x: type_order.get(x.get("type", "skill"), 0))
        except Exception:
            pass
        return res_list
    except Exception as e:
        return [mock_skill, mock_event, mock_competition]

# -----------------------------------------------------------------------------
# 6. 自動下滑 JS
# -----------------------------------------------------------------------------
def trigger_auto_scroll():
    components.html("""
        <script>
            setTimeout(() => {
                const parentMain = window.parent.document.querySelector('.main');
                if (parentMain) {
                    parentMain.scrollTo({
                        top: parentMain.scrollHeight,
                        behavior: 'smooth'
                    });
                }
            }, 350);
        </script>
    """, height=0)

# -----------------------------------------------------------------------------
# 7. 主頁面渲染 (Wide 寬版面)
# -----------------------------------------------------------------------------
st.markdown("<div class='warm-title'>☕ 引路微光</div>", unsafe_allow_html=True)
st.markdown("<div class='warm-subtitle'>🌱「每一顆種子，都有適合它發芽的土壤」🌱</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PART 1: 寫信給學長姐 💬
# -----------------------------------------------------------------------------
st.markdown("""
    <div class='section-card'>
        <div class='tape-deco-premium'>💌 MAILBOX</div>
        <h4 style='color: #8D5B4C; margin-top:0; text-align:center; font-size:1.35rem; font-weight: 800;'>寫一封信給學長姐</h4>
        <p style='color: #6D5952; font-size: 0.98rem; text-align:center;'>聊聊你的主修、最近想精進什麼，或是目前對什麼領域感到好奇？學長姐會幫你挑出核心特質標籤。</p>
    </div>
""", unsafe_allow_html=True)

# 單欄居中的輸入區與遞交按鈕
col_center1, col_center2, col_center3 = st.columns([1, 6, 1])
with col_center2:
    user_desc_input = st.text_area(
        label="在此輸入你的背景描述...",
        placeholder="我是商管學生，未來想做行銷，平常喜歡自省，對高齡社會創新專案有興趣，也略懂 Python...",
        label_visibility="collapsed",
        value=st.session_state.user_desc,
        height=140
    )

    # 溫馨一鍵帶入自述範例，極致防呆設計
    st.markdown("<p style='color: #8D5B4C; font-size: 0.88rem; font-weight: 800; margin-bottom: 6px; margin-top: 10px;'>💡 沒靈感？點擊下方學長姐自述範例一鍵帶入：</p>", unsafe_allow_html=True)
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        if st.button("💼 商管行銷流 ➔", use_container_width=True, key="demo_mkt"):
            st.session_state.user_desc = "我是商管大三學生，未來想做行銷與產品企劃。平常喜歡自我探索，對高齡樂齡設計、社會創新很有興趣，也略懂 Python 數據分析與簡報傳達。"
            st.rerun()
    with col_e2:
        if st.button("💻 科技工程流 ➔", use_container_width=True, key="demo_tech"):
            st.session_state.user_desc = "我是資工系大二，想精進 AI 實踐與軟體工程技術。喜歡研究機器學習、ChatGPT 等科技工具。休閒時喜歡動漫與遊戲設計，希望未來能做出自己的軟體專案。"
            st.rerun()
    with col_e3:
        if st.button("🎨 藝術設計流 ➔", use_container_width=True, key="demo_art"):
            st.session_state.user_desc = "我是視覺傳達系學生，擅長插畫與視覺創意。想多接觸 UI/UX 設計以及專案管理，對永續轉型與地方創生感興趣，希望能將美學融入永續設計。"
            st.rerun()

    if st.session_state.step == 1:
        st.markdown("<div style='margin-top:15px;'>", unsafe_allow_html=True)
        if st.button("創造我的興趣標籤", use_container_width=True):
            if user_desc_input.strip() == "":
                st.warning("信件內容空空的，多寫幾個字讓學長姐認識你吧！")
            else:
                with st.spinner("學長姐正在細心拆信，閱讀你的心聲..."):
                    st.session_state.user_desc = user_desc_input
                    st.session_state.tags = extract_tags_from_text(user_desc_input)
                    st.session_state.step = 2
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PART 2: 標籤確認與微調 🏷️ (Step >= 2 才顯示)
# -----------------------------------------------------------------------------
if st.session_state.step >= 2:
    st.markdown("""
        <div class='whisper-card'>
            <div class='whisper-title'>💬 學長姐悄悄話</div>
            <div class='whisper-body'>
                「別焦慮！大學生活就像是開盲盒，你寫的每個字，都在對齊你未來的人脈頻率。看，我幫你讀取出的特質如下，這就是你的起點喔！」
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='section-card'>
            <div class='tape-deco-premium'>🏷️ RADAR TAGS</div>
            <h4 style='color: #8D5B4C; margin-top:0; text-align:center; font-size:1.35rem; font-weight:800;'>學長姐讀取到的你</h4>
            <p style='color: #6D5952; font-size: 0.98rem; text-align:center;'>這些是目前調諧出的特質標籤。點擊下方 ❌ 可立刻刪除，也歡迎手動輸入其他標籤隨意調整！</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 6, 1])
    with col_c2:
        if st.session_state.tags:
            st.markdown("<div style='text-align:center; background-color:#FCFAF7; border-radius:20px; padding:15px; border:1px solid #E8DCC4;'>", unsafe_allow_html=True)
            cols_chips = st.columns(len(st.session_state.tags))
            for idx, tag in enumerate(st.session_state.tags):
                with cols_chips[idx]:
                    st.markdown(f"<div style='text-align:center; margin-bottom:10px;'><span class='warm-chip-premium'>🏷️ {tag}</span></div>", unsafe_allow_html=True)
                    st.markdown("<div class='del-btn' style='text-align:center;'>", unsafe_allow_html=True)
                    if st.button("❌", key=f"del_{tag}"):
                        st.session_state.tags.remove(tag)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("目前沒有標籤，快手動新增幾個吧！")
            
        st.markdown("<br>", unsafe_allow_html=True)
        col_input, col_add = st.columns([3, 1])
        with col_input:
            new_tag = st.text_input(
                label="手動新增特質標籤", 
                placeholder="例如：自我探索、跨域創新、心理學...",
                label_visibility="collapsed"
            )
        with col_add:
            if st.button("新增特質 ➕", use_container_width=True):
                if new_tag and new_tag.strip() not in st.session_state.tags:
                    st.session_state.tags.append(new_tag.strip())
                    st.rerun()

        if st.session_state.step == 2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("建立我的專屬活動盲盒", use_container_width=True):
                st.session_state.step = 3
                st.session_state.recommended_events = generate_recommendations(st.session_state.user_desc, st.session_state.tags)
                st.session_state.show_balloons = True
                st.rerun()

# -----------------------------------------------------------------------------
# PART 3: 開啟活動盲盒 🛍️ (Step == 3 才顯示，實體軟木塞佈告欄)
# -----------------------------------------------------------------------------
if st.session_state.step == 3:
    if st.session_state.get("show_balloons", False):
        st.balloons()
        st.session_state.show_balloons = False
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='corkboard'>
            <div class='tape-deco-premium' style='background-color:#8D5B4C; color:white; width:160px; top:-15px;'>📌 TODAY'S BOARD</div>
            <div class='corkboard-title'>☕ 學長姐今日公告：專屬你的活動盲盒</div>
            <p style='color: #6D5952; font-size: 0.95rem; text-align:center; margin-bottom: 20px; font-weight:500; padding:0 20px;'>
               在 Wide 全寬公佈欄上，盲盒已<b>橫向一排完美呈現！從左至右依序為：技能、活動、競賽</b>！<br>
               翻面後點擊<b>『深入瞭解』</b>，將伴隨彈跳動畫為你翻開<b>極致奢華的實踐學習地圖手冊</b>！
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    events_json = json.dumps(st.session_state.recommended_events, ensure_ascii=False)
    
    # 🎯 橫向一排 React Component 大改造：
    # 最外層使用 flex flex-row flex-nowrap justify-center items-center，寬度設定在 max-w-6xl。
    # 卡片寬度精確設為 w-[18.5rem] (296px)，總寬小於 1000px，確保在 Wide 模式下 100% 橫向一排展開，絕不折行！
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdn.tailwindcss.com"></script>
      <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
      <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
      <script src="https://unpkg.com/framer-motion@10.16.4/dist/framer-motion.js"></script>
      <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
      
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
        body {
          font-family: 'Noto Sans TC', sans-serif;
          background-color: #FAF0E6;
          margin: 0;
          padding: 0;
          overflow: hidden;
        }
        .perspective-1000 { perspective: 1000px; }
        .preserve-3d { transform-style: preserve-3d; }
        .backface-hidden { backface-visibility: hidden; }
        .rotate-y-180 { transform: rotateY(180deg); }
      </style>
    </head>
    <body>
      <div id="root" class="flex justify-center items-center py-2 relative w-full h-[600px]"></div>
    
      <script type="text/babel">
        const { useState } = React;
        const { motion, AnimatePresence } = window.Motion || window.framerMotion;
    
        const recommendedEvents = __EVENTS_JSON_PLACEHOLDER__;
    
        const typeStyles = {
          skill: { 
            bg: 'from-[#E2B49A] to-[#A86F58]', 
            label: '⚡ 建議技能', 
            btnBg: 'bg-[#6D5952]',
            btnText: 'text-white'
          },
          event: { 
            bg: 'from-[#F4E3B1] to-[#D5A75C]', 
            label: '🌱 活動實踐', 
            btnBg: 'bg-[#E07A5F]',
            btnText: 'text-white'
          },
          competition: { 
            bg: 'from-[#E8DCC4] to-[#CBB190]', 
            label: '🏆 競賽建議', 
            btnBg: 'bg-[#8D5B4C]',
            btnText: 'text-white' 
          }
        };
    
        const WarmCard = ({ eventData, onLearnMore }) => {
          const [isFlipped, setIsFlipped] = useState(false);
          const style = typeStyles[eventData.type] || typeStyles.skill;
    
          return (
            <div className="w-[18.5rem] h-[23rem] perspective-1000 mx-3 flex-shrink-0">
              <motion.div
                className="w-full h-full relative preserve-3d"
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ type: "spring", stiffness: 120, damping: 14 }}
                whileHover={{ scale: 1.05, y: -8 }}
              >
                {/* 正面 */}
                <div 
                  className={`absolute w-full h-full backface-hidden rounded-[2rem] shadow-[0_12px_25px_rgba(141,91,76,0.12)] p-5 flex flex-col justify-between items-center border border-[#E8DCC4]/30 bg-gradient-to-br ${style.bg} text-[#3D3430] cursor-pointer`}
                  onClick={() => setIsFlipped(true)}
                >
                  <div className="text-[10px] font-bold tracking-wider bg-white/70 px-3 py-1 rounded-full text-[#6D5952] select-none">
                    {style.label}
                  </div>
                  
                  <div className="flex flex-col items-center space-y-3 my-auto">
                    <motion.div 
                      animate={{ y: [0, -5, 0], rotate: [0, -2, 2, 0] }}
                      transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                      whileHover={{ scale: 1.15, rotate: [0, -5, 5, 0] }}
                      className="text-6xl filter drop-shadow-md select-none"
                    >
                      🛍️
                    </motion.div>
                    <h3 className="font-bold text-base text-[#3D3430] tracking-wide mt-1 select-none">開啟溫慢小袋</h3>
                  </div>
                  <p className="text-[10px] text-[#6D5952]/80 font-bold select-none">今日專屬推薦 (點擊翻開)</p>
                </div>
    
                {/* 背面 */}
                <div className="absolute w-full h-full backface-hidden rounded-[2rem] shadow-[0_15px_30px_rgba(61,52,48,0.12)] p-5 bg-[#FCF9F5] border-2 border-dashed border-[#E8DCC4] text-[#3D3430] flex flex-col rotate-y-180 overflow-y-auto relative">
                  
                  <button 
                    className="absolute top-3 right-3 text-[10px] font-bold bg-[#FAF0E6] hover:bg-[#E8DCC4] border border-[#E8DCC4] text-[#8D5B4C] px-2 py-0.5 rounded transition-all"
                    onClick={() => setIsFlipped(false)}
                  >
                    ↺ 返回
                  </button>
    
                  <div className="absolute -top-1 left-4 w-20 h-4 bg-[#FAF0E6]/95 border border-[#E8DCC4]/30 rotate-1 shadow-sm opacity-90 flex items-center justify-center text-[8px] text-[#8D5B4C] font-mono select-none">
                    ⭐ WARM TAPE
                  </div>
    
                  <div className="text-[9px] font-bold text-[#E07A5F] mt-3 mb-1 uppercase tracking-widest select-none">
                    {style.label}
                  </div>
                  <h4 className="text-sm font-bold mb-2 border-b border-dashed border-[#E8DCC4] pb-1.5 text-[#3D3430] leading-snug">
                    {eventData.title}
                  </h4>
                  
                  <div className="text-[11px] leading-relaxed text-[#6D5952] flex-1 overflow-y-auto pr-1">
                     <p className="italic bg-[#FAF0E6] p-2.5 rounded-xl border border-[#E8DCC4]/50 leading-relaxed text-[11px]">
                       「{eventData.desc}」
                     </p>
                  </div>
    
                  <button 
                    className={`w-full py-2.5 rounded-xl font-bold transition-all shadow-md active:scale-95 mt-2 ${style.btnBg} ${style.btnText} hover:opacity-95 text-xs`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onLearnMore(eventData);
                    }}
                  >
                    深入瞭解 ☕
                  </button>
                </div>
              </motion.div>
            </div>
          );
        };
    
        const PracticeModal = ({ data, onClose }) => {
          if (!data) return null;
          const style = typeStyles[data.type] || typeStyles.skill;
    
          return (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            >
              <motion.div 
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                transition={{ type: "spring", stiffness: 150, damping: 18 }}
                className="bg-[#FCF9F5] border-4 border-dashed border-[#CBB190] rounded-[2.5rem] p-10 max-w-4xl w-full max-h-[550px] overflow-y-auto shadow-2xl relative text-[#3D3430]"
              >
                <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-40 h-6 bg-[#FAF0E6]/90 border border-[#E8DCC4]/30 rotate-1 shadow-sm flex items-center justify-center text-[10px] text-[#8D5B4C] font-mono select-none">
                  ⭐ PRACTICE MAP
                </div>
    
                <button 
                  className="absolute top-4 right-4 bg-[#E07A5F] hover:bg-[#D0694D] text-white font-bold text-xs px-5 py-2 rounded-full shadow-sm transition-all"
                  onClick={onClose}
                >
                  ❌ 關閉手冊
                </button>
    
                <div className="text-xs font-bold text-[#E07A5F] mt-3 uppercase tracking-widest">{style.label}</div>
                <h3 className="text-2xl font-bold mb-5 border-b-2 border-dashed border-[#E8DCC4] pb-2 text-[#3D3430]">{data.theme}</h3>
    
                <div className="space-y-5 pr-1">
                  <div className="bg-[#FAF0E6] p-5 rounded-2xl border border-[#E8DCC4]/40 text-base leading-relaxed">
                    <span className="font-bold text-[#8D5B4C]">💡 學長姐推薦理由：</span>
                    <p className="mt-1.5 text-[#6D5952] italic">「{data.desc}」</p>
                  </div>
    
                  <div className="border-l-2 border-dashed border-[#E8DCC4] pl-6 ml-2 py-1 space-y-5">
                    <div className="relative">
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#E07A5F] border-2 border-white"></div>
                      <p className="text-base leading-relaxed text-[#6D5952] font-semibold">{data.roadmap_1}</p>
                    </div>
                    <div className="relative">
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#D5A75C] border-2 border-white"></div>
                      <p className="text-base leading-relaxed text-[#6D5952] font-semibold">{data.roadmap_2}</p>
                    </div>
                    <div className="relative">
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-[#8D5B4C] border-2 border-white"></div>
                      <p className="text-base leading-relaxed text-[#6D5952] font-semibold">{data.roadmap_3}</p>
                    </div>
                  </div>
    
                  <div className="pt-4 flex items-center justify-between border-t border-dashed border-[#E8DCC4] mt-6">
                    <div className="text-sm text-[#8D5B4C] font-bold">
                      <span>🔗 建議參考網站/平台:</span>
                      <div className="bg-[#FAF0E6] px-3 py-1 rounded border border-[#E8DCC4]/20 text-sm mt-2 font-mono text-[#3D3430]">{data.search_query}</div>
                    </div>
                    
                    <button 
                      className={`px-8 py-3.5 rounded-xl font-bold transition-all shadow-md active:scale-95 ${style.btnBg} ${style.btnText} hover:opacity-95 text-sm`}
                      onClick={() => window.open(data.search_url, '_blank')}
                    >
                      前往參考網站 ☕
                    </button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          );
        };
    
        const App = () => {
          const [modalData, setModalData] = useState(null);
    
          return (
            <div className="w-full h-full relative flex flex-col justify-center items-center">
              {/* 卡片橫排容器：支援橫向滾動，防擠壓 */}
              <div className="flex flex-row flex-nowrap justify-start md:justify-center items-center w-full max-w-6xl px-2 overflow-x-auto overflow-y-hidden py-4 scrollbar-thin">
                {recommendedEvents.map((ev, i) => (
                  <WarmCard key={i} eventData={ev} onLearnMore={(d) => setModalData(d)} />
                ))}
              </div>
    
              <AnimatePresence>
                {modalData && (
                  <PracticeModal data={modalData} onClose={() => setModalData(null)} />
                )}
              </AnimatePresence>
            </div>
          );
        };
    
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
      </script>
    </body>
    </html>
    """
    
    html_code = html_template.replace("__EVENTS_JSON_PLACEHOLDER__", events_json)
    components.html(html_code, height=610)
    


# -----------------------------------------------------------------------------
# 8. 重置與自動下滑觸發
# -----------------------------------------------------------------------------
if st.session_state.step > 1:
    st.markdown("<br>", unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns([1,2,1])
    with col_r2:
        if st.button("重設推薦雷達 🔄", use_container_width=True):
            st.session_state.step = 1
            st.session_state.tags = []
            st.session_state.user_desc = ""
            st.rerun()
    
    trigger_auto_scroll()
