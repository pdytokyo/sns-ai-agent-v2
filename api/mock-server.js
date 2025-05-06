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
  
  setTimeout(() => {
    res.json({
      script: `# ${theme}に関するスクリプト\n\nこんにちは、今日は${theme}について話します。\n\n${theme}は現代社会において非常に重要なトピックです。多くの人々が日々この問題に直面しています。\n\nまず、${theme}の基本的な概念を理解することが大切です。次に、実践的なアプローチを考えていきましょう。\n\n最後に、${theme}を日常生活に取り入れる方法をご紹介します。`,
      alt: `# 別の${theme}スクリプト\n\n皆さん、${theme}について考えたことはありますか？\n\n今日は${theme}の魅力と可能性について探っていきます。\n\n${theme}は私たちの生活を豊かにする可能性を秘めています。具体的な例を見ていきましょう。\n\n1. ${theme}の歴史\n2. 現代における${theme}の役割\n3. 未来の${theme}の展望\n\nぜひコメントで皆さんの${theme}体験を教えてください！`
    });
  }, 1500);
});

app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
  console.log('Mock API ready');
});
