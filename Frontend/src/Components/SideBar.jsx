import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './SideBar.css';

function SideBar({ onFileSelected }) {
    const [files, setFiles] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState(null);
    const [loadingFiles, setLoadingFiles] = useState(true);
    const { token, logout } = useAuth();

    const API_BASE_URL = 'http://127.0.0.1:8000';

    // Fetch list of uploaded files
    useEffect(() => {
        if (token) {
            fetchFiles();
        }
    }, [token]);

    const fetchFiles = async () => {
        try {
            setLoadingFiles(true);
            console.log('Fetching files from:', `${API_BASE_URL}/files`);
            const response = await fetch(`${API_BASE_URL}/files`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`Failed to fetch files: ${response.status}`);
            }

            const data = await response.json();
            console.log('Files data received:', data);

            setFiles(data.files || []);
            setUploadError(null);
        } catch (error) {
            console.error('Error fetching files:', error);
            setUploadError(`Failed to load files: ${error.message}`);
        } finally {
            setLoadingFiles(false);
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.name.endsWith('.pdf')) {
            setUploadError('Please upload a PDF file');
            return;
        }

        setUploading(true);
        setUploadError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('Uploading file:', file.name);
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            console.log('Upload response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Upload error response:', errorText);
                throw new Error(`Upload failed: ${response.status}`);
            }

            const responseData = await response.json();
            console.log('Upload successful:', responseData);

            // Refresh file list after successful upload
            console.log('Refreshing file list...');
            await fetchFiles();

            // Reset file input
            event.target.value = '';
        } catch (error) {
            console.error('Error uploading file:', error);
            setUploadError(`Upload failed: ${error.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleSelectFile = (file) => {
        setSelectedFile(file);
        // Notify parent component of selected file object
        if (onFileSelected) {
            onFileSelected(file);
        }
    };

    const handleDeleteFile = async (fileId) => {
        const confirmed = window.confirm('Are you sure you want to delete this PDF? This action cannot be undone.');
        if (!confirmed) {
            return;
        }

        setUploadError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                const errMsg = await response.text();
                throw new Error(`Failed to delete file: ${response.status} ${errMsg}`);
            }

            // Refresh file list and local selection
            await fetchFiles();
            if (selectedFile?.file_id === fileId) {
                setSelectedFile(null);
                if (onFileSelected) onFileSelected(null);
            }
        } catch (error) {
            console.error('Error deleting file:', error);
            setUploadError(`Delete failed: ${error.message}`);
        }
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h1>Documents</h1>
                <button className="logout-btn" onClick={logout} title="Logout">
                    🚪 Logout
                </button>
            </div>

            <div className="upload-section">
                <label htmlFor="file-input" className="upload-button">
                    + Upload PDF
                </label>
                <input
                    id="file-input"
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    style={{ display: 'none' }}
                />
                {uploading && <div className="upload-status">Uploading...</div>}
                {uploadError && <div className="error-message">{uploadError}</div>}
            </div>

            <div className="files-section">
                {loadingFiles ? (
                    <div className="loading">Loading files...</div>
                ) : files.length === 0 ? (
                    <div className="no-files">No PDFs uploaded yet</div>
                ) : (
                    <ul className="files-list">
                        {files.map((file, index) => (
                            <li
                                key={file.file_id || index}
                                className={`file-item ${selectedFile?.file_id === file.file_id ? 'selected' : ''}`}
                            >
                                <div className="file-entry" onClick={() => handleSelectFile(file)}>
                                    <span className="file-icon">📄</span>
                                    <span className="file-name" title={file.filename}>{file.filename}</span>
                                </div>
                                <button
                                    className="delete-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteFile(file.file_id);
                                    }}
                                    title="Delete file"
                                >
                                    ❌
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default SideBar;