import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/ui/toast/use-toast'
import { Loader2 } from 'lucide-react'

type Stage = 'theme' | 'options' | 'edit'

type ScriptSection = {
  type: string
  content: string
  duration?: number
  original_reel_id?: string
}

type Script = {
  id: string
  title: string
  style: string
  sections: ScriptSection[]
  original_reel_id: string
  engagement_stats: {
    like_count: number
    comment_count: number
    view_count: number
  }
}

type Target = {
  age?: string
  gender?: string
  interest?: string
}

export default function Home() {
  const [stage, setStage] = useState<Stage>('theme')
  const [theme, setTheme] = useState('')
  const [target, setTarget] = useState<string>('{}')
  const [useSavedSettings, setUseSavedSettings] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [scripts, setScripts] = useState<Script[]>([])
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)
  const [editedSections, setEditedSections] = useState<ScriptSection[]>([])
  const [matchingReelsCount, setMatchingReelsCount] = useState(0)
  const { toast } = useToast()

  const clientId = "c123"

  const handleThemeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!theme.trim()) return
    
    setIsLoading(true)
    
    toast({
      title: 'データ収集中...',
      description: 'Instagramからデータを収集しています。しばらくお待ちください。',
    })
    
    try {
      let targetObj: Target = {}
      
      try {
        if (target.trim()) {
          targetObj = JSON.parse(target)
        }
      } catch (e) {
        console.error('Invalid target JSON:', e)
        toast({
          title: 'ターゲット設定エラー',
          description: '正しいJSON形式で入力してください。例: {"age":"18-24","interest":"study"}',
          variant: 'destructive',
        })
        setIsLoading(false)
        return
      }
      
      const response = await fetch('http://localhost:8000/script/auto', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: clientId,
          theme,
          target: Object.keys(targetObj).length > 0 ? targetObj : undefined,
          need_video: false,
          use_saved_settings: useSavedSettings
        }),
      })
      
      if (!response.ok) {
        throw new Error('スクリプト生成に失敗しました')
      }
      
      const data = await response.json()
      
      setScripts(data.scripts || [])
      setMatchingReelsCount(data.matching_reels_count || 0)
      setStage('options')
    } catch (error) {
      console.error('スクリプト生成エラー:', error)
      toast({
        title: 'エラー',
        description: 'スクリプト生成に失敗しました。もう一度お試しください。',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleScriptSelect = (script: Script) => {
    setSelectedScript(script)
    setEditedSections([...script.sections])
    setStage('edit')
  }

  const handleSectionChange = (index: number, content: string) => {
    const newSections = [...editedSections]
    newSections[index] = { ...newSections[index], content }
    setEditedSections(newSections)
  }

  const handleSaveScript = async () => {
    if (!selectedScript) return
    
    setIsLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/script/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: clientId,
          script_id: selectedScript.id,
          option: 1, // 選択したオプション番号
          sections: editedSections
        }),
      })
      
      if (!response.ok) {
        throw new Error('スクリプト保存に失敗しました')
      }
      
      toast({
        title: '保存しました！',
        description: 'スクリプトが正常に保存されました。',
        variant: "default"
      })
    } catch (error) {
      console.error('スクリプト保存エラー:', error)
      toast({
        title: 'エラー',
        description: 'スクリプト保存に失敗しました。もう一度お試しください。',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
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
              <div className="space-y-2">
                <label className="text-sm font-medium">テーマ</label>
                <Input
                  placeholder="スクリプトのテーマを入力..."
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">ターゲット設定 (JSON)</label>
                <Input
                  placeholder='{"age":"18-24","interest":"study"}'
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500">
                  年齢層、性別、興味関心をJSON形式で指定できます
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="useSavedSettings"
                  checked={useSavedSettings}
                  onChange={(e) => setUseSavedSettings(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="useSavedSettings" className="text-sm">
                  保存設定を使用する
                </label>
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
              <h1 className="text-2xl font-bold">スクリプト選択</h1>
              <p className="text-gray-500">生成されたスクリプトから選択してください</p>
              <p className="text-sm text-blue-600 mt-1">一致リール数: {matchingReelsCount}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scripts.map((script) => (
                <Button 
                  key={script.id} 
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start text-left"
                  onClick={() => handleScriptSelect(script)}
                >
                  <div className="flex justify-between items-center mb-2 w-full">
                    <h3 className="font-medium">{script.title}</h3>
                    <span className="text-sm text-gray-500">{script.style}</span>
                  </div>
                  <div className="text-sm whitespace-pre-line">
                    {script.sections.map((section, idx) => (
                      <div key={idx} className="mb-2">
                        {section.content}
                      </div>
                    ))}
                  </div>
                  <div className="text-xs text-gray-400 mt-2 self-end">
                    エンゲージメント: いいね {script.engagement_stats.like_count}・コメント {script.engagement_stats.comment_count}
                  </div>
                </Button>
              ))}
            </div>
            
            <Button onClick={() => setStage('theme')}>
              テーマ入力に戻る
            </Button>
          </div>
        )
        
      case 'edit':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">スクリプト編集</h1>
              <p className="text-gray-500">選択したスクリプトを編集してください</p>
            </div>
            
            {selectedScript && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">{selectedScript.title}</h3>
                  <span className="text-sm text-gray-500">{selectedScript.style}</span>
                </div>
                
                {editedSections.map((section, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between">
                      <label className="text-xs font-medium">
                        {section.type === 'intro' ? 'イントロ' : 
                         section.type === 'main' ? 'メイン' : 
                         section.type === 'cta' ? 'CTA' : section.type}
                      </label>
                      {section.duration && (
                        <span className="text-xs text-gray-400">
                          推奨尺: {section.duration}秒
                        </span>
                      )}
                    </div>
                    <Textarea
                      value={section.content}
                      onChange={(e) => handleSectionChange(idx, e.target.value)}
                      className="min-h-[100px]"
                    />
                  </div>
                ))}
                
                <div className="text-xs text-gray-400 italic text-center">
                  元の構造を維持することで最高のパフォーマンスが得られます。必要に応じて特定の編集を行ってください。
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={() => setStage('options')}
                    disabled={isLoading}
                  >
                    選択に戻る
                  </Button>
                  <Button 
                    onClick={handleSaveScript}
                    disabled={isLoading}
                  >
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    保存する
                  </Button>
                </div>
              </div>
            )}
          </div>
        )
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="container max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-center mb-6">
            <div className="flex space-x-4">
              <div className={`flex flex-col items-center ${stage === 'theme' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'theme' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                  1
                </div>
                <span className="text-sm mt-1">テーマ</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === 'options' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'options' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                  2
                </div>
                <span className="text-sm mt-1">選択</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === 'edit' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'edit' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                  3
                </div>
                <span className="text-sm mt-1">編集・保存</span>
              </div>
            </div>
          </div>
          
          {renderStage()}
        </div>
      </div>
    </main>
  )
}
