# 「盲盒式」社團與活動人脈推薦助理 — 深度規劃方案 (AIWeb_plan.md)

本規劃方案針對 `Project_outline.md` 進行技術升級與工程細化，拋棄高大上的空洞概念，直接給出核心架構、資料庫 Schema、關鍵演算法與前端動態組件的具體實作程式碼。

---

## 🛠️ 1. 架構升級與技術選型 (Tech Stack 2.0)

為確保 MVP 階段的**超高開發速度**與**極致的視覺震撼力（Premium UI）**，建議捨棄傳統複雜的獨立前後端架構，改採現代 Serverless Edge 架構，或精簡版 Python + React Stack：

```
[前端: Next.js 14 (App Router) + TailwindCSS + Framer Motion]
       │ (透過 Vercel Edge Functions 進行 Serverless 呼叫)
       ▼
[AI 引擎: Gemini 1.5 Pro/Flash] ◄──► [向量資料庫: Supabase (PostgreSQL + pgvector)]
```

*   **優勢**：
    *   **pgvector**：直接在 PostgreSQL 內做向量搜尋，免去維護 Pinecone/Chroma 與 PostgreSQL 兩套資料庫的同步地獄（Out-of-sync）。
    *   **Framer Motion**：實現 3D 卡片翻轉、流光與粒子效果，這是盲盒「開箱儀式感」的視覺核心。
    *   **Gemini 1.5 Flash**：利用超大 Context window 與極快的推理速度，做用戶標籤動態比對與 Markdown 渲染。

---

## 🗄️ 2. 資料庫設計 (Database Schema & pgvector)

我們直接在 PostgreSQL 中啟用 `pgvector` 擴充套件。以下是具體的 SQL DDL 定義，包含用戶畫像表、活動表以及「不感興趣」的負回饋追蹤表（用以打破同溫層與避免重複推薦）：

```sql
-- 啟用向量套件
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. 用戶資料表
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname VARCHAR(50) NOT NULL,
    major VARCHAR(100),
    tags TEXT[], -- 萃取出的標籤：['商管', 'Python', '行銷']
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 活動/社團資料表
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    organization VARCHAR(100),
    description TEXT NOT NULL,
    category VARCHAR(50), -- '💼 背景補強', '🌱 興趣延伸', '🎁 盲盒驚喜'
    tags TEXT[],
    event_url TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    location TEXT,
    embedding VECTOR(1536), -- 儲存活動說明的語意向量 (使用 Gemini text-embedding-004, 實際維度為 768 或 1536)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 用戶推薦歷史與負回饋表 (避免重複並做推薦修正)
CREATE TABLE user_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(event_id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL, -- 'opened' (點開), 'dismissed' (滑掉不感興趣), 'applied' (報名)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧠 3. 盲盒推薦引擎核心邏輯 (Recommendation Algorithm)

盲盒推薦的精髓是：**1 🚀 背景補強 + 1 🌱 興趣延伸 + 1 🎁 跨界驚喜**。
以下是 Python FastAPI 的推薦路由核心程式碼，展示如何利用 `pgvector` 的餘弦相似度，搭配隨機度（Random offset）混合撈出 3 筆活動：

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
from pgvector.psycopg2 import register_vector

app = FastAPI()

class RecommendRequest(BaseModel):
    user_id: str
    user_embedding: List[float] # 用戶當前興趣標籤的平均向量

@app.post("/api/recommend")
async def get_blind_box(req: RecommendRequest):
    # 連線至 Supabase / PostgreSQL
    conn = psycopg2.connect("postgresql://...")
    register_vector(conn)
    cur = conn.cursor()
    
    try:
        # 1. 排除用戶過去 7 天內「滑掉(dismissed)」或「已推薦過」的活動
        exclude_query = """
            SELECT event_id FROM user_feedback 
            WHERE user_id = %s AND (action = 'dismissed' OR created_at > NOW() - INTERVAL '7 days')
        """
        cur.execute(exclude_query, (req.user_id,))
        excluded_ids = [row[0] for row in cur.fetchall()]
        if not excluded_ids:
            excluded_ids = ['00000000-0000-0000-0000-000000000000'] # dummy
            
        # 🎯 盲盒 1：背景補強 (相似度最高，相似度權重 0.9)
        cur.execute("""
            SELECT event_id, title, description, category, event_url 
            FROM events 
            WHERE event_id NOT IN %s
            ORDER BY embedding <=> %s::vector
            LIMIT 1;
        """, (tuple(excluded_ids), req.user_embedding))
        box_career = cur.fetchone()
        
        # 🎯 盲盒 2：興趣延伸 (相似度中等，跳過前 3 筆最相似，取第 4 筆，或改隨機偏移)
        cur.execute("""
            SELECT event_id, title, description, category, event_url 
            FROM events 
            WHERE event_id NOT IN %s AND event_id != %s
            ORDER BY embedding <=> %s::vector
            LIMIT 1 OFFSET 3;
        """, (tuple(excluded_ids), box_career[0] if box_career else '00000000-0000-0000-0000-000000000000', req.user_embedding))
        box_interest = cur.fetchone()

        # 🎯 盲盒 3：驚喜爆彈 (隨機取樣跨領域活動，餘弦相似度在大於 0.4 且小於 0.7 的區間隨機抽樣)
        cur.execute("""
            SELECT event_id, title, description, category, event_url 
            FROM events 
            WHERE event_id NOT IN %s 
              AND event_id NOT IN (%s, %s)
              AND (embedding <=> %s::vector) BETWEEN 0.3 AND 0.7
            ORDER BY RANDOM()
            LIMIT 1;
        """, (
            tuple(excluded_ids), 
            box_career[0] if box_career else '00000000-0000-0000-0000-000000000000', 
            box_interest[0] if box_interest else '00000000-0000-0000-0000-000000000000',
            req.user_embedding
        ))
        box_surprise = cur.fetchone()
        
        return {
            "status": "success",
            "boxes": [
                {"type": "career", "data": box_career},
                {"type": "interest", "data": box_interest},
                {"type": "surprise", "data": box_surprise}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
```

