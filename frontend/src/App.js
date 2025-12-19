import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  FileText, 
  FolderArchive, 
  CheckCircle, 
  XCircle, 
  Download, 
  Loader2,
  AlertCircle,
  Trash2,
  Info
} from 'lucide-react';

const API_URL = '/api';

// Styles
const styles = {
  app: {
    minHeight: '100vh',
    background: 'linear-gradient(to bottom right, #f8fafc, #f1f5f9)',
  },
  header: {
    background: 'white',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    borderBottom: '1px solid #e2e8f0',
  },
  headerContent: {
    maxWidth: '896px',
    margin: '0 auto',
    padding: '16px 24px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  headerIcon: {
    padding: '8px',
    background: '#e0e7ff',
    borderRadius: '8px',
  },
  headerTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#1e293b',
    margin: 0,
  },
  headerSubtitle: {
    fontSize: '14px',
    color: '#64748b',
    margin: 0,
  },
  main: {
    maxWidth: '896px',
    margin: '0 auto',
    padding: '32px 24px',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    border: '1px solid #e2e8f0',
    padding: '24px',
    marginBottom: '24px',
  },
  cardTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '16px',
    marginTop: 0,
  },
  uploadGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '16px',
  },
  uploadZone: (isDragging, hasFile) => ({
    position: 'relative',
    border: '2px dashed',
    borderColor: isDragging ? '#6366f1' : hasFile ? '#4ade80' : '#cbd5e1',
    borderRadius: '12px',
    padding: '32px',
    textAlign: 'center',
    transition: 'all 0.2s',
    background: isDragging ? '#eef2ff' : hasFile ? '#f0fdf4' : 'white',
    cursor: 'pointer',
  }),
  uploadInput: {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    opacity: 0,
    cursor: 'pointer',
  },
  uploadContent: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  },
  uploadLabel: {
    fontWeight: '500',
    color: '#334155',
    margin: 0,
  },
  uploadDesc: {
    fontSize: '14px',
    color: '#64748b',
    margin: 0,
  },
  fileName: {
    fontWeight: '500',
    color: '#166534',
    margin: 0,
  },
  fileSize: {
    fontSize: '14px',
    color: '#16a34a',
    margin: 0,
  },
  buttonGroup: {
    display: 'flex',
    gap: '12px',
    marginTop: '24px',
  },
  primaryButton: (disabled) => ({
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px 24px',
    borderRadius: '12px',
    fontWeight: '500',
    fontSize: '16px',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    background: disabled ? '#f1f5f9' : '#4f46e5',
    color: disabled ? '#94a3b8' : 'white',
    boxShadow: disabled ? 'none' : '0 4px 14px rgba(99, 102, 241, 0.3)',
    transition: 'all 0.2s',
  }),
  secondaryButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    borderRadius: '12px',
    fontWeight: '500',
    fontSize: '16px',
    border: 'none',
    cursor: 'pointer',
    background: 'transparent',
    color: '#475569',
    transition: 'all 0.2s',
  },
  errorBox: {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '24px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  errorTitle: {
    fontWeight: '600',
    color: '#991b1b',
    margin: 0,
  },
  errorText: {
    color: '#b91c1c',
    marginTop: '4px',
    margin: 0,
  },
  resultsHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
  },
  downloadButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    background: '#16a34a',
    color: 'white',
    borderRadius: '8px',
    fontWeight: '500',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(22, 163, 74, 0.3)',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    marginBottom: '24px',
  },
  statCard: (bgColor) => ({
    background: bgColor,
    borderRadius: '12px',
    padding: '16px',
    textAlign: 'center',
  }),
  statNumber: (color) => ({
    fontSize: '24px',
    fontWeight: 'bold',
    color: color,
    margin: 0,
  }),
  statLabel: {
    fontSize: '14px',
    color: '#64748b',
    margin: 0,
  },
  resultCard: (isSuccess) => ({
    padding: '16px',
    borderRadius: '8px',
    border: '1px solid',
    borderColor: isSuccess ? '#bbf7d0' : '#fecaca',
    background: isSuccess ? '#f0fdf4' : '#fef2f2',
    marginBottom: '12px',
  }),
  resultContent: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  resultTitle: (isSuccess) => ({
    fontWeight: '500',
    color: isSuccess ? '#166534' : '#991b1b',
    margin: 0,
  }),
  resultDetails: (isSuccess) => ({
    fontSize: '14px',
    color: isSuccess ? '#15803d' : '#b91c1c',
    marginTop: '4px',
  }),
  logsButton: {
    fontSize: '14px',
    color: '#475569',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '8px 0',
  },
  logsBox: {
    marginTop: '8px',
    padding: '16px',
    background: '#0f172a',
    color: '#e2e8f0',
    fontSize: '12px',
    borderRadius: '8px',
    overflow: 'auto',
    maxHeight: '256px',
    fontFamily: 'monospace',
    whiteSpace: 'pre-wrap',
  },
  helpCard: {
    background: '#f8fafc',
    borderRadius: '16px',
    padding: '24px',
    border: '1px solid #e2e8f0',
  },
  helpTitle: {
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '12px',
    marginTop: 0,
  },
  helpList: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  },
  helpItem: {
    display: 'flex',
    gap: '8px',
    fontSize: '14px',
    color: '#475569',
    marginBottom: '8px',
  },
  helpNumber: {
    fontWeight: 'bold',
    color: '#4f46e5',
  },
  codeBox: {
    marginTop: '16px',
    padding: '16px',
    background: '#1e293b',
    borderRadius: '8px',
    border: '1px solid #334155',
  },
  codeTitle: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#94a3b8',
    marginBottom: '12px',
    marginTop: 0,
  },
  code: {
    fontSize: '13px',
    color: '#e2e8f0',
    overflow: 'auto',
    fontFamily: 'monospace',
    whiteSpace: 'pre',
    margin: 0,
  },
  footer: {
    maxWidth: '896px',
    margin: '0 auto',
    padding: '16px 24px',
    textAlign: 'center',
    fontSize: '14px',
    color: '#94a3b8',
  },
};

