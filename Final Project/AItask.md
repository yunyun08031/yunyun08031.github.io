# 盲盒式社團與活動人脈推薦助理 — 實戰開發任務清單 (AItask.md)

本文件結合 `AIWeb_plan.md` 的規格需求與 `hug.md` 對於活動爬蟲模組的可行性探討，針對「Accupass、Blink、校內公告」等高難度爬取目標，給出具體可行的爬蟲實作程式碼，並拆解出階段式的開發 Task List。

---

## 🔍 一、 爬蟲模組可行性修正建議 (Feasibility & Crawler Strategy)

### 1. 傳統爬蟲的痛點（為何 BeautifulSoup 會失敗？）
*   **Accupass** 採用 GraphQL API 與動態載入，且設有強大的 Cloudflare WAF，直接用靜態 GET 請求會被秒擋。
*   **校內公告** 結構混亂、毫無 API 標準，每個處室的網頁格式都不同，維護 CSS Selector 將會是地獄。

### 2. 破局方案：Playwright + Gemini 智慧爬蟲（實踐代碼）
我們採用 **Playwright** 模擬真實瀏覽器繞過 Cloudflare，並將抓到的無效 HTML/Text 直接餵給 **Gemini API** 進行結構化資料轉換（Structured Output），直接輸出符合 Pydantic 格式的活動資料。

以下是高度可行的 Python 爬蟲核心實作程式碼，請直接加入開發專案：

```python
# crawler/smart_crawler.py
import asyncio
from playwright.async_api import async_playwright
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import json

# 1. 定義活動結構化輸出格式 (Pydantic Schema)
class EventSchema(BaseModel):
    title: str = Field(description="活動或社團招募的名稱")
    organization: str = Field(description="主辦單位或社團名稱")
    description: str = Field(description="活動內容的精簡總結（約100字）")
    category: str = Field(description="分類，必須是 '💼 背景補強', '🌱 興趣延伸', '🎁 盲盒驚喜' 其中之一")
    tags: List[str] = Field(description="活動關鍵字標籤，例如 ['商管', 'Python', '行銷', '社創']")
    event_url: str = Field(description="活動報名或詳細資訊的來源網址")
    start_time: Optional[str] = Field(description="活動開始時間，ISO 8601 格式，若無則留空")
    location: Optional[str] = Field(description="活動舉辦地點，若為線上則填寫 '線上'")

class EventListSchema(BaseModel):
    events: List[EventSchema]

# 2. 智慧爬蟲主程式
async def scrape_and_extract(url: str) -> Optional[EventListSchema]:
    async with async_playwright() as p:
        # 啟動 Chromium 瀏覽器，設定 user-agent 繞過 Cloudflare
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"🔗 正在導航至: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 取得網頁純文字，過濾掉無用的 HTML tags 減輕 Token 負擔
            body_text = await page.evaluate("() => document.body.innerText")
            await browser.close()
            
            # 3. 呼叫 Gemini 進行結構化擷取
            print("🧠 正在使用 Gemini 進行資料結構化與標籤萃取...")
            client = genai.Client() # 預設讀取 GEMINI_API_KEY 環境變數
            
            prompt = f"""
            請分析以下網頁的純文字內容，並從中萃取出所有有價值的「大學生活動、社團招募、競賽、講座」資訊。
            
            網頁來源網址: {url}
            網頁純文字內容:
            ---
            {body_text[:8000]} -- 限制長度避免爆 Token
            ---
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EventListSchema,
                    temperature=0.1
                ),
            )
            
            # 解析結果
            result = EventListSchema.model_validate_json(response.text)
            return result

        except Exception as e:
            print(f"❌ 爬取或解析失敗: {e}")
            await browser.close()
            return None

# 測試運行
if __name__ == "__main__":
    test_url = "https://www.accupass.com/event/250520123456" # 請替換為真實 Accupass 頁面
    loop = asyncio.get_event_loop()
    events = loop.run_until_complete(scrape_and_extract(test_url))
    if events:
        print(json.dumps(events.model_dump(), indent=2, ensure_ascii=False))
```

---

## 📝 二、 開發任務清單 (AItask TODO List)

本清單將開發流程拆解為 4 大階段，以利團隊進行敏捷開發：