---

## 💬 4. Gemini System Prompt 精準調教

後端呼叫 Gemini API 時的 System Instruction 設定。這裡除了限制 `MAX_EVENTS = 3` 外，還特別加入了 **「直擊痛點的暖男/辣妹學長姐人格」**，並確保回覆內容的 Markdown 結構嚴格符合前端解析格式：

```markdown
你是一位在大學打滾多年、看透各種社團與競賽、最懂學生職涯痛點的「毒舌卻暖心的學長姐」。
你的任務是將系統推薦給用戶的 3 個活動，用最具說服力、幽默且一針見血的口吻包裝成 Markdown 格式。

【強制輸出規範】
1. 每次回覆只能且必須包含剛好 3 個活動。
2. 語氣要像在跟學弟妹聊天，拒絕使用「親愛的用戶」、「您好」等官腔。
3. 每個活動必須明確指出「為什麼你該去（直擊痛點）」與「去完能帶走什麼（實質收穫，如：充實履歷的專案經歷、認識行銷圈大佬）」。
4. 嚴格遵守以下 Markdown 輸出結構，以便前端精準擷取「點擊進入」按鈕的超連結：

### [盲盒類型] 📦 活動名
> **學長姐碎碎念**：[一針見血的痛點分析]
* **你將獲得**：[具體收穫]
* **傳送門**：[點我開啟盲盒]([EVENT_URL])
```

---

## 🎨 5. 溫暖聚落風格「Q彈手寫便條卡片」組件 (React + Framer Motion)

為了呼應 **「☕溫暖聚落 (Warm Community)」** 的療癒、友善氛圍，我們捨棄冰冷的科技暗色調。
*   **視覺色彩**：以米白色、燕麥色（`#FAF6F0` / `#FCF9F5`）為底色，搭配暖橘色（`#E07A5F`）、深褐大地色（`#3D3430`）。
*   **介面排版**：圓角（`rounded-3xl`）、手寫體感覺（字體建議使用 *Noto Sans TC* 搭配手寫風 *Chenyuluobei*），活動卡片模擬實體公佈欄上的「紙膠帶手寫便條紙」。
*   **互動體驗**：盲盒是一只輕飄飄、**帶有呼吸感與Q彈震動（Spring Physics）**的「市集牛皮紙袋 🛍️」，點擊開啟時袋子會彈跳並撕開，翻轉出溫暖的便條紙卡。