function FileUploadZone({ accept, label, icon: Icon, file, onFileSelect, description }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  return (
    <div
      style={styles.uploadZone(isDragging, !!file)}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept={accept}
        onChange={(e) => onFileSelect(e.target.files[0])}
        style={styles.uploadInput}
      />
      
      <div style={styles.uploadContent}>
        {file ? (
          <>
            <CheckCircle size={48} color="#22c55e" />
            <div>
              <p style={styles.fileName}>{file.name}</p>
              <p style={styles.fileSize}>
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </>
        ) : (
          <>
            <Icon size={48} color={isDragging ? '#6366f1' : '#94a3b8'} />
            <div>
              <p style={styles.uploadLabel}>{label}</p>
              <p style={styles.uploadDesc}>{description}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ResultCard({ result }) {
  const isSuccess = result.success;
  
  return (
    <div style={styles.resultCard(isSuccess)}>
      <div style={styles.resultContent}>
        {isSuccess ? (
          <CheckCircle size={20} color="#22c55e" />
        ) : (
          <XCircle size={20} color="#ef4444" />
        )}
        <div style={{ flex: 1 }}>
          <p style={styles.resultTitle(isSuccess)}>
            {result.file}
          </p>
          {isSuccess ? (
            <div style={styles.resultDetails(isSuccess)}>
              <p style={{ margin: '4px 0' }}>Output: {result.output}</p>
              <p style={{ margin: '4px 0' }}>{result.rows.toLocaleString()} rows × {result.columns} columns</p>
              <p style={{ margin: '4px 0' }}>{result.plates_processed} plates processed, {result.plates_skipped} skipped</p>
            </div>
          ) : (
            <p style={styles.resultDetails(isSuccess)}>{result.reason}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function LogViewer({ logs }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!logs || logs.length === 0) return null;
  
  return (
    <div style={{ marginTop: '16px' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={styles.logsButton}
      >
        <Info size={16} />
        {isExpanded ? 'Hide' : 'Show'} processing logs ({logs.length} lines)
      </button>
      
      {isExpanded && (
        <pre style={styles.logsBox}>
          {logs.join('\n')}
        </pre>
      )}
    </div>
  );
}

export default function App() {
  const [configFile, setConfigFile] = useState(null);
  const [dataZip, setDataZip] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const canProcess = configFile && dataZip && !isProcessing;

  const handleProcess = async () => {
    if (!canProcess) return;
    
    setIsProcessing(true);
    setError(null);
    setResult(null);
    
    const formData = new FormData();
    formData.append('config', configFile);
    formData.append('data_zip', dataZip);
    
    try {
      const response = await fetch(`${API_URL}/process`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Processing failed');
      }
      
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!result?.job_id) return;
    
    // Use direct backend URL for file download
    const link = document.createElement('a');
    link.href = `http://localhost:8000/api/download/${result.job_id}`;
    link.download = 'harmony_concatenated_results.zip';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = async () => {
    if (result?.job_id) {
      try {
        await fetch(`${API_URL}/cleanup/${result.job_id}`, { method: 'DELETE' });
      } catch (e) {
        // Ignore cleanup errors
      }
    }
    
    setConfigFile(null);
    setDataZip(null);
    setResult(null);
    setError(null);
  };

  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <div style={styles.headerIcon}>
            <FolderArchive size={24} color="#4f46e5" />
          </div>
          <div>
            <h1 style={styles.headerTitle}>Harmony Concatenator</h1>
            <p style={styles.headerSubtitle}>Combine plate data from Harmony exports</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={styles.main}>
        {/* Upload Section */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Upload Files</h2>
          
          <div style={styles.uploadGrid}>
            <FileUploadZone
              accept=".yml,.yaml"
              label="Configuration File"
              description="Drop config.yml here"
              icon={FileText}
              file={configFile}
              onFileSelect={setConfigFile}
            />
            
            <FileUploadZone
              accept=".zip"
              label="Plate Data (ZIP)"
              description="Drop plate folders as .zip"
              icon={FolderArchive}
              file={dataZip}
              onFileSelect={setDataZip}
            />
          </div>
          
          {/* Action Buttons */}
          <div style={styles.buttonGroup}>
            <button
              onClick={handleProcess}
              disabled={!canProcess}
              style={styles.primaryButton(!canProcess)}
            >
              {isProcessing ? (
                <>
                  <Loader2 size={20} className="spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Process Data
                </>
              )}
            </button>
            
            {(configFile || dataZip || result) && (
              <button
                onClick={handleReset}
                style={styles.secondaryButton}
              >
                <Trash2 size={20} />
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div style={styles.errorBox}>
            <AlertCircle size={24} color="#ef4444" />
            <div>
              <h3 style={styles.errorTitle}>Error</h3>
              <p style={styles.errorText}>{error}</p>
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div style={styles.card}>
            <div style={styles.resultsHeader}>
              <h2 style={styles.cardTitle}>Results</h2>
              <button
                onClick={handleDownload}
                style={styles.downloadButton}
              >
                <Download size={20} />
                Download Results
              </button>
            </div>
            
            {/* Summary Stats */}
            <div style={styles.statsGrid}>
              <div style={styles.statCard('#f8fafc')}>
                <p style={styles.statNumber('#1e293b')}>{result.result.plates_found}</p>
                <p style={styles.statLabel}>Plates Found</p>
              </div>
              <div style={styles.statCard('#f0fdf4')}>
                <p style={styles.statNumber('#16a34a')}>{result.result.files_processed}</p>
                <p style={styles.statLabel}>Files Processed</p>
              </div>
              <div style={styles.statCard('#fef2f2')}>
                <p style={styles.statNumber('#dc2626')}>{result.result.files_failed}</p>
                <p style={styles.statLabel}>Files Failed</p>
              </div>
            </div>
            
            {/* Individual Results */}
            <div>
              {result.result.results.map((r, i) => (
                <ResultCard key={i} result={r} />
              ))}
            </div>
            
            {/* Logs */}
            <LogViewer logs={result.result.logs} />
          </div>
        )}

        {/* Help Section */}
        {!result && (
          <div style={styles.helpCard}>
            <h3 style={styles.helpTitle}>How to use</h3>
            <ol style={styles.helpList}>
              <li style={styles.helpItem}>
                <span style={styles.helpNumber}>1.</span>
                Create a config.yml file defining your plate mappings and file patterns
              </li>
              <li style={styles.helpItem}>
                <span style={styles.helpNumber}>2.</span>
                ZIP your Harmony export folder containing all plate subfolders
              </li>
              <li style={styles.helpItem}>
                <span style={styles.helpNumber}>3.</span>
                Upload both files and click "Process Data"
              </li>
              <li style={styles.helpItem}>
                <span style={styles.helpNumber}>4.</span>
                Download the concatenated CSV files
              </li>
            </ol>
            
            <div style={styles.codeBox}>
              <p style={styles.codeTitle}>Example config.yml:</p>
              <pre style={styles.code}>
<span style={{color: '#0891b2'}}>plate_format</span>: <span style={{color: '#c026d3'}}>384</span>
{'\n'}<span style={{color: '#0891b2'}}>plates</span>:
{'\n'}  <span style={{color: '#16a34a'}}>"32846"</span>: {'{'}<span style={{color: '#0891b2'}}>plate_number</span>: <span style={{color: '#c026d3'}}>1</span>, <span style={{color: '#0891b2'}}>replicate</span>: <span style={{color: '#c026d3'}}>1</span>{'}'}
{'\n'}  <span style={{color: '#16a34a'}}>"32847"</span>: {'{'}<span style={{color: '#0891b2'}}>plate_number</span>: <span style={{color: '#c026d3'}}>1</span>, <span style={{color: '#0891b2'}}>replicate</span>: <span style={{color: '#c026d3'}}>2</span>{'}'}
{'\n'}  <span style={{color: '#16a34a'}}>"32848"</span>: {'{'}<span style={{color: '#0891b2'}}>plate_number</span>: <span style={{color: '#c026d3'}}>1</span>, <span style={{color: '#0891b2'}}>replicate</span>: <span style={{color: '#c026d3'}}>3</span>{'}'}
{'\n'}<span style={{color: '#0891b2'}}>input_files</span>:
{'\n'}  - <span style={{color: '#16a34a'}}>"PlateResults.txt"</span>
{'\n'}  - <span style={{color: '#16a34a'}}>"Objects_Population - Nuclei.txt"</span>
              </pre>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        Francis Crick Institute - High Throughput Screening STP
      </footer>

      {/* Spinner animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}