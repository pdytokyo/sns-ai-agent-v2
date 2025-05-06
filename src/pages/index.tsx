import React, { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { useToast } from "../components/ui/toast/use-toast";
import { Toaster } from "../components/ui/toast/toaster";
import { Loader2 } from "lucide-react";

type Stage = "theme" | "options" | "edit";
type Script = {
  script: string;
  alt: string;
};

export default function Home() {
  const [stage, setStage] = useState<Stage>("theme");
  const [theme, setTheme] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [scripts, setScripts] = useState<Script | null>(null);
  const [selectedScript, setSelectedScript] = useState<string>("");
  const [editedScript, setEditedScript] = useState("");
  const { toast } = useToast();

  const handleThemeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!theme.trim()) return;
    
    setIsLoading(true);
    toast({
      title: "生成中...",
      description: "スクリプトを生成しています",
      duration: 5000,
    });
    
    try {
      const response = await fetch("http://localhost:8000/script", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ theme }),
      });
      
      if (!response.ok) {
        throw new Error("Failed to generate scripts");
      }
      
      const data = await response.json();
      setScripts(data);
      setStage("options");
    } catch (error) {
      console.error("Error generating scripts:", error);
      toast({
        title: "エラー",
        description: "スクリプト生成に失敗しました。もう一度お試しください。",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleScriptSelect = (script: string) => {
    setSelectedScript(script);
    setEditedScript(script);
    setStage("edit");
  };

  const handleSaveScript = () => {
    setSelectedScript(editedScript);
    
    toast({
      title: "保存しました！",
      description: "スクリプトが正常に保存されました。",
    });
  };

  const renderStage = () => {
    switch (stage) {
      case "theme":
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">スクリプト生成</h1>
              <p className="text-gray-500">テーマを入力してスクリプトを生成してください</p>
            </div>
            
            <form onSubmit={handleThemeSubmit} className="space-y-4">
              <div>
                <Input
                  placeholder="スクリプトのテーマを入力..."
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              
              <Button type="submit" disabled={isLoading || !theme.trim()}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                スクリプト生成
              </Button>
            </form>
          </div>
        );
        
      case "options":
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">選択</h1>
              <p className="text-gray-500">生成されたスクリプトから選択してください</p>
            </div>
            
            {scripts && (
              <div className="grid grid-cols-1 gap-4">
                <Button 
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start text-left"
                  onClick={() => handleScriptSelect(scripts.script)}
                >
                  <div className="text-sm whitespace-pre-line">
                    {scripts.script}
                  </div>
                </Button>
                
                <Button 
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start text-left"
                  onClick={() => handleScriptSelect(scripts.alt)}
                >
                  <div className="text-sm whitespace-pre-line">
                    {scripts.alt}
                  </div>
                </Button>
              </div>
            )}
            
            <Button onClick={() => setStage("theme")}>
              テーマに戻る
            </Button>
          </div>
        );
        
      case "edit":
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold">編集 &amp; 保存</h1>
              <p className="text-gray-500">選択したスクリプトを編集してください</p>
            </div>
            
            <div className="space-y-4">
              <Textarea
                value={editedScript}
                onChange={(e) => setEditedScript(e.target.value)}
                className="min-h-[300px]"
              />
              
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setStage("options")}
                >
                  選択に戻る
                </Button>
                <Button onClick={handleSaveScript}>
                  スクリプトを保存
                </Button>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="container max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-center mb-6">
            <div className="flex space-x-4">
              <div className={`flex flex-col items-center ${stage === "theme" ? "text-blue-600 font-medium" : "text-gray-400"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === "theme" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-400"}`}>
                  1
                </div>
                <span className="text-sm mt-1">テーマ</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === "options" ? "text-blue-600 font-medium" : "text-gray-400"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === "options" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-400"}`}>
                  2
                </div>
                <span className="text-sm mt-1">選択</span>
              </div>
              
              <div className={`flex flex-col items-center ${stage === "edit" ? "text-blue-600 font-medium" : "text-gray-400"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${stage === "edit" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-400"}`}>
                  3
                </div>
                <span className="text-sm mt-1">編集 &amp; 保存</span>
              </div>
            </div>
          </div>
          
          {renderStage()}
        </div>
      </div>
      <Toaster />
    </main>
  );
}
