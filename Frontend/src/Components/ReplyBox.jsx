import './ReplyBox.css';

function ReplyBox({ response, isLoading }) {
    if (isLoading) {
        return (
            <div className="reply-box loading">
                <div className="loading-spinner"></div>
                <p>Getting answer...</p>
            </div>
        );
    }

    if (!response) {
        return (
            <div className="reply-box empty">
                <p>Ask a question to get started</p>
            </div>
        );
    }

    try {
        const answer = response.answer || response.response || '';
        const sources = response.sources || [];

        console.log('Response object:', response);
        console.log('Answer:', answer);
        console.log('Sources:', sources);

        return (
            <div className="reply-box">
                {answer && (
                    <div className="answer-section">
                        <h3>Answer</h3>
                        <div className="answer-text">
                            {answer}
                        </div>
                    </div>
                )}

                {sources && sources.length > 0 && (
                    <div className="sources-section">
                        <h3>Sources</h3>
                        <div className="sources-list">
                            {sources.map((source, index) => {
                                // Handle both string sources and object sources
                                const sourceDisplay = typeof source === 'string'
                                    ? source
                                    : `${source.source} (Page ${source.page})`;

                                return (
                                    <div key={index} className="source-item">
                                        <span className="source-number">{index + 1}</span>
                                        <span className="source-text">{sourceDisplay}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        );
    } catch (error) {
        console.error('Error rendering ReplyBox:', error);
        return (
            <div className="reply-box empty">
                <p>Error displaying response. Check console for details.</p>
            </div>
        );
    }
}

export default ReplyBox;
