// frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from 'aws-amplify/auth';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import axios from 'axios';
import './App.css';

// 設定を読み込む関数
const loadConfig = () => {
  // ウィンドウオブジェクトから設定を取得
  if (window.REACT_APP_CONFIG) {
    return {
      apiEndpoint: window.REACT_APP_CONFIG.apiEndpoint,
      userPoolId: window.REACT_APP_CONFIG.userPoolId,
      userPoolClientId: window.REACT_APP_CONFIG.userPoolClientId,
      region: window.REACT_APP_CONFIG.region,
    };
  }
  
  // 環境変数から設定を取得（ローカル開発用。frontend/.env.local に VITE_ で始まる名前で書く）
  return {
    apiEndpoint: import.meta.env.VITE_API_ENDPOINT || 'YOUR_API_ENDPOINT',
    userPoolId: import.meta.env.VITE_USER_POOL_ID || 'YOUR_USER_POOL_ID',
    userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID || 'YOUR_USER_POOL_CLIENT_ID',
    region: import.meta.env.VITE_REGION || 'us-east-1',
  };
};

// 設定を取得
const config = loadConfig();

// Amplify設定（リージョンは userPoolId に含まれる）
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: config.userPoolId,
      userPoolClientId: config.userPoolClientId,
      loginWith: { email: true },
    },
  },
});

// ChatInterfaceコンポーネントの定義
function ChatInterface({ signOut, user }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // メッセージが追加されたら自動スクロール
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // チャットメッセージ送信
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    setError(null);

    try {
      // 認証トークンを取得
      const { tokens } = await fetchAuthSession();
      const idToken = tokens?.idToken?.toString();
      if (!idToken) {
        throw new Error('ログインの期限が切れました。ログインし直してください');
      }

      const response = await axios.post(config.apiEndpoint, {
        message: userMessage,
        conversationHistory: messages
      }, {
        headers: {
          'Authorization': idToken,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
      } else {
        setError('応答の取得に失敗しました');
      }
    } catch (err) {
      console.error("API Error:", err);
      setError(`エラーが発生しました: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 会話をクリア
  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Bedrock LLM チャットボット</h1>
        <div className="header-buttons">
          <button className="clear-button" onClick={clearConversation}>
            会話をクリア
          </button>
          <button className="logout-button" onClick={signOut}>
            ログアウト ({user?.signInDetails?.loginId ?? user?.username})
          </button>
        </div>
      </header>
      
      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Bedrock Chatbot へようこそ！</h2>
              <p>何でも質問してください。</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="message assistant loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="メッセージを入力..."
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            送信
          </button>
        </form>
      </main>
      
      <footer>
        <p>Powered by Amazon Bedrock</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    // サインアップは Cognito 側で禁止しているので、「Create Account」タブを出さない。
    // ログインできるのは、terraform.tfvars の allowed_emails のアドレスだけ。
    <Authenticator hideSignUp>
      {({ signOut, user }) => (
        <ChatInterface signOut={signOut} user={user} />
      )}
    </Authenticator>
  );
}

export default App;