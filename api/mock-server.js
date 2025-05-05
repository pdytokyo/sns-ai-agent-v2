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

app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
});
