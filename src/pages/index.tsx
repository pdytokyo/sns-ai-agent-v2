import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/ui/toast/use-toast'
import { Loader2 } from 'lucide-react'

type Stage = 'theme' | 'options' | 'edit'
type Script = {
  id: string
  title: string
  content: string
  style: string
}

export default function Home() {
  const [stage, setStage] = useState<Stage>('theme')
  const [theme, setTheme] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [scripts, setScripts] = useState<Script[]>([])
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)
  const [editedScript, setEditedScript] = useState('')
  const { toast } = useToast()

  const handleThemeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!theme.trim()) return
    
    setIsLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/script', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ theme }),
      })
      
      if (!response.ok) {
        throw new Error('Failed to generate scripts')
      }
      
      const data = await response.json()
      
      setScripts(data.scripts || [])
      setStage('options')
    } catch (error) {
      console.error('Error generating scripts:', error)
      toast({
        title: 'Error',
        description: 'Failed to generate scripts. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleScriptSelect = (script: Script) => {
    setSelectedScript(script)
    setEditedScript(script.content)
    setStage('edit')
  }

  const handleSaveScript = () => {
    // Save the edited script to local component state
    if (selectedScript) {
      const updatedScript = { ...selectedScript, content: editedScript }
      const updatedScripts = scripts.map(script => 
        script.id === selectedScript.id ? updatedScript : script
      )
      setScripts(updatedScripts)
      setSelectedScript(updatedScript)
      
      toast({
        title: 'Saved!',
        description: 'Your script has been saved successfully.',
        variant: "default"
      })
    }
  }

  const renderStage = () => {
    switch (stage) {
      case 'theme':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Script Generator</h1>
              <p className="text-gray-500">Enter a theme to generate script options</p>
            </div>
            
            <form onSubmit={handleThemeSubmit} className="space-y-4">
              <div>
                <Input
                  placeholder="Enter a theme for your script..."
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <Button type="submit" disabled={isLoading || !theme.trim()}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Generate Scripts
              </Button>
            </form>
          </div>
        )
        
      case 'options':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Select a Script</h1>
              <p className="text-gray-500">Choose one of the generated scripts</p>
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
                    {script.content}
                  </div>
                </Button>
              ))}
            </div>
            
            <Button onClick={() => setStage('theme')}>
              Back to Theme
            </Button>
          </div>
        )
        
      case 'edit':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">Edit Script</h1>
              <p className="text-gray-500">Make changes to your selected script</p>
            </div>
            
            {selectedScript && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">{selectedScript.title}</h3>
                  <span className="text-sm text-gray-500">{selectedScript.style}</span>
                </div>
                
                <Textarea
                  value={editedScript}
                  onChange={(e) => setEditedScript(e.target.value)}
                  className="min-h-[300px]"
                />
                
                <div className="text-xs text-gray-400 italic text-center">
                  Maintain the original structure for best performance. Make specific edits as needed.
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={() => setStage('options')}
                  >
                    Back to Options
                  </Button>
                  <Button onClick={handleSaveScript}>
                    Save Script
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
                <span className="text-sm mt-1">Theme</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === 'options' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'options' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                  2
                </div>
                <span className="text-sm mt-1">Options</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === 'edit' ? 'text-primary font-medium' : 'text-gray-400'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === 'edit' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400'}`}>
                  3
                </div>
                <span className="text-sm mt-1">Edit & Save</span>
              </div>
            </div>
          </div>
          
          {renderStage()}
        </div>
      </div>
    </main>
  )
}
