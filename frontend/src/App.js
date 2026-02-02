import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, Trash2, Database, CheckCircle, Loader, X, Bot, User, FileSearch, BarChart3, PieChart, TrendingUp, Zap } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// Easter Egg: Konami Code detector
const useKonamiCode = (callback) => {
  const [keys, setKeys] = useState([]);
  const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

  useEffect(() => {
    const handleKeyDown = (e) => {
      setKeys(prev => {
        const newKeys = [...prev, e.key].slice(-10);
        if (newKeys.join(',') === konamiCode.join(',')) {
          callback();
          return [];
        }
        return newKeys;
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
};

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processingStatus, setProcessingStatus] = useState({});
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I can help you find information from the document database. Ask me anything!',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [collectionInfo, setCollectionInfo] = useState({
    document_count: 0,
    total_chunks: 0
  });
  const [easterEggActive, setEasterEggActive] = useState(false);
  const messagesEndRef = useRef(null);

  // Mock analytics data - replace with real API call
  const [analytics, setAnalytics] = useState({
    totalChunks: 846,
    avgChunkSize: 512,
    totalTokens: 438464,

    documentTypes: [
      { type: 'PDF', count: 23, percentage: 65 },
      { type: 'DOCX', count: 10, percentage: 28 },
    ],
    chunkDistribution: [
      { range: '0-200', count: 156 },
      { range: '200-400', count: 423 },
      { range: '400-600', count: 489 },

    ],
    recentActivity: [
      { action: 'Document uploaded', file: 'Q4_Report.pdf', time: '2 hours ago' },
      { action: 'Query processed', query: 'revenue growth', time: '3 hours ago' },
      { action: 'Document uploaded', file: 'Strategy_2024.docx', time: '5 hours ago' }
    ]
  });

  // Easter Egg activation
  useKonamiCode(() => {
    setEasterEggActive(true);
    setTimeout(() => setEasterEggActive(false), 5000);
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadCollectionInfo();
  }, []);

  const loadCollectionInfo = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setCollectionInfo({
        document_count: data.collection.document_count,
        total_chunks: data.collection.document_count
      });
    } catch (error) {
      console.error('Failed to load collection info:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (!files.length) return;

    const newFiles = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.name.split('.').pop().toLowerCase(),
      status: 'pending'
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      newFiles.forEach(file => {
        setProcessingStatus(prev => ({ ...prev, [file.id]: 'processing' }));
      });

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });

      const results = await response.json();

      newFiles.forEach(file => {
        setProcessingStatus(prev => ({ ...prev, [file.id]: 'completed' }));
      });

      loadCollectionInfo();
      alert(`Successfully uploaded ${results.length} document(s)`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Make sure the backend is running at ' + API_BASE);

      newFiles.forEach(file => {
        setProcessingStatus(prev => ({ ...prev, [file.id]: 'error' }));
      });
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isThinking) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsThinking(true);

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: inputMessage, n_results: 5 })
      });

      const data = await response.json();

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Query failed:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend is running at ' + API_BASE,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsThinking(false);
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    setProcessingStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[fileId];
      return newStatus;
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <X className="w-4 h-4 text-red-500" />;
      default:
        return <Loader className="w-4 h-4 text-yellow-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Easter Egg Overlay */}
      {easterEggActive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80 animate-pulse">
          <div className="text-center">
            <div className="text-6xl mb-4 animate-bounce">🎮</div>
            <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600 mb-2">
              KONAMI CODE ACTIVATED!
            </div>
            <div className="text-xl text-white">You've unlocked the secret RAG power mode! 🚀</div>
            <div className="text-sm text-gray-400 mt-4">May your embeddings be dense and your retrievals precise</div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg ${easterEggActive ? 'animate-spin' : ''}`}>
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">RAG Assistant</h1>
                <p className="text-sm text-slate-500">Retrieval-Augmented Generation System</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-white text-blue-600 shadow-md'
                : 'bg-white/50 text-slate-600 hover:bg-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-white text-blue-600 shadow-md'
                : 'bg-white/50 text-slate-600 hover:bg-white'
            }`}
          >
            <Bot className="w-4 h-4" />
            Chat with RAG
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'documents'
                ? 'bg-white text-blue-600 shadow-md'
                : 'bg-white/50 text-slate-600 hover:bg-white'
            }`}
          >
            <Upload className="w-4 h-4" />
            Document Management
          </button>
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-600">Total Chunks</div>
                  <Database className="w-5 h-5 text-blue-500" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{analytics.totalChunks.toLocaleString()}</div>
                <div className="text-xs text-green-600 mt-1">↑ 12% from last week</div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-600">Avg Chunk Size</div>
                  <Zap className="w-5 h-5 text-yellow-500" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{analytics.avgChunkSize}</div>
                <div className="text-xs text-slate-500 mt-1">tokens per chunk</div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-600">Total Tokens</div>
                  <TrendingUp className="w-5 h-5 text-purple-500" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{(analytics.totalTokens / 1000).toFixed(0)}K</div>
                <div className="text-xs text-slate-500 mt-1">in vector database</div>
              </div>

              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-600">Documents</div>
                  <FileText className="w-5 h-5 text-green-500" />
                </div>
                <div className="text-3xl font-bold text-slate-800">{collectionInfo.document_count}</div>
                <div className="text-xs text-slate-500 mt-1">files indexed</div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Document Types */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center gap-2 mb-4">
                  <PieChart className="w-5 h-5 text-blue-500" />
                  <h3 className="text-lg font-semibold text-slate-800">Document Types</h3>
                </div>
                <div className="space-y-3">
                  {analytics.documentTypes.map((doc, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-slate-700">{doc.type}</span>
                        <span className="text-sm text-slate-500">{doc.count} files ({doc.percentage}%)</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${doc.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Chunk Distribution */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="w-5 h-5 text-purple-500" />
                  <h3 className="text-lg font-semibold text-slate-800">Chunk Size Distribution</h3>
                </div>
                <div className="space-y-3">
                  {analytics.chunkDistribution.map((chunk, idx) => {
                    const maxCount = Math.max(...analytics.chunkDistribution.map(c => c.count));
                    const percentage = (chunk.count / maxCount) * 100;
                    return (
                      <div key={idx}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-slate-700">{chunk.range} tokens</span>
                          <span className="text-sm text-slate-500">{chunk.count} chunks</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-600 h-2 rounded-full transition-all"
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {analytics.recentActivity.map((activity, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-800">{activity.action}</div>
                      <div className="text-xs text-slate-500">{activity.file || activity.query}</div>
                    </div>
                    <div className="text-xs text-slate-400">{activity.time}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Easter Egg Hint */}
            <div className="text-center text-xs text-slate-400 mt-8">
              Psst... try the Konami Code 🎮
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="bg-white rounded-xl shadow-md flex flex-col h-[calc(100vh-280px)]">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}

                  <div className={`max-w-2xl ${message.role === 'user' ? 'order-1' : ''}`}>
                    <div
                      className={`rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                          : 'bg-slate-100 text-slate-800'
                      }`}
                    >
                      <p className="leading-relaxed">{message.content}</p>
                    </div>

                    {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center gap-1 text-xs text-slate-500 mb-1">
                          <FileSearch className="w-3 h-3" />
                          Sources:
                        </div>
                        {message.sources.map((source, idx) => (
                          <div
                            key={idx}
                            className="text-xs bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg inline-flex items-center gap-2 mr-2"
                          >
                            <FileText className="w-3 h-3" />
                            {source.filename} (p.{source.page})
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="text-xs text-slate-400 mt-1">
                      {formatTime(message.timestamp)}
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center">
                      <User className="w-5 h-5 text-slate-600" />
                    </div>
                  )}
                </div>
              ))}

              {isThinking && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-slate-100 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-slate-200 p-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask a question about your documents..."
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isThinking}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isThinking || !inputMessage.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
              <div className="text-xs text-slate-500 mt-2">
                Ask questions and get answers augmented with information from your document database
              </div>
            </div>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-md p-8">
              <label className="block">
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-12 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all cursor-pointer">
                  <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                  <div className="text-lg font-medium text-slate-700 mb-2">
                    Drop files here or click to upload
                  </div>
                  <div className="text-sm text-slate-500">
                    Supports PDF, DOCX, and TXT files
                  </div>
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.docx,.doc,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              </label>
            </div>

            {uploadedFiles.length > 0 && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">Uploaded Files</h3>
                <div className="space-y-2">
                  {uploadedFiles.map(file => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="w-8 h-8 text-blue-500" />
                        <div className="flex-1">
                          <div className="font-medium text-slate-800">{file.name}</div>
                          <div className="text-sm text-slate-500">
                            {formatFileSize(file.size)} • {file.type.toUpperCase()}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {getStatusIcon(processingStatus[file.id] || 'pending')}
                        <span className="text-sm font-medium text-slate-600 capitalize min-w-[80px]">
                          {processingStatus[file.id] || 'pending'}
                        </span>
                        <button
                          onClick={() => removeFile(file.id)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                        >
                          <X className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;