```tsx
// components/WarmCommunityCard.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface BoxProps {
  type: 'career' | 'interest' | 'surprise';
  title: string;
  markdownContent: string;
}

// 溫暖聚落色彩定義 (大地烘焙色系)
const typeStyles = {
  career: { 
    bg: 'bg-gradient-to-br from-[#E8DCC4] to-[#CBB190]', 
    label: '💼 背景補強', 
    btnBg: 'bg-[#8D5B4C]',
    btnText: 'text-white' 
  },
  interest: { 
    bg: 'bg-gradient-to-br from-[#F4E3B1] to-[#D5A75C]', 
    label: '🌱 興趣延伸', 
    btnBg: 'bg-[#E07A5F]',
    btnText: 'text-white'
  },
  surprise: { 
    bg: 'bg-gradient-to-br from-[#E2B49A] to-[#A86F58]', 
    label: '🎁 盲盒驚喜', 
    btnBg: 'bg-[#6D5952]',
    btnText: 'text-white'
  }
};

export const WarmCommunityCard: React.FC<BoxProps> = ({ type, title, markdownContent }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const currentStyle = typeStyles[type];

  return (
    <div className="w-80 h-96 perspective-1000 cursor-pointer" onClick={() => setIsFlipped(!isFlipped)}>
      <motion.div
        className="w-full h-full relative preserve-3d duration-700"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ type: "spring", stiffness: 120, damping: 15 }} // 彈性 Q 彈動畫
        whileHover={{ scale: 1.03, y: -5 }}
      >
        {/* 卡片正面 - 市集手繪牛皮紙袋 */}
        <div className={`absolute w-full h-full backface-hidden rounded-3xl shadow-[0_12px_30px_rgba(141,91,76,0.12)] p-6 flex flex-col justify-between items-center border border-[#E8DCC4]/30 ${currentStyle.bg} text-[#3D3430]`}>
          <div className="text-xs font-semibold tracking-wider bg-white/60 px-3 py-1 rounded-full text-[#6D5952]">
            {currentStyle.label}
          </div>
          
          <div className="my-auto text-center space-y-3">
            {/* 牛皮紙袋 Q 彈呼吸與懸停抖動 */}
            <motion.div 
              animate={{ 
                y: [0, -6, 0],
                rotate: [0, -2, 2, 0]
              }}
              transition={{ 
                repeat: Infinity, 
                duration: 2.5, 
                ease: "easeInOut" 
              }}
              whileHover={{ scale: 1.15, rotate: [0, -5, 5, 0] }}
              className="text-7xl filter drop-shadow-md"
            >
              🛍️
            </motion.div>
            <h3 className="font-bold text-lg tracking-wide text-[#3D3430] font-sans">打開溫暖小袋</h3>
          </div>
          <p className="text-xs text-[#6D5952]/70 font-medium">今天還可以開啟 3/3 個聚落</p>
        </div>

        {/* 卡片背面 - 實體手寫便條紙 (公佈欄風格) */}
        <div className="absolute w-full h-full backface-hidden rounded-3xl shadow-[0_15px_35px_rgba(61,52,48,0.1)] p-6 bg-[#FCF9F5] border-2 border-dashed border-[#E8DCC4] text-[#3D3430] flex flex-col rotate-y-180 overflow-y-auto relative">
          
          {/* 紙膠帶 Deco 特效 */}
          <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-24 h-5 bg-[#FAF0E6]/80 border border-[#E8DCC4]/30 rotate-1 shadow-sm opacity-90 flex items-center justify-center text-[10px] text-[#8D5B4C] font-mono select-none">
            ⭐ TAPE
          </div>

          <div className="text-xs font-bold text-[#E07A5F] mt-2 mb-1">{currentStyle.label}</div>
          <h4 className="text-base font-bold mb-3 border-b-2 border-dashed border-[#E8DCC4] pb-2 text-[#3D3430] font-sans">
            {title}
          </h4>
          
          <div className="text-sm flex-1 leading-relaxed text-[#6D5952] font-medium font-sans">
             {/* 這邊可用 react-markdown 渲染學長姐的溫馨手寫留言 */}
             <p className="italic bg-[#FAF0E6] p-3 rounded-xl border border-[#E8DCC4]/50 mb-2">
               「這場社會實踐能帶你到第一線接觸高齡創新，雖然有點累，但能學到很多課堂上沒有的人情溫度喔！」
             </p>
          </div>

          <button className={`mt-4 w-full py-2.5 rounded-xl font-bold tracking-wide transition-all shadow-md active:scale-95 ${currentStyle.btnBg} ${currentStyle.btnText}`}>
            去看看吧 ☕
          </button>
        </div>
      </motion.div>
    </div>
  );
};
```

*(註：在全域 CSS 中引入 `.perspective-1000 { perspective: 1000px; }` 與 `.preserve-3d { transform-style: preserve-3d; }` 即可啟用 3D 翻轉)*

---

## 🚀 6. 獨特加分項功能 (Unfair Advantages) — 領先市場的規劃

1.  **「每日限額與飢餓行銷 (Daily Limit & Quota)」**
    *   大學生容易彈性疲乏，一次給太多反而選擇障礙。
    *   **設計**：每天伺服器在凌晨 12 點重置，用戶僅有 3 次翻牌機會。消耗完後，卡片會呈現「鎖定狀態」，並倒數計時「距離下次盲盒重置還有 XX 小時」。這能大幅提升留存率（D1 Retention）與降低 AI Token 的消耗成本。
2.  **「履歷一鍵對齊 (Resume Synchronizer)」**
    *   用戶點擊「衝一波（確認參加）」後，系統自動將該活動記錄在用戶的「成長歷程資料庫」。
    *   在學期末或求職季，用戶點擊「生成履歷描述」，AI 會分析他參加過的盲盒活動，直接寫成符合 STAR 原則的 Resume Bullets，讓活動人脈直接轉換為求職即戰力。
3.  **「AI 自動化活動爬蟲 (LLM-based Crawler)」**
    *   直接寫死 BeautifulSoup 容易因為網站改版而壞掉。
    *   **規劃**：採用 **Playwright + Gemini Flash**。每週自動開啟 Accupass 與學校公告，由 Gemini 讀取 HTML 的 `innerText`，直接精確結構化輸出為 JSON，再利用 embedding 存入 pgvector。這完全免去了繁瑣的正規表達式與 CSS Selector 維護。
