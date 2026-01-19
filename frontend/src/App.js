import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, Trash2, Database, CheckCircle, Loader, X, Bot, User, FileSearch } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

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
  const messagesEndRef = useRef(null);

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

    // Upload to backend
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      // Update status to processing
      newFiles.forEach(file => {
        setProcessingStatus(prev => ({ ...prev, [file.id]: 'processing' }));
      });

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });

      const results = await response.json();

      // Update status to completed
      newFiles.forEach(file => {
        setProcessingStatus(prev => ({ ...prev, [file.id]: 'completed' }));
      });

      // Reload collection info
      loadCollectionInfo();

      alert(`Successfully uploaded ${results.length} document(s)`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Make sure the backend is running at ' + API_BASE);

      // Update status to error
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
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">RAG Assistant</h1>
                <p className="text-sm text-slate-500">Retrieval-Augmented Generation System</p>
              </div>
            </div>

            {/* Collection Stats */}
            <div className="flex gap-6 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{collectionInfo.document_count}</div>
                <div className="text-slate-500">Documents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{collectionInfo.total_chunks}</div>
                <div className="text-slate-500">Chunks</div>
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

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="bg-white rounded-xl shadow-md flex flex-col h-[calc(100vh-280px)]">
            {/* Chat Messages */}
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

                    {/* Sources for assistant messages */}
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
                            <span className="text-blue-500">• {(source.relevance * 100).toFixed(0)}%</span>
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

              {/* Thinking indicator */}
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

            {/* Input Area */}
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
            {/* Upload Area */}
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

            {/* File List */}
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