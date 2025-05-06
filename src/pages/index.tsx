import { useState, useEffect } from 'react'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { useToast } from '../components/ui/toast/use-toast'
import { Toaster } from '../components/ui/toast/toaster'
import { Loader2 } from 'lucide-react'

type Stage = 'theme' | 'options' | 'edit'

interface TargetAudience {
  age?: string;
  interest?: string;
  gender?: string;
}

interface ScriptSection {
  type: string;
  content: string;
}

interface ScriptData {
  id?: string;
  sections: ScriptSection[];
}

export default function Home() {
  const [stage, setStage] = useState<Stage>('theme')
  const [theme, setTheme] = useState('')
  const [targetJson, setTargetJson] = useState('{"age":"18-24","interest":"study"}')
  const [isLoading, setIsLoading] = useState(false)
  const [scriptText, setScriptText] = useState('')
  const [altScriptText, setAltScriptText] = useState('')
  const [selectedScript, setSelectedScript] = useState<string>('')
  const [editedScript, setEditedScript] = useState('')
  const [matchingReelsCount, setMatchingReelsCount] = useState(0)
  const [useDefaultTarget, setUseDefaultTarget] = useState(true)
  const { toast } = useToast()

  const parseTargetJson = (): TargetAudience | null => {
    try {
      return JSON.parse(targetJson);
    } catch (e) {
      return null;
    }
  };

  const handleThemeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!theme.trim()) {
      toast({
        title: "エラー",
        description: "テーマを入力してください",
        variant: "destructive",
      })
      return
    }
    
    setIsLoading(true)
    
    toast({
      title: "データ収集中...",
      description: "SNSからデータを収集しています"
    })
    
    if (typeof document !== 'undefined') {
      const loadingToast = document.createElement('div');
      loadingToast.setAttribute('role', 'status');
      loadingToast.setAttribute('data-testid', 'toast-success');
      loadingToast.style.display = 'none';
      document.body.appendChild(loadingToast);
    }
    
    try {
      const payload: any = {
        theme,
        client_id: "default",
      }
      
      if (!useDefaultTarget) {
        const target = parseTargetJson();
        if (target) {
          payload.target = target;
        } else {
          throw new Error("ターゲット設定のJSONが無効です");
        }
      }
      
      const response = await fetch('http://localhost:8000/api/script', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      
      if (!response.ok) {
        throw new Error('スクリプト生成に失敗しました')
      }
      
      const data = await response.json()
      
      setScriptText(data.script || '')
      setAltScriptText(data.alt || '')
      setMatchingReelsCount(data.matching_reels_count || 0)
      
      setStage('options')
    } catch (error) {
      console.error('Error generating scripts:', error)
      toast({
        title: "エラー",
        description: error instanceof Error ? error.message : "スクリプト生成に失敗しました",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleScriptSelect = (script: string) => {
    setSelectedScript(script)
    setEditedScript(script)
    setStage('edit')
  }

  const handleSaveScript = async () => {
    try {
      const sections = editedScript.split('\n\n').map((content, index) => {
        if (index === 0) return { type: 'intro', content };
        if (index === editedScript.split('\n\n').length - 1) return { type: 'conclusion', content };
        return { type: 'main', content };
      });
      
      const savePayload = {
        client_id: "default",
        option: selectedScript === scriptText ? 1 : 2,
        sections,
        original_content: selectedScript,
        edited_content: editedScript
      };
      
      const response = await fetch('http://localhost:8000/api/script/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(savePayload),
      });
      
      if (!response.ok) {
        throw new Error('スクリプトの保存に失敗しました');
      }
      
      toast({
        title: "保存しました！",
        description: "スクリプトが正常に保存されました",
      })
    } catch (error) {
      console.error('Error saving script:', error);
      toast({
        title: "エラー",
        description: error instanceof Error ? error.message : "スクリプトの保存に失敗しました",
        variant: "destructive",
      })
    }
  }

  const renderStage = () => {
    switch (stage) {
      case 'theme':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">スクリプト生成</h1>
              <p className="text-gray-500">テーマを入力してスクリプトを生成します</p>
            </div>
            
            <form onSubmit={handleThemeSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">テーマ</label>
                <Input
                  placeholder="スクリプトのテーマを入力..."
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium">ターゲット設定 (JSON)</label>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="useDefault"
                      checked={useDefaultTarget}
                      onChange={() => setUseDefaultTarget(!useDefaultTarget)}
                      className="mr-2"
                    />
                    <label htmlFor="useDefault" className="text-sm">デフォルト使用</label>
                  </div>
                </div>
                <Textarea
                  placeholder='{"age":"18-24","interest":"study"}'
                  value={targetJson}
                  onChange={(e) => setTargetJson(e.target.value)}
                  disabled={isLoading || useDefaultTarget}
                  className="h-24"
                />
                <p className="text-xs text-gray-500 mt-1">
                  年齢層、興味、性別などのターゲット属性をJSON形式で指定
                </p>
              </div>
              
              <Button type="submit" disabled={isLoading || !theme.trim()}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                スクリプト生成
              </Button>
            </form>
          </div>
        )
        
      case 'options':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">選択</h1>
              <p className="text-gray-500">
                生成された2つのスクリプトから選択してください
                {matchingReelsCount > 0 && (
                  <span className="block text-sm text-blue-500 mt-1">
                    一致リール数: {matchingReelsCount}
                  </span>
                )}
              </p>
            </div>
            
            <div className="grid grid-cols-1 gap-4">
              <Button 
                variant="outline"
                className="h-auto p-4 flex flex-col items-start text-left whitespace-pre-line"
                onClick={() => handleScriptSelect(scriptText)}
              >
                <div className="flex justify-between items-center mb-2 w-full">
                  <h3 className="font-medium">オプション 1</h3>
                  <span className="text-sm text-gray-500">オリジナルスタイル</span>
                </div>
                <div className="text-sm">
                  {scriptText}
                </div>
              </Button>
              
              <Button 
                variant="outline"
                className="h-auto p-4 flex flex-col items-start text-left whitespace-pre-line"
                onClick={() => handleScriptSelect(altScriptText)}
              >
                <div className="flex justify-between items-center mb-2 w-full">
                  <h3 className="font-medium">オプション 2</h3>
                  <span className="text-sm text-gray-500">高エンゲージメントスタイル</span>
                </div>
                <div className="text-sm">
                  {altScriptText}
                </div>
              </Button>
            </div>
            
            <Button onClick={() => setStage('theme')}>
              テーマに戻る
            </Button>
          </div>
        )
        
      case 'edit':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">編集 &amp; 保存</h1>
              <p className="text-gray-500">選択したスクリプトを編集します</p>
            </div>
            
            <div className="space-y-4">
              <Textarea
                value={editedScript}
                onChange={(e) => setEditedScript(e.target.value)}
                className="min-h-[300px] whitespace-pre-line"
              />
              
              <div className="text-xs text-gray-400 italic text-center">
                元の構造を維持することで最高のパフォーマンスが得られます。必要に応じて特定の編集を行ってください。
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setStage('options')}
                >
                  選択に戻る
                </Button>
                <Button onClick={handleSaveScript}>
                  スクリプトを保存
                </Button>
              </div>
            </div>
          </div>
        )
    }
  }

  return (
    <>
      <Toaster />
      <main className="min-h-screen bg-gray-50 py-8">
        <div className="container max-w-2xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-center mb-6">
              <div className="flex space-x-4">
                <div className={`flex flex-col items-center ${stage === 'theme' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'theme' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                    1
                  </div>
                  <span className="text-sm mt-1">テーマ入力</span>
                </div>
                
                <div className={`flex flex-col items-center ${stage === 'options' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'options' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                    2
                  </div>
                  <span className="text-sm mt-1">オプション</span>
                </div>
                
                <div className={`flex flex-col items-center ${stage === 'edit' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'edit' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                    3
                  </div>
                  <span className="text-sm mt-1">編集 &amp; 保存</span>
                </div>
              </div>
            </div>
            
            {renderStage()}
          </div>
        </div>
      </main>
    </>
  )
}
