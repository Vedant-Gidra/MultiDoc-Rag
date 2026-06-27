
import { useState, useEffect } from 'react';
import './App.css'
import { useAuth } from './context/AuthContext';
import Login from './Components/Login';
import Signup from './Components/Signup';
import SideBar from './Components/SideBar';
import QueryBox from './Components/QueryBox';
import ReplyBox from './Components/ReplyBox';
import { API_BASE_URL } from './config';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [queryError, setQueryError] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const { user, token, loading } = useAuth();

  useEffect(() => {
    // Clear UI state on user change (logout/login switch accounts)
    setSelectedFile(null);
    setResponse(null);
    setQueryError(null);
  }, [token]);

  if (loading) {
    return <div className="loading-page">Loading...</div>;
  }

  if (!token) {
    return (
      <>
        {authMode === 'login' ? (
          <Login onSwitchToSignup={() => setAuthMode('signup')} />
        ) : (
          <Signup onSwitchToLogin={() => setAuthMode('login')} />
        )}
      </>
    );
  }

  const handleFileSelected = (file) => {
    setSelectedFile(file);
    setResponse(null);
    setQueryError(null);
    console.log('Selected file:', file);
  };

  const handleQuerySubmit = async (query, file) => {
    setIsLoading(true);
    setQueryError(null);

    try {
      console.log('Submitting query:', query);
      console.log('File object:', file);

      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          question: query,
          file_id: file.file_id,
        }),
      });

      console.log('Query response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Query error response:', errorText);
        throw new Error(`Failed to get answer: ${response.status}`);
      }

      const data = await response.json();
      console.log('Query response data:', data);
      setResponse(data);
    } catch (error) {
      console.error('Error querying:', error);
      setQueryError(`${error.message}. Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <SideBar onFileSelected={handleFileSelected} />
      <div className="main-content">
        {selectedFile ? (
          <div className="chat-area">
            <h2>Chatting about: <span className="file-name">{selectedFile.filename}</span></h2>
            {queryError && <div className="global-error">{queryError}</div>}
            <ReplyBox response={response} isLoading={isLoading} />
            <QueryBox
              selectedFile={selectedFile}
              onQuerySubmit={handleQuerySubmit}
              isLoading={isLoading}
            />
          </div>
        ) : (
          <div className="empty-state">
            <p>Select a PDF to start asking questions</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
