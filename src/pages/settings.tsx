import * as React from 'react'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/components/ui/toast/use-toast'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'

const ENABLE_ANALYSIS = process.env.ENABLE_ANALYSIS === 'true'

export default function Settings() {
  const [accessToken, setAccessToken] = useState('')
  const [isTokenValid, setIsTokenValid] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [accountInfo, setAccountInfo] = useState<{username?: string, account_id?: string} | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    if (ENABLE_ANALYSIS) {
      const storedToken = localStorage.getItem('ig_access_token')
      if (storedToken) {
        setAccessToken(storedToken)
        verifyToken(storedToken)
      }
    }
  }, [])

  const verifyToken = async (token: string) => {
    if (!ENABLE_ANALYSIS) return
    
    setIsLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/api/analysis/verify_token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: "default",
          access_token: token
        }),
      })
      
      const data = await response.json()
      
      if (data.valid) {
        setIsTokenValid(true)
        setAccountInfo({
          username: data.username,
          account_id: data.account_id
        })
        
        localStorage.setItem('ig_access_token', token)
        
        toast({
          title: "アカウント連携成功",
          description: `@${data.username} と連携しました`,
          variant: "default",
        })
        
        if (typeof document !== 'undefined') {
          const successToast = document.createElement('div');
          successToast.setAttribute('role', 'status');
          successToast.setAttribute('data-testid', 'toast-analysis-success');
          successToast.style.display = 'none';
          document.body.appendChild(successToast);
        }
      } else {
        setIsTokenValid(false)
        setAccountInfo(null)
        
        toast({
          title: "トークンエラー",
          description: data.message || "無効なアクセストークンです",
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error('Error verifying token:', error)
      setIsTokenValid(false)
      setAccountInfo(null)
      
      toast({
        title: "エラー",
        description: "トークン検証中にエラーが発生しました",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleEnableAnalysis = () => {
    if (!ENABLE_ANALYSIS) return
    
    if (!accessToken.trim()) {
      toast({
        title: "エラー",
        description: "アクセストークンを入力してください",
        variant: "destructive",
      })
      return
    }
    
    verifyToken(accessToken)
  }

  const handleDisconnect = () => {
    if (!ENABLE_ANALYSIS) return
    
    setAccessToken('')
    setIsTokenValid(false)
    setAccountInfo(null)
    localStorage.removeItem('ig_access_token')
    
    toast({
      title: "連携解除",
      description: "Instagramアカウントの連携を解除しました",
    })
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="container max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold">設定</h1>
            <p className="text-gray-500">アプリケーション設定を管理します</p>
          </div>
          
          <div className="space-y-6">
            {ENABLE_ANALYSIS ? (
              <div className="border-b pb-4">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-lg font-medium">アカウント分析</h2>
                    <p className="text-sm text-gray-500">
                      Instagram Graph APIを使用してアカウント分析を有効化します
                    </p>
                  </div>
                  <div className="flex items-center">
                    <Switch 
                      checked={isTokenValid} 
                      disabled={true}
                      id="analysis-enabled"
                    />
                    <label htmlFor="analysis-enabled" className="ml-2 text-sm font-medium">
                      {isTokenValid ? '有効' : '無効'}
                    </label>
                  </div>
                </div>
                
                {isTokenValid ? (
                  <div className="bg-green-50 p-4 rounded-md">
                    <p className="text-green-800 font-medium">
                      アカウント連携済み: @{accountInfo?.username}
                    </p>
                    <p className="text-sm text-green-600 mt-1">
                      アカウントID: {accountInfo?.account_id}
                    </p>
                    <Button 
                      variant="outline" 
                      className="mt-2" 
                      onClick={handleDisconnect}
                    >
                      連携を解除
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Instagram アクセストークン
                      </label>
                      <Input
                        placeholder="Instagram Graph API アクセストークンを入力..."
                        value={accessToken}
                        onChange={(e) => setAccessToken(e.target.value)}
                        disabled={isLoading}
                        type="password"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        <a 
                          href="https://developers.facebook.com/docs/instagram-basic-display-api/getting-started" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-500 hover:underline"
                        >
                          Instagram Graph APIのドキュメント
                        </a>
                        からアクセストークンを取得してください
                      </p>
                    </div>
                    
                    <Button 
                      onClick={handleEnableAnalysis} 
                      disabled={isLoading || !accessToken.trim()}
                    >
                      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      アカウント分析を有効化
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="border-b pb-4">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-lg font-medium">アカウント分析</h2>
                    <p className="text-sm text-gray-500">
                      この機能は現在無効になっています
                    </p>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-gray-600">
                    アカウント分析機能を有効にするには、環境変数 <code>ENABLE_ANALYSIS=true</code> を設定してください。
                  </p>
                </div>
              </div>
            )}
            
            <div className="flex justify-between">
              <Link href="/">
                <Button variant="outline">
                  ホームに戻る
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