### 🏁 階段一：基礎建設與資料庫初始化 (Milestone 1)
- [ ] **1.1 環境變數與專案初始化**
  - 初始化 FastAPI + Next.js 專案結構。
  - 設定 `.env`（包含 `GEMINI_API_KEY`、`DATABASE_URL`）。
- [ ] **1.2 PostgreSQL + pgvector 資料庫架設**
  - 在 Supabase / 本地 Docker 啟動 PostgreSQL。
  - 執行 `CREATE EXTENSION IF NOT EXISTS vector;` 啟用向量支援。
  - 執行 `AItask.md` / `AIWeb_plan.md` 中定義的 DDL，建立 `users`、`events`、`user_feedback` 資料表。

### 🕷️ 階段二：AI 智慧爬蟲與向量管道建置 (Milestone 2)
- [ ] **2.1 實作 Playwright 網頁抓取模組**
  - 安裝 `playwright` 與 `google-genai` 套件。
  - 完成 `crawler/smart_crawler.py` 的編寫。
- [ ] **2.2 活動資料向量化 (Vector Embedding Pipeline)**
  - 當爬蟲抓到 `EventSchema` 資料後，呼叫 Gemini Embedding API 將 `title + description` 轉為 1536 維度向量。
  - 將向量與活動詳細資料一併寫入 PostgreSQL 的 `events` 資料表。
- [ ] **2.3 爬蟲定時排程 (Cron Job)**
  - 使用 Python `APScheduler` 或 GitHub Actions，設定每週固定時間自動執行爬蟲並寫入資料庫。

### 🧠 階段三：後端 API 與推薦演算法實作 (Milestone 3)
- [ ] **3.1 用戶 Onboarding 與標籤萃取 API**
  - 實作對話接口：接收用戶輸入（例如：「我是商管學生想做行銷...」）。
  - 透過 Gemini API 萃取出 `現有優勢`、`技能缺口`、`潛在興趣` 三大類標籤。
  - 將萃取出的標籤進行向量化，計算出用戶的 `user_embedding` 並儲存。
- [ ] **3.2 盲盒推薦演算法實作**
  - 完成 FastAPI 推薦路由 `/api/recommend`。
  - 用 SQL 餘弦相似度 `<=>` 實現：
    * 💼 **背景補強**（相似度最高）。
    * 🌱 **興趣延伸**（相似度中等，以 OFFSET 跳過最接近項）。
    * 🎁 **盲盒驚喜**（相似度 `0.3~0.7` 間隨機撈取，突破資訊繭房）。
  - 串接負回饋過濾（過濾已看過或 dismissed 的 `event_id`）。
- [ ] **3.3 Gemini 學長姐語氣包裝 API**
  - 實作 System Instruction，將撈出的 3 個活動格式化輸出成直擊痛點的 Markdown。

### 🎨 階段四：前端溫暖聚落風格 UI 與 Q彈互動 (Milestone 4)
- [ ] **4.1 Onboarding 標籤確認面板**
  - 製作符合燕麥色系的療癒系標籤微調 UI，讓用戶可以自由點擊 `x` 刪除或手動新增標籤。
- [ ] **4.2 3D 溫暖牛皮紙袋卡片與 Framer Motion 彈跳特效**
  - 使用大地烘焙色系，實作模擬實體公佈欄上「紙膠帶手寫便條紙」的活動卡片。
  - 設計「市集牛皮紙袋 🛍️」的 Q 彈呼吸與懸停抖動動畫。
  - 加入 `Framer Motion` 3D 翻轉（正面紙袋，背面手寫便條紙），採用彈性物理 (Spring physics) 帶來安心且踏實的開箱回饋。
- [ ] **4.3 每日重置與聚落開箱機制 (Gamification)**
  - 使用 LocalStorage / 資料庫限制用戶每天只能開啟 3 個溫暖小袋。
  - 加入「去看看吧 ☕」按鈕，點擊後觸發 `applied` 回饋並引導至活動傳送門。
- [ ] **4.4 履歷一鍵對齊 (STAR 原則生成)**
  - 用戶可在個人中心查看已參加的活動。
  - 點擊「一鍵優化履歷」，後端串接 Gemini，將活動歷程轉換為精美履歷描述。
