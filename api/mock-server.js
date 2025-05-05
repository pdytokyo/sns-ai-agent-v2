const express = require('express');
const cors = require('cors');
const app = express();
const port = 8000;

app.use(cors());
app.use(express.json());

app.post('/script', (req, res) => {
  const { theme } = req.body;
  
  if (!theme) {
    return res.status(400).json({ error: 'Theme is required' });
  }
  
  // Simulate API delay
  setTimeout(() => {
    // Mock response with two script options
    const scripts = [
      {
        id: '1',
        title: 'Option 1',
        style: 'Problem-Solution Style',
        content: `👋 Struggling with ${theme}? I was too until I found these 3 game-changers.

🔥 First: The 90/20 rule. Work intensely for 90 minutes, then take a FULL 20-minute break. Your brain needs this reset!

🔥 Second: Create a dedicated workspace that you ONLY use for work. Your brain will associate this space with focus mode.

🔥 Third: End your workday with a shutdown ritual. Write tomorrow's top 3 tasks and physically close your laptop.

Which hack are you trying first? Drop a comment! #ProductivityTips`
      },
      {
        id: '2',
        title: 'Option 2',
        style: 'Day-in-the-Life Style',
        content: `POV: How I mastered ${theme}

Morning routine is EVERYTHING. I prep cold brew the night before + set out my workout clothes.

7AM: Quick 20-min workout instead of scrolling. This single habit changed my ENTIRE day.

8:30AM: Time block my calendar before opening emails. Game-changer!

12PM: Actual lunch break AWAY from my desk. No phone allowed.

3PM energy slump? 10-min walk outside instead of another coffee.

Saved 2+ hours in my day. What part are you struggling with? #ProductivityHacks`
      }
    ];
    
    res.json({ scripts });
  }, 1500);
});

app.post('/script/auto', (req, res) => {
  const { theme, target, client_id, need_video, use_saved_settings } = req.body;
  
  if (!theme) {
    return res.status(400).json({ error: 'Theme is required' });
  }
  
  // Simulate API delay
  setTimeout(() => {
    // Mock response with two script options in the new format
    const scripts = [
      {
        id: '1',
        title: '問題解決型',
        style: '問題解決型',
        original_reel_id: 'mock_reel_1',
        engagement_stats: {
          like_count: 1250,
          comment_count: 87,
          view_count: 15000
        },
        sections: [
          {
            type: 'intro',
            content: `👋 ${theme}で悩んでいませんか？私も同じでした。でも、この3つのゲームチェンジャーを見つけるまでは。`,
            duration: 10
          },
          {
            type: 'main',
            content: `🔥 まず：90/20ルール。90分間集中して作業し、その後完全に20分休憩します。脳はこのリセットが必要です！

🔥 次に：作業専用のスペースを作りましょう。あなたの脳はこのスペースを集中モードと関連付けます。

🔥 最後に：一日の終わりにシャットダウン儀式を行いましょう。明日のトップ3タスクを書き出し、物理的にラップトップを閉じます。`,
            duration: 30
          },
          {
            type: 'cta',
            content: `どのハックを最初に試しますか？コメントで教えてください！ #${theme}のコツ`,
            duration: 5
          }
        ]
      },
      {
        id: '2',
        title: '日常紹介型',
        style: '日常紹介型',
        original_reel_id: 'mock_reel_2',
        engagement_stats: {
          like_count: 980,
          comment_count: 65,
          view_count: 12000
        },
        sections: [
          {
            type: 'intro',
            content: `POV: 私がどのように${theme}をマスターしたか`,
            duration: 8
          },
          {
            type: 'main',
            content: `朝のルーティンが全てです。前日の夜に水出しコーヒーを準備し、運動着を出しておきます。

午前7時：スクロールする代わりに、素早い20分のワークアウト。この習慣が一日を変えました。

午前8時30分：メールを開く前にカレンダーでタイムブロッキング。ゲームチェンジャーです！

正午：デスクから離れて実際のランチブレイク。スマホは禁止。

午後3時のエネルギー低下？別のコーヒーの代わりに外で10分間歩きます。`,
            duration: 35
          },
          {
            type: 'cta',
            content: `一日に2時間以上節約できました。あなたはどの部分で苦労していますか？ #${theme}のハック`,
            duration: 7
          }
        ]
      }
    ];
    
    res.json({ 
      scripts,
      matching_reels_count: 8 // Mock number of matching reels
    });
  }, 2000);
});

app.post('/script/save', (req, res) => {
  const { client_id, script_id, option, sections } = req.body;
  
  if (!script_id || !sections) {
    return res.status(400).json({ error: 'Script ID and sections are required' });
  }
  
  // Simulate API delay
  setTimeout(() => {
    res.json({ 
      success: true,
      message: 'Script saved successfully'
    });
  }, 1000);
});

app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
});
