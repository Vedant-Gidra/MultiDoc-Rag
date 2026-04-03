import { useState } from 'react';
import './QueryBox.css';

function QueryBox({ selectedFile, onQuerySubmit, isLoading }) {
    const [query, setQuery] = useState('');
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!query.trim()) {
            setError('Please enter a query');
            return;
        }

        if (!selectedFile) {
            setError('Please select a PDF first');
            return;
        }

        setError(null);
        await onQuerySubmit(query, selectedFile);
        setQuery('');
    };

    return (
        <form className="query-box" onSubmit={handleSubmit}>
            <div className="query-input-container">
                <input
                    type="text"
                    className="query-input"
                    placeholder="Ask a question about the document..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isLoading || !selectedFile}
                />
                <button
                    type="submit"
                    className="send-button"
                    disabled={isLoading || !selectedFile || !query.trim()}
                    title={!selectedFile ? 'Select a PDF first' : 'Send query'}
                >
                    {isLoading ? (
                        <span className="sending">Sending...</span>
                    ) : (
                        <span className="send-icon">→</span>
                    )}
                </button>
            </div>
            {error && <div className="query-error">{error}</div>}
        </form>
    );
}

export default QueryBox;